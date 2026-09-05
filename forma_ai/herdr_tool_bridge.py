"""Thin bridge from Herdr pane context to governed tool routing."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from forma_ai.broker import JsonlAuditSink
from forma_ai.mcp_client import MCPToolCallResult
from forma_ai.models import _atomic_json
from forma_ai.tool_registry import ToolRegistry
from forma_ai.tool_routing import (
    RegistryMCPCaller,
    ToolApprovalStore,
    ToolCapabilityRequest,
    ToolProposalStore,
    ToolRouter,
    ToolRoutingError,
)


@dataclass(frozen=True)
class ToolCallArtifact:
    schema_version: int
    correlation_id: str
    capability_id: str
    operation: str
    text: str
    is_error: bool
    artifact_path: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class HerdrToolBridge:
    def __init__(self, *, repository_root: Path) -> None:
        if not repository_root.is_absolute():
            raise ValueError("repository root must be absolute")
        self.repository_root = repository_root

    def call(
        self,
        *,
        product_root: Path,
        correlation_id: str,
        capability_id: str,
        operation: str,
        arguments: Mapping[str, Any],
        data_classes: frozenset[str],
        catalog_path: Path,
        local_paths: tuple[Path, ...] = (),
        workspace_dir: Path | None = None,
        now: datetime | None = None,
    ) -> ToolCallArtifact:
        _validate_product_root(product_root)
        if workspace_dir is not None:
            _validate_workspace_dir(workspace_dir)
        if not catalog_path.is_absolute() or not catalog_path.is_file():
            raise ValueError("tool routing catalog must be an existing absolute file")
        moment = now or datetime.now(timezone.utc)
        request = ToolCapabilityRequest(
            correlation_id=correlation_id,
            capability_id=capability_id,
            operation=operation,
            arguments=arguments,
            data_classes=data_classes,
        )
        audit = JsonlAuditSink(product_root / "logs/audit/tools.jsonl")
        registry = ToolRegistry(
            product_root,
            catalog_path=self.repository_root / "config/tool-packages.json",
            repository_root=self.repository_root,
            local_paths=local_paths,
        )
        approvals = ToolApprovalStore(product_root)
        router = ToolRouter(
            registry,
            catalog_path=catalog_path,
            approvals=approvals,
            audit=audit,
            caller=RegistryMCPCaller(),
        )
        decision = router.resolve(request)
        if decision.route in {"blocked", "tool_missing"}:
            return ToolCallArtifact(
                1,
                correlation_id,
                capability_id,
                operation,
                f"{decision.route}:{','.join(decision.reasons) or decision.route}",
                True,
                None,
            )
        proposals = ToolProposalStore(product_root)
        proposal = None
        retain_proposal = False
        try:
            retained = proposals.find_matching(request)
            if retained is None:
                proposal, payload, _preview = router.propose(request, now=moment)
                proposals.save(proposal, payload)
            else:
                proposal, payload = retained
            if proposal.approval_required and not approvals.has_record(proposal.proposal_id):
                retain_proposal = True
                return ToolCallArtifact(
                    1,
                    correlation_id,
                    capability_id,
                    operation,
                    f"TOOL_APPROVAL_REQUIRED:{proposal.proposal_id}",
                    True,
                    None,
                )
            result = router.execute(
                proposal,
                payload,
                arguments=dict(arguments),
                now=moment,
            )
        except ToolRoutingError as exc:
            return ToolCallArtifact(
                1,
                correlation_id,
                capability_id,
                operation,
                exc.code,
                True,
                None,
            )
        finally:
            if proposal is not None and not retain_proposal:
                proposals.discard(proposal.proposal_id)
        artifact = ToolCallArtifact(
            1,
            correlation_id,
            capability_id,
            operation,
            _extract_text(result),
            result.is_error,
            None,
        )
        if workspace_dir is not None:
            artifact = _write_workspace_artifact(workspace_dir, artifact)
        return artifact


def _extract_text(result: MCPToolCallResult) -> str:
    parts: list[str] = []
    for item in result.content:
        if item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    if parts:
        return "\n".join(parts)
    return json.dumps(list(result.content), ensure_ascii=False, separators=(",", ":"))


def _write_workspace_artifact(workspace_dir: Path, artifact: ToolCallArtifact) -> ToolCallArtifact:
    directory = workspace_dir / ".forma" / "tool-artifacts"
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    filename = f"{artifact.correlation_id}.json"
    path = directory / filename
    relative = str(path.relative_to(workspace_dir))
    stored = ToolCallArtifact(
        artifact.schema_version,
        artifact.correlation_id,
        artifact.capability_id,
        artifact.operation,
        artifact.text,
        artifact.is_error,
        relative,
    )
    _atomic_json(path, stored.to_dict())
    return stored


def _validate_product_root(root: Path) -> None:
    if not root.is_absolute():
        raise ValueError("product root must be absolute")
    resolved = root.resolve(strict=False)
    if resolved == Path("/") or resolved == Path.home() or root.is_symlink():
        raise ValueError("product root is unsafe")


def _validate_workspace_dir(path: Path) -> None:
    if not path.is_absolute():
        raise ValueError("workspace directory must be absolute")
    if not path.is_dir() or path.is_symlink():
        raise ValueError("workspace directory must be an existing directory")
