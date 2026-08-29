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


class SemanticaAdapterContractTests(unittest.TestCase):
    def test_uses_pinned_agent_context_surface_without_automatic_extraction(self):
        context = FixtureContext()
        adapter = SemanticaContextBackend(context)
        metadata = {"record_id": "record-1", "status": "confirmed", "version": 1}
        memory_id = adapter.store("confirmed fact", metadata)
        self.assertEqual(memory_id, "upstream-1")
        call = context.calls[0]
        self.assertFalse(call[2]["extract_entities"])
        self.assertFalse(call[2]["extract_relationships"])
        self.assertFalse(call[2]["auto_extract"])
        self.assertEqual(adapter.get(memory_id)["metadata"], metadata)

    def test_retrieval_disables_graph_and_uses_max_results(self):
        context = FixtureContext()
        adapter = SemanticaContextBackend(context)
        adapter.retrieve("fact", 7)
        kwargs = context.calls[-1][2]
        self.assertEqual(kwargs["max_results"], 7)
        self.assertFalse(kwargs["use_graph"])
        self.assertFalse(kwargs["expand_graph"])

    def test_health_and_forget_are_normalized(self):
        context = FixtureContext()
        adapter = SemanticaContextBackend(context)
        identity = adapter.store("fact", {})
        self.assertEqual(adapter.health()["status"], "healthy")
        self.assertTrue(adapter.forget(identity))
        self.assertFalse(adapter.forget(identity))


if __name__ == "__main__":
    unittest.main()
