#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path("/Users/a123/.openclaw/scripts/audit-feedback-gaps.py")


def load_module():
    spec = importlib.util.spec_from_file_location("audit_feedback_gaps_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AuditFeedbackGapsTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registry_session_context_keeps_user_target(self) -> None:
        registry_path = self.root / "conversation-ids.json"
        session_path = self.root / "owner-session.jsonl"
        registry_path.write_text(
            json.dumps(
                {
                    "sessions": {
                        str(session_path): {
                            "accountId": "default",
                            "chatId": "user:ou_owner",
                            "target": "user:ou_owner",
                            "senderOpenId": "ou_owner",
                            "lastSeenAt": "2026-05-22T06:31:56.217Z",
                        }
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.module.FEISHU_ID_REGISTRY = registry_path
        context = self.module.registry_session_context(session_path)

        self.assertEqual(context["target"], "user:ou_owner")
        self.assertEqual(context["account_id"], "default")
        self.assertEqual(context["target_source"], "feishu_id_registry")

    def test_session_chat_context_parses_user_target_and_owner(self) -> None:
        records = [
            {
                "customType": "openclaw.runtime-context",
                "content": (
                    'System: [2026-05-22 14:31:53 GMT+8] Feishu[default] DM | 林翀 (ou_owner) [msg:om_xxx]\n'
                    'Conversation info (untrusted metadata):\n'
                    '```json\n'
                    '{\n'
                    '  "chat_id": "user:ou_owner",\n'
                    '  "sender_id": "ou_owner",\n'
                    '  "sender": "林翀"\n'
                    '}\n'
                    '```'
                ),
            }
        ]

        context = self.module.session_chat_context(records)

        self.assertEqual(context["target"], "user:ou_owner")
        self.assertEqual(context["account_id"], "default")
        self.assertEqual(context["source_sender_open_id"], "ou_owner")
        self.assertEqual(context["source_sender_name"], "林翀")

    def test_infer_chat_for_paths_returns_owner_fields_for_direct_message(self) -> None:
        agents_dir = self.root / "agents"
        session_dir = agents_dir / "main-shared" / "sessions"
        session_dir.mkdir(parents=True)
        session_path = session_dir / "owner-session.jsonl"
        session_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "customType": "openclaw.runtime-context",
                            "content": (
                                'System: Feishu[default] DM\n'
                                '```json\n'
                                '{\n'
                                '  "chat_id": "user:ou_owner",\n'
                                '  "sender_id": "ou_owner",\n'
                                '  "sender": "林翀"\n'
                                '}\n'
                                '```'
                            ),
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "type": "message",
                            "message": {
                                "content": [
                                    {
                                        "type": "toolCall",
                                        "name": "exec",
                                        "arguments": {
                                            "command": "cp /tmp/01_chinese_entrance.png /tmp/feishu-deliver/01_chinese_entrance.png"
                                        },
                                    }
                                ]
                            },
                        },
                        ensure_ascii=False,
                    ),
                ]
            ),
            encoding="utf-8",
        )

        self.module.AGENTS_DIR = agents_dir
        context = self.module.infer_chat_for_paths(["/tmp/01_chinese_entrance.png"])

        self.assertEqual(context["target"], "user:ou_owner")
        self.assertEqual(context["account_id"], "default")
        self.assertEqual(context["source_sender_open_id"], "ou_owner")
        self.assertEqual(context["source_sender_name"], "林翀")
        self.assertEqual(context["source_session_file"], str(session_path))

    def test_infer_chat_for_paths_prefers_owner_trajectory_over_later_complaint_session(self) -> None:
        agents_dir = self.root / "agents"
        owner_dir = agents_dir / "main-shared" / "sessions"
        complaint_dir = agents_dir / "main" / "sessions"
        owner_dir.mkdir(parents=True)
        complaint_dir.mkdir(parents=True)

        image_path = "/tmp/01_chinese_entrance.png"
        owner_session_key = "agent:main-shared:feishu:direct:ou_owner"
        owner_registry_path = owner_dir / "owner-session.jsonl"
        registry_path = self.root / "conversation-ids.json"
        registry_path.write_text(
            json.dumps(
                {
                    "sessions": {
                        owner_session_key: {
                            "accountId": "default",
                            "chatId": "user:ou_owner",
                            "target": "user:ou_owner",
                            "senderOpenId": "ou_owner",
                        },
                        str(owner_registry_path): {
                            "accountId": "default",
                            "chatId": "user:ou_owner",
                            "target": "user:ou_owner",
                            "senderOpenId": "ou_owner",
                        },
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.module.FEISHU_ID_REGISTRY = registry_path

        owner_trajectory = owner_dir / "owner-session.trajectory.jsonl"
        owner_trajectory.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "sessionKey": owner_session_key,
                            "type": "context.compiled",
                            "data": {
                                "messagesSnapshot": [
                                    {
                                        "role": "custom",
                                        "customType": "openclaw.runtime-context",
                                        "content": (
                                            'System: Feishu[default] DM\n'
                                            '```json\n'
                                            '{\n'
                                            '  "chat_id": "user:ou_owner",\n'
                                            '  "sender_id": "ou_owner",\n'
                                            '  "sender": "林翀"\n'
                                            '}\n'
                                            '```'
                                        ),
                                    }
                                ]
                            },
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "sessionKey": owner_session_key,
                            "type": "tool_call",
                            "data": {
                                "command": f'python3 generate.py -o "{image_path}"',
                            },
                        },
                        ensure_ascii=False,
                    ),
                ]
            ),
            encoding="utf-8",
        )

        complaint_session = complaint_dir / "complaint-session.jsonl"
        complaint_session.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "customType": "openclaw.runtime-context",
                            "content": (
                                'System: Feishu[default] DM\n'
                                '```json\n'
                                '{\n'
                                '  "chat_id": "user:ou_me",\n'
                                '  "sender_id": "ou_me",\n'
                                '  "sender": "涂是淦"\n'
                                '}\n'
                                '```'
                            ),
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "type": "message",
                            "message": {
                                "content": [
                                    {
                                        "type": "toolCall",
                                        "name": "exec",
                                        "arguments": {
                                            "command": f"cat {image_path}"
                                        },
                                    }
                                ]
                            },
                        },
                        ensure_ascii=False,
                    ),
                ]
            ),
            encoding="utf-8",
        )

        self.module.AGENTS_DIR = agents_dir
        context = self.module.infer_chat_for_paths([image_path])

        self.assertEqual(context["target"], "user:ou_owner")
        self.assertEqual(context["source_sender_open_id"], "ou_owner")
        self.assertEqual(context["source_sender_name"], "林翀")
        self.assertTrue(context["source_session_file"].endswith(".trajectory.jsonl"))

    def test_is_cron_session_path_detects_session_id_even_when_beyond_first_2kb(self) -> None:
        cron_runs_dir = self.root / "cron" / "runs"
        cron_runs_dir.mkdir(parents=True)
        run_file = cron_runs_dir / "job.jsonl"
        run_file.write_text(
            json.dumps(
                {
                    "summary": "x" * 3000,
                    "sessionId": "252c4b70-3976-4409-9e23-97171801f03d",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.module.CRON_RUNS_DIR = cron_runs_dir

        session_path = self.root / "agents" / "main" / "sessions" / "252c4b70-3976-4409-9e23-97171801f03d.trajectory.jsonl"
        session_path.parent.mkdir(parents=True)
        session_path.write_text("", encoding="utf-8")

        self.assertTrue(self.module._is_cron_session_path(session_path))

    def test_infer_chat_for_paths_ignores_cron_replay_session(self) -> None:
        agents_dir = self.root / "agents"
        owner_dir = agents_dir / "main-shared" / "sessions"
        cron_dir = agents_dir / "main" / "sessions"
        owner_dir.mkdir(parents=True)
        cron_dir.mkdir(parents=True)
        cron_runs_dir = self.root / "cron" / "runs"
        cron_runs_dir.mkdir(parents=True)
        self.module.CRON_RUNS_DIR = cron_runs_dir

        image_path = "/tmp/10_modern_strict_entrance.png"
        owner_session_key = "agent:main-shared:feishu:direct:ou_owner"
        owner_trajectory = owner_dir / "owner.trajectory.jsonl"
        owner_trajectory.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "sessionKey": owner_session_key,
                            "type": "context.compiled",
                            "data": {
                                "messagesSnapshot": [
                                    {
                                        "role": "custom",
                                        "customType": "openclaw.runtime-context",
                                        "content": (
                                            'System: Feishu[default] DM\n'
                                            '```json\n'
                                            '{\n'
                                            '  "chat_id": "user:ou_owner",\n'
                                            '  "sender_id": "ou_owner",\n'
                                            '  "sender": "林翀"\n'
                                            '}\n'
                                            '```'
                                        ),
                                    }
                                ]
                            },
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "sessionKey": owner_session_key,
                            "type": "tool_call",
                            "data": {"command": f'python3 generate.py -o "{image_path}"'},
                        },
                        ensure_ascii=False,
                    ),
                ]
            ),
            encoding="utf-8",
        )

        cron_session_id = "252c4b70-3976-4409-9e23-97171801f03d"
        (cron_runs_dir / "job.jsonl").write_text(
            json.dumps({"sessionId": cron_session_id}, ensure_ascii=False),
            encoding="utf-8",
        )
        cron_trajectory = cron_dir / f"{cron_session_id}.trajectory.jsonl"
        cron_trajectory.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "sessionKey": f"agent:main:cron:job:run:{cron_session_id}",
                            "type": "tool_result",
                            "data": {
                                "text": json.dumps(
                                    {
                                        "path": image_path,
                                        "target": "user:ou_me",
                                    },
                                    ensure_ascii=False,
                                )
                            },
                        },
                        ensure_ascii=False,
                    ),
                ]
            ),
            encoding="utf-8",
        )

        self.module.AGENTS_DIR = agents_dir
        context = self.module.infer_chat_for_paths([image_path])

        self.assertEqual(context["target"], "user:ou_owner")
        self.assertTrue(context["source_session_file"].endswith("owner.trajectory.jsonl"))

    def test_infer_chat_for_paths_downgrades_conflicting_target_and_sender(self) -> None:
        agents_dir = self.root / "agents"
        session_dir = agents_dir / "main" / "sessions"
        session_dir.mkdir(parents=True)
        session_path = session_dir / "conflict.jsonl"
        session_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "customType": "openclaw.runtime-context",
                            "content": (
                                'System: Feishu[main] DM\n'
                                '```json\n'
                                '{\n'
                                '  "chat_id": "user:ou_me",\n'
                                '  "sender_id": "ou_me",\n'
                                '  "sender": "涂是淦"\n'
                                '}\n'
                                '```'
                            ),
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "type": "message",
                            "message": {
                                "content": [
                                    {
                                        "type": "toolCall",
                                        "name": "message",
                                        "arguments": {
                                            "target": "user:ou_owner",
                                            "media": "/tmp/10_modern_strict_entrance.png",
                                        },
                                    }
                                ]
                            },
                        },
                        ensure_ascii=False,
                    ),
                ]
            ),
            encoding="utf-8",
        )

        self.module.AGENTS_DIR = agents_dir
        context = self.module.infer_chat_for_paths(["/tmp/10_modern_strict_entrance.png"])

        self.assertEqual(context["target"], "user:ou_owner")
        self.assertFalse(context["target_resolved"])
        self.assertEqual(context["target_confidence"], "low")
        self.assertIn("conflict", context["target_conflict_reason"])

    def test_sibling_manifest_target_is_not_auto_sendable(self) -> None:
        context = self.module.finalize_target_context(
            {
                "target": "chat:oc_old_group",
                "account_id": "main",
                "target_source": "sibling_manifest",
            }
        )

        self.assertEqual(context["target"], "chat:oc_old_group")
        self.assertEqual(context["target_confidence"], "low")
        self.assertFalse(context["auto_send_allowed"])
        self.assertEqual(context["auto_send_block_reason"], "target_missing_or_low_confidence")

    def test_audit_delivery_manifest_includes_fallback_owner_summary(self) -> None:
        images_dir = self.root / "workspace" / "images"
        images_dir.mkdir(parents=True)
        image_path = images_dir / "01_chinese_entrance.png"
        image_path.write_bytes(b"png")
        manifest_path = images_dir / "01_chinese_entrance.delivery.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "project_id": "01_chinese_entrance",
                    "original_image": str(image_path),
                    "delivery_status": "pending_target_resolution",
                    "delivery_attempted": False,
                    "delivery_target": {
                        "target": "",
                        "user_id": "",
                        "chat_id": "",
                    },
                    "deliverables": {
                        "images": [str(image_path)],
                    },
                    "fallback_reason": "missing_delivery_target",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.module.GENERIC_DELIVERY_DIRS = [images_dir]
        self.module.PROJECTS_DIR = self.root / "workspace" / "brand-poster-projects"
        with mock.patch.object(self.module, "find_message_delivery_evidence", return_value=None):
            with mock.patch.object(
                self.module,
                "infer_chat_for_paths",
                return_value={
                    "target": "",
                    "account_id": "",
                    "source_sender_open_id": "ou_owner",
                    "source_sender_name": "林翀",
                    "source_session_file": "/tmp/owner-session.jsonl",
                    "target_source": "session_runtime_context",
                },
            ):
                findings = self.module.audit_delivery_manifests(limit=10, cutoff=None)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["fallback_owner_summary"], "林翀 (ou_owner)")
        self.assertEqual(findings[0]["source_sender_name"], "林翀")
        self.assertEqual(findings[0]["target_resolved"], False)
        self.assertFalse(findings[0]["fallback_blocked"])

    def test_audit_delivery_manifest_blocks_auto_send_when_media_route_conflicts(self) -> None:
        images_dir = self.root / "workspace" / "images" / "task"
        images_dir.mkdir(parents=True)
        image_path = images_dir / "result.png"
        image_path.write_bytes(b"png")
        (images_dir / "result.png.route.json").write_text(
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
        manifest_path = images_dir / "result.delivery.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "project_id": "route_conflict",
                    "original_image": str(image_path),
                    "delivery_status": "failed",
                    "delivery_attempted": True,
                    "delivery_target": {
                        "target": "chat:oc_group",
                        "account_id": "main",
                        "target_source": "manifest_delivery_target",
                    },
                    "deliverables": {
                        "images": [str(image_path)],
                    },
                    "fallback_reason": "send failed",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.module.GENERIC_DELIVERY_DIRS = [self.root / "workspace" / "images"]
        self.module.PROJECTS_DIR = self.root / "workspace" / "brand-poster-projects"
        with mock.patch.object(self.module, "find_message_delivery_evidence", return_value=None):
            findings = self.module.audit_delivery_manifests(limit=10, cutoff=None)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["target"], "chat:oc_group")
        self.assertFalse(findings[0]["auto_send_allowed"])
        self.assertEqual(findings[0]["auto_send_block_reason"], "media_route_route_record_target_conflict")
        self.assertEqual(findings[0]["media_route_guard"]["recorded_targets"], ["chat:oc_group", "user:ou_owner"])


if __name__ == "__main__":
    unittest.main()
