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
        return []

    def delete_vectors(self, identities):
        for identity in identities:
            self.items.pop(identity, None)
        return True

    def save(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)

    def load(self, path):
        return None


@unittest.skipUnless(
    os.environ.get("MAC_AI_WORK_OS_SEMANTICA_INTEGRATION") == "1",
    "real pinned Semantica runtime integration is opt-in",
)
class RealSemanticaIntegrationTests(unittest.TestCase):
    def test_agent_context_store_retrieve_save_reload_and_forget(self):
        from semantica.context import AgentContext

        from mac_ai_work_os.adapters.semantica import SemanticaContextBackend

        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state"
            vector = ExplicitLocalVectorBoundary()
            context = AgentContext(
                vector_store=vector,
                knowledge_graph=None,
                retention_days=None,
                graph_expansion=False,
                decision_tracking=False,
            )
            backend = SemanticaContextBackend(context, embedding_route="test-explicit-local")
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
            context.save(str(state))

            restored_context = AgentContext(
                vector_store=ExplicitLocalVectorBoundary(),
                knowledge_graph=None,
                retention_days=None,
                graph_expansion=False,
                decision_tracking=False,
            )
            restored_context.load(str(state))
            restored = SemanticaContextBackend(restored_context, embedding_route="test-explicit-local")
            self.assertEqual(restored.get(memory_id)["content"], "Alpha Harbor is the fixture capital")
            self.assertTrue(restored.forget(memory_id))
            self.assertIsNone(restored.get(memory_id))


if __name__ == "__main__":
    unittest.main()
