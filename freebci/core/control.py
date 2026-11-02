"""Small local control plane for a running session.

The control plane is intentionally modest: a loopback TCP socket carrying
newline-delimited JSON.  It exposes read-only status plus a stop command; it
does not accept arbitrary board commands.  LSL remains the data plane.

Every server gets a random bearer token.  A client must present it, which keeps
another local process from stopping a recording by accident.
"""
from __future__ import annotations

import json
import secrets
import socket
import threading
from typing import Any, Dict, Optional

from freebci.core.models import SessionStatus
from freebci.core.session import SessionController

PROTOCOL_VERSION = 1
MAX_REQUEST_BYTES = 64 * 1024


class ControlError(RuntimeError):
    """Raised for invalid control requests or transport failures."""


def _encode(payload: Dict[str, Any]) -> bytes:
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


class ControlServer:
    """Loopback JSON control endpoint owned by one ``SessionController``."""

    def __init__(
        self,
        controller: SessionController,
        host: str = "127.0.0.1",
        port: int = 0,
        token: Optional[str] = None,
        accept_timeout: float = 0.2,
    ) -> None:
        self.controller = controller
        self.host = host
        self.token = token or secrets.token_urlsafe(24)
        self.accept_timeout = accept_timeout
        self.port = int(port)
        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    @property
    def address(self) -> str:
        return "tcp://%s:%d" % (self.host, self.port)

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self._thread is not None:
            raise ControlError("control server is already started")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(4)
        sock.settimeout(self.accept_timeout)
        self._socket = sock
        self.port = int(sock.getsockname()[1])
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="freebci-control",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            sock = self._socket
            if sock is None:
                return
            try:
                connection, _ = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                connection.settimeout(2.0)
                request = self._read_request(connection)
                response = self._dispatch(request)
            except Exception as exc:  # noqa: BLE001 - keep the control loop alive
                response = {"ok": False, "error": str(exc)}
            try:
                connection.sendall(_encode(response))
            except OSError:
                pass
            finally:
                try:
                    connection.close()
                except OSError:
                    pass

    @staticmethod
    def _read_request(connection: socket.socket) -> Dict[str, Any]:
        chunks = []
        size = 0
        while b"\n" not in b"".join(chunks):
            chunk = connection.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_REQUEST_BYTES:
                raise ControlError("control request is too large")
        raw = b"".join(chunks).split(b"\n", 1)[0]
        if not raw:
            raise ControlError("empty control request")
        try:
            request = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ControlError("control request is not valid JSON") from exc
        if not isinstance(request, dict):
            raise ControlError("control request must be a JSON object")
        return request

    def _dispatch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if request.get("token") != self.token:
            raise ControlError("invalid control token")
        command = request.get("command")
        if command == "ping":
            return {"ok": True, "protocol": PROTOCOL_VERSION}
        if command == "status":
            return {"ok": True, "snapshot": _snapshot_payload(self.controller)}
        if command == "stop":
            status = self.controller.stop()
            return {
                "ok": True,
                "status": status.value if isinstance(status, SessionStatus) else str(status),
                "snapshot": _snapshot_payload(self.controller),
            }
        raise ControlError("unknown control command: %r" % (command,))


class ControlClient:
    """Tiny client for the loopback control plane."""

    def __init__(self, host: str, port: int, token: str, timeout: float = 2.0) -> None:
        self.host = host
        self.port = int(port)
        self.token = token
        self.timeout = float(timeout)

    def _request(self, command: str) -> Dict[str, Any]:
        payload = _encode({"command": command, "token": self.token})
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.sendall(payload)
                sock.shutdown(socket.SHUT_WR)
                response = _read_response(sock)
        except OSError as exc:
            raise ControlError("control connection failed: %s" % exc) from exc
        if not response.get("ok"):
            raise ControlError(response.get("error", "control request failed"))
        return response

    def ping(self) -> bool:
        return bool(self._request("ping").get("ok"))

    def status(self) -> Dict[str, Any]:
        return self._request("status")["snapshot"]

    def stop(self) -> str:
        return self._request("stop")["status"]


def _read_response(sock: socket.socket) -> Dict[str, Any]:
    chunks = []
    size = 0
    while b"\n" not in b"".join(chunks):
        chunk = sock.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > MAX_REQUEST_BYTES:
            raise ControlError("control response is too large")
    raw = b"".join(chunks).split(b"\n", 1)[0]
    if not raw:
        raise ControlError("control server returned an empty response")
    try:
        response = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ControlError("control response is not valid JSON") from exc
    if not isinstance(response, dict):
        raise ControlError("control response must be a JSON object")
    return response


def _snapshot_payload(controller: SessionController) -> Dict[str, Any]:
    snapshot = controller.snapshot()
    return {
        "state": snapshot.state.value,
        "session_id": snapshot.session_id,
        "channel_count": controller.config.channel_count,
        "sample_count": snapshot.sample_count,
        "blocks": snapshot.blocks,
        "elapsed_seconds": snapshot.elapsed_seconds,
        "display_dropped_samples": snapshot.display_dropped_samples,
        "error": snapshot.error,
        "output_path": snapshot.output_path,
    }
