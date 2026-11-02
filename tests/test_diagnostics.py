"""GUI-free checks for the passive diagnostics dialog."""
import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets

from freebci.api.my_diagnostics import MyDiagnostics
from freebci.core.diagnostics import diagnostics_fields, idle_fields
from freebci.core.models import SessionState


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


    def test_formats_a_stalled_controller_snapshot(self):
        snapshot = SimpleNamespace(
            state=SessionState.RECORDING,
            session_id="FreeBCI_test",
            elapsed_seconds=12.5,
            sample_count=3120,
            blocks=780,
            lost_samples=0,
            display_dropped_samples=4,
            seconds_since_block=3.2,
            markers=2,
            error=None,
            output_path=r"C:\data\Stream_1",
        )
        writer = SimpleNamespace(
            snapshot=lambda: {"files": 1, "queue_depth": 3, "queue_capacity": 512}
        )
        controller = SimpleNamespace(snapshot=lambda: snapshot, writer=writer)
        fields = diagnostics_fields(controller, r"C:\fallback", "tcp://127.0.0.1:5555", "none")
        self.assertEqual(fields["state"], "recording")
        self.assertEqual(fields["samples"], "3,120")
        self.assertEqual(fields["queue"], "3 / 512")
        self.assertIn("stalled", fields["since"])
        self.assertEqual(fields["output"], snapshot.output_path)

    def test_idle_fields_keep_the_output_root(self):
        fields = idle_fields(r"C:\data", "none configured")
        self.assertEqual(fields["state"], "idle")
        self.assertEqual(fields["output"], r"C:\data")
        self.assertEqual(fields["control"], "not running")


if __name__ == "__main__":
    unittest.main()
