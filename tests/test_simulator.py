import unittest

import numpy as np

from freebci.core.simulator import SimulatedBoard


class SimulatedBoardTest(unittest.TestCase):
    def test_produces_brainflow_shaped_frames(self):
        board = SimulatedBoard(channels=16, sampling_rate=250)
        self.assertEqual(board.get_num_rows(2037), 26)
        self.assertEqual(board.get_board_data_count(), 0)
        board.start_stream()
        count = board.get_board_data_count()
        self.assertGreater(count, 0)
        data = board.get_board_data()
        self.assertEqual(data.shape, (26, count))
        self.assertTrue(np.all(data[1:17, :] != 0))
        self.assertEqual(data[17, 0], 1.0)
        board.stop_stream()

    def test_advances_eeg_samples_and_packet_counter(self):
        board = SimulatedBoard(channels=8, sampling_rate=250)
        board.start_stream()
        first = board.get_board_data()
        second = board.get_board_data()
        self.assertEqual(first.shape, (18, 2))
        self.assertEqual(second.shape, (18, 2))
        self.assertFalse(np.array_equal(first[1, :], second[1, :]))
        self.assertEqual(int(second[0, 0]), 1)
        board.stop_stream()
        self.assertEqual(board.get_board_data().shape, (18, 0))


if __name__ == "__main__":
    unittest.main()
