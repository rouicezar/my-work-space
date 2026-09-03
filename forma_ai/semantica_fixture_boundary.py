"""Explicit no-network embedding boundary for Semantica integration proofs."""

from __future__ import annotations

import json
import math
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterable

import numpy as np


class ExplicitLocalVectorBoundary:
    """In-memory vector store surface for AgentContext proofs."""

    def __init__(self):
        self.items: dict[str, dict[str, Any]] = {}
        self.next_id = 0
        self.model = "fixture-local"

    def embed(self, text: str) -> np.ndarray:
        encoded = text.encode("utf-8")
        buckets = [0.0] * 8
        for index, value in enumerate(encoded):
            buckets[index % 8] += value / 255.0
        return np.array(buckets, dtype=np.float32)

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text).tolist()

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

    def search_vectors(self, query_vector, k: int = 5):
        query = np.asarray(query_vector)
        ranked = []
        for identity, item in self.items.items():
            score = float(np.dot(query, item["vector"]))
            ranked.append({"id": identity, "score": score, "metadata": item["metadata"]})
        return sorted(ranked, key=lambda item: item["score"], reverse=True)[:k]

    def delete_vectors(self, identities):
        for identity in identities:
            self.items.pop(identity, None)
        return True

    def save(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)

    def load(self, path):
        return None

    def health(self, probe: bool = False):
        return {
            "status": "healthy",
            "model": self.model,
            "dimension": 8,
            "vector_count": len(self.items),
        }


class ExplicitLocalEmbeddingClient:
    model = "fixture-local"

    def embed(self, text: str) -> list[float]:
        encoded = text.encode("utf-8")
        buckets = [0.0] * 8
        for index, value in enumerate(encoded):
            buckets[index % 8] += value / 255.0
        return buckets

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)

    def probe(self) -> dict[str, Any]:
        return {"status": "healthy", "model": self.model, "dimension": 8}


class FixturePersistentVectorStore:
    SCHEMA_VERSION = "1"

    def __init__(self, path: Path, client: ExplicitLocalEmbeddingClient):
        if not path.is_absolute():
            raise ValueError("vector index path must be absolute")
        self.path = path.resolve()
        self.client = client
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute(
                "CREATE TABLE IF NOT EXISTS vectors "
                "(id TEXT PRIMARY KEY, dimension INTEGER NOT NULL, vector TEXT NOT NULL, metadata TEXT NOT NULL)"
            )
            db.execute(
                "INSERT OR IGNORE INTO metadata(key, value) VALUES ('schema_version', ?)",
                (self.SCHEMA_VERSION,),
            )
            db.execute(
                "INSERT OR IGNORE INTO metadata(key, value) VALUES ('model', ?)",
                (self.client.model,),
            )

    def embed(self, text: str) -> list[float]:
        return self.client.embed(text)

    def embed_query(self, text: str) -> list[float]:
        return self.client.embed_query(text)

    def store_vectors(self, vectors: Iterable[Iterable[float]], metadata: Iterable[dict[str, Any]]) -> list[str]:
        vector_list = [list(vector) for vector in vectors]
        metadata_list = list(metadata)
        if not vector_list or len(vector_list) != len(metadata_list):
            raise ValueError("vectors and metadata must be non-empty and equal length")
        dimension = len(vector_list[0])
        identities = [str(uuid.uuid4()) for _ in vector_list]
        with self._connect() as db:
            row = db.execute("SELECT value FROM metadata WHERE key = 'dimension'").fetchone()
            if row and int(row[0]) != dimension:
                raise ValueError("vector dimension mismatch")
            db.execute(
                "INSERT OR IGNORE INTO metadata(key, value) VALUES ('dimension', ?)",
                (str(dimension),),
            )
            for identity, vector, item_metadata in zip(identities, vector_list, metadata_list):
                db.execute(
                    "INSERT INTO vectors(id, dimension, vector, metadata) VALUES (?, ?, ?, ?)",
                    (identity, dimension, json.dumps(vector), json.dumps(item_metadata, sort_keys=True)),
                )
        return identities

    def search_vectors(self, query_vector, k: int = 5):
        query = list(query_vector)
        with self._connect() as db:
            rows = list(db.execute("SELECT id, vector, metadata FROM vectors"))
        scored = []
        for row in rows:
            vector = json.loads(row["vector"])
            scored.append(
                {
                    "id": row["id"],
                    "score": _cosine(query, vector),
                    "metadata": json.loads(row["metadata"]),
                }
            )
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:k]

    def delete_vectors(self, identities):
        with self._connect() as db:
            before = db.total_changes
            for identity in identities:
                db.execute("DELETE FROM vectors WHERE id = ?", (identity,))
            return db.total_changes - before

    def save(self, _path=None):
        return None

    def load(self, _path=None):
        self._initialize()

    def health(self, probe: bool = False):
        with self._connect() as db:
            count = db.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
        result = {"status": "healthy", "model": self.client.model, "dimension": 8, "vector_count": count}
        if probe:
            result["embedding"] = self.client.probe()
        return result


def _cosine(left: list[float], right: list[float]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
