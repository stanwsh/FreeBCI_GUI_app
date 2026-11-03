import json
import os
import shutil
import time
import unittest

from freebci.core.logging import StructuredLogger

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_ROOT = os.path.join(REPO, ".test-tmp")


class LoggingTests(unittest.TestCase):
    def setUp(self):
        os.makedirs(TMP_ROOT, exist_ok=True)
        self.directory = os.path.join(TMP_ROOT, "log-%d" % time.time_ns())
        os.makedirs(self.directory)
        self.path = os.path.join(self.directory, "session.log")

    def tearDown(self):
        shutil.rmtree(self.directory, ignore_errors=True)

    def _records(self, path):
        with open(path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def test_writes_structured_records_and_fields(self):
        logger = StructuredLogger(self.path)
        logger.log("info", "recording.started", "started", session_id="abc", count=2)
        logger.log("warning", "recording.gap", "gap", missing=3)
        logger.close()
        records = self._records(self.path)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["event"], "recording.started")
        self.assertEqual(records[0]["session_id"], "abc")
        self.assertEqual(records[0]["count"], 2)
        self.assertEqual(records[1]["level"], "warning")
        self.assertGreater(records[0]["time_ns"], 0)

    def test_rotates_without_losing_the_new_record(self):
        logger = StructuredLogger(self.path, max_bytes=300, backups=1)
        for index in range(20):
            logger.log("info", "event.%d" % index, "x" * 40)
        logger.close()
        self.assertTrue(os.path.exists(self.path + ".1"))
        latest = self._records(self.path)
        self.assertEqual(latest[-1]["event"], "event.19")

    def test_closed_logger_rejects_writes(self):
        logger = StructuredLogger(self.path)
        logger.close()
        with self.assertRaises(RuntimeError):
            logger.log("info", "late", "late")


if __name__ == "__main__":
    unittest.main()
