import json
import os
import shutil
import time
import unittest

from freebci.core.device import DeviceManager
from freebci.core.models import BoardProfile, SessionConfig, SessionStatus
from freebci.core.session import SessionController
from freebci.core.simulator import SimulatedBoard

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".test-tmp")


class ReconnectTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_ROOT, exist_ok=True)
        self.root = os.path.join(TEST_ROOT, "reconnect-%d" % time.time_ns())
        os.makedirs(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _run_once(self, manager, label):
        profile = BoardProfile(2037, "ReconnectBoard", 8, 250)
        config = SessionConfig(
            session_id=label,
            board=profile,
            sampling_rate=250,
            output_root=self.root,
            channel_count=8,
        )
        controller = SessionController(config, manager.gateway(), display_queue_blocks=16)
        controller.start()
        deadline = time.time() + 5
        while controller.snapshot().sample_count < 20 and time.time() < deadline:
            time.sleep(0.01)
        status = controller.stop()
        self.assertEqual(status, SessionStatus.COMPLETED)
        with open(os.path.join(controller.output_path, "manifest.json"), encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["status"], "completed")

    def test_release_and_reconnect_starts_a_fresh_session(self):
        manager = DeviceManager()
        first = SimulatedBoard(8, 250)
        manager.adopt(first, BoardProfile(2037, "ReconnectBoard", 8, 250))
        self._run_once(manager, "first")
        self.assertTrue(manager.release())
        self.assertFalse(manager.connected)
        second = SimulatedBoard(8, 250)
        manager.adopt(second, BoardProfile(2037, "ReconnectBoard", 8, 250))
        self._run_once(manager, "second")
        manager.release()


if __name__ == "__main__":
    unittest.main()
