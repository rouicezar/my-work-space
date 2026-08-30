"""Thin adapter for the pinned Semantica AgentContext contract."""

from __future__ import annotations

from typing import Any


class SemanticaContextBackend:
    def __init__(
        self, context: Any, *, embedding_route: str | None = None,
        semantic_store: Any | None = None,
    ):
        self.context = context
        self.embedding_route = embedding_route
        self.semantic_store = semantic_store

    def store(self, content: str, metadata: dict[str, Any]) -> str:
        result = self.context.store(
            content,
            metadata=metadata,
            extract_entities=False,
            extract_relationships=False,
            auto_extract=False,
        )
        return result if isinstance(result, str) else ""

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
        return self.context.forget(memory_id=memory_id) == 1

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
