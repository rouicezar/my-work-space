"""Prove governed memory workflow through pinned Semantica and governance layers."""

from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from forma_ai.governed_memory import GovernedMemory, MemoryGovernanceError, SourceReference
from forma_ai.semantica_runtime import SemanticaLayout, SemanticaRuntimeInspector, Runner


WORKER_ENV_ROOT = "FORMA_MEMORY_PROOF_ROOT"


def evaluate_proof_payload(payload: dict[str, Any]) -> dict[str, Any]:
    required = (
        "confirmed_record_id",
        "semantica_id",
        "retrieved",
        "conflict_detected",
        "corrected_record_id",
        "corrected_version",
        "exported_count",
        "deleted",
        "restarted_retrieve_empty",
        "restarted_export_empty",
        "history_versions",
    )
    missing = [field for field in required if field not in payload]
    if missing:
        return {"status": "proof_failed", "reason": "worker_payload_incomplete", "missing": missing}
    if not payload.get("confirmed_record_id") or not payload.get("semantica_id"):
        return {"status": "proof_failed", "reason": "confirm_failed"}
    if not payload.get("retrieved"):
        return {"status": "proof_failed", "reason": "retrieve_failed"}
    if not payload.get("conflict_detected"):
        return {"status": "proof_failed", "reason": "conflict_not_detected"}
    if payload.get("corrected_version") != 2 or not payload.get("corrected_record_id"):
        return {"status": "proof_failed", "reason": "correction_failed"}
    if payload.get("exported_count") != 1:
        return {"status": "proof_failed", "reason": "export_failed"}
    if not payload.get("deleted"):
        return {"status": "proof_failed", "reason": "delete_failed"}
    if not payload.get("restarted_retrieve_empty") or not payload.get("restarted_export_empty"):
        return {"status": "proof_failed", "reason": "restart_failed"}
    if payload.get("history_versions") != [1, 2]:
        return {"status": "proof_failed", "reason": "history_failed"}
    if payload.get("provenance_preserved") is False:
        return {"status": "proof_failed", "reason": "provenance_not_preserved"}
    return {
        "status": "proof_passed",
        "reason": None,
        "confirmed_record_id": payload.get("confirmed_record_id"),
        "semantica_id": payload.get("semantica_id"),
        "corrected_record_id": payload.get("corrected_record_id"),
    }


def run_governed_memory_cycle(product_root: Path) -> dict[str, Any]:
    """Run the full governed workflow inline (requires importable Semantica)."""
    from semantica.context import AgentContext

    from forma_ai.adapters.semantica import SemanticaContextBackend
    from forma_ai.semantica_fixture_boundary import (
        ExplicitLocalEmbeddingClient,
        FixturePersistentVectorStore,
    )

    source = SourceReference("proof://fixture/1", "2026-08-30T00:00:00+00:00", "sha256:proof")
    vector_path = product_root / "data/semantica/vector-index.sqlite3"
    state_path = product_root / "data/semantica/context"

    def build_memory() -> tuple[GovernedMemory, SemanticaContextBackend]:
        client = ExplicitLocalEmbeddingClient()
        vector = FixturePersistentVectorStore(vector_path, client)
        context = AgentContext(
            vector_store=vector,
            knowledge_graph=None,
            retention_days=None,
            graph_expansion=False,
            decision_tracking=False,
        )
        backend = SemanticaContextBackend(
            context,
            embedding_route="fixture-local",
            semantic_store=vector,
            state_path=state_path,
        )
        return GovernedMemory(product_root, backend), backend

    memory, backend = build_memory()
    candidate = memory.propose(
        claim_key="proof.region.capital",
        content="Alpha Harbor is the proof capital",
        sources=[source],
        correlation_id="proof-run-1",
        actor="proof-user",
    )
    confirmed = memory.confirm(candidate.candidate_id, actor="proof-reviewer", correlation_id="proof-run-2")
    retrieved = memory.retrieve("proof capital", 5)
    retrieved_ok = bool(retrieved and retrieved[0].record_id == confirmed.record_id)

    conflict = memory.propose(
        claim_key="proof.region.capital",
        content="Beta Harbor is the proof capital",
        sources=[source],
        correlation_id="proof-run-3",
        actor="proof-user",
    )
    conflict_detected = False
    try:
        memory.confirm(conflict.candidate_id, actor="proof-reviewer", correlation_id="proof-run-4")
    except MemoryGovernanceError as exc:
        conflict_detected = exc.code == "MEMORY_CONFLICT"
    conflict_row = memory.get_candidate(conflict.candidate_id)
    conflict_detected = conflict_detected and conflict_row is not None and conflict_row.status == "conflict"

    corrected = memory.correct(
        confirmed.record_id,
        content="Alpha Harbor remains the proof capital",
        sources=[source],
        actor="proof-reviewer",
        correlation_id="proof-run-5",
    )
    exported = memory.export()
    exported_count = len(exported.get("records", []))
    provenance_ok = False
    if exported_count == 1:
        record = exported["records"][0]
        upstream = backend.get(record["semantica_id"])
        provenance_ok = bool(
            upstream is not None
            and upstream.get("metadata", {}).get("record_id") == corrected.record_id
            and upstream.get("metadata", {}).get("version") == 2
            and record.get("sources")
        )

    memory.delete(corrected.record_id, actor="proof-reviewer", correlation_id="proof-run-6")
    deleted = memory.get(corrected.record_id) is None and memory.retrieve("proof capital", 5) == []

    restarted, _ = build_memory()
    restarted_retrieve_empty = restarted.retrieve("proof capital", 5) == []
    restarted_export_empty = restarted.export()["records"] == []
    history_versions = [item["version"] for item in restarted.history("proof.region.capital")]

    return {
        "confirmed_record_id": confirmed.record_id,
        "semantica_id": confirmed.semantica_id,
        "retrieved": retrieved_ok,
        "conflict_detected": conflict_detected,
        "corrected_record_id": corrected.record_id,
        "corrected_version": corrected.version,
        "exported_count": exported_count,
        "provenance_preserved": provenance_ok,
        "deleted": deleted,
        "restarted_retrieve_empty": restarted_retrieve_empty,
        "restarted_export_empty": restarted_export_empty,
        "history_versions": history_versions,
    }


