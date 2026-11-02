"""Session clock and block timestamp reconstruction.

Only host clocks are used.  The original device packet counter is useful for
loss accounting, but it is not a sample timestamp and is not exposed as one.
"""
from __future__ import annotations

import time
from typing import Optional

from freebci.core.models import SampleBlock


class SessionClock:
    """Monotonic session time plus wall-clock estimates for each block."""

    def __init__(self) -> None:
        self.started_wall_ns: int = 0
        self.started_monotonic_ns: int = 0
        self.sample_index: int = 0
        self.sequence: int = 0

    @property
    def running(self) -> bool:
        return self.started_monotonic_ns != 0

    def start(self) -> int:
        self.started_wall_ns = time.time_ns()
        self.started_monotonic_ns = time.perf_counter_ns()
        self.sample_index = 0
        self.sequence = 0
        return self.started_wall_ns

    def elapsed_seconds(self, now_monotonic_ns: Optional[int] = None) -> float:
        if not self.started_monotonic_ns:
            return 0.0
        now = now_monotonic_ns or time.perf_counter_ns()
        return max(0.0, (now - self.started_monotonic_ns) / 1_000_000_000)

    def new_block(self, data, sampling_rate: int) -> SampleBlock:
        """Create a block and advance the sample index.

        The first-sample wall time is estimated by subtracting the block
        duration from the host receive time.  This is honest block-level
        timing, not a hardware timestamp.
        """
        now_wall_ns = time.time_ns()
        now_mono_ns = time.perf_counter_ns()
        count = int(data.shape[1]) if getattr(data, "ndim", 0) == 2 else 0
        duration_ns = int(count * 1_000_000_000 / sampling_rate) if sampling_rate else 0
        first_ns = now_wall_ns - duration_ns
        block = SampleBlock(
            sequence=self.sequence,
            sample_index=self.sample_index,
            data=data,
            sampling_rate=sampling_rate,
            host_time_ns=now_wall_ns,
            monotonic_ns=now_mono_ns,
            first_sample_time_ns=first_ns,
        )
        self.sample_index += count
        self.sequence += 1
        return block
