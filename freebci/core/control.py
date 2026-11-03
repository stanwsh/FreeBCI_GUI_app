"""Small local control plane for a running session.

The control plane is intentionally modest: a loopback TCP socket carrying
newline-delimited JSON.  It exposes read-only status, session markers, stop, a
demo-session start request, and application shutdown; it does not accept
arbitrary board commands.  LSL remains the data plane.

The server can outlive a single session: the GUI owns one server for its whole
lifetime and supplies the current ``SessionController`` through a provider.
That keeps the discovery file and token stable while the app moves between
idle and recording.  A server can also own one fixed controller, which is what
the unit tests and small scripts use.

Every server gets a random bearer token.  A client must present it, which keeps
another local process from stopping a recording by accident.  A discovery file
containing the endpoint and token can be written for scripts on the same
machine; treat that file as a secret.
"""
from __future__ import annotations

import json
import os
import secrets
import socket
import threading
import time
from typing import Any, Callable, Dict, Optional

from freebci.core.models import SessionStatus
from freebci.core.session import SessionController

PROTOCOL_VERSION = 1
MAX_REQUEST_BYTES = 64 * 1024


class ControlError(RuntimeError):
    """Raised for invalid control requests or transport failures."""

    def __init__(self, message: str, code: str = "invalid_request") -> None:
        super().__init__(message)
        self.code = code


def _encode(payload: Dict[str, Any]) -> bytes:
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


