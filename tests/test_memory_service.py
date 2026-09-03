import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from forma_ai.broker import BrokerRequest, MemoryAuditSink
from forma_ai.governed_memory import GovernedMemory
from forma_ai.memory_service import (
    GovernedMemoryService,
    MemoryServicePolicy,
    create_memory_server,
)
from tests.test_governed_memory import FakeSemantica


TOKEN = "m" * 48


class MemoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Product"
        self.backend = FakeSemantica()
        self.audit = MemoryAuditSink()
        self.service = GovernedMemoryService(
            MemoryServicePolicy(TOKEN), GovernedMemory(self.root, self.backend), self.audit
        )

    def tearDown(self):
        self.temp.cleanup()

    def request(self, path, payload=None, *, token=TOKEN, correlation="run-http-1"):
        body = json.dumps(payload).encode() if payload is not None else b""
        headers = {"Authorization": f"Bearer {token}", "X-Correlation-ID": correlation}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        return self.service.handle(BrokerRequest(
            "POST" if payload is not None else "GET", path, headers, body
        ))

    def decoded(self, response):
        return json.loads(response.body)

    def test_auth_route_and_body_boundaries_fail_closed_and_are_audited(self):
        denied = self.request("/v1/memory/health", token="wrong")
        self.assertEqual(denied.status, 401)
        missing = self.request("/unknown")
        self.assertEqual(missing.status, 404)
        oversized = self.service.handle(BrokerRequest(
            "POST", "/v1/memory/propose", {"Authorization": f"Bearer {TOKEN}"}, b"",
            declared_body_bytes=self.service.policy.max_body_bytes + 1,
        ))
        self.assertEqual(oversized.status, 413)
        self.assertEqual([item["status"] for item in self.audit.events], [401, 404, 413])

    def test_candidate_confirm_retrieve_correct_history_export_delete_round_trip(self):
        source = {"uri": "fixture://doc/1", "observed_at": "2026-08-30T00:00:00+00:00"}
        proposed = self.decoded(self.request("/v1/memory/propose", {
            "actor": "user", "claim_key": "fixture.capital", "content": "Alpha is capital",
            "sources": [source],
        }))
        candidate = proposed["result"]["candidate_id"]
        confirmed = self.decoded(self.request("/v1/memory/confirm", {
            "actor": "reviewer", "candidate_id": candidate,
        }, correlation="run-http-2"))["result"]
        record = confirmed["record_id"]
        fetched = self.decoded(self.request("/v1/memory/get", {"record_id": record}))["result"]
        self.assertEqual(fetched["record_id"], record)
        retrieved = self.decoded(self.request("/v1/memory/retrieve", {
            "query": "capital", "limit": 5,
        }))["result"]
        self.assertEqual(retrieved[0]["record_id"], record)
        corrected = self.decoded(self.request("/v1/memory/correct", {
            "actor": "reviewer", "record_id": record, "content": "Alpha remains capital",
            "sources": [source],
        }, correlation="run-http-3"))["result"]
        history = self.decoded(self.request("/v1/memory/history", {
            "claim_key": "fixture.capital",
        }))["result"]
        self.assertEqual([item["version"] for item in history], [1, 2])
        exported = self.decoded(self.request("/v1/memory/export", {}))["result"]
        self.assertEqual(len(exported["records"]), 1)
        self.assertEqual(exported["records"][0]["record_id"], corrected["record_id"])
        self.assertEqual(exported["records"][0]["version"], 2)
        deleted = self.request("/v1/memory/delete", {
            "actor": "reviewer", "record_id": corrected["record_id"],
        }, correlation="run-http-4")
        self.assertEqual(deleted.status, 200)
        self.assertEqual(self.decoded(self.request("/v1/memory/export", {}))["result"]["records"], [])
        self.assertTrue(all("content" not in event for event in self.audit.events))

    def test_reject_and_health_operations_preserve_governance_boundary(self):
        source = {"uri": "fixture://doc/2", "observed_at": "2026-08-30T00:00:00+00:00"}
        candidate = self.decoded(self.request("/v1/memory/propose", {
            "actor": "user", "claim_key": "fixture.rejected", "content": "Do not promote",
            "sources": [source],
        }))["result"]["candidate_id"]
        rejected = self.request("/v1/memory/reject", {
            "actor": "reviewer", "candidate_id": candidate,
        })
        self.assertEqual(self.decoded(rejected)["result"]["status"], "rejected")
        health = self.decoded(self.request("/v1/memory/health"))["result"]
        self.assertEqual(health["confirmed_authority"], "semantica")
        self.assertEqual(self.backend.items, {})

    def test_candidate_list_and_get_endpoints_are_governance_only(self):
        source = {"uri": "fixture://doc/3", "observed_at": "2026-08-30T00:00:00+00:00"}
        proposed = self.decoded(self.request("/v1/memory/propose", {
            "actor": "user", "claim_key": "fixture.pending", "content": "Pending only",
            "sources": [source],
        }))
        candidate_id = proposed["result"]["candidate_id"]
        listed = self.decoded(self.request("/v1/memory/candidates", {}))["result"]
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["candidate_id"], candidate_id)
        fetched = self.decoded(self.request("/v1/memory/candidate/get", {
            "candidate_id": candidate_id,
        }))["result"]
        self.assertEqual(fetched["status"], "pending")
        self.assertEqual(self.backend.items, {})

    def test_unavailable_semantica_returns_capability_failure_not_empty_success(self):
        source = {"uri": "fixture://doc/1", "observed_at": "2026-08-30T00:00:00+00:00"}
        candidate = self.decoded(self.request("/v1/memory/propose", {
            "actor": "user", "claim_key": "fixture.fact", "content": "A fact", "sources": [source],
        }))["result"]["candidate_id"]
        self.backend.available = False
        response = self.request("/v1/memory/confirm", {
            "actor": "reviewer", "candidate_id": candidate,
        })
        self.assertEqual(response.status, 503)
        self.assertEqual(self.decoded(response)["error"]["code"], "SEMANTICA_UNAVAILABLE")

    def test_unexpected_failure_is_sanitized_and_audited(self):
        self.service.memory.health = lambda: (_ for _ in ()).throw(RuntimeError("secret detail"))
        response = self.request("/v1/memory/health")
        self.assertEqual(response.status, 500)
        self.assertEqual(self.decoded(response)["error"]["code"], "MEMORY_SERVICE_INTERNAL")
        self.assertNotIn("secret detail", response.body.decode())
        self.assertEqual(self.audit.events[-1]["outcome"], "internal_error")

    def test_real_loopback_transport_requires_auth_and_preserves_correlation(self):
        server = create_memory_server("127.0.0.1", 0, self.service)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            denied = urllib.request.Request(f"http://127.0.0.1:{port}/live")
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(denied, timeout=2)
            self.assertEqual(raised.exception.code, 401)
            allowed = urllib.request.Request(
                f"http://127.0.0.1:{port}/live",
                headers={"Authorization": f"Bearer {TOKEN}", "X-Correlation-ID": "real-http-1"},
            )
            with urllib.request.urlopen(allowed, timeout=2) as response:
                body = json.loads(response.read())
                self.assertEqual(response.headers["X-Correlation-ID"], "real-http-1")
                self.assertEqual(body["result"]["status"], "ok")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_server_rejects_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            create_memory_server("0.0.0.0", 0, self.service)


if __name__ == "__main__":
    unittest.main()
