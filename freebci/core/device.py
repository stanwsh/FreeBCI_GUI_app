"""Single-owner device lifecycle for prepared boards.

Transport-specific dialogs still perform the vendor handshake (COM port,
Wi-Fi address, Bluetooth pairing), but once a board is prepared the manager is
the only object that decides whether it is ready, streaming, or released.
"""

from __future__ import annotations

import threading
from enum import Enum
from typing import Any, Iterable, Optional

from freebci.core.gateway import BrainFlowGateway
from freebci.core.models import BoardProfile


class DeviceError(RuntimeError):
    """Raised when a device transition is not valid."""


class DeviceState(str, Enum):
    DISCONNECTED = "disconnected"
    READY = "ready"
    STREAMING = "streaming"


class DeviceManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._board: Optional[Any] = None
        self._profile: Optional[BoardProfile] = None
        self._state = DeviceState.DISCONNECTED

    @property
    def board(self) -> Optional[Any]:
        with self._lock:
            return self._board

    @property
    def profile(self) -> Optional[BoardProfile]:
        with self._lock:
            return self._profile

    @property
    def state(self) -> DeviceState:
        with self._lock:
            return self._state

    @property
    def connected(self) -> bool:
        return self.board is not None

    def adopt(self, board: Any, profile: BoardProfile) -> None:
        """Make ``board`` the active device, releasing any previous board."""
        if board is None:
            raise DeviceError("no prepared board was supplied")
        with self._lock:
            if self._board is board:
                self._profile = profile
                return
            previous = self._board
            if previous is not None:
                self._release_locked(previous)
            self._board = board
            self._profile = profile
            self._state = DeviceState.READY

    def mark_streaming(self) -> None:
        with self._lock:
            if self._board is None:
                raise DeviceError("no board is connected")
            self._state = DeviceState.STREAMING

    def mark_ready(self) -> None:
        with self._lock:
            if self._board is not None:
                self._state = DeviceState.READY

    def gateway(self, post_start_config: Iterable[str] = ()) -> BrainFlowGateway:
        with self._lock:
            if self._board is None or self._profile is None:
                raise DeviceError("no board is connected")
            return BrainFlowGateway(
                self._board,
                self._profile.board_id,
                self._profile.channels,
                post_start_config=post_start_config,
            )

    def release(self) -> bool:
        """Release the active board.  Returns True when one was released."""
        with self._lock:
            board = self._board
            if board is None:
                self._state = DeviceState.DISCONNECTED
                return False
            self._release_locked(board)
            return True

    def _release_locked(self, board: Any) -> None:
        self._board = None
        self._profile = None
        self._state = DeviceState.DISCONNECTED
        try:
            board.release_session()
        except Exception:
            # Releasing a wedged transport must not prevent a reconnect.
            pass
