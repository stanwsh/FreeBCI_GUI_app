"""Small DSP façade used by the presentation layer.

The BrainFlow calls live behind ``core.gateway`` so that presentation code does
not need to know about the vendor SDK just to draw a filtered trace.
"""

from __future__ import annotations

import numpy as np

from freebci.core.gateway import (
    bandpass_inplace as _gateway_bandpass,
    bandstop_inplace as _gateway_bandstop,
    fft_magnitude as _gateway_fft,
    standard_powers as _gateway_standard_powers,
)


def fft_magnitude(values: np.ndarray, window: int = 2) -> np.ndarray:
    return _gateway_fft(values, window)


def bandstop_inplace(data: np.ndarray, sampling_rate: int, frequency: float) -> np.ndarray:
    return _gateway_bandstop(data, sampling_rate, frequency)


def bandpass_inplace(
    data: np.ndarray,
    sampling_rate: int,
    low_hz: float,
    high_hz: float,
) -> np.ndarray:
    return _gateway_bandpass(data, sampling_rate, low_hz, high_hz)


def standard_powers(data: np.ndarray, band: np.ndarray, sampling_rate: int):
    return _gateway_standard_powers(data, band, sampling_rate)
