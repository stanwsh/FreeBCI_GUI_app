import unittest
from types import SimpleNamespace

import numpy as np

from freebci.api.session_view_model import SessionViewModel
from freebci.core.models import SessionState


class FakeController:
    def __init__(self):
        self.markers = []
        self.writer = None

    def snapshot(self):
        return SimpleNamespace(
            state=SessionState.RECORDING,
            session_id="session-1",
            elapsed_seconds=2.0,
            sample_count=500,
            blocks=2,
            lost_samples=0,
            display_dropped_samples=0,
            seconds_since_block=0.1,
            markers=1,
            output_path=r"C:\logs\Recordings\Stream_1",
            error="",
        )

    def add_marker(self, label, source="api"):
        marker = {"label": label, "source": source, "sample_index": 500}
        self.markers.append(marker)
        return marker


class SessionViewModelTests(unittest.TestCase):
    def setUp(self):
        self.controller = None
        self.view_model = SessionViewModel(
            lambda: self.controller,
            lambda: r"C:\logs",
            lambda: "127.0.0.1:1234",
            lambda: "none configured",
        )

    def test_idle_diagnostics_use_the_configured_root(self):
        fields = self.view_model.diagnostics()
        self.assertEqual(fields["state"], "idle")
        self.assertEqual(fields["output"], r"C:\logs")
        self.assertEqual(fields["lsl"], "none configured")

    def test_active_diagnostics_use_the_controller_snapshot(self):
        self.controller = FakeController()
        fields = self.view_model.diagnostics()
        self.assertEqual(fields["state"], "recording")
        self.assertEqual(fields["samples"], "500")
        self.assertEqual(fields["session"], "session-1")

    def test_marker_is_delegated_and_requires_a_session(self):
        with self.assertRaises(RuntimeError):
            self.view_model.add_marker("manual")
        self.controller = FakeController()
        marker = self.view_model.add_marker("manual")
        self.assertEqual(marker["sample_index"], 500)
        self.assertEqual(self.controller.markers[0]["source"], "gui")

    def test_history_is_bounded_by_the_view_model(self):
        self.view_model.append_block(np.array([[99, 1, 2]]))
        self.assertEqual(self.view_model.history.tolist(), [[1, 2]])
        self.view_model.append_block(np.array([[99, 3, 4]]), limit=4)
        self.assertEqual(self.view_model.history.tolist(), [[2, 99, 3, 4]])


if __name__ == "__main__":
    unittest.main()
