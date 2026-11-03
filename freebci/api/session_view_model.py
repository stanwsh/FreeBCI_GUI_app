"""Presentation adapter between the session core and the GUI.

The view model owns no acquisition state.  It resolves the currently active
``SessionController`` on demand, owns the bounded display history, and turns
both into the read-only values the widgets display.  Keeping these lookups here
stops individual widgets from reaching into the controller (and its writer)
directly.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional

import numpy as np

from freebci.core.diagnostics import diagnostics_fields, idle_fields
from freebci.core.models import StateSnapshot
from freebci.core.ring import RingBuffer
from freebci.core.session import SessionController


@dataclass(frozen=True)
class DisplaySnapshot:
    """Immutable view of the data a plot may render."""

    history: np.ndarray
    channel_count: int
    sampling_rate: int
    state: str
    sample_count: int
    total_samples: int


class SessionViewModel:
    def __init__(
        self,
        controller_provider: Callable[[], Optional[SessionController]],
        output_root_provider: Callable[[], str],
        control_provider: Callable[[], str],
        lsl_provider: Callable[[], str],
    ):
        self._controller_provider = controller_provider
        self._output_root_provider = output_root_provider
        self._control_provider = control_provider
        self._lsl_provider = lsl_provider
        self._ring: Optional[RingBuffer] = None

    @property
    def history(self) -> Optional[np.ndarray]:
        if self._ring is None or self._ring.count == 0:
            return None
        return self._ring.latest()

    def set_history(self, history: Optional[np.ndarray]) -> None:
        if history is None:
            self._ring = None
            return
        rows = int(history.shape[0])
        self._ring = RingBuffer(rows=rows, capacity=60000)
        if history.shape[1] > 1:
            self._ring.write(history)

    def append_block(self, block: np.ndarray, limit: int = 60000) -> np.ndarray:
        """Append one display block to the bounded ring history."""
        if self._ring is None:
            self._ring = RingBuffer(rows=int(block.shape[0]), capacity=int(limit))
        elif limit != self._ring.capacity:
            existing = self._ring.latest()
            self._ring = RingBuffer(rows=int(block.shape[0]), capacity=int(limit))
            if existing.shape[1]:
                self._ring.write(existing)
        if self._ring.count == 0:
            self._ring.write(block[:, 1:])
        else:
            self._ring.write(block)
        return self._ring.latest()

    def display_snapshot(self) -> Optional[DisplaySnapshot]:
        if self._ring is None or self._ring.count == 0:
            return None
        controller = self.controller
        if controller is None:
            return None
        state_snapshot = controller.snapshot()
        history = self._ring.latest()
        return DisplaySnapshot(
            history=history,
            channel_count=controller.config.channel_count,
            sampling_rate=controller.config.sampling_rate,
            state=state_snapshot.state.value,
            sample_count=state_snapshot.sample_count,
            total_samples=self._ring.total_written,
        )

    @property
    def controller(self) -> Optional[SessionController]:
        return self._controller_provider()

    @property
    def active(self) -> bool:
        return self.controller is not None

    def snapshot(self) -> Optional[StateSnapshot]:
        controller = self.controller
        if controller is None:
            return None
        return controller.snapshot()

    def diagnostics(self) -> Dict[str, str]:
        controller = self.controller
        output_root = self._output_root_provider()
        lsl_summary = self._lsl_provider()
        if controller is None:
            return idle_fields(output_root, lsl_summary)
        return diagnostics_fields(
            controller,
            output_root,
            self._control_provider(),
            lsl_summary,
        )

    def add_marker(self, label: str, source: str = "gui") -> dict:
        controller = self.controller
        if controller is None:
            raise RuntimeError("no active session")
        return controller.add_marker(label, source=source)
