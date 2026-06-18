#!/usr/bin/env python3
import re
import unittest
from pathlib import Path


SKILL_MD = Path(__file__).resolve().parents[1] / "SKILL.md"


class CopywriterChainTests(unittest.TestCase):
    def test_copy_stage_uses_strategy_then_copywriter(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")

        self.assertIn('"agentId": "strategy"', text)
        self.assertIn('"agentId": "copywriter"', text)
        self.assertIn("copy_strategy.json", text)
        self.assertIn("copywriting.json", text)
        self.assertIn("不得让 `strategy` 直接写最终 `copywriting.json`", text)

    def test_strategy_template_writes_strategy_not_final_copy(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        match = re.search(r"### 给 strategy 的任务描述模板\n\n```(?P<body>.*?)```", text, re.S)
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("不要写最终文案", body)
        self.assertIn("copy_strategy.json", body)
        self.assertNotIn("写入：/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copywriting.json", body)

    def test_copywriter_template_writes_final_copy(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        match = re.search(r"\*\*给 copywriter 的任务描述模板：\*\*\n\n```(?P<body>.*?)```", text, re.S)
        self.assertIsNotNone(match)
        body = match.group("body")

        self.assertIn("copy_strategy.json", body)
        self.assertIn("copywriting.json", body)
        self.assertIn("最终可上画面的文案", body)


if __name__ == "__main__":
    unittest.main()
