#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path("/Users/a123/.openclaw/scripts/feishu-route-guard.py")


def load_module():
    spec = importlib.util.spec_from_file_location("feishu_route_guard_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FeishuRouteGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_allows_explicit_target_when_file_has_no_route_record(self) -> None:
        media = self.root / "loose.png"
        media.write_bytes(b"png")

        result = self.module.check_media_route(media, "user:ou_owner")

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "no_route_record")

    def test_allows_matching_task_manifest_target(self) -> None:
        task_dir = self.root / "task"
        task_dir.mkdir()
        media = task_dir / "image.png"
        media.write_bytes(b"png")
        (task_dir / "task_manifest.json").write_text(
            json.dumps(
                {
                    "delivery_target": {
                        "target": "user:ou_owner",
                        "account_id": "main",
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = self.module.check_media_route(media, "user:ou_owner")

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "matched")

    def test_blocks_conflicting_route_sidecar_target(self) -> None:
        media = self.root / "image.png"
        media.write_bytes(b"png")
        self.module.write_route_sidecar(
            media,
            target="user:ou_owner",
            account_id="main",
            source="unit-test",
            source_manifest="",
        )

        result = self.module.check_media_route(media, "chat:oc_group")

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "target_conflict")
        self.assertEqual(result["requested_target"], "chat:oc_group")
        self.assertEqual(result["recorded_targets"], ["user:ou_owner"])

    def test_allows_manifest_that_exists_without_target(self) -> None:
        task_dir = self.root / "task"
        task_dir.mkdir()
        media = task_dir / "image.png"
        media.write_bytes(b"png")
        (task_dir / "task_manifest.json").write_text(
            json.dumps({"delivery_target": {"target": ""}}, ensure_ascii=False),
            encoding="utf-8",
        )

        result = self.module.check_media_route(media, "user:ou_owner")

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "no_actionable_route_record")

    def test_blocks_conflicting_targets_across_route_records(self) -> None:
        task_dir = self.root / "task"
        task_dir.mkdir()
        media = task_dir / "image.png"
        media.write_bytes(b"png")
        self.module.write_route_sidecar(
            media,
            target="user:ou_owner",
            account_id="main",
            source="unit-test",
            source_manifest="",
        )
        media.with_name("image.delivery.json").write_text(
            json.dumps({"delivery_target": {"target": "chat:oc_group"}}, ensure_ascii=False),
            encoding="utf-8",
        )

        result = self.module.check_media_route(media, "chat:oc_group")

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "route_record_target_conflict")
        self.assertEqual(result["recorded_targets"], ["chat:oc_group", "user:ou_owner"])

    def test_ignores_shared_feishu_deliver_task_manifest_for_loose_media(self) -> None:
        deliver_dir = self.root / "workspace" / "feishu-deliver"
        deliver_dir.mkdir(parents=True)
        media = deliver_dir / "image.png"
        media.write_bytes(b"png")
        (deliver_dir / "task_manifest.json").write_text(
            json.dumps({"delivery_target": {"target": "chat:oc_old_group"}}, ensure_ascii=False),
            encoding="utf-8",
        )

        result = self.module.check_media_route(media, "user:ou_owner")

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "no_route_record")


if __name__ == "__main__":
    unittest.main()
