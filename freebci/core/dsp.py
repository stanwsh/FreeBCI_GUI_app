"""Small DSP façade used by the presentation layer.

BrainFlow's filter functions operate in place on NumPy arrays.  Keeping those
imports here means the main window does not need to know about BrainFlow just
to draw a notch-filtered trace.
"""

from __future__ import annotations

import numpy as np


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
