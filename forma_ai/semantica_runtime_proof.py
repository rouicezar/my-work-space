"""Prove managed Semantica runtime lifecycle without leaking secrets."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Callable

from forma_ai.omlx_embeddings import EmbeddingError, OMLXEmbeddingClient
from forma_ai.semantica_runtime import SemanticaLayout, SemanticaRuntimeInspector, Runner


WORKER_ENV_WORK_DIR = "FORMA_SEMANTICA_PROOF_WORK_DIR"
WORKER_ENV_MODE = "FORMA_SEMANTICA_PROOF_MODE"
WORKER_ENV_OMLX_PORT = "FORMA_SEMANTICA_PROOF_OMLX_PORT"
WORKER_ENV_EMBEDDING_MODEL = "FORMA_SEMANTICA_PROOF_EMBEDDING_MODEL"
WORKER_ENV_EXPECTED_DIMENSION = "FORMA_SEMANTICA_PROOF_EXPECTED_DIMENSION"
WORKER_ENV_PRODUCT_ROOT = "FORMA_SEMANTICA_PROOF_PRODUCT_ROOT"


def evaluate_worker_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Reduce worker JSON to honest proof evidence (pure/testable)."""
    required = ("store_id", "retrieved", "reloaded", "forgotten")
    missing = [field for field in required if field not in payload]
    if missing:
        return {
            "status": "proof_failed",
            "reason": "worker_payload_incomplete",
            "missing": missing,
        }
    if not payload.get("store_id"):
        return {"status": "proof_failed", "reason": "store_failed"}
    if not payload.get("retrieved"):
        return {"status": "proof_failed", "reason": "retrieve_failed"}
    if not payload.get("reloaded"):
        return {"status": "proof_failed", "reason": "reload_failed"}
    if not payload.get("forgotten"):
        return {"status": "proof_failed", "reason": "forget_failed"}
    return {
        "status": "proof_passed",
        "reason": None,
        "embedding_mode": payload.get("embedding_mode"),
        "memory_id": payload.get("store_id"),
    }


def probe_omlx_embedding_route(
    *,
    port: int,
    api_key: str,
    embedding_model: str,
    expected_dimension: int | None = None,
) -> dict[str, Any]:
    try:
        client = OMLXEmbeddingClient(
            port=port,
            api_key=api_key,
            model=embedding_model,
            expected_dimension=expected_dimension,
        )
        return client.probe()
    except (EmbeddingError, ValueError) as exc:
        code = exc.code if isinstance(exc, EmbeddingError) else "EMBEDDING_ROUTE_INVALID"
        return {"status": "unavailable", "code": code}


def _worker_script() -> str:
    return textwrap.dedent(
        """
        import json
        import os
        from pathlib import Path

        import numpy as np
        from semantica.context import AgentContext

        work_dir = Path(os.environ[__WORK_DIR__])
        mode = os.environ[__MODE__]
        work_dir.mkdir(parents=True, exist_ok=True)
        state_dir = work_dir / "state"
        vector_path = work_dir / "vectors.sqlite3"

        class ExplicitLocalVectorBoundary:
            def __init__(self):
                self.items = {}
                self.next_id = 0

            def embed(self, text):
                encoded = text.encode("utf-8")
                buckets = [0.0] * 8
                for index, value in enumerate(encoded):
                    buckets[index % 8] += value / 255.0
                return np.array(buckets, dtype=np.float32)

            def store_vectors(self, vectors, metadata):
                identities = []
                for vector, item_metadata in zip(vectors, metadata):
                    self.next_id += 1
                    identity = f"vector-{self.next_id}"
                    self.items[identity] = {
                        "vector": np.asarray(vector),
                        "metadata": dict(item_metadata),
                    }
                    identities.append(identity)
                return identities

            def search_vectors(self, query_vector, k):
                query = np.asarray(query_vector)
                ranked = []
                for identity, item in self.items.items():
                    score = float(np.dot(query, item["vector"]))
                    ranked.append(
                        {"id": identity, "score": score, "metadata": item["metadata"]}
                    )
                return sorted(ranked, key=lambda item: item["score"], reverse=True)[:k]

            def delete_vectors(self, identities):
                for identity in identities:
                    self.items.pop(identity, None)
                return True

            def save(self, path):
                Path(path).mkdir(parents=True, exist_ok=True)

            def load(self, path):
                return None

            def health(self, probe=False):
                return {
                    "status": "healthy",
                    "model": "fixture-local",
                    "dimension": 8,
                    "vector_count": len(self.items),
                }

        def build_vector_store():
            if mode == "omlx":
                product_root = Path(os.environ[__PRODUCT_ROOT__])
                from forma_ai.omlx_embeddings import OMLXEmbeddingClient, PersistentOMLXVectorStore

                client = OMLXEmbeddingClient(
                    port=int(os.environ[__OMLX_PORT__]),
                    api_key=os.environ["OMLX_API_KEY"],
                    model=os.environ[__EMBEDDING_MODEL__],
                    expected_dimension=int(os.environ[__EXPECTED_DIMENSION__])
                    if os.environ.get(__EXPECTED_DIMENSION__)
                    else None,
                )
                return PersistentOMLXVectorStore(
                    product_root / "data/semantica/proof-vector-index.sqlite3",
                    client,
                ), "omlx"
            return ExplicitLocalVectorBoundary(), "fixture"

        def run_cycle(vector_store, embedding_mode):
            context = AgentContext(
                vector_store=vector_store,
                knowledge_graph=None,
                retention_days=None,
                graph_expansion=False,
                decision_tracking=False,
            )
            metadata = {
                "schema_version": 1,
                "record_id": "proof-record-1",
                "claim_key": "proof.capital",
                "status": "confirmed",
                "version": 1,
                "correlation_id": "semantica-proof-1",
                "sources": [
                    {
                        "uri": "proof://fixture/1",
                        "observed_at": "2026-08-30T00:00:00+00:00",
                    }
                ],
            }
            memory_id = context.store(
                "Alpha Harbor is the proof capital",
                metadata=metadata,
                extract_entities=False,
                extract_relationships=False,
                auto_extract=False,
            )
            state_dir.mkdir(parents=True, exist_ok=True)
            context.save(str(state_dir))
            retrieved = False
            for item in vector_store.search_vectors(vector_store.embed("proof capital"), k=5):
                item_metadata = item.get("metadata", {})
                if item_metadata.get("record_id") == "proof-record-1":
                    retrieved = True
                    break
            restored_store, _ = build_vector_store()
            restored = AgentContext(
                vector_store=restored_store,
                knowledge_graph=None,
                retention_days=None,
                graph_expansion=False,
                decision_tracking=False,
            )
            restored.load(str(state_dir))
            reloaded = restored.get_memory(memory_id) is not None
            forgotten = restored.forget(memory_id=memory_id) == 1
            return {
                "store_id": memory_id,
                "retrieved": retrieved,
                "reloaded": reloaded,
                "forgotten": forgotten,
                "embedding_mode": embedding_mode,
            }

        vector_store, embedding_mode = build_vector_store()
        print(json.dumps(run_cycle(vector_store, embedding_mode)))
        """
    ).replace("__WORK_DIR__", repr(WORKER_ENV_WORK_DIR)).replace(
        "__MODE__", repr(WORKER_ENV_MODE)
    ).replace("__PRODUCT_ROOT__", repr(WORKER_ENV_PRODUCT_ROOT)).replace(
        "__OMLX_PORT__", repr(WORKER_ENV_OMLX_PORT)
    ).replace("__EMBEDDING_MODEL__", repr(WORKER_ENV_EMBEDDING_MODEL)).replace(
        "__EXPECTED_DIMENSION__", repr(WORKER_ENV_EXPECTED_DIMENSION)
    )


