"""Background Wi-Fi discovery and board preparation."""
import threading

from freebci.qt import QtCore

from freebci.ui.workers.wifi_discovery import discover
from freebci.core.gateway import prepare_wifi_board


class WifiDiscoveryWorker(QtCore.QThread):
    """Find boards on the local network without blocking the dialog."""

    found = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, extra_addresses=(), parent=None):
        super(WifiDiscoveryWorker, self).__init__(parent)
        self.extra_addresses = tuple(extra_addresses)
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()

    def run(self):
        try:
            result = discover(self.extra_addresses)
        except Exception as exc:  # noqa: BLE001 - surfaced in the dialog
            if not self._cancelled.is_set():
                self.failed.emit(str(exc))
            return
        if not self._cancelled.is_set():
            self.found.emit(result)


class WifiConnectWorker(QtCore.QThread):
    """Prepare a Wi-Fi board, retrying the first connection a few times."""

    succeeded = QtCore.Signal(object, str)
    failed = QtCore.Signal(str)
    progress = QtCore.Signal(str)

    def __init__(self, board_id, ip_address, ip_port, parent=None):
        super(WifiConnectWorker, self).__init__(parent)
        self.board_id = board_id
        self.ip_address = ip_address
        self.ip_port = int(ip_port)
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()

    def run(self):
        board = None
        last_error = "Connection cancelled"
        for attempt in range(3):
            if self._cancelled.is_set():
                break
            self.progress.emit(
                "Connecting to %s (attempt %d of 3)..." % (self.ip_address, attempt + 1)
            )
            try:
                board = prepare_wifi_board(
                    self.board_id, self.ip_address, self.ip_port, timeout=5
                )
                if self._cancelled.is_set():
                    try:
                        board.release_session()
                    finally:
                        return
                board.config_board('~6')
                self._cancelled.wait(0.1)
                response = board.config_board('v') or ''
                if self._cancelled.is_set():
                    try:
                        board.release_session()
                    finally:
                        return
                self.succeeded.emit(board, response)
                return
            except Exception as exc:  # noqa: BLE001 - retried, then surfaced
                last_error = str(exc)
                if board is not None:
                    try:
                        board.release_session()
                    except Exception:
                        pass
                board = None
                if self._cancelled.is_set():
                    break
                if attempt < 2 and self._cancelled.wait(1.0):
                    break
        if not self._cancelled.is_set():
            self.failed.emit(last_error)
