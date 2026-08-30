"""Thin adapter for the pinned Semantica AgentContext contract."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


class SemanticaContextBackend:
    def __init__(
        self, context: Any, *, embedding_route: str | None = None,
        semantic_store: Any | None = None, state_path: str | Path | None = None,
    ):
        self.context = context
        self.embedding_route = embedding_route
        self.semantic_store = semantic_store
        self.state_path = Path(state_path).resolve() if state_path is not None else None
        if state_path is not None and not Path(state_path).is_absolute():
            raise ValueError("Semantica state path must be absolute")
        if self.state_path is not None and (self.state_path / "agent_memory.json").is_file():
            self.context.load(str(self.state_path))

    def store(self, content: str, metadata: dict[str, Any]) -> str:
        result = self.context.store(
            content,
            metadata=metadata,
            extract_entities=False,
            extract_relationships=False,
            auto_extract=False,
        )
        if not isinstance(result, str) or not result:
            return ""
        try:
            self._persist()
        except Exception:
            self.context.forget(result)
            raise
        return result

    def get(self, memory_id: str) -> dict[str, Any] | None:
        return self.context.get_memory(memory_id)

    def retrieve(self, query: str, limit: int) -> list[dict[str, Any]]:
        if self.semantic_store is None:
            raise RuntimeError("SEMANTIC_INDEX_UNVERIFIED")
        vector = self.semantic_store.embed(query)
        return [
            {"metadata": result.get("metadata", {})}
            for result in self.semantic_store.search_vectors(vector, k=limit)
        ]

    def forget(self, memory_id: str) -> bool:
        snapshot = self.context.get_memory(memory_id)
        deleted = self.context.forget(memory_id=memory_id) == 1
        if not deleted:
            return False
        try:
            self._persist()
        except Exception:
            if snapshot:
                self.context.store(
                    snapshot["content"], metadata=snapshot.get("metadata", {}),
                    entities=snapshot.get("entities", []), relationships=snapshot.get("relationships", []),
                    memory_id=memory_id, extract_entities=False,
                    extract_relationships=False, auto_extract=False,
                )
            raise
        return True

    def _persist(self) -> None:
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = Path(tempfile.mkdtemp(prefix=".semantica-state-", dir=self.state_path.parent))
        try:
            self.context.save(str(temporary))
            source = temporary / "agent_memory.json"
            if not source.is_file() or source.is_symlink():
                raise RuntimeError("SEMANTICA_STATE_INVALID")
            self.state_path.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(source, 0o600)
            os.replace(source, self.state_path / "agent_memory.json")
        finally:
            shutil.rmtree(temporary, ignore_errors=True)

    def health(self) -> dict[str, Any]:
        if not self.embedding_route:
            return {
                "status": "unavailable",
                "code": "EMBEDDING_ROUTE_UNVERIFIED",
                "details": "Semantica requires an explicit verified local embedding route",
            }
        if self.semantic_store is None:
            return {
                "status": "unavailable",
                "code": "SEMANTIC_INDEX_UNVERIFIED",
                "details": "Semantica requires a verified product semantic index",
            }
        try:
            result = self.context.health()
            healthy = isinstance(result, dict) and result.get("status") in {"healthy", "ok"}
            index = self.semantic_store.health(probe=True)
            healthy = healthy and index.get("status") == "healthy"
            return {
                "status": "healthy" if healthy else "unavailable",
                "embedding_route": self.embedding_route,
                "details": result,
                "semantic_index": index,
            }
        except Exception as exc:
            return {"status": "unavailable", "error_type": type(exc).__name__}
