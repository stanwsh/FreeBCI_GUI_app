"""Drive a running FreeBCI GUI from another Python process.

The GUI publishes a loopback control endpoint in ``control.json``.  This script
uses ``freebci.core.ControlClient`` to read status, start a session, add a
marker, stop, and optionally shut the GUI down.

Examples (run from the repository root)::

    python examples/control_client.py status
    python examples/control_client.py demo --duration 5 --marker baseline
    python examples/control_client.py marker "stimulus onset"
    python examples/control_client.py stop

Use ``--discovery PATH`` (or ``FREEBCI_CONTROL_FILE``) when the file is not in
the default FreeBCI data directory.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from freebci.core import ControlClient, ControlError  # noqa: E402

DEFAULT_TIMEOUT = 15.0


def _candidate_discovery_paths() -> Iterable[Path]:
    """Yield likely control.json locations without raising on a missing one."""
    explicit = os.environ.get("FREEBCI_CONTROL_FILE")
    if explicit:
        yield Path(explicit).expanduser()

    home = os.environ.get("FREEBCI_HOME")
    if home:
        yield Path(home).expanduser() / "control.json"

    yield Path.home() / "Documents" / "FreeBCI" / "control.json"
    yield REPO_ROOT / "logs" / "control.json"
    yield Path.cwd() / "logs" / "control.json"


def resolve_discovery(explicit: Optional[str] = None) -> Path:
    """Return the discovery file to use, with a useful error when missing."""
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


def wait_for_stop(client: ControlClient, timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Poll until the asynchronous GUI stop finishes.

    ``ControlClient.stop()`` only asks the GUI to stop.  A later ``status()``
    reports ``finalized`` (or ``failed``) once the writer and manifest are
    closed, which is the point at which the recording folder is complete.
    """
    deadline = time.monotonic() + max(0.0, float(timeout))
    last: Dict[str, Any] = {}
    while True:
        last = client.status()
        if last.get("state") in ("idle", "finalized", "failed"):
            return last
        if time.monotonic() >= deadline:
            raise ControlError(
                "timed out waiting for the session to stop (last state: %s)"
                % last.get("state", "unknown")
            )
        time.sleep(0.1)


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--discovery",
        help="path to control.json (default: FreeBCI data directory)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="seconds to wait for start/stop (default: %(default)s)",
    )
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("status", help="print the current session snapshot")
    commands.add_parser("ping", help="check that the control endpoint is alive")

    clock = commands.add_parser("clock", help="estimate the host clock offset")
    clock.add_argument("--samples", type=int, default=5)

    marker = commands.add_parser("marker", help="append a labeled marker")
    marker.add_argument("label", help="marker label, for example 'stimulus onset'")

    start = commands.add_parser("start", help="start the connected board or demo")
    start.add_argument(
        "board",
        help="board id, catalog name, or 'demo'; a real board must be connected",
    )
    start.add_argument(
        "--no-wait",
        action="store_true",
        help="return after the start request instead of polling for recording",
    )

    demo = commands.add_parser(
        "demo",
        help="start a demo session, optionally wait and add one marker",
    )
    demo.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="seconds to leave the demo running (default: %(default)s)",
    )
    demo.add_argument("--marker", help="marker label to add after the session starts")

    commands.add_parser("stop", help="stop the current session and wait for finalize")
    commands.add_parser("shutdown", help="stop and close the GUI")
    return parser


def run(args: argparse.Namespace) -> int:
    discovery = resolve_discovery(args.discovery)
    print("discovery: %s" % discovery, file=sys.stderr)
    client = ControlClient.from_discovery(str(discovery))

    if args.command == "ping":
        print("pong" if client.ping() else "no response")
    elif args.command == "status":
        _print_json(client.status())
    elif args.command == "clock":
        _print_json(client.clock_offset(samples=args.samples))
    elif args.command == "marker":
        _print_json(client.marker(args.label))
    elif args.command == "start":
        print(client.start(args.board))
        if not args.no_wait:
            _print_json(client.wait_started(timeout=args.timeout))
    elif args.command == "demo":
        print(client.start("demo"))
        _print_json(client.wait_started(timeout=args.timeout))
        if args.marker:
            _print_json(client.marker(args.marker))
        if args.duration > 0:
            time.sleep(args.duration)
        print(client.stop())
        _print_json(wait_for_stop(client, timeout=args.timeout))
    elif args.command == "stop":
        print(client.stop())
        _print_json(wait_for_stop(client, timeout=args.timeout))
    elif args.command == "shutdown":
        print(client.shutdown())
    else:
        raise SystemExit("choose a command; use --help for the list")
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2
    try:
        return run(args)
    except ControlError as exc:
        print("control error [%s]: %s" % (exc.code, exc), file=sys.stderr)
        return 2
    except (FileNotFoundError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
