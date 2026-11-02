import unittest
from unittest.mock import patch

from freebci.api.wifi_discovery import (
    candidate_addresses,
    parse_board_payload,
    parse_wifi_interfaces,
    probe_board,
)


class BoardPayloadTest(unittest.TestCase):
    def test_reads_channels_and_readiness(self):
        parsed = parse_board_payload(
            {
                "board_connected": True,
                "board_type": "daisy",
                "num_channels": 16,
            }
        )
        self.assertEqual(parsed, (16, "daisy", True))

    def test_ignores_unrelated_or_malformed_payloads(self):
        self.assertIsNone(parse_board_payload({"unrelated": True}))
        self.assertIsNone(parse_board_payload([]))
        self.assertIsNone(parse_board_payload({"num_channels": "sixteen"}))

    def test_accepts_a_board_without_a_connection_flag(self):
        self.assertEqual(parse_board_payload({"num_channels": 8}), (8, "", None))

    def test_probe_returns_a_device_only_for_a_board_response(self):
        payload = '{"board_connected": true, "num_channels": 16, "board_type": "daisy"}'
        with patch("freebci.api.wifi_discovery._read_text", return_value=payload):
            device = probe_board("192.168.4.1")
        self.assertIsNotNone(device)
        self.assertEqual(device.channels, 16)
        self.assertTrue(device.ready)

    def test_probe_returns_none_when_nothing_answers(self):
        with patch("freebci.api.wifi_discovery._read_text", side_effect=OSError("offline")):
            self.assertIsNone(probe_board("192.168.4.1"))

    def test_probe_falls_back_to_the_wifi_manager_page(self):
        with patch(
            "freebci.api.wifi_discovery._read_text",
            side_effect=[OSError("no board endpoint"), "<title>FreeBCI WiFi Manager</title>"],
        ):
            device = probe_board("192.168.4.1")
        self.assertIsNotNone(device)
        self.assertEqual(device.address, "192.168.4.1")
        self.assertIsNone(device.channels)


class WifiInterfaceTest(unittest.TestCase):
    def test_reads_connected_freebci_access_point(self):
        status = parse_wifi_interfaces(
            """
            Name                   : Wi-Fi
            State                  : connected
            SSID                   : FreeBCI-1018
            BSSID                  : aa:bb:cc:dd:ee:ff
            """
        )
        self.assertTrue(status.connected)
        self.assertTrue(status.is_freebci)
        self.assertEqual(status.ssid, "FreeBCI-1018")

    def test_reports_disconnected_without_claiming_an_ssid(self):
        status = parse_wifi_interfaces(
            """
            Name                   : Wi-Fi
            State                  : disconnected
            SSID                   :
            """
        )
        self.assertFalse(status.connected)
        self.assertIsNone(status.ssid)
        self.assertEqual(status.detail, "Not connected to a Wi-Fi network")

    def test_missing_ssid_is_unknown_not_disconnected(self):
        status = parse_wifi_interfaces("Function WlanQueryInterface returns error 5")
        self.assertFalse(status.connected)
        self.assertEqual(status.detail, "Wi-Fi status unavailable")


class CandidateAddressTest(unittest.TestCase):
    def test_includes_default_and_first_host_of_local_networks(self):
        addresses = candidate_addresses(
            extra=("10.0.0.5",),
            local_addresses=("192.168.4.2", "127.0.0.1"),
        )
        self.assertEqual(addresses[0], "192.168.4.1")
        self.assertIn("10.0.0.5", addresses)
        self.assertIn("192.168.4.1", addresses)
        self.assertNotIn("127.0.0.1", addresses)

    def test_deduplicates_addresses(self):
        addresses = candidate_addresses(
            extra=("192.168.4.1", "192.168.4.1"),
            local_addresses=(),
        )
        self.assertEqual(addresses, ("192.168.4.1",))


if __name__ == "__main__":
    unittest.main()
