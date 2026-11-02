import json
import os
import shutil
import time
import unittest

import numpy as np

from freebci.core.models import BoardProfile, SessionConfig, SessionState, SessionStatus
from freebci.core.session import SessionController

TEST_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".test-tmp")


class SmallGateway:
    board_id = 997
    channel_count = 4

    def __init__(self, samples=40):
        self.samples = samples
        self.reads = 0

    def start_stream(self):
        pass

    def stop_stream(self):
        pass

    def get_data_count(self):
        return self.samples if self.reads == 0 else 0

    def read(self):
        self.reads += 1
        data = np.zeros((1 + 4 + 3, self.samples), dtype=np.float64)
        data[1:5, :] = 1.0
        return data

    def release(self):
        pass


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_ROOT, exist_ok=True)
        self.root = os.path.join(TEST_ROOT, "lifecycle-%d" % time.time_ns())
        os.makedirs(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_one_hundred_sessions_finalize_cleanly(self):
        for index in range(100):
            profile = BoardProfile(board_id=997, name="CycleBoard", channels=4, sampling_rate=250)
            config = SessionConfig(
                session_id="cycle-%03d" % index,
                board=profile,
                sampling_rate=250,
                output_root=self.root,
                channel_count=4,
            )
            controller = SessionController(config, SmallGateway(), display_queue_blocks=8)
            controller.start()
            deadline = time.time() + 2
            while controller.snapshot().sample_count < 40 and time.time() < deadline:
                time.sleep(0.005)
            status = controller.stop()
            self.assertEqual(status, SessionStatus.COMPLETED)
            self.assertEqual(controller.snapshot().state, SessionState.FINALIZED)
            self.assertEqual(controller.snapshot().sample_count, 40)
            with open(os.path.join(controller.output_path, "manifest.json"), encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["status"], "completed")


if __name__ == "__main__":
    unittest.main()
