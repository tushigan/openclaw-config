import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_chat_report.py"


def load_module():
    spec = importlib.util.spec_from_file_location("export_chat_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ResolveCurrentSessionKeyTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_prefers_runtime_session_key_from_environment(self):
        session_key = "agent:design-shared:feishu:group:oc_group"
        calls = []

        def fake_run(cmd, cwd=None):
            calls.append(cmd)
            raise AssertionError("CLI should not be called when runtime session key is present")

        self.mod.run = fake_run

        resolved = self.mod.resolve_current_session_key(
            workspace=Path("/state"),
            cwd=Path("/state/workspace-design"),
            env={"OPENCLAW_MCP_SESSION_KEY": session_key},
        )

        self.assertEqual(resolved, session_key)
        self.assertEqual(calls, [])

    def test_filters_to_workspace_agent_before_global_recent_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            design_workspace = state / "workspace-design"
            design_workspace.mkdir()
            (state / "openclaw.json").write_text(
                json.dumps(
                    {
                        "agents": {
                            "list": [
                                {"id": "main", "workspace": str(state / "workspace")},
                                {"id": "design", "workspace": str(design_workspace)},
                                {"id": "design-shared", "workspace": str(design_workspace)},
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            sessions = [
                {
                    "key": "agent:main:feishu:direct:ou_admin",
                    "agentId": "main",
                    "updatedAt": 30,
                    "kind": "direct",
                },
                {
                    "key": "agent:design-shared:feishu:group:oc_group",
                    "agentId": "design-shared",
                    "updatedAt": 20,
                    "kind": "group",
                },
                {
                    "key": "agent:research-shared:feishu:group:oc_other",
                    "agentId": "research-shared",
                    "updatedAt": 25,
                    "kind": "group",
                },
            ]

            def fake_run(cmd, cwd=None):
                self.assertIn("--all-agents", cmd)
                return self.mod.subprocess.CompletedProcess(
                    cmd, 0, json.dumps({"sessions": sessions}), ""
                )

            self.mod.run = fake_run

            resolved = self.mod.resolve_current_session_key(
                workspace=state,
                cwd=design_workspace,
                env={},
            )

            self.assertEqual(resolved, "agent:design-shared:feishu:group:oc_group")

    def test_can_filter_direct_or_group_peer_when_multiple_sessions_are_active(self):
        sessions = [
            {
                "key": "agent:design-shared:feishu:group:oc_other",
                "agentId": "design-shared",
                "updatedAt": 40,
                "kind": "group",
            },
            {
                "key": "agent:design-shared:feishu:direct:ou_user",
                "agentId": "design-shared",
                "updatedAt": 30,
                "kind": "direct",
            },
            {
                "key": "agent:design-shared:feishu:group:oc_target",
                "agentId": "design-shared",
                "updatedAt": 20,
                "kind": "group",
            },
        ]

        def fake_run(cmd, cwd=None):
            return self.mod.subprocess.CompletedProcess(cmd, 0, json.dumps({"sessions": sessions}), "")

        self.mod.run = fake_run

        resolved = self.mod.resolve_current_session_key(
            workspace=Path("/state"),
            cwd=Path("/state/workspace-design"),
            env={},
            agent_id="design-shared",
            chat_type="group",
            peer_id="oc_target",
        )

        self.assertEqual(resolved, "agent:design-shared:feishu:group:oc_target")

    def test_explicit_filters_override_unmatched_environment_session(self):
        sessions = [
            {
                "key": "agent:design-shared:feishu:group:oc_target",
                "agentId": "design-shared",
                "updatedAt": 20,
                "kind": "group",
            }
        ]

        def fake_run(cmd, cwd=None):
            return self.mod.subprocess.CompletedProcess(cmd, 0, json.dumps({"sessions": sessions}), "")

        self.mod.run = fake_run

        resolved = self.mod.resolve_current_session_key(
            workspace=Path("/state"),
            cwd=Path("/state/workspace-design"),
            env={"OPENCLAW_MCP_SESSION_KEY": "agent:main:feishu:direct:ou_admin"},
            agent_id="design-shared",
            chat_type="group",
            peer_id="oc_target",
        )

        self.assertEqual(resolved, "agent:design-shared:feishu:group:oc_target")


class ReportFilenameTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_default_report_dir_points_to_openclaw_issue_summary_folder(self):
        self.assertEqual(
            self.mod.default_report_dir(),
            Path.home() / "Downloads" / "openclaw 问题汇总",
        )

    def test_report_filename_uses_timestamp_conversation_id_and_short_chinese_issue(self):
        name = self.mod.build_report_filename(
            generated_ts="20260609-012345",
            session_key="agent:design-shared:feishu:group:oc_5ec63adf29751538edd6738e36200d22",
            issue_title="群聊聊天记录导出错了",
        )

        self.assertEqual(
            name,
            "20260609-012345-oc_5ec63adf29751538edd6738e36200d22-群聊聊天记录导出.md",
        )


if __name__ == "__main__":
    unittest.main()
