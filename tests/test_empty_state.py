"""Checks for the first-run surface shown before acquisition starts."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from freebci.qt import QtWidgets

from freebci.ui.empty_state import EmptyState


class EmptyStateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_actions_are_wired_and_labelled(self):
        calls = []
        widget = EmptyState(
            lambda: calls.append("connect"),
            lambda: calls.append("demo"),
        )
        try:
            self.assertEqual(widget.connectButton.text(), "Connect a board")
            self.assertEqual(widget.demoButton.text(), "Start demo session")
            self.assertEqual(widget.connectButton.objectName(), "emptyPrimary")
            self.assertEqual(widget.demoButton.objectName(), "emptySecondary")
            widget.connectButton.click()
            widget.demoButton.click()
            self.assertEqual(calls, ["connect", "demo"])
        finally:
            widget.close()


if __name__ == "__main__":
    unittest.main()
