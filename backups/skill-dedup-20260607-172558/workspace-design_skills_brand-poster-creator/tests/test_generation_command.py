#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "execute_generation.py"


def load_module():
    spec = importlib.util.spec_from_file_location("brand_poster_execute_generation_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BrandPosterGenerationCommandTests(unittest.TestCase):
    def test_count_is_forwarded_to_gpt_image_generator(self) -> None:
        module = load_module()

        cmd = module.build_command(
            prompt_path=Path("/tmp/prompt.md"),
            output_path=Path("/tmp/final_poster.png"),
            refs=[],
            size="1920x1080",
            aspect="16:9",
            model="gpt-image-2",
            count=4,
        )

        self.assertIn("--count", cmd)
        self.assertEqual(cmd[cmd.index("--count") + 1], "4")

    def test_preflight_blocks_when_required_logo_is_not_in_ref_order(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "prompt_draft.md").write_text("prompt", encoding="utf-8")
            (project_dir / "copywriting.json").write_text("{}", encoding="utf-8")
            logo_path = project_dir / "logo.png"
            logo_path.write_bytes(b"logo")
            ip_path = project_dir / "ip.png"
            ip_path.write_bytes(b"ip")
            brief = {
                "must_include": ["品牌LOGO", "品牌IP"],
                "assets": {
                    "logo": str(logo_path),
                    "ip": str(ip_path),
                },
            }
            ref_order_data = {
                "ref_order": [
                    {"index": 0, "role": "ip", "path": str(ip_path)},
                ]
            }

            errors, _refs, _missing_refs, _required_files = module.validate_preflight(project_dir, brief, ref_order_data)

        self.assertTrue(any("Logo" in error and "ref_order" in error for error in errors), errors)

    def test_preflight_blocks_when_required_ip_is_not_in_ref_order(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "prompt_draft.md").write_text("prompt", encoding="utf-8")
            (project_dir / "copywriting.json").write_text("{}", encoding="utf-8")
            logo_path = project_dir / "logo.png"
            logo_path.write_bytes(b"logo")
            ip_path = project_dir / "ip.png"
            ip_path.write_bytes(b"ip")
            brief = {
                "must_include": ["品牌LOGO", "品牌IP"],
                "hero_priority": {"hero_1": "品牌IP"},
                "assets": {
                    "logo": str(logo_path),
                    "ip": str(ip_path),
                },
            }
            ref_order_data = {
                "ref_order": [
                    {"index": 0, "role": "logo", "path": str(logo_path)},
                ]
            }

            errors, _refs, _missing_refs, _required_files = module.validate_preflight(project_dir, brief, ref_order_data)

        self.assertTrue(any("IP" in error and "ref_order" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
