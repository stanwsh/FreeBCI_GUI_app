import unittest

import numpy as np

from freebci.core.lsl_queue import LslSampleQueue


class LslQueueTests(unittest.TestCase):
    def test_pushes_and_drains_in_order(self):
        queue = LslSampleQueue(max_samples=10)
        queue.push([[1, 2], [3, 4]])
        queue.push(np.array([[5, 6]]))
        drained = queue.drain()
        np.testing.assert_array_equal(drained, [[1, 2], [3, 4], [5, 6]])
        self.assertIsNone(queue.drain())
        self.assertEqual(queue.pending, 0)

    def test_drops_oldest_rows_and_counts_them(self):
        queue = LslSampleQueue(max_samples=3)
        queue.push([[1], [2]])
        queue.push([[3], [4], [5]])
        self.assertEqual(queue.pending, 3)
        self.assertEqual(queue.dropped, 2)
        np.testing.assert_array_equal(queue.drain(), [[3], [4], [5]])

    def test_single_oversized_block_is_trimmed(self):
        queue = LslSampleQueue(max_samples=2)
        queue.push([[1], [2], [3], [4]])
        self.assertEqual(queue.received, 4)
        self.assertEqual(queue.dropped, 2)
        np.testing.assert_array_equal(queue.drain(), [[3], [4]])

    def test_clear_drops_pending_without_counting_a_fault(self):
        queue = LslSampleQueue(max_samples=4)
        queue.push([[1], [2]])
        queue.clear()
        self.assertEqual(queue.pending, 0)
        self.assertEqual(queue.dropped, 0)
        queue.push([[3]])
        np.testing.assert_array_equal(queue.drain(), [[3]])


if __name__ == "__main__":
    unittest.main()
