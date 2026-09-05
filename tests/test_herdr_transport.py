import json
import os
import subprocess
import time
import unittest
import uuid
from unittest.mock import Mock, patch
from forma_ai.herdr_transport import _connect_unix_socket


class FailedConnectionCleanupTests(unittest.TestCase):
    def test_failed_reconnect_closes_allocated_socket(self):
        sock = Mock()
        sock.connect.side_effect = FileNotFoundError('runtime stopped')
        with patch('forma_ai.herdr_transport.socket.socket', return_value=sock):
            with self.assertRaises(FileNotFoundError):
                _connect_unix_socket('/fixture/missing.sock', 1)
        sock.close.assert_called_once()

from forma_ai.herdr_transport import (
    SUPPORTED_PROTOCOL,
    HerdrProtocolError,
    HerdrRequestError,
    HerdrSubscriptionListener,
    HerdrSocketTransport,
    HerdrTransportError,
    resolve_socket_path,
)


def _pong(protocol=SUPPORTED_PROTOCOL, **overrides):
    payload = {
        "type": "pong",
        "version": "0.8.2",
        "protocol": protocol,
        "capabilities": {"live_handoff": True, "detached_server_daemon": False},
    }
    payload.update(overrides)
    return payload


class FakeSocket:
    def __init__(self, path, lines, sent):
        self.path = path
        self.timeout = None
        self.closed = False
        self.sent_count = 0
        self._lines = lines
        self._sent = sent
        self._out = b""

    def settimeout(self, value):
        self.timeout = value

    def sendall(self, data):
        self.sent_count += 1
        self._sent.append((self.path, json.loads(data.decode("utf-8"))))
        for line in self._lines:
            if isinstance(line, bytes):
                self._out += line
            else:
                self._out += (json.dumps(line) + "\n").encode("utf-8")

    def recv(self, size):
        chunk = self._out[:size]
        self._out = self._out[size:]
        return chunk

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
        return False


class FakeSocketFactory:
    """Hands out one scripted socket (or raises) per connection attempt."""

    def __init__(self, scripts):
        self._scripts = list(scripts)
        self.sockets = []
        self.sent = []

    def __call__(self, path):
        script = self._scripts.pop(0) if self._scripts else []
        if isinstance(script, Exception):
            raise script
        sock = FakeSocket(path, script, self.sent)
        self.sockets.append(sock)
        return sock


def make_transport(scripts):
    factory = FakeSocketFactory(scripts)
    transport = HerdrSocketTransport(
        socket_path="/tmp/fake-herdr/herdr.sock",
        environ={},
        socket_factory=factory,
    )
    return transport, factory


