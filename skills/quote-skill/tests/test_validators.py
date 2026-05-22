import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quote_skill.validators import QuoteValidationError, validate_quote_content


def valid_content(case_type: str = "项目案") -> dict:
    return {
        "case_type": case_type,
        "annual_context": {
            "business_goal": "年度品牌增长",
            "service_period": "2026 年度",
            "service_boundary": "品牌经营相关服务",
            "core_service_modules": ["品牌策略", "产品定义"],
            "priority": "高",
        },
        "title": "测试报价",
        "subtitle": "阶段化测试",
        "overview_paragraphs": [],
        "pricing_summary": {},
        "stages": [
            {
                "stage_name": "第一阶段：项目共识",
                "stage_price": "待补充",
                "stage_duration": "待确认",
                "stage_deliverables": ["共识纪要"],
                "projects": [
                    {
                        "project_name": "需求共识",
                        "project_deliverables": ["需求共识纪要"],
                        "service_catalog_refs": ["catalog-1", "catalog-2"],
                        "tasks": [
                            {
                                "task_name": "目标澄清",
                                "description_bullets": ["明确项目目标。"],
                                "service_catalog_refs": ["catalog-1"],
                            },
                            {
                                "task_name": "范围确认",
                                "description_bullets": ["确认本次范围。"],
                                "service_catalog_refs": ["catalog-2"],
                            },
                        ],
                    },
                    {
                        "project_name": "资料梳理",
                        "project_deliverables": ["资料梳理清单"],
                        "service_catalog_refs": ["catalog-3", "catalog-4"],
                        "tasks": [
                            {
                                "task_name": "资料收集",
                                "description_bullets": ["收集现有资料。"],
                                "service_catalog_refs": ["catalog-3"],
                            },
                            {
                                "task_name": "风险备注",
                                "description_bullets": ["记录当前风险。"],
                                "service_catalog_refs": ["catalog-4"],
                            },
                        ],
                    },
                ],
            },
            {
                "stage_name": "第二阶段：策略与设计",
                "stage_price": "待补充",
                "stage_duration": "待确认",
                "stage_deliverables": ["设计提案"],
                "projects": [
                    {
                        "project_name": "策略提炼",
                        "project_deliverables": ["策略提案"],
                        "service_catalog_refs": ["catalog-5", "catalog-6"],
                        "tasks": [
                            {
                                "task_name": "卖点提炼",
                                "description_bullets": ["提炼核心卖点。"],
                                "service_catalog_refs": ["catalog-5"],
                            },
                            {
                                "task_name": "信息层级整理",
                                "description_bullets": ["整理包装信息层级。"],
                                "service_catalog_refs": ["catalog-6"],
                            },
                        ],
                    },
                    {
                        "project_name": "设计执行",
                        "project_deliverables": ["设计方案"],
                        "service_catalog_refs": ["catalog-7", "catalog-8"],
                        "tasks": [
                            {
                                "task_name": "主视觉设计",
                                "description_bullets": ["完成主视觉方案。"],
                                "service_catalog_refs": ["catalog-7"],
                            },
                            {
                                "task_name": "延展应用整理",
                                "description_bullets": ["整理延展应用方向。"],
                                "service_catalog_refs": ["catalog-8"],
                            },
                        ],
                    },
                ],
            }
        ],
        "pending_catalog_items": [],
        "closing_notes": [],
    }


def single_stage_content(case_type: str = "散案") -> dict:
    content = valid_content(case_type=case_type)
    content["stages"] = [deepcopy(content["stages"][0])]
    return content


def full_case_minimal_content() -> dict:
    content = valid_content(case_type="全案")
    content["stages"] = [
        {
            "stage_name": "品牌年度经营",
            "stage_kind": "service_module",
            "stage_price": "待补充",
            "stage_duration": "2026 年度",
            "stage_deliverables": ["年度经营计划"],
            "projects": [
                {
                    "project_name": "年度策略统筹",
                    "project_deliverables": ["年度策略建议"],
                    "service_catalog_refs": [],
                    "tasks": [
                        {
                            "task_name": "季度方向校准",
                            "description_bullets": ["围绕季度经营重点进行校准。"],
                            "service_catalog_refs": ["catalog-annual-1"],
                        }
                    ],
                }
            ],
        }
    ]
    return content


