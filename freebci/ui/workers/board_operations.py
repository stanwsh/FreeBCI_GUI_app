"""Serialized background execution for short board commands.

Impedance, channel-enable, timing, and data-mode buttons need to stop the
stream, send one vendor command, and restart it.  Running that sequence on a
single worker keeps those operations off the Qt event loop and prevents two
button presses from interleaving their stop/start pairs.
"""

import queue

from freebci.qt import QtCore


class BoardOperationWorker(QtCore.QThread):
    succeeded = QtCore.Signal(str, object)
    failed = QtCore.Signal(str, str)

    def __init__(self, parent=None):
        super(BoardOperationWorker, self).__init__(parent)
        self._queue = queue.Queue()
        self._stop = False

    def submit(self, name, operation):
        if self._stop:
            return
        self._queue.put((name, operation))
        if not self.isRunning():
            self.start()

    def stop(self):
        self._stop = True
        self._queue.put(None)
        if self.isRunning():
            self.wait(3000)

    def run(self):
        while not self._stop:
            item = self._queue.get()
            if item is None or self._stop:
                break
            name, operation = item
            try:
                result = operation()
            except Exception as exc:  # noqa: BLE001 - board SDK surface
                self.failed.emit(name, str(exc))
            else:
                self.succeeded.emit(name, result)
