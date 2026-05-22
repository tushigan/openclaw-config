import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quote_skill.project import create_project, create_version, record_outputs


class ProjectTests(unittest.TestCase):
    def test_create_project_allows_precreated_empty_quote_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            quote_dir = (
                Path(tmp)
                / "workspace-business"
                / "projects"
                / "丹夫"
                / "品牌升级沟通"
                / "quote"
            )
            quote_dir.mkdir(parents=True)

            project_dir = create_project(
                None,
                client_name="丹夫",
                project_name="品牌升级沟通",
                output_mode="html_pdf",
                project_dir=quote_dir,
            )

            self.assertEqual(project_dir, quote_dir)
            self.assertTrue((quote_dir / "project.json").is_file())
            self.assertTrue((quote_dir / "versions" / "v1" / "version.json").is_file())

    def test_create_project_supports_direct_project_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            quote_dir = (
                Path(tmp)
                / "workspace-business"
                / "projects"
                / "丹夫"
                / "品牌升级沟通"
                / "quote"
            )

            project_dir = create_project(
                None,
                client_name="丹夫",
                project_name="品牌升级沟通",
                output_mode="html_pdf",
                project_dir=quote_dir,
            )

            self.assertEqual(project_dir, quote_dir)
            self.assertTrue((quote_dir / "project.json").is_file())
            self.assertTrue((quote_dir / "source-materials").is_dir())
            self.assertTrue((quote_dir / "working-notes").is_dir())
            self.assertTrue((quote_dir / "versions" / "v1" / "version.json").is_file())

    def test_create_project_builds_tree_and_project_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"

            project_dir = create_project(
                projects_root,
                client_name="丹夫",
                project_name="品牌升级报价",
                output_mode="html_pdf",
            )

            self.assertEqual(project_dir, projects_root / "丹夫" / "品牌升级报价")
            self.assertTrue((project_dir / "source-materials").is_dir())
            self.assertTrue((project_dir / "working-notes").is_dir())
            self.assertTrue((project_dir / "versions" / "v1").is_dir())
            self.assertTrue((project_dir / "versions" / "v1" / "version.json").is_file())
            self.assertTrue(
                (project_dir / "versions" / "v1" / "quote-content.json").is_file()
            )

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            version_payload = json.loads(
                (project_dir / "versions" / "v1" / "version.json").read_text(encoding="utf-8")
            )
            quote_payload = json.loads(
                (project_dir / "versions" / "v1" / "quote-content.json").read_text(encoding="utf-8")
            )

            self.assertEqual(project_payload["client_name"], "丹夫")
            self.assertEqual(project_payload["project_name"], "品牌升级报价")
            self.assertEqual(project_payload["status"], "collecting-info")
            self.assertEqual(project_payload["current_version"], "v1")
            self.assertEqual(project_payload["pricing_owner"], "human")
            self.assertEqual(project_payload["suggested_case_type"], "")
            self.assertEqual(project_payload["confirmed_case_type"], "")
            self.assertEqual(project_payload["business_goal"], "")
            self.assertEqual(project_payload["catalog_pending_summary"], [])
            self.assertEqual(project_payload["versions"], ["v1"])
            self.assertEqual(project_payload["output_mode"], "html_pdf")
            self.assertEqual(version_payload["version"], "v1")
            self.assertIsNone(version_payload["based_on"])
            self.assertEqual(version_payload["detected_new_catalog_items"], [])
            self.assertEqual(version_payload["catalog_refs_used"], [])
            self.assertIn("stages", quote_payload)
            self.assertEqual(quote_payload["case_type"], "")
            self.assertEqual(quote_payload["pending_catalog_items"], [])
            self.assertEqual(quote_payload["stages"], [])

            created_at = datetime.fromisoformat(project_payload["created_at"])
            updated_at = datetime.fromisoformat(project_payload["updated_at"])
            self.assertIsNotNone(created_at.tzinfo)
            self.assertIsNotNone(updated_at.tzinfo)

    def test_create_project_does_not_overwrite_existing_project_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"
            project_dir = create_project(
                projects_root,
                client_name="丹夫",
                project_name="品牌升级报价",
                output_mode="html_pdf",
            )

            original_project = (project_dir / "project.json").read_text(encoding="utf-8")
            original_version = (
                project_dir / "versions" / "v1" / "version.json"
            ).read_text(encoding="utf-8")
            original_quote_content = (
                project_dir / "versions" / "v1" / "quote-content.json"
            ).read_text(encoding="utf-8")

            (project_dir / "project.json").write_text('{"preserved": true}', encoding="utf-8")
            (project_dir / "versions" / "v1" / "version.json").write_text(
                '{"version": "v1", "custom": true}', encoding="utf-8"
            )
            (project_dir / "versions" / "v1" / "quote-content.json").write_text(
                '{"title": "existing"}', encoding="utf-8"
            )

            with self.assertRaises(FileExistsError):
                create_project(
                    projects_root,
                    client_name="丹夫",
                    project_name="品牌升级报价",
                    output_mode="xlsx",
                )

            self.assertEqual(
                (project_dir / "project.json").read_text(encoding="utf-8"),
                '{"preserved": true}',
            )
            self.assertEqual(
                (project_dir / "versions" / "v1" / "version.json").read_text(encoding="utf-8"),
                '{"version": "v1", "custom": true}',
            )
            self.assertEqual(
                (project_dir / "versions" / "v1" / "quote-content.json").read_text(encoding="utf-8"),
                '{"title": "existing"}',
            )
            self.assertNotEqual(original_project, '{"preserved": true}')
            self.assertNotEqual(original_version, '{"version": "v1", "custom": true}')
            self.assertNotEqual(original_quote_content, '{"title": "existing"}')

    def test_create_project_refuses_to_reinitialize_existing_project_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"
            project_dir = projects_root / "丹夫" / "品牌升级报价"
            project_dir.mkdir(parents=True)
            sentinel = project_dir / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                create_project(
                    projects_root,
                    client_name="丹夫",
                    project_name="品牌升级报价",
                    output_mode="html_pdf",
                )

            self.assertTrue(project_dir.is_dir())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_create_version_increments_to_v2_and_links_to_v1(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"
            project_dir = create_project(
                projects_root,
                client_name="丹夫",
                project_name="品牌升级报价",
                output_mode="html_pdf",
            )

            version_dir = create_version(project_dir, change_reason="根据反馈补充阶段内容")

            self.assertEqual(version_dir, project_dir / "versions" / "v2")
            self.assertTrue((version_dir / "version.json").is_file())
            self.assertTrue((version_dir / "quote-content.json").is_file())

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            version_payload = json.loads((version_dir / "version.json").read_text(encoding="utf-8"))

            self.assertEqual(project_payload["current_version"], "v2")
            self.assertEqual(project_payload["status"], "revising")
            self.assertEqual(project_payload["versions"], ["v1", "v2"])
            self.assertEqual(version_payload["version"], "v2")
            self.assertEqual(version_payload["based_on"], "v1")
            self.assertEqual(version_payload["change_reason"], "根据反馈补充阶段内容")

    def test_create_version_carries_forward_quote_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"
            project_dir = create_project(
                projects_root,
                client_name="丹夫",
                project_name="品牌升级报价",
                output_mode="html_pdf",
            )

            previous_quote_content_path = project_dir / "versions" / "v1" / "quote-content.json"
            previous_quote_content_path.write_text(
                json.dumps(
                    {
                        "title": "品牌升级报价",
                        "subtitle": "v1",
                        "overview_paragraphs": ["原始内容"],
                        "pricing_summary": {"label": "当前报价结构", "details": "A", "total": "1"},
                        "stage_plan": [{"name": "阶段一"}],
                        "stages": [
                            {
                                "stage_name": "阶段一",
                                "stage_price": "待补充",
                                "stage_duration": "待确认",
                                "stage_deliverables": ["项目交付"],
                                "projects": [],
                            }
                        ],
                        "service_sections": [],
                        "closing_notes": ["备注"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            version_dir = create_version(project_dir, change_reason="继续修订")

            self.assertEqual(
                json.loads((version_dir / "quote-content.json").read_text(encoding="utf-8")),
                json.loads(previous_quote_content_path.read_text(encoding="utf-8")),
            )

    def test_record_outputs_updates_status_and_output_file_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"
            project_dir = create_project(
                projects_root,
                client_name="丹夫",
                project_name="品牌升级报价",
                output_mode="html_pdf",
            )
            create_version(project_dir, change_reason="根据反馈补充阶段内容")

            outputs = ["versions/v2/quote.html", "versions/v2/quote.pdf"]
            record_outputs(project_dir, "v2", outputs)

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            version_payload = json.loads(
                (project_dir / "versions" / "v2" / "version.json").read_text(encoding="utf-8")
            )

            self.assertEqual(project_payload["status"], "pending-review")
            self.assertEqual(version_payload["outputs"], outputs)

    def test_record_outputs_preserves_existing_metadata_when_optional_args_not_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"
            project_dir = create_project(
                projects_root,
                client_name="丹夫",
                project_name="品牌升级报价",
                output_mode="html_pdf",
            )
            create_version(project_dir, change_reason="根据反馈补充阶段内容")

            first_outputs = ["versions/v2/quote.html"]
            first_detected = [{"proposed_task": "新任务"}]
            first_refs = ["catalog-1", "catalog-2"]
            first_pool_ids = ["pending-1"]
            record_outputs(
                project_dir,
                "v2",
                first_outputs,
                case_type="散案",
                detected_new_catalog_items=first_detected,
                catalog_refs_used=first_refs,
                pending_pool_item_ids=first_pool_ids,
            )

            second_outputs = ["versions/v2/quote.html", "versions/v2/quote.pdf"]
            record_outputs(project_dir, "v2", second_outputs)

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            version_payload = json.loads(
                (project_dir / "versions" / "v2" / "version.json").read_text(encoding="utf-8")
            )

            self.assertEqual(version_payload["outputs"], second_outputs)
            self.assertEqual(version_payload["case_type"], "散案")
            self.assertEqual(version_payload["detected_new_catalog_items"], first_detected)
            self.assertEqual(version_payload["catalog_refs_used"], first_refs)
            self.assertEqual(version_payload["pending_pool_item_ids"], first_pool_ids)
            self.assertEqual(project_payload["confirmed_case_type"], "散案")
            self.assertEqual(project_payload["catalog_pending_summary"], first_detected)

    def test_record_outputs_rejects_non_current_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects_root = Path(tmp) / "projects"
            project_dir = create_project(
                projects_root,
                client_name="丹夫",
                project_name="品牌升级报价",
                output_mode="html_pdf",
            )
            create_version(project_dir, change_reason="根据反馈补充阶段内容")

            with self.assertRaises(ValueError):
                record_outputs(project_dir, "v1", ["versions/v1/quote.pdf"])

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project_payload["status"], "revising")


if __name__ == "__main__":
    unittest.main()
