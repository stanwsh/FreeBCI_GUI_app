"""Bounded LSL staging queue.

The GUI receives blocks on the acquisition timer and sends them to one or more
LSL outlets.  A busy event loop must not grow an unbounded Python list or block
acquisition, so each stream stages samples here and sends them in chunks.
Dropped samples are counted rather than silently forgotten.
"""

from __future__ import annotations

import threading
from typing import List, Optional

import numpy as np


class LslSampleQueue:
    def __init__(self, max_samples: int = 4096) -> None:
        self.max_samples = max(1, int(max_samples))
        self._lock = threading.Lock()
        self._rows: List[np.ndarray] = []
        self._count = 0
        self.dropped = 0
        self.received = 0

    @property
    def pending(self) -> int:
        with self._lock:
            return self._count

    def push(self, samples) -> int:
        """Append an ``(n, channels)`` array, dropping oldest rows if needed."""
        array = np.asarray(samples, dtype=np.float64)
        if array.ndim == 1:
            array = array.reshape(1, -1)
        if array.ndim != 2 or array.shape[0] == 0:
            return 0
        array = np.array(array, dtype=np.float64, copy=True)
        with self._lock:
            self.received += int(array.shape[0])
            self._rows.append(array)
            self._count += int(array.shape[0])
            while self._count > self.max_samples:
                head = self._rows[0]
                excess = self._count - self.max_samples
                if head.shape[0] <= excess:
                    self._rows.pop(0)
                    self._count -= int(head.shape[0])
                    self.dropped += int(head.shape[0])
                else:
                    self._rows[0] = head[excess:]
                    self._count -= excess
                    self.dropped += excess
            return self.dropped

    def drain(self) -> Optional[np.ndarray]:
        with self._lock:
            if not self._rows:
                return None
            rows = self._rows
            self._rows = []
            self._count = 0
        if len(rows) == 1:
            return rows[0]
        return np.concatenate(rows, axis=0)

    def clear(self) -> None:
        with self._lock:
            self._rows = []
            self._count = 0
