"""Bounded, single-allocation history maintenance for display buffers."""

import numpy as np


def append_bounded(history: np.ndarray, block: np.ndarray, limit: int) -> np.ndarray:
    """Return ``history`` plus ``block``, keeping at most ``limit`` columns.

    One allocation is used, and the result is always contiguous chronological
    data.  ``limit`` must be positive.
    """
    if limit <= 0:
        raise ValueError("history limit must be positive")
    if block.shape[1] >= limit:
        return block[:, -limit:].copy()
    keep = max(0, limit - block.shape[1])
    if history.shape[1] > keep:
        history = history[:, -keep:] if keep else history[:, :0]
    return np.concatenate((history, block), axis=1)
