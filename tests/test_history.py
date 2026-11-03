import unittest

import numpy as np

from freebci.core.history import append_bounded


class BoundedHistoryTests(unittest.TestCase):
    def test_appends_without_trimming_below_the_limit(self):
        history = np.array([[1, 2, 3]])
        result = append_bounded(history, np.array([[4, 5]]), 10)
        self.assertEqual(result.tolist(), [[1, 2, 3, 4, 5]])

    def test_keeps_only_the_newest_columns(self):
        history = np.array([[1, 2, 3, 4]])
        result = append_bounded(history, np.array([[5, 6, 7]]), 5)
        self.assertEqual(result.tolist(), [[3, 4, 5, 6, 7]])

    def test_a_block_larger_than_the_limit_keeps_its_tail(self):
        result = append_bounded(np.zeros((1, 2)), np.arange(10).reshape(1, 10), 4)
        self.assertEqual(result.tolist(), [[6, 7, 8, 9]])

    def test_rejects_a_non_positive_limit(self):
        with self.assertRaises(ValueError):
            append_bounded(np.zeros((1, 1)), np.zeros((1, 1)), 0)


if __name__ == "__main__":
    unittest.main()
