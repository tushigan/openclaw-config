#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path("/Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py")


def load_module():
    spec = importlib.util.spec_from_file_location("product_photo_common_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProductPhotographySizeDefaultsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()

    def test_known_ratios_use_highest_safe_resolution(self) -> None:
        self.assertEqual(self.module.size_for_ratio("1:1"), "2880x2880")
        self.assertEqual(self.module.size_for_ratio("4:5"), "2560x3200")
        self.assertEqual(self.module.size_for_ratio("3:4"), "2448x3264")
        self.assertEqual(self.module.size_for_ratio("9:16"), "2160x3840")
        self.assertEqual(self.module.size_for_ratio("16:9"), "3840x2160")

    def test_unknown_ratio_defaults_to_highest_safe_square(self) -> None:
        self.assertEqual(self.module.size_for_ratio(""), "2880x2880")
        self.assertEqual(self.module.size_for_ratio("weird"), "2880x2880")


if __name__ == "__main__":
    unittest.main()
