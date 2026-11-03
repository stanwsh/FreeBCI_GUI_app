import json
import os
import shutil
import time
import unittest

import numpy as np

from freebci.core.models import BoardProfile, SampleBlock, SessionConfig, SessionStatus
from freebci.core.recording import RecordingWriter
from freebci.core.session import SessionController

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".test-tmp")


class FakeGateway:
    """Deterministic stand-in for a prepared board."""

    board_id = 999
    channel_count = 4

    def __init__(self, samples=12_000, chunk=2_500):
        self.samples = samples
        self.chunk = chunk
        self.remaining = samples
        self.packet = 0
        self.started = False

    def start_stream(self):
        self.started = True

    def stop_stream(self):
        self.started = False

    def get_data_count(self):
        return min(self.chunk, self.remaining)

    def read(self):
        count = min(self.chunk, self.remaining)
        self.remaining -= count
        data = np.zeros((1 + self.channel_count + 3, count), dtype=np.float64)
        data[0, :] = self.packet
        self.packet = (self.packet + count) % 256
        for channel in range(self.channel_count):
            data[1 + channel, :] = channel + 1
        data[1 + self.channel_count :, :] = 7
        return data

    def release(self):
        pass


class SessionControllerTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_ROOT, exist_ok=True)
        self.root = os.path.join(TEST_ROOT, "run-%d" % time.time_ns())
        os.makedirs(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_records_complete_session_with_manifest(self):
        profile = BoardProfile(board_id=999, name="FakeBoard", channels=4, sampling_rate=250)
        config = SessionConfig(
            session_id="test-session",
            board=profile,
            sampling_rate=250,
            output_root=self.root,
            channel_count=4,
        )
        gateway = FakeGateway()
        seen_markers = []
        controller = SessionController(config, gateway, marker_callback=seen_markers.append)
        controller.start()
        deadline = time.time() + 5
        while controller.stats.samples < 12_000 and time.time() < deadline:
            time.sleep(0.01)
        marker = controller.add_marker("stimulus on", source="test")
        self.assertEqual(marker["label"], "stimulus on")
        self.assertEqual(controller.snapshot().markers, 1)
        self.assertEqual(seen_markers[0]["label"], "stimulus on")
        status = controller.stop()
        self.assertEqual(status, SessionStatus.COMPLETED)
        snapshot = controller.snapshot()
        self.assertEqual(snapshot.sample_count, 12_000)
        self.assertGreaterEqual(snapshot.seconds_since_block, 0.0)

        session_dir = controller.output_path
        self.assertTrue(os.path.isdir(session_dir))
        manifest_path = os.path.join(session_dir, "manifest.json")
        self.assertTrue(os.path.isfile(manifest_path))
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["status"], "completed")
        self.assertEqual(manifest["samples_recorded"], 12_000)
        self.assertEqual(manifest["clock"]["timebase"], "host-wall")
        self.assertGreater(manifest["clock"]["started_wall_ns"], 0)
        self.assertGreater(manifest["clock"]["stopped_wall_ns"], 0)
        self.assertEqual(manifest["channel_count"], 4)
        self.assertEqual(len(manifest["files"]), 1)
        self.assertEqual(manifest["files"][0]["samples"], 12_000)
        self.assertTrue(manifest["files"][0]["sha256"])
        self.assertEqual(len(manifest["markers"]), 1)
        self.assertEqual(manifest["markers"][0]["label"], "stimulus on")
        self.assertEqual(manifest["markers"][0]["source"], "test")
        markers_path = os.path.join(session_dir, "markers.jsonl")
        with open(markers_path, encoding="utf-8") as handle:
            marker_lines = handle.readlines()
        self.assertEqual(len(marker_lines), 1)
        self.assertEqual(json.loads(marker_lines[0])["label"], "stimulus on")

        first_csv = os.path.join(session_dir, "1.csv")
        with open(first_csv, encoding="utf-8") as handle:
            lines = handle.readlines()
        self.assertEqual(len(lines), 12_001)
        self.assertTrue(lines[0].startswith("channel1,channel2,channel3,channel4,<AUX 0>"))
        first_row = lines[1].rstrip("\r\n").split(",")
        self.assertEqual(first_row[0], "1.000000")
        self.assertEqual(first_row[-1], "7")

    def test_rotates_csv_after_nine_chunks(self):
        profile = BoardProfile(board_id=999, name="FakeBoard", channels=4, sampling_rate=250)
        config = SessionConfig(
            session_id="test-rotation",
            board=profile,
            sampling_rate=250,
            output_root=self.root,
            channel_count=4,
        )
        controller = SessionController(config, FakeGateway(samples=95_000, chunk=2_500))
        controller.start()
        deadline = time.time() + 10
        while controller.stats.samples < 95_000 and time.time() < deadline:
            time.sleep(0.01)
        status = controller.stop()
        self.assertEqual(status, SessionStatus.COMPLETED)

        session_dir = controller.output_path
        with open(os.path.join(session_dir, "manifest.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(len(manifest["files"]), 2)
        self.assertEqual(manifest["files"][0]["samples"], 90_000)
        self.assertEqual(manifest["files"][1]["samples"], 5_000)
        self.assertEqual(manifest["samples_recorded"], 95_000)
        with open(os.path.join(session_dir, "1.csv"), encoding="utf-8") as handle:
            self.assertEqual(len(handle.readlines()), 90_001)
        with open(os.path.join(session_dir, "2.csv"), encoding="utf-8") as handle:
            self.assertEqual(len(handle.readlines()), 5_001)

    def test_stop_is_idempotent_and_leaves_finalized_state(self):
        profile = BoardProfile(board_id=999, name="FakeBoard", channels=4, sampling_rate=250)
        config = SessionConfig(
            session_id="test-session-2",
            board=profile,
            sampling_rate=250,
            output_root=self.root,
            channel_count=4,
        )
        controller = SessionController(config, FakeGateway(samples=500, chunk=500))
        controller.start()
        controller.stop()
        second = controller.stop()
        self.assertEqual(second, SessionStatus.COMPLETED)
        self.assertEqual(controller.snapshot().state.value, "finalized")

    def test_manifest_reports_missing_samples(self):
        profile = BoardProfile(board_id=999, name="FakeBoard", channels=4, sampling_rate=250)
        config = SessionConfig(
            session_id="test-gap",
            board=profile,
            sampling_rate=250,
            output_root=self.root,
            channel_count=4,
        )
        writer = RecordingWriter(config)
        writer.start()
        with open(os.path.join(writer.session_dir, "manifest.json"), encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["status"], "recording")
        now = time.time_ns()
        data = np.zeros((8, 10), dtype=np.float64)
        data[1:5, :] = 1
        data[5:, :] = 7
        writer.submit(SampleBlock(0, 0, data, 250, now, now, now))
        writer.submit(SampleBlock(1, 20, data, 250, now, now, now))
        writer.close()
        with open(os.path.join(writer.session_dir, "manifest.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["samples_recorded"], 20)
        self.assertEqual(manifest["lost_samples"], 10)
        self.assertEqual(manifest["gaps"][0]["start_sample"], 10)
        self.assertEqual(manifest["gaps"][0]["end_sample"], 20)


if __name__ == "__main__":
    unittest.main()
