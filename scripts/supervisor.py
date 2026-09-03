#!/usr/bin/env python3
"""Versioned process protocol between the native app and product Supervisor."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import preflight
from forma_ai.artifacts import load_component, select_artifact, verify_file
from forma_ai.downloads import ResumableDownloader
from forma_ai.installer import OMLXInstallLayout, OMLXInstaller
from forma_ai.lifecycle import LifecycleJournal
from forma_ai.models import (
    huggingface_snapshot,
    link_external_model,
    load_model,
    verify_snapshot,
)
from forma_ai.model_downloads import download_model_snapshot
from forma_ai.broker import BrokerPolicy, JsonlAuditSink, OMLXBroker, OMLXUpstream, create_server
from forma_ai.processes import herdr_process_spec, omlx_process_spec
from forma_ai.runtime import RuntimeManager, SubprocessController
from forma_ai.semantica_runtime import SemanticaLayout, SemanticaRuntimeInspector
from forma_ai.governed_memory import GovernedMemory
from forma_ai.embedding_config import activate_embedding_route, load_approved_embedding_route
from forma_ai.memory_service import (
    GovernedMemoryService,
    MemoryServicePolicy,
    create_memory_server,
)
from forma_ai.cloud_approval import CloudApprovalStore
from forma_ai.cloud_catalog import load_cloud_provider
from forma_ai.cloud_proposals import CloudProposalStore
from forma_ai.deepseek_adapter import DeepSeekAdapter
from forma_ai.mcp_client import MCPServerSpec, connect_stdio_server
from forma_ai.skills import SkillRegistry
from forma_ai.tool_registry import ToolRegistry
from forma_ai.inference_routing import RoutingError, TaskRequirements, create_cloud_proposal
from forma_ai.local_tasks import (
    MAXIMUM_TASK_BYTES, LocalTaskError, LocalTaskRequest, completion_body, normalize_local_result,
    parse_local_task,
)
from forma_ai.cloud_preferences import CloudPreferenceStore
from forma_ai.local_profiles import load_local_profile
from forma_ai.system_resources import measure_available_memory
from forma_ai.task_orchestrator import (
    MAXIMUM_UNIFIED_TASK_BYTES, local_task_from_unified, parse_unified_task,
    plan_unified_task,
)
from forma_ai.herdr_adapter import HerdrAdapter
from forma_ai.herdr_transport import (
    HerdrProtocolError,
    HerdrSocketTransport,
    HerdrTransportError,
    resolve_socket_path,
)


SCHEMA_VERSION = 1
DEFAULT_UPSTREAMS = REPOSITORY_ROOT / "config/upstreams.json"
DEFAULT_MODELS = REPOSITORY_ROOT / "config/models.json"
DEFAULT_MODEL_ID = "qwen3-0.6b-4bit-alpha"
DEFAULT_EMBEDDING_MODEL_ID = "multilingual-e5-small-mlx-alpha"
HERDR_SESSION_NAME = "forma-workbench"
DEFAULT_CLOUD_PROVIDERS = REPOSITORY_ROOT / "config/cloud-providers.json"
DEFAULT_LOCAL_PROFILES = REPOSITORY_ROOT / "config/local-model-profiles.json"
DEFAULT_HARDWARE_PROFILES = REPOSITORY_ROOT / "config/hardware-profiles.yaml"
MAXIMUM_CLOUD_PAYLOAD_BYTES = 8 * 1024 * 1024


class ProtocolArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def envelope(
    *,
    command: str,
    request_id: str,
    status: str,
    payload: dict[str, Any] | None = None,
    error: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "request_id": request_id,
        "status": status,
        "payload": payload,
        "error": error,
        "emitted_at": datetime.now(timezone.utc).isoformat(),
    }


def parser() -> argparse.ArgumentParser:
    result = ProtocolArgumentParser(description=__doc__)
    result.add_argument("--request-id", required=True)
    commands = result.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("preflight")
    probe.add_argument(
        "--profiles",
        type=Path,
        default=REPOSITORY_ROOT / "config/hardware-profiles.yaml",
    )
    probe.add_argument("--check-path", type=Path, required=True)
    probe.add_argument("--ports", type=int, nargs="*", default=list(preflight.DEFAULT_PORTS))
    for name in ("installation-plan", "installation-status", "install-omlx"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        if name != "installation-status":
            command.add_argument("--os-major", type=int, required=True)
            command.add_argument("--upstreams", type=Path, default=DEFAULT_UPSTREAMS)
        if name == "install-omlx":
            command.add_argument("--approve-artifact-sha256", required=True)
    for name in (
        "model-plan", "link-model", "embedding-plan", "download-embedding",
        "activate-embedding",
    ):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--cache-root", type=Path, required=True)
        command.add_argument("--catalog", type=Path, default=DEFAULT_MODELS)
        command.add_argument(
            "--model-id",
            default=DEFAULT_EMBEDDING_MODEL_ID if "embedding" in name else DEFAULT_MODEL_ID,
        )
        if name in {"link-model", "download-embedding", "activate-embedding"}:
            command.add_argument("--approve-revision", required=True)
    for name in ("runtime-status", "start-runtime", "stop-runtime", "sample-task", "local-task"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        if name == "start-runtime":
            command.add_argument("--omlx-port", type=int, default=8000)
            command.add_argument("--broker-port", type=int, default=43110)
            command.add_argument("--memory-port", type=int, default=43111)
            command.add_argument("--os-major", type=int, required=True)
            command.add_argument("--architecture", required=True)
            command.add_argument("--upstreams", type=Path, default=DEFAULT_UPSTREAMS)
        if name in {"sample-task", "local-task"}:
            command.add_argument("--broker-port", type=int, default=43110)
    semantica_status = commands.add_parser("semantica-status")
    semantica_status.add_argument("--root", type=Path, required=True)
    internal = commands.add_parser("internal-broker")
    internal.add_argument("--root", type=Path, required=True)
    internal.add_argument("--omlx-port", type=int, required=True)
    internal.add_argument("--broker-port", type=int, required=True)
    memory_internal = commands.add_parser("internal-memory-service")
    memory_internal.add_argument("--root", type=Path, required=True)
    memory_internal.add_argument("--memory-port", type=int, required=True)
    cloud_preview = commands.add_parser("cloud-preview")
    cloud_preview.add_argument("--root", type=Path, required=True)
    cloud_preview.add_argument("--catalog", type=Path, default=DEFAULT_CLOUD_PROVIDERS)
    cloud_preview.add_argument("--provider-id", default="deepseek")
    cloud_preview.add_argument("--model-id", required=True)
    cloud_preview.add_argument("--estimated-input-tokens", type=int, required=True)
    cloud_preview.add_argument("--maximum-output-tokens", type=int, required=True)
    cloud_preview.add_argument("--minimum-available-memory-mb", type=int, required=True)
    cloud_preview.add_argument("--required-capability", action="append", required=True)
    cloud_preview.add_argument("--data-class", action="append", required=True)
    cloud_preview.add_argument("--reason-code", action="append", required=True)
    cloud_preview.add_argument("--redaction", action="append", default=[])
    for name in ("cloud-approve", "cloud-reject", "cloud-execute"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--proposal-id", required=True)
        if name == "cloud-approve":
            command.add_argument("--maximum-cost-usd", type=float, required=True)
        if name == "cloud-execute":
            command.add_argument("--catalog", type=Path, default=DEFAULT_CLOUD_PROVIDERS)
    for name in ("cloud-settings", "set-cloud-settings"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--catalog", type=Path, default=DEFAULT_CLOUD_PROVIDERS)
        command.add_argument("--provider-id", default="deepseek")
        if name == "set-cloud-settings":
            selection = command.add_mutually_exclusive_group(required=True)
            selection.add_argument("--enable", action="store_true")
            selection.add_argument("--disable", action="store_true")
            command.add_argument("--model-id")
    task_submit = commands.add_parser("task-submit")
    task_submit.add_argument("--root", type=Path, required=True)
    task_submit.add_argument("--broker-port", type=int, default=43110)
    task_submit.add_argument("--model-catalog", type=Path, default=DEFAULT_MODELS)
    task_submit.add_argument("--hardware-profiles", type=Path, default=DEFAULT_HARDWARE_PROFILES)
    task_submit.add_argument("--local-profiles", type=Path, default=DEFAULT_LOCAL_PROFILES)
    task_submit.add_argument("--evidence-root", type=Path, default=REPOSITORY_ROOT)
    task_submit.add_argument(
        "--local-profile-id", default="qwen3-0.6b-4bit-apple-silicon-alpha",
    )
    task_submit.add_argument("--cloud-catalog", type=Path, default=DEFAULT_CLOUD_PROVIDERS)
    herdr_snapshot = commands.add_parser("herdr-snapshot")
    herdr_snapshot.add_argument("--root", type=Path, required=True)
    for name in ("mcp-list-tools", "mcp-call-tool"):
        command = commands.add_parser(name)
        command.add_argument("--server-command", required=True)
        command.add_argument("--server-arg", action="append", default=[])
        if name == "mcp-call-tool":
            command.add_argument("--tool-name", required=True)
            command.add_argument("--arguments-json", default="{}")
    skills_list = commands.add_parser("skills-list")
    skills_list.add_argument("--skill-root", action="append", required=True, type=Path)
    skills_inject = commands.add_parser("skills-inject")
    skills_inject.add_argument("--skill-root", action="append", required=True, type=Path)
    skills_inject.add_argument("--skill-name", action="append", required=True)
    tools_discover = commands.add_parser("tools-discover")
    tools_discover.add_argument("--root", type=Path, required=True)
    tools_discover.add_argument("--catalog", type=Path, default=REPOSITORY_ROOT / "config/tool-packages.json")
    tools_discover.add_argument("--local-path", action="append", default=[], type=Path)
    tools_install = commands.add_parser("tools-install")
    tools_install.add_argument("--root", type=Path, required=True)
    tools_install.add_argument("--catalog", type=Path, default=REPOSITORY_ROOT / "config/tool-packages.json")
    tools_install.add_argument("--package-id", required=True)
    for name in ("tools-start", "tools-stop"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--catalog", type=Path, default=REPOSITORY_ROOT / "config/tool-packages.json")
        command.add_argument("--tool-id", required=True)
    return result


def validate_request_id(value: str) -> str:
    parsed = uuid.UUID(value)
    if str(parsed) != value.lower():
        raise ValueError("request ID must use canonical UUID form")
    return str(parsed)


def run(args: argparse.Namespace, input_data: bytes | None = None) -> dict[str, Any]:
    request_id = validate_request_id(args.request_id)
    if args.command in {"mcp-list-tools", "mcp-call-tool"}:
        spec = MCPServerSpec(command=args.server_command, args=tuple(args.server_arg))
        client = connect_stdio_server(spec)
        try:
            if args.command == "mcp-list-tools":
                tools = client.list_tools()
                payload = {
                    "schema_version": 1,
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.input_schema,
                        }
                        for tool in tools
                    ],
                }
            else:
                try:
                    arguments = json.loads(args.arguments_json)
                except json.JSONDecodeError as exc:
                    raise ValueError("arguments JSON is invalid") from exc
                if not isinstance(arguments, dict):
                    raise ValueError("arguments JSON must decode to an object")
                result = client.call_tool(args.tool_name, arguments)
                payload = {
                    "schema_version": 1,
                    "tool_name": args.tool_name,
                    "content": list(result.content),
                    "is_error": result.is_error,
                }
        finally:
            client.close()
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload=payload,
        )
    if args.command in {"skills-list", "skills-inject"}:
        registry = SkillRegistry(args.skill_root)
        if args.command == "skills-list":
            payload = {
                "schema_version": 1,
                "skills": [item.to_catalog_entry() for item in registry.descriptors],
            }
        else:
            payload = {
                "schema_version": 1,
                "injection": registry.inject(args.skill_name),
                "skill_names": list(args.skill_name),
            }
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload=payload,
        )
    if args.command in {"tools-discover", "tools-install", "tools-start", "tools-stop"}:
        _validate_product_root(args.root)
        registry = ToolRegistry(
            args.root,
            catalog_path=args.catalog,
            repository_root=REPOSITORY_ROOT,
            local_paths=args.local_path if hasattr(args, "local_path") else (),
        )
        if args.command == "tools-discover":
            payload = {
                "schema_version": 1,
                "tools": [
                    {
                        "tool_id": item.tool_id,
                        "version": item.version,
                        "source": item.source,
                        "command": item.command,
                        "args": list(item.args),
                        "install_dir": None if item.install_dir is None else str(item.install_dir),
                    }
                    for item in registry.discover()
                ],
            }
        elif args.command == "tools-install":
            installation = registry.install(args.package_id)
            payload = {
                "schema_version": 1,
                "tool_id": installation.tool_id,
                "version": installation.version,
                "source": installation.source,
                "install_dir": str(installation.install_dir),
            }
        elif args.command == "tools-start":
            state = registry.start(args.tool_id)
            payload = {"schema_version": 1, **asdict(state)}
        else:
            registry.stop(args.tool_id)
            payload = {"schema_version": 1, "tool_id": args.tool_id, "stopped": True}
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload=payload,
        )
    if args.command == "herdr-snapshot":
        _validate_product_root(args.root)
        status = RuntimeManager(args.root).status()
        if not status.get("herdr_alive"):
            return envelope(
                command=args.command,
                request_id=request_id,
                status="ok",
                payload={
                    "schema_version": 1,
                    "freshness": "stale",
                    "reason": "HERDR_NOT_RUNNING",
                    "version": None,
                    "protocol": None,
                    "agents": [],
                },
            )
        socket_path = resolve_socket_path(environ={"HERDR_SESSION": HERDR_SESSION_NAME})
        transport = HerdrSocketTransport(socket_path=socket_path, environ={})
        snapshot = HerdrAdapter(request=transport, probe=transport.probe).snapshot()
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={
                "schema_version": 1,
                "freshness": "fresh",
                "reason": None,
                "version": snapshot.version,
                "protocol": snapshot.protocol,
                "agents": [asdict(item) for item in snapshot.agents],
            },
        )
    if args.command == "preflight":
        if not args.profiles.is_absolute() or not args.check_path.is_absolute():
            raise ValueError("preflight paths must be absolute")
        if not args.check_path.is_dir():
            raise ValueError("preflight check path must be an existing directory")
        if len(args.ports) != len(set(args.ports)) or any(
            port < 1024 or port > 65535 for port in args.ports
        ):
            raise ValueError("preflight ports must be unique unprivileged TCP ports")
        report = preflight.build_report(args.profiles, args.check_path, tuple(args.ports))
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload=report,
        )
    if args.command in {"installation-plan", "installation-status", "install-omlx"}:
        _validate_product_root(args.root)
    if args.command in {
        "model-plan", "link-model", "embedding-plan", "download-embedding",
        "activate-embedding",
    }:
        _validate_product_root(args.root)
    if args.command == "task-submit":
        _validate_product_root(args.root)
        for path in (
            args.model_catalog, args.hardware_profiles, args.local_profiles, args.cloud_catalog,
        ):
            if not path.is_absolute() or not path.is_file():
                raise ValueError("task routing catalogs must be existing absolute files")
        if not args.evidence_root.is_absolute() or not args.evidence_root.is_dir():
            raise ValueError("task evidence root must be an existing absolute directory")
        model_ids = _catalog_ids(args.model_catalog, "models")
        hardware_ids = _catalog_ids(args.hardware_profiles, "profiles")
        profile = load_local_profile(
            args.local_profiles, args.local_profile_id,
            known_model_ids=model_ids, known_hardware_profile_ids=hardware_ids,
            repository_root=args.evidence_root,
        )
        provider = load_cloud_provider(args.cloud_catalog, "deepseek")
        cloud = CloudPreferenceStore(args.root).load(provider)
        memory = measure_available_memory()
        runtime = RuntimeManager(args.root).status()
        if input_data is None:
            raise ValueError("task body is required")
        task = parse_unified_task(input_data)
        plan, requirements, _ = plan_unified_task(
            task, profile=profile, runtime_healthy=runtime["phase"] == "running",
            available_memory_mb=memory.available_memory_mb, cloud=cloud,
        )
        audit = JsonlAuditSink(args.root / "logs/audit/tasks.jsonl")
        audit.record({
            "schema_version": 1, "event": "task_route",
            "correlation_id": request_id, "route": plan.route,
            "reason_codes": list(plan.reason_codes),
            "local_profile_id": profile.id,
            "local_evidence_status": profile.evidence_status,
            "runtime_phase": runtime["phase"],
            "memory_evidence_code": memory.code,
            "available_memory_mb": memory.available_memory_mb,
            "cloud_state_code": cloud.code,
        })
        common = {
            "schema_version": 1, "plan": asdict(plan),
            "resource": asdict(memory), "runtime_phase": runtime["phase"],
            "cloud_unavailable_code": None,
        }
        if plan.route == "local":
            _, broker_token, _ = _runtime_secrets()
            try:
                result = _local_task(
                    args.broker_port, broker_token, request_id,
                    local_task_from_unified(task), profile.runtime_model_ids,
                )
            except LocalTaskError:
                plan = replace(
                    plan,
                    route="cloud_proposal_required" if cloud.valid and cloud.enabled
                    else "capability_unavailable",
                    reason_codes=("local_validation_failed",),
                )
                common["plan"] = asdict(plan)
                audit.record({
                    "schema_version": 1, "event": "task_route_transition",
                    "correlation_id": request_id, "route": plan.route,
                    "reason_codes": ["local_validation_failed"],
                })
            else:
                return envelope(
                    command=args.command, request_id=request_id, status="ok",
                    payload={**common, "result": asdict(result), "proposal": None},
                )
        if plan.route == "cloud_proposal_required":
            try:
                proposal, payload = create_cloud_proposal(
                    correlation_id=request_id, provider=provider, model_id=cloud.model_id,
                    requirements=requirements, reason_codes=plan.reason_codes,
                    outbound_body={
                        "model": cloud.model_id,
                        "messages": [{"role": "user", "content": task.prompt}],
                        "max_tokens": task.maximum_output_tokens, "stream": False,
                    },
                    redactions=(), now=datetime.now(timezone.utc),
                )
            except RoutingError as exc:
                plan = replace(plan, route="capability_unavailable")
                common["plan"] = asdict(plan)
                common["cloud_unavailable_code"] = exc.code
                audit.record({
                    "schema_version": 1, "event": "task_route_transition",
                    "correlation_id": request_id, "route": plan.route,
                    "reason_codes": list(plan.reason_codes),
                    "cloud_unavailable_code": exc.code,
                })
                return envelope(
                    command=args.command, request_id=request_id, status="ok",
                    payload={**common, "result": None, "proposal": None},
                )
            CloudProposalStore(args.root).save(proposal, payload)
            return envelope(
                command=args.command, request_id=request_id, status="ok",
                payload={**common, "result": None, "proposal": proposal.to_dict()},
            )
        return envelope(
            command=args.command, request_id=request_id, status="ok",
            payload={**common, "result": None, "proposal": None},
        )
    if args.command in {
        "cloud-preview", "cloud-approve", "cloud-reject", "cloud-execute",
        "cloud-settings", "set-cloud-settings",
    }:
        _validate_product_root(args.root)
    if args.command in {"cloud-settings", "set-cloud-settings"}:
        if not args.catalog.is_absolute() or not args.catalog.is_file():
            raise ValueError("cloud catalog must be an existing absolute file")
        provider = load_cloud_provider(args.catalog, args.provider_id)
        store = CloudPreferenceStore(args.root)
        if args.command == "cloud-settings":
            state = store.load(provider)
        elif args.enable:
            if not args.model_id:
                raise ValueError("enabled cloud requires a model")
            state = store.save(
                enabled=True, provider=provider, model_id=args.model_id,
                now=datetime.now(timezone.utc),
            )
        else:
            if args.model_id is not None:
                raise ValueError("disabled cloud cannot retain a model")
            state = store.save(enabled=False, now=datetime.now(timezone.utc))
        return envelope(
            command=args.command, request_id=request_id, status="ok", payload=asdict(state),
        )
    if args.command == "cloud-preview":
        if input_data is None or not input_data or len(input_data) > MAXIMUM_CLOUD_PAYLOAD_BYTES:
            raise ValueError("cloud payload is missing or too large")
        if not args.catalog.is_absolute() or not args.catalog.is_file():
            raise ValueError("cloud catalog must be an existing absolute file")
        try:
            outbound_body = json.loads(input_data)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("cloud payload must be UTF-8 JSON") from exc
        if not isinstance(outbound_body, dict):
            raise ValueError("cloud payload must be a JSON object")
        provider = load_cloud_provider(args.catalog, args.provider_id)
        requirements = TaskRequirements(
            estimated_input_tokens=args.estimated_input_tokens,
            maximum_output_tokens=args.maximum_output_tokens,
            required_capabilities=frozenset(args.required_capability),
            minimum_available_memory_mb=args.minimum_available_memory_mb,
            data_classes=frozenset(args.data_class),
        )
        proposal, payload = create_cloud_proposal(
            correlation_id=request_id, provider=provider, model_id=args.model_id,
            requirements=requirements, reason_codes=tuple(args.reason_code),
            outbound_body=outbound_body, redactions=tuple(args.redaction),
            now=datetime.now(timezone.utc),
        )
        CloudProposalStore(args.root).save(proposal, payload)
        return envelope(
            command=args.command, request_id=request_id, status="ok",
            payload={"schema_version": 1, "proposal": proposal.to_dict(), "approval_required": True},
        )
    if args.command in {"cloud-approve", "cloud-reject", "cloud-execute"}:
        proposals = CloudProposalStore(args.root)
        proposal, payload = proposals.load(args.proposal_id)
        audit = JsonlAuditSink(args.root / "logs/audit/cloud.jsonl")
        if args.command == "cloud-approve":
            approval = CloudApprovalStore(args.root).approve(
                proposal, maximum_cost_usd=args.maximum_cost_usd,
                now=datetime.now(timezone.utc),
            )
            audit.record({
                "schema_version": 1, "event": "cloud_escalation_decision",
                "correlation_id": proposal.correlation_id, "proposal_id": proposal.proposal_id,
                "provider": proposal.provider_id, "model": proposal.model_id,
                "payload_sha256": proposal.payload_sha256, "outcome": "approved",
                "maximum_cost_usd": approval.maximum_cost_usd,
            })
            return envelope(
                command=args.command, request_id=request_id, status="ok",
                payload={"schema_version": 1, "approval": asdict(approval)},
            )
        if args.command == "cloud-reject":
            proposals.reject(args.proposal_id)
            audit.record({
                "schema_version": 1, "event": "cloud_escalation_decision",
                "correlation_id": proposal.correlation_id, "proposal_id": proposal.proposal_id,
                "provider": proposal.provider_id, "model": proposal.model_id,
                "payload_sha256": proposal.payload_sha256, "outcome": "denied",
            })
            return envelope(
                command=args.command, request_id=request_id, status="ok",
                payload={"schema_version": 1, "proposal_id": proposal.proposal_id, "outcome": "denied"},
            )
        if not args.catalog.is_absolute() or not args.catalog.is_file():
            raise ValueError("cloud catalog must be an existing absolute file")
        api_key = os.environ.get("FORMA_AI_DEEPSEEK_API_KEY", "")
        provider = load_cloud_provider(args.catalog, proposal.provider_id)
        try:
            result = DeepSeekAdapter(
                provider, CloudApprovalStore(args.root), audit,
            ).execute(proposal, payload, api_key=api_key, now=datetime.now(timezone.utc))
        finally:
            proposals.discard(args.proposal_id)
        return envelope(
            command=args.command, request_id=request_id, status="ok",
            payload={"schema_version": 1, "result": asdict(result)},
        )
    if args.command in {
        "model-plan", "link-model", "embedding-plan", "download-embedding",
        "activate-embedding",
    }:
        if not args.cache_root.is_absolute() or not args.cache_root.is_dir():
            raise ValueError("model cache root must be an existing absolute directory")
        if not args.catalog.is_absolute() or not args.catalog.is_file():
            raise ValueError("model catalog must be an existing absolute file")
        model = load_model(args.catalog, args.model_id)
        if args.command in {
            "embedding-plan", "download-embedding", "activate-embedding",
        } and "embedding" not in model.capabilities:
            raise ValueError("selected model is not embedding capable")
        snapshot = huggingface_snapshot(args.cache_root, model)
        if args.command in {"model-plan", "embedding-plan"}:
            try:
                verified = verify_snapshot(args.cache_root, model)
                available = True
                reason = None
            except Exception as exc:
                verified = snapshot
                available = False
                reason = getattr(exc, "code", "MODEL_UNAVAILABLE")
            return envelope(
                command=args.command,
                request_id=request_id,
                status="ok",
                payload={
                    "schema_version": 1,
                    "model_id": model.id,
                    "repository": model.repository,
                    "revision": model.revision,
                    "license": model.license,
                    "capabilities": list(model.capabilities),
                    "quantization_bits": model.quantization_bits,
                    "embedding_dimension": model.embedding_dimension,
                    "query_prefix": model.query_prefix,
                    "document_prefix": model.document_prefix,
                    "size_bytes": sum(item.size_bytes for item in model.files.values()),
                    "source_path": str(verified),
                    "available_verified": available,
                    "unavailable_reason": reason,
                    "approval_required": True,
                },
            )
        if args.approve_revision != model.revision:
            raise ValueError("model approval does not match selected revision")
        if args.command == "download-embedding":
            downloaded = download_model_snapshot(
                cache_root=args.cache_root,
                model=model,
                approved_revision=args.approve_revision,
            )
            return envelope(
                command=args.command,
                request_id=request_id,
                status="ok",
                payload=downloaded.to_dict(),
            )
        if args.command == "activate-embedding" and RuntimeManager(args.root).status()["phase"] != "stopped":
            raise ValueError("embedding activation requires a stopped runtime")
        reference = link_external_model(
            product_root=args.root,
            cache_root=args.cache_root,
            model=model,
        )
        if args.command == "activate-embedding":
            route = activate_embedding_route(
                args.root, model, reference, approved_revision=args.approve_revision,
            )
            return envelope(
                command=args.command, request_id=request_id, status="ok",
                payload={"schema_version": 1, "route": asdict(route), "reference": asdict(reference)},
            )
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={"schema_version": 1, "reference": asdict(reference)},
        )
    if args.command in {
        "runtime-status", "start-runtime", "stop-runtime", "sample-task", "local-task",
        "internal-broker", "internal-memory-service", "semantica-status",
    }:
        _validate_product_root(args.root)
    if args.command == "semantica-status":
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload=SemanticaRuntimeInspector(SemanticaLayout(args.root)).status(),
        )
    if args.command == "runtime-status":
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={"schema_version": 1, **RuntimeManager(args.root).status()},
        )
    if args.command == "stop-runtime":
        stopped = RuntimeManager(args.root).stop()
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={"schema_version": 1, "runtime": asdict(stopped)},
        )
    if args.command == "internal-broker":
        _run_internal_broker(args.root, args.omlx_port, args.broker_port)
        return envelope(command=args.command, request_id=request_id, status="ok", payload={"schema_version": 1})
    if args.command == "internal-memory-service":
        _run_internal_memory_service(args.root, args.memory_port)
        return envelope(command=args.command, request_id=request_id, status="ok", payload={"schema_version": 1})
    if args.command == "start-runtime":
        _validate_runtime_ports(args.omlx_port, args.broker_port, args.memory_port)
        omlx_key, broker_token, memory_token = _runtime_secrets()
        herdr_executable = _installed_herdr_executable(
            args.root, args.upstreams, os_major=args.os_major, architecture=args.architecture,
        )
        herdr_spec = herdr_process_spec(
            executable=herdr_executable, root=args.root, session_name=HERDR_SESSION_NAME,
        )
        for path in (Path(herdr_spec.working_directory), Path(herdr_spec.environment["HOME"])):
            path.mkdir(parents=True, exist_ok=True)
        executable = _installed_omlx_executable(args.root)
        spec = omlx_process_spec(executable=executable, app_support=args.root, port=args.omlx_port)
        for path in (
            Path(spec.working_directory),
            Path(spec.environment["HOME"]),
            Path(spec.environment["TMPDIR"]),
        ):
            path.mkdir(parents=True, exist_ok=True)
        omlx_environment = dict(spec.environment)
        omlx_environment["OMLX_API_KEY"] = omlx_key
        broker_executable, broker_prefix = _supervisor_invocation()
        broker_arguments = [
            *broker_prefix, "--request-id", str(uuid.uuid4()), "internal-broker",
            "--root", str(args.root), "--omlx-port", str(args.omlx_port),
            "--broker-port", str(args.broker_port),
        ]
        runtime_home = args.root / "state/homes/broker"
        runtime_tmp = args.root / "state/runtime/broker/tmp"
        runtime_home.mkdir(parents=True, exist_ok=True)
        runtime_tmp.mkdir(parents=True, exist_ok=True)
        broker_environment = {
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(runtime_home),
            "TMPDIR": str(runtime_tmp),
            "NO_PROXY": "127.0.0.1,localhost,::1",
            "OMLX_API_KEY": omlx_key,
            "FORMA_AI_BROKER_TOKEN": broker_token,
        }
        embedding_route = load_approved_embedding_route(args.root)
        if embedding_route is None:
            memory_executable = broker_executable
            memory_arguments = [
                *broker_prefix, "--request-id", str(uuid.uuid4()), "internal-memory-service",
                "--root", str(args.root), "--memory-port", str(args.memory_port),
            ]
        else:
            semantica_status = SemanticaRuntimeInspector(SemanticaLayout(args.root)).status()
            if semantica_status.get("installation") != "verified":
                raise ValueError("approved embedding route requires verified managed Semantica")
            memory_executable = SemanticaLayout(args.root).python()
            memory_arguments = [
                str(_memory_runtime_entrypoint()), "--root", str(args.root),
                "--memory-port", str(args.memory_port), "--omlx-port", str(args.omlx_port),
                "--embedding-model", embedding_route.api_model,
                "--expected-dimension", str(embedding_route.expected_dimension),
                "--query-prefix", embedding_route.query_prefix,
                "--document-prefix", embedding_route.document_prefix,
            ]
        memory_home = args.root / "state/homes/memory"
        memory_tmp = args.root / "state/runtime/memory/tmp"
        memory_home.mkdir(parents=True, exist_ok=True)
        memory_tmp.mkdir(parents=True, exist_ok=True)
        memory_environment = {
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(memory_home),
            "TMPDIR": str(memory_tmp),
            "NO_PROXY": "127.0.0.1,localhost,::1",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "FORMA_AI_MEMORY_TOKEN": memory_token,
            "OMLX_API_KEY": omlx_key,
        }
        record = RuntimeManager(args.root).start(
            correlation_id=request_id,
            herdr={
                "executable": herdr_spec.executable,
                "arguments": herdr_spec.arguments,
                "environment": herdr_spec.environment,
                "working_directory": herdr_spec.working_directory,
                "log_path": args.root / "logs/herdr/server.log",
            },
            omlx={
                "executable": spec.executable,
                "arguments": spec.arguments,
                "environment": omlx_environment,
                "working_directory": spec.working_directory,
                "log_path": args.root / "logs/omlx/server.log",
            },
            broker={
                "executable": broker_executable,
                "arguments": broker_arguments,
                "environment": broker_environment,
                "working_directory": args.root / "state/runtime/broker",
                "log_path": args.root / "logs/broker/server.log",
            },
            memory={
                "executable": memory_executable,
                "arguments": memory_arguments,
                "environment": memory_environment,
                "working_directory": args.root / "state/runtime/memory",
                "log_path": args.root / "logs/memory/server.log",
            },
            herdr_probe=_herdr_probe(HERDR_SESSION_NAME),
            omlx_probe=lambda: _http_ready(args.omlx_port, omlx_key),
            broker_probe=lambda: _http_ready(args.broker_port, broker_token),
            memory_probe=lambda: _http_ready(args.memory_port, memory_token, "/live"),
            omlx_adopt=lambda: _adopt_omlx_server(
                args.omlx_port, args.root / "logs/omlx/server.log"
            ),
            timeout=90.0,
        )
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={"schema_version": 1, "runtime": asdict(record)},
        )
    if args.command == "sample-task":
        _, broker_token, _ = _runtime_secrets()
        status = RuntimeManager(args.root).status()
        if status["phase"] != "running":
            raise ValueError("runtime is not running")
        payload = _sample_task(args.broker_port, broker_token, request_id)
        return envelope(command=args.command, request_id=request_id, status="ok", payload=payload)
    if args.command == "local-task":
        if input_data is None:
            raise ValueError("local task body is required")
        _, broker_token, _ = _runtime_secrets()
        status = RuntimeManager(args.root).status()
        if status["phase"] != "running":
            raise ValueError("runtime is not running")
        task = parse_local_task(input_data)
        result = _local_task(args.broker_port, broker_token, request_id, task)
        return envelope(
            command=args.command, request_id=request_id, status="ok", payload=asdict(result),
        )
    if args.command == "installation-status":
        journal = LifecycleJournal(OMLXInstallLayout(args.root).operations)
        state = journal.load_optional()
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={
                "schema_version": 1,
                "component": "omlx",
                "operation": asdict(state) if state else None,
            },
        )
    if args.command in {"installation-plan", "install-omlx"}:
        if args.os_major < 15 or args.os_major > 99:
            raise ValueError("unsupported macOS major version")
        if not args.upstreams.is_absolute() or not args.upstreams.is_file():
            raise ValueError("upstream manifest must be an existing absolute file")
        expected = select_artifact(
            load_component(args.upstreams, "omlx"),
            platform="macos",
            os_major=args.os_major,
        )
        layout = OMLXInstallLayout(args.root)
        if args.command == "installation-plan":
            cached = layout.downloads / expected.name
            partial = layout.downloads / f"{expected.name}.part"
            cached_bytes = 0
            cached_verified = False
            cache_blocker = None
            if cached.is_file() and not cached.is_symlink():
                cached_verified = verify_file(cached, expected).valid
                if cached_verified:
                    cached_bytes = expected.size_bytes
                else:
                    cache_blocker = "DESTINATION_INVALID"
            partial_bytes = (
                partial.stat().st_size if partial.is_file() and not partial.is_symlink() else 0
            )
            active = _matches_active_bundle(layout, expected.release, expected.sha256)
            return envelope(
                command=args.command,
                request_id=request_id,
                status="ok",
                payload={
                    "schema_version": 1,
                    "component": "omlx",
                    "release": expected.release,
                    "artifact_name": expected.name,
                    "artifact_size_bytes": expected.size_bytes,
                    "artifact_sha256": expected.sha256,
                    "downloaded_bytes": min(max(cached_bytes, partial_bytes), expected.size_bytes),
                    "cached_artifact_verified": cached_verified,
                    "cache_blocker": cache_blocker,
                    "product_root": str(args.root),
                    "already_active": active,
                    "approval_required": True,
                },
            )
        if args.approve_artifact_sha256 != expected.sha256:
            raise ValueError("installation approval does not match selected artifact")
        installer = OMLXInstaller(
            layout,
            expected,
            downloader=ResumableDownloader(),
        )
        active = installer.run()
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={"schema_version": 1, "active": asdict(active)},
        )
    raise ValueError("unsupported command")


def _validate_product_root(root: Path) -> None:
    if not root.is_absolute():
        raise ValueError("product root must be absolute")
    resolved = root.resolve(strict=False)
    if resolved == Path("/") or resolved == Path.home() or root.is_symlink():
        raise ValueError("product root is unsafe")


def _catalog_ids(path: Path, collection: str) -> frozenset[str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw[collection]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("routing catalog is invalid") from exc
    if (
        raw.get("schema_version") != 1 or not isinstance(entries, list) or not entries
        or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in entries)
    ):
        raise ValueError("routing catalog is invalid")
    ids = frozenset(item["id"] for item in entries)
    if len(ids) != len(entries):
        raise ValueError("routing catalog contains duplicate identifiers")
    return ids


def _matches_active_bundle(layout: OMLXInstallLayout, release: str, digest: str) -> bool:
    if not layout.active_record.is_file() or layout.active_record.is_symlink():
        return False
    try:
        record = json.loads(layout.active_record.read_text(encoding="utf-8"))
        app = Path(record["app_path"])
        return (
            record.get("schema_version") == 1
            and record.get("component") == "omlx"
            and record.get("release") == release
            and record.get("artifact_sha256") == digest
            and app == layout.app(release)
            and app.is_dir()
            and not app.is_symlink()
        )
    except (KeyError, OSError, TypeError, json.JSONDecodeError):
        return False


def _validate_runtime_ports(omlx_port: int, broker_port: int, memory_port: int = 43111) -> None:
    ports = (omlx_port, broker_port, memory_port)
    if any(not 1024 <= port <= 65535 for port in ports) or len(set(ports)) != len(ports):
        raise ValueError("runtime ports must be unique unprivileged ports")


def _installed_omlx_executable(root: Path) -> Path:
    layout = OMLXInstallLayout(root)
    if not layout.active_record.is_file() or layout.active_record.is_symlink():
        raise ValueError("oMLX active record is missing or unsafe")
    try:
        record = json.loads(layout.active_record.read_text(encoding="utf-8"))
        release = record["release"]
        app = Path(record["app_path"])
    except (KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("oMLX active record is invalid") from exc
    if (
        record.get("schema_version") != 1
        or record.get("component") != "omlx"
        or not isinstance(release, str)
        or app != layout.app(release)
        or not app.is_dir()
        or app.is_symlink()
    ):
        raise ValueError("oMLX active bundle does not match the managed layout")
    executable = app / "Contents/MacOS/omlx-cli"
    if not executable.is_file() or executable.is_symlink() or not os.access(executable, os.X_OK):
        raise ValueError("oMLX runtime executable is missing or unsafe")
    return executable


def _installed_herdr_executable(
    root: Path, upstreams: Path, *, os_major: int, architecture: str,
) -> Path:
    """Resolve and re-verify the digest-pinned Herdr binary before every launch.

    Herdr has no app-bundle activation record (unlike oMLX); its manifest
    `install_mode` is `verified_release_binary`, so the cached download itself
    is re-hashed against `config/upstreams.json` on each resolution instead.
    """
    if not upstreams.is_absolute() or not upstreams.is_file():
        raise ValueError("upstream manifest must be an existing absolute file")
    expected = select_artifact(
        load_component(upstreams, "herdr"),
        platform="macos",
        os_major=os_major,
        architecture=architecture,
    )
    executable = OMLXInstallLayout(root).downloads / expected.name
    if not executable.is_file() or executable.is_symlink() or not os.access(executable, os.X_OK):
        raise ValueError("Herdr runtime executable is missing or unsafe")
    if not verify_file(executable, expected).valid:
        raise ValueError("Herdr runtime executable failed digest verification")
    return executable


def _runtime_secrets() -> tuple[str, str, str]:
    omlx_key, broker_token = _broker_secrets()
    memory_token = _memory_secret()
    secrets = (omlx_key, broker_token, memory_token)
    if len(set(secrets)) != 3:
        raise ValueError("distinct Keychain runtime secrets are required")
    return secrets


def _broker_secrets() -> tuple[str, str]:
    omlx_key = os.environ.get("OMLX_API_KEY", "")
    broker_token = os.environ.get("FORMA_AI_BROKER_TOKEN", "")
    if len(omlx_key) < 32 or len(broker_token) < 32 or omlx_key == broker_token:
        raise ValueError("distinct inference runtime secrets are required")
    return omlx_key, broker_token


def _memory_secret() -> str:
    memory_token = os.environ.get("FORMA_AI_MEMORY_TOKEN", "")
    if len(memory_token) < 32:
        raise ValueError("memory runtime secret is required")
    return memory_token


def _supervisor_invocation() -> tuple[Path, list[str]]:
    if getattr(sys, "frozen", False):
        return Path(sys.executable), []
    return Path(sys.executable), [str(REPOSITORY_ROOT / "scripts/supervisor.py")]


def _memory_runtime_entrypoint() -> Path:
    if getattr(sys, "frozen", False):
        candidate = Path(sys.executable).resolve().parent.parent / "MemoryRuntime/semantica_memory_runtime.py"
    else:
        candidate = REPOSITORY_ROOT / "scripts/semantica_memory_runtime.py"
    if not candidate.is_absolute() or not candidate.is_file() or candidate.is_symlink():
        raise ValueError("managed memory runtime entrypoint is missing or unsafe")
    return candidate


def _http_ready(port: int, token: str, path: str = "/health") -> bool:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=1.0) as response:
            body = json.loads(response.read(1024 * 1024))
            status = body.get("status", "")
            if path == "/live" and isinstance(body.get("result"), dict):
                status = body["result"].get("status", "")
            return response.status == 200 and str(status).lower() in {"ok", "healthy"}
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
        return False


def _herdr_probe(session_name: str) -> Callable[[], bool]:
    def probe() -> bool:
        socket_path = resolve_socket_path(environ={"HERDR_SESSION": session_name})
        try:
            HerdrSocketTransport(socket_path=socket_path, environ={}).probe()
            return True
        except (HerdrTransportError, HerdrProtocolError, OSError):
            return False

    return probe


def _adopt_omlx_server(port: int, log_path: Path):
    result = subprocess.run(
        ["/usr/sbin/lsof", "-nP", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"],
        capture_output=True,
        text=True,
        check=False,
    )
    pids = {line.strip() for line in result.stdout.splitlines() if line.strip().isdigit()}
    if result.returncode != 0 or len(pids) != 1:
        raise ValueError("oMLX listener identity is missing or ambiguous")
    return SubprocessController().adopt(
        role="omlx", pid=int(next(iter(pids))), command_prefix="omlx-server", log_path=log_path
    )


def _run_internal_broker(root: Path, omlx_port: int, broker_port: int) -> None:
    _validate_runtime_ports(omlx_port, broker_port)
    omlx_key, broker_token = _broker_secrets()
    broker = OMLXBroker(
        BrokerPolicy(client_token=broker_token, allowed_origins=frozenset()),
        OMLXUpstream(f"http://127.0.0.1:{omlx_port}", omlx_key, timeout=30.0),
        JsonlAuditSink(root / "logs/audit/inference.jsonl"),
    )
    server = create_server("127.0.0.1", broker_port, broker)
    try:
        server.serve_forever()
    finally:
        server.server_close()


class _UnavailableSemanticaBackend:
    def health(self) -> dict[str, str]:
        return {"status": "unavailable", "code": "EMBEDDING_ROUTE_UNVERIFIED"}

    def store(self, content: str, metadata: dict[str, Any]) -> str:
        raise RuntimeError("unavailable backend cannot store")

    def get(self, memory_id: str) -> None:
        return None

    def retrieve(self, query: str, limit: int) -> list[dict[str, Any]]:
        return []

    def forget(self, memory_id: str) -> bool:
        return False


def _run_internal_memory_service(root: Path, memory_port: int) -> None:
    if not 1024 <= memory_port <= 65535:
        raise ValueError("memory service port must be unprivileged")
    memory_token = _memory_secret()
    memory = GovernedMemory(root, _UnavailableSemanticaBackend())
    service = GovernedMemoryService(
        MemoryServicePolicy(memory_token),
        memory,
        JsonlAuditSink(root / "logs/audit/memory-service.jsonl"),
    )
    server = create_memory_server("127.0.0.1", memory_port, service)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _broker_request(port: int, token: str, path: str, correlation_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    encoded = json.dumps(body, separators=(",", ":")).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-Correlation-ID": correlation_id,
    }
    if encoded is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=encoded, headers=headers,
        method="POST" if encoded is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=35.0) as response:
        return json.loads(response.read(8_388_608))


def _sample_task(port: int, token: str, correlation_id: str) -> dict[str, Any]:
    models = _broker_request(port, token, "/v1/models", correlation_id)
    entries = models.get("data")
    if not isinstance(entries, list) or not entries or not isinstance(entries[0].get("id"), str):
        raise ValueError("broker returned no usable local model")
    model = entries[0]["id"]
    completion = _broker_request(
        port, token, "/v1/chat/completions", correlation_id,
        {
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly: LOCAL_AI_READY"}],
            "temperature": 0,
            "max_tokens": 16,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )
    try:
        content = completion["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("sample completion returned no text") from exc
    if not isinstance(content, str) or not content.strip():
        raise ValueError("sample completion returned empty text")
    return {
        "schema_version": 1,
        "correlation_id": correlation_id,
        "model": model,
        "output": content,
        "audit_path": "logs/audit/inference.jsonl",
    }


def _local_task(
    port: int, token: str, correlation_id: str, task: LocalTaskRequest,
    allowed_model_ids: frozenset[str] | None = None,
):
    models = _broker_request(port, token, "/v1/models", correlation_id)
    entries = models.get("data")
    if (
        not isinstance(entries, list) or not entries or not isinstance(entries[0], dict)
        or not isinstance(entries[0].get("id"), str)
    ):
        raise ValueError("broker returned no usable local model")
    model = entries[0]["id"]
    if allowed_model_ids is not None and model not in allowed_model_ids:
        raise ValueError("runtime model does not match the verified local profile")
    completion = _broker_request(
        port, token, "/v1/chat/completions", correlation_id,
        completion_body(task, model),
    )
    return normalize_local_result(
        completion, correlation_id=correlation_id, expected_model=model,
    )


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    command = next(
        (
            item
            for item in (
                "preflight", "installation-plan", "installation-status", "install-omlx",
                "model-plan", "link-model", "embedding-plan", "download-embedding",
                "activate-embedding",
                "runtime-status", "start-runtime", "stop-runtime", "sample-task", "local-task", "internal-broker",
                "internal-memory-service", "semantica-status",
                "cloud-preview", "cloud-approve", "cloud-reject", "cloud-execute",
                "cloud-settings", "set-cloud-settings",
                "task-submit",
            )
            if item in raw
        ),
        "unknown",
    )
    request_id = "invalid"
    if "--request-id" in raw:
        index = raw.index("--request-id") + 1
        if index < len(raw):
            request_id = raw[index]
    try:
        args = parser().parse_args(raw)
        input_data = None
        if args.command == "cloud-preview":
            input_data = sys.stdin.buffer.read(MAXIMUM_CLOUD_PAYLOAD_BYTES + 1)
        elif args.command == "local-task":
            input_data = sys.stdin.buffer.read(MAXIMUM_TASK_BYTES + 1)
        elif args.command == "task-submit":
            input_data = sys.stdin.buffer.read(MAXIMUM_UNIFIED_TASK_BYTES + 1)
        response = run(args, input_data=input_data)
        exit_code = 0
    except Exception as exc:
        response = envelope(
            command=command,
            request_id=request_id,
            status="error",
            error={
                "code": getattr(exc, "code", "SUPERVISOR_COMMAND_FAILED"),
                "message": "Supervisor command could not complete.",
            },
        )
        exit_code = 2
    print(json.dumps(response, ensure_ascii=False, separators=(",", ":")))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
