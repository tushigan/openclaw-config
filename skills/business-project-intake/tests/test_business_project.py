import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from business_project.project import (
    archive_material,
    create_business_project,
    prepare_quote_handoff,
    sync_quote_state,
)


class BusinessProjectTests(unittest.TestCase):
    def test_create_business_project_builds_full_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-business"
            source_file = workspace_root / "incoming" / "brief.txt"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.write_text("客户想先梳理需求，再决定是否报价。", encoding="utf-8")

            project_dir = create_business_project(
                workspace_root=workspace_root,
                client_name="丹夫",
                project_name="品牌升级沟通",
                current_goal="梳理需求边界",
                source_materials=[
                    {
                        "type": "doc",
                        "path": str(source_file),
                        "title": "初始需求简述",
                        "source_channel": "feishu",
                    }
                ],
            )

            self.assertEqual(
                project_dir,
                workspace_root / "projects" / "丹夫" / "品牌升级沟通",
            )
            self.assertTrue((project_dir / "project.json").is_file())
            self.assertTrue((project_dir / "materials.json").is_file())
            self.assertTrue((project_dir / "progress.json").is_file())
            self.assertTrue((project_dir / "tasks.json").is_file())
            self.assertTrue((project_dir / "quote-handoff.json").is_file())
            self.assertTrue((project_dir / "materials" / "audio").is_dir())
            self.assertTrue((project_dir / "materials" / "images").is_dir())
            self.assertTrue((project_dir / "materials" / "docs").is_dir())
            self.assertTrue((project_dir / "materials" / "chat").is_dir())
            self.assertTrue((project_dir / "notes" / "meeting-notes").is_dir())
            self.assertTrue((project_dir / "outputs" / "handoff").is_dir())
            self.assertTrue((project_dir / "quote").is_dir())

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            materials_payload = json.loads((project_dir / "materials.json").read_text(encoding="utf-8"))
            progress_payload = json.loads((project_dir / "progress.json").read_text(encoding="utf-8"))
            handoff_payload = json.loads(
                (project_dir / "quote-handoff.json").read_text(encoding="utf-8")
            )

            self.assertEqual(project_payload["client_name"], "丹夫")
            self.assertEqual(project_payload["project_name"], "品牌升级沟通")
            self.assertEqual(project_payload["current_stage"], "线索")
            self.assertEqual(project_payload["lifecycle_status"], "active")
            self.assertEqual(project_payload["current_goal"], "梳理需求边界")
            self.assertEqual(project_payload["quote_status"], "not-ready")
            self.assertEqual(project_payload["material_count"], 1)
            self.assertEqual(len(materials_payload["items"]), 1)
            self.assertEqual(progress_payload["entries"][0]["event_type"], "intake")
            self.assertEqual(handoff_payload["handoff_status"], "draft")
            self.assertEqual(handoff_payload["quote_project_dir"], str(project_dir / "quote"))

    def test_archive_material_copies_file_and_updates_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-business"
            source_file = workspace_root / "incoming" / "photo.jpg"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.write_bytes(b"fake-image")

            project_dir = create_business_project(
                workspace_root=workspace_root,
                client_name="丹夫",
                project_name="品牌升级沟通",
                current_goal="梳理需求边界",
                source_materials=[
                    {
                        "type": "doc",
                        "path": str(source_file),
                        "title": "占位材料",
                        "source_channel": "feishu",
                    }
                ],
            )

            record = archive_material(
                project_dir=project_dir,
                source_path=source_file,
                material_type="image",
                title="现场拍照",
                source_channel="feishu",
            )

            self.assertEqual(record["type"], "image")
            self.assertEqual(record["processing_status"], "copied")
            self.assertTrue(Path(record["stored_path"]).is_file())

            materials_payload = json.loads((project_dir / "materials.json").read_text(encoding="utf-8"))
            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))

            self.assertEqual(len(materials_payload["items"]), 2)
            self.assertEqual(project_payload["material_count"], 2)
            self.assertEqual(project_payload["latest_material_id"], record["material_id"])

    def test_prepare_quote_handoff_marks_project_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-business"
            source_file = workspace_root / "incoming" / "brief.txt"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.write_text("范围已确认，可以准备报价。", encoding="utf-8")

            project_dir = create_business_project(
                workspace_root=workspace_root,
                client_name="丹夫",
                project_name="品牌升级沟通",
                current_goal="梳理需求边界",
                source_materials=[
                    {
                        "type": "doc",
                        "path": str(source_file),
                        "title": "初始需求简述",
                        "source_channel": "feishu",
                    }
                ],
            )

            handoff = prepare_quote_handoff(
                project_dir=project_dir,
                trigger_reason="用户明确要求开始报价",
                recommended_case_type="项目案",
                confirmed_scope=["品牌策略", "包装方向"],
                excluded_scope=["拍摄执行"],
            )

            self.assertEqual(handoff["handoff_status"], "ready")
            self.assertEqual(handoff["recommended_case_type"], "项目案")
            self.assertEqual(handoff["confirmed_scope"], ["品牌策略", "包装方向"])
            self.assertEqual(handoff["excluded_scope"], ["拍摄执行"])

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project_payload["quote_status"], "ready")
            self.assertEqual(project_payload["quote_project_dir"], str(project_dir / "quote"))

    def test_sync_quote_state_updates_parent_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-business"
            source_file = workspace_root / "incoming" / "brief.txt"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.write_text("进入报价阶段。", encoding="utf-8")

            project_dir = create_business_project(
                workspace_root=workspace_root,
                client_name="丹夫",
                project_name="品牌升级沟通",
                current_goal="梳理需求边界",
                source_materials=[
                    {
                        "type": "doc",
                        "path": str(source_file),
                        "title": "初始需求简述",
                        "source_channel": "feishu",
                    }
                ],
            )

            prepare_quote_handoff(
                project_dir=project_dir,
                trigger_reason="用户明确要求开始报价",
                recommended_case_type="项目案",
            )

            sync_quote_state(
                project_dir=project_dir,
                quote_version="v1",
                output_refs=["quote/versions/v1/quote.html", "quote/versions/v1/quote.xlsx"],
            )

            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            progress_payload = json.loads((project_dir / "progress.json").read_text(encoding="utf-8"))
            tasks_payload = json.loads((project_dir / "tasks.json").read_text(encoding="utf-8"))
            handoff_payload = json.loads(
                (project_dir / "quote-handoff.json").read_text(encoding="utf-8")
            )

            self.assertEqual(project_payload["quote_status"], "quoted")
            self.assertEqual(project_payload["current_quote_version"], "v1")
            self.assertEqual(project_payload["current_stage"], "报价中")
            self.assertEqual(handoff_payload["handoff_status"], "quoted")
            self.assertEqual(handoff_payload["current_quote_version"], "v1")
            self.assertEqual(
                handoff_payload["quote_output_refs"],
                ["quote/versions/v1/quote.html", "quote/versions/v1/quote.xlsx"],
            )
            self.assertEqual(progress_payload["entries"][-1]["event_type"], "quote-sent")
            self.assertEqual(tasks_payload["tasks"][-1]["title"], "跟进本轮报价反馈")


if __name__ == "__main__":
    unittest.main()
