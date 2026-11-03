"""Board catalog data shared by the GUI and the core.

The table is intentionally data, not device logic: no BrainFlow import, no
BoardShim creation.  ``ConnectionInfo`` still exposes the legacy list shape
for the existing dialogs, but the catalog is the single source of truth.
"""

from typing import Dict, List, Mapping, Tuple

from freebci.core.models import BoardProfile

# name, board id, connect type, baud, protocol, max rate, wifi, ext trigger,
# channels, accelerometer, external trigger, battery
BOARD_ROWS: Tuple[Tuple[object, ...], ...] = (
    ("FreeBCI_USB_8_I", 2023, 2, "921600", 1, 2000, 0, 0, 8, False, False, True),
    ("FreeBCI_USB_8_II", 2024, 2, "921600", 0, 2000, 0, 0, 8, False, False, True),
    ("FreeBCI_USB_16_I", 2025, 2, "921600", 1, 1000, 0, 0, 16, True, False, True),
    ("FreeBCI_USB_16_II", 2026, 2, "921600", 0, 1000, 0, 0, 16, False, False, False),
    ("FreeBCI_BT_8_I", 2027, 2, "921600", 1, 2000, 0, 0, 8, False, False, False),
    ("FreeBCI_BT_8_II", 2028, 2, "921600", 0, 2000, 0, 0, 8, False, False, False),
    ("FreeBCI_BT_16_I", 2029, 2, "921600", 1, 1000, 0, 0, 16, False, False, False),
    ("FreeBCI_BT_16_II", 2030, 2, "921600", 0, 1000, 0, 0, 16, False, False, False),
    ("FreeBCI_WiFi_8_I_USB", 2031, 2, "2000000", 1, 4000, 1, 0, 8, True, False, True),
    ("FreeBCI_WiFi_8_I_WIFI", 2032, 1, False, 1, 4000, 1, 0, 8, True, False, True),
    ("FreeBCI_WiFi_8_II_USB", 2033, 2, "2000000", 0, 4000, 1, 0, 8, True, False, True),
    ("FreeBCI_WiFi_8_II_WIFI", 2034, 1, False, 0, 4000, 1, 0, 8, True, False, True),
    ("FreeBCI_WiFi_8_III_USB", 2035, 2, "2000000", 1, 4000, 1, 1, 8, True, True, True),
    ("FreeBCI_WiFi_8_III_WIFI", 2036, 1, False, 1, 4000, 1, 1, 8, True, True, True),
    ("FreeBCI_WiFi_16_I_USB", 2037, 2, "2000000", 1, 4000, 1, 0, 16, True, False, True),
    ("FreeBCI_WiFi_16_I_WIFI", 2038, 1, False, 1, 4000, 1, 0, 16, True, False, True),
    ("FreeBCI_WiFi_16_II_USB", 2039, 2, "2000000", 0, 4000, 1, 0, 16, True, False, True),
    ("FreeBCI_WiFi_16_II_WIFI", 2040, 1, False, 0, 4000, 1, 0, 16, True, False, True),
    ("FreeBCI_WiFi_16_III_USB", 2041, 2, "2000000", 1, 4000, 1, 1, 16, True, True, True),
    ("FreeBCI_WiFi_16_III_WIFI", 2042, 1, False, 1, 4000, 1, 1, 16, True, True, True),
    ("FreeBCI_USB_24", 2043, 2, "6040000", 0, 4000, 0, 1, 24, False, True, False),
    ("FreeBCI_USB_32", 2044, 2, "6040000", 0, 4000, 0, 1, 32, False, True, False),
    ("FreeBCI_USB_64", 2045, 2, "6040000", 0, 2000, 0, 1, 64, False, True, False),
    ("FreeBCI_WiFi_24_USB", 2046, 2, "2000000", 0, 2000, 0, 1, 24, False, True, False),
    ("FreeBCI_WiFi_24_WIFI", 2047, 1, False, 0, 2000, 0, 1, 24, False, True, False),
    ("FreeBCI_WiFi_32_USB", 2048, 2, "2000000", 0, 1000, 0, 1, 32, False, True, False),
    ("FreeBCI_WiFi_32_WIFI", 2049, 1, False, 0, 8000, 0, 1, 32, False, True, False),
    ("FreeBCI_WiFi_64_USB", 2050, 2, "2000000", 0, 500, 0, 1, 64, False, True, False),
    ("FreeBCI_WiFi_64_WIFI", 2051, 1, False, 0, 500, 0, 1, 64, False, True, False),
)

_BY_ID = {int(row[1]): row for row in BOARD_ROWS}


def rows() -> List[List[object]]:
    """Return the legacy mutable list-of-lists shape used by the dialogs."""
    return [list(row) for row in BOARD_ROWS]


def get_row(board_id: int) -> Tuple[object, ...]:
    try:
        return _BY_ID[int(board_id)]
    except KeyError:
        raise KeyError("unknown FreeBCI board id: %s" % (board_id,))


def load_catalog() -> Mapping[int, BoardProfile]:
    catalog: Dict[int, BoardProfile] = {}
    for row in BOARD_ROWS:
        catalog[int(row[1])] = BoardProfile(
            board_id=int(row[1]),
            name=str(row[0]),
            channels=int(row[8]),
            sampling_rate=int(row[5]),
            has_accelerometer=bool(row[9]),
            has_external_trigger=bool(row[10]),
            has_battery=bool(row[11]),
        )
    return catalog


def get_profile(board_id: int) -> BoardProfile:
    try:
        return load_catalog()[int(board_id)]
    except KeyError:
        raise KeyError("unknown FreeBCI board id: %s" % (board_id,))
