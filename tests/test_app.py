import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from freebci.app import create_application


class ApplicationCompositionTest(unittest.TestCase):
    def test_reuses_the_process_application(self):
        first = create_application([])
        second = create_application([])
        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
