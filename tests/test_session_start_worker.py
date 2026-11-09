import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from freebci.qt import QtCore, QtWidgets

from freebci.ui.workers.session_start import SessionStartWorker


class FakeController:
    def __init__(self, error=None):
        self.error = error
        self.started = False

    def start(self):
        self.started = True
        if self.error:
            raise RuntimeError(self.error)


class SessionStartWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def _wait(self, worker, predicate):
        for _ in range(200):
            self.app.processEvents()
            if predicate():
                return
            QtCore.QThread.msleep(5)
        self.fail("worker did not finish")

    def test_reports_success(self):
        controller = FakeController()
        worker = SessionStartWorker(controller)
        delivered = []
        worker.succeeded.connect(delivered.append)
        worker.start()
        self._wait(worker, lambda: bool(delivered))
        worker.wait(1000)
        self.assertTrue(controller.started)
        self.assertIs(delivered[0], controller)

    def test_reports_start_failure(self):
        controller = FakeController("board did not start")
        worker = SessionStartWorker(controller)
        failures = []
        worker.failed.connect(failures.append)
        worker.start()
        self._wait(worker, lambda: bool(failures))
        worker.wait(1000)
        self.assertIn("board did not start", failures[0])


if __name__ == "__main__":
    unittest.main()
