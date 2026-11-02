"""Thin device gateway boundary.

The core depends on this small surface rather than on a BrainFlow
``BoardShim`` directly.  The adapter below is the only place where the
(vendored, hardware-validated) BrainFlow package is called.
"""
from __future__ import annotations

from typing import Any, Iterable, Protocol, runtime_checkable

import numpy as np


class GatewayError(RuntimeError):
    """Raised when a transport-level operation fails."""


@runtime_checkable
class BoardGateway(Protocol):
    board_id: int
    channel_count: int

    def start_stream(self) -> None: ...
    def stop_stream(self) -> None: ...
    def get_data_count(self) -> int: ...
    def read(self) -> np.ndarray: ...
    def release(self) -> None: ...


class BrainFlowGateway:
    """Adapter around an already-prepared BrainFlow ``BoardShim``.

    Connection dialogs remain responsible for transport preparation because
    they contain the hardware-specific COM/Wi-Fi/UPnP setup.  Once prepared,
    the board is handed to this gateway and is only touched by the acquisition
    worker and the session controller.
    """

    def __init__(
        self,
        board: Any,
        board_id: int,
        channel_count: int,
        post_start_config: Iterable[str] = (),
    ) -> None:
        if board is None:
            raise GatewayError("no prepared BrainFlow board was supplied")
        self._board = board
        self.board_id = int(board_id)
        self.channel_count = int(channel_count)
        self.post_start_config = tuple(post_start_config)

    def start_stream(self) -> None:
        try:
            self._board.start_stream()
            for command in self.post_start_config:
                self._board.config_board(command)
        except Exception as exc:  # noqa: BLE001 - SDK exception surface is broad
            try:
                self._board.stop_stream()
            except Exception:  # noqa: BLE001 - already failing
                pass
            raise GatewayError("could not start the board stream: %s" % exc) from exc

    def stop_stream(self) -> None:
        try:
            self._board.stop_stream()
        except Exception as exc:  # noqa: BLE001
            raise GatewayError("could not stop the board stream: %s" % exc) from exc

    def get_data_count(self) -> int:
        try:
            return int(self._board.get_board_data_count())
        except Exception as exc:  # noqa: BLE001
            raise GatewayError("could not query the board buffer: %s" % exc) from exc

    def read(self) -> np.ndarray:
        try:
            return self._board.get_board_data()
        except Exception as exc:  # noqa: BLE001
            raise GatewayError("could not read the board buffer: %s" % exc) from exc

    def release(self) -> None:
        try:
            self._board.release_session()
        except Exception as exc:  # noqa: BLE001
            raise GatewayError("could not release the board session: %s" % exc) from exc
