import os
import shutil
import time
import unittest

from freebci.core.control import ControlClient, ControlError, ControlServer
from freebci.core.models import BoardProfile, SessionConfig
from freebci.core.session import SessionController
from tests.test_core import FakeGateway, TEST_ROOT


class ControlPlaneTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_ROOT, exist_ok=True)
        self.root = os.path.join(TEST_ROOT, "control-%d" % time.time_ns())
        os.makedirs(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _controller(self, samples=3000):
        profile = BoardProfile(board_id=999, name="FakeBoard", channels=4, sampling_rate=250)
        config = SessionConfig(
            session_id="control-test",
            board=profile,
            sampling_rate=250,
            output_root=self.root,
            channel_count=4,
        )
        return SessionController(config, FakeGateway(samples=samples, chunk=500))

    def test_status_and_stop_over_loopback(self):
        controller = self._controller()
        controller.start()
        server = ControlServer(controller, token="test-token")
        server.start()
        client = ControlClient(server.host, server.port, "test-token")
        try:
            self.assertTrue(client.ping())
            deadline = time.time() + 5
            while controller.stats.samples < 3000 and time.time() < deadline:
                time.sleep(0.01)
            status = client.status()
            self.assertIn(status["state"], ("recording", "stopping", "finalized"))
            self.assertEqual(status["channel_count"], 4)
            self.assertEqual(status["sample_count"], 3000)
            self.assertEqual(client.stop(), "completed")
            self.assertEqual(controller.snapshot().state.value, "finalized")
        finally:
            server.stop()

    def test_wrong_token_is_rejected(self):
        controller = self._controller()
        controller.start()
        server = ControlServer(controller, token="right-token")
        server.start()
        try:
            with self.assertRaises(ControlError):
                ControlClient(server.host, server.port, "wrong-token").status()
        finally:
            controller.stop()
            server.stop()

    def test_server_stop_is_idempotent(self):
        controller = self._controller()
        server = ControlServer(controller, token="test-token")
        server.start()
        server.stop()
        server.stop()
        self.assertFalse(server.running)


if __name__ == "__main__":
    unittest.main()