def _probe_environment(layout: SemanticaLayout) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(layout.root / "state" / "homes" / "semantica-proof"),
        "TMPDIR": str(layout.root / "state" / "runtime" / "semantica" / "proof"),
        "NO_PROXY": "127.0.0.1,localhost,::1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    }


def run_semantica_runtime_proof(
    product_root: Path,
    *,
    omlx_port: int | None = None,
    omlx_api_key: str | None = None,
    embedding_model: str | None = None,
    expected_dimension: int | None = None,
    runner: Runner = subprocess.run,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    if not product_root.is_absolute():
        return {
            "schema_version": 1,
            "component": "semantica",
            "status": "proof_failed",
            "reason": "product_root_not_absolute",
        }
    layout = SemanticaLayout(product_root)
    inspector_status = SemanticaRuntimeInspector(layout, runner=runner).status()
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "component": "semantica",
        "installation": inspector_status.get("installation"),
        "library": inspector_status.get("library"),
        "agent_context": inspector_status.get("agent_context"),
        "managed_python": str(layout.python()),
    }
    if inspector_status.get("installation") != "verified":
        evidence.update(
            {
                "status": "proof_failed",
                "reason": "installation_not_verified",
                "code": inspector_status.get("code"),
            }
        )
        return evidence

    embedding_mode = "fixture"
    embedding_probe: dict[str, Any] | None = None
    if omlx_port is not None and omlx_api_key and embedding_model:
        embedding_probe = probe_omlx_embedding_route(
            port=omlx_port,
            api_key=omlx_api_key,
            embedding_model=embedding_model,
            expected_dimension=expected_dimension,
        )
        if embedding_probe.get("status") == "healthy":
            embedding_mode = "omlx"

    with tempfile.TemporaryDirectory(prefix="semantica-proof-") as temporary:
        work_dir = Path(temporary)
        environment = _probe_environment(layout)
        environment[WORKER_ENV_WORK_DIR] = str(work_dir)
        environment[WORKER_ENV_MODE] = embedding_mode
        environment[WORKER_ENV_PRODUCT_ROOT] = str(product_root)
        if embedding_mode == "omlx":
            environment[WORKER_ENV_OMLX_PORT] = str(omlx_port)
            environment[WORKER_ENV_EMBEDDING_MODEL] = embedding_model or ""
            if expected_dimension is not None:
                environment[WORKER_ENV_EXPECTED_DIMENSION] = str(expected_dimension)
            environment["OMLX_API_KEY"] = omlx_api_key or ""
            repo_root = repository_root or Path(__file__).resolve().parents[1]
            environment["PYTHONPATH"] = str(repo_root)
        worker_path = work_dir / "semantica_proof_worker.py"
        worker_path.write_text(_worker_script(), encoding="utf-8")
        python = layout.python()
        try:
            result = runner(
                [str(python), "-I", str(worker_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=60.0,
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

    evaluated = evaluate_worker_payload(payload)
    evidence.update(evaluated)
    if embedding_probe is not None:
        evidence["embedding_probe"] = {
            "status": embedding_probe.get("status"),
            "model": embedding_probe.get("model"),
            "dimension": embedding_probe.get("dimension"),
            "code": embedding_probe.get("code"),
        }
    return evidence


def redact_proof_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return evidence safe for stdout; secrets must never appear."""
    blocked = {"OMLX_API_KEY", "api_key", "token", "secret"}
    sanitized = dict(evidence)

    def _scrub(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: ("[redacted]" if key in blocked else _scrub(item))
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [_scrub(item) for item in value]
        if isinstance(value, str) and any(marker in value for marker in blocked):
            return "[redacted]"
        return value

    return _scrub(sanitized)
