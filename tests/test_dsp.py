import unittest

import numpy as np

from freebci.core.dsp import bandpass_inplace, bandstop_inplace, fft_magnitude


class DspTests(unittest.TestCase):
    def setUp(self):
        self.data = np.sin(np.linspace(0, 20 * np.pi, 512)) * 10.0
        self.fs = 250

    def test_bandpass_keeps_shape_and_is_finite(self):
        result = bandpass_inplace(self.data.copy(), self.fs, 5.0, 50.0)
        self.assertEqual(result.shape, self.data.shape)
        self.assertTrue(np.isfinite(result).all())

    def test_bandstop_keeps_shape_and_is_finite(self):
        result = bandstop_inplace(self.data.copy(), self.fs, 50.0)
        self.assertEqual(result.shape, self.data.shape)
        self.assertTrue(np.isfinite(result).all())

    def test_fft_returns_expected_half_spectrum(self):
        values = fft_magnitude(self.data, 2)
        self.assertEqual(len(values), 257)


if __name__ == "__main__":
    unittest.main()
