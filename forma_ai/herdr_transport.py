"""Official Herdr v0.8.2 socket transport (newline-delimited JSON, protocol 20)."""

from __future__ import annotations

import json
import os
import socket
import uuid
from typing import Callable, Mapping

SUPPORTED_PROTOCOL = 20


class HerdrTransportError(RuntimeError):
    """The Herdr socket could not be reached or spoke malformed JSON."""


class HerdrProtocolError(RuntimeError):
    """The Herdr server failed the fail-closed protocol compatibility gate."""


class HerdrRequestError(RuntimeError):
    """The Herdr server returned an error response for a request."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def validate_pong(pong: object) -> None:
    if not isinstance(pong, dict):
        raise HerdrProtocolError("Herdr ping did not return a pong payload")
    if pong.get("type") != "pong":
        raise HerdrProtocolError(
            f"Herdr ping returned payload type {pong.get('type')!r}"
        )
    protocol = pong.get("protocol")
    if protocol != SUPPORTED_PROTOCOL:
        raise HerdrProtocolError(
            f"Herdr server protocol {protocol!r} is not supported; "
            f"expected {SUPPORTED_PROTOCOL}"
        )


def resolve_socket_path(
    *,
    socket_path: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: str | None = None,
) -> str:
    env = os.environ if environ is None else environ
    if socket_path is not None:
        return socket_path
    override = env.get("HERDR_SOCKET_PATH")
    if override:
        return override
    base = os.path.expanduser("~") if home is None else home
    config_root = os.path.join(base, ".config", "herdr")
    session = env.get("HERDR_SESSION")
    if session:
        return os.path.join(config_root, "sessions", session, "herdr.sock")
    return os.path.join(config_root, "herdr.sock")


def _connect_unix_socket(path: str, timeout: float) -> socket.socket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(path)
    return sock


class HerdrSocketTransport:
    """Request callable for HerdrAdapter backed by the official socket API.

    One connection per request; the response is located by the first line
    carrying a ``result`` or ``error`` key because error responses may carry
    an empty ``id`` and unsolicited event lines carry none at all. The server
    protocol is verified via ping before first use and fails closed.
    """

    def __init__(
        self,
        *,
        socket_path: str | None = None,
        environ: Mapping[str, str] | None = None,
        socket_factory: Callable[[str], socket.socket] | None = None,
        request_timeout: float = 5.0,
    ) -> None:
        self._socket_path = socket_path
        self._environ = environ
        if socket_factory is None:
            timeout = request_timeout

            def socket_factory(path: str) -> socket.socket:
                return _connect_unix_socket(path, timeout)

        self._socket_factory = socket_factory
        self._protocol_verified = False

    def __call__(
        self, method: str, params: dict[str, object]
    ) -> dict[str, object]:
        if not self._protocol_verified:
            self.probe()
            self._protocol_verified = True
        return self._unwrap(self._exchange(method, params), method)

    def probe(self) -> dict[str, object]:
        try:
            pong = self._unwrap(self._exchange("ping", {}), "ping")
        except HerdrRequestError as exc:
            raise HerdrProtocolError(
                f"Herdr server rejected the ping handshake: {exc}"
            ) from exc
        validate_pong(pong)
        return pong

    def _exchange(self, method: str, params: dict[str, object]) -> dict[str, object]:
        path = resolve_socket_path(
            socket_path=self._socket_path, environ=self._environ
        )
        payload = {"id": uuid.uuid4().hex, "method": method, "params": params}
        try:
            sock = self._socket_factory(path)
        except OSError as exc:
            raise HerdrTransportError(
                f"cannot connect to Herdr socket {path}: {exc}"
            ) from exc
        with sock:
            try:
                sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
                response = self._read_response(sock)
            except OSError as exc:
                raise HerdrTransportError(
                    f"Herdr socket {path} failed: {exc}"
                ) from exc
        return response

    @staticmethod
    def _read_response(sock: socket.socket) -> dict[str, object]:
        buffer = b""
        while True:
            while b"\n" not in buffer:
                chunk = sock.recv(4096)
                if not chunk:
                    raise HerdrTransportError(
                        "Herdr connection closed before a response line"
                    )
                buffer += chunk
            line, _, buffer = buffer.partition(b"\n")
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            try:
                message = json.loads(text)
            except ValueError as exc:
                raise HerdrTransportError(
                    f"malformed Herdr response line: {text!r}"
                ) from exc
            if isinstance(message, dict) and ("result" in message or "error" in message):
                return message

    @staticmethod
    def _unwrap(response: dict[str, object], method: str) -> dict[str, object]:
        if "error" in response:
            error = response["error"]
            if not isinstance(error, dict):
                raise HerdrTransportError(
                    f"malformed Herdr error response for {method}"
                )
            raise HerdrRequestError(
                str(error.get("code", "HERDR_ERROR")),
                str(error.get("message", "")),
            )
        result = response.get("result")
        if not isinstance(result, dict):
            raise HerdrTransportError(
                f"Herdr response for {method} has no result payload"
            )
        return result


class HerdrSubscriptionListener:
    """Dedicated long-lived connection carrying one Herdr event subscription.

    Herdr closes a request connection right after its response, so a
    subscription cannot share the request path: the subscription socket stays
    open past its ``subscription_started`` ack and pushes unsolicited
    ``{"event": ..., "data": ...}`` envelopes until the server goes away. The
    server supports one subscription per connection.
    """

    def __init__(
        self,
        *,
        socket_path: str | None = None,
        environ: Mapping[str, str] | None = None,
        socket_factory: Callable[[str], socket.socket] | None = None,
        subscribe_timeout: float = 5.0,
    ) -> None:
        self._socket_path = socket_path
        self._environ = environ
        if socket_factory is None:
            timeout = subscribe_timeout

            def socket_factory(path: str) -> socket.socket:
                return _connect_unix_socket(path, timeout)

        self._socket_factory = socket_factory
        self._stopped = False
        self._socket: socket.socket | None = None
        self._read_buffer = b""

    def subscribe(
        self,
        subscriptions: list[dict[str, object]],
        on_event: Callable[[dict[str, object]], None],
    ) -> None:
        self._stopped = False
        path = resolve_socket_path(
            socket_path=self._socket_path, environ=self._environ
        )
        payload = {
            "id": uuid.uuid4().hex,
            "method": "events.subscribe",
            "params": {"subscriptions": list(subscriptions)},
        }
        try:
            sock = self._socket_factory(path)
        except OSError as exc:
            raise HerdrTransportError(
                f"cannot connect to Herdr socket {path}: {exc}"
            ) from exc
        self._socket = sock
        self._read_buffer = b""
        try:
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            self._validate_ack(self._read_message(sock))
            while not self._stopped:
                message = self._read_message(sock)
                if isinstance(message, dict) and "event" in message and "data" in message:
                    on_event(message)
        except OSError as exc:
            if self._stopped:
                return
            raise HerdrTransportError(
                f"Herdr subscription socket {path} failed: {exc}"
            ) from exc
        finally:
            self._socket = None
            sock.close()

    def stop(self) -> None:
        """Close the subscription connection from this or another thread."""
        self._stopped = True
        sock = self._socket
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    @staticmethod
    def _validate_ack(message: object) -> None:
        if not isinstance(message, dict):
            raise HerdrTransportError("malformed Herdr subscription ack")
        if "error" in message:
            error = message["error"]
            if not isinstance(error, dict):
                raise HerdrTransportError(
                    "malformed Herdr subscription error response"
                )
            raise HerdrRequestError(
                str(error.get("code", "HERDR_ERROR")),
                str(error.get("message", "")),
            )
        result = message.get("result")
        if not isinstance(result, dict) or result.get("type") != "subscription_started":
            raise HerdrProtocolError(
                "Herdr events.subscribe did not confirm subscription_started"
            )

    def _read_message(self, sock: socket.socket) -> dict[str, object]:
        while True:
            while b"\n" not in self._read_buffer:
                chunk = sock.recv(4096)
                if not chunk:
                    raise HerdrTransportError(
                        "Herdr subscription connection closed"
                    )
                self._read_buffer += chunk
            line, _, self._read_buffer = self._read_buffer.partition(b"\n")
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            try:
                message = json.loads(text)
            except ValueError as exc:
                raise HerdrTransportError(
                    f"malformed Herdr subscription line: {text!r}"
                ) from exc
            if isinstance(message, dict):
                return message
