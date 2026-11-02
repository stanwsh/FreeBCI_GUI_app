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
            self.assertGreater(status["elapsed_seconds"], 0.0)
            self.assertGreaterEqual(status["seconds_since_block"], 0.0)
            self.assertGreater(status["last_block_wall_ns"], 0)
            self.assertGreater(status["last_sample_time_ns"], 0)
            self.assertEqual(client.stop(), "completed")
            self.assertEqual(controller.snapshot().state.value, "finalized")
        finally:
            server.stop()

    def test_stop_callback_defers_to_owner(self):
        controller = self._controller()
        controller.start()
        called = []
        server = ControlServer(
            controller,
            token="test-token",
            stop_callback=lambda: called.append(True),
        )
        server.start()
        try:
            client = ControlClient(server.host, server.port, "test-token")
            self.assertEqual(client.stop(), "stop_requested")
            self.assertEqual(called, [True])
            self.assertNotEqual(controller.snapshot().state.value, "finalized")
        finally:
            server.stop()
            controller.stop()

    def test_marker_and_discovery_file(self):
        controller = self._controller()
        controller.start()
        server = ControlServer(controller, token="test-token")
        server.start()
        discovery = os.path.join(self.root, "control.json")
        try:
            server.write_discovery(discovery)
            client = ControlClient.from_discovery(discovery)
            self.assertTrue(client.ping())
            self.assertEqual(client.status()["markers"], 0)
            marker = client.marker("event")
            self.assertEqual(marker["label"], "event")
            self.assertEqual(marker["source"], "control")
            self.assertEqual(client.status()["markers"], 1)
            self.assertEqual(controller.snapshot().markers, 1)
        finally:
            controller.stop()
            server.stop()
            ControlServer.remove_discovery(discovery)
        self.assertFalse(os.path.exists(discovery))
        with self.assertRaises(ControlError):
            ControlClient.from_discovery(discovery)

    def test_shutdown_callback_defers_to_owner(self):
        controller = self._controller()
        controller.start()
        called = []
        server = ControlServer(
            controller,
            token="test-token",
            shutdown_callback=lambda: called.append(True),
        )
        server.start()
        try:
            client = ControlClient(server.host, server.port, "test-token")
            self.assertEqual(client.shutdown(), "shutdown_requested")
            self.assertEqual(called, [True])
        finally:
            controller.stop()
            server.stop()

    def test_shutdown_without_callback_is_rejected(self):
        controller = self._controller()
        controller.start()
        server = ControlServer(controller, token="test-token")
        server.start()
        try:
            client = ControlClient(server.host, server.port, "test-token")
            with self.assertRaises(ControlError):
                client.shutdown()
        finally:
            controller.stop()
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

    def test_idle_server_can_request_a_start(self):
        called = []
        server = ControlServer(
            None,
            token="test-token",
            start_callback=lambda: called.append(True),
        )
        server.start()
        try:
            client = ControlClient(server.host, server.port, "test-token")
            idle = client.status()
            self.assertEqual(idle["state"], "idle")
            self.assertEqual(idle["sample_count"], 0)
            self.assertEqual(client.start(), "start_requested")
            self.assertEqual(called, [True])
            with self.assertRaises(ControlError):
                client.marker("not yet")
            with self.assertRaises(ControlError):
                client.stop()
        finally:
            server.stop()

    def test_controller_provider_tracks_the_active_session(self):
        state = {"controller": None}
        server = ControlServer(
            None,
            token="test-token",
            controller_provider=lambda: state["controller"],
        )
        server.start()
        controller = self._controller()
        controller.start()
        state["controller"] = controller
        try:
            client = ControlClient(server.host, server.port, "test-token")
            deadline = time.time() + 5
            while controller.stats.samples < 3000 and time.time() < deadline:
                time.sleep(0.01)
            status = client.status()
            self.assertIn(status["state"], ("recording", "stopping", "finalized"))
            self.assertEqual(status["channel_count"], 4)
            self.assertEqual(client.marker("from control")["label"], "from control")
        finally:
            state["controller"] = None
            controller.stop()
            server.stop()


if __name__ == "__main__":
    unittest.main()
