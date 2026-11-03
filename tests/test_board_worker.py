import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore, QtWidgets

from freebci.ui.workers.board_operations import BoardOperationWorker


class BoardOperationWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_runs_operations_in_order(self):
        worker = BoardOperationWorker()
        results = []
        worker.succeeded.connect(lambda name, result: results.append((name, result)))
        worker.submit('a', lambda: 'A')
        worker.submit('b', lambda: 'B')
        self._wait_for(lambda: len(results) == 2)
        worker.stop()
        self.assertEqual(results, [('a', 'A'), ('b', 'B')])

    def test_reports_failure_and_continues(self):
        worker = BoardOperationWorker()
        failures = []
        results = []
        worker.failed.connect(lambda name, message: failures.append((name, message)))
        worker.succeeded.connect(lambda name, result: results.append(name))

        def fail():
            raise RuntimeError('rejected')

        worker.submit('bad', fail)
        worker.submit('good', lambda: 'ok')
        self._wait_for(lambda: len(failures) == 1 and len(results) == 1)
        worker.stop()
        self.assertEqual(failures, [('bad', 'rejected')])
        self.assertEqual(results, ['good'])

    def _wait_for(self, predicate):
        for _ in range(200):
            self.app.processEvents()
            if predicate():
                return
            QtCore.QThread.msleep(5)
        self.fail('worker did not finish')


if __name__ == '__main__':
    unittest.main()
