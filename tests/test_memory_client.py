"""P7-T06 contract tests for governed-memory loopback client."""

import json
import unittest
from unittest.mock import MagicMock

from forma_ai.memory_client import MemoryClient, MemoryClientError


TOKEN = "m" * 48


class MemoryClientTests(unittest.TestCase):
    def test_health_and_candidates_unwrap_service_envelope(self):
        calls: list[tuple[str, str, dict | None]] = []

        def open_url(request, *, timeout):
            path = request.full_url.rsplit("/", 1)[-1]
            if path == "health":
                body = {"schema_version": 1, "result": {"confirmed_authority": "semantica"}}
            else:
                body = {
                    "schema_version": 1,
                    "result": [{"candidate_id": "c-1", "status": "pending"}],
                }
            response = MagicMock()
            response.read.return_value = json.dumps(body).encode()
            response.__enter__.return_value = response
            return response

        client = MemoryClient("127.0.0.1", 43111, TOKEN, open_url=open_url)
        health = client.health("corr-1")
        candidates = client.list_candidates("corr-2")
        self.assertEqual(health["confirmed_authority"], "semantica")
        self.assertEqual(candidates[0]["candidate_id"], "c-1")

    def test_http_error_surfaces_service_code(self):
        import urllib.error

        def open_url(request, *, timeout):
            body = json.dumps({"error": {"code": "SEMANTICA_UNAVAILABLE"}}).encode()
            raise urllib.error.HTTPError(
                request.full_url, 503, "unavailable", hdrs=None,
                fp=MagicMock(read=lambda size=-1: body),
            )

        client = MemoryClient("127.0.0.1", 43111, TOKEN, open_url=open_url)
        with self.assertRaises(MemoryClientError) as raised:
            client.confirm(actor="reviewer", candidate_id="c-1", correlation_id="corr-3")
        self.assertEqual(raised.exception.code, "SEMANTICA_UNAVAILABLE")
        self.assertEqual(raised.exception.http_status, 503)

    def test_unreachable_service_fails_closed(self):
        import urllib.error

        def open_url(request, *, timeout):
            raise urllib.error.URLError("connection refused")

        client = MemoryClient("127.0.0.1", 43111, TOKEN, open_url=open_url)
        with self.assertRaises(MemoryClientError) as raised:
            client.health("corr-4")
        self.assertEqual(raised.exception.code, "MEMORY_SERVICE_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
