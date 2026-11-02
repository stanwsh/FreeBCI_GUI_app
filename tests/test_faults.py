import json
import os
import shutil
import time
import unittest
from unittest.mock import Mock

import numpy as np

from freebci.core.models import (
    BoardProfile,
    SampleBlock,
    SessionConfig,
    SessionState,
    SessionStatus,
)
from freebci.core.recording import RecordingWriter
from freebci.core.session import SessionController

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".test-tmp")


class FailingReadGateway:
    board_id = 998
    channel_count = 4

    def __init__(self):
        self.reads = 0

    def start_stream(self):
        pass

    def stop_stream(self):
        pass

    def get_data_count(self):
        return 250

    def read(self):
        self.reads += 1
        if self.reads > 2:
            raise RuntimeError("USB device disappeared")
        data = np.zeros((8, 250), dtype=np.float64)
        data[1:5, :] = 1
        return data

    def release(self):
        pass


class FailingStartGateway(FailingReadGateway):
    def start_stream(self):
        raise RuntimeError("board did not start")


class FaultHandlingTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_ROOT, exist_ok=True)
        self.root = os.path.join(TEST_ROOT, "fault-%d" % time.time_ns())
        os.makedirs(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _config(self, name):
        profile = BoardProfile(board_id=998, name="FaultBoard", channels=4, sampling_rate=250)
        return SessionConfig(
            session_id=name,
            board=profile,
            sampling_rate=250,
            output_root=self.root,
            channel_count=4,
        )

    def test_acquisition_failure_is_reported_and_partial(self):
        controller = SessionController(self._config("fault-read"), FailingReadGateway())
        controller.start()
        deadline = time.time() + 5
        while not controller.check_health() and time.time() < deadline:
            time.sleep(0.01)
        self.assertIn("USB device disappeared", controller.check_health())
        status = controller.stop()
        self.assertEqual(status, SessionStatus.PARTIAL)
        with open(os.path.join(controller.output_path, "manifest.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["status"], "partial")

    def test_start_failure_leaves_a_failed_manifest(self):
        controller = SessionController(self._config("fault-start"), FailingStartGateway())
        with self.assertRaises(RuntimeError):
            controller.start()
        self.assertEqual(controller.snapshot().state, SessionState.FAILED)
        with open(os.path.join(controller.output_path, "manifest.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["status"], "failed")


    def test_disk_full_during_flush_still_finalizes_failed_manifest(self):
        config = self._config("disk-full")
        writer = RecordingWriter(config, queue_blocks=8)
        writer.start()
        now = time.time_ns()
        data = np.zeros((1 + 4 + 3, 500), dtype=np.float64)
        block = SampleBlock(
            sequence=0,
            sample_index=0,
            data=data,
            sampling_rate=250,
            host_time_ns=now,
            monotonic_ns=time.perf_counter_ns(),
            first_sample_time_ns=now,
        )
        writer.submit(block)
        writer._write_chunk = Mock(side_effect=OSError("No space left on device"))
        writer.close(SessionStatus.COMPLETED)
        with open(os.path.join(writer.session_dir, "manifest.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["status"], "failed")
        self.assertIn("No space left on device", " ".join(manifest["errors"]))


if __name__ == "__main__":
    unittest.main()
