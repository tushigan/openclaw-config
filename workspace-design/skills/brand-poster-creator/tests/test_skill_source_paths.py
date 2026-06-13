#!/usr/bin/env python3
import re
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"


class SkillSourcePathTests(unittest.TestCase):
    def test_skill_uses_top_level_script_paths_after_dedup(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")

        forbidden = [
            "/Users/a123/.openclaw/workspace/skills/brand-poster-creator",
            "/Users/a123/.openclaw/workspace-design/skills/brand-poster-creator",
        ]
        for path in forbidden:
            self.assertNotIn(path, text)

        script_paths = re.findall(r"/Users/a123/\.openclaw/skills/brand-poster-creator/scripts/[\w_]+\.py", text)
        self.assertGreaterEqual(len(script_paths), 8)
        for raw_path in script_paths:
            self.assertTrue(Path(raw_path).exists(), raw_path)

    def test_skill_documents_direction_split_and_protected_launcher(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")

        self.assertIn("split_direction_projects.py", text)
        self.assertIn("direction_split_manifest.json", text)
        self.assertIn("runpy.run_path", text)
        self.assertIn("不得复制 skill 脚本", text)


if __name__ == "__main__":
    unittest.main()
