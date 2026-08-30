"""Bounded oMLX embedding client and product-owned persistent vector index."""

from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Iterable


class EmbeddingError(RuntimeError):
    """A sanitized, stable failure from the local embedding boundary."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class OMLXEmbeddingClient:
    def __init__(self, *, port: int, api_key: str, model: str,
        timeout_seconds: float = 15.0, max_response_bytes: int = 16 * 1024 * 1024,
                 expected_dimension: int | None = None, query_prefix: str = "",
                 document_prefix: str = ""):
        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if len(api_key) < 32:
            raise ValueError("api_key must contain at least 32 characters")
        if not model.strip():
            raise ValueError("model must be pinned explicitly")
        if timeout_seconds <= 0 or max_response_bytes <= 0:
            raise ValueError("timeout and response limit must be positive")
        if expected_dimension is not None and expected_dimension <= 0:
            raise ValueError("expected_dimension must be positive")
        if not isinstance(query_prefix, str) or not isinstance(document_prefix, str):
            raise ValueError("embedding prefixes must be strings")
        self.url = f"http://127.0.0.1:{port}/v1/embeddings"
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.expected_dimension = expected_dimension
        self.query_prefix = query_prefix
        self.document_prefix = document_prefix

    def embed(self, text: str) -> list[float]:
        return self.embed_document(text)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_many([self.query_prefix + text])[0]

    def embed_document(self, text: str) -> list[float]:
        return self.embed_many([self.document_prefix + text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not isinstance(item, str) or not item.strip() for item in texts):
            raise ValueError("texts must be a non-empty list of non-empty strings")
        body = json.dumps({"model": self.model, "input": texts, "encoding_format": "float"},
                          separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            self.url, data=body, method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except urllib.error.HTTPError as exc:
            raise EmbeddingError("EMBEDDING_HTTP_ERROR", f"oMLX returned HTTP {exc.code}") from None
        except TimeoutError:
            raise EmbeddingError("EMBEDDING_TIMEOUT", "oMLX embedding request timed out") from None
        except (urllib.error.URLError, OSError):
            raise EmbeddingError("EMBEDDING_UNREACHABLE", "oMLX embedding service is unavailable") from None
        if len(raw) > self.max_response_bytes:
            raise EmbeddingError("EMBEDDING_RESPONSE_TOO_LARGE", "oMLX embedding response exceeded its limit")
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise EmbeddingError("EMBEDDING_INVALID_RESPONSE", "oMLX returned invalid JSON") from None
        if not isinstance(payload, dict) or payload.get("model") != self.model:
            raise EmbeddingError("EMBEDDING_MODEL_MISMATCH", "oMLX returned an unexpected model")
        data = payload.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise EmbeddingError("EMBEDDING_COUNT_MISMATCH", "oMLX returned an unexpected embedding count")
        ordered: list[list[float] | None] = [None] * len(texts)
        dimension: int | None = None
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get("index"), int):
                raise EmbeddingError("EMBEDDING_INVALID_RESPONSE", "oMLX returned an invalid embedding item")
            index, vector = item["index"], item.get("embedding")
            if index < 0 or index >= len(texts) or ordered[index] is not None:
                raise EmbeddingError("EMBEDDING_INDEX_MISMATCH", "oMLX returned invalid embedding indexes")
            if not isinstance(vector, list) or not vector:
                raise EmbeddingError("EMBEDDING_INVALID_VECTOR", "oMLX returned an empty or invalid vector")
            normalized = []
            for value in vector:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise EmbeddingError("EMBEDDING_INVALID_VECTOR", "oMLX returned a non-finite vector")
                normalized.append(float(value))
            dimension = dimension or len(normalized)
            if len(normalized) != dimension:
                raise EmbeddingError("EMBEDDING_DIMENSION_MISMATCH", "oMLX returned inconsistent dimensions")
            ordered[index] = normalized
        if self.expected_dimension is not None and dimension != self.expected_dimension:
            raise EmbeddingError("EMBEDDING_DIMENSION_MISMATCH", "oMLX returned an unexpected dimension")
        return [vector for vector in ordered if vector is not None]

    def probe(self) -> dict[str, Any]:
        vectors = self.embed_many(["mac-ai-work-os-probe-a", "mac-ai-work-os-probe-b"])
        return {"status": "healthy", "model": self.model, "dimension": len(vectors[0])}


class PersistentOMLXVectorStore:
    """Small local index implementing Semantica's vector-store surface."""

    SCHEMA_VERSION = "1"

    def __init__(self, path: str | Path, client: OMLXEmbeddingClient):
        requested_path = Path(path).expanduser()
        if not requested_path.is_absolute():
            raise ValueError("vector index path must be absolute")
        self.path = requested_path.resolve()
        self.client = client
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS vectors (id TEXT PRIMARY KEY, dimension INTEGER NOT NULL, vector TEXT NOT NULL, metadata TEXT NOT NULL)")
            existing = dict(db.execute("SELECT key, value FROM metadata"))
            for key, value in {"schema_version": self.SCHEMA_VERSION, "model": self.client.model}.items():
                if key in existing and existing[key] != value:
                    raise EmbeddingError("VECTOR_INDEX_BINDING_MISMATCH", f"vector index {key} does not match")
                db.execute("INSERT OR IGNORE INTO metadata(key, value) VALUES (?, ?)", (key, value))
        os.chmod(self.path, 0o600)

    def embed(self, text: str) -> list[float]:
        return self.client.embed(text)

    def embed_query(self, text: str) -> list[float]:
        embed_query = getattr(self.client, "embed_query", self.client.embed)
        return embed_query(text)

    def store_vectors(self, vectors: Iterable[Iterable[float]], metadata: Iterable[dict[str, Any]]) -> list[str]:
        vector_list = [self._normalize_vector(vector) for vector in vectors]
        metadata_list = list(metadata)
        if not vector_list or len(vector_list) != len(metadata_list):
            raise ValueError("vectors and metadata must be non-empty and have equal length")
        dimension = len(vector_list[0])
        if any(len(vector) != dimension for vector in vector_list):
            raise EmbeddingError("EMBEDDING_DIMENSION_MISMATCH", "vectors have inconsistent dimensions")
        ids = [str(uuid.uuid4()) for _ in vector_list]
        with self._lock, self._connect() as db:
            self._bind_dimension(db, dimension)
            for identity, vector, item_metadata in zip(ids, vector_list, metadata_list):
                if not isinstance(item_metadata, dict):
                    raise ValueError("metadata entries must be objects")
                db.execute("INSERT INTO vectors(id, dimension, vector, metadata) VALUES (?, ?, ?, ?)",
                           (identity, dimension, json.dumps(vector), json.dumps(item_metadata, sort_keys=True)))
        return ids

    def search_vectors(self, query_vector: Iterable[float], k: int = 5) -> list[dict[str, Any]]:
        if k <= 0:
            raise ValueError("k must be positive")
        query = self._normalize_vector(query_vector)
        with self._lock, self._connect() as db:
            self._bind_dimension(db, len(query))
            rows = list(db.execute("SELECT id, vector, metadata FROM vectors"))
        scored = [{"id": row["id"], "score": self._cosine(query, json.loads(row["vector"])),
                   "metadata": json.loads(row["metadata"])} for row in rows]
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:k]

    def delete_vectors(self, ids: Iterable[str]) -> int:
        identities = list(ids)
        if not identities:
            return 0
        with self._lock, self._connect() as db:
            before = db.total_changes
            db.executemany("DELETE FROM vectors WHERE id = ?", ((identity,) for identity in identities))
            return db.total_changes - before

    def save(self, _path: str | Path | None = None) -> None:
        return None

    def load(self, _path: str | Path | None = None) -> None:
        self._initialize()

    def health(self, *, probe: bool = False) -> dict[str, Any]:
        with self._lock, self._connect() as db:
            count = db.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
            metadata = dict(db.execute("SELECT key, value FROM metadata"))
        result: dict[str, Any] = {"status": "healthy", "model": metadata["model"],
                                  "dimension": int(metadata["dimension"]) if "dimension" in metadata else None,
                                  "vector_count": count}
        if probe:
            result["embedding"] = self.client.probe()
        return result

    def _bind_dimension(self, db: sqlite3.Connection, dimension: int) -> None:
        row = db.execute("SELECT value FROM metadata WHERE key = 'dimension'").fetchone()
        if row and int(row[0]) != dimension:
            raise EmbeddingError("VECTOR_INDEX_BINDING_MISMATCH", "vector index dimension does not match")
        db.execute("INSERT OR IGNORE INTO metadata(key, value) VALUES ('dimension', ?)", (str(dimension),))

    @staticmethod
    def _normalize_vector(vector: Iterable[float]) -> list[float]:
        values = list(vector)
        if not values:
            raise ValueError("vectors must not be empty")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
               for value in values):
            raise ValueError("vectors must contain finite numbers")
        return [float(value) for value in values]

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
