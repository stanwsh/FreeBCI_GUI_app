import unittest

from freebci.core.packets import PacketLossCounter


class PacketLossCounterTest(unittest.TestCase):
    def test_repeated_values_are_one_frame(self):
        counter = PacketLossCounter()
        counter.add([5, 5, 5, 5])
        counter.add([5, 5, 5, 5])
        counter.add([6, 6, 6, 6])
        self.assertEqual(counter.received, 2)
        self.assertEqual(counter.lost, 0)
        self.assertEqual(counter.percent, 0.0)

    def test_reports_missing_frames_and_handles_wrap(self):
        counter = PacketLossCounter()
        counter.add([254, 254, 255, 255])
        counter.add([1, 1, 2, 2])
        self.assertEqual(counter.received, 4)
        self.assertEqual(counter.lost, 1)
        self.assertAlmostEqual(counter.percent, 20.0)

    def test_reset_starts_a_new_session(self):
        counter = PacketLossCounter()
        counter.add([5, 5])
        counter.reset()
        counter.add([9, 9])
        self.assertEqual(counter.received, 1)
        self.assertEqual(counter.lost, 0)


if __name__ == "__main__":
    unittest.main()