class ControlServer:
    """Loopback JSON control endpoint for an app or one fixed session."""

    def __init__(
        self,
        controller: Optional[SessionController] = None,
        host: str = "127.0.0.1",
        port: int = 0,
        token: Optional[str] = None,
        accept_timeout: float = 0.2,
        stop_callback: Optional[Callable[[], None]] = None,
        shutdown_callback: Optional[Callable[[], None]] = None,
        start_callback: Optional[Callable[[str], None]] = None,
        controller_provider: Optional[Callable[[], Optional[SessionController]]] = None,
    ) -> None:
        self.controller = controller
        self.controller_provider = controller_provider
        self.host = host
        self.token = token or secrets.token_urlsafe(24)
        self.stop_callback = stop_callback
        self.shutdown_callback = shutdown_callback
        self.start_callback = start_callback
        self.accept_timeout = accept_timeout
        self.port = int(port)
        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._start_pending = threading.Event()
        self._start_pending_until = 0.0

    def active_controller(self) -> Optional[SessionController]:
        controller = (
            self.controller_provider()
            if self.controller_provider is not None
            else self.controller
        )
        if controller is not None:
            self._start_pending.clear()
        return controller

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

    def discovery_payload(self) -> Dict[str, Any]:
        controller = self.active_controller()
        return {
            "schema": "freebci.control/1",
            "protocol": PROTOCOL_VERSION,
            "host": self.host,
            "address": self.host,
            "port": self.port,
            "token": self.token,
            "pid": os.getpid(),
            "created_wall_ns": time.time_ns(),
            "session_id": controller.config.session_id if controller is not None else "",
        }

    def write_discovery(self, path: str) -> str:
        """Atomically publish the endpoint for local scripts."""
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(self.discovery_payload(), handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        return path

    @staticmethod
    def remove_discovery(path: str) -> None:
        try:
            os.remove(path)
        except FileNotFoundError:
            return
        except OSError:
            return

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
            request_id = None
            try:
                connection.settimeout(2.0)
                request = self._read_request(connection)
                request_id = request.get("id")
                response = self._dispatch(request)
            except Exception as exc:  # noqa: BLE001 - keep the control loop alive
                response = {
                    "ok": False,
                    "error": str(exc),
                    "code": getattr(exc, "code", "internal_error"),
                }
            if request_id is not None:
                response["id"] = request_id
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
        received_ns = time.time_ns()
        if request.get("token") != self.token:
            raise ControlError("invalid control token")
        command = request.get("command")
        if command == "ping":
            return {"ok": True, "protocol": PROTOCOL_VERSION}
        if command == "time":
            client_send_ns = request.get("client_send_ns")
            if not isinstance(client_send_ns, int) or client_send_ns < 0:
                raise ControlError("time requires client_send_ns as an integer")
            return {
                "ok": True,
                "client_send_ns": client_send_ns,
                "server_receive_ns": received_ns,
                "server_send_ns": time.time_ns(),
            }
        if command == "status":
            controller = self.active_controller()
            if controller is None:
                return {"ok": True, "snapshot": _idle_snapshot_payload()}
            return {"ok": True, "snapshot": _snapshot_payload(controller)}
        if command == "start":
            if self.start_callback is None:
                raise ControlError("start is not available for this control endpoint")
            if self.active_controller() is not None:
                raise ControlError("a session is already active", code="busy")
            if self._start_pending.is_set() and time.monotonic() < self._start_pending_until:
                raise ControlError("a start request is already pending", code="busy")
            self._start_pending.clear()
            board = request.get("board")
            if board is None or not str(board).strip():
                raise ControlError("start requires a board selector")
            self._start_pending.set()
            self._start_pending_until = time.monotonic() + 30.0
            try:
                self.start_callback(str(board).strip())
            except Exception:
                self._start_pending.clear()
                raise
            return {"ok": True, "status": "start_requested", "board": str(board).strip()}
        if command == "marker":
            controller = self.active_controller()
            if controller is None:
                raise ControlError("no active session", code="no_session")
            label = request.get("label", "")
            if not isinstance(label, str):
                raise ControlError("marker label must be a string")
            marker = controller.add_marker(label, source="control")
            return {"ok": True, "marker": marker}
        if command == "shutdown":
            if self.shutdown_callback is None:
                raise ControlError("shutdown is not available for this session")
            self.shutdown_callback()
            return {"ok": True, "status": "shutdown_requested"}
        if command == "stop":
            controller = self.active_controller()
            if controller is None:
                raise ControlError("no active session", code="no_session")
            if self.stop_callback is not None:
                self.stop_callback()
                status = "stop_requested"
            else:
                result = controller.stop()
                status = result.value if isinstance(result, SessionStatus) else str(result)
            return {
                "ok": True,
                "status": status,
                "snapshot": _snapshot_payload(controller),
            }
        raise ControlError("unknown control command: %r" % (command,))


class ControlClient:
    """Tiny client for the loopback control plane."""

    def __init__(self, host: str, port: int, token: str, timeout: float = 2.0) -> None:
        self.host = host
        self.port = int(port)
        self.token = token
        self.timeout = float(timeout)
        self._next_id = 0
        self._id_lock = threading.Lock()

    def _request(self, command: str, **fields: Any) -> Dict[str, Any]:
        with self._id_lock:
            self._next_id += 1
            request_id = self._next_id
        payload_fields = {"command": command, "token": self.token, "id": request_id}
        payload_fields.update(fields)
        payload = _encode(payload_fields)
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.sendall(payload)
                sock.shutdown(socket.SHUT_WR)
                response = _read_response(sock)
        except OSError as exc:
            raise ControlError("control connection failed: %s" % exc) from exc
        if response.get("id") != request_id:
            raise ControlError("control response id does not match the request")
        if not response.get("ok"):
            raise ControlError(
                response.get("error", "control request failed"),
                code=str(response.get("code", "request_failed")),
            )
        return response

    @classmethod
    def from_discovery(cls, path: str) -> "ControlClient":
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ControlError("could not read control discovery file: %s" % exc) from exc
        if payload.get("protocol") != PROTOCOL_VERSION:
            raise ControlError("unsupported control protocol in discovery file")
        return cls(
            host=payload.get("address", "127.0.0.1"),
            port=int(payload["port"]),
            token=str(payload["token"]),
        )

    @classmethod
    def from_runtime_file(cls, path: str) -> "ControlClient":
        """Alias for :meth:`from_discovery`, matching the protocol document."""
        return cls.from_discovery(path)

    def ping(self) -> bool:
        return bool(self._request("ping").get("ok"))

    def status(self) -> Dict[str, Any]:
        return self._request("status")["snapshot"]

    def wait_started(self, timeout: float = 10.0) -> Dict[str, Any]:
        """Poll until the session is armed or recording, or raise on timeout."""
        deadline = time.monotonic() + max(0.0, float(timeout))
        while True:
            snapshot = self.status()
            if snapshot.get("state") in ("armed", "recording"):
                return snapshot
            if snapshot.get("state") == "failed":
                raise ControlError(snapshot.get("error") or "session failed to start")
            if time.monotonic() >= deadline:
                raise ControlError("timed out waiting for the session to start")
            time.sleep(0.05)

    def marker(self, label: str) -> Dict[str, Any]:
        return self._request("marker", label=label)["marker"]

    def start(self, board: Any) -> str:
        return self._request("start", board=str(board))["status"]

    def clock_offset(self, samples: int = 5) -> Dict[str, Any]:
        """Estimate server-minus-client clock offset and its uncertainty.

        The estimate is only meaningful for endpoints on the same host; the
        round-trip term is still reported so callers can reject noisy samples.
        """
        count = max(1, int(samples))
        best = None
        for _ in range(count):
            client_send_ns = time.time_ns()
            response = self._request("time", client_send_ns=client_send_ns)
            client_receive_ns = time.time_ns()
            server_receive_ns = int(response["server_receive_ns"])
            server_send_ns = int(response["server_send_ns"])
            round_trip_ns = max(
                0,
                (client_receive_ns - client_send_ns)
                - (server_send_ns - server_receive_ns),
            )
            offset_ns = int(
                (
                    (server_receive_ns - client_send_ns)
                    + (server_send_ns - client_receive_ns)
                )
                / 2
            )
            if best is None or round_trip_ns < best["round_trip_ns"]:
                best = {
                    "offset_ns": offset_ns,
                    "uncertainty_ns": round_trip_ns // 2,
                    "round_trip_ns": round_trip_ns,
                    "samples": count,
                }
        return best

    def stop(self) -> str:
        return self._request("stop")["status"]

    def shutdown(self) -> str:
        return self._request("shutdown")["status"]


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
        "lost_samples": snapshot.lost_samples,
        "seconds_since_block": snapshot.seconds_since_block,
        "markers": snapshot.markers,
        "last_block_wall_ns": snapshot.last_block_wall_ns,
        "last_sample_time_ns": snapshot.last_sample_time_ns,
        "clock_id": "host-monotonic",
        "monotonic_ns": time.monotonic_ns(),
        "wall_ns": time.time_ns(),
        "error": snapshot.error,
        "output_path": snapshot.output_path,
    }


def _idle_snapshot_payload() -> Dict[str, Any]:
    """Stable status shape while the application is idle."""
    return {
        "state": "idle",
        "session_id": "",
        "channel_count": 0,
        "sample_count": 0,
        "blocks": 0,
        "elapsed_seconds": 0.0,
        "display_dropped_samples": 0,
        "lost_samples": 0,
        "seconds_since_block": 0.0,
        "markers": 0,
        "last_block_wall_ns": 0,
        "last_sample_time_ns": 0,
        "clock_id": "host-monotonic",
        "monotonic_ns": time.monotonic_ns(),
        "wall_ns": time.time_ns(),
        "error": "",
        "output_path": "",
    }
