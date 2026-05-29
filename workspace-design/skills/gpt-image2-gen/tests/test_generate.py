#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest import mock

import requests


SCRIPT_PATH = Path("/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py")


def load_module():
    spec = importlib.util.spec_from_file_location("gpt_image2_generate_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_http_error(status_code: int, message: str) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    response._content = message.encode("utf-8")
    return requests.HTTPError(f"{status_code}: {message}", response=response)


class GenerateProviderRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.module.API_URL = "https://n.lconai.com"
        self.module.AIXOR_API_URL = "https://cn.aixor.org"
        self.module.ENDPOINT_KEYS = {
            "n.lconai.com": "primary-key",
            "cn.aixor.org": "backup-key",
        }
        self.module.load_provider_state = lambda: {}

    def test_aixor_remaps_gpt_image_2_pro(self) -> None:
        actual = self.module.normalize_model_for_provider("gpt-image-2-pro", "https://cn.aixor.org")
        self.assertEqual(actual, "gpt-image-2")

    def test_primary_keeps_gpt_image_2_pro(self) -> None:
        actual = self.module.normalize_model_for_provider("gpt-image-2-pro", "https://n.lconai.com")
        self.assertEqual(actual, "gpt-image-2-pro")

    def test_ratio_strings_map_to_highest_safe_sizes(self) -> None:
        self.assertEqual(self.module.DEFAULT_SIZE, "2880x2880")
        self.assertEqual(self.module.normalize_size("1:1"), "2880x2880")
        self.assertEqual(self.module.normalize_size("3:4"), "2448x3264")
        self.assertEqual(self.module.normalize_size("4:5"), "2560x3200")
        self.assertEqual(self.module.normalize_size("16:9"), "3840x2160")
        self.assertEqual(self.module.normalize_size("9:16"), "2160x3840")

    def test_recent_primary_failure_prefers_backup_first(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        self.module.load_provider_state = lambda: {"primary_down_until": 9999999999}
        candidates = self.module.build_provider_candidates()
        self.assertGreaterEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["provider"], "aixor")
        self.assertEqual(candidates[1]["provider"], "n.lconai")

    def test_auto_mode_prefers_primary_then_cn_aixor_by_default(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        self.module.load_provider_state = lambda: {}
        candidates = self.module.build_provider_candidates()
        self.assertGreaterEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["base_url"], "https://n.lconai.com")
        self.assertEqual(candidates[1]["base_url"], "https://cn.aixor.org")

    def test_auto_mode_switches_to_backup_without_retrying_primary(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        primary_error = make_http_error(
            500,
            '{"error":{"message":"正在加号请稍等","type":"invalid_request_error"}}',
        )
        call_order = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            call_order.append((base_url, model))
            if "n.lconai.com" in base_url:
                raise primary_error
            return [{"b64_json": "aGVsbG8="}]

        with mock.patch.object(self.module, "call_images_generations", side_effect=fake_generations):
            with mock.patch.dict(os.environ, {"BANANA_RETRY_ATTEMPTS": "3", "BANANA_RETRY_BACKOFFS": "0,0"}, clear=False):
                meta = {}
                items = self.module.call_images_api(
                    prompt="test",
                    image_size="1024x1024",
                    reference_images=[],
                    model="gpt-image-2-pro",
                    count=1,
                    invocation_meta=meta,
                )

        self.assertEqual(len(items), 1)
        self.assertEqual(
            call_order,
            [
                ("https://n.lconai.com", "gpt-image-2-pro"),
                ("https://cn.aixor.org", "gpt-image-2"),
            ],
        )
        self.assertEqual(meta["api_provider"], "aixor")
        self.assertEqual(meta["effective_model"], "gpt-image-2")

    def test_auto_mode_switches_to_backup_on_primary_timeout(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        primary_error = requests.ReadTimeout("primary timeout")
        call_order = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            call_order.append((base_url, model))
            if "n.lconai.com" in base_url:
                raise primary_error
            return [{"b64_json": "aGVsbG8="}]

        with mock.patch.object(self.module, "call_images_generations", side_effect=fake_generations):
            with mock.patch.dict(os.environ, {"BANANA_RETRY_ATTEMPTS": "3", "BANANA_RETRY_BACKOFFS": "0,0"}, clear=False):
                meta = {}
                items = self.module.call_images_api(
                    prompt="test-timeout",
                    image_size="1024x1024",
                    reference_images=[],
                    model="gpt-image-2-pro",
                    count=1,
                    invocation_meta=meta,
                )

        self.assertEqual(len(items), 1)
        self.assertEqual(
            call_order,
            [
                ("https://n.lconai.com", "gpt-image-2-pro"),
                ("https://cn.aixor.org", "gpt-image-2"),
            ],
        )
        self.assertEqual(meta["api_provider"], "aixor")

    def test_auto_mode_switches_to_backup_on_unavailable_primary_token(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        primary_error = make_http_error(
            401,
            '{"error":{"message":"该令牌状态不可用","type":"new_api_error"}}',
        )
        call_order = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            call_order.append((base_url, model))
            if "n.lconai.com" in base_url:
                raise primary_error
            return [{"b64_json": "aGVsbG8="}]

        with mock.patch.object(self.module, "call_images_generations", side_effect=fake_generations):
            with mock.patch.dict(os.environ, {"BANANA_RETRY_ATTEMPTS": "3", "BANANA_RETRY_BACKOFFS": "0,0"}, clear=False):
                meta = {}
                items = self.module.call_images_api(
                    prompt="test-token-unavailable",
                    image_size="1024x1024",
                    reference_images=[],
                    model="gpt-image-2-pro",
                    count=1,
                    invocation_meta=meta,
                )

        self.assertEqual(len(items), 1)
        self.assertEqual(
            call_order,
            [
                ("https://n.lconai.com", "gpt-image-2-pro"),
                ("https://cn.aixor.org", "gpt-image-2"),
            ],
        )
        self.assertEqual(meta["api_provider"], "aixor")

    def test_primary_only_still_retries_busy_errors(self) -> None:
        self.module.PROVIDER_MODE = "primary"
        primary_error = make_http_error(
            500,
            '{"error":{"message":"正在加号请稍等","type":"invalid_request_error"}}',
        )
        attempts = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            attempts.append((base_url, model))
            raise primary_error

        with mock.patch.object(self.module, "call_images_generations", side_effect=fake_generations):
            with mock.patch.dict(os.environ, {"BANANA_RETRY_ATTEMPTS": "3", "BANANA_RETRY_BACKOFFS": "0,0"}, clear=False):
                with self.assertRaises(requests.HTTPError):
                    self.module.call_images_api(
                        prompt="test",
                        image_size="1024x1024",
                        reference_images=[],
                        model="gpt-image-2-pro",
                        count=1,
                    )

        self.assertEqual(attempts, [("https://n.lconai.com", "gpt-image-2-pro")] * 3)


class GenerateCliReferenceRoleTests(unittest.TestCase):
    def test_help_lists_layout_reference_flag(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--ref-layout", result.stdout)

    def test_typed_reference_order_preserves_cli_order(self) -> None:
        module = load_module()
        args = SimpleNamespace(
            distill_id="",
            no_auto_skeleton=True,
            ref_base=[],
            ref_logo=["logo.png"],
            ref_product=["product.jpg"],
            ref_layout=[],
            ref_ip=[],
            ref_mascot=[],
            ref_style=["style.jpg"],
            ref_background=[],
            ref_typography=[],
            ref_element=[],
            reference=["skeleton.png"],
        )

        ordered = module.collect_ordered_typed_references(
            args,
            [
                "--ref-style", "style.jpg",
                "--ref-layout", "skeleton.png",
                "--ref-product", "product.jpg",
                "--ref-logo", "logo.png",
            ],
        )

        self.assertEqual(
            ordered,
            [
                ("style", "style.jpg"),
                ("layout", "skeleton.png"),
                ("product", "product.jpg"),
                ("logo", "logo.png"),
            ],
        )

        typed_for_prompt = [(idx, role, path) for idx, (role, path) in enumerate(ordered, 1)]
        role_text = module.describe_reference_roles(typed_for_prompt)
        self.assertIn("Image 1: artistic tone reference", role_text)
        self.assertIn("Image 2: layout reference", role_text)
        self.assertIn("Image 3: product reference", role_text)
        self.assertIn("Image 4: brand LOGO", role_text)


class GenerateDeliveryTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.module.AGENTS_DIR = self.root / "agents"
        self.module.AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_resolve_delivery_target_prefers_explicit_user_target(self) -> None:
        target = self.module.resolve_delivery_target(
            feishu_target="",
            feishu_user_id="ou_owner",
            feishu_chat_id="",
            feishu_account_id="main",
            source_session_key="agent:main-shared:feishu:direct:ou_owner",
        )

        self.assertEqual(
            target,
            {
                "target": "user:ou_owner",
                "user_id": "ou_owner",
                "chat_id": "",
                "account_id": "main",
                "source_session_key": "agent:main-shared:feishu:direct:ou_owner",
                "target_source": "explicit_target",
            },
        )

    def test_resolve_delivery_target_prefers_explicit_chat_target(self) -> None:
        target = self.module.resolve_delivery_target(
            feishu_target="",
            feishu_user_id="",
            feishu_chat_id="oc_group",
            feishu_account_id="default",
            source_session_key="agent:main-shared:feishu:group:oc_group",
        )

        self.assertEqual(
            target,
            {
                "target": "chat:oc_group",
                "user_id": "",
                "chat_id": "oc_group",
                "account_id": "default",
                "source_session_key": "agent:main-shared:feishu:group:oc_group",
                "target_source": "explicit_target",
            },
        )

    def test_resolve_delivery_target_keeps_explicit_target(self) -> None:
        target = self.module.resolve_delivery_target(
            feishu_target="user:ou_explicit",
            feishu_user_id="",
            feishu_chat_id="",
            feishu_account_id="main",
            source_session_key="agent:main-shared:feishu:direct:ou_explicit",
        )

        self.assertEqual(target["target"], "user:ou_explicit")
        self.assertEqual(target["user_id"], "ou_explicit")
        self.assertEqual(target["chat_id"], "")

    def test_resolve_delivery_target_derives_target_from_source_session_key(self) -> None:
        target = self.module.resolve_delivery_target(
            feishu_target="",
            feishu_user_id="",
            feishu_chat_id="",
            feishu_account_id="",
            source_session_key="agent:main-shared:feishu:direct:ou_owner",
        )

        self.assertEqual(target["target"], "user:ou_owner")
        self.assertEqual(target["user_id"], "ou_owner")
        self.assertEqual(target["target_source"], "source_session_key")

    def test_infer_delivery_target_from_recent_sessions_does_not_rebind_rerunner_dm(self) -> None:
        owner_dir = self.module.AGENTS_DIR / "main-shared" / "sessions"
        rerun_dir = self.module.AGENTS_DIR / "main" / "sessions"
        owner_dir.mkdir(parents=True)
        rerun_dir.mkdir(parents=True)

        output_path = self.root / "workspace" / "images" / "office_render_20260522" / "05_modern_tea_to_desk.png"
        output_path.parent.mkdir(parents=True)
        output_path.write_bytes(b"png")

        owner_session = owner_dir / "owner.trajectory.jsonl"
        owner_session.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "sessionKey": "agent:main-shared:feishu:direct:ou_owner",
                            "type": "tool_call",
                            "data": {
                                "command": f'python3 generate.py -o "{output_path}"',
                            },
                        },
                        ensure_ascii=False,
                    ),
                ]
            ),
            encoding="utf-8",
        )

        rerun_session = rerun_dir / "rerun.trajectory.jsonl"
        rerun_session.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "sessionKey": "agent:main:feishu:direct:ou_me",
                            "type": "tool_call",
                            "data": {
                                "command": f'python3 generate.py -o "{output_path}"',
                            },
                        },
                        ensure_ascii=False,
                    ),
                ]
            ),
            encoding="utf-8",
        )

        inferred = self.module.infer_delivery_target_from_recent_sessions(output_path, [])

        self.assertEqual(inferred.get("target", ""), "")
        self.assertEqual(inferred["target_source"], "recent_session_scan")
        self.assertEqual(
            {item["target"] for item in inferred["target_candidates"]},
            {"user:ou_owner", "user:ou_me"},
        )
        self.assertIn("conflict", inferred["target_conflict_reason"])

    def test_infer_delivery_target_from_recent_sessions_can_inherit_consistent_sibling_manifest(self) -> None:
        project_dir = self.root / "workspace" / "images" / "office_render_20260522"
        project_dir.mkdir(parents=True)
        sibling_manifest = project_dir / "04_modern_entrance.delivery.json"
        sibling_manifest.write_text(
            json.dumps(
                {
                    "project_id": "04_modern_entrance",
                    "delivery_target": {
                        "target": "user:ou_owner",
                        "account_id": "default",
                        "source_session_key": "agent:main-shared:feishu:direct:ou_owner",
                        "target_source": "explicit_target",
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        output_path = project_dir / "05_modern_tea_to_desk.png"
        output_path.write_bytes(b"png")
        inferred = self.module.infer_delivery_target_from_recent_sessions(output_path, [])

        self.assertEqual(inferred["target"], "user:ou_owner")
        self.assertEqual(inferred["account_id"], "default")
        self.assertEqual(inferred["target_source"], "sibling_manifest")

    def test_build_delivery_result_marks_pending_target_resolution_when_missing(self) -> None:
        manifest = self.module.build_delivery_result_payload(
            output_path=Path("/tmp/demo.png"),
            deliver_paths=[Path("/tmp/feishu-deliver/demo.png")],
            delivery_target={
                "target": "",
                "user_id": "",
                "chat_id": "",
                "account_id": "",
                "source_session_key": "",
                "target_source": "recent_session_scan",
            },
            sent=None,
        )

        self.assertEqual(manifest["delivery_status"], "pending_target_resolution")
        self.assertFalse(manifest["delivery_attempted"])
        self.assertTrue(manifest["fallback_required"])
        self.assertEqual(manifest["fallback_reason"], "missing_delivery_target")
        self.assertEqual(manifest["user_report"], "IMAGE GENERATED BUT TARGET NOT RESOLVED")
        self.assertEqual(manifest["target_candidates"], [])
        self.assertEqual(manifest["target_conflict_reason"], "")


if __name__ == "__main__":
    unittest.main()
