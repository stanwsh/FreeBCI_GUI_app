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

    The module also owns the small transport-preparation helpers below so that
    dialogs and workers never import BrainFlow themselves.  Preparation is
    deliberately separate from acquisition: a prepared board is handed to
    :class:`BrainFlowGateway`, which is the only object the session touches.
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


def prepare_serial_board(
    board_id: int,
    serial_port: str,
    other_info: str,
    timeout: float = 3.0,
):
    """Open and prepare a serial board, releasing it if preparation fails."""
    from brainflow.board_shim import BoardShim, BrainFlowInputParams

    params = BrainFlowInputParams()
    params.serial_port = str(serial_port)
    params.other_info = str(other_info)
    params.timeout = float(timeout)
    board = BoardShim(int(board_id), params)
    try:
        board.prepare_session()
    except Exception:
        try:
            board.release_session()
        except Exception:
            pass
        raise
    return board


def prepare_wifi_board(
    board_id: int,
    ip_address: str,
    ip_port: int,
    timeout: float = 5.0,
):
    """Open and prepare a Wi-Fi board, releasing it if preparation fails."""
    from brainflow.board_shim import BoardShim, BrainFlowInputParams

    params = BrainFlowInputParams()
    params.ip_address = str(ip_address)
    params.ip_port = int(ip_port)
    params.timeout = float(timeout)
    board = BoardShim(int(board_id), params)
    try:
        board.prepare_session()
    except Exception:
        try:
            board.release_session()
        except Exception:
            pass
        raise
    return board


def fft_magnitude(values: np.ndarray, window: int = 2) -> np.ndarray:
    from brainflow.data_filter import DataFilter

    return DataFilter.perform_fft(values, window)


def bandstop_inplace(data: np.ndarray, sampling_rate: int, frequency: float) -> np.ndarray:
    from brainflow.data_filter import DataFilter, FilterTypes

    DataFilter.perform_bandstop(
        data, sampling_rate, frequency, 4.0, 2, FilterTypes.BUTTERWORTH, 0.0
    )
    return data


def bandpass_inplace(
    data: np.ndarray,
    sampling_rate: int,
    low_hz: float,
    high_hz: float,
) -> np.ndarray:
    from brainflow.data_filter import DataFilter, FilterTypes

    center = (low_hz + high_hz) / 2.0
    width = high_hz - low_hz
    DataFilter.perform_bandpass(
        data, sampling_rate, center, width, 2, FilterTypes.BUTTERWORTH, 0.0
    )
    return data


def standard_powers(data: np.ndarray, band: np.ndarray, sampling_rate: int):
    from brainflow.data_filter import DataFilter

    return DataFilter.get_standard_powers(np.asarray(data), band, sampling_rate, False)
