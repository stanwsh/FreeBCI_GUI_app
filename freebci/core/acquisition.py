"""Background acquisition worker.

The worker is the only code that polls BrainFlow during a session.  It hands
ordered blocks to the session controller, which fans them out to the bounded
recording queue and to a separate, lossy display queue.
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from freebci.core.clock import SessionClock
from freebci.core.gateway import BoardGateway
from freebci.core.models import SampleBlock


class AcquisitionService:
    def __init__(
        self,
        gateway: BoardGateway,
        clock: SessionClock,
        sampling_rate: int,
        on_block: Callable[[SampleBlock], None],
        poll_interval: float = 0.01,
    ) -> None:
        self.gateway = gateway
        self.clock = clock
        self.sampling_rate = int(sampling_rate)
        self.on_block = on_block
        self.poll_interval = poll_interval
        self.error: Optional[str] = None
        self.blocks = 0
        self.samples = 0
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("acquisition worker is already started")
        self._stop.clear()
        self.error = None
        self._thread = threading.Thread(
            target=self._run,
            name="freebci-acquisition",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                count = self.gateway.get_data_count()
                if count <= 0:
                    self._stop.wait(self.poll_interval)
                    continue
                data = self.gateway.read()
                if data is None or getattr(data, "ndim", 0) != 2 or data.shape[1] == 0:
                    self._stop.wait(self.poll_interval)
                    continue
                block = self.clock.new_block(data, self.sampling_rate)
                self.blocks += 1
                self.samples += block.sample_count
                self.on_block(block)
            except Exception as exc:  # noqa: BLE001 - report and stop, never hide
                self.error = "acquisition failed: %s" % exc
                self._stop.set()
                return
