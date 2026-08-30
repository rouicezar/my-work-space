import os
import tempfile
import unittest
from pathlib import Path

import numpy as np


class ExplicitLocalVectorBoundary:
    """No-network test boundary; production will route embeddings through oMLX."""

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
            self.items[identity] = {"vector": np.asarray(vector), "metadata": dict(item_metadata)}
            identities.append(identity)
        return identities

    def search_vectors(self, query_vector, k):
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

    def health(self, probe=False):
        return {"status": "healthy", "model": "fixture-local", "dimension": 8,
                "vector_count": len(self.items)}


class ExplicitLocalEmbeddingClient:
    model = "fixture-local"

    def embed(self, text):
        encoded = text.encode("utf-8")
        buckets = [0.0] * 8
        for index, value in enumerate(encoded):
            buckets[index % 8] += value / 255.0
        return buckets

    def probe(self):
        return {"status": "healthy", "model": self.model, "dimension": 8}


@unittest.skipUnless(
    os.environ.get("FORMA_AI_SEMANTICA_INTEGRATION") == "1",
    "real pinned Semantica runtime integration is opt-in",
)
class RealSemanticaIntegrationTests(unittest.TestCase):
    def test_agent_context_store_retrieve_save_reload_and_forget(self):
        from semantica.context import AgentContext

        from forma_ai.adapters.semantica import SemanticaContextBackend
        from forma_ai.omlx_embeddings import PersistentOMLXVectorStore

        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state"
            vector = PersistentOMLXVectorStore(
                Path(directory) / "vectors.sqlite3", ExplicitLocalEmbeddingClient()
            )
            context = AgentContext(
                vector_store=vector,
                knowledge_graph=None,
                retention_days=None,
                graph_expansion=False,
                decision_tracking=False,
            )
            backend = SemanticaContextBackend(
                context, embedding_route="test-explicit-local", semantic_store=vector,
                state_path=state,
            )
            metadata = {
                "schema_version": 1,
                "record_id": "real-record-1",
                "claim_key": "fixture.capital",
                "status": "confirmed",
                "version": 1,
                "correlation_id": "real-semantica-1",
                "sources": [{"uri": "fixture://real/1", "observed_at": "2026-08-30T00:00:00+00:00"}],
            }
            memory_id = backend.store("Alpha Harbor is the fixture capital", metadata)
            self.assertTrue(memory_id)
            self.assertEqual(backend.get(memory_id)["metadata"]["record_id"], "real-record-1")
            retrieved = backend.retrieve("fixture capital", 5)
            self.assertTrue(any(item["metadata"].get("record_id") == "real-record-1" for item in retrieved))

            restored_vector = PersistentOMLXVectorStore(
                Path(directory) / "vectors.sqlite3", ExplicitLocalEmbeddingClient()
            )
            restored_context = AgentContext(
                vector_store=restored_vector,
                knowledge_graph=None,
                retention_days=None,
                graph_expansion=False,
                decision_tracking=False,
            )
            restored = SemanticaContextBackend(
                restored_context, embedding_route="test-explicit-local",
                semantic_store=restored_vector, state_path=state,
            )
            self.assertEqual(restored.get(memory_id)["content"], "Alpha Harbor is the fixture capital")
            self.assertTrue(any(
                item["metadata"].get("record_id") == "real-record-1"
                for item in restored.retrieve("fixture capital", 5)
            ))
            self.assertTrue(restored.forget(memory_id))
            self.assertIsNone(restored.get(memory_id))


if __name__ == "__main__":
    unittest.main()
