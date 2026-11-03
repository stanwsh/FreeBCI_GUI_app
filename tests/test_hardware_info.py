"""Regression checks for refreshing MNE metadata from hardware settings."""
import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np

from freebci.ui.main_window import MainWindow


class HardwareInfoTest(unittest.TestCase):
    def _window(self, sampling_rate=250):
        return SimpleNamespace(
            channels=np.array(["Fp1", "Fp2"]),
            SamplingRate=sampling_rate,
            ts_time=5,
            networking=SimpleNamespace(refreshSamplingRate=lambda rate: None),
        )

    def test_make_info_uses_the_current_sampling_rate(self):
        window = self._window(250)
        self.assertEqual(MainWindow._make_info(window)["sfreq"], 250)
        window.SamplingRate = 500
        info = MainWindow._make_info(window)
        self.assertEqual(info["sfreq"], 500)
        self.assertEqual(info["ch_names"], ["Fp1", "Fp2"])

    def test_get_hardware_info_rebuilds_info_instead_of_setting_sfreq(self):
        window = self._window()
        window._make_info = lambda: MainWindow._make_info(window)
        MainWindow.getHardwareInfo(
            window,
            SimpleNamespace(
                chanMatched_index=[0, 1],
                baudRate="2000000",
                SamplingRate=500,
            ),
        )
        self.assertEqual(window.info["sfreq"], 500)
        self.assertEqual(window.ts_plot_range, 2500)


if __name__ == "__main__":
    unittest.main()
