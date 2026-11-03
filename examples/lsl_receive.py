"""Receive FreeBCI EEG and marker streams over LSL.

Start LSL in the GUI's Networking view, then run this from another process::

    python examples/lsl_receive.py --discover
    python examples/lsl_receive.py --name FreeBCI_EEG1
    python examples/lsl_receive.py --name FreeBCI_EEG1 --duration 10 --json

The EEG chunks are printed as ``(first LSL timestamp, count, first sample)``.
The marker inlet is drained on every loop and prints labels such as ``manual``
or a label sent by the control API.  LSL timestamps are host-clock timestamps,
not device sample timestamps; use them for ordering and correlation, not as a
claim of physical sample synchronization.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import pylsl
except ImportError as exc:  # pragma: no cover - exercised only without pylsl
    raise SystemExit(
        "pylsl is required for this example; install requirements.txt first"
    ) from exc


def describe_stream(info: Any) -> Dict[str, Any]:
    """Return stable, JSON-friendly metadata for a StreamInfo."""
    return {
        "name": info.name(),
        "type": info.type(),
        "channels": int(info.channel_count()),
        "nominal_srate": float(info.nominal_srate()),
        "source_id": info.source_id(),
        "hostname": info.hostname(),
        "uid": info.uid(),
        "created_at": float(info.created_at()),
    }


def find_stream(
    name: Optional[str] = None,
    stream_type: Optional[str] = None,
    source_id: Optional[str] = None,
    timeout: float = 5.0,
) -> Any:
    """Resolve the first matching LSL stream or raise a readable error."""
    if name:
        streams = pylsl.resolve_byprop("name", name, timeout=timeout)
        description = "name=%r" % name
    elif source_id:
        streams = pylsl.resolve_byprop("source_id", source_id, timeout=timeout)
        description = "source_id=%r" % source_id
    elif stream_type:
        streams = pylsl.resolve_byprop("type", stream_type, timeout=timeout)
        description = "type=%r" % stream_type
    else:
        streams = pylsl.resolve_streams(wait_time=timeout)
        description = "any stream"
    if not streams:
        raise RuntimeError(
            "no LSL stream found for %s; start LSL in the FreeBCI Networking "
            "view and check the stream name" % description
        )
    return streams[0]


def drain_markers(inlet: Any) -> List[Tuple[str, float]]:
    """Read all currently queued marker samples without blocking."""
    samples, timestamps = inlet.pull_chunk(timeout=0.0, max_samples=64)
    markers: List[Tuple[str, float]] = []
    for sample, timestamp in zip(samples, timestamps):
        label = sample[0] if sample else ""
        markers.append((str(label), float(timestamp)))
    return markers


def _short_sample(sample: Sequence[float], limit: int = 8) -> str:
    values = list(sample[:limit])
    text = " ".join("%.4g" % float(value) for value in values)
    if len(sample) > limit:
        text += " ..."
    return text


def _print_stream(info: Dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps({"kind": "stream", **info}, separators=(",", ":")))
    else:
        print(
            "stream: %s | type=%s | channels=%d | nominal_srate=%.3f Hz | "
            "source_id=%s"
            % (
                info["name"],
                info["type"],
                info["channels"],
                info["nominal_srate"],
                info["source_id"] or "-",
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--discover", action="store_true", help="list LSL streams and exit")
    parser.add_argument("--name", help="stream name, for example FreeBCI_EEG1")
    parser.add_argument("--type", default="EEG", help="LSL type when --name is omitted")
    parser.add_argument("--source-id", help="stable LSL source id")
    parser.add_argument("--marker-name", default="FreeBCI_Markers")
    parser.add_argument(
        "--no-markers",
        action="store_true",
        help="do not open the FreeBCI marker stream",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="seconds to run; 0 means until Ctrl+C (default: %(default)s)",
    )
    parser.add_argument("--max-chunks", type=int, default=0, help="stop after N chunks")
    parser.add_argument("--max-samples", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit one JSON object per line instead of a text report",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    if args.discover:
        streams = [describe_stream(info) for info in pylsl.resolve_streams(wait_time=args.timeout)]
        if args.json:
            print(json.dumps(streams, indent=2, sort_keys=True))
        elif not streams:
            print("no LSL streams found")
        else:
            for info in streams:
                _print_stream(info, False)
        return 0

    stream_info = find_stream(
        name=args.name,
        stream_type=None if args.name else args.type,
        source_id=args.source_id,
        timeout=args.timeout,
    )
    info = describe_stream(stream_info)
    _print_stream(info, args.json)

    inlet = pylsl.StreamInlet(stream_info, max_buflen=60, recover=True)
    marker_inlet = None
    if not args.no_markers:
        try:
            marker_inlet = pylsl.StreamInlet(
                find_stream(name=args.marker_name, timeout=1.0),
                max_buflen=60,
                recover=True,
            )
        except RuntimeError as exc:
            print("marker stream unavailable: %s" % exc, file=sys.stderr)

    started = time.monotonic()
    deadline = started + args.duration if args.duration > 0 else None
    chunks = 0
    samples_total = 0
    next_report = started + 1.0

    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                break

            samples, timestamps = inlet.pull_chunk(
                timeout=0.25, max_samples=max(1, args.max_samples)
            )
            if samples:
                chunks += 1
                samples_total += len(samples)
                first_time = float(timestamps[0]) if timestamps else 0.0
                age = pylsl.local_clock() - first_time if first_time else 0.0
                if args.json:
                    print(
                        json.dumps(
                            {
                                "kind": "samples",
                                "lsl_time": first_time,
                                "age_seconds": age,
                                "count": len(samples),
                                "first_sample": list(samples[0]),
                            },
                            separators=(",", ":"),
                        )
                    )
                else:
                    print(
                        "chunk %d: lsl_time=%.6f age=%.3fs count=%d first=[%s]"
                        % (
                            chunks,
                            first_time,
                            age,
                            len(samples),
                            _short_sample(samples[0]),
                        )
                    )

            if marker_inlet is not None:
                for label, timestamp in drain_markers(marker_inlet):
                    age = pylsl.local_clock() - timestamp
                    if args.json:
                        print(
                            json.dumps(
                                {
                                    "kind": "marker",
                                    "label": label,
                                    "lsl_time": timestamp,
                                    "age_seconds": age,
                                },
                                separators=(",", ":"),
                            )
                        )
                    else:
                        print(
                            "MARKER %-24s lsl_time=%.6f age=%.3fs"
                            % (label, timestamp, age)
                        )

            now = time.monotonic()
            if not args.json and now >= next_report:
                elapsed = max(1e-9, now - started)
                print(
                    "summary: %.1fs, %d samples, %.1f samples/s"
                    % (elapsed, samples_total, samples_total / elapsed)
                )
                next_report = now + 1.0

            if args.max_chunks and chunks >= args.max_chunks:
                break
    except KeyboardInterrupt:
        pass
    finally:
        try:
            inlet.close()
        except Exception:
            pass
        if marker_inlet is not None:
            try:
                marker_inlet.close()
            except Exception:
                pass

    elapsed = max(1e-9, time.monotonic() - started)
    summary = {
        "kind": "summary",
        "chunks": chunks,
        "samples": samples_total,
        "seconds": elapsed,
        "samples_per_second": samples_total / elapsed,
    }
    if args.json:
        print(json.dumps(summary, separators=(",", ":")))
    else:
        print(
            "done: %d samples in %d chunks over %.2fs (%.1f samples/s)"
            % (
                samples_total,
                chunks,
                elapsed,
                samples_total / elapsed,
            )
        )
    return 0


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except (RuntimeError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
