#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
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
        self.module.API_URL = "https://direct.aixor.org"
        self.module.AIXOR_API_URL = "https://n.lconai.com"
        self.module.ENDPOINT_KEYS = {
            "direct.aixor.org": "primary-key",
            "n.lconai.com": "backup-key",
        }
        self.module.load_provider_state = lambda: {}

    def test_direct_aixor_remaps_gpt_image_2_pro(self) -> None:
        actual = self.module.normalize_model_for_provider("gpt-image-2-pro", "https://direct.aixor.org")
        self.assertEqual(actual, "gpt-image-2")

    def test_backup_lconai_uses_base_model_at_sub_2k(self) -> None:
        actual = self.module.normalize_model_for_provider("gpt-image-2-pro", "https://n.lconai.com", 1920, 1080)
        self.assertEqual(actual, "gpt-image-2")

    def test_backup_lconai_uses_pro_model_above_2k(self) -> None:
        actual = self.module.normalize_model_for_provider("gpt-image-2", "https://n.lconai.com", 2160, 3840)
        self.assertEqual(actual, "gpt-image-2-pro")

    def test_ratio_strings_map_to_fast_sub_2k_sizes(self) -> None:
        self.assertEqual(self.module.DEFAULT_SIZE, "1920x1080")
        self.assertEqual(self.module.normalize_size("1:1"), "1920x1920")
        self.assertEqual(self.module.normalize_size("3:4"), "1440x1920")
        self.assertEqual(self.module.normalize_size("4:5"), "1536x1920")
        self.assertEqual(self.module.normalize_size("16:9"), "1920x1080")
        self.assertEqual(self.module.normalize_size("9:16"), "1080x1920")

    def test_recent_primary_failure_prefers_backup_first(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        self.module.load_provider_state = lambda: {"primary_down_until": 9999999999}
        candidates = self.module.build_provider_candidates()
        self.assertGreaterEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["provider"], "n.lconai")
        self.assertEqual(candidates[1]["provider"], "aixor")

    def test_auto_mode_prefers_direct_aixor_then_lconai_by_default(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        self.module.load_provider_state = lambda: {}
        candidates = self.module.build_provider_candidates()
        self.assertGreaterEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["base_url"], "https://direct.aixor.org")
        self.assertEqual(candidates[1]["base_url"], "https://n.lconai.com")

    def test_auto_mode_switches_to_backup_without_retrying_primary(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        primary_error = make_http_error(
            500,
            '{"error":{"message":"正在加号请稍等","type":"invalid_request_error"}}',
        )
        call_order = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            call_order.append((base_url, model))
            if "direct.aixor.org" in base_url:
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
                ("https://direct.aixor.org", "gpt-image-2"),
                ("https://n.lconai.com", "gpt-image-2"),
            ],
        )
        self.assertEqual(meta["api_provider"], "n.lconai")
        self.assertEqual(meta["effective_model"], "gpt-image-2")

    def test_auto_mode_switches_to_backup_on_primary_timeout(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        primary_error = requests.ReadTimeout("primary timeout")
        call_order = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            call_order.append((base_url, model))
            if "direct.aixor.org" in base_url:
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
                ("https://direct.aixor.org", "gpt-image-2"),
                ("https://n.lconai.com", "gpt-image-2"),
            ],
        )
        self.assertEqual(meta["api_provider"], "n.lconai")

    def test_auto_mode_switches_to_backup_on_unavailable_primary_token(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        primary_error = make_http_error(
            401,
            '{"error":{"message":"该令牌状态不可用","type":"new_api_error"}}',
        )
        call_order = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            call_order.append((base_url, model))
            if "direct.aixor.org" in base_url:
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
                ("https://direct.aixor.org", "gpt-image-2"),
                ("https://n.lconai.com", "gpt-image-2"),
            ],
        )
        self.assertEqual(meta["api_provider"], "n.lconai")

    def test_count_gt_one_fans_out_parallel_single_requests_on_selected_provider(self) -> None:
        self.module.PROVIDER_MODE = "primary"
        calls = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            calls.append((base_url, model, n))
            return [{"b64_json": "aGVsbG8="}]

        with mock.patch.object(self.module, "call_images_generations", side_effect=fake_generations):
            items = self.module.call_images_api(
                prompt="test-parallel-count",
                image_size="1024x1024",
                reference_images=[],
                model="gpt-image-2",
                count=3,
            )

        self.assertEqual(len(items), 3)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(call == ("https://direct.aixor.org", "gpt-image-2", 1) for call in calls))

    def test_count_gt_one_switches_to_backup_and_fans_out_there_if_primary_batch_fails(self) -> None:
        self.module.PROVIDER_MODE = "auto"
        primary_error = requests.ReadTimeout("primary timeout")
        calls = []

        def fake_generations(prompt, size, model, base_url, headers, n=1):
            calls.append((base_url, model, n))
            if "direct.aixor.org" in base_url:
                raise primary_error
            return [{"b64_json": "aGVsbG8="}]

        with mock.patch.object(self.module, "call_images_generations", side_effect=fake_generations):
            with mock.patch.dict(os.environ, {"BANANA_RETRY_ATTEMPTS": "1", "BANANA_RETRY_BACKOFFS": "0"}, clear=False):
                meta = {}
                items = self.module.call_images_api(
                    prompt="test-backup-parallel-count",
                    image_size="1024x1024",
                    reference_images=[],
                    model="gpt-image-2-pro",
                    count=3,
                    invocation_meta=meta,
                )

        self.assertEqual(len(items), 3)
        primary_calls = [call for call in calls if "direct.aixor.org" in call[0]]
        backup_calls = [call for call in calls if "n.lconai.com" in call[0]]
        self.assertEqual(len(primary_calls), 3)
        self.assertEqual(len(backup_calls), 3)
        self.assertTrue(all(call[2] == 1 for call in calls))
        self.assertEqual(meta["api_provider"], "n.lconai")

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

        self.assertEqual(attempts, [("https://direct.aixor.org", "gpt-image-2")] * 3)


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

    def test_parse_runtime_context_prefers_sender_for_private_chat(self) -> None:
        context = self.module.parse_runtime_context(
            'Feishu[main]\n'
            'Conversation info (untrusted metadata):\n'
            '```json\n'
            '{"chat_id":"oc_private_chat","sender_id":"ou_owner","sender":"Owner","is_group_chat":false}\n'
            '```'
        )

        self.assertEqual(context["target"], "user:ou_owner")
        self.assertEqual(context["source_sender_open_id"], "ou_owner")

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

    def test_infer_delivery_target_from_recent_sessions_does_not_trust_sibling_manifest_for_auto_delivery(self) -> None:
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

        self.assertEqual(inferred["target"], "")
        self.assertEqual(inferred["target_source"], "sibling_manifest")
        self.assertEqual(inferred["target_conflict_reason"], "sibling_manifest_not_trusted_for_auto_delivery")
        self.assertEqual(
            {item["target"] for item in inferred["target_candidates"]},
            {"user:ou_owner"},
        )

    def test_global_images_directory_does_not_inherit_sibling_manifest_target(self) -> None:
        global_images_dir = self.root / "workspace" / "images"
        global_images_dir.mkdir(parents=True)
        self.module.WORKSPACE = self.root / "workspace"

        sibling_manifest = global_images_dir / "old_group_task.delivery.json"
        sibling_manifest.write_text(
            json.dumps(
                {
                    "project_id": "old_group_task",
                    "delivery_target": {
                        "target": "chat:oc_group",
                        "account_id": "main",
                        "target_source": "explicit_target",
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        output_path = global_images_dir / "new_private_task.png"
        output_path.write_bytes(b"png")
        inferred = self.module.infer_delivery_target_from_recent_sessions(output_path, [])

        self.assertEqual(inferred["target"], "")
        self.assertEqual(inferred["target_source"], "")
        self.assertEqual(inferred["target_conflict_reason"], "")

    def test_shared_images_output_is_rewritten_into_isolated_task_directory(self) -> None:
        self.module.WORKSPACE = self.root / "workspace"
        global_images_dir = self.module.WORKSPACE / "images"
        global_images_dir.mkdir(parents=True)
        requested_output = global_images_dir / "carton_470_270_165_ratio.png"

        actual_output = self.module.resolve_task_output_path(
            requested_output,
            delivery_target={"target": "user:ou_owner"},
            prompt="白色纸箱比例调整",
            started_at=datetime(2026, 6, 8, 2, 1, 48, tzinfo=timezone.utc),
        )

        self.assertEqual(actual_output.name, requested_output.name)
        self.assertEqual(actual_output.parent.parent, global_images_dir)
        self.assertNotEqual(actual_output.parent, global_images_dir)
        self.assertIn("carton-470-270-165-ratio", actual_output.parent.name)
        self.assertIn("ou-owner", actual_output.parent.name)

    def test_project_output_directory_is_already_isolated(self) -> None:
        self.module.WORKSPACE = self.root / "workspace"
        requested_output = self.module.WORKSPACE / "images" / "carton_project" / "ratio.png"

        actual_output = self.module.resolve_task_output_path(
            requested_output,
            delivery_target={"target": "user:ou_owner"},
            prompt="白色纸箱比例调整",
            started_at=datetime(2026, 6, 8, 2, 1, 48, tzinfo=timezone.utc),
        )

        self.assertEqual(actual_output, requested_output)

    def test_task_manifest_persists_locked_delivery_target_without_session_dependency(self) -> None:
        self.module.WORKSPACE = self.root / "workspace"
        output_path = self.module.WORKSPACE / "images" / "carton" / "ratio.png"
        delivery_target = {
            "target": "user:ou_owner",
            "user_id": "ou_owner",
            "chat_id": "",
            "account_id": "main",
            "source_session_key": "agent:main-shared:feishu:direct:ou_owner",
            "target_source": "source_session_key",
            "channel": "feishu",
        }

        manifest_path = self.module.write_task_manifest(
            output_path=output_path,
            requested_output_path=self.module.WORKSPACE / "images" / "ratio.png",
            prompt="白色纸箱比例调整",
            size="1920x1080",
            aspect="16:9",
            model="gpt-image-2",
            count=1,
            references=[],
            delivery_target=delivery_target,
            started_at=datetime(2026, 6, 8, 2, 1, 48, tzinfo=timezone.utc),
        )

        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["delivery_target"]["target"], "user:ou_owner")
        self.assertEqual(payload["delivery_target"]["target_source"], "source_session_key")
        self.assertEqual(payload["requested_output"], str(self.module.WORKSPACE / "images" / "ratio.png"))
        self.assertEqual(payload["output"], str(output_path))
        self.assertEqual(payload["target_locked"], True)

    def test_main_generates_in_isolated_directory_and_keeps_requested_alias(self) -> None:
        self.module.WORKSPACE = self.root / "workspace"
        self.module.DELIVERY_DIR = self.root / "workspace" / "feishu-deliver"
        requested_output = self.module.WORKSPACE / "images" / "shared.png"
        png_payload = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGA"
            "WjR9awAAAABJRU5ErkJggg=="
        )

        with mock.patch.object(sys, "argv", [
            str(SCRIPT_PATH),
            "--prompt",
            "demo image",
            "--size",
            "1:1",
            "--output",
            str(requested_output),
            "--feishu-user-id",
            "ou_owner",
            "--feishu-account-id",
            "main",
        ]):
            with mock.patch.object(self.module, "call_images_api", return_value=[{"b64_json": png_payload}]):
                with mock.patch.object(self.module, "validate_image_signature", return_value=None):
                    with mock.patch.object(self.module, "assert_returned_size", return_value=None):
                        with mock.patch.object(
                            self.module,
                            "send_feishu_images",
                            return_value={"ok": True, "reason": "", "sent_paths": [str(requested_output)], "results": []},
                        ):
                            exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(requested_output.exists())
        task_manifests = list((self.module.WORKSPACE / "images").glob("*/task_manifest.json"))
        self.assertEqual(len(task_manifests), 1)
        task_manifest = json.loads(task_manifests[0].read_text(encoding="utf-8"))
        self.assertEqual(task_manifest["delivery_target"]["target"], "user:ou_owner")
        self.assertNotEqual(Path(task_manifest["output"]).parent, self.module.WORKSPACE / "images")
        delivery_manifest = Path(task_manifest["delivery_manifest"])
        self.assertTrue(delivery_manifest.exists())
        delivery_payload = json.loads(delivery_manifest.read_text(encoding="utf-8"))
        self.assertEqual(delivery_payload["delivery_target"]["target"], "user:ou_owner")
        self.assertEqual(delivery_payload["delivery_status"], "sent")
        deliver_copy = self.module.DELIVERY_DIR / requested_output.name
        route_sidecar = deliver_copy.with_name(f"{deliver_copy.name}.route.json")
        self.assertTrue(route_sidecar.exists())
        route_payload = json.loads(route_sidecar.read_text(encoding="utf-8"))
        self.assertEqual(route_payload["delivery_target"]["target"], "user:ou_owner")

    def test_send_feishu_images_blocks_route_conflict_before_lark_cli(self) -> None:
        self.module.WORKSPACE = self.root / "workspace"
        deliver_dir = self.root / "workspace" / "feishu-deliver"
        deliver_dir.mkdir(parents=True)
        media = deliver_dir / "image.png"
        media.write_bytes(b"png")
        self.module.stamp_feishu_route(
            media,
            delivery_target={
                "target": "user:ou_owner",
                "account_id": "main",
                "target_source": "unit-test",
            },
            source_manifest="",
        )

        with mock.patch.object(self.module.subprocess, "run", wraps=self.module.subprocess.run) as run_mock:
            sent = self.module.send_feishu_images([media], target="chat:oc_group")

        self.assertFalse(sent["ok"])
        self.assertFalse(sent["results"][0]["sent"])
        self.assertEqual(sent["results"][0]["route_check"]["status"], "target_conflict")
        commands = [" ".join(call.args[0]) for call in run_mock.call_args_list]
        self.assertFalse(any("lark-cli" in command for command in commands))

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
