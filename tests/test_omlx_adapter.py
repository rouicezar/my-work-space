import unittest
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from forma_ai.adapters.omlx import (
    AdapterError,
    HTTPResult,
    InstallationEvidence,
    OMLXAdapter,
    UrllibTransport,
)


INSTALLED = InstallationEvidence(True, ["/Applications/oMLX.app"])
NOT_INSTALLED = InstallationEvidence(False, [])


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def request(self, method, path, payload=None):
        self.requests.append((method, path, payload))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class OMLXAdapterTests(unittest.TestCase):
    def test_unreachable_uninstalled_is_not_reported_as_empty_models(self):
        adapter = OMLXAdapter(FakeTransport([AdapterError("UNREACHABLE", "refused")]))
        report = adapter.probe(NOT_INSTALLED)
        self.assertEqual(report.status, "not_installed")
        self.assertFalse(report.server_reachable)
        self.assertEqual(report.error["code"], "UNREACHABLE")

    def test_unreachable_installed_is_stopped(self):
        adapter = OMLXAdapter(FakeTransport([AdapterError("UNREACHABLE", "refused")]))
        self.assertEqual(adapter.probe(INSTALLED).status, "stopped")

    def test_loading_health_is_starting(self):
        adapter = OMLXAdapter(FakeTransport([HTTPResult(503, {"status": "loading"})]))
        report = adapter.probe(INSTALLED)
        self.assertEqual(report.status, "starting")
        self.assertTrue(report.server_reachable)

    def test_healthy_server_without_models_is_explicit(self):
        adapter = OMLXAdapter(
            FakeTransport([
                HTTPResult(200, {"status": "healthy"}),
                HTTPResult(200, {"object": "list", "data": []}),
            ])
        )
        report = adapter.probe(INSTALLED)
        self.assertEqual(report.status, "healthy_no_models")
        self.assertTrue(report.shallow_health)
        self.assertFalse(report.deep_probe_passed)

    def test_models_without_generation_are_only_shallow_ready(self):
        adapter = OMLXAdapter(
            FakeTransport([
                HTTPResult(200, {"status": "ok"}),
                HTTPResult(200, {"data": [{"id": "model-a"}]}),
            ])
        )
        report = adapter.probe(INSTALLED)
        self.assertEqual(report.status, "shallow_ready")
        self.assertFalse(report.deep_probe_performed)

    def test_deep_probe_success_is_ready(self):
        transport = FakeTransport([
            HTTPResult(200, {"status": "healthy"}),
            HTTPResult(200, {"data": [{"id": "model-a"}]}),
            HTTPResult(200, {"choices": [{"message": {"content": "OK"}}]}),
        ])
        report = OMLXAdapter(transport).probe(INSTALLED, deep=True)
        self.assertEqual(report.status, "ready")
        self.assertTrue(report.deep_probe_passed)
        self.assertEqual(transport.requests[-1][1], "/v1/chat/completions")
        self.assertEqual(transport.requests[-1][2]["max_tokens"], 2)

    def test_deep_probe_timeout_is_degraded_not_ready(self):
        adapter = OMLXAdapter(
            FakeTransport([
                HTTPResult(200, {"status": "healthy"}),
                HTTPResult(200, {"data": [{"id": "model-a"}]}),
                AdapterError("TIMEOUT", "generation timed out"),
            ])
        )
        report = adapter.probe(INSTALLED, deep=True)
        self.assertEqual(report.status, "degraded")
        self.assertTrue(report.shallow_health)
        self.assertFalse(report.deep_probe_passed)
        self.assertEqual(report.error["code"], "TIMEOUT")

    def test_auth_failure_is_distinct(self):
        adapter = OMLXAdapter(FakeTransport([AdapterError("AUTH_REQUIRED", "missing key", http_status=401)]))
        report = adapter.probe(INSTALLED)
        self.assertEqual(report.status, "auth_required")
        self.assertEqual(report.error["http_status"], 401)

    def test_invalid_models_shape_is_incompatible(self):
        adapter = OMLXAdapter(
            FakeTransport([
                HTTPResult(200, {"status": "healthy"}),
                HTTPResult(200, {"models": []}),
            ])
        )
        report = adapter.probe(INSTALLED)
        self.assertEqual(report.status, "incompatible")
        self.assertEqual(report.error["code"], "INVALID_MODELS")

    def test_real_http_transport_and_bearer_auth(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(("GET", self.path, self.headers.get("Authorization"), None))
                if self.path == "/health":
                    self.respond({"status": "healthy"})
                elif self.path == "/v1/models":
                    self.respond({"object": "list", "data": [{"id": "model-a"}]})
                else:
                    self.send_error(404)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length))
                requests.append(("POST", self.path, self.headers.get("Authorization"), body))
                self.respond({"choices": [{"message": {"content": "OK"}}]})

            def respond(self, body):
                payload = json.dumps(body).encode()
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
            base_url = f"http://127.0.0.1:{server.server_port}"
            adapter = OMLXAdapter(UrllibTransport(base_url, api_key="secret", timeout=1))
            report = adapter.probe(INSTALLED, deep=True)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(report.status, "ready")
        self.assertEqual([item[1] for item in requests], ["/health", "/v1/models", "/v1/chat/completions"])
        self.assertTrue(all(item[2] == "Bearer secret" for item in requests))
        self.assertEqual(requests[-1][3]["model"], "model-a")


if __name__ == "__main__":
    unittest.main()
