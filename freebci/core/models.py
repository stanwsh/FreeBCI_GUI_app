"""Value objects shared by the acquisition core and the GUI.

These types are deliberately free of PyQt5 and BrainFlow.  A block contains
the raw board rows exactly as BrainFlow returned them; channel extraction is
left to the consumer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


class SessionState(Enum):
    """Coarse session lifecycle.  Transitions are owned by SessionController."""

    IDLE = "idle"
    CONNECTED = "connected"
    ARMED = "armed"
    RECORDING = "recording"
    STOPPING = "stopping"
    FINALIZED = "finalized"
    FAILED = "failed"


class SessionStatus(str, Enum):
    """Outcome written to the session manifest."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class BoardProfile:
    board_id: int
    name: str
    channels: int
    sampling_rate: int
    has_accelerometer: bool = False
    has_external_trigger: bool = False
    has_battery: bool = False


@dataclass(frozen=True)
class SessionConfig:
    session_id: str
    board: BoardProfile
    sampling_rate: int
    output_root: str
    channel_count: int
    started_wall_ns: int = 0

    @property
    def board_id(self) -> int:
        return self.board.board_id

    @property
    def board_name(self) -> str:
        return self.board.name


@dataclass(frozen=True)
class SampleBlock:
    """One contiguous read from the device.

    ``sample_index`` is the index of the first EEG sample in the session,
    starting at zero.  ``first_sample_time_ns`` is a reconstructed wall-clock
    estimate for that sample, not a hardware timestamp.
    """

    sequence: int
    sample_index: int
    data: np.ndarray
    sampling_rate: int
    host_time_ns: int
    monotonic_ns: int
    first_sample_time_ns: int

    @property
    def sample_count(self) -> int:
        return int(self.data.shape[1])

    @property
    def duration_ns(self) -> int:
        if self.sampling_rate <= 0:
            return 0
        return int(self.sample_count * 1_000_000_000 / self.sampling_rate)


@dataclass
class SessionStats:
    blocks: int = 0
    samples: int = 0
    display_dropped_samples: int = 0
    packet_loss_samples: int = 0
    started_monotonic_ns: int = 0
    stopped_monotonic_ns: int = 0
    error: Optional[str] = None

    def reset(self) -> None:
        self.blocks = 0
        self.samples = 0
        self.display_dropped_samples = 0
        self.packet_loss_samples = 0
        self.started_monotonic_ns = 0
        self.stopped_monotonic_ns = 0
        self.error = None

    @property
    def duration_seconds(self) -> float:
        if not self.started_monotonic_ns:
            return 0.0
        end = self.stopped_monotonic_ns or self.started_monotonic_ns
        return max(0.0, (end - self.started_monotonic_ns) / 1_000_000_000)


@dataclass(frozen=True)
class StateSnapshot:
    """Immutable state published to the GUI once per refresh tick."""

    state: SessionState
    session_id: str
    sample_count: int
    blocks: int
    elapsed_seconds: float
    display_dropped_samples: int
    lost_samples: int = 0
    error: Optional[str] = None
    output_path: str = ""
