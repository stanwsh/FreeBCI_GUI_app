"""Session orchestration for the Qt-free core.

Lifecycle: IDLE -> CONNECTED -> ARMED -> RECORDING -> STOPPING -> FINALIZED.
The controller is intentionally single-device in this phase.  It is the only
object the GUI needs to start and stop a session.
"""
from __future__ import annotations

import dataclasses
import queue
import threading
import time
from typing import Callable, Optional

from freebci.core.acquisition import AcquisitionService
from freebci.core.clock import SessionClock
from freebci.core.gateway import BoardGateway
from freebci.core.models import (
    SampleBlock,
    SessionConfig,
    SessionState,
    SessionStats,
    SessionStatus,
    StateSnapshot,
)
from freebci.core.recording import RecordingError, RecordingWriter


class SessionController:
    def __init__(
        self,
        config: SessionConfig,
        gateway: BoardGateway,
        display_queue_blocks: int = 128,
        marker_callback: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.base_config = config
        self.config = config
        self.gateway = gateway
        self.marker_callback = marker_callback
        self.state = SessionState.CONNECTED
        self.stats = SessionStats()
        self.error: Optional[str] = None
        self.display_queue: "queue.Queue[SampleBlock]" = queue.Queue(maxsize=display_queue_blocks)
        self.clock = SessionClock()
        self.writer: Optional[RecordingWriter] = None
        self.acquisition: Optional[AcquisitionService] = None
        self._lock = threading.RLock()
        self._output_path = ""

    @property
    def output_path(self) -> str:
        return self._output_path

    def start(self) -> None:
        with self._lock:
            if self.state not in (SessionState.IDLE, SessionState.CONNECTED, SessionState.FINALIZED):
                raise RuntimeError("cannot start session from state %s" % self.state.value)
            self.stats.reset()
            self.error = None
            started_ns = self.clock.start()
            self.config = dataclasses.replace(self.base_config, started_wall_ns=started_ns)
            self.writer = RecordingWriter(self.config)
            self._output_path = self.writer.start()
            self.acquisition = AcquisitionService(
                gateway=self.gateway,
                clock=self.clock,
                sampling_rate=self.config.sampling_rate,
                on_block=self._on_block,
            )
            self.state = SessionState.ARMED
            self.stats.started_monotonic_ns = self.clock.started_monotonic_ns
            try:
                self.gateway.start_stream()
                self.acquisition.start()
                self.state = SessionState.RECORDING
            except Exception as exc:  # noqa: BLE001
                self.error = str(exc)
                self.stats.error = self.error
                self.state = SessionState.FAILED
                if self.writer is not None:
                    self.writer.close(SessionStatus.FAILED)
                raise

    def stop(self, status: Optional[SessionStatus] = None, timeout: float = 10.0) -> SessionStatus:
        with self._lock:
            if self.state in (SessionState.FINALIZED, SessionState.FAILED) and self.writer is None:
                return SessionStatus.FAILED
            previous = self.state
            self.state = SessionState.STOPPING
            self.stats.stopped_monotonic_ns = time.perf_counter_ns()
            acquisition = self.acquisition
            writer = self.writer

        if acquisition is not None:
            acquisition.stop(timeout=5.0)
        stop_error = None
        try:
            self.gateway.stop_stream()
        except Exception as exc:  # noqa: BLE001
            stop_error = "stop_stream failed: %s" % exc

        if status is None:
            if self.error or (writer is not None and writer.error):
                status = SessionStatus.FAILED
            elif acquisition is not None and acquisition.error:
                status = SessionStatus.PARTIAL
            else:
                status = SessionStatus.COMPLETED

        if writer is not None:
            self._output_path = writer.close(status)
        if stop_error:
            self.error = self.error or stop_error
        if self.error:
            self.state = SessionState.FAILED
        else:
            self.state = SessionState.FINALIZED
        return status

    def request_stop(self) -> None:
        """Signal the acquisition worker without joining it (worker-safe)."""
        if self.acquisition is not None:
            self.acquisition._stop.set()

    def add_marker(self, label: str, source: str = "api") -> dict:
        """Record an event at the current session sample offset."""
        with self._lock:
            if self.state not in (SessionState.ARMED, SessionState.RECORDING):
                raise RuntimeError(
                    "cannot add a marker while the session is %s" % self.state.value
                )
            writer = self.writer
            if writer is None:
                raise RuntimeError("session has no recording writer")
            sample_index = self.stats.samples
            elapsed = self.clock.elapsed_seconds()
        marker = writer.add_marker(
            label,
            source=source,
            sample_index=sample_index,
            elapsed_seconds=elapsed,
        )
        if self.marker_callback is not None:
            try:
                self.marker_callback(marker)
            except Exception:
                # A display/LSL sink must never invalidate the saved marker.
                pass
        return marker

    def _on_block(self, block: SampleBlock) -> None:
        self.stats.blocks += 1
        self.stats.samples += block.sample_count
        self.stats.last_block_monotonic_ns = time.perf_counter_ns()
        self.stats.last_block_wall_ns = block.host_time_ns
        self.stats.last_sample_time_ns = block.first_sample_time_ns
        writer = self.writer
        if writer is None:
            raise RecordingError("session has no recording writer")
        try:
            writer.submit(block)
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            self.stats.error = self.error
            self.state = SessionState.FAILED
            raise
        try:
            self.display_queue.put_nowait(block)
        except queue.Full:
            self.stats.display_dropped_samples += block.sample_count

    def drain_display(self, max_blocks: int = 64):
        blocks = []
        for _ in range(max_blocks):
            try:
                blocks.append(self.display_queue.get_nowait())
            except queue.Empty:
                break
        return blocks

    def check_health(self) -> Optional[str]:
        writer_error = self.writer.error if self.writer is not None else None
        acquisition_error = self.acquisition.error if self.acquisition is not None else None
        if writer_error or acquisition_error:
            message = writer_error or acquisition_error
            if self.state in (SessionState.RECORDING, SessionState.ARMED):
                status = SessionStatus.FAILED if writer_error else SessionStatus.PARTIAL
                self.stop(status)
            return message
        return None

    def snapshot(self) -> StateSnapshot:
        now_ns = time.perf_counter_ns()
        reference_ns = self.stats.last_block_monotonic_ns or self.stats.started_monotonic_ns
        since_block = (now_ns - reference_ns) / 1_000_000_000 if reference_ns else 0.0
        writer = self.writer
        writer_snapshot = writer.snapshot() if writer is not None else {}
        return StateSnapshot(
            state=self.state,
            session_id=self.config.session_id,
            sample_count=self.stats.samples,
            blocks=self.stats.blocks,
            elapsed_seconds=self.stats.duration_seconds,
            display_dropped_samples=self.stats.display_dropped_samples,
            lost_samples=writer.lost_samples if writer is not None else 0,
            seconds_since_block=max(0.0, since_block),
            markers=int(writer_snapshot.get("markers", 0)),
            error=self.error or (writer.error if writer is not None else None),
            output_path=self._output_path,
            last_block_wall_ns=self.stats.last_block_wall_ns,
            last_sample_time_ns=self.stats.last_sample_time_ns,
        )
