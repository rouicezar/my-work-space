"""Factory for the pinned managed Semantica and local oMLX embedding boundary."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from mac_ai_work_os.adapters.semantica import SemanticaContextBackend
from mac_ai_work_os.omlx_embeddings import OMLXEmbeddingClient, PersistentOMLXVectorStore
from mac_ai_work_os.semantica_runtime import EXPECTED_VERSION, SemanticaLayout


class ManagedSemanticaError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def create_managed_semantica_backend(
    *, product_root: Path, omlx_port: int, omlx_api_key: str,
    embedding_model: str, expected_dimension: int | None = None,
    query_prefix: str = "", document_prefix: str = "",
) -> SemanticaContextBackend:
    if not product_root.is_absolute():
        raise ManagedSemanticaError("MEMORY_ROOT_INVALID", "product root must be absolute")
    layout = SemanticaLayout(product_root)
    try:
        semantica = importlib.import_module("semantica")
        context_module = importlib.import_module("semantica.context")
    except ImportError as exc:
        raise ManagedSemanticaError("SEMANTICA_IMPORT_FAILED", "managed Semantica is unavailable") from exc
    module_path = Path(semantica.__file__).resolve()
    try:
        module_path.relative_to(layout.version_root().resolve())
    except ValueError as exc:
        raise ManagedSemanticaError("SEMANTICA_MODULE_ESCAPES_RUNTIME", str(module_path)) from exc
    if getattr(semantica, "__version__", None) != EXPECTED_VERSION:
        raise ManagedSemanticaError("SEMANTICA_VERSION_MISMATCH", str(getattr(semantica, "__version__", None)))
    agent_context: Any = getattr(context_module, "AgentContext", None)
    if agent_context is None:
        raise ManagedSemanticaError("SEMANTICA_AGENT_CONTEXT_MISSING", "AgentContext is unavailable")
    client = OMLXEmbeddingClient(
        port=omlx_port, api_key=omlx_api_key, model=embedding_model,
        expected_dimension=expected_dimension,
        query_prefix=query_prefix, document_prefix=document_prefix,
    )
    vector_store = PersistentOMLXVectorStore(
        product_root / "data/semantica/vector-index.sqlite3", client
    )
    context = agent_context(
        vector_store=vector_store, knowledge_graph=None, retention_days=None,
        graph_expansion=False, decision_tracking=False,
    )
    return SemanticaContextBackend(
        context, embedding_route=f"omlx://{embedding_model}", semantic_store=vector_store,
        state_path=product_root / "data/semantica/context",
    )
