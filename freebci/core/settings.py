"""Typed hardware-settings files with atomic replacement.

The GUI's channel editor owns the XML format.  This module gives the rest of
the application a small, validated view of the same file instead of reaching
into ``ElementTree`` indexes from a dialog.
"""

from __future__ import annotations

import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Tuple


class SettingsError(ValueError):
    """A hardware-settings file is missing or malformed."""


@dataclass(frozen=True)
class ChannelSettings:
    pca_gain: str
    input_type: str
    bias_include: str
    srb2: str
    srb1: str


@dataclass(frozen=True)
class HardwareSettings:
    channels: Tuple[ChannelSettings, ...]
    sampling_rate: Optional[int] = None
    baud_rate: Optional[int] = None


def _text(element: ET.Element, name: str, channel: int) -> str:
    child = element.find(name)
    if child is None or child.text is None or not child.text.strip():
        raise SettingsError("channel %d is missing %s" % (channel, name))
    return child.text.strip()


def _optional_int(root: ET.Element, name: str) -> Optional[int]:
    raw = root.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw)
    except ValueError:
        raise SettingsError("%s must be an integer" % name)
    if value <= 0:
        raise SettingsError("%s must be positive" % name)
    return value


def load_settings(path: str, expected_channels: Optional[int] = None) -> HardwareSettings:
    """Load channel settings and optional sampling/baud metadata.

    Channel elements are ordered by their numeric suffix, not by document
    order, so a hand-edited file cannot silently shift channel assignments.
    """
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as ex:
        raise SettingsError("cannot read settings: %s" % ex)

    if root.tag != "Channels":
        raise SettingsError("root element must be Channels")

    numbered = []
    for element in root:
        if not element.tag.startswith("Channel"):
            continue
        suffix = element.tag[len("Channel"):]
        if not suffix.isdigit() or int(suffix) <= 0:
            raise SettingsError("invalid channel element %s" % element.tag)
        numbered.append((int(suffix), element))
    numbered.sort(key=lambda item: item[0])

    if not numbered:
        raise SettingsError("no channels found")
    if expected_channels is not None and len(numbered) != expected_channels:
        raise SettingsError(
            "expected %d channels, found %d" % (expected_channels, len(numbered))
        )
    for expected, (number, _element) in enumerate(numbered, start=1):
        if number != expected:
            raise SettingsError("channel %d is missing" % expected)

    channels = tuple(
        ChannelSettings(
            pca_gain=_text(element, "pca_gain", number),
            input_type=_text(element, "input_type", number),
            bias_include=_text(element, "bias_include", number),
            srb2=_text(element, "srb2", number),
            srb1=_text(element, "srb1", number),
        )
        for number, element in numbered
    )
    return HardwareSettings(
        channels=channels,
        sampling_rate=_optional_int(root, "sampling_rate"),
        baud_rate=_optional_int(root, "baud_rate"),
    )


def _can_write(directory: str) -> bool:
    """Probe a directory without relying on Windows ACL reporting."""
    probe = None
    try:
        os.makedirs(directory, exist_ok=True)
        probe = os.path.join(
            directory, ".freebci-write-%d-%d" % (os.getpid(), time.time_ns())
        )
        with open(probe, "x", encoding="utf-8"):
            pass
        os.unlink(probe)
        return True
    except OSError:
        if probe is not None:
            try:
                os.unlink(probe)
            except OSError:
                pass
        return False


def _fallback_settings_directory() -> str:
    """Return a per-user settings directory outside the application folder."""
    roots = []
    home = os.environ.get("FREEBCI_HOME")
    if home:
        roots.append(home)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        roots.append(os.path.join(local_app_data, "FreeBCI"))
    roots.append(os.path.join(os.path.expanduser("~"), "Documents", "FreeBCI"))
    for root in roots:
        candidate = os.path.join(root, "settings")
        if _can_write(candidate):
            return candidate
    raise SettingsError("no writable directory for hardware settings")


def writable_settings_path(path: str) -> str:
    """Keep the shipped path when writable, otherwise use the user profile.

    Application folders are often read-only after installation.  The settings
    editor still needs a durable place for its last-sent configuration, so it
    redirects that one autosave file to the writable user data directory.
    """
    path = os.path.abspath(path)
    if _can_write(os.path.dirname(path)):
        return path
    fallback = os.path.join(_fallback_settings_directory(), os.path.basename(path))
    return fallback


def save_settings(path: str, settings: HardwareSettings) -> None:
    """Write settings to a temporary file, fsync it, then atomically replace."""
    if not settings.channels:
        raise SettingsError("refusing to save an empty channel list")

    root = ET.Element("Channels")
    root.set("version", "1.0")
    root.set("encoding", "UTF-8")
    if settings.sampling_rate is not None:
        root.set("sampling_rate", str(settings.sampling_rate))
    if settings.baud_rate is not None:
        root.set("baud_rate", str(settings.baud_rate))
    for number, channel in enumerate(settings.channels, start=1):
        element = ET.SubElement(root, "Channel%d" % number)
        for name in ("pca_gain", "input_type", "bias_include", "srb2", "srb1"):
            child = ET.SubElement(element, name)
            child.text = str(getattr(channel, name))
    try:
        ET.indent(root, space="\t")
    except AttributeError:  # pragma: no cover - Python < 3.9
        pass

    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    temporary = "%s.tmp-%d-%d" % (path, os.getpid(), time.time_ns())
    try:
        with open(temporary, "x", encoding="utf-8", newline="\n") as handle:
            handle.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            handle.write(ET.tostring(root, encoding="unicode"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
