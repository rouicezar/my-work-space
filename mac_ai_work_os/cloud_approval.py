"""Private, expiring, one-shot approvals for exact cloud payloads."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mac_ai_work_os.inference_routing import CloudEscalationProposal
from mac_ai_work_os.models import _atomic_json


class CloudApprovalError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CloudApprovalRecord:
    schema_version: int
    proposal_id: str
    correlation_id: str
    provider_id: str
    model_id: str
    payload_sha256: str
    maximum_output_tokens: int
    maximum_cost_usd: float
    approved_at: str
    expires_at: str
    consumed_at: str | None


class CloudApprovalStore:
    def __init__(self, product_root: Path):
        if not product_root.is_absolute():
            raise CloudApprovalError("PRODUCT_ROOT_INVALID", str(product_root))
        self.directory = product_root / "state/cloud-approvals"

    def approve(
        self, proposal: CloudEscalationProposal, *, maximum_cost_usd: float,
        now: datetime, ttl_seconds: int = 300,
    ) -> CloudApprovalRecord:
        _aware(now)
        if (
            isinstance(maximum_cost_usd, bool) or not isinstance(maximum_cost_usd, (int, float))
            or maximum_cost_usd < proposal.estimated_cost.maximum
        ):
            raise CloudApprovalError("APPROVAL_COST_TOO_LOW", str(maximum_cost_usd))
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 600:
            raise CloudApprovalError("APPROVAL_TTL_INVALID", str(ttl_seconds))
        record = CloudApprovalRecord(
            1, proposal.proposal_id, proposal.correlation_id, proposal.provider_id,
            proposal.model_id, proposal.payload_sha256, proposal.maximum_output_tokens,
            float(maximum_cost_usd), now.astimezone(timezone.utc).isoformat(),
            (now.astimezone(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat(), None,
        )
        with self._lock():
            path = self._path(proposal.proposal_id)
            if path.exists() or path.is_symlink():
                raise CloudApprovalError("APPROVAL_ALREADY_EXISTS", proposal.proposal_id)
            _atomic_json(path, asdict(record))
        return record

    def consume(
        self, proposal: CloudEscalationProposal, payload: bytes, *, now: datetime,
    ) -> CloudApprovalRecord:
        _aware(now)
        with self._lock():
            record = self._load(proposal.proposal_id)
            if record.consumed_at is not None:
                raise CloudApprovalError("APPROVAL_ALREADY_CONSUMED", proposal.proposal_id)
            if now.astimezone(timezone.utc) > datetime.fromisoformat(record.expires_at):
                raise CloudApprovalError("APPROVAL_EXPIRED", proposal.proposal_id)
            binding = (
                record.correlation_id == proposal.correlation_id
                and record.provider_id == proposal.provider_id
                and record.model_id == proposal.model_id
                and record.payload_sha256 == proposal.payload_sha256
                and record.maximum_output_tokens == proposal.maximum_output_tokens
                and hashlib.sha256(payload).hexdigest() == record.payload_sha256
                and record.maximum_cost_usd >= proposal.estimated_cost.maximum
            )
            if not binding:
                raise CloudApprovalError("APPROVAL_BINDING_MISMATCH", proposal.proposal_id)
            consumed = CloudApprovalRecord(
                **{**asdict(record), "consumed_at": now.astimezone(timezone.utc).isoformat()}
            )
            _atomic_json(self._path(proposal.proposal_id), asdict(consumed))
            return consumed

    def _load(self, proposal_id: str) -> CloudApprovalRecord:
        path = self._path(proposal_id)
        if not path.is_file() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise CloudApprovalError("APPROVAL_UNAVAILABLE", proposal_id)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            record = CloudApprovalRecord(**raw)
            datetime.fromisoformat(record.approved_at)
            datetime.fromisoformat(record.expires_at)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CloudApprovalError("APPROVAL_INVALID", proposal_id) from exc
        if record.schema_version != 1 or record.proposal_id != proposal_id:
            raise CloudApprovalError("APPROVAL_INVALID", proposal_id)
        return record

    def _path(self, proposal_id: str) -> Path:
        if not proposal_id or Path(proposal_id).name != proposal_id:
            raise CloudApprovalError("PROPOSAL_ID_INVALID", proposal_id)
        return self.directory / f"{proposal_id}.json"

    def _lock(self):
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self.directory.is_symlink() or not self.directory.is_dir():
            raise CloudApprovalError("APPROVAL_DIRECTORY_UNSAFE", str(self.directory))
        os.chmod(self.directory, 0o700)
        path = self.directory / ".lock"
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        os.fchmod(descriptor, 0o600)
        handle = os.fdopen(descriptor, "r+")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle


def _aware(value: datetime) -> None:
    if value.tzinfo is None:
        raise CloudApprovalError("TIME_INVALID", "timezone-aware datetime required")
