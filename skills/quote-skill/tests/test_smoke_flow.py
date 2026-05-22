from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quote_skill.project import create_project

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_SCRIPT = REPO_ROOT / "scripts" / "render_quote_bundle.py"
NODE_BIN = Path(
    "/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
)
HTML_TO_PDF_SCRIPT = REPO_ROOT / "scripts" / "render_html_to_pdf.mjs"


class SmokeFlowTests(unittest.TestCase):
    EXISTING_SERVICE_IDS = {
        "task_1": "产品定义__产品策略及表现__包装创意__现有任务一",
        "task_2": "产品定义__产品策略及表现__包装创意__现有任务二",
        "task_3": "视觉设计__包装设计__设计执行__现有任务三",
        "task_4": "视觉设计__包装设计__设计执行__现有任务四",
    }

    def _base_content(self) -> dict:
        return {
            "title": "示例报价方案",
            "subtitle": "项目合作报价方案",
            "case_type": "散案",
            "overview_paragraphs": ["这是一个端到端冒烟测试。"],
            "pricing_summary": {
                "label": "当前报价结构",
                "details": "待人工填写",
                "total": "合计待定",
            },
            "annual_context": {},
            "stages": [
                {
                    "stage_name": "第一阶段：项目共识",
                    "stage_price": "待补充",
                    "stage_duration": "待确认",
                    "stage_deliverables": ["共识纪要"],
                    "projects": [
                        {
                            "project_name": "项目一",
                            "project_deliverables": ["项目一交付"],
                            "service_catalog_refs": [
                                self.EXISTING_SERVICE_IDS["task_1"],
                                self.EXISTING_SERVICE_IDS["task_2"],
                            ],
                            "tasks": [
                                {
                                    "task_name": "包装卖点语气校准",
                                    "description_bullets": ["新增任务说明。"],
                                    "service_catalog_refs": [],
                                    "catalog_status": "pending_review",
                                    "catalog_candidate": {
                                        "proposed_level_1_module": "产品定义",
                                        "proposed_level_2_module": "产品策略及表现",
                                        "proposed_project": "包装创意",
                                        "proposed_task": "包装卖点语气校准",
                                        "description": "围绕包装语气补一条新增任务。",
                                        "reason": "本次报价出现新条目",
                                    },
                                },
                                {
                                    "task_name": "任务二",
                                    "description_bullets": ["说明二"],
                                    "service_catalog_refs": [self.EXISTING_SERVICE_IDS["task_2"]],
                                },
                            ],
                        },
                        {
                            "project_name": "项目二",
                            "project_deliverables": ["项目二交付"],
                            "service_catalog_refs": [
                                self.EXISTING_SERVICE_IDS["task_3"],
                                self.EXISTING_SERVICE_IDS["task_4"],
                            ],
                            "tasks": [
                                {
                                    "task_name": "任务三",
                                    "description_bullets": ["说明三"],
                                    "service_catalog_refs": [self.EXISTING_SERVICE_IDS["task_3"]],
                                },
                                {
                                    "task_name": "任务四",
                                    "description_bullets": ["说明四"],
                                    "service_catalog_refs": [self.EXISTING_SERVICE_IDS["task_4"]],
                                },
                            ],
                        },
                    ],
                }
            ],
            "closing_notes": ["仅供测试。"],
        }

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
                None,
                None,
            ]
        )
        worksheet.append(
            [
                "Y",
                "产品定义",
                "产品策略及表现",
                "包装创意",
                "现有任务一",
                "说明一",
                "策略部",
                "3",
                "交付一",
                "1000",
                None,
                None,
            ]
        )
        worksheet.append(
            [
                "Y",
                None,
                None,
                None,
                "现有任务二",
                "说明二",
                "策略部",
                "2",
                "交付二",
                "2000",
                None,
                None,
            ]
        )
        worksheet.append(
            [
                "Y",
                "视觉设计",
                "包装设计",
                "设计执行",
                "现有任务三",
                "说明三",
                "设计部",
                "4",
                "交付三",
                "3000",
                None,
                None,
            ]
        )
        worksheet.append(
            [
                "Y",
                None,
                None,
                None,
                "现有任务四",
                "说明四",
                "设计部",
                "5",
                "交付四",
                "4000",
                None,
                None,
            ]
        )
        workbook_path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(workbook_path)

    def _run_bundle(
        self,
        *,
        content: dict,
        version_dir: Path,
        workbook_path: Path,
        catalog_json_path: Path,
        pending_pool_path: Path,
        project_dir: Path | None = None,
        version: str | None = None,
        expect_success: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        content_path = version_dir / "quote-content.json"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_text(
            json.dumps(content, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
        command = [
            sys.executable,
            str(BUNDLE_SCRIPT),
            "--content",
            str(content_path),
            "--output-dir",
            str(version_dir),
            "--formats",
            "html",
            "pdf",
            "xlsx",
            "--service-catalog-workbook",
            str(workbook_path),
            "--service-catalog-json",
            str(catalog_json_path),
            "--pending-pool",
            str(pending_pool_path),
            "--node-bin",
            str(NODE_BIN),
            "--html-to-pdf-script",
            str(HTML_TO_PDF_SCRIPT),
        ]
        if project_dir is not None:
            command.extend(["--project-dir", str(project_dir)])
        if version is not None:
            command.extend(["--version", version])

        return subprocess.run(
            command,
            check=expect_success,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_end_to_end_quote_bundle_generation(self):
        content = self._base_content()

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            projects_root = workspace / "projects"
            project_dir = create_project(
                projects_root,
                "示例客户",
                "示例项目",
                output_mode="html_pdf_xlsx",
            )
            version_dir = project_dir / "versions" / "v1"
            workbook_path = workspace / "assets" / "standards" / "service-catalog.xlsx"
            catalog_json_path = workspace / "data" / "service-catalog.json"
            pending_pool_path = workspace / "data" / "catalog-pending-review.json"
            self._make_workbook(workbook_path)

            catalog_json_path.parent.mkdir(parents=True, exist_ok=True)
            catalog_json_path.write_text(
                json.dumps(
                    {
                        "catalog_name": "stale",
                        "source_file": str(workbook_path),
                        "source_sheet": "汇总表",
                        "generated_at": "2000-01-01T00:00:00+00:00",
                        "services": [{"service_id": "stale-service", "task": "旧任务"}],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            stale_time = 946684800
            os.utime(catalog_json_path, (stale_time, stale_time))
            fresh_time = stale_time + 60
            os.utime(workbook_path, (fresh_time, fresh_time))

            self._run_bundle(
                content=content,
                version_dir=version_dir,
                workbook_path=workbook_path,
                catalog_json_path=catalog_json_path,
                pending_pool_path=pending_pool_path,
                project_dir=project_dir,
                version="v1",
            )

            self.assertTrue((version_dir / "quote.html").exists())
            self.assertTrue((version_dir / "quote.pdf").exists())
            self.assertTrue((version_dir / "quote.xlsx").exists())
            self.assertTrue(catalog_json_path.exists())
            self.assertTrue(pending_pool_path.exists())

            catalog_payload = json.loads(catalog_json_path.read_text(encoding="utf-8"))
            self.assertEqual(catalog_payload["catalog_name"], "service-catalog")
            self.assertEqual(catalog_payload["source_file"], str(workbook_path))
            self.assertEqual(catalog_payload["source_sheet"], "汇总表")
            self.assertEqual(len(catalog_payload["services"]), 4)
            self.assertNotEqual(catalog_payload["services"][0]["service_id"], "stale-service")
            self.assertEqual(catalog_payload["services"][0]["task"], "现有任务一")

            pending_payload = json.loads(pending_pool_path.read_text(encoding="utf-8"))
            self.assertEqual(len(pending_payload["items"]), 1)
            self.assertEqual(pending_payload["items"][0]["project_name"], "示例项目")

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            version_payload = json.loads((version_dir / "version.json").read_text(encoding="utf-8"))
            self.assertEqual(project_payload["current_version"], "v1")
            self.assertEqual(project_payload["status"], "pending-review")
            self.assertEqual(project_payload["confirmed_case_type"], "散案")
            self.assertEqual(project_payload["catalog_pending_summary"][0]["project_name"], "示例项目")
            self.assertEqual(version_payload["case_type"], "散案")
            self.assertEqual(
                version_payload["detected_new_catalog_items"][0]["proposed_task"],
                "包装卖点语气校准",
            )
            self.assertEqual(
                sorted(version_payload["catalog_refs_used"]),
                sorted(self.EXISTING_SERVICE_IDS.values()),
            )
            self.assertEqual(len(version_payload["pending_pool_item_ids"]), 1)

            skill_text = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("先完成报价，后处理清单沉淀", skill_text)
            self.assertIn("散案 / 项目案 / 全案", skill_text)
            self.assertIn("PDF 固定由 HTML 转出", skill_text)

            reference_text = (REPO_ROOT / "references" / "service-catalog.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("如果主清单更新，先重建 data/service-catalog.json", reference_text)
            self.assertIn("先完成正式报价，再进入公司总待入库池", reference_text)
            self.assertIn("本次不入库则移出总池，但保留项目级记录", reference_text)

    def test_bundle_fails_before_render_when_pending_items_lack_project_context(self):
        content = self._base_content()

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            version_dir = workspace / "output"
            workbook_path = workspace / "assets" / "standards" / "service-catalog.xlsx"
            catalog_json_path = workspace / "data" / "service-catalog.json"
            pending_pool_path = workspace / "data" / "catalog-pending-review.json"
            self._make_workbook(workbook_path)

            result = self._run_bundle(
                content=content,
                version_dir=version_dir,
                workbook_path=workbook_path,
                catalog_json_path=catalog_json_path,
                pending_pool_path=pending_pool_path,
                expect_success=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("缺少 project-dir 或 version", result.stderr)
            self.assertFalse((version_dir / "quote.html").exists())
            self.assertFalse((version_dir / "quote.pdf").exists())
            self.assertFalse((version_dir / "quote.xlsx").exists())
            self.assertFalse(pending_pool_path.exists())

    def test_bundle_without_pending_items_does_not_write_empty_pending_pool(self):
        content = self._base_content()
        content["stages"][0]["projects"][0]["tasks"][0] = {
            "task_name": "任务一",
            "description_bullets": ["说明一"],
            "service_catalog_refs": [self.EXISTING_SERVICE_IDS["task_1"]],
        }

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            projects_root = workspace / "projects"
            project_dir = create_project(
                projects_root,
                "示例客户",
                "无待入库项目",
                output_mode="html_pdf_xlsx",
            )
            version_dir = project_dir / "versions" / "v1"
            workbook_path = workspace / "assets" / "standards" / "service-catalog.xlsx"
            catalog_json_path = workspace / "data" / "service-catalog.json"
            pending_pool_path = workspace / "data" / "catalog-pending-review.json"
            self._make_workbook(workbook_path)

            self._run_bundle(
                content=content,
                version_dir=version_dir,
                workbook_path=workbook_path,
                catalog_json_path=catalog_json_path,
                pending_pool_path=pending_pool_path,
                project_dir=project_dir,
                version="v1",
            )

            self.assertTrue((version_dir / "quote.html").exists())
            self.assertTrue((version_dir / "quote.pdf").exists())
            self.assertTrue((version_dir / "quote.xlsx").exists())
            self.assertFalse(pending_pool_path.exists())

    def test_bundle_fails_before_render_when_catalog_ref_does_not_exist(self):
        content = self._base_content()
        content["stages"][0]["projects"][0]["service_catalog_refs"] = ["不存在的服务ref"]

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            projects_root = workspace / "projects"
            project_dir = create_project(
                projects_root,
                "示例客户",
                "非法引用项目",
                output_mode="html_pdf_xlsx",
            )
            version_dir = project_dir / "versions" / "v1"
            workbook_path = workspace / "assets" / "standards" / "service-catalog.xlsx"
            catalog_json_path = workspace / "data" / "service-catalog.json"
            pending_pool_path = workspace / "data" / "catalog-pending-review.json"
            self._make_workbook(workbook_path)

            result = self._run_bundle(
                content=content,
                version_dir=version_dir,
                workbook_path=workbook_path,
                catalog_json_path=catalog_json_path,
                pending_pool_path=pending_pool_path,
                project_dir=project_dir,
                version="v1",
                expect_success=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("不存在的服务清单引用", result.stderr)
            self.assertFalse((version_dir / "quote.html").exists())
            self.assertFalse((version_dir / "quote.pdf").exists())
            self.assertFalse((version_dir / "quote.xlsx").exists())
            self.assertFalse(pending_pool_path.exists())


if __name__ == "__main__":
    unittest.main()
