"""Qt-free acquisition core for FreeBCI GUI.

The modules in this package do not import PyQt5.  The GUI talks to the core
through a small number of data objects (``SessionConfig``, ``SampleBlock``,
``StateSnapshot``) and the ``SessionController`` facade.
"""

from freebci.core.models import (
    BoardProfile,
    SampleBlock,
    SessionConfig,
    SessionState,
    SessionStats,
    SessionStatus,
)

__all__ = [
    "BoardProfile",
    "SampleBlock",
    "SessionConfig",
    "SessionState",
    "SessionStats",
    "SessionStatus",
]
