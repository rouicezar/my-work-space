"""P7-T04 contract tests for candidate/approval policy bound to Semantica authority."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from forma_ai.governed_memory import GovernedMemory, MemoryGovernanceError, SourceReference
from forma_ai.memory_governance_policy import (
    CONFIRMED_AUTHORITY,
    CONFIRMED_METADATA_STATUS,
    UnavailableSemanticaBackend,
    build_confirmed_metadata,
    validate_confirmed_metadata,
)


class TrackingBackend:
    def __init__(self):
        self.items: dict[str, dict] = {}
        self.store_calls = 0
        self.next_id = 0
        self.available = True

    def store(self, content: str, metadata: dict) -> str:
        self.store_calls += 1
        validate_confirmed_metadata(metadata)
        self.next_id += 1
        identity = f"sem-{self.next_id}"
        self.items[identity] = {"id": identity, "content": content, "metadata": dict(metadata)}
        return identity

    def get(self, memory_id: str):
        return self.items.get(memory_id)

    def retrieve(self, query: str, limit: int):
        query = query.casefold()
        return [item for item in self.items.values() if query in item["content"].casefold()][:limit]

    def forget(self, memory_id: str) -> bool:
        return self.items.pop(memory_id, None) is not None

    def health(self):
        return {"status": "healthy" if self.available else "unavailable"}


class MemoryGovernancePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Product"
        self.backend = TrackingBackend()
        self.memory = GovernedMemory(self.root, self.backend)
        self.source = SourceReference("fixture://doc/1", "2026-08-30T00:00:00+00:00")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_confirmed_metadata_envelope_is_semantica_bound(self) -> None:
        metadata = build_confirmed_metadata(
            record_id="record-1",
            claim_key="fixture.claim",
            version=1,
            previous_record_id=None,
            sources=[self.source],
            correlation_id="run-policy-1",
        )
        validate_confirmed_metadata(metadata)
        self.assertEqual(metadata["status"], CONFIRMED_METADATA_STATUS)

    def test_propose_never_writes_to_semantica(self) -> None:
        candidate = self.memory.propose(
            claim_key="fixture.claim", content="Candidate only", sources=[self.source],
            correlation_id="run-policy-2", actor="user",
        )
        self.assertEqual(candidate.status, "pending")
        self.assertEqual(self.backend.store_calls, 0)
        self.assertEqual(self.backend.items, {})
        self.assertEqual(self.memory.retrieve("Candidate"), [])

    def test_confirm_is_only_upstream_write_with_confirmed_metadata(self) -> None:
        candidate = self.memory.propose(
            claim_key="fixture.claim", content="Confirmed fact", sources=[self.source],
            correlation_id="run-policy-3", actor="user",
        )
        confirmed = self.memory.confirm(candidate.candidate_id, actor="reviewer", correlation_id="run-policy-4")
        self.assertEqual(self.backend.store_calls, 1)
        upstream = self.backend.items[confirmed.semantica_id]["metadata"]
        self.assertEqual(upstream["status"], CONFIRMED_METADATA_STATUS)
        self.assertEqual(upstream["record_id"], confirmed.record_id)
        self.assertEqual(self.memory.health()["confirmed_authority"], CONFIRMED_AUTHORITY)

    def test_reject_never_writes_to_semantica(self) -> None:
        candidate = self.memory.propose(
            claim_key="fixture.reject", content="Reject me", sources=[self.source],
            correlation_id="run-policy-5", actor="user",
        )
        self.memory.reject(candidate.candidate_id, actor="reviewer", correlation_id="run-policy-6")
        self.assertEqual(self.backend.store_calls, 0)
        item = self.memory.get_candidate(candidate.candidate_id)
        self.assertIsNotNone(item)
        self.assertEqual(item.status, "rejected")

    def test_list_and_get_candidate_are_governance_only(self) -> None:
        first = self.memory.propose(
            claim_key="a", content="First", sources=[self.source],
            correlation_id="run-policy-7", actor="user",
        )
        second = self.memory.propose(
            claim_key="b", content="Second", sources=[self.source],
            correlation_id="run-policy-8", actor="user",
        )
        pending = self.memory.list_candidates()
        self.assertEqual({item.candidate_id for item in pending}, {first.candidate_id, second.candidate_id})
        self.assertEqual(self.memory.get_candidate(first.candidate_id).claim_key, "a")
        self.memory.reject(second.candidate_id, actor="reviewer", correlation_id="run-policy-9")
        self.assertEqual(self.memory.list_candidates(), [first])

    def test_unavailable_semantica_backend_fails_confirm_closed(self) -> None:
        memory = GovernedMemory(self.root / "stub", UnavailableSemanticaBackend())
        candidate = memory.propose(
            claim_key="fixture.stub", content="Never promote", sources=[self.source],
            correlation_id="run-policy-10", actor="user",
        )
        with self.assertRaises(MemoryGovernanceError) as raised:
            memory.confirm(candidate.candidate_id, actor="reviewer", correlation_id="run-policy-11")
        self.assertEqual(raised.exception.code, "SEMANTICA_UNAVAILABLE")

    def test_ledger_candidate_capabilities_remain_product_governance(self) -> None:
        ledger = json.loads(
            (Path(__file__).resolve().parents[1] / "config/semantica-capability-ledger.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {row["id"]: row for row in ledger["capabilities"]}
        for capability_id in ("memory.candidate_propose", "memory.confirm_reject", "memory.conflict_detection"):
            row = by_id[capability_id]
            self.assertEqual(row["authority"], "product_governance")
            self.assertEqual(row["verdict"], "product_gap")
        self.assertEqual(by_id["memory.store"]["authority"], "semantica")


if __name__ == "__main__":
    unittest.main()
