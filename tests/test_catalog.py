import unittest

from freebci.core.catalog import BOARD_ROWS, get_profile, get_row, load_catalog, rows


class BoardCatalogTests(unittest.TestCase):
    def test_catalog_contains_all_known_boards(self):
        catalog = load_catalog()
        self.assertEqual(len(BOARD_ROWS), 29)
        self.assertEqual(len(catalog), 29)
        self.assertEqual(catalog[2038].name, "FreeBCI_WiFi_16_I_WIFI")
        self.assertEqual(catalog[2038].channels, 16)
        self.assertTrue(catalog[2038].has_battery)

    def test_rows_are_a_mutable_legacy_copy(self):
        data = rows()
        self.assertEqual(data[14][1], 2037)
        data[14][0] = "changed"
        self.assertNotEqual(rows()[14][0], "changed")

    def test_profile_and_row_lookup(self):
        self.assertEqual(get_row(2038), BOARD_ROWS[15])
        self.assertEqual(get_profile(2045).channels, 64)
        with self.assertRaises(KeyError):
            get_profile(9999)


if __name__ == "__main__":
    unittest.main()
