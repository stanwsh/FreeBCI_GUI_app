"""Worker for applying hardware-settings command sequences.

The board configuration protocol is synchronous: each ``config_board`` call
waits for the device.  Keeping the whole sequence on a worker thread means the
settings dialog stays responsive and can report per-command progress.
"""

import threading

from PyQt5 import QtCore


class SettingsCommandWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, int)
    failed = QtCore.pyqtSignal(str)
    succeeded = QtCore.pyqtSignal()

    def __init__(self, board, commands, parent=None):
        super(SettingsCommandWorker, self).__init__(parent)
        self._board = board
        self._commands = tuple(commands)
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()

    @property
    def cancelled(self):
        return self._cancelled.is_set()

    def run(self):
        total = len(self._commands)
        for index, command in enumerate(self._commands, start=1):
            if self._cancelled.is_set():
                return
            try:
                self._board.config_board(command)
            except Exception as exc:  # noqa: BLE001 - device SDK surface
                if not self._cancelled.is_set():
                    self.failed.emit(str(exc))
                return
            self.progress.emit(index, total)
        if not self._cancelled.is_set():
            self.succeeded.emit()