def _worker_script() -> str:
    return textwrap.dedent(
        """
        import json
        import os
        import sys
        from pathlib import Path

        sys.path.insert(0, os.environ[__REPO_ROOT__])
        from forma_ai.governed_memory_proof import run_governed_memory_cycle

        root = Path(os.environ[__WORK_ROOT__])
        print(json.dumps(run_governed_memory_cycle(root)))
        """
    ).replace("__REPO_ROOT__", repr("FORMA_AI_REPOSITORY_ROOT")).replace(
        "__WORK_ROOT__", repr(WORKER_ENV_ROOT)
    )


def run_governed_memory_proof(
    product_root: Path,
    *,
    work_root: Path | None = None,
    runner: Runner = subprocess.run,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    if not product_root.is_absolute():
        return {
            "schema_version": 1,
            "component": "governed_memory",
            "status": "proof_failed",
            "reason": "product_root_not_absolute",
        }
    layout = SemanticaLayout(product_root)
    inspector = SemanticaRuntimeInspector(layout, runner=runner).status()
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "component": "governed_memory",
        "installation": inspector.get("installation"),
        "managed_python": str(layout.python()),
    }
    if inspector.get("installation") != "verified":
        evidence.update(
            {
                "status": "proof_failed",
                "reason": "installation_not_verified",
                "code": inspector.get("code"),
            }
        )
        return evidence

    repo_root = repository_root or Path(__file__).resolve().parents[1]
    cycle_root = work_root or product_root
    environment = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(cycle_root / "state/homes/governed-memory-proof"),
        "TMPDIR": str(cycle_root / "state/runtime/governed-memory-proof"),
        "NO_PROXY": "127.0.0.1,localhost,::1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "FORMA_AI_REPOSITORY_ROOT": str(repo_root),
        WORKER_ENV_ROOT: str(cycle_root),
    }
    with tempfile.TemporaryDirectory(prefix="governed-memory-proof-") as temporary:
        worker_path = Path(temporary) / "governed_memory_proof_worker.py"
        worker_path.write_text(_worker_script(), encoding="utf-8")
        python = layout.python()
        try:
            result = runner(
                [str(python), "-I", str(worker_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=120.0,
                env=environment,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            evidence.update(
                {
                    "status": "proof_failed",
                    "reason": "worker_failed",
                    "error_type": type(exc).__name__,
                }
            )
            return evidence
        if result.returncode != 0:
            evidence.update(
                {
                    "status": "proof_failed",
                    "reason": "worker_nonzero_exit",
                    "worker_code": result.returncode,
                }
            )
            return evidence
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            evidence.update({"status": "proof_failed", "reason": "worker_invalid_json"})
            return evidence

    evaluated = evaluate_proof_payload(payload)
    evidence.update(evaluated)
    return evidence
