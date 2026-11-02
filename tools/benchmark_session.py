"""Run a short hardware-free session and print throughput and integrity metrics.

This is a developer/CI tool: it exercises the same acquisition, recording, and
manifest path as the GUI, but uses the synthetic board instead of hardware.

Usage:
    python tools/benchmark_session.py --seconds 10 --channels 16 --rate 250
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from freebci.core.gateway import BrainFlowGateway
from freebci.core.models import BoardProfile, SessionConfig
from freebci.core.session import SessionController
from freebci.core.simulator import SimulatedBoard


def run(args) -> dict:
    board = SimulatedBoard(channels=args.channels, sampling_rate=args.rate)
    profile = BoardProfile(
        board_id=2037,
        name="Simulated FreeBCI",
        channels=args.channels,
        sampling_rate=args.rate,
    )
    config = SessionConfig(
        session_id="benchmark_%d" % time.time_ns(),
        board=profile,
        sampling_rate=args.rate,
        output_root=os.path.abspath(args.output),
        channel_count=args.channels,
    )
    controller = SessionController(config, BrainFlowGateway(board, board_id=2037, channel_count=args.channels))
    started = time.perf_counter()
    controller.start()
    try:
        deadline = started + max(0.5, args.seconds)
        while time.perf_counter() < deadline:
            time.sleep(0.05)
    finally:
        status = controller.stop()
    elapsed = time.perf_counter() - started
    snapshot = controller.snapshot()
    writer = controller.writer.snapshot() if controller.writer is not None else {}
    return {
        "status": status.value,
        "elapsed_seconds": round(elapsed, 3),
        "requested_seconds": args.seconds,
        "channels": args.channels,
        "sampling_rate": args.rate,
        "samples": snapshot.sample_count,
        "effective_rate_hz": round(snapshot.sample_count / elapsed, 2) if elapsed else 0.0,
        "blocks": snapshot.blocks,
        "lost_samples": snapshot.lost_samples,
        "display_dropped_samples": snapshot.display_dropped_samples,
        "markers": snapshot.markers,
        "files": writer.get("files", 0),
        "queue_depth": writer.get("queue_depth", 0),
        "queue_capacity": writer.get("queue_capacity", 0),
        "output_path": snapshot.output_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10.0, help="session duration")
    parser.add_argument("--channels", type=int, default=16, help="synthetic channel count")
    parser.add_argument("--rate", type=int, default=250, help="samples per second")
    parser.add_argument("--output", default=os.path.join(REPO_ROOT, "logs", "benchmark"))
    parser.add_argument("--json", action="store_true", help="print only the JSON result")
    args = parser.parse_args()
    result = run(args)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("FreeBCI session benchmark")
        for key in (
            "status",
            "elapsed_seconds",
            "channels",
            "sampling_rate",
            "samples",
            "effective_rate_hz",
            "blocks",
            "lost_samples",
            "display_dropped_samples",
            "files",
            "queue_depth",
            "queue_capacity",
            "output_path",
        ):
            print("  %-24s %s" % (key + ":", result[key]))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
