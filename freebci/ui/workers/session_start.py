"""Start a prepared session without blocking the Qt event loop."""

from PyQt5 import QtCore


class SessionStartWorker(QtCore.QThread):
    succeeded = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, controller, parent=None):
        super(SessionStartWorker, self).__init__(parent)
        self.controller = controller

    def run(self):
        try:
            self.controller.start()
        except Exception as exc:  # noqa: BLE001 - board SDK surface
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(self.controller)
