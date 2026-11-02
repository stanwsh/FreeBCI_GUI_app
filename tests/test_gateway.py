import unittest

from freebci.core.gateway import BrainFlowGateway, GatewayError


class FakeBoard:
    def __init__(self, fail_config=False):
        self.calls = []
        self.fail_config = fail_config

    def start_stream(self):
        self.calls.append(("start_stream",))

    def config_board(self, command):
        self.calls.append(("config_board", command))
        if self.fail_config:
            raise RuntimeError("command rejected")

    def stop_stream(self):
        self.calls.append(("stop_stream",))

    def get_board_data_count(self):
        return 0

    def get_board_data(self):
        return []

    def release_session(self):
        self.calls.append(("release_session",))


class BrainFlowGatewayTest(unittest.TestCase):
    def test_applies_post_start_configuration_in_order(self):
        board = FakeBoard()
        gateway = BrainFlowGateway(
            board,
            board_id=2038,
            channel_count=16,
            post_start_config=(chr(34) + ',',),
        )
        gateway.start_stream()
        self.assertEqual(
            board.calls,
            [("start_stream",), ("config_board", chr(34) + ',')],
        )

    def test_failed_start_configuration_stops_the_stream(self):
        board = FakeBoard(fail_config=True)
        gateway = BrainFlowGateway(
            board,
            board_id=2038,
            channel_count=16,
            post_start_config=(chr(34) + ',',),
        )
        with self.assertRaises(GatewayError):
            gateway.start_stream()
        self.assertEqual(
            board.calls,
            [("start_stream",), ("config_board", chr(34) + ','), ("stop_stream",)],
        )


if __name__ == "__main__":
    unittest.main()
