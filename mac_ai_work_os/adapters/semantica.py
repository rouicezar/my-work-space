"""Thin adapter for the pinned Semantica AgentContext contract."""

from __future__ import annotations

from typing import Any


class SemanticaContextBackend:
    def __init__(self, context: Any, *, embedding_route: str | None = None):
        self.context = context
        self.embedding_route = embedding_route

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
        return self.context.retrieve(
            query, max_results=limit, use_graph=False, include_entities=False,
            include_relationships=False, expand_graph=False,
        )

    def forget(self, memory_id: str) -> bool:
        return self.context.forget(memory_id=memory_id) == 1

    def health(self) -> dict[str, Any]:
        if not self.embedding_route:
            return {
                "status": "unavailable",
                "code": "EMBEDDING_ROUTE_UNVERIFIED",
                "details": "Semantica requires an explicit verified local embedding route",
            }
        try:
            result = self.context.health()
            healthy = isinstance(result, dict) and result.get("status") in {"healthy", "ok"}
            return {
                "status": "healthy" if healthy else "unavailable",
                "embedding_route": self.embedding_route,
                "details": result,
            }
        except Exception as exc:
            return {"status": "unavailable", "error_type": type(exc).__name__}
