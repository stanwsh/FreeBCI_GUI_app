"""Run a longer synthetic session and report throughput, loss, and memory.

This is the repeatable soak harness used before a hardware release.  It uses the
same acquisition/recording services as the GUI and the synthetic board, so it
can run unattended for minutes or hours.

Usage:
    python tools/soak_session.py --minutes 10 --channels 16 --rate 250
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import time
from ctypes import wintypes

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from freebci.core.gateway import BrainFlowGateway
from freebci.core.models import BoardProfile, SessionConfig
from freebci.core.session import SessionController
from freebci.core.simulator import SimulatedBoard


class _MemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def working_set_mb() -> float:
    if os.name != "nt":
        return 0.0
    counters = _MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.K32GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_MemoryCounters),
        wintypes.DWORD,
    ]
    kernel32.K32GetProcessMemoryInfo.restype = wintypes.BOOL
    process = kernel32.GetCurrentProcess()
    if not kernel32.K32GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
        return 0.0
    return counters.WorkingSetSize / (1024.0 * 1024.0)


def run(minutes: float, channels: int, rate: int, output: str) -> dict:
    board = SimulatedBoard(channels=channels, sampling_rate=rate)
    profile = BoardProfile(board_id=2037, name="Simulated FreeBCI", channels=channels, sampling_rate=rate)
    config = SessionConfig(
        session_id="soak_%d" % time.time_ns(),
        board=profile,
        sampling_rate=rate,
        output_root=os.path.abspath(output),
        channel_count=channels,
    )
    controller = SessionController(config, BrainFlowGateway(board, board_id=2037, channel_count=channels))
    started = time.perf_counter()
    controller.start()
    try:
        duration = max(1.0, minutes * 60.0)
        next_report = started + min(30.0, duration)
        while time.perf_counter() - started < duration:
            time.sleep(0.5)
            controller.drain_display(64)
            if time.perf_counter() >= next_report:
                snapshot = controller.snapshot()
                print(
                    "  t=%6.1fs samples=%d rate=%.1fHz lost=%d dropped=%d queue=%d mem=%.1fMB"
                    % (
                        time.perf_counter() - started,
                        snapshot.sample_count,
                        snapshot.sample_count / max(0.1, time.perf_counter() - started),
                        snapshot.lost_samples,
                        snapshot.display_dropped_samples,
                        controller.writer.snapshot().get("queue_depth", 0),
                        working_set_mb(),
                    )
                )
                next_report += min(30.0, duration)
    finally:
        status = controller.stop()
    elapsed = time.perf_counter() - started
    snapshot = controller.snapshot()
    writer = controller.writer.snapshot() if controller.writer is not None else {}
    return {
        "status": status.value,
        "elapsed_seconds": round(elapsed, 1),
        "samples": snapshot.sample_count,
        "effective_rate_hz": round(snapshot.sample_count / elapsed, 2) if elapsed else 0.0,
        "lost_samples": snapshot.lost_samples,
        "display_dropped_samples": snapshot.display_dropped_samples,
        "files": writer.get("files", 0),
        "markers": snapshot.markers,
        "output_path": snapshot.output_path,
        "working_set_mb": round(working_set_mb(), 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minutes", type=float, default=10.0)
    parser.add_argument("--channels", type=int, default=16)
    parser.add_argument("--rate", type=int, default=250)
    parser.add_argument("--output", default=os.path.join(REPO_ROOT, "logs", "soak"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run(args.minutes, args.channels, args.rate, args.output)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("Soak result")
        for key, value in result.items():
            print("  %-24s %s" % (key + ":", value))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