class QuoteValidatorTests(unittest.TestCase):
    def test_validate_quote_content_accepts_valid_staged_content(self):
        normalized = validate_quote_content(valid_content())
        self.assertEqual(normalized["case_type"], "项目案")
        self.assertEqual(
            normalized["stages"][0]["projects"][0]["tasks"][0]["task_name"], "目标澄清"
        )
        self.assertEqual(normalized["pending_catalog_items"], [])

    def test_validate_quote_content_rejects_unknown_case_type(self):
        content = valid_content(case_type="神秘案")
        with self.assertRaises(QuoteValidationError):
            validate_quote_content(content)

    def test_validate_quote_content_rejects_stage_with_only_one_project(self):
        content = valid_content()
        content["stages"][0]["projects"] = [content["stages"][0]["projects"][0]]
        with self.assertRaises(QuoteValidationError):
            validate_quote_content(content)

    def test_validate_quote_content_accepts_scatter_case_with_single_complete_stage(self):
        normalized = validate_quote_content(single_stage_content(case_type="散案"))
        self.assertEqual(normalized["case_type"], "散案")
        self.assertEqual(len(normalized["stages"]), 1)

    def test_validate_quote_content_rejects_project_with_only_one_task(self):
        content = valid_content()
        content["stages"][0]["projects"][0]["tasks"] = [
            content["stages"][0]["projects"][0]["tasks"][0]
        ]
        with self.assertRaises(QuoteValidationError):
            validate_quote_content(content)

    def test_validate_quote_content_rejects_project_case_with_only_one_stage(self):
        content = single_stage_content(case_type="项目案")
        with self.assertRaises(QuoteValidationError):
            validate_quote_content(content)

    def test_validate_quote_content_rejects_task_without_description(self):
        content = valid_content()
        content["stages"][0]["projects"][0]["tasks"][0]["description_bullets"] = []
        with self.assertRaises(QuoteValidationError):
            validate_quote_content(content)

    def test_validate_quote_content_allows_missing_project_catalog_refs_when_task_refs_exist(self):
        content = valid_content()
        content["stages"][0]["projects"][0]["service_catalog_refs"] = []
        normalized = validate_quote_content(content)
        self.assertEqual(normalized["stages"][0]["projects"][0]["service_catalog_refs"], [])

    def test_validate_quote_content_accepts_scatter_case_with_pending_candidate(self):
        content = single_stage_content(case_type="散案")
        content["stages"][0]["projects"][0]["tasks"][0]["service_catalog_refs"] = []
        content["stages"][0]["projects"][0]["tasks"][0]["catalog_status"] = "pending_review"
        content["stages"][0]["projects"][0]["tasks"][0]["catalog_candidate"] = {
            "proposed_level_1_module": "产品定义",
            "proposed_level_2_module": "产品策略及表现",
            "proposed_project": "包装创意",
            "proposed_task": "包装卖点语气校准",
            "description": "围绕包装卖点语气新增一项任务。",
            "reason": "本项目新增条目",
        }

        normalized = validate_quote_content(content)

        self.assertEqual(len(normalized["pending_catalog_items"]), 1)
        self.assertEqual(
            normalized["pending_catalog_items"][0]["proposed_task"], "包装卖点语气校准"
        )

    def test_validate_quote_content_rejects_invalid_catalog_status(self):
        content = valid_content()
        content["stages"][0]["projects"][0]["tasks"][0]["catalog_status"] = "draft"
        with self.assertRaises(QuoteValidationError):
            validate_quote_content(content)

    def test_validate_quote_content_rejects_pending_review_without_required_candidate_fields(self):
        content = single_stage_content(case_type="散案")
        content["stages"][0]["projects"][0]["tasks"][0]["service_catalog_refs"] = []
        content["stages"][0]["projects"][0]["tasks"][0]["catalog_status"] = "pending_review"
        content["stages"][0]["projects"][0]["tasks"][0]["catalog_candidate"] = {
            "proposed_level_1_module": "产品定义",
            "proposed_level_2_module": "产品策略及表现",
            "proposed_project": "",
            "proposed_task": "包装卖点语气校准",
            "description": "围绕包装卖点语气新增一项任务。",
            "reason": "本项目新增条目",
        }
        with self.assertRaises(QuoteValidationError):
            validate_quote_content(content)

    def test_validate_quote_content_rejects_full_case_without_annual_context(self):
        content = valid_content(case_type="全案")
        content["annual_context"] = {}
        with self.assertRaises(QuoteValidationError):
            validate_quote_content(content)

    def test_validate_quote_content_accepts_full_case_with_single_module_project_task(self):
        normalized = validate_quote_content(full_case_minimal_content())
        self.assertEqual(normalized["case_type"], "全案")
        self.assertEqual(len(normalized["stages"]), 1)
        self.assertEqual(len(normalized["stages"][0]["projects"]), 1)
        self.assertEqual(len(normalized["stages"][0]["projects"][0]["tasks"]), 1)


if __name__ == "__main__":
    unittest.main()
