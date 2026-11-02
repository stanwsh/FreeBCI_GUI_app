"""A deterministic, hardware-free board for demos and tests.

The simulator implements the small set of ``BoardShim`` methods the GUI uses.
It lets a new installation exercise acquisition, plotting, recording, LSL, and
the diagnostics window without a FreeBCI board connected.
"""
from __future__ import annotations

import time

import numpy as np


class SimulatedBoard:
    """Generate synthetic EEG frames in the BrainFlow row layout."""

    def __init__(self, channels: int = 16, sampling_rate: int = 250) -> None:
        self.channels = int(channels)
        self.sampling_rate = int(sampling_rate)
        self.num_rows = 1 + self.channels + 3 + 4 + 2
        self._active = False
        self._frame = 0
        self._last_read = time.monotonic()

    # ---------------------------------------------------------- BoardShim API
    def start_stream(self, *args, **kwargs) -> None:
        self._active = True
        self._last_read = time.monotonic()

    def stop_stream(self, *args, **kwargs) -> None:
        self._active = False

    def prepare_session(self, *args, **kwargs) -> None:
        pass

    def release_session(self, *args, **kwargs) -> None:
        self._active = False

    def config_board(self, command: str, *args, **kwargs) -> str:
        return "ok"

    def get_board_data_count(self, *args, **kwargs) -> int:
        if not self._active:
            return 0
        # Produce roughly one 10 ms poll worth of samples at the configured rate.
        return max(1, int(self.sampling_rate / 100))

    def get_board_data(self, *args, **kwargs) -> np.ndarray:
        if not self._active:
            return np.zeros((self.num_rows, 0), dtype=np.float64)
        self._last_read = time.monotonic()
        count = self.get_board_data_count()
        # Pace simulated frames like a real board instead of spinning as fast as
        # Python can allocate arrays.
        time.sleep(count / float(self.sampling_rate))
        data = np.zeros((self.num_rows, count), dtype=np.float64)
        t = (np.arange(count, dtype=np.float64) + self._frame) / float(self.sampling_rate)
        for channel in range(1, self.channels + 1):
            # A mix of alpha and slower activity, with a channel-specific phase.
            data[channel, :] = (
                20.0 * np.sin(2.0 * np.pi * (8.0 + channel % 4) * t + channel)
                + 5.0 * np.sin(2.0 * np.pi * 1.5 * t)
            )
        data[0, :] = (self._frame // count) % 256
        data[self.channels + 1:self.channels + 4, :] = 1.0
        data[self.channels + 4:self.channels + 8, :] = 0.0
        self._frame += count
        return data

    def get_eeg_channels(self, board_id: int) -> list:
        return list(range(1, self.channels + 1))

    def get_accel_channels(self, board_id: int) -> list:
        return [self.channels + 1, self.channels + 2, self.channels + 3]

    def get_other_channels(self, board_id: int) -> list:
        return [self.channels + 4, self.channels + 5, self.channels + 6, self.channels + 7]

    def get_num_rows(self, board_id: int) -> int:
        return self.num_rows
