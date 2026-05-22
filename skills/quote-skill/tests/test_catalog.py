import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zipfile import BadZipFile

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quote_skill.catalog import build_catalog, parse_summary_sheet
from quote_skill.catalog_pending import (
    add_pending_items,
    load_pending_items,
    remove_pending_item,
    resolve_pending_items,
)
from quote_skill.catalog_sync import ensure_catalog_json, needs_catalog_rebuild


class CatalogTests(unittest.TestCase):
    def _make_workbook(self, workbook_path: Path) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "汇总表"
        worksheet.append(
            [
                "选择",
                "模块",
                "模块",
                "项目",
                "任务",
                "说明",
                "服务部门",
                "计划时间(工作日)",
                "交付成果",
                "建议报价",
                "",
                None,
            ]
        )
        worksheet.append(
            [
                0,
                "品牌策略",
                "供给侧调研分析",
                "企业调研",
                "高层核心团队访谈",
                "访谈企业高层团队。",
                "策略部",
                "5",
                "企业调研分析报告.ppt\n访谈纪要.docx",
                "1000",
                None,
                None,
            ]
        )
        worksheet.append(
            [
                None,
                None,
                None,
                None,
                "企业战略目标分析",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        )
        worksheet.append(
            [
                None,
                None,
                None,
                None,
                None,
                "缺少任务名称，不应生成服务项。",
                "策略部",
                "2",
                "错误示例.docx",
                "200",
                None,
                None,
            ]
        )
        workbook.save(workbook_path)

    def test_parse_summary_sheet_fills_down_parent_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "service-catalog.xlsx"
            self._make_workbook(workbook_path)

            rows = parse_summary_sheet(workbook_path)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1]["level_1_module"], "品牌策略")
            self.assertEqual(rows[1]["level_2_module"], "供给侧调研分析")
            self.assertEqual(rows[1]["project"], "企业调研")
            self.assertEqual(rows[1]["task"], "企业战略目标分析")
            self.assertIsNone(rows[1]["service_department"])
            self.assertIsNone(rows[1]["planned_workdays"])
            self.assertEqual(rows[1]["deliverables"], [])
            self.assertIsNone(rows[1]["suggested_price"])
            self.assertEqual(
                rows[0]["deliverables"],
                ["企业调研分析报告.ppt", "访谈纪要.docx"],
            )
            self.assertEqual(rows[0]["service_department"], "策略部")
            self.assertEqual(rows[0]["planned_workdays"], "5")
            self.assertEqual(rows[0]["suggested_price"], "1000")
            self.assertTrue(all(row["task"] for row in rows))

    def test_parse_summary_sheet_skips_rows_without_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "service-catalog.xlsx"
            self._make_workbook(workbook_path)

            rows = parse_summary_sheet(workbook_path)

            self.assertEqual(len(rows), 2)
            self.assertFalse(any(row["source"]["row"] == 4 for row in rows))
            self.assertFalse(any("row-" in row["service_id"] for row in rows))

    def test_build_catalog_writes_machine_readable_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "service-catalog.xlsx"
            output_path = Path(tmp) / "service-catalog.json"
            self._make_workbook(workbook_path)

            payload = build_catalog(workbook_path, output_path)

            written_text = output_path.read_text(encoding="utf-8")
            written_payload = json.loads(written_text)
            self.assertEqual(payload["source_sheet"], "汇总表")
            self.assertEqual(written_payload["source_sheet"], "汇总表")
            self.assertEqual(len(written_payload["services"]), 2)
            self.assertEqual(
                written_payload["services"][0]["service_id"],
                "品牌策略__供给侧调研分析__企业调研__高层核心团队访谈",
            )
            self.assertIn("品牌策略", written_text)
            self.assertNotIn("\\u54c1\\u724c\\u7b56\\u7565", written_text)
            self.assertIn('\n  "catalog_name"', written_text)

            generated_at = written_payload["generated_at"]
            self.assertIsInstance(generated_at, str)
            parsed_generated_at = datetime.fromisoformat(generated_at)
            self.assertIsNotNone(parsed_generated_at.tzinfo)
            self.assertIsNotNone(parsed_generated_at.utcoffset())

    def test_needs_catalog_rebuild_when_workbook_is_newer(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "service-catalog.xlsx"
            output_path = Path(tmp) / "service-catalog.json"
            self._make_workbook(workbook_path)
            build_catalog(workbook_path, output_path)

            newer = output_path.stat().st_mtime + 10
            os.utime(workbook_path, (newer, newer))

            self.assertTrue(needs_catalog_rebuild(workbook_path, output_path))

    def test_ensure_catalog_json_rebuilds_when_json_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "service-catalog.xlsx"
            output_path = Path(tmp) / "service-catalog.json"
            self._make_workbook(workbook_path)
            output_path.write_text("{not-json}", encoding="utf-8")

            payload = ensure_catalog_json(workbook_path, output_path)

            self.assertEqual(payload["source_file"], str(workbook_path))
            self.assertEqual(payload["source_sheet"], "汇总表")
            self.assertEqual(len(payload["services"]), 2)

    def test_ensure_catalog_json_rebuilds_when_json_structure_is_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "service-catalog.xlsx"
            output_path = Path(tmp) / "service-catalog.json"
            self._make_workbook(workbook_path)
            output_path.write_text(
                json.dumps({"source_sheet": "汇总表"}, ensure_ascii=False),
                encoding="utf-8",
            )

            payload = ensure_catalog_json(workbook_path, output_path)

            self.assertEqual(payload["source_file"], str(workbook_path))
            self.assertEqual(payload["source_sheet"], "汇总表")
            self.assertEqual(len(payload["services"]), 2)

    def test_needs_catalog_rebuild_when_source_file_does_not_match_workbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "service-catalog.xlsx"
            other_workbook_path = Path(tmp) / "other-service-catalog.xlsx"
            output_path = Path(tmp) / "service-catalog.json"
            self._make_workbook(workbook_path)
            self._make_workbook(other_workbook_path)
            build_catalog(other_workbook_path, output_path)

            self.assertTrue(needs_catalog_rebuild(workbook_path, output_path))

    def test_ensure_catalog_json_raises_when_workbook_cannot_be_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            workbook_path = Path(tmp) / "service-catalog.xlsx"
            output_path = Path(tmp) / "service-catalog.json"
            workbook_path.write_text("not-an-xlsx", encoding="utf-8")

            with self.assertRaises(BadZipFile):
                ensure_catalog_json(workbook_path, output_path)

    def test_pending_pool_adds_and_removes_company_level_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending_path = Path(tmp) / "catalog-pending-review.json"

            created = add_pending_items(
                pending_path,
                [
                    {
                        "client_name": "示例客户",
                        "project_name": "示例项目",
                        "version": "v2",
                        "proposed_level_1_module": "产品定义",
                        "proposed_level_2_module": "产品策略及表现",
                        "proposed_project": "包装创意",
                        "proposed_task": "包装卖点语气校准",
                        "description": "围绕包装语气补一条新增任务。",
                        "reason": "本次报价出现新条目",
                    }
                ],
            )

            self.assertEqual(len(created), 1)
            pending_item = created[0]
            self.assertEqual(pending_item["status"], "pending-review")
            self.assertIn("pending_id", pending_item)
            self.assertIn("discovered_at", pending_item)
            self.assertEqual(pending_item["client_name"], "示例客户")
            self.assertEqual(pending_item["project_name"], "示例项目")
            self.assertEqual(pending_item["version"], "v2")
            self.assertEqual(pending_item["proposed_level_1_module"], "产品定义")
            self.assertEqual(pending_item["proposed_level_2_module"], "产品策略及表现")
            self.assertEqual(pending_item["proposed_project"], "包装创意")
            self.assertEqual(pending_item["proposed_task"], "包装卖点语气校准")
            self.assertEqual(pending_item["description"], "围绕包装语气补一条新增任务。")
            self.assertEqual(pending_item["reason"], "本次报价出现新条目")

            loaded = load_pending_items(pending_path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["pending_id"], pending_item["pending_id"])

            remove_pending_item(pending_path, pending_item["pending_id"])
            self.assertEqual(load_pending_items(pending_path), [])

    def test_pending_pool_reuses_same_record_across_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending_path = Path(tmp) / "catalog-pending-review.json"
            base_item = {
                "client_name": "示例客户",
                "project_name": "示例项目",
                "proposed_level_1_module": "产品定义",
                "proposed_level_2_module": "产品策略及表现",
                "proposed_project": "包装创意",
                "proposed_task": "包装卖点语气校准",
                "description": "围绕包装语气补一条新增任务。",
                "reason": "本次报价出现新条目",
            }

            created_v1 = add_pending_items(
                pending_path,
                [{**base_item, "version": "v1"}],
            )
            created_v2 = add_pending_items(
                pending_path,
                [{**base_item, "version": "v2"}],
            )

            self.assertEqual(len(created_v1), 1)
            self.assertEqual(created_v1[0]["version"], "v1")
            self.assertEqual(created_v2, [])

            loaded = load_pending_items(pending_path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["pending_id"], created_v1[0]["pending_id"])
            self.assertEqual(loaded[0]["version"], "v1")

            resolved = resolve_pending_items(
                pending_path,
                [{**base_item, "version": "v2"}],
            )
            self.assertEqual(len(resolved), 1)
            self.assertEqual(resolved[0]["pending_id"], created_v1[0]["pending_id"])

    def test_add_pending_items_returns_only_newly_created_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending_path = Path(tmp) / "catalog-pending-review.json"
            existing = add_pending_items(
                pending_path,
                [
                    {
                        "client_name": "旧客户",
                        "project_name": "旧项目",
                        "version": "v1",
                        "proposed_level_1_module": "品牌策略",
                        "proposed_level_2_module": "市场洞察",
                        "proposed_project": "用户调研",
                        "proposed_task": "竞品盘点",
                        "description": "已有待审核旧项。",
                        "reason": "旧记录",
                    }
                ],
            )

            created = add_pending_items(
                pending_path,
                [
                    {
                        "client_name": "新客户",
                        "project_name": "新项目",
                        "version": "v3",
                        "proposed_level_1_module": "产品定义",
                        "proposed_level_2_module": "产品策略及表现",
                        "proposed_project": "包装创意",
                        "proposed_task": "包装卖点语气校准",
                        "description": "这是本次新增的待入库项。",
                        "reason": "本次报价出现新条目",
                    }
                ],
            )

            loaded = load_pending_items(pending_path)
            self.assertEqual(len(existing), 1)
            self.assertEqual(len(created), 1)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(created[0]["client_name"], "新客户")
            self.assertEqual(loaded[0]["client_name"], "旧客户")
            self.assertEqual(loaded[1]["pending_id"], created[0]["pending_id"])

    def test_add_pending_items_deduplicates_repeated_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending_path = Path(tmp) / "catalog-pending-review.json"
            candidate = {
                "client_name": "示例客户",
                "project_name": "示例项目",
                "version": "v2",
                "proposed_level_1_module": "产品定义",
                "proposed_level_2_module": "产品策略及表现",
                "proposed_project": "包装创意",
                "proposed_task": "包装卖点语气校准",
                "description": "围绕包装语气补一条新增任务。",
                "reason": "本次报价出现新条目",
            }

            first_created = add_pending_items(pending_path, [candidate])
            second_created = add_pending_items(pending_path, [dict(candidate)])

            loaded = load_pending_items(pending_path)
            self.assertEqual(len(first_created), 1)
            self.assertEqual(second_created, [])
            self.assertEqual(len(loaded), 1)

    def test_add_pending_items_rejects_candidates_with_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending_path = Path(tmp) / "catalog-pending-review.json"

            with self.assertRaises(ValueError):
                add_pending_items(
                    pending_path,
                    [
                        {
                            "client_name": "示例客户",
                            "project_name": "示例项目",
                            "version": "v2",
                            "proposed_level_1_module": "产品定义",
                            "proposed_level_2_module": "",
                            "proposed_project": "包装创意",
                            "proposed_task": "包装卖点语气校准",
                            "description": "围绕包装语气补一条新增任务。",
                            "reason": "本次报价出现新条目",
                        }
                    ],
                )

            self.assertEqual(load_pending_items(pending_path), [])


if __name__ == "__main__":
    unittest.main()
