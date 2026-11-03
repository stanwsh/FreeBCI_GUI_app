import unittest
from unittest.mock import MagicMock, patch

from freebci.core.gateway import (
    BrainFlowGateway,
    GatewayError,
    prepare_serial_board,
    prepare_wifi_board,
)


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

    def test_serial_preparation_sets_transport_parameters(self):
        board = MagicMock()
        with patch("brainflow.board_shim.BoardShim", return_value=board) as ctor:
            prepared = prepare_serial_board(2037, "COM3", "2000000", timeout=3)
        self.assertIs(prepared, board)
        board.prepare_session.assert_called_once()
        params = ctor.call_args[0][1]
        self.assertEqual(params.serial_port, "COM3")
        self.assertEqual(params.other_info, "2000000")
        self.assertEqual(params.timeout, 3.0)

    def test_wifi_preparation_sets_transport_parameters(self):
        board = MagicMock()
        with patch("brainflow.board_shim.BoardShim", return_value=board) as ctor:
            prepared = prepare_wifi_board(2038, "192.168.4.1", 8899)
        self.assertIs(prepared, board)
        board.prepare_session.assert_called_once()
        params = ctor.call_args[0][1]
        self.assertEqual(params.ip_address, "192.168.4.1")
        self.assertEqual(params.ip_port, 8899)
        self.assertEqual(params.timeout, 5.0)

    def test_preparation_failure_releases_the_board(self):
        board = MagicMock()
        board.prepare_session.side_effect = RuntimeError("no board")
        with patch("brainflow.board_shim.BoardShim", return_value=board):
            with self.assertRaises(RuntimeError):
                prepare_wifi_board(2038, "192.168.4.1", 8899)
        board.release_session.assert_called_once()


if __name__ == "__main__":
    unittest.main()
