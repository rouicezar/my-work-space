import unittest

from mac_ai_work_os.adapters.semantica import SemanticaContextBackend


class FixtureContext:
    def __init__(self):
        self.calls = []
        self.memories = {}

    def store(self, content, **kwargs):
        self.calls.append(("store", content, kwargs))
        self.memories["upstream-1"] = {"id": "upstream-1", "content": content, "metadata": kwargs["metadata"]}
        return "upstream-1"

    def get_memory(self, memory_id):
        self.calls.append(("get", memory_id))
        return self.memories.get(memory_id)

    def retrieve(self, query, **kwargs):
        self.calls.append(("retrieve", query, kwargs))
        return list(self.memories.values())

    def forget(self, memory_id=None):
        self.calls.append(("forget", memory_id))
        return 1 if self.memories.pop(memory_id, None) else 0

    def health(self):
        return {"status": "healthy", "total_memories": len(self.memories)}


class FixtureSemanticStore:
    def __init__(self):
        self.calls = []

    def embed(self, text):
        self.calls.append(("embed", text))
        return [1.0, 0.0]

    def search_vectors(self, vector, k=5):
        self.calls.append(("search", vector, k))
        return [{"id": "vector-1", "score": 1.0, "metadata": {"record_id": "record-1"}}]

    def health(self, probe=False):
        self.calls.append(("health", probe))
        return {"status": "healthy", "model": "fixture", "dimension": 2}


class SemanticaAdapterContractTests(unittest.TestCase):
    def test_uses_pinned_agent_context_surface_without_automatic_extraction(self):
        context = FixtureContext()
        adapter = SemanticaContextBackend(
            context, embedding_route="fixture-local", semantic_store=FixtureSemanticStore()
        )
        metadata = {"record_id": "record-1", "status": "confirmed", "version": 1}
        memory_id = adapter.store("confirmed fact", metadata)
        self.assertEqual(memory_id, "upstream-1")
        call = context.calls[0]
        self.assertFalse(call[2]["extract_entities"])
        self.assertFalse(call[2]["extract_relationships"])
        self.assertFalse(call[2]["auto_extract"])
        self.assertEqual(adapter.get(memory_id)["metadata"], metadata)

    def test_retrieval_uses_product_index_record_id_metadata(self):
        context = FixtureContext()
        store = FixtureSemanticStore()
        adapter = SemanticaContextBackend(
            context, embedding_route="fixture-local", semantic_store=store
        )
        self.assertEqual(adapter.retrieve("fact", 7), [{"metadata": {"record_id": "record-1"}}])
        self.assertEqual(store.calls[:2], [("embed", "fact"), ("search", [1.0, 0.0], 7)])
        self.assertFalse(any(call[0] == "retrieve" for call in context.calls))

    def test_health_and_forget_are_normalized(self):
        context = FixtureContext()
        adapter = SemanticaContextBackend(
            context, embedding_route="fixture-local", semantic_store=FixtureSemanticStore()
        )
        identity = adapter.store("fact", {})
        self.assertEqual(adapter.health()["status"], "healthy")
        self.assertTrue(adapter.forget(identity))
        self.assertFalse(adapter.forget(identity))

    def test_missing_embedding_route_is_explicitly_unavailable(self):
        health = SemanticaContextBackend(FixtureContext()).health()
        self.assertEqual(health["status"], "unavailable")
        self.assertEqual(health["code"], "EMBEDDING_ROUTE_UNVERIFIED")

    def test_missing_product_semantic_index_is_explicitly_unavailable(self):
        adapter = SemanticaContextBackend(
            FixtureContext(), embedding_route="fixture-local"
        )
        health = adapter.health()
        self.assertEqual(health["status"], "unavailable")
        self.assertEqual(health["code"], "SEMANTIC_INDEX_UNVERIFIED")
        with self.assertRaisesRegex(RuntimeError, "SEMANTIC_INDEX_UNVERIFIED"):
            adapter.retrieve("fact", 5)


if __name__ == "__main__":
    unittest.main()
