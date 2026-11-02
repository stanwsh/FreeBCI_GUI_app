"""Background serial connection setup.

Board preparation and the FreeBCI baud/channel handshake take several seconds.
Running that work in the GUI thread freezes the window, so the serial dialog
uses this worker and reports the prepared board back through Qt signals.
"""
import time

from PyQt5 import QtCore
from brainflow.board_shim import BoardShim, BrainFlowInputParams


_BAUD_INDEX = {
    "115200": 0,
    "921600": 1,
    "2000000": 2,
    "3000000": 3,
    "6040000": 4,
}


def _open_board(board_id, serial_port, other_info):
    params = BrainFlowInputParams()
    params.serial_port = serial_port
    params.timeout = 3
    params.other_info = other_info
    board = BoardShim(board_id, params)
    board.prepare_session()
    board.config_board('g')
    time.sleep(0.2)
    return board


class BluetoothConnectWorker(QtCore.QThread):
    """Prepare a Bluetooth serial board without blocking the dialog."""

    succeeded = QtCore.pyqtSignal(object, str)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, board_id, serial_port, baud_rate, parent=None):
        super(BluetoothConnectWorker, self).__init__(parent)
        self.board_id = board_id
        self.serial_port = serial_port
        self.baud_rate = str(baud_rate)

    def run(self):
        board = None
        try:
            board = _open_board(self.board_id, self.serial_port, self.baud_rate)
            response = board.config_board('v')
            board.config_board(',')
            self.succeeded.emit(board, response)
        except Exception as exc:  # noqa: BLE001 - surfaced in the dialog
            if board is not None:
                try:
                    board.release_session()
                except Exception:
                    pass
            self.failed.emit(str(exc))


class SerialConnectWorker(QtCore.QThread):
    """Prepare a board on a worker thread, then hand it to the dialog."""

    succeeded = QtCore.pyqtSignal(object, str)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, board_id, serial_port, initial_baud, target_baud, channel_num, parent=None):
        super(SerialConnectWorker, self).__init__(parent)
        self.board_id = board_id
        self.serial_port = serial_port
        self.initial_baud = str(initial_baud)
        self.target_baud = str(target_baud)
        self.channel_num = int(channel_num)

    def run(self):
        board = None
        try:
            board = _open_board(self.board_id, self.serial_port, self.initial_baud)
            response = board.config_board('v')
            if self.channel_num == 16:
                board.config_board(chr(34) + ',')
            baud_index = _BAUD_INDEX[self.target_baud]
            board.config_board(chr(34) + '_' + str(baud_index))
            board.release_session()
            board = None
            time.sleep(0.2)
            board = _open_board(self.board_id, self.serial_port, self.target_baud)
            self.succeeded.emit(board, response)
        except Exception as exc:  # noqa: BLE001 - reported to the dialog
            if board is not None:
                try:
                    board.release_session()
                except Exception:
                    pass
            self.failed.emit(str(exc))
