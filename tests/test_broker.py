import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mac_ai_work_os.broker import (
    BrokerPolicy,
    BrokerRequest,
    BrokerResponse,
    MemoryAuditSink,
    OMLXBroker,
    OMLXUpstream,
    JsonlAuditSink,
    create_server,
)


TOKEN = "client-token-with-at-least-thirty-two-characters"
ORIGIN = "http://127.0.0.1:43110"


class FakeUpstream:
    def __init__(self):
        self.requests = []

    def request(self, method, path, body, correlation_id):
        self.requests.append((method, path, body, correlation_id))
        payload = {"path": path, "correlation_id": correlation_id}
        return BrokerResponse(200, {"Content-Type": "application/json"}, json.dumps(payload).encode())


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.upstream = FakeUpstream()
        self.audit = MemoryAuditSink()
        self.broker = OMLXBroker(
            BrokerPolicy(TOKEN, frozenset({ORIGIN}), max_body_bytes=128),
            self.upstream,
            self.audit,
        )

    def request(self, method="GET", target="/health", headers=None, body=b""):
        values = {"Authorization": f"Bearer {TOKEN}"}
        values.update(headers or {})
        return self.broker.handle(BrokerRequest(method, target, values, body))

    def test_allowed_request_forwards_only_known_route_and_correlates_audit(self):
        response = self.request(headers={"X-Correlation-ID": "run-123"})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers["X-Correlation-ID"], "run-123")
        self.assertEqual(self.upstream.requests[0][:2], ("GET", "/health"))
        self.assertEqual(self.audit.events[0]["outcome"], "forwarded")
        self.assertEqual(self.audit.events[0]["correlation_id"], "run-123")
        self.assertNotIn(TOKEN, repr(self.audit.events))

    def test_unknown_route_query_and_wrong_method_are_denied(self):
        for method, target in [("GET", "/admin"), ("GET", "/health?x=1"), ("POST", "/health")]:
            with self.subTest(method=method, target=target):
                self.assertEqual(self.request(method, target).status, 404)
        self.assertEqual(self.upstream.requests, [])

    def test_auth_origin_body_and_json_fail_closed(self):
        self.assertEqual(self.broker.handle(BrokerRequest("GET", "/health", {})).status, 401)
        self.assertEqual(self.request(headers={"Origin": "https://evil.example"}).status, 403)
        self.assertEqual(self.request("POST", "/v1/chat/completions", {"Content-Type": "application/json"}, b"x" * 129).status, 413)
        self.assertEqual(self.request("POST", "/v1/chat/completions", {"Content-Type": "text/plain"}, b"{}").status, 400)
        self.assertEqual(self.request("POST", "/v1/chat/completions", {"Content-Type": "application/json"}, b"[]").status, 400)
        self.assertEqual(self.upstream.requests, [])

    def test_exact_allowed_origin_and_preflight(self):
        response = self.request(headers={"Origin": ORIGIN})
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], ORIGIN)
        preflight = self.broker.preflight(BrokerRequest("OPTIONS", "/v1/chat/completions", {
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        }))
        self.assertEqual(preflight.status, 204)
        self.assertEqual(self.audit.events[-1]["outcome"], "preflight_allowed")
        denied = self.broker.preflight(BrokerRequest("OPTIONS", "/v1/chat/completions", {
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        }))
        self.assertEqual(denied.status, 403)
        self.assertEqual(self.audit.events[-1]["outcome"], "preflight_denied")

    def test_declared_oversize_body_is_denied_without_materializing_it(self):
        response = self.broker.handle(BrokerRequest(
            "POST",
            "/v1/chat/completions",
            {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
            b"",
            declared_body_bytes=10_000,
        ))
        self.assertEqual(response.status, 413)
        self.assertEqual(self.audit.events[-1]["request_bytes"], 10_000)
        self.assertEqual(self.upstream.requests, [])

    def test_live_http_server_enforces_policy(self):
        server = create_server("127.0.0.1", 0, self.broker)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/health"
            allowed = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
            with urllib.request.urlopen(allowed, timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertTrue(response.headers["X-Correlation-ID"])
            with self.assertRaises(urllib.error.HTTPError) as denied:
                urllib.request.urlopen(url, timeout=2)
            self.assertEqual(denied.exception.code, 401)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_non_loopback_server_binding_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            create_server("0.0.0.0", 0, self.broker)

    def test_jsonl_audit_file_is_private_and_contains_no_request_body(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "broker.jsonl")
            sink = JsonlAuditSink(Path(path))
            broker = OMLXBroker(BrokerPolicy(TOKEN), self.upstream, sink)
            secret_body = b'{"prompt":"do-not-audit-this"}'
            response = broker.handle(BrokerRequest(
                "POST",
                "/v1/chat/completions",
                {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
                secret_body,
            ))
            self.assertEqual(response.status, 200)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            content = Path(path).read_text(encoding="utf-8")
            self.assertNotIn("do-not-audit-this", content)
            self.assertNotIn(TOKEN, content)


class OMLXUpstreamTests(unittest.TestCase):
    def test_injects_upstream_auth_and_correlation(self):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                observed["authorization"] = self.headers.get("Authorization")
                observed["correlation"] = self.headers.get("X-Correlation-ID")
                payload = b'{"status":"healthy"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            upstream = OMLXUpstream(f"http://127.0.0.1:{server.server_port}", "upstream-secret")
            response = upstream.request("GET", "/health", b"", "run-456")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        self.assertEqual(response.status, 200)
        self.assertEqual(observed["authorization"], "Bearer upstream-secret")
        self.assertEqual(observed["correlation"], "run-456")

    def test_rejects_non_loopback_upstream(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            OMLXUpstream("https://example.com", "key")


if __name__ == "__main__":
    unittest.main()
