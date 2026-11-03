"""Fixed-capacity ring buffer for display and processing windows.

The producer writes blocks; readers copy the latest contiguous window.  The
buffer never blocks the producer: when full, the oldest samples are overwritten.
"""

import threading

import numpy as np


class RingBuffer:
    def __init__(self, rows: int, capacity: int, dtype=np.float64):
        if rows <= 0 or capacity <= 0:
            raise ValueError("rows and capacity must be positive")
        self.rows = int(rows)
        self.capacity = int(capacity)
        self._buffer = np.zeros((self.rows, self.capacity), dtype=dtype)
        self._write = 0
        self._count = 0
        self._total = 0
        self._lock = threading.Lock()

    @property
    def total_written(self) -> int:
        with self._lock:
            return self._total

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    def write(self, block) -> None:
        data = getattr(block, "data", block)
        data = np.asarray(data)
        if data.ndim != 2 or data.shape[0] != self.rows or data.shape[1] == 0:
            raise ValueError(
                "ring block must have shape (%d, n), got %s"
                % (self.rows, data.shape)
            )
        with self._lock:
            if data.shape[1] >= self.capacity:
                data = data[:, -self.capacity:]
            n = data.shape[1]
            first = min(n, self.capacity - self._write)
            self._buffer[:, self._write:self._write + first] = data[:, :first]
            remainder = n - first
            if remainder:
                self._buffer[:, :remainder] = data[:, first:]
            self._write = (self._write + n) % self.capacity
            self._count = min(self.capacity, self._count + n)
            self._total += n

    def latest(self, n_samples: int = None) -> np.ndarray:
        with self._lock:
            n = self._count if n_samples is None else min(int(n_samples), self._count)
            if n <= 0:
                return np.zeros((self.rows, 0), dtype=self._buffer.dtype)
            start = (self._write - n) % self.capacity
            end = start + n
            if end <= self.capacity:
                return self._buffer[:, start:end].copy()
            return np.concatenate(
                (self._buffer[:, start:], self._buffer[:, :end - self.capacity]),
                axis=1,
            )

    def clear(self) -> None:
        with self._lock:
            self._write = 0
            self._count = 0
            self._total = 0
