"""Durable, bounded recording writer.

The writer owns the legacy CSV/TXT layout plus a machine-readable manifest and
per-file sidecars.  It runs on its own thread so disk latency cannot stall the
acquisition worker or the GUI.

Legacy layout (kept for compatibility):

    <root>/Recordings/Stream_YYYY_mm_dd_HHMMSS/
        1.csv, 1.txt, 1.meta.json
        2.csv, 2.txt, 2.meta.json
        manifest.json

Each CSV/TXT file holds up to nine 10,000-sample chunks (90,000 samples).
A queue overflow is a hard error: the session is failed rather than silently
dropping physiological samples.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import queue
import threading
import time
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import numpy as np

from freebci.core.logging import StructuredLogger
from freebci.core.models import SampleBlock, SessionConfig, SessionStatus
from freebci.version import VERSION

CHUNK_SAMPLES = 10_000
CHUNKS_PER_FILE = 9
AUX_CHANNELS = 3
CHECKPOINT_SECONDS = 5.0


class RecordingError(RuntimeError):
    """Raised when recording cannot continue without losing data."""


class RecordingWriter:
    def __init__(self, config: SessionConfig, queue_blocks: int = 512) -> None:
        self.config = config
        self.record_root = os.path.join(config.output_root, "Recordings")
        self.session_dir: Optional[str] = None
        self._queue: "queue.Queue[Optional[SampleBlock]]" = queue.Queue(maxsize=queue_blocks)
        self._thread: Optional[threading.Thread] = None
        self._closed = False
        self._started_ns = 0
        self._stopped_ns = 0
        self._stop_reason = "user"
        self.error: Optional[str] = None
        self.blocks_received = 0
        self.samples_received = 0
        self.samples_written = 0
        self.files: List[dict] = []
        self.gaps: List[dict] = []
        self.markers: List[dict] = []
        self.markers_path: Optional[str] = None
        self.writing_path: Optional[str] = None
        self.logger: Optional[StructuredLogger] = None
        self.log_path: Optional[str] = None
        self.lost_samples = 0
        self._errors: List[str] = []
        self._next_sample_index: Optional[int] = None
        self._marker_lock = threading.Lock()

        self._file_number = 1
        self._handle_txt = None
        self._handle_csv = None
        self._csv_writer = None
        self._chunks_in_file = 0
        self._file_samples = 0
        self._file_start_sample = 0
        self._pending: List[np.ndarray] = []
        self._pending_samples = 0
        self._last_checkpoint = 0.0

    # ------------------------------------------------------------------ API
    def start(self) -> str:
        if self._thread is not None:
            return self.session_dir or ""
        os.makedirs(self.record_root, exist_ok=True)
        self.session_dir = self._make_session_dir()
        self.markers_path = os.path.join(self.session_dir, "markers.jsonl")
        self.writing_path = os.path.join(self.session_dir, ".writing")
        _atomic_json(
            self.writing_path,
            {
                "pid": os.getpid(),
                "session_id": self.config.session_id,
                "started_wall_ns": self.config.started_wall_ns or _wall_ns(),
            },
        )
        with open(self.markers_path, "w", encoding="utf-8", newline="\n"):
            pass
        self.log_path = os.path.join(self.session_dir, "session.log")
        self.logger = StructuredLogger(self.log_path)
        self._log(
            "info",
            "recording.started",
            "recording writer started",
            session_id=self.config.session_id,
            board_id=self.config.board_id,
            channel_count=self.config.channel_count,
            sampling_rate=self.config.sampling_rate,
        )
        self._started_ns = self.config.started_wall_ns or _wall_ns()
        self._last_checkpoint = time.monotonic()
        self._write_manifest(SessionStatus.RECORDING)
        self._thread = threading.Thread(
            target=self._run,
            name="freebci-recording",
            daemon=True,
        )
        self._thread.start()
        return self.session_dir

    def submit(self, block: SampleBlock) -> None:
        """Queue a block without blocking the acquisition worker."""
        if self.error:
            raise RecordingError(self.error)
        if self._closed:
            raise RecordingError("recording writer is already closed")
        self.blocks_received += 1
        self.samples_received += block.sample_count
        if self._next_sample_index is not None and block.sample_index > self._next_sample_index:
            missing = block.sample_index - self._next_sample_index
            self.gaps.append(
                {
                    "start_sample": self._next_sample_index,
                    "end_sample": block.sample_index,
                    "missing_samples": missing,
                }
            )
            self.lost_samples += missing
            self._log(
                "warning",
                "recording.gap",
                "sample-index gap",
                start_sample=self._next_sample_index,
                end_sample=block.sample_index,
                missing_samples=missing,
            )
        self._next_sample_index = block.sample_index + block.sample_count
        try:
            self._queue.put_nowait(block)
        except queue.Full as exc:
            self.error = (
                "recording queue is full; acquisition stopped to avoid "
                "silently losing samples"
            )
            self._errors.append(self.error)
            self._log("error", "recording.queue_full", self.error)
            raise RecordingError(self.error) from exc

    def add_marker(
        self,
        label: str,
        source: str = "api",
        sample_index: int = 0,
        elapsed_seconds: float = 0.0,
    ) -> dict:
        """Append a marker without blocking acquisition.

        Markers are written immediately to ``markers.jsonl`` so they survive a
        crash, then included in the next manifest checkpoint.  The sample index
        is the number of samples received when the marker was requested; it is
        a session-relative offset, not a hardware timestamp.
        """
        if not self.session_dir or not self.markers_path:
            raise RecordingError("recording has not started")
        text = " ".join(str(label or "").split())[:500] or "marker"
        marker = {
            "label": text,
            "source": str(source or "api")[:40],
            "sample_index": max(0, int(sample_index)),
            "elapsed_seconds": round(max(0.0, float(elapsed_seconds)), 6),
            "wall_time": _iso(time.time_ns()),
        }
        line = json.dumps(marker, sort_keys=True) + "\n"
        try:
            with open(self.markers_path, "a", encoding="utf-8", newline="\n") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise RecordingError("could not write marker: %s" % exc) from exc
        with self._marker_lock:
            self.markers.append(marker)
        self._log(
            "info",
            "recording.marker",
            "marker added",
            label=marker["label"],
            source=marker["source"],
            sample_index=marker["sample_index"],
        )
        return marker

    def close(self, status: SessionStatus = SessionStatus.COMPLETED, reason: str = "user") -> str:
        """Flush remaining data, stop the writer, and write the manifest."""
        if self._closed:
            return self.session_dir or ""
        self._closed = True
        self._stop_reason = str(reason)
        if self._thread is not None and self._thread.is_alive():
            self._queue.put(None)
            self._thread.join(timeout=30.0)
        self._stopped_ns = _wall_ns()
        try:
            self._flush_pending()
        except Exception as exc:  # noqa: BLE001 - preserve the manifest on a full disk
            self.error = "recording failed while flushing: %s" % exc
            self._errors.append(self.error)
            self._log("error", "recording.flush_failed", self.error)
        self._close_file()
        if self.error:
            status = SessionStatus.FAILED
        self._log(
            "info" if status != SessionStatus.FAILED else "error",
            "recording.closed",
            "recording writer closed",
            status=status.value,
            samples_written=self.samples_written,
            blocks_received=self.blocks_received,
            lost_samples=self.lost_samples,
        )
        self._write_manifest(status)
        if self.writing_path:
            try:
                os.unlink(self.writing_path)
            except OSError:
                pass
        if self.logger is not None:
            self.logger.close()
        return self.session_dir or ""

    def wait(self, timeout: float = 30.0) -> None:
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def snapshot(self) -> dict:
        with self._marker_lock:
            marker_count = len(self.markers)
        return {
            "session_dir": self.session_dir,
            "blocks": self.blocks_received,
            "samples": self.samples_received,
            "written": self.samples_written,
            "files": len(self.files),
            "gaps": len(self.gaps),
            "markers": marker_count,
            "lost_samples": self.lost_samples,
            "queue_depth": self._queue.qsize(),
            "queue_capacity": self._queue.maxsize,
            "error": self.error,
        }

    # -------------------------------------------------------------- internal
    def _log(self, level: str, event: str, message: str = "", **fields) -> None:
        if self.logger is None:
            return
        try:
            self.logger.log(level, event, message, **fields)
        except Exception:  # noqa: BLE001 - logging must never stop acquisition
            pass

    def _run(self) -> None:
        while True:
            block = self._queue.get()
            if block is None:
                return
            try:
                self._write_block(block)
            except Exception as exc:  # noqa: BLE001 - keep the thread alive to report
                self.error = "recording failed: %s" % exc
                self._errors.append(self.error)
                self._log("error", "recording.write_failed", self.error)
                self._drain_queue()
                return

    def _drain_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    def _write_block(self, block: SampleBlock) -> None:
        values = self._extract_rows(block)
        self._pending.append(values)
        self._pending_samples += values.shape[1]
        while self._pending_samples >= CHUNK_SAMPLES:
            chunk = self._take_pending(CHUNK_SAMPLES)
            self._write_chunk(chunk)
        now = time.monotonic()
        if now - self._last_checkpoint >= CHECKPOINT_SECONDS:
            self._last_checkpoint = now
            self._write_manifest(SessionStatus.RECORDING)

    def _extract_rows(self, block: SampleBlock) -> np.ndarray:
        data = np.asarray(block.data)
        channel_count = self.config.channel_count
        needed = 1 + channel_count + AUX_CHANNELS
        if data.ndim != 2 or data.shape[0] < needed:
            raise RecordingError(
                "board block has %s rows; expected at least %s for %s channels"
                % (data.shape if data.ndim == 2 else "?", needed, channel_count)
            )
        rows = np.array(data[1 : 1 + channel_count], dtype=np.float64, copy=True)
        aux = np.array(
            data[1 + channel_count : 1 + channel_count + AUX_CHANNELS],
            dtype=np.float64,
            copy=True,
        )
        aux = np.rint(aux).astype(np.float64)
        return np.vstack([rows, aux])

    def _take_pending(self, count: int) -> np.ndarray:
        remaining = count
        parts: List[np.ndarray] = []
        while remaining > 0:
            head = self._pending[0]
            if head.shape[1] <= remaining:
                parts.append(head)
                self._pending.pop(0)
                remaining -= head.shape[1]
            else:
                parts.append(head[:, :remaining])
                self._pending[0] = head[:, remaining:]
                remaining = 0
        self._pending_samples -= count
        if len(parts) == 1:
            return parts[0]
        return np.concatenate(parts, axis=1)

    def _flush_pending(self) -> None:
        if self._pending_samples:
            chunk = self._take_pending(self._pending_samples)
            self._write_chunk(chunk)

    def _write_chunk(self, values: np.ndarray) -> None:
        if self._handle_csv is None:
            self._open_file()
        assert self._csv_writer is not None
        assert self._handle_txt is not None
        samples = values.shape[1]
        for column in values.T:
            self._csv_writer.writerow(
                ["%.6f" % float(v) for v in column[: self.config.channel_count]]
                + [str(int(v)) for v in column[self.config.channel_count :]]
            )
            self._handle_txt.write(
                ",".join(
                    ["%.6f" % float(v) for v in column[: self.config.channel_count]]
                    + [str(int(v)) for v in column[self.config.channel_count :]]
                )
                + "\n"
            )
        self._file_samples += samples
        self.samples_written += samples
        self._chunks_in_file += 1
        if self._chunks_in_file >= CHUNKS_PER_FILE:
            self._close_file()

    def _open_file(self) -> None:
        assert self.session_dir is not None
        number = self._file_number
        txt_path = os.path.join(self.session_dir, "%d.txt" % number)
        csv_path = os.path.join(self.session_dir, "%d.csv" % number)
        self._handle_txt = open(txt_path, "w", encoding="utf-8", newline="\n")
        self._handle_csv = open(csv_path, "w", encoding="utf-8", newline="")
        self._csv_writer = csv.writer(self._handle_csv)
        header = ["channel%d" % (i + 1) for i in range(self.config.channel_count)]
        header += ["<AUX %d>" % i for i in range(AUX_CHANNELS)]
        self._csv_writer.writerow(header)
        self._handle_txt.write("FreeBCI Raw Data\n")
        self._handle_txt.write("Number of Channels: %d\n" % self.config.channel_count)
        self._handle_txt.write("Sampling Rate: %d Hz\n" % self.config.sampling_rate)
        self._handle_txt.write("Board: %s\n" % self.config.board_name)
        self._handle_txt.write(
            "".join(["%d " % (i + 1) for i in range(self.config.channel_count)])
            + "".join("<AUX %d> " % i for i in range(AUX_CHANNELS))
            + "\n"
        )
        self._handle_txt.write(
            "Start Time: %s\n" % datetime.fromtimestamp(self._started_ns / 1e9).strftime("%Y_%m_%d_%H%M%S")
        )
        self._file_samples = 0
        self._chunks_in_file = 0
        self._file_start_sample = self.samples_written

    def _close_file(self) -> None:
        if self._handle_csv is None:
            return
        assert self.session_dir is not None
        number = self._file_number
        try:
            self._handle_csv.flush()
            os.fsync(self._handle_csv.fileno())
        except OSError:
            pass
        try:
            self._handle_txt.flush()
            os.fsync(self._handle_txt.fileno())
        except OSError:
            pass
        self._handle_csv.close()
        self._handle_txt.close()
        self._handle_csv = None
        self._handle_txt = None
        self._csv_writer = None

        csv_path = os.path.join(self.session_dir, "%d.csv" % number)
        meta = {
            "file": "%d.csv" % number,
            "samples": self._file_samples,
            "start_sample": self._file_start_sample,
            "end_sample": self._file_start_sample + self._file_samples,
            "sampling_rate": self.config.sampling_rate,
            "channels": self.config.channel_count,
            "sha256": _sha256_file(csv_path),
        }
        _atomic_json(os.path.join(self.session_dir, "%d.meta.json" % number), meta)
        self.files.append(meta)
        self._file_number += 1

    def _make_session_dir(self) -> str:
        stamp_ns = self.config.started_wall_ns or _wall_ns()
        stamp = datetime.fromtimestamp(stamp_ns / 1e9).strftime("%Y_%m_%d_%H%M%S")
        base = os.path.join(self.record_root, "Stream_" + stamp)
        candidate = base
        suffix = 1
        while os.path.exists(candidate):
            candidate = "%s_%d" % (base, suffix)
            suffix += 1
        os.makedirs(candidate)
        return candidate

    def _write_manifest(self, status: SessionStatus) -> None:
        if not self.session_dir:
            return
        if self.error:
            status = SessionStatus.FAILED
        with self._marker_lock:
            markers = list(self.markers)
        manifest = {
            "schema": "freebci.session/1",
            "schema_version": 1,
            "app_version": VERSION,
            "session_id": self.config.session_id,
            "status": status.value,
            "created_wall_ns": self._started_ns,
            "board": {"id": self.config.board_id, "name": self.config.board_name},
            "device": {
                "board_id": self.config.board_id,
                "name": self.config.board_name,
                "channels": self.config.channel_count,
                "family": "unknown",
            },
            "config": {
                "sampling_rate": self.config.sampling_rate,
                "channel_names": [
                    "channel%d" % (index + 1)
                    for index in range(self.config.channel_count)
                ],
            },
            "start": {
                "first_sample_index": 0,
                "host_wall_ns": self._started_ns,
                "host_monotonic_ns": 0,
            },
            "stop": {
                "last_sample_index": max(0, self.samples_written - 1),
                "host_wall_ns": self._stopped_ns or _wall_ns(),
                "host_monotonic_ns": 0,
                "reason": self._stop_reason,
            },
            "channel_count": self.config.channel_count,
            "sampling_rate": self.config.sampling_rate,
            "started_at": _iso(self._started_ns),
            "stopped_at": _iso(self._stopped_ns),
            "clock": {
                "timebase": "host-wall",
                "started_wall_ns": self._started_ns,
                "stopped_wall_ns": self._stopped_ns,
                "sample_index_origin": 0,
                "sampling_rate_hz": self.config.sampling_rate,
                "note": "host-clock estimates; not hardware timestamps",
            },
            "sample_count": self.samples_written,
            "samples_recorded": self.samples_written,
            "blocks_received": self.blocks_received,
            "lost_samples": self.lost_samples,
            "gaps": self.gaps,
            "markers": markers,
            "chunks": [
                {
                    "file": item.get("file"),
                    "first_sample_index": item.get("start_sample", 0),
                    "n_samples": item.get("samples", 0),
                    "sha256": item.get("sha256", ""),
                    "status": "complete",
                }
                for item in self.files
            ],
            "files": self.files,
            "session_log": "session.log",
            "errors": self._errors,
        }
        _atomic_json(os.path.join(self.session_dir, "manifest.json"), manifest)


def recover_sessions(output_root: str) -> List[dict]:
    """Return sessions that have a ``.writing`` marker and were not finalized.

    Recovery is read-only: files stay where they are, so a user or a later
    repair tool can decide whether to import, resume, or discard the data.
    """
    found: List[dict] = []
    root = os.path.join(output_root, "Recordings")
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return found
    for name in names:
        session_dir = os.path.join(root, name)
        marker = os.path.join(session_dir, ".writing")
        if not os.path.isfile(marker):
            continue
        manifest: dict = {}
        try:
            with open(os.path.join(session_dir, "manifest.json"), encoding="utf-8") as handle:
                manifest = json.load(handle)
        except (OSError, ValueError):
            pass
        found.append(
            {
                "session_dir": session_dir,
                "session_id": manifest.get("session_id", ""),
                "status": manifest.get("status", "unknown"),
                "samples_recorded": manifest.get("samples_recorded", 0),
                "manifest": manifest,
            }
        )
    return found


def _wall_ns() -> int:
    import time

    return time.time_ns()


def _iso(ns: int) -> str:
    if not ns:
        return ""
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).isoformat()


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _atomic_json(path: str, payload: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
