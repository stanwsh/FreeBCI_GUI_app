import unittest
from pathlib import Path

LEGACY_FONT_NAMES = ("黑体", "等线", "SimSun", "宋体", "微软雅黑", "Arial")


class FontTests(unittest.TestCase):
    def test_presentation_uses_the_preferred_ui_font(self):
        package = Path(__file__).resolve().parents[1] / "freebci"
        offenders = []
        for path in package.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for name in LEGACY_FONT_NAMES:
                if name in text:
                    offenders.append("%s: %s" % (path.relative_to(package), name))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
