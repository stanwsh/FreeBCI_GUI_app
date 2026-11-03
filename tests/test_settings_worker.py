import unittest

from PyQt5 import QtCore

from freebci.api.settings_worker import SettingsCommandWorker


class FakeBoard:
    def __init__(self, fail_on=None):
        self.commands = []
        self.fail_on = fail_on

    def config_board(self, command):
        self.commands.append(command)
        if self.fail_on == command:
            raise RuntimeError("rejected %s" % command)
        return "ok"


class SettingsCommandWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])

    def _run(self, worker):
        progress = []
        failures = []
        successes = []
        worker.progress.connect(lambda done, total: progress.append((done, total)))
        worker.failed.connect(failures.append)
        worker.succeeded.connect(lambda: successes.append(True))
        worker.start()
        worker.wait(3000)
        self.app.processEvents()
        return progress, failures, successes

    def test_runs_commands_in_order_and_reports_progress(self):
        board = FakeBoard()
        progress, failures, successes = self._run(
            SettingsCommandWorker(board, ["a", "b", "c"])
        )
        self.assertEqual(board.commands, ["a", "b", "c"])
        self.assertEqual(progress, [(1, 3), (2, 3), (3, 3)])
        self.assertEqual(failures, [])
        self.assertEqual(successes, [True])

    def test_stops_on_a_rejected_command(self):
        board = FakeBoard(fail_on="b")
        progress, failures, successes = self._run(
            SettingsCommandWorker(board, ["a", "b", "c"])
        )
        self.assertEqual(board.commands, ["a", "b"])
        self.assertEqual(progress, [(1, 3)])
        self.assertEqual(len(failures), 1)
        self.assertIn("rejected b", failures[0])
        self.assertEqual(successes, [])


if __name__ == "__main__":
    unittest.main()
