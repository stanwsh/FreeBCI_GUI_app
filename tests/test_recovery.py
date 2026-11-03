import json
import os
import shutil
import time
import unittest

from freebci.core.recording import recover_sessions

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_ROOT = os.path.join(REPO, ".test-tmp")


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        os.makedirs(TMP_ROOT, exist_ok=True)
        self.root = os.path.join(TMP_ROOT, "recover-%d" % time.time_ns())
        self.sessions = os.path.join(self.root, "Recordings")
        os.makedirs(self.sessions)
        self.finished = os.path.join(self.sessions, "Stream_finished")
        self.unfinished = os.path.join(self.sessions, "Stream_unfinished")
        os.makedirs(self.finished)
        os.makedirs(self.unfinished)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, directory, name, payload):
        with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
            if isinstance(payload, str):
                handle.write(payload)
            else:
                json.dump(payload, handle)

    def test_only_sessions_with_writing_marker_are_reported(self):
        self._write(self.finished, "manifest.json", {"session_id": "done", "status": "completed"})
        self._write(self.unfinished, "manifest.json", {"session_id": "open", "status": "recording", "samples_recorded": 42})
        open(os.path.join(self.unfinished, ".writing"), "w").close()
        found = recover_sessions(self.root)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["session_id"], "open")
        self.assertEqual(found[0]["samples_recorded"], 42)
        self.assertEqual(found[0]["status"], "recording")

    def test_corrupt_manifest_still_reports_the_session(self):
        open(os.path.join(self.unfinished, ".writing"), "w").close()
        self._write(self.unfinished, "manifest.json", "{not json")
        found = recover_sessions(self.root)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["status"], "unknown")
        self.assertEqual(found[0]["manifest"], {})

    def test_missing_recordings_directory_is_empty(self):
        self.assertEqual(recover_sessions(os.path.join(self.root, "missing")), [])


if __name__ == "__main__":
    unittest.main()
