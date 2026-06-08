#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "split_direction_projects.py"


class SplitDirectionProjectsTests(unittest.TestCase):
    def test_splits_options_into_prompt_ready_child_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "BP-TEST-001"
            (base / "images").mkdir(parents=True)
            (base / "brief.json").write_text(
                json.dumps(
                    {
                        "task_id": "BP-TEST-001",
                        "brand_name": "测试品牌",
                        "ratio": "9:16",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (base / "copywriting.json").write_text(
                json.dumps(
                    {
                        "options": [
                            {
                                "direction_name": "热血鼓劲",
                                "main_title": "全力以赴",
                                "sub_title": "每一步都是答案",
                                "brand_line": "测试品牌 为你加油",
                                "strategy_note": "直接号召",
                            },
                            {
                                "direction_name": "温暖陪伴",
                                "main_title": "这一路有我陪你",
                                "sub_title": "稳稳走进考场",
                                "brand_line": "测试品牌 一直在",
                                "strategy_note": "陪伴口吻",
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (base / "project_state.json").write_text(
                json.dumps(
                    {
                        "current_stage": "copywriting",
                        "stage_status": "completed",
                        "workflow_flags": {},
                        "attempts": {},
                        "resume": {},
                        "artifacts": ["brief.json", "copywriting.json"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                ["python3", str(SCRIPT), "--project-dir", str(base)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for suffix, title in [("A", "全力以赴"), ("B", "这一路有我陪你")]:
                child = root / f"BP-TEST-001-{suffix}"
                self.assertTrue(child.exists())
                copywriting = json.loads((child / "copywriting.json").read_text(encoding="utf-8"))
                self.assertEqual(copywriting["title_main"]["文案"], title)
                self.assertIn("subtitle_main", copywriting)
                self.assertIn("brand_line", copywriting)
                state = json.loads((child / "project_state.json").read_text(encoding="utf-8"))
                self.assertIsInstance(state["stage_status"], dict)
                self.assertEqual(state["stage_status"]["copywriting"], "done")
                brief = json.loads((child / "brief.json").read_text(encoding="utf-8"))
                self.assertEqual(brief["task_id"], f"BP-TEST-001-{suffix}")
                self.assertEqual(brief["direction_name"], copywriting["_meta"]["direction_name"])


if __name__ == "__main__":
    unittest.main()
