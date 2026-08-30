"""Verified activation record for an approved local embedding model."""

from __future__ import annotations

import json
import re
import sqlite3
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from forma_ai.models import (
    MODEL_ID, REVISION, ModelDefinition, ModelReference, _atomic_json,
)


API_MODEL = re.compile(r"^[A-Za-z0-9._/-]{1,160}$")


class EmbeddingConfigError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ApprovedEmbeddingRoute:
    model_id: str
    api_model: str
    revision: str
    expected_dimension: int
    query_prefix: str
    document_prefix: str


def activate_embedding_route(
    product_root: Path, model: ModelDefinition, reference: ModelReference,
    *, approved_revision: str,
) -> ApprovedEmbeddingRoute:
    if "embedding" not in model.capabilities:
        raise EmbeddingConfigError("MODEL_NOT_EMBEDDING_CAPABLE", model.id)
    if approved_revision != model.revision:
        raise EmbeddingConfigError("MODEL_APPROVAL_MISMATCH", model.id)
    if (
        model.embedding_dimension is None or model.query_prefix is None
        or model.document_prefix is None
    ):
        raise EmbeddingConfigError("EMBEDDING_CONTRACT_INVALID", model.id)
    if (
        reference.model_id != model.id or reference.revision != model.revision
        or reference.storage_mode != "external-reference"
    ):
        raise EmbeddingConfigError("EMBEDDING_REFERENCE_MISMATCH", model.id)
    api_model = model.repository.rsplit("/", 1)[-1]
    index = product_root / "data/semantica/vector-index.sqlite3"
    if index.exists():
        if not index.is_file() or index.is_symlink():
            raise EmbeddingConfigError("VECTOR_INDEX_UNSAFE", str(index))
        try:
            with sqlite3.connect(index) as db:
                row = db.execute("SELECT value FROM metadata WHERE key = 'model'").fetchone()
        except sqlite3.Error as exc:
            raise EmbeddingConfigError("VECTOR_INDEX_INVALID", str(index)) from exc
        if row and row[0] != api_model:
            raise EmbeddingConfigError("VECTOR_INDEX_MIGRATION_REQUIRED", str(row[0]))
    route = ApprovedEmbeddingRoute(
        model.id, api_model, model.revision, model.embedding_dimension,
        model.query_prefix, model.document_prefix,
    )
    _atomic_json(product_root / "state/models/embedding-active.json", {
        "schema_version": 1, "provider": "omlx", "capability": "embedding",
        "model_id": route.model_id, "api_model": route.api_model,
        "revision": route.revision, "expected_dimension": route.expected_dimension,
        "query_prefix": route.query_prefix, "document_prefix": route.document_prefix,
        "activated_at": datetime.now(timezone.utc).isoformat(),
    })
    return route


def load_approved_embedding_route(product_root: Path) -> ApprovedEmbeddingRoute | None:
    if not product_root.is_absolute():
        raise EmbeddingConfigError("MEMORY_ROOT_INVALID", "product root must be absolute")
    path = product_root / "state/models/embedding-active.json"
    if not path.exists() and not path.is_symlink():
        return None
    if not path.is_file() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise EmbeddingConfigError("EMBEDDING_ROUTE_UNSAFE", str(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EmbeddingConfigError("EMBEDDING_ROUTE_INVALID", str(path)) from exc
    model_id = payload.get("model_id")
    api_model = payload.get("api_model")
    revision = payload.get("revision")
    dimension = payload.get("expected_dimension")
    query_prefix = payload.get("query_prefix")
    document_prefix = payload.get("document_prefix")
    if (
        payload.get("schema_version") != 1
        or payload.get("provider") != "omlx"
        or payload.get("capability") != "embedding"
        or not isinstance(model_id, str) or not MODEL_ID.fullmatch(model_id)
        or not isinstance(api_model, str) or not API_MODEL.fullmatch(api_model)
        or api_model.startswith("/") or ".." in api_model.split("/")
        or not isinstance(revision, str) or not REVISION.fullmatch(revision)
        or isinstance(dimension, bool) or not isinstance(dimension, int) or dimension <= 0
        or not isinstance(query_prefix, str) or len(query_prefix) > 80
        or not isinstance(document_prefix, str) or len(document_prefix) > 80
    ):
        raise EmbeddingConfigError("EMBEDDING_ROUTE_INVALID", str(path))
    reference_path = product_root / "state/models" / f"{model_id}.json"
    if (
        not reference_path.is_file() or reference_path.is_symlink()
        or stat.S_IMODE(reference_path.stat().st_mode) & 0o077
    ):
        raise EmbeddingConfigError("EMBEDDING_REFERENCE_UNSAFE", str(reference_path))
    try:
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        link = Path(reference["link_path"])
        source = Path(reference["source_path"])
    except (KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise EmbeddingConfigError("EMBEDDING_REFERENCE_INVALID", str(reference_path)) from exc
    try:
        linked_source = link.resolve(strict=True)
        expected_source = source.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise EmbeddingConfigError("EMBEDDING_REFERENCE_MISMATCH", model_id) from exc
    if (
        reference.get("schema_version") != 1
        or reference.get("model_id") != model_id
        or reference.get("revision") != revision
        or reference.get("storage_mode") != "external-reference"
        or not link.is_absolute() or not source.is_absolute()
        or not link.is_symlink() or linked_source != expected_source
    ):
        raise EmbeddingConfigError("EMBEDDING_REFERENCE_MISMATCH", model_id)
    try:
        link.relative_to(product_root / "data/omlx/models")
    except ValueError as exc:
        raise EmbeddingConfigError("EMBEDDING_LINK_ESCAPES_PRODUCT", str(link)) from exc
    return ApprovedEmbeddingRoute(
        model_id, api_model, revision, dimension, query_prefix, document_prefix
    )
