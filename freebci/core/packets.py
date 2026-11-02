"""Board packet-counter accounting.

FreeBCI frames carry an 8-bit counter.  A 16-channel synchronous frame expands
to 16 rows with the same counter value, so counting every repeated value as a
wrap would report hundreds of false losses.
"""
from __future__ import annotations

from typing import Iterable

# A jump larger than half the 8-bit range is treated as a firmware counter
# restart.  A real gap that large cannot be distinguished from a restart, and
# the board resets its counter when the channel mode changes after start.
COUNTER_RESET_JUMP = 128


class PacketLossCounter:
    def __init__(self) -> None:
        self.received = 0
        self.lost = 0
        self.last = None

    def reset(self) -> None:
        self.received = 0
        self.lost = 0
        self.last = None

    def add(self, values: Iterable[int]) -> None:
        previous = self.last
        for raw in values:
            value = int(raw) & 0xFF
            if previous is None:
                self.received = 1
            elif value == previous:
                continue
            else:
                delta = (value - previous) % 256
                self.received += 1
                if 1 < delta <= COUNTER_RESET_JUMP:
                    self.lost += delta - 1
            previous = value
        self.last = previous

    @property
    def percent(self) -> float:
        total = self.received + self.lost
        return 100.0 * self.lost / total if total else 0.0
