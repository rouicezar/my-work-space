"""Private persistence for pending cloud payloads between Supervisor invocations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path

from mac_ai_work_os.inference_routing import CloudEscalationProposal, CostEstimate
from mac_ai_work_os.models import _atomic_json


PROPOSAL_ID = re.compile(r"^[0-9a-f-]{36}$")


class CloudProposalError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class CloudProposalStore:
    def __init__(self, product_root: Path):
        if not product_root.is_absolute():
            raise CloudProposalError("PRODUCT_ROOT_INVALID", str(product_root))
        self.directory = product_root / "state/cloud-proposals"

    def save(self, proposal: CloudEscalationProposal, payload: bytes) -> None:
        if hashlib.sha256(payload).hexdigest() != proposal.payload_sha256:
            raise CloudProposalError("PROPOSAL_PAYLOAD_MISMATCH", proposal.proposal_id)
        if len(payload) != proposal.payload_size_bytes:
            raise CloudProposalError("PROPOSAL_PAYLOAD_MISMATCH", proposal.proposal_id)
        self._prepare_directory()
        metadata = self._metadata_path(proposal.proposal_id)
        body = self._payload_path(proposal.proposal_id)
        if metadata.exists() or metadata.is_symlink() or body.exists() or body.is_symlink():
            raise CloudProposalError("PROPOSAL_ALREADY_EXISTS", proposal.proposal_id)
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

    def load(self, proposal_id: str) -> tuple[CloudEscalationProposal, bytes]:
        self._validate_directory()
        metadata = self._metadata_path(proposal_id)
        body = self._payload_path(proposal_id)
        for path in (metadata, body):
            if not path.is_file() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077:
                raise CloudProposalError("PROPOSAL_UNAVAILABLE", proposal_id)
        try:
            raw = json.loads(metadata.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or not isinstance(raw.get("estimated_cost"), dict):
                raise TypeError("proposal metadata must be an object")
            estimate = CostEstimate(**raw.pop("estimated_cost"))
            for field in ("reason_codes", "data_classes", "redactions"):
                value = raw.get(field)
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    raise TypeError(f"{field} must be a string array")
                raw[field] = tuple(value)
            proposal = CloudEscalationProposal(**raw, estimated_cost=estimate)
            payload = body.read_bytes()
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CloudProposalError("PROPOSAL_INVALID", proposal_id) from exc
        if (
            proposal.schema_version != 1 or proposal.proposal_id != proposal_id
            or hashlib.sha256(payload).hexdigest() != proposal.payload_sha256
            or len(payload) != proposal.payload_size_bytes
        ):
            raise CloudProposalError("PROPOSAL_INVALID", proposal_id)
        return proposal, payload

    def delete_payload(self, proposal_id: str) -> None:
        path = self._payload_path(proposal_id)
        if path.is_symlink():
            raise CloudProposalError("PROPOSAL_PAYLOAD_UNSAFE", proposal_id)
        path.unlink(missing_ok=True)

    def reject(self, proposal_id: str) -> CloudEscalationProposal:
        proposal, _ = self.load(proposal_id)
        self.discard(proposal_id)
        return proposal

    def discard(self, proposal_id: str) -> None:
        self._validate_directory()
        metadata = self._metadata_path(proposal_id)
        payload = self._payload_path(proposal_id)
        if metadata.is_symlink() or payload.is_symlink():
            raise CloudProposalError("PROPOSAL_PATH_UNSAFE", proposal_id)
        payload.unlink(missing_ok=True)
        metadata.unlink(missing_ok=True)

    def _prepare_directory(self) -> None:
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self.directory.is_symlink() or not self.directory.is_dir():
            raise CloudProposalError("PROPOSAL_DIRECTORY_UNSAFE", str(self.directory))
        os.chmod(self.directory, 0o700)

    def _validate_directory(self) -> None:
        if (
            not self.directory.is_dir() or self.directory.is_symlink()
            or stat.S_IMODE(self.directory.stat().st_mode) & 0o077
        ):
            raise CloudProposalError("PROPOSAL_DIRECTORY_UNSAFE", str(self.directory))

    def _metadata_path(self, proposal_id: str) -> Path:
        self._validate_id(proposal_id)
        return self.directory / f"{proposal_id}.json"

    def _payload_path(self, proposal_id: str) -> Path:
        self._validate_id(proposal_id)
        return self.directory / f"{proposal_id}.payload"

    @staticmethod
    def _validate_id(proposal_id: str) -> None:
        if not PROPOSAL_ID.fullmatch(proposal_id) or Path(proposal_id).name != proposal_id:
            raise CloudProposalError("PROPOSAL_ID_INVALID", proposal_id)
