import tempfile
import unittest
from pathlib import Path

from mac_ai_work_os.governed_memory import (
    GovernedMemory,
    MemoryGovernanceError,
    SourceReference,
)


class FakeSemantica:
    def __init__(self):
        self.items = {}
        self.available = True
        self.next_id = 0

    def store(self, content, metadata):
        self.next_id += 1
        identity = f"sem-{self.next_id}"
        self.items[identity] = {"id": identity, "content": content, "metadata": dict(metadata)}
        return identity

    def get(self, memory_id):
        return self.items.get(memory_id)

    def retrieve(self, query, limit):
        query = query.casefold()
        return [item for item in self.items.values() if query in item["content"].casefold()][:limit]

    def forget(self, memory_id):
        return self.items.pop(memory_id, None) is not None

    def health(self):
        return {"status": "healthy" if self.available else "unavailable"}


class GovernedMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "Product"
        self.backend = FakeSemantica()
        self.memory = GovernedMemory(self.root, self.backend)
        self.source = SourceReference("fixture://document/1", "2026-08-30T00:00:00+00:00", "sha256:test")

    def tearDown(self):
        self.temporary.cleanup()

    def propose(self, content="Paris is the capital of France"):
        return self.memory.propose(
            claim_key="country.france.capital", content=content, sources=[self.source],
            correlation_id="run-1", actor="fixture-user",
        )

    def test_candidate_is_not_written_or_retrievable_before_confirmation(self):
        candidate = self.propose()
        self.assertEqual(candidate.status, "pending")
        self.assertEqual(self.backend.items, {})
        self.assertEqual(self.memory.retrieve("Paris"), [])

    def test_confirmation_writes_governed_envelope_and_survives_restart(self):
        confirmed = self.memory.confirm(self.propose().candidate_id, actor="reviewer", correlation_id="run-2")
        self.assertEqual(confirmed.version, 1)
        self.assertEqual(self.backend.items[confirmed.semantica_id]["metadata"]["status"], "confirmed")
        restarted = GovernedMemory(self.root, self.backend)
        self.assertEqual(restarted.get(confirmed.record_id), confirmed)
        self.assertEqual(restarted.retrieve("capital")[0].record_id, confirmed.record_id)
        self.assertEqual(self.memory.database.stat().st_mode & 0o777, 0o600)

    def test_duplicate_is_idempotent_and_conflict_fails_closed(self):
        first = self.memory.confirm(self.propose().candidate_id, actor="reviewer", correlation_id="run-2")
        duplicate = self.memory.confirm(self.propose("  PARIS is the capital of France ").candidate_id, actor="reviewer", correlation_id="run-3")
        self.assertEqual(duplicate.record_id, first.record_id)
        self.assertEqual(len(self.backend.items), 1)
        conflict = self.propose("Lyon is the capital of France")
        with self.assertRaisesRegex(MemoryGovernanceError, "country.france.capital") as raised:
            self.memory.confirm(conflict.candidate_id, actor="reviewer", correlation_id="run-4")
        self.assertEqual(raised.exception.code, "MEMORY_CONFLICT")
        self.assertEqual(self.memory.get(first.record_id), first)

    def test_correction_creates_version_history_and_removes_old_authority_item(self):
        first = self.memory.confirm(self.propose().candidate_id, actor="reviewer", correlation_id="run-2")
        corrected = self.memory.correct(
            first.record_id, content="Paris remains France's capital", sources=[self.source],
            actor="reviewer", correlation_id="run-5",
        )
        self.assertEqual(corrected.version, 2)
        self.assertEqual(corrected.previous_record_id, first.record_id)
        self.assertNotIn(first.semantica_id, self.backend.items)
        self.assertIsNone(self.memory.get(first.record_id))
        self.assertEqual([item["status"] for item in self.memory.history(first.claim_key)], ["superseded", "confirmed"])

    def test_delete_removes_content_and_keeps_content_free_tombstone(self):
        record = self.memory.confirm(self.propose().candidate_id, actor="reviewer", correlation_id="run-2")
        self.memory.delete(record.record_id, actor="reviewer", correlation_id="run-6")
        self.assertIsNone(self.memory.get(record.record_id))
        self.assertEqual(self.memory.retrieve("Paris"), [])
        with self.memory._connect() as connection:
            row = connection.execute("SELECT content, sources, status FROM records WHERE record_id = ?", (record.record_id,)).fetchone()
        self.assertIsNone(row[0])
        self.assertEqual(row[1], "[]")
        self.assertEqual(row[2], "deleted")
        self.assertEqual(self.memory.export()["records"], [])

    def test_delete_after_correction_erases_content_from_entire_version_chain(self):
        first = self.memory.confirm(self.propose().candidate_id, actor="reviewer", correlation_id="run-2")
        corrected = self.memory.correct(
            first.record_id, content="Paris remains France's capital", sources=[self.source],
            actor="reviewer", correlation_id="run-5",
        )
        self.memory.delete(corrected.record_id, actor="reviewer", correlation_id="run-6")
        with self.memory._connect() as connection:
            rows = connection.execute(
                "SELECT content, sources FROM records WHERE claim_key = ?", (corrected.claim_key,)
            ).fetchall()
        self.assertTrue(rows)
        self.assertTrue(all(row[0] is None and row[1] == "[]" for row in rows))
        self.assertEqual(self.memory.export()["records"], [])

    def test_unavailable_semantica_never_promotes_candidate(self):
        candidate = self.propose()
        self.backend.available = False
        with self.assertRaises(MemoryGovernanceError) as raised:
            self.memory.confirm(candidate.candidate_id, actor="reviewer", correlation_id="run-7")
        self.assertEqual(raised.exception.code, "SEMANTICA_UNAVAILABLE")
        self.assertEqual(self.backend.items, {})

    def test_source_and_correlation_are_mandatory(self):
        with self.assertRaises(MemoryGovernanceError):
            self.memory.propose(
                claim_key="x", content="fact", sources=[], correlation_id="run-8", actor="user"
            )
        with self.assertRaises(MemoryGovernanceError):
            self.memory.propose(
                claim_key="x", content="fact", sources=[self.source], correlation_id="bad id", actor="user"
            )


if __name__ == "__main__":
    unittest.main()
