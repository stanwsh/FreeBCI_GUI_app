import json
import os
import shutil
import socket
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
            self.assertEqual(status["clock_id"], "host-monotonic")
            self.assertGreater(status["monotonic_ns"], 0)
            self.assertGreater(status["wall_ns"], 0)
            self.assertEqual(client.stop(), "completed")
            self.assertEqual(controller.snapshot().state.value, "finalized")
        finally:
            server.stop()

    def test_request_ids_and_error_codes_are_preserved(self):
        server = ControlServer(token="test-token")
        server.start()
        try:
            with socket.create_connection((server.host, server.port), timeout=2) as sock:
                sock.sendall(
                    ('{"command":"ping","token":"test-token","id":41}\n').encode("utf-8")
                )
                response = json.loads(sock.makefile("rb").readline())
            self.assertEqual(response["id"], 41)
            self.assertTrue(response["ok"])
            with socket.create_connection((server.host, server.port), timeout=2) as sock:
                sock.sendall(
                    ('{"command":"marker","token":"test-token","id":42,"label":"x"}\n').encode("utf-8")
                )
                error = json.loads(sock.makefile("rb").readline())
            self.assertEqual(error["id"], 42)
            self.assertFalse(error["ok"])
            self.assertEqual(error["code"], "no_session")
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
            with open(discovery, encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["schema"], "freebci.control/1")
            self.assertEqual(payload["host"], "127.0.0.1")
            self.assertGreater(payload["pid"], 0)
            client = ControlClient.from_runtime_file(discovery)
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

    def test_clock_offset_reports_uncertainty(self):
        controller = self._controller()
        controller.start()
        server = ControlServer(controller, token="test-token")
        server.start()
        try:
            client = ControlClient(server.host, server.port, "test-token")
            result = client.clock_offset(samples=3)
            self.assertGreaterEqual(result["uncertainty_ns"], 0)
            self.assertGreaterEqual(result["round_trip_ns"], 0)
            self.assertLess(abs(result["offset_ns"]), 5_000_000_000)
            self.assertEqual(result["samples"], 3)
        finally:
            server.stop()
            controller.stop()

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
            start_callback=lambda board: called.append(board),
        )
        server.start()
        try:
            client = ControlClient(server.host, server.port, "test-token")
            idle = client.status()
            self.assertEqual(idle["state"], "idle")
            self.assertEqual(idle["sample_count"], 0)
            self.assertEqual(client.start("demo"), "start_requested")
            self.assertEqual(called, ["demo"])
            with self.assertRaises(ControlError):
                client.start("")
            with self.assertRaises(ControlError):
                client.marker("not yet")
            with self.assertRaises(ControlError):
                client.stop()
            with self.assertRaises(ControlError):
                client.wait_started(0.1)
        finally:
            server.stop()

    def test_pending_start_rejects_a_second_request(self):
        server = ControlServer(None, token="test-token", start_callback=lambda board: None)
        server.start()
        try:
            client = ControlClient(server.host, server.port, "test-token")
            self.assertEqual(client.start("demo"), "start_requested")
            with self.assertRaises(ControlError) as caught:
                client.start("demo")
            self.assertEqual(caught.exception.code, "busy")
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
