"""GUI-free checks for the passive diagnostics dialog."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets

from freebci.api.my_diagnostics import MyDiagnostics


class DiagnosticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_renders_snapshot_and_copyable_summary(self):
        data = {
            "state": "recording",
            "session": "FreeBCI_test",
            "elapsed": "12.5 s",
            "rate": "249.8 Hz",
            "samples": "3120",
            "blocks": "780",
            "lost": "0",
            "dropped": "0",
            "since": "0.02 s",
            "markers": "2",
            "files": "1",
            "queue": "3 / 512",
            "recording": "1.csv, 1.txt",
            "output": r"C:\data\Stream_1",
            "control": "tcp://127.0.0.1:5555",
            "lsl": "2 active",
            "error": "-",
        }
        dialog = MyDiagnostics(lambda: data)
        try:
            dialog.refresh()
            self.assertEqual(dialog.fields["state"].text(), "recording")
            self.assertEqual(dialog.fields["samples"].text(), "3120")
            self.assertEqual(dialog.fields["queue"].text(), "3 / 512")
            summary = dialog.summary_text()
            self.assertIn("State: recording", summary)
            self.assertIn("Samples received: 3120", summary)
        finally:
            dialog.close()


if __name__ == "__main__":
    unittest.main()
