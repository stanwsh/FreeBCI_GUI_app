"""Background Wi-Fi discovery and board preparation."""
import time
from urllib.parse import urlparse

import upnpclient
from PyQt5 import QtCore
from brainflow.board_shim import BoardShim, BrainFlowInputParams


class WifiDiscoveryWorker(QtCore.QThread):
    """Find FreeBCI access points without blocking the dialog."""

    found = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(WifiDiscoveryWorker, self).__init__(parent)

    def run(self):
        try:
            devices = upnpclient.discover(timeout=2)
            rows = []
            for device in devices:
                if device.device_type != 'urn:schemas-upnp-org:device:Basic:1':
                    continue
                parsed = urlparse(device.location)
                rows.append((str(device.serial_number), parsed.hostname))
            self.found.emit(rows)
        except Exception as exc:  # noqa: BLE001 - surfaced in the dialog
            self.failed.emit(str(exc))


class WifiConnectWorker(QtCore.QThread):
    """Prepare a Wi-Fi board and apply the FreeBCI channel handshake."""

    succeeded = QtCore.pyqtSignal(object, str)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, board_id, ip_address, ip_port, channel_num, parent=None):
        super(WifiConnectWorker, self).__init__(parent)
        self.board_id = board_id
        self.ip_address = ip_address
        self.ip_port = int(ip_port)
        self.channel_num = int(channel_num)

    def run(self):
        board = None
        try:
            params = BrainFlowInputParams()
            params.ip_address = self.ip_address
            params.ip_port = self.ip_port
            params.timeout = 3
            board = BoardShim(self.board_id, params)
            board.prepare_session()
            board.config_board('~6')
            time.sleep(0.1)
            response = board.config_board('v')
            if self.channel_num == 16:
                board.config_board(chr(34) + ',')
            self.succeeded.emit(board, response)
        except Exception as exc:  # noqa: BLE001 - surfaced in the dialog
            if board is not None:
                try:
                    board.release_session()
                except Exception:
                    pass
            self.failed.emit(str(exc))
