"""Qt-free acquisition core for FreeBCI GUI.

The modules in this package do not import PyQt5.  The GUI talks to the core
through a small number of data objects (``SessionConfig``, ``SampleBlock``,
``StateSnapshot``) and the ``SessionController`` facade.
"""

from freebci.core.control import ControlClient, ControlError, ControlServer
from freebci.core.device import DeviceError, DeviceManager, DeviceState
from freebci.core.gateway import prepare_serial_board, prepare_wifi_board
from freebci.core.models import (
    BoardProfile,
    SampleBlock,
    SessionConfig,
    SessionState,
    SessionStats,
    SessionStatus,
)
from freebci.core.simulator import SimulatedBoard

__all__ = [
    "BoardProfile",
    "ControlClient",
    "ControlError",
    "ControlServer",
    "DeviceError",
    "DeviceManager",
    "DeviceState",
    "prepare_serial_board",
    "prepare_wifi_board",
    "SampleBlock",
    "SessionConfig",
    "SessionState",
    "SessionStats",
    "SessionStatus",
    "SimulatedBoard",
]
