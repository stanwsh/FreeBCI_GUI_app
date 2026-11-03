import unittest

from freebci.core.actions import action_availability


class ActionAvailabilityTest(unittest.TestCase):
    def test_idle_connected_window_allows_editing_and_release(self):
        actions = action_availability("idle", connected=True)
        self.assertTrue(actions.demo)
        self.assertTrue(actions.boards)
        self.assertTrue(actions.release)
        self.assertTrue(actions.hardware)
        self.assertTrue(actions.channels)
        self.assertFalse(actions.marker)

    def test_recording_only_allows_markers(self):
        actions = action_availability("recording", connected=True)
        self.assertTrue(actions.marker)
        self.assertFalse(actions.demo)
        self.assertFalse(actions.boards)
        self.assertFalse(actions.hardware)
        self.assertFalse(actions.channels)
        self.assertTrue(actions.release)

    def test_starting_blocks_editing_and_release(self):
        actions = action_availability("idle", starting=True, connected=True)
        self.assertFalse(actions.demo)
        self.assertFalse(actions.boards)
        self.assertFalse(actions.release)
        self.assertFalse(actions.hardware)

    def test_disconnected_window_cannot_release(self):
        actions = action_availability("idle", connected=False)
        self.assertFalse(actions.release)


if __name__ == "__main__":
    unittest.main()
