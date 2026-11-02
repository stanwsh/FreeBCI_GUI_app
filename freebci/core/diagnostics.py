"""Qt-free formatting for the session diagnostics surface.

The GUI owns the dialog; this module owns the presentation of a controller
snapshot.  Keeping it out of the window makes the diagnostics text testable
without PyQt and prevents the dialog from reaching into acquisition internals.
"""
from __future__ import annotations

from typing import Dict

from freebci.core.session import SessionController


def idle_fields(output_root: str, lsl_summary: str) -> Dict[str, str]:
    return {
        "state": "idle",
        "session": "-",
        "elapsed": "-",
        "rate": "-",
        "samples": "-",
        "blocks": "-",
        "lost": "-",
        "dropped": "-",
        "since": "-",
        "markers": "-",
        "files": "-",
        "queue": "-",
        "recording": "not recording",
        "output": output_root,
        "control": "not running",
        "lsl": lsl_summary,
        "error": "-",
    }


def diagnostics_fields(
    controller: SessionController,
    output_root: str,
    control_endpoint: str,
    lsl_summary: str,
) -> Dict[str, str]:
    snapshot = controller.snapshot()
    writer = controller.writer.snapshot() if controller.writer else {}
    elapsed = float(snapshot.elapsed_seconds or 0.0)
    rate = float(snapshot.sample_count) / elapsed if elapsed > 0 else 0.0
    since = float(snapshot.seconds_since_block or 0.0)
    state = snapshot.state.value
    stalled = state == "recording" and since >= 2.0

    return {
        "state": state,
        "session": snapshot.session_id or "-",
        "elapsed": "%.1f s" % elapsed,
        "rate": "%.1f Hz" % rate if rate else "-",
        "samples": "{:,}".format(snapshot.sample_count),
        "blocks": "{:,}".format(snapshot.blocks),
        "lost": "{:,}".format(snapshot.lost_samples),
        "dropped": "{:,}".format(snapshot.display_dropped_samples),
        "since": "%.1f s%s" % (since, " (stalled)" if stalled else ""),
        "markers": "{:,}".format(snapshot.markers),
        "files": "{:,}".format(writer.get("files", 0)),
        "queue": "%d / %d"
        % (writer.get("queue_depth", 0), writer.get("queue_capacity", 0)),
        "recording": "recording" if state == "recording" else state,
        "output": snapshot.output_path or output_root,
        "control": control_endpoint or "not running",
        "lsl": lsl_summary,
        "error": snapshot.error or "-",
    }
