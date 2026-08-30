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
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import preflight
from mac_ai_work_os.artifacts import load_component, select_artifact, verify_file
from mac_ai_work_os.downloads import ResumableDownloader
from mac_ai_work_os.installer import OMLXInstallLayout, OMLXInstaller
from mac_ai_work_os.lifecycle import LifecycleJournal
from mac_ai_work_os.models import (
    huggingface_snapshot,
    link_external_model,
    load_model,
    verify_snapshot,
)
from mac_ai_work_os.model_downloads import download_model_snapshot
from mac_ai_work_os.broker import BrokerPolicy, JsonlAuditSink, OMLXBroker, OMLXUpstream, create_server
from mac_ai_work_os.processes import omlx_process_spec
from mac_ai_work_os.runtime import RuntimeManager, SubprocessController
from mac_ai_work_os.semantica_runtime import SemanticaLayout, SemanticaRuntimeInspector
from mac_ai_work_os.governed_memory import GovernedMemory
from mac_ai_work_os.embedding_config import activate_embedding_route, load_approved_embedding_route
from mac_ai_work_os.memory_service import (
    GovernedMemoryService,
    MemoryServicePolicy,
    create_memory_server,
)
from mac_ai_work_os.cloud_approval import CloudApprovalStore
from mac_ai_work_os.cloud_catalog import load_cloud_provider
from mac_ai_work_os.cloud_proposals import CloudProposalStore
from mac_ai_work_os.deepseek_adapter import DeepSeekAdapter
from mac_ai_work_os.inference_routing import TaskRequirements, create_cloud_proposal
from mac_ai_work_os.local_tasks import (
    MAXIMUM_TASK_BYTES, LocalTaskRequest, completion_body, normalize_local_result,
    parse_local_task,
)
from mac_ai_work_os.cloud_preferences import CloudPreferenceStore


SCHEMA_VERSION = 1
DEFAULT_UPSTREAMS = REPOSITORY_ROOT / "config/upstreams.json"
DEFAULT_MODELS = REPOSITORY_ROOT / "config/models.json"
DEFAULT_MODEL_ID = "qwen3-0.6b-4bit-alpha"
DEFAULT_EMBEDDING_MODEL_ID = "multilingual-e5-small-mlx-alpha"
DEFAULT_CLOUD_PROVIDERS = REPOSITORY_ROOT / "config/cloud-providers.json"
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
    return result


def validate_request_id(value: str) -> str:
    parsed = uuid.UUID(value)
    if str(parsed) != value.lower():
        raise ValueError("request ID must use canonical UUID form")
    return str(parsed)


def run(args: argparse.Namespace, input_data: bytes | None = None) -> dict[str, Any]:
    request_id = validate_request_id(args.request_id)
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
        api_key = os.environ.get("MAC_AI_WORK_OS_DEEPSEEK_API_KEY", "")
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
            "MAC_AI_WORK_OS_BROKER_TOKEN": broker_token,
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
            "MAC_AI_WORK_OS_MEMORY_TOKEN": memory_token,
            "OMLX_API_KEY": omlx_key,
        }
        record = RuntimeManager(args.root).start(
            correlation_id=request_id,
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


def _runtime_secrets() -> tuple[str, str, str]:
    omlx_key, broker_token = _broker_secrets()
    memory_token = _memory_secret()
    secrets = (omlx_key, broker_token, memory_token)
    if len(set(secrets)) != 3:
        raise ValueError("distinct Keychain runtime secrets are required")
    return secrets


def _broker_secrets() -> tuple[str, str]:
    omlx_key = os.environ.get("OMLX_API_KEY", "")
    broker_token = os.environ.get("MAC_AI_WORK_OS_BROKER_TOKEN", "")
    if len(omlx_key) < 32 or len(broker_token) < 32 or omlx_key == broker_token:
        raise ValueError("distinct inference runtime secrets are required")
    return omlx_key, broker_token


def _memory_secret() -> str:
    memory_token = os.environ.get("MAC_AI_WORK_OS_MEMORY_TOKEN", "")
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


def _local_task(port: int, token: str, correlation_id: str, task: LocalTaskRequest):
    models = _broker_request(port, token, "/v1/models", correlation_id)
    entries = models.get("data")
    if (
        not isinstance(entries, list) or not entries or not isinstance(entries[0], dict)
        or not isinstance(entries[0].get("id"), str)
    ):
        raise ValueError("broker returned no usable local model")
    model = entries[0]["id"]
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
