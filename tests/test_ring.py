import unittest

import numpy as np

from freebci.core.ring import RingBuffer


class RingBufferTests(unittest.TestCase):
    def test_latest_returns_chronological_data(self):
        ring = RingBuffer(rows=2, capacity=5)
        ring.write(np.array([[1, 2, 3], [10, 20, 30]]))
        ring.write(np.array([[4, 5], [40, 50]]))
        self.assertEqual(ring.latest().tolist(), [[1, 2, 3, 4, 5], [10, 20, 30, 40, 50]])
        self.assertEqual(ring.latest(2).tolist(), [[4, 5], [40, 50]])
        self.assertEqual(ring.total_written, 5)

    def test_wrap_keeps_the_newest_window(self):
        ring = RingBuffer(rows=1, capacity=4)
        ring.write(np.array([[1, 2, 3, 4]]))
        ring.write(np.array([[5, 6]]))
        self.assertEqual(ring.latest().tolist(), [[3, 4, 5, 6]])
        self.assertEqual(ring.latest(3).tolist(), [[4, 5, 6]])

    def test_oversized_block_keeps_its_tail(self):
        ring = RingBuffer(rows=1, capacity=3)
        ring.write(np.array([[1, 2, 3, 4, 5]]))
        self.assertEqual(ring.latest().tolist(), [[3, 4, 5]])
        self.assertEqual(ring.total_written, 3)

    def test_rejects_wrong_row_count(self):
        ring = RingBuffer(rows=2, capacity=4)
        with self.assertRaises(ValueError):
            ring.write(np.zeros((1, 3)))


if __name__ == "__main__":
    unittest.main()
