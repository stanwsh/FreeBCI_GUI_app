"""Presentation adapter between the session core and the GUI.

The view model owns no acquisition state.  It resolves the currently active
``SessionController`` on demand, owns the bounded display history, and turns
both into the read-only values the widgets display.  Keeping these lookups here
stops individual widgets from reaching into the controller (and its writer)
directly.
"""

from typing import Callable, Dict, Optional

import numpy as np

from freebci.core.diagnostics import diagnostics_fields, idle_fields
from freebci.core.history import append_bounded
from freebci.core.models import StateSnapshot
from freebci.core.session import SessionController


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
        self._history: Optional[np.ndarray] = None

    @property
    def history(self) -> Optional[np.ndarray]:
        return self._history

    def set_history(self, history: Optional[np.ndarray]) -> None:
        self._history = history

    def append_block(self, block: np.ndarray, limit: int = 60000) -> np.ndarray:
        """Append one display block to the bounded history."""
        if self._history is None or self._history.shape[1] <= 1:
            self._history = block[:, 1:]
        else:
            self._history = append_bounded(self._history, block, limit)
        return self._history

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
