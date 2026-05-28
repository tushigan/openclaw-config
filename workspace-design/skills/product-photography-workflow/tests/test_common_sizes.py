#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "common.py"
RUN_GENERATION_PATH = SKILL_DIR / "scripts" / "run_generation.py"


def load_module():
    spec = importlib.util.spec_from_file_location("product_photo_common_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_run_generation_module():
    spec = importlib.util.spec_from_file_location("product_photo_run_generation_under_test", RUN_GENERATION_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProductPhotographySizeDefaultsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.run_generation_module = load_run_generation_module()

    def test_known_ratios_use_highest_safe_resolution(self) -> None:
        self.assertEqual(self.module.size_for_ratio("1:1"), "2880x2880")
        self.assertEqual(self.module.size_for_ratio("4:5"), "2560x3200")
        self.assertEqual(self.module.size_for_ratio("3:4"), "2448x3264")
        self.assertEqual(self.module.size_for_ratio("9:16"), "2160x3840")
        self.assertEqual(self.module.size_for_ratio("16:9"), "3840x2160")

    def test_unknown_ratio_defaults_to_highest_safe_square(self) -> None:
        self.assertEqual(self.module.size_for_ratio(""), "2880x2880")
        self.assertEqual(self.module.size_for_ratio("weird"), "2880x2880")

    def test_default_output_root_uses_local_machine_home(self) -> None:
        output_root = self.module.DEFAULT_OUTPUT_ROOT
        self.assertTrue(output_root.is_absolute())
        self.assertNotIn("/Users/a123/.openclaw", str(output_root))
        self.assertEqual(output_root, Path.home() / "Documents" / "Codex" / "product-photography-workflow" / "outputs")

    def test_default_gpt_image_entry_uses_local_codex_skill_path(self) -> None:
        gpt_script = self.run_generation_module.DEFAULT_GPT_IMAGE2_SCRIPT
        self.assertTrue(gpt_script.is_absolute())
        self.assertNotIn("/Users/a123/.openclaw", str(gpt_script))
        self.assertEqual(gpt_script, Path.home() / ".codex" / "skills" / "gpt-image2-gen" / "scripts" / "generate.py")


if __name__ == "__main__":
    unittest.main()
