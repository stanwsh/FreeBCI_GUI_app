import os
import shutil
import time
import unittest
import xml.etree.ElementTree as ET

from freebci.core.settings import (
    ChannelSettings,
    HardwareSettings,
    SettingsError,
    load_settings,
    save_settings,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_ROOT = os.path.join(REPO, ".test-tmp")


def _channel(gain="X24", input_type="Normal", bias="Yes", srb2="On", srb1="Off"):
    return ChannelSettings(gain, input_type, bias, srb2, srb1)


class SettingsTests(unittest.TestCase):
    def setUp(self):
        os.makedirs(TMP_ROOT, exist_ok=True)
        self.directory = os.path.join(TMP_ROOT, "settings-%d" % time.time_ns())
        os.makedirs(self.directory)
        self.path = os.path.join(self.directory, "settings.xml")

    def tearDown(self):
        shutil.rmtree(self.directory, ignore_errors=True)

    def test_round_trip_preserves_values_and_metadata(self):
        settings = HardwareSettings(
            channels=(_channel(), _channel(gain="X12", bias="No")),
            sampling_rate=500,
            baud_rate=2000000,
        )
        save_settings(self.path, settings)
        loaded = load_settings(self.path, expected_channels=2)
        self.assertEqual(loaded, settings)
        root = ET.parse(self.path).getroot()
        self.assertEqual(root.get("sampling_rate"), "500")
        self.assertEqual(root.get("baud_rate"), "2000000")

    def test_channel_tags_are_ordered_numerically(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("<Channels><Channel2><pca_gain>X12</pca_gain>"
                         "<input_type>Normal</input_type><bias_include>No</bias_include>"
                         "<srb2>On</srb2><srb1>Off</srb1></Channel2></Channels>")
        with self.assertRaises(SettingsError):
            load_settings(self.path, expected_channels=1)
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("<Channels><Channel1><pca_gain>X6</pca_gain>"
                         "<input_type>Normal</input_type><bias_include>Yes</bias_include>"
                         "<srb2>On</srb2><srb1>Off</srb1></Channel1></Channels>")
        loaded = load_settings(self.path)
        self.assertEqual(loaded.channels[0].pca_gain, "X6")

    def test_malformed_values_are_rejected(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("<Channels><Channel1><pca_gain>X24</pca_gain></Channel1></Channels>")
        with self.assertRaises(SettingsError):
            load_settings(self.path)
        with self.assertRaises(SettingsError):
            save_settings(self.path, HardwareSettings(channels=()))

    def test_atomic_write_replaces_an_existing_file(self):
        save_settings(self.path, HardwareSettings((_channel(),)))
        before = os.stat(self.path).st_mtime_ns
        save_settings(self.path, HardwareSettings((_channel(gain="X24"),), sampling_rate=250))
        self.assertEqual(load_settings(self.path).sampling_rate, 250)
        self.assertGreaterEqual(os.stat(self.path).st_mtime_ns, before)


if __name__ == "__main__":
    unittest.main()
