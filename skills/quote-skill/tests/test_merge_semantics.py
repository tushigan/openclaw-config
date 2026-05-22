from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quote_skill.renderers import render_html
from validate_merge_semantics import validate_merge_semantics


HTML_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "templates" / "quote.html"
)


def sample_quote_content() -> dict:
    return {
        "title": "测试报价",
        "subtitle": "合并校验",
        "case_type": "散案",
        "overview_paragraphs": ["测试概述。"],
        "pricing_summary": {
            "label": "当前报价结构",
            "details": "按阶段执行",
            "total": "待补充",
        },
        "stages": [
            {
                "stage_name": "第一阶段",
                "stage_price": "待补充",
                "stage_duration": "2 周",
                "stage_deliverables": ["阶段交付 A"],
                "projects": [
                    {
                        "project_name": "项目一",
                        "project_deliverables": ["项目一交付"],
                        "service_catalog_refs": ["catalog-1", "catalog-2"],
                        "tasks": [
                            {
                                "task_name": "任务一",
                                "description_bullets": ["说明一"],
                                "service_catalog_refs": ["catalog-1"],
                            },
                            {
                                "task_name": "任务二",
                                "description_bullets": ["说明二"],
                                "service_catalog_refs": ["catalog-2"],
                            },
                        ],
                    },
                    {
                        "project_name": "项目二",
                        "project_deliverables": ["项目二交付"],
                        "service_catalog_refs": ["catalog-3", "catalog-4"],
                        "tasks": [
                            {
                                "task_name": "任务三",
                                "description_bullets": ["说明三"],
                                "service_catalog_refs": ["catalog-3"],
                            },
                            {
                                "task_name": "任务四",
                                "description_bullets": ["说明四"],
                                "service_catalog_refs": ["catalog-4"],
                            },
                        ],
                    },
                ],
            }
        ],
        "closing_notes": ["报价有效期 15 天。"],
    }


class MergeSemanticsTests(unittest.TestCase):
    def test_validator_accepts_renderer_output(self):
        content = sample_quote_content()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            content_path = tmp_dir / "quote-content.json"
            html_path = tmp_dir / "quote.html"
            content_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
            render_html(content, template_path=HTML_TEMPLATE_PATH, output_path=html_path)

            validate_merge_semantics(content_path, html_path)

    def test_validator_rejects_fake_merged_html(self):
        content = sample_quote_content()
        fake_html = """
        <table><tbody>
        <tr><td class="block">第一阶段</td><td class="project">项目一</td><td>任务一</td></tr>
        <tr><td class="block"></td><td class="project"></td><td>任务二</td></tr>
        </tbody></table>
        """

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            content_path = tmp_dir / "quote-content.json"
            html_path = tmp_dir / "quote.html"
            content_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
            html_path.write_text(fake_html, encoding="utf-8")

            with self.assertRaises(SystemExit):
                validate_merge_semantics(content_path, html_path)


if __name__ == "__main__":
    unittest.main()
