import unittest

from freebci.core.device import DeviceError, DeviceManager, DeviceState
from freebci.core.models import BoardProfile


class FakeBoard:
    def __init__(self, name):
        self.name = name
        self.released = 0

    def release_session(self):
        self.released += 1


def profile(board_id=2037):
    return BoardProfile(board_id, "FreeBCI_WiFi_16_I", 16, 250)


class DeviceManagerTests(unittest.TestCase):
    def test_adopt_ready_streaming_and_release(self):
        manager = DeviceManager()
        board = FakeBoard("one")
        manager.adopt(board, profile())
        self.assertEqual(manager.state, DeviceState.READY)
        self.assertTrue(manager.connected)
        manager.mark_streaming()
        self.assertEqual(manager.state, DeviceState.STREAMING)
        manager.mark_ready()
        self.assertEqual(manager.state, DeviceState.READY)
        self.assertTrue(manager.release())
        self.assertFalse(manager.connected)
        self.assertEqual(board.released, 1)
        self.assertEqual(manager.state, DeviceState.DISCONNECTED)
        self.assertFalse(manager.release())

    def test_replacing_a_board_releases_the_previous_one(self):
        manager = DeviceManager()
        first = FakeBoard("one")
        second = FakeBoard("two")
        manager.adopt(first, profile())
        manager.adopt(second, profile(2038))
        self.assertEqual(first.released, 1)
        self.assertIs(manager.board, second)
        self.assertEqual(manager.profile.board_id, 2038)

    def test_gateway_requires_a_board(self):
        manager = DeviceManager()
        with self.assertRaises(DeviceError):
            manager.gateway()
        with self.assertRaises(DeviceError):
            manager.mark_streaming()

    def test_gateway_uses_the_adopted_profile(self):
        manager = DeviceManager()
        manager.adopt(FakeBoard("one"), profile())
        gateway = manager.gateway(post_start_config=("x",))
        self.assertEqual(gateway.board_id, 2037)
        self.assertEqual(gateway.channel_count, 16)
        self.assertEqual(gateway.post_start_config, ("x",))


if __name__ == "__main__":
    unittest.main()