class HerdrSocketTransportTests(unittest.TestCase):
    def test_first_use_verifies_protocol_then_sends_request(self):
        transport, factory = make_transport(
            [
                [{"id": "any", "result": _pong()}],
                [{"id": "any", "result": {"type": "agent_info", "agent": {}}}],
            ]
        )

        response = transport("agent.get", {"target": "pane-001"})

        self.assertEqual(response, {"type": "agent_info", "agent": {}})
        self.assertEqual(len(factory.sent), 2)
        ping_envelope = factory.sent[0][1]
        self.assertEqual(ping_envelope["method"], "ping")
        self.assertEqual(ping_envelope["params"], {})
        self.assertIsInstance(ping_envelope["id"], str)
        self.assertNotEqual(ping_envelope["id"], "")
        request_envelope = factory.sent[1][1]
        self.assertEqual(request_envelope["method"], "agent.get")
        self.assertEqual(request_envelope["params"], {"target": "pane-001"})
        for envelope in (ping_envelope, request_envelope):
            self.assertEqual(set(envelope), {"id", "method", "params"})
        self.assertEqual(len(factory.sockets), 2)
        for sock in factory.sockets:
            self.assertEqual(sock.sent_count, 1)
            self.assertTrue(sock.closed)

    def test_protocol_verified_once_across_requests(self):
        transport, factory = make_transport(
            [
                [{"id": "x", "result": _pong()}],
                [{"id": "x", "result": {"type": "agent_info"}}],
                [{"id": "x", "result": {"type": "agent_info"}}],
            ]
        )

        transport("agent.get", {})
        transport("agent.get", {})

        self.assertEqual(len(factory.sent), 3)
        self.assertEqual(
            [envelope["method"] for _path, envelope in factory.sent],
            ["ping", "agent.get", "agent.get"],
        )

    def test_unsolicited_event_lines_are_skipped(self):
        transport, _factory = make_transport(
            [
                [
                    {"event": "pane.updated", "data": {}},
                    {"id": "x", "result": _pong()},
                ],
                [
                    {"event": "agent.output", "data": {"text": "hi"}},
                    {"id": "x", "result": {"type": "ok"}},
                ],
            ]
        )

        response = transport("pane.send_keys", {"pane_id": "p", "keys": ["ctrl+c"]})

        self.assertEqual(response, {"type": "ok"})

    def test_error_response_raises_request_error_even_with_empty_id(self):
        transport, _factory = make_transport(
            [
                [{"id": "x", "result": _pong()}],
                [
                    {
                        "id": "",
                        "error": {"code": "unknown_method", "message": "no such method"},
                    }
                ],
            ]
        )

        with self.assertRaises(HerdrRequestError) as ctx:
            transport("not.a.method", {})

        self.assertEqual(ctx.exception.code, "unknown_method")
        self.assertEqual(ctx.exception.message, "no such method")

    def test_protocol_mismatch_fails_closed_on_every_call(self):
        transport, _factory = make_transport(
            [
                [{"id": "x", "result": _pong(protocol=SUPPORTED_PROTOCOL - 1)}],
                [{"id": "x", "result": _pong(protocol=SUPPORTED_PROTOCOL - 1)}],
            ]
        )

        with self.assertRaises(HerdrProtocolError):
            transport("session.snapshot", {})
        with self.assertRaises(HerdrProtocolError):
            transport("session.snapshot", {})

    def test_non_pong_ping_payload_fails_closed(self):
        transport, _factory = make_transport(
            [[{"id": "x", "result": {"type": "unexpected"}}]]
        )

        with self.assertRaises(HerdrProtocolError):
            transport("session.snapshot", {})

    def test_probe_raises_protocol_error_when_ping_is_rejected(self):
        transport, _factory = make_transport(
            [[{"id": "", "error": {"code": "internal_error", "message": "boom"}}]]
        )

        with self.assertRaises(HerdrProtocolError):
            transport.probe()

    def test_probe_returns_validated_pong_payload(self):
        transport, _factory = make_transport([[{"id": "x", "result": _pong()}]])

        pong = transport.probe()

        self.assertEqual(pong["type"], "pong")
        self.assertEqual(pong["protocol"], SUPPORTED_PROTOCOL)

    def test_unreachable_socket_raises_transport_error(self):
        transport, _factory = make_transport([ConnectionRefusedError("refused")])

        with self.assertRaises(HerdrTransportError):
            transport("agent.get", {})

    def test_malformed_response_line_raises_transport_error(self):
        transport, _factory = make_transport([[b"@@@not json@@@\n"]])

        with self.assertRaises(HerdrTransportError):
            transport("agent.get", {})

    def test_connection_closed_before_response_raises_transport_error(self):
        transport, _factory = make_transport(
            [
                [{"id": "x", "result": _pong()}],
                [],
            ]
        )

        with self.assertRaises(HerdrTransportError):
            transport("agent.get", {})


def _agent_status_event(agent_status, pane_id="pane-001", workspace_id="workspace-001"):
    return {
        "event": "pane.agent_status_changed",
        "data": {
            "pane_id": pane_id,
            "workspace_id": workspace_id,
            "agent_status": agent_status,
        },
    }


def make_listener(factory):
    return HerdrSubscriptionListener(
        socket_path="/tmp/fake-herdr/herdr.sock",
        environ={},
        socket_factory=factory,
    )


