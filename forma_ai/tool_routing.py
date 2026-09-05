"""Capability-to-tool resolution with approval, sandbox, and audit governance."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

from forma_ai.adapter_contract import AuditEnvelope, PolicyPreview
from forma_ai.broker import AuditSink
from forma_ai.mcp_client import MCPClient, MCPToolCallResult
from forma_ai.models import _atomic_json
from forma_ai.tool_registry import ToolInstallation, ToolRegistry


CORRELATION = re.compile(r"^[0-9a-f-]{36}$")
PROPOSAL_ID = re.compile(r"^[0-9a-f-]{36}$")
CAPABILITY_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
OPERATION = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SENSITIVITY = frozenset({"low", "high"})
BLOCKED_DATA_CLASSES = frozenset({"credentials", "regulated_secrets"})


class ToolRoutingError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ToolRouteRule:
    capability_id: str
    operation: str
    tool_id: str
    mcp_tool_name: str
    sensitivity: str
    sandbox_required: bool


@dataclass(frozen=True)
class ToolCapabilityRequest:
    correlation_id: str
    capability_id: str
    operation: str
    arguments: Mapping[str, Any]
    data_classes: frozenset[str]


@dataclass(frozen=True)
class ToolRouteDecision:
    route: str
    tool_id: str | None
    mcp_tool_name: str | None
    source: str | None
    reasons: tuple[str, ...]
    approval_required: bool
    sandbox_required: bool


@dataclass(frozen=True)
class ToolCallProposal:
    schema_version: int
    proposal_id: str
    correlation_id: str
    capability_id: str
    operation: str
    tool_id: str
    mcp_tool_name: str
    payload_sha256: str
    payload_size_bytes: int
    data_classes: tuple[str, ...]
    approval_required: bool
    sandbox_required: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ToolApprovalRecord:
    schema_version: int
    proposal_id: str
    correlation_id: str
    tool_id: str
    mcp_tool_name: str
    payload_sha256: str
    approved_at: str
    expires_at: str
    consumed_at: str | None


class ToolApprovalStore:
    def __init__(self, product_root: Path) -> None:
        if not product_root.is_absolute():
            raise ToolRoutingError("PRODUCT_ROOT_INVALID", str(product_root))
        self.directory = product_root / "state/tool-approvals"

    def approve(self, proposal: ToolCallProposal, *, now: datetime, ttl_seconds: int = 300) -> ToolApprovalRecord:
        _aware(now)
        if not proposal.approval_required:
            raise ToolRoutingError("TOOL_APPROVAL_NOT_REQUIRED", proposal.proposal_id)
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 600:
            raise ToolRoutingError("TOOL_APPROVAL_TTL_INVALID", str(ttl_seconds))
        record = ToolApprovalRecord(
            1,
            proposal.proposal_id,
            proposal.correlation_id,
            proposal.tool_id,
            proposal.mcp_tool_name,
            proposal.payload_sha256,
            now.astimezone(timezone.utc).isoformat(),
            (now.astimezone(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat(),
            None,
        )
        path = self._path(proposal.proposal_id)
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        if path.exists():
            raise ToolRoutingError("TOOL_APPROVAL_ALREADY_EXISTS", proposal.proposal_id)
        _atomic_json(path, asdict(record))
        return record

    def consume(self, proposal: ToolCallProposal, payload: bytes, *, now: datetime) -> ToolApprovalRecord:
        _aware(now)
        if not proposal.approval_required:
            return ToolApprovalRecord(
                1, proposal.proposal_id, proposal.correlation_id, proposal.tool_id,
                proposal.mcp_tool_name, proposal.payload_sha256,
                now.astimezone(timezone.utc).isoformat(),
                now.astimezone(timezone.utc).isoformat(),
                now.astimezone(timezone.utc).isoformat(),
            )
        path = self._path(proposal.proposal_id)
        if not path.is_file():
            raise ToolRoutingError("TOOL_APPROVAL_UNAVAILABLE", proposal.proposal_id)
        record = ToolApprovalRecord(**json.loads(path.read_text(encoding="utf-8")))
        if record.consumed_at is not None:
            raise ToolRoutingError("TOOL_APPROVAL_ALREADY_CONSUMED", proposal.proposal_id)
        if now.astimezone(timezone.utc) > datetime.fromisoformat(record.expires_at):
            raise ToolRoutingError("TOOL_APPROVAL_EXPIRED", proposal.proposal_id)
        binding = (
            record.correlation_id == proposal.correlation_id
            and record.tool_id == proposal.tool_id
            and record.mcp_tool_name == proposal.mcp_tool_name
            and record.payload_sha256 == proposal.payload_sha256
            and hashlib.sha256(payload).hexdigest() == proposal.payload_sha256
        )
        if not binding:
            raise ToolRoutingError("TOOL_APPROVAL_BINDING_MISMATCH", proposal.proposal_id)
        consumed = ToolApprovalRecord(**{**asdict(record), "consumed_at": now.astimezone(timezone.utc).isoformat()})
        _atomic_json(path, asdict(consumed))
        return consumed

    def has_record(self, proposal_id: str) -> bool:
        path = self._path(proposal_id)
        return path.is_file() and not path.is_symlink()

    def _path(self, proposal_id: str) -> Path:
        if not proposal_id or Path(proposal_id).name != proposal_id:
            raise ToolRoutingError("TOOL_PROPOSAL_ID_INVALID", proposal_id)
        return self.directory / f"{proposal_id}.json"


class MCPCaller(Protocol):
    def call_tool(
        self,
        installation: ToolInstallation,
        tool_name: str,
        arguments: Mapping[str, Any],
    ) -> MCPToolCallResult: ...


class RegistryMCPCaller:
    def call_tool(
        self,
        installation: ToolInstallation,
        tool_name: str,
        arguments: Mapping[str, Any],
    ) -> MCPToolCallResult:
        client = MCPClient.from_server_spec(installation.server_spec())
        try:
            client.connect()
            return client.call_tool(tool_name, arguments)
        finally:
            client.close()


class ToolProposalStore:
    def __init__(self, product_root: Path) -> None:
        if not product_root.is_absolute():
            raise ToolRoutingError("PRODUCT_ROOT_INVALID", str(product_root))
        self.directory = product_root / "state/tool-proposals"

    def save(self, proposal: ToolCallProposal, payload: bytes) -> None:
        if hashlib.sha256(payload).hexdigest() != proposal.payload_sha256:
            raise ToolRoutingError("TOOL_PROPOSAL_PAYLOAD_MISMATCH", proposal.proposal_id)
        if len(payload) != proposal.payload_size_bytes:
            raise ToolRoutingError("TOOL_PROPOSAL_PAYLOAD_MISMATCH", proposal.proposal_id)
        self._prepare_directory()
        metadata = self._metadata_path(proposal.proposal_id)
        body = self._payload_path(proposal.proposal_id)
        if metadata.exists() or metadata.is_symlink() or body.exists() or body.is_symlink():
            raise ToolRoutingError("TOOL_PROPOSAL_ALREADY_EXISTS", proposal.proposal_id)
        descriptor, name = tempfile.mkstemp(prefix=".payload-", dir=self.directory)
        temporary = Path(name)
        os.fchmod(descriptor, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, body)
            try:
                _atomic_json(metadata, proposal.to_dict())
            except Exception:
                body.unlink(missing_ok=True)
                raise
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def load(self, proposal_id: str) -> tuple[ToolCallProposal, bytes]:
        self._validate_directory()
        metadata = self._metadata_path(proposal_id)
        body = self._payload_path(proposal_id)
        for path in (metadata, body):
            if not path.is_file() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077:
                raise ToolRoutingError("TOOL_PROPOSAL_UNAVAILABLE", proposal_id)
        try:
            raw = json.loads(metadata.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise TypeError("proposal metadata must be an object")
            data_classes = raw.get("data_classes")
            if not isinstance(data_classes, list) or not all(isinstance(item, str) for item in data_classes):
                raise TypeError("data_classes must be a string array")
            raw["data_classes"] = tuple(data_classes)
            proposal = ToolCallProposal(**raw)
            payload = body.read_bytes()
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ToolRoutingError("TOOL_PROPOSAL_INVALID", proposal_id) from exc
        if (
            proposal.schema_version != 1
            or proposal.proposal_id != proposal_id
            or hashlib.sha256(payload).hexdigest() != proposal.payload_sha256
            or len(payload) != proposal.payload_size_bytes
        ):
            raise ToolRoutingError("TOOL_PROPOSAL_INVALID", proposal_id)
        return proposal, payload

    def find_matching(
        self,
        request: ToolCapabilityRequest,
    ) -> tuple[ToolCallProposal, bytes] | None:
        if not self.directory.exists():
            return None
        self._validate_directory()
        matches: list[tuple[ToolCallProposal, bytes]] = []
        for metadata in sorted(self.directory.glob("*.json")):
            proposal, payload = self.load(metadata.stem)
            if (
                proposal.correlation_id != request.correlation_id
                or proposal.capability_id != request.capability_id
                or proposal.operation != request.operation
                or proposal.data_classes != tuple(sorted(request.data_classes))
            ):
                continue
            try:
                body = json.loads(payload)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ToolRoutingError("TOOL_PROPOSAL_INVALID", proposal.proposal_id) from exc
            if body.get("arguments") == dict(request.arguments):
                matches.append((proposal, payload))
        if len(matches) > 1:
            raise ToolRoutingError("TOOL_PROPOSAL_AMBIGUOUS", request.correlation_id)
        return matches[0] if matches else None

    def discard(self, proposal_id: str) -> None:
        self._validate_directory()
        metadata = self._metadata_path(proposal_id)
        payload = self._payload_path(proposal_id)
        if metadata.is_symlink() or payload.is_symlink():
            raise ToolRoutingError("TOOL_PROPOSAL_PATH_UNSAFE", proposal_id)
        payload.unlink(missing_ok=True)
        metadata.unlink(missing_ok=True)

    def _prepare_directory(self) -> None:
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self.directory.is_symlink() or not self.directory.is_dir():
            raise ToolRoutingError("TOOL_PROPOSAL_DIRECTORY_UNSAFE", str(self.directory))
        os.chmod(self.directory, 0o700)

    def _validate_directory(self) -> None:
        if (
            not self.directory.is_dir()
            or self.directory.is_symlink()
            or stat.S_IMODE(self.directory.stat().st_mode) & 0o077
        ):
            raise ToolRoutingError("TOOL_PROPOSAL_DIRECTORY_UNSAFE", str(self.directory))

    def _metadata_path(self, proposal_id: str) -> Path:
        self._validate_id(proposal_id)
        return self.directory / f"{proposal_id}.json"

    def _payload_path(self, proposal_id: str) -> Path:
        self._validate_id(proposal_id)
        return self.directory / f"{proposal_id}.payload"

    @staticmethod
    def _validate_id(proposal_id: str) -> None:
        if not PROPOSAL_ID.fullmatch(proposal_id) or Path(proposal_id).name != proposal_id:
            raise ToolRoutingError("TOOL_PROPOSAL_ID_INVALID", proposal_id)


class ToolRouter:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        catalog_path: Path,
        approvals: ToolApprovalStore,
        audit: AuditSink,
        caller: MCPCaller | None = None,
    ) -> None:
        self.registry = registry
        self.catalog_path = catalog_path
        self.approvals = approvals
        self.audit = audit
        self.caller = caller

    def resolve(self, request: ToolCapabilityRequest) -> ToolRouteDecision:
        _validate_request(request)
        if request.data_classes & BLOCKED_DATA_CLASSES:
            return ToolRouteDecision(
                "blocked", None, None, None, ("blocked_data_class",), True, True,
            )
        rule = _find_rule(self.catalog_path, request.capability_id, request.operation)
        installation = _find_installation(self.registry.discover(), rule.tool_id)
        if installation is None:
            return ToolRouteDecision(
                "tool_missing", rule.tool_id, rule.mcp_tool_name, None, ("tool_not_installed",),
                rule.sensitivity == "high", rule.sandbox_required,
            )
        approval_required = rule.sensitivity == "high" or "external_write" in request.data_classes
        route = "approval_required" if approval_required else "ready"
        return ToolRouteDecision(
            route, installation.tool_id, rule.mcp_tool_name, installation.source, (),
            approval_required, rule.sandbox_required,
        )

    def propose(self, request: ToolCapabilityRequest, *, now: datetime) -> tuple[ToolCallProposal, bytes, PolicyPreview]:
        decision = self.resolve(request)
        if decision.route == "blocked":
            raise ToolRoutingError("TOOL_ROUTE_BLOCKED", decision.reasons[0])
        if decision.route == "tool_missing":
            raise ToolRoutingError("TOOL_NOT_INSTALLED", decision.tool_id or "")
        payload = json.dumps(
            {"tool_id": decision.tool_id, "mcp_tool_name": decision.mcp_tool_name, "arguments": dict(request.arguments)},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        proposal = ToolCallProposal(
            1,
            str(uuid.uuid4()),
            request.correlation_id,
            request.capability_id,
            request.operation,
            decision.tool_id or "",
            decision.mcp_tool_name or "",
            hashlib.sha256(payload).hexdigest(),
            len(payload),
            tuple(sorted(request.data_classes)),
            decision.approval_required,
            decision.sandbox_required,
        )
        preview = PolicyPreview(
            request.correlation_id,
            f"tool.call/{decision.mcp_tool_name}",
            tuple(sorted(request.data_classes)),
            external_write=decision.approval_required,
            approval_required=decision.approval_required,
            payload_sha256=proposal.payload_sha256,
        )
        self.audit.record({
            "schema_version": 1,
            "event": "tool_route_proposed",
            "correlation_id": request.correlation_id,
            "proposal_id": proposal.proposal_id,
            "tool_id": proposal.tool_id,
            "mcp_tool_name": proposal.mcp_tool_name,
            "approval_required": proposal.approval_required,
            "sandbox_required": proposal.sandbox_required,
            "payload_sha256": proposal.payload_sha256,
            "payload_size_bytes": proposal.payload_size_bytes,
            "proposed_at": now.astimezone(timezone.utc).isoformat(),
        })
        return proposal, payload, preview

    def execute(
        self,
        proposal: ToolCallProposal,
        payload: bytes,
        *,
        arguments: Mapping[str, Any],
        now: datetime,
    ) -> MCPToolCallResult:
        if self.caller is None:
            raise ToolRoutingError("TOOL_CALLER_UNAVAILABLE", proposal.proposal_id)
        outcome = "failed"
        error_code: str | None = None
        try:
            self.approvals.consume(proposal, payload, now=now)
            installation = self.registry.get(proposal.tool_id)
            if proposal.sandbox_required and installation.source == "local":
                raise ToolRoutingError("TOOL_SANDBOX_REQUIRED", proposal.tool_id)
            result = self.caller.call_tool(installation, proposal.mcp_tool_name, arguments)
            outcome = "completed" if not result.is_error else "failed"
            if result.is_error:
                error_code = "TOOL_CALL_ERROR"
            return result
        except ToolRoutingError as exc:
            error_code = exc.code
            raise
        finally:
            envelope = AuditEnvelope(
                str(uuid.uuid4()),
                proposal.correlation_id,
                f"tool.call/{proposal.mcp_tool_name}",
                outcome,
                now.astimezone(timezone.utc).isoformat(),
                ("arguments", "payload"),
            )
            self.audit.record({
                "schema_version": 1,
                "event": "tool_call",
                **envelope.to_dict(),
                "proposal_id": proposal.proposal_id,
                "tool_id": proposal.tool_id,
                "mcp_tool_name": proposal.mcp_tool_name,
                "payload_sha256": proposal.payload_sha256,
                "approval_required": proposal.approval_required,
                "sandbox_required": proposal.sandbox_required,
                "error_code": error_code,
            })


def load_tool_routes(path: Path) -> tuple[ToolRouteRule, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ToolRoutingError("TOOL_ROUTE_CATALOG_INVALID", "schema")
    rules: list[ToolRouteRule] = []
    for item in data.get("routes", []):
        capability_id = str(item.get("capability_id", ""))
        operation = str(item.get("operation", ""))
        tool_id = str(item.get("tool_id", ""))
        mcp_tool_name = str(item.get("mcp_tool_name", ""))
        sensitivity = str(item.get("sensitivity", ""))
        sandbox_required = item.get("sandbox_required", False)
        if (
            not CAPABILITY_ID.fullmatch(capability_id)
            or not OPERATION.fullmatch(operation)
            or not tool_id
            or not mcp_tool_name
            or sensitivity not in SENSITIVITY
            or not isinstance(sandbox_required, bool)
        ):
            raise ToolRoutingError("TOOL_ROUTE_CATALOG_INVALID", f"{capability_id}/{operation}")
        rules.append(
            ToolRouteRule(
                capability_id, operation, tool_id, mcp_tool_name, sensitivity, sandbox_required,
            )
        )
    return tuple(rules)


def _find_rule(catalog_path: Path, capability_id: str, operation: str) -> ToolRouteRule:
    for rule in load_tool_routes(catalog_path):
        if rule.capability_id == capability_id and rule.operation == operation:
            return rule
    raise ToolRoutingError("TOOL_ROUTE_NOT_FOUND", f"{capability_id}/{operation}")


def _find_installation(installations: tuple[ToolInstallation, ...], tool_id: str) -> ToolInstallation | None:
    for installation in installations:
        if installation.tool_id == tool_id:
            return installation
    return None


def _validate_request(request: ToolCapabilityRequest) -> None:
    if not CORRELATION.fullmatch(request.correlation_id):
        raise ToolRoutingError("TOOL_CORRELATION_INVALID", request.correlation_id)
    if not CAPABILITY_ID.fullmatch(request.capability_id):
        raise ToolRoutingError("TOOL_CAPABILITY_INVALID", request.capability_id)
    if not OPERATION.fullmatch(request.operation):
        raise ToolRoutingError("TOOL_OPERATION_INVALID", request.operation)


def _aware(value: datetime) -> None:
    if value.tzinfo is None:
        raise ToolRoutingError("TIME_INVALID", "naive datetime")
