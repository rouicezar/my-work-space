"""P7-T06 contract tests for memory review binding and audit correlation."""

import json
import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from forma_ai.broker import JsonlAuditSink
from forma_ai.governed_memory import GovernedMemory
from forma_ai.memory_review_binding import (
    MEMORY_REVIEW_AUDIT_PATH,
    SUPERVISOR_COMMANDS,
    audit_review_event,
    binding_contract,
    build_review_snapshot,
)
from forma_ai.memory_service import GovernedMemoryService, MemoryServicePolicy, create_memory_server
from scripts import supervisor
from tests.test_governed_memory import FakeSemantica


TOKEN = "m" * 48


class MemoryReviewBindingTests(unittest.TestCase):
    def test_binding_contract_maps_ui_states_to_real_fields_and_routes(self):
        contract = binding_contract()
        self.assertEqual(contract["confirmed_authority"], "semantica")
        self.assertEqual(contract["loopback_port"], 43111)
        self.assertEqual(contract["audit_path"], MEMORY_REVIEW_AUDIT_PATH)
        self.assertEqual(contract["supervisor_commands"], SUPERVISOR_COMMANDS)
        self.assertEqual(contract["http_routes"]["confirm"]["path"], "/v1/memory/confirm")
        self.assertEqual(contract["ui_state_fields"]["confirmed"]["semantica_id"], "semantica_id")
        self.assertEqual(contract["ui_state_fields"]["candidate"]["primary_id"], "candidate_id")

    def test_build_review_snapshot_reflects_semantica_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            service = GovernedMemoryService(
                MemoryServicePolicy(TOKEN),
                GovernedMemory(root, FakeSemantica()),
                JsonlAuditSink(root / "logs/audit/memory-service.jsonl"),
            )
            server = create_memory_server("127.0.0.1", 0, service)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                source = {"uri": "fixture://doc/1", "observed_at": "2026-08-30T00:00:00+00:00"}
                from forma_ai.memory_client import MemoryClient

                client = MemoryClient("127.0.0.1", port, TOKEN)
                proposed = client.propose(
                    actor="user",
                    claim_key="fixture.binding",
                    content="Binding truth",
                    sources=[source],
                    correlation_id="bind-1",
                )
                client.confirm(
                    actor="reviewer",
                    candidate_id=proposed["candidate_id"],
                    correlation_id="bind-2",
                )
                pending = client.propose(
                    actor="user",
                    claim_key="fixture.pending",
                    content="Still pending",
                    sources=[source],
                    correlation_id="bind-3",
                )
                snapshot = build_review_snapshot(client, "bind-4")
                self.assertEqual(snapshot["confirmed_authority"], "semantica")
                self.assertEqual(len(snapshot["confirmed_records"]), 1)
                self.assertTrue(snapshot["confirmed_records"][0]["semantica_id"].startswith("sem-"))
                self.assertEqual(snapshot["pending_candidates"][0]["candidate_id"], pending["candidate_id"])
                self.assertEqual(snapshot["binding"]["confirmed_authority"], "semantica")
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()


class SupervisorMemoryReviewTests(unittest.TestCase):
    def test_memory_review_confirm_is_audited_and_correlated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            service = GovernedMemoryService(
                MemoryServicePolicy(TOKEN),
                GovernedMemory(root, FakeSemantica()),
                JsonlAuditSink(root / "logs/audit/memory-service.jsonl"),
            )
            server = create_memory_server("127.0.0.1", 0, service)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            request_id = str(uuid.uuid4())
            try:
                port = server.server_address[1]
                source = {"uri": "fixture://doc/9", "observed_at": "2026-08-30T00:00:00+00:00"}
                from forma_ai.memory_client import MemoryClient

                client = MemoryClient("127.0.0.1", port, TOKEN)
                candidate_id = client.propose(
                    actor="user",
                    claim_key="fixture.supervisor",
                    content="Supervisor binding",
                    sources=[source],
                    correlation_id="sup-1",
                )["candidate_id"]
                with patch.dict("os.environ", {"FORMA_AI_MEMORY_TOKEN": TOKEN}, clear=False):
                    response = supervisor.run(supervisor.parser().parse_args([
                        "--request-id", request_id,
                        "memory-review-confirm",
                        "--root", str(root),
                        "--memory-port", str(port),
                        "--candidate-id", candidate_id,
                        "--actor", "reviewer",
                    ]))
                self.assertEqual(response["command"], "memory-review-confirm")
                self.assertEqual(response["payload"]["confirmed"]["claim_key"], "fixture.supervisor")
                audit_path = root / MEMORY_REVIEW_AUDIT_PATH
                audit = json.loads(audit_path.read_text(encoding="utf-8").strip())
                self.assertEqual(audit["correlation_id"], request_id)
                self.assertEqual(audit["event"], "memory_review_decision")
                self.assertEqual(audit["outcome"], "confirmed")
                self.assertEqual(audit["candidate_id"], candidate_id)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()


if __name__ == "__main__":
    unittest.main()