class HerdrSubscriptionListenerTests(unittest.TestCase):
    def test_subscribe_streams_dotted_events_until_connection_closes(self):
        factory = FakeSocketFactory(
            [
                [
                    {"id": "any", "result": {"type": "subscription_started"}},
                    _agent_status_event("working"),
                    _agent_status_event("idle"),
                ]
            ]
        )
        listener = make_listener(factory)
        received = []

        with self.assertRaises(HerdrTransportError):
            listener.subscribe(
                [{"type": "pane.agent_status_changed", "pane_id": "pane-001"}],
                received.append,
            )

        self.assertEqual(len(factory.sockets), 1)
        self.assertEqual(len(factory.sent), 1)
        _path, envelope = factory.sent[0]
        self.assertEqual(envelope["method"], "events.subscribe")
        self.assertEqual(
            envelope["params"],
            {
                "subscriptions": [
                    {"type": "pane.agent_status_changed", "pane_id": "pane-001"}
                ]
            },
        )
        self.assertEqual(set(envelope), {"id", "method", "params"})
        self.assertIsInstance(envelope["id"], str)
        self.assertNotEqual(envelope["id"], "")
        self.assertEqual(
            received,
            [_agent_status_event("working"), _agent_status_event("idle")],
        )
        self.assertTrue(factory.sockets[0].closed)

    def test_stop_from_event_callback_ends_subscription_without_error(self):
        factory = FakeSocketFactory(
            [
                [
                    {"id": "any", "result": {"type": "subscription_started"}},
                    _agent_status_event("working"),
                    _agent_status_event("idle"),
                ]
            ]
        )
        listener = make_listener(factory)
        received = []

        def on_event(event):
            received.append(event)
            listener.stop()

        listener.subscribe(
            [{"type": "pane.agent_status_changed", "pane_id": "pane-001"}],
            on_event,
        )

        self.assertEqual(received, [_agent_status_event("working")])
        self.assertTrue(factory.sockets[0].closed)

    def test_subscribe_error_response_raises_request_error(self):
        factory = FakeSocketFactory(
            [
                [
                    {
                        "id": "",
                        "error": {"code": "internal_error", "message": "boom"},
                    }
                ]
            ]
        )
        listener = make_listener(factory)

        with self.assertRaises(HerdrRequestError) as ctx:
            listener.subscribe(
                [{"type": "pane.agent_status_changed"}], lambda _event: None
            )

        self.assertEqual(ctx.exception.code, "internal_error")
        self.assertEqual(ctx.exception.message, "boom")

    def test_unexpected_ack_payload_fails_closed(self):
        factory = FakeSocketFactory(
            [[{"id": "any", "result": {"type": "agent_info"}}]]
        )
        listener = make_listener(factory)

        with self.assertRaises(HerdrProtocolError):
            listener.subscribe(
                [{"type": "pane.agent_status_changed"}], lambda _event: None
            )

    def test_unreachable_socket_raises_transport_error(self):
        factory = FakeSocketFactory([ConnectionRefusedError("refused")])
        listener = make_listener(factory)

        with self.assertRaises(HerdrTransportError):
            listener.subscribe(
                [{"type": "pane.agent_status_changed"}], lambda _event: None
            )

    def test_malformed_event_line_raises_transport_error(self):
        factory = FakeSocketFactory(
            [
                [
                    {"id": "any", "result": {"type": "subscription_started"}},
                    b"@@@not json@@@\n",
                ]
            ]
        )
        listener = make_listener(factory)

        with self.assertRaises(HerdrTransportError):
            listener.subscribe(
                [{"type": "pane.agent_status_changed"}], lambda _event: None
            )


