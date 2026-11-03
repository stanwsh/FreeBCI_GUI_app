import argparse
import json
import os
import shutil
import time
import unittest
from pathlib import Path
from unittest import mock

from examples import control_client, lsl_receive, raw_control
from freebci.core import ControlServer
from tests.test_core import TEST_ROOT


class ExampleTests(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_ROOT, exist_ok=True)
        self.root = os.path.join(TEST_ROOT, "examples-%d" % time.time_ns())
        os.makedirs(self.root)
        self.discovery = os.path.join(self.root, "control.json")
        with open(self.discovery, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema": "freebci.control/1",
                    "protocol": 1,
                    "host": "127.0.0.1",
                    "address": "tcp://127.0.0.1:5555",
                    "port": 5555,
                    "token": "test-token",
                },
                handle,
            )

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_control_discovery_uses_explicit_path(self):
        self.assertEqual(
            control_client.resolve_discovery(self.discovery),
            Path(self.discovery),
        )

    def test_control_discovery_uses_environment(self):
        with mock.patch.dict(
            os.environ,
            {"FREEBCI_CONTROL_FILE": self.discovery, "FREEBCI_HOME": self.root},
            clear=False,
        ):
            self.assertEqual(control_client.resolve_discovery(), Path(self.discovery))

    def test_control_parser_accepts_demo_options(self):
        args = control_client.build_parser().parse_args(
            ["demo", "--duration", "2.5", "--marker", "baseline"]
        )
        self.assertEqual(args.command, "demo")
        self.assertEqual(args.duration, 2.5)
        self.assertEqual(args.marker, "baseline")

    def test_raw_endpoint_from_discovery(self):
        args = argparse.Namespace(
            discovery=self.discovery,
            host=None,
            port=None,
            token=None,
        )
        self.assertEqual(
            raw_control.resolve_endpoint(args),
            ("127.0.0.1", 5555, "test-token"),
        )

    def test_lsl_marker_drain_keeps_labels_and_timestamps(self):
        class FakeInlet:
            def pull_chunk(self, timeout=0.0, max_samples=64):
                return [["baseline"], ["stimulus"]], [10.0, 11.5]

        self.assertEqual(
            lsl_receive.drain_markers(FakeInlet()),
            [("baseline", 10.0), ("stimulus", 11.5)],
        )

    def test_raw_client_matches_control_server(self):
        server = ControlServer(token="test-token")
        server.start()
        try:
            client = raw_control.RawControlClient(server.host, server.port, "test-token")
            ping = client.request("ping")
            self.assertTrue(ping["ok"])
            self.assertEqual(ping["id"], 1)
            status = client.request("status")
            self.assertEqual(status["snapshot"]["state"], "idle")
            with self.assertRaises(raw_control.RawControlError) as raised:
                client.request("marker", label="no session")
            self.assertEqual(raised.exception.code, "no_session")
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()

