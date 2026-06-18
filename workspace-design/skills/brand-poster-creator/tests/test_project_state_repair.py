#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager, STAGE_ORDER  # noqa: E402


class ProjectStateRepairTests(unittest.TestCase):
    def test_repairs_legacy_scalar_stage_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "BP-TEST-A"
            project_dir.mkdir()
            (project_dir / "project_state.json").write_text(
                json.dumps(
                    {
                        "current_stage": "copywriting",
                        "stage_status": "completed",
                        "workflow_flags": {"copy_confirmed": True},
                        "attempts": {},
                        "resume": {"next_stage": "prompt"},
                        "artifacts": [
                            "brief.json",
                            "copywriting.json",
                            "images/logo.jpg",
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manager = ProjectManager(project_dir)

            self.assertIsInstance(manager.state["stage_status"], dict)
            self.assertEqual(set(STAGE_ORDER), set(manager.state["stage_status"].keys()))
            self.assertEqual(manager.state["stage_status"]["copywriting"], "done")
            self.assertIsInstance(manager.state["artifacts"], dict)
            self.assertEqual(manager.state["artifacts"]["brief"], "brief.json")
            self.assertEqual(manager.state["artifacts"]["copywriting"], "copywriting.json")


if __name__ == "__main__":
    unittest.main()