class ResolveSocketPathTests(unittest.TestCase):
    HOME = "/home/tester"

    def test_explicit_path_wins_over_environment(self):
        self.assertEqual(
            resolve_socket_path(
                socket_path="/explicit/herdr.sock",
                environ={"HERDR_SOCKET_PATH": "/env/herdr.sock", "HERDR_SESSION": "work"},
                home=self.HOME,
            ),
            "/explicit/herdr.sock",
        )

    def test_env_socket_path_beats_session_and_default(self):
        self.assertEqual(
            resolve_socket_path(
                environ={"HERDR_SOCKET_PATH": "/env/herdr.sock", "HERDR_SESSION": "work"},
                home=self.HOME,
            ),
            "/env/herdr.sock",
        )

    def test_named_session_uses_sessions_directory(self):
        self.assertEqual(
            resolve_socket_path(environ={"HERDR_SESSION": "work"}, home=self.HOME),
            "/home/tester/.config/herdr/sessions/work/herdr.sock",
        )

    def test_default_session_socket(self):
        self.assertEqual(
            resolve_socket_path(environ={}, home=self.HOME),
            "/home/tester/.config/herdr/herdr.sock",
        )

    def test_empty_env_values_fall_through_to_default(self):
        self.assertEqual(
            resolve_socket_path(
                environ={"HERDR_SOCKET_PATH": "", "HERDR_SESSION": ""},
                home=self.HOME,
            ),
            "/home/tester/.config/herdr/herdr.sock",
        )


def _find_herdr_binary():
    candidates = (
        os.environ.get("FORMA_HERDR_TEST_BINARY"),
        os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "Forma AI",
            "cache",
            "downloads",
            "herdr-macos-aarch64",
        ),
    )
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


@unittest.skipUnless(_find_herdr_binary(), "verified Herdr artifact binary is not available")
class HerdrSocketTransportLiveTests(unittest.TestCase):
    def setUp(self):
        from forma_ai.herdr_adapter import HerdrAdapter

        self.HerdrAdapter = HerdrAdapter
        self.binary = _find_herdr_binary()
        self.session_name = f"forma-p3t11-test-{uuid.uuid4().hex[:8]}"
        self.socket_path = os.path.join(
            os.path.expanduser("~"),
            ".config",
            "herdr",
            "sessions",
            self.session_name,
            "herdr.sock",
        )
        self.server = None
        try:
            self.server = subprocess.Popen(
                [self.binary, "--session", self.session_name, "server"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            deadline = time.monotonic() + 15.0
            while not os.path.exists(self.socket_path):
                if time.monotonic() > deadline:
                    raise AssertionError("Herdr test server socket did not appear")
                if self.server.poll() is not None:
                    raise AssertionError(
                        f"Herdr test server exited early with {self.server.returncode}"
                    )
                time.sleep(0.1)
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        for args in (
            ["session", "stop", self.session_name, "--json"],
            ["session", "delete", self.session_name, "--json"],
        ):
            subprocess.run(
                [self.binary, *args],
                capture_output=True,
                timeout=30,
            )
        if self.server is not None and self.server.poll() is None:
            self.server.terminate()
            try:
                self.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server.kill()
                self.server.wait(timeout=5)

    def test_live_ping_and_session_snapshot(self):
        transport = HerdrSocketTransport(socket_path=self.socket_path, environ={})

        pong = transport.probe()
        snapshot_response = transport("session.snapshot", {})

        self.assertEqual(pong["type"], "pong")
        self.assertEqual(pong["protocol"], SUPPORTED_PROTOCOL)
        self.assertEqual(pong["version"], "0.8.2")
        self.assertEqual(snapshot_response["type"], "session_snapshot")
        snapshot = snapshot_response["snapshot"]
        self.assertEqual(snapshot["protocol"], SUPPORTED_PROTOCOL)
        self.assertEqual(snapshot["agents"], [])
        self.assertEqual(snapshot["panes"], [])

    def test_live_adapter_availability_reports_ready(self):
        transport = HerdrSocketTransport(socket_path=self.socket_path, environ={})
        adapter = self.HerdrAdapter(
            executable_finder=lambda _name: self.binary,
            clock=lambda: "2026-09-01T00:00:00Z",
            probe=transport.probe,
        )

        availability = adapter.availability()

        self.assertTrue(availability.installed)
        self.assertEqual(availability.health.status, "ready")
        self.assertTrue(availability.health.reachable)
        self.assertTrue(availability.health.ready)
        self.assertEqual(availability.health.proof, "ping_pong_verified")


if __name__ == "__main__":
    unittest.main()
