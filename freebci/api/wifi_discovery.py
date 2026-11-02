"""Detect FreeBCI Wi-Fi boards and the current wireless network.

The board exposes a small HTTP API on its access-point address.  Probing
``/board`` is a stronger availability check than assuming that a configured
board id is reachable: it only succeeds when the board's web service answers.
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple
from urllib.request import Request, build_opener, ProxyHandler

DEFAULT_ADDRESS = "192.168.4.1"
DEFAULT_PORT = 8899
BOARD_HTTP_TIMEOUT = 1.0
_WIFI_MANAGER_MARKER = "FreeBCI WiFi Manager"
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_OPENER = build_opener(ProxyHandler({}))


@dataclass(frozen=True)
class WifiDevice:
    """A board that answered on the local network."""

    address: str
    channels: Optional[int] = None
    board_type: str = ""
    ready: Optional[bool] = None
    port: int = DEFAULT_PORT


@dataclass(frozen=True)
class WifiStatus:
    """The PC's current Wi-Fi association."""

    ssid: Optional[str] = None
    connected: bool = False
    is_freebci: bool = False
    detail: str = "Wi-Fi status unavailable"


@dataclass(frozen=True)
class DiscoveryResult:
    devices: Tuple[WifiDevice, ...]
    wifi: WifiStatus


def parse_board_payload(payload: object) -> Optional[Tuple[Optional[int], str, Optional[bool]]]:
    """Return ``(channels, board_type, ready)`` from a ``/board`` response."""
    if not isinstance(payload, dict):
        return None
    if "board_connected" not in payload and "num_channels" not in payload:
        return None
    channels = payload.get("num_channels")
    if "num_channels" in payload:
        if isinstance(channels, bool) or not isinstance(channels, int) or channels <= 0:
            return None
    else:
        channels = None
    board_type = payload.get("board_type")
    board_type = str(board_type) if board_type else ""
    ready = payload.get("board_connected")
    if not isinstance(ready, bool):
        ready = None
    return channels, board_type, ready


def parse_wifi_interfaces(text: str) -> WifiStatus:
    """Parse the relevant fields from ``netsh wlan show interfaces``."""
    ssid = None
    state = None
    for line in text.splitlines():
        match = re.match(r"^\s*State\s*:\s*(.+?)\s*$", line, re.IGNORECASE)
        if match and state is None:
            state = match.group(1).strip()
        match = re.match(r"^\s*SSID\s*:\s*(.+?)\s*$", line, re.IGNORECASE)
        if match and ssid is None:
            ssid = match.group(1).strip()
    if state and state.lower() in {"disconnected", "not connected"}:
        return WifiStatus(detail="Not connected to a Wi-Fi network")
    if not ssid:
        return WifiStatus()
    return WifiStatus(
        ssid=ssid,
        connected=True,
        is_freebci=ssid.lower().startswith("freebci"),
        detail="Connected to %s" % ssid,
    )


def _decode_windows_output(data: bytes) -> str:
    try:
        return data.decode("mbcs", errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def _run_netsh() -> str:
    if os.name != "nt":
        return ""
    try:
        completed = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return _decode_windows_output(completed.stdout)


def current_wifi_status() -> WifiStatus:
    """Read the current SSID without depending on a third-party package."""
    text = _run_netsh()
    if not text:
        return WifiStatus()
    return parse_wifi_interfaces(text)


def _is_private_ipv4(address: str) -> bool:
    try:
        parts = [int(part) for part in address.split(".")]
    except ValueError:
        return False
    if len(parts) != 4 or any(part < 0 or part > 255 for part in parts):
        return False
    first, second = parts[0], parts[1]
    return (
        first == 10
        or (first == 172 and 16 <= second <= 31)
        or (first == 192 and second == 168)
    )


def _local_ipv4_addresses() -> List[str]:
    addresses = set()
    try:
        for entry in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(entry[4][0])
    except OSError:
        pass
    if os.name == "nt":
        try:
            completed = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                timeout=3,
                check=False,
            )
            text = _decode_windows_output(completed.stdout)
            addresses.update(_IPV4_RE.findall(text))
        except (OSError, subprocess.TimeoutExpired):
            pass
    return sorted(address for address in addresses if _is_private_ipv4(address))


def candidate_addresses(
    extra: Iterable[str] = (),
    local_addresses: Optional[Sequence[str]] = None,
) -> Tuple[str, ...]:
    """Build a small, deterministic list of likely board addresses."""
    addresses = [DEFAULT_ADDRESS]
    addresses.extend(str(address).strip() for address in extra if str(address).strip())
    if local_addresses is None:
        local_addresses = _local_ipv4_addresses()
    for address in local_addresses:
        if not _is_private_ipv4(address):
            continue
        parts = address.split(".")
        addresses.append(".".join(parts[:3] + ["1"]))
    result: List[str] = []
    for address in addresses:
        if address and address not in result:
            result.append(address)
    return tuple(result)


def _read_text(address: str, path: str, timeout: float) -> str:
    request = Request(
        "http://%s%s" % (address, path),
        headers={"User-Agent": "FreeBCI-GUI"},
    )
    with _OPENER.open(request, timeout=timeout) as response:
        return response.read(65536).decode("utf-8", errors="replace")


def probe_board(address: str, timeout: float = BOARD_HTTP_TIMEOUT) -> Optional[WifiDevice]:
    """Return a device only if the board's HTTP service answers at ``address``."""
    try:
        payload = json.loads(_read_text(address, "/board", timeout))
    except Exception:  # noqa: BLE001 - any network/JSON failure means "not a board"
        try:
            text = _read_text(address, "/wifi", timeout)
        except Exception:  # noqa: BLE001 - not reachable
            return None
        if _WIFI_MANAGER_MARKER not in text:
            return None
        return WifiDevice(address=address)
    parsed = parse_board_payload(payload)
    if parsed is None:
        return None
    channels, board_type, ready = parsed
    return WifiDevice(
        address=address,
        channels=channels,
        board_type=board_type,
        ready=ready,
    )


def probe_addresses(
    addresses: Iterable[str],
    timeout: float = BOARD_HTTP_TIMEOUT,
) -> Tuple[WifiDevice, ...]:
    unique = []
    for address in addresses:
        if address and address not in unique:
            unique.append(address)
    if not unique:
        return ()
    with ThreadPoolExecutor(max_workers=min(8, len(unique))) as executor:
        devices = list(executor.map(lambda address: probe_board(address, timeout), unique))
    found = [device for device in devices if device is not None]
    return tuple(sorted(found, key=lambda device: (device.address != DEFAULT_ADDRESS, device.address)))


def discover(
    extra_addresses: Iterable[str] = (),
    timeout: float = BOARD_HTTP_TIMEOUT,
) -> DiscoveryResult:
    """Probe likely board addresses and report the current Wi-Fi association."""
    wifi = current_wifi_status()
    addresses = candidate_addresses(extra_addresses)
    return DiscoveryResult(devices=probe_addresses(addresses, timeout), wifi=wifi)
