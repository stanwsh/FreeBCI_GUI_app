"""Minimal standard-library client for the FreeBCI control socket.

This script shows the wire format directly, so the same request/response
exchange can be implemented in MATLAB, C#, JavaScript, or another language.
It does not import ``freebci`` or PyQt5.

The transport is one newline-delimited JSON object per request on loopback TCP.
The running GUI publishes the address and token in ``control.json``.  See
``examples/README.md`` for the full command table and the async start/stop flow.

Examples::

    python examples/raw_control.py ping
    python examples/raw_control.py status
    python examples/raw_control.py start demo
    python examples/raw_control.py marker "stimulus onset"
    python examples/raw_control.py stop
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class RawControlError(RuntimeError):
    """A wire-level error, including the server's stable error code."""

    def __init__(self, message: str, code: str = "invalid_request") -> None:
        super().__init__(message)
        self.code = code


def _candidate_discovery_paths() -> Iterable[Path]:
    explicit = os.environ.get("FREEBCI_CONTROL_FILE")
    if explicit:
        yield Path(explicit).expanduser()

    home = os.environ.get("FREEBCI_HOME")
    if home:
        yield Path(home).expanduser() / "control.json"

    yield Path.home() / "Documents" / "FreeBCI" / "control.json"
    yield Path.cwd() / "logs" / "control.json"


def resolve_discovery(explicit: Optional[str] = None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_dir():
            path = path / "control.json"
        if not path.is_file():
            raise FileNotFoundError("control discovery file not found: %s" % path)
        return path

    candidates = list(_candidate_discovery_paths())
    for path in candidates:
        if path.is_file():
            return path
    tried = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "could not find control.json; start the FreeBCI GUI or pass "
        "--discovery PATH. Tried: %s" % tried
    )


def load_discovery(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RawControlError("control.json must contain a JSON object")
    return payload


class RawControlClient:
    """One request per TCP connection, exactly like the built-in client."""

    def __init__(self, host: str, port: int, token: str, timeout: float = 2.0) -> None:
        self.host = host
        self.port = int(port)
        self.token = token
        self.timeout = float(timeout)
        self._next_id = 0

    def request(self, command: str, **fields: Any) -> Dict[str, Any]:
        self._next_id += 1
        request_id = self._next_id
        payload: Dict[str, Any] = {
            "command": command,
            "token": self.token,
            "id": request_id,
        }
        payload.update(fields)
        wire = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")

        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.sendall(wire)
                sock.shutdown(socket.SHUT_WR)
                raw = sock.makefile("rb").readline()
        except OSError as exc:
            raise RawControlError("control connection failed: %s" % exc) from exc
        if not raw:
            raise RawControlError("control server returned an empty response")
        try:
            response = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RawControlError("control response is not valid JSON") from exc
        if not isinstance(response, dict):
            raise RawControlError("control response must be a JSON object")
        if response.get("id") != request_id:
            raise RawControlError("control response id does not match the request")
        if not response.get("ok"):
            raise RawControlError(
                str(response.get("error", "control request failed")),
                code=str(response.get("code", "request_failed")),
            )
        return response


def resolve_endpoint(args: argparse.Namespace):
    """Return (host, port, token) from explicit flags or control.json."""
    need_file = args.discovery or not (args.host and args.port and args.token)
    if not need_file:
        return args.host, args.port, args.token

    path = resolve_discovery(args.discovery)
    payload = load_discovery(str(path))
    host = args.host or payload.get("host")
    if not host:
        # Older discovery files only had a tcp://host:port address string.
        address = str(payload.get("address", ""))
        if address.startswith("tcp://"):
            address = address[6:]
        host = address.rsplit(":", 1)[0] if address else "127.0.0.1"
    try:
        port = int(args.port or payload["port"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RawControlError("control.json has no valid port") from exc
    token = args.token or payload.get("token")
    if not token:
        raise RawControlError("control.json has no token")
    print("discovery: %s" % path, file=sys.stderr)
    return str(host), port, str(token)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--discovery", help="path to control.json")
    parser.add_argument("--host", help="override the address from control.json")
    parser.add_argument("--port", type=int, help="override the port")
    parser.add_argument("--token", help="override the token")
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("ping", help="check the endpoint")
    commands.add_parser("status", help="read the current session snapshot")
    start = commands.add_parser("start", help="request a session start")
    start.add_argument("board", help="board id, catalog name, or 'demo'")
    marker = commands.add_parser("marker", help="append a marker")
    marker.add_argument("label")
    commands.add_parser("stop", help="request a stop")
    commands.add_parser("shutdown", help="request GUI shutdown")
    commands.add_parser("time", help="exchange timestamps for offset estimation")
    return parser


def run(args: argparse.Namespace) -> int:
    host, port, token = resolve_endpoint(args)
    client = RawControlClient(host, port, token)

    if args.command == "start":
        response = client.request("start", board=args.board)
    elif args.command == "marker":
        response = client.request("marker", label=args.label)
    elif args.command == "time":
        response = client.request("time", client_send_ns=time.time_ns())
    else:
        response = client.request(args.command)
    print(json.dumps(response, indent=2, sort_keys=True))
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2
    try:
        return run(args)
    except RawControlError as exc:
        print("control error [%s]: %s" % (exc.code, exc), file=sys.stderr)
        return 2
    except (FileNotFoundError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
