"""Pure state-to-action mapping for the window and tests.

The window still has legacy booleans for widget bookkeeping, but menu and
connection enablement should be derived from one immutable table instead of
being recomputed ad hoc in each handler.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionAvailability:
    marker: bool
    demo: bool
    boards: bool
    release: bool
    hardware: bool
    channels: bool


def action_availability(
    state: str,
    starting: bool = False,
    connected: bool = False,
) -> ActionAvailability:
    active = state in ("armed", "recording", "stopping")
    editable = not active and not starting
    return ActionAvailability(
        marker=state in ("armed", "recording"),
        demo=editable,
        boards=editable,
        release=connected and not starting,
        hardware=editable,
        channels=editable,
    )
