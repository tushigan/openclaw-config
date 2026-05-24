import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import init_internal_interview_project as init_project_script  # type: ignore
import internal_interview_research.project as project_module  # type: ignore
from internal_interview_research.project import (  # type: ignore
    analyze_project,
    advance_project,
    build_chain_acceptance_test_plan,
    build_dispatch_plan,
    build_parallel_chain_acceptance_test_plan,
    build_final_delivery_payload,
    build_participant_outreach_plan,
    close_project,
    create_internal_interview_project,
    finalize_project_on_deadline,
    evaluate_project_actions,
    ingest_participant_reply,
    mark_delivery_complete,
    prepare_feishu_delivery,
    repair_project_participants,
    recover_project_replies,
    register_project_check_job,
    stop_project_and_cleanup,
    update_participant,
    update_project_deadline,
)


def _ts(hours_offset: int = 0) -> str:
    return (datetime.now().astimezone() + timedelta(hours=hours_offset)).isoformat()


def _verified_binding_kwargs(open_id, session_key, confirmed_at=None):
    return {
        "conversation_binding_id": f"research:{open_id}",
        "conversation_binding_status": "已绑定",
        "binding_confirmed_at": confirmed_at or _ts(),
        "binding_confirmation_evidence": f"status 校验通过：{open_id} -> {session_key}",
        "binding_target_session_key": session_key,
        "binding_check_result": "已核验通过",
    }


class InternalInterviewResearchTests(unittest.TestCase):
    def test_init_script_parse_participant_keeps_user_openid_and_reason(self):
        parsed = init_project_script._parse_participant("张三:user:ou_123abc:龙虾内测群成员")

        self.assertEqual(parsed["姓名"], "张三")
        self.assertEqual(parsed["飞书标识"], "user:ou_123abc")
        self.assertEqual(parsed["纳入原因"], "龙虾内测群成员")

    def test_init_script_parse_participant_accepts_raw_openid_and_normalizes_to_user_target(self):
        parsed = init_project_script._parse_participant("张三:ou_123abc:龙虾内测群成员")

        self.assertEqual(parsed["飞书标识"], "user:ou_123abc")

    def test_init_script_parse_participant_rejects_invalid_feishu_target(self):
        with self.assertRaises(ValueError):
            init_project_script._parse_participant("张三:user:龙虾内测群成员")

    def test_create_project_builds_chinese_files_and_direct_participants(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"

            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="组织协作访谈",
                initiator_name="李经理",
                initiator_feishu_id="user:ou_initiator",
                research_goal="了解跨部门协作中的信息断点",
                research_scope="产品、销售、交付三方的协作体验",
                participant_source_mode="直接名单",
                participant_scope_text="核心参与人",
                project_deadline_at=_ts(hours_offset=48),
                participants=[
                    {"姓名": "张三", "飞书标识": "user:ou_zhangsan", "纳入原因": "销售代表"},
                    {"姓名": "李四", "飞书标识": "user:ou_lisi", "纳入原因": "产品经理"},
                ],
            )

            self.assertEqual(project_dir, workspace_root / "projects" / "组织协作访谈")
            self.assertTrue((project_dir / "项目总表.yaml").is_file())
            self.assertTrue((project_dir / "受访对象清单.yaml").is_file())
            self.assertTrue((project_dir / "发起人访谈纪要.md").is_file())
            self.assertTrue((project_dir / "调研问题清单.md").is_file())
            self.assertTrue((project_dir / "阶段总结.md").is_file())
            self.assertTrue((project_dir / "最终调研报告.md").is_file())
            self.assertTrue((project_dir / "访谈记录").is_dir())

            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))

            self.assertEqual(project_payload["项目名称"], "组织协作访谈")
            self.assertEqual(project_payload["发起人"]["姓名"], "李经理")
            self.assertEqual(project_payload["受访对象来源方式"], "直接名单")
            self.assertTrue(project_payload["是否可进入自动访谈"])
            self.assertEqual(project_payload["样本概况"]["总人数"], 2)
            self.assertEqual(project_payload["项目类型"], "真实调研")
            self.assertEqual(participants_payload["受访对象列表"][0]["当前状态"], "待创建会话")
            self.assertEqual(project_payload["运行模式"], "真实调研")
            self.assertEqual(project_payload["访谈执行设置"]["发送账号标识"], "research")
            self.assertTrue(project_payload["访谈执行设置"]["禁止使用用户身份发送"])
            self.assertEqual(project_payload["访谈策略"]["默认提问方式"], "判断题优先")
            self.assertEqual(project_payload["访谈策略"]["默认交互形态"], "文本选择题")
            self.assertEqual(project_payload["访谈策略"]["首轮结构"], "说明消息+1个短文本选择题")
            self.assertTrue(project_payload["访谈策略"]["卡片模式已禁用"])
            self.assertEqual(project_payload["派发策略"]["派发模式"], "一次性全发")
            self.assertEqual(project_payload["派发策略"]["每批人数"], 10)
            self.assertEqual(project_payload["访谈策略"]["单人有效问题上限"], 4)
            self.assertEqual(project_payload["执行架构"]["发起代理"], "research")
            self.assertEqual(project_payload["执行架构"]["访谈代理"], "research-shared")
            self.assertEqual(project_payload["执行架构"]["会话粒度"], "每人一会话")
            self.assertEqual(project_payload["巡检设置"]["推进任务ID"], "")
            self.assertEqual(project_payload["巡检设置"]["汇报任务ID"], "")
            self.assertEqual(project_payload["最终交付信息"]["冻结观察期小时"], 48)
            self.assertEqual(project_payload["最终交付信息"]["冻结观察截止时间"], "")
            self.assertEqual(participants_payload["受访对象列表"][0]["最近一次提问方式"], "")
            self.assertEqual(participants_payload["受访对象列表"][0]["累计按钮题次数"], 0)
            self.assertEqual(participants_payload["受访对象列表"][0]["累计选择题次数"], 0)
            self.assertEqual(participants_payload["受访对象列表"][0]["累计开放题次数"], 0)
            self.assertEqual(participants_payload["受访对象列表"][0]["执行会话代理"], "research-shared")
            self.assertEqual(participants_payload["受访对象列表"][0]["会话绑定状态"], "未绑定")
            self.assertFalse(participants_payload["受访对象列表"][0]["是否已回收至research"])
            self.assertEqual(participants_payload["受访对象列表"][0]["最近一次发送chatID"], "")
            self.assertEqual(participants_payload["受访对象列表"][0]["最近一次发送确认状态"], "")
            self.assertEqual(participants_payload["受访对象列表"][0]["最近一次发送确认时间"], "")
            self.assertEqual(participants_payload["受访对象列表"][0]["最近一次发送确认依据"], "")

    def test_create_project_normalizes_participant_feishu_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="飞书标识标准化",
                initiator_name="李经理",
                initiator_feishu_id="user:ou_initiator",
                research_goal="验证飞书标识标准化",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "张三", "飞书标识": "ou_zhangsan", "纳入原因": "销售"}],
            )

            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]

            self.assertEqual(participant["飞书标识"], "user:ou_zhangsan")

    def test_create_project_rejects_invalid_participant_feishu_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"

            with self.assertRaises(ValueError):
                create_internal_interview_project(
                    workspace_root=workspace_root,
                    project_name="非法飞书标识",
                    initiator_name="李经理",
                    initiator_feishu_id="user:ou_initiator",
                    research_goal="验证飞书标识校验",
                    research_scope="单人",
                    participant_source_mode="直接名单",
                    participant_scope_text="单人",
                    project_deadline_at=_ts(hours_offset=24),
                    participants=[{"姓名": "张三", "飞书标识": "user", "纳入原因": "销售"}],
                )

    def test_create_project_with_scope_mode_marks_suggestions_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"

            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="新人融入访谈",
                initiator_name="王总监",
                initiator_feishu_id="user:ou_director",
                research_goal="了解新员工试用期融入体验",
                research_scope="最近三个月入职的新员工与其直属主管",
                participant_source_mode="范围建议",
                participant_scope_text="最近三个月入职的新员工、直属主管各 3 人",
                project_deadline_at=_ts(hours_offset=72),
                participants=[],
            )

            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))

            self.assertEqual(project_payload["受访对象来源方式"], "范围建议")
            self.assertTrue(project_payload["建议名单待确认"])
            self.assertFalse(project_payload["是否可直接开始批量访谈"])

    def test_project_without_deadline_blocks_automatic_interview_until_updated(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"

            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="反馈流程访谈",
                initiator_name="赵经理",
                initiator_feishu_id="user:ou_zhao",
                research_goal="了解需求反馈流程体验",
                research_scope="设计、产品、运营协作流程",
                participant_source_mode="直接名单",
                participant_scope_text="核心协作人",
                project_deadline_at="",
                participants=[{"姓名": "周五", "飞书标识": "user:ou_zhou", "纳入原因": "运营"}],
            )

            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))
            self.assertFalse(project_payload["是否可进入自动访谈"])

            update_project_deadline(
                project_dir=project_dir,
                new_deadline_at=_ts(hours_offset=24),
                changed_by="赵经理",
                reason="补充正式截止时间",
            )

            updated_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))
            self.assertTrue(updated_payload["是否可进入自动访谈"])
            self.assertEqual(len(updated_payload["截止时间变更记录"]), 1)

    def test_evaluate_project_actions_triggers_followups(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="协作阻塞点访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="识别协作阻塞点",
                research_scope="跨部门流程",
                participant_source_mode="直接名单",
                participant_scope_text="核心协作人",
                project_deadline_at=_ts(hours_offset=30),
                participants=[{"姓名": "吴一", "飞书标识": "user:ou_wuyi", "纳入原因": "交付"}],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="吴一",
                status="待回复",
                last_outbound_at=_ts(hours_offset=-7),
                followup_count=0,
                execution_session_id="session-wuyi",
                execution_session_key="research-shared-xietong-wuyi",
                **_verified_binding_kwargs("ou_wuyi", "research-shared-xietong-wuyi"),
                last_message_id="om_wuyi_1",
                last_chat_id="oc_wuyi_1",
                send_confirmation_status="已调用发送",
            )
            actions = evaluate_project_actions(project_dir=project_dir, now_at=_ts())
            self.assertEqual(actions["受访对象动作"][0]["建议动作"], "第一次跟进")

            update_participant(
                project_dir=project_dir,
                participant_name="吴一",
                status="待回复",
                last_outbound_at=_ts(hours_offset=-13),
                followup_count=1,
                execution_session_id="session-wuyi",
                execution_session_key="research-shared-xietong-wuyi",
                **_verified_binding_kwargs("ou_wuyi", "research-shared-xietong-wuyi"),
                last_message_id="om_wuyi_2",
                last_chat_id="oc_wuyi_2",
                send_confirmation_status="已调用发送",
            )
            actions = evaluate_project_actions(project_dir=project_dir, now_at=_ts())
            self.assertEqual(actions["受访对象动作"][0]["建议动作"], "第二次跟进")

    def test_dispatch_plan_defaults_to_full_wave_when_all_participants_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            participants = [
                {"姓名": f"测试{i:02d}", "飞书标识": f"user:ou_{i:02d}", "纳入原因": "受控样本"}
                for i in range(30)
            ]
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="批量派发测试",
                initiator_name="陈经理",
                initiator_feishu_id="user:ou_chen",
                research_goal="验证批次派发",
                research_scope="30人样本",
                participant_source_mode="直接名单",
                participant_scope_text="30人",
                project_deadline_at=_ts(hours_offset=48),
                participants=participants,
            )
            for i in range(30):
                update_participant(
                    project_dir=project_dir,
                    participant_name=f"测试{i:02d}",
                    status="待首发",
                    execution_agent="research-shared",
                    execution_session_id=f"session-{i:02d}",
                    execution_session_key=f"research-shared-batch-{i:02d}",
                    **_verified_binding_kwargs(f"ou_{i:02d}", f"research-shared-batch-{i:02d}"),
                )

            plan = build_dispatch_plan(project_dir=project_dir)
            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))

            self.assertEqual(plan["派发模式"], "一次性全发")
            self.assertEqual(plan["首轮发送人数"], 30)
            self.assertEqual(len(plan["首轮对象列表"]), 30)
            self.assertEqual(plan["批次数"], 0)
            self.assertEqual(project_payload["批次状态"], "待首发")
            self.assertEqual(project_payload["派发批次记录"], [])

    def test_dispatch_plan_with_explicit_small_batch_keeps_rate_limit_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            participants = [
                {"姓名": f"测试{i:02d}", "飞书标识": f"user:ou_{i:02d}", "纳入原因": "受控样本"}
                for i in range(30)
            ]
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="批量派发限流测试",
                initiator_name="陈经理",
                initiator_feishu_id="user:ou_chen",
                research_goal="验证限流派发",
                research_scope="30人样本",
                participant_source_mode="直接名单",
                participant_scope_text="30人",
                project_deadline_at=_ts(hours_offset=48),
                participants=participants,
            )
            for i in range(30):
                update_participant(
                    project_dir=project_dir,
                    participant_name=f"测试{i:02d}",
                    status="待首发",
                    execution_agent="research-shared",
                    execution_session_id=f"session-{i:02d}",
                    execution_session_key=f"research-shared-batch-{i:02d}",
                    **_verified_binding_kwargs(f"ou_{i:02d}", f"research-shared-batch-{i:02d}"),
                )

            plan = build_dispatch_plan(project_dir=project_dir, batch_size=10, batch_interval_minutes=10)

            self.assertEqual(plan["派发模式"], "分批限流")
            self.assertEqual(plan["批次数"], 3)
            self.assertEqual([item["计划发送人数"] for item in plan["批次列表"]], [10, 10, 10])

    def test_build_first_touch_plan_requires_bound_shared_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )

            blocked = build_participant_outreach_plan(project_dir=project_dir, participant_name="肖宁劼")

            self.assertFalse(blocked["允许发送"])
            self.assertEqual(blocked["建议动作"], "先真实创建专属会话")
            self.assertIn("sessions_spawn", blocked["阻止原因"])

            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="research-shared-peixun-openid_xiao",
                **_verified_binding_kwargs("ou_xiao", "research-shared-peixun-openid_xiao"),
            )
            plan = build_participant_outreach_plan(project_dir=project_dir, participant_name="肖宁劼")

            self.assertTrue(plan["允许发送"])
            self.assertEqual(plan["发送账号标识"], "research")
            self.assertIn("feishu_im_user_message", plan["禁止工具"])
            self.assertEqual(plan["执行会话代理"], "research-shared")
            self.assertEqual(plan["执行会话Key"], "research-shared-peixun-openid_xiao")
            self.assertEqual(plan["会话绑定状态"], "已绑定")
            self.assertEqual(plan["运行模式"], "真实调研")
            self.assertEqual(plan["首轮触达"]["提问方式"], "选择题")
            self.assertEqual(plan["首轮触达"]["交互形态"], "文本选项")
            self.assertEqual(plan["首轮触达"]["工具"], "sessions_send")
            self.assertEqual(plan["首轮触达"]["工具参数"]["sessionKey"], "research-shared-peixun-openid_xiao")
            self.assertEqual(plan["首轮触达"]["共享会话消息参数"]["accountId"], "research")
            self.assertEqual(plan["首轮触达"]["共享会话消息参数"]["target"], "user:ou_xiao")
            self.assertIn("请直接回复", plan["首轮触达"]["消息内容"])
            self.assertFalse(plan["首轮触达"]["是否降级发送"])
            self.assertEqual(plan["首轮触达"]["记录口径"], "文本选择题")
            self.assertIn("只占用你 1 分钟", plan["说明消息"])

    def test_build_first_touch_plan_requires_cross_session_send_visibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="research-shared-peixun-openid_xiao",
                **_verified_binding_kwargs("ou_xiao", "research-shared-peixun-openid_xiao"),
            )
            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "tree"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {"id": "research", "tools": {"profile": "full"}},
                                {"id": "research-shared", "tools": {"profile": "full"}},
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                config_path=config_path,
            )

            self.assertFalse(plan["允许发送"])
            self.assertEqual(plan["建议动作"], "先修正 shared 投递配置并重启 gateway")
            self.assertIn("Session send visibility", plan["阻止原因"])

    def test_build_first_touch_plan_uses_sessions_send_in_strict_shared_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="research-shared-peixun-openid_xiao",
                **_verified_binding_kwargs("ou_xiao", "research-shared-peixun-openid_xiao"),
            )
            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "all"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {
                                    "id": "research",
                                    "tools": {"profile": "full"},
                                },
                                {
                                    "id": "research-shared",
                                    "tools": {"profile": "full"},
                                },
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                config_path=config_path,
            )

            self.assertTrue(plan["允许发送"])
            self.assertEqual(plan["首轮触达"]["工具"], "sessions_send")
            self.assertEqual(plan["首轮触达"]["工具参数"]["sessionKey"], "research-shared-peixun-openid_xiao")
            self.assertEqual(plan["首轮触达"]["共享会话消息工具"], "message")
            self.assertIn("messageId", plan["发送后核验"]["共享会话必须返回字段"])

    def test_build_first_touch_plan_embeds_strict_shared_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="上下文收紧测试",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="验证 shared 会话拿到固定项目上下文",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="research-shared-context-xiao",
                **_verified_binding_kwargs("ou_xiao", "research-shared-context-xiao"),
            )
            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "all"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {"id": "research", "tools": {"profile": "full"}},
                                {"id": "research-shared", "tools": {"profile": "full"}},
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                config_path=config_path,
            )
            shared_message = plan["首轮触达"]["工具参数"]["message"]

            self.assertIn(f"项目目录：{project_dir}", shared_message)
            self.assertIn("项目类型：真实调研", shared_message)
            self.assertIn("受访对象open_id：ou_xiao", shared_message)
            self.assertIn("执行会话Key：research-shared-context-xiao", shared_message)
            self.assertIn("项目上下文漂移", shared_message)
            self.assertIn("正式回写命令", shared_message)
            self.assertIn("manage_internal_interview_project.py ingest-reply", shared_message)
            self.assertIn("feishu_conversation_binding` 执行 `action=unbind", shared_message)
            self.assertIn("manage_internal_interview_project.py finalize-participant", shared_message)
            protocol_payload = plan["首轮触达"]["严格协议载荷"]
            self.assertEqual(protocol_payload["protocol_version"], "internal-interview-shared/v1")
            self.assertEqual(protocol_payload["project_dir"], str(project_dir))
            self.assertEqual(protocol_payload["project_type"], "真实调研")
            self.assertEqual(protocol_payload["participant_name"], "肖宁劼")
            self.assertEqual(protocol_payload["participant_open_id"], "ou_xiao")
            self.assertEqual(protocol_payload["execution_session_key"], "research-shared-context-xiao")
            self.assertIn("ingest-reply", protocol_payload["ingest_reply_command"])
            self.assertIn("finalize-participant", protocol_payload["finalize_participant_command"])
            self.assertTrue(protocol_payload["unbind_rule"]["required"])
            self.assertIn("[internal-interview-shared-payload/v1]", shared_message)

    def test_old_manual_shared_payload_is_rejected(self):
        old_payload = (
            "现在执行重启后首轮真实调研外发。严格遵守：1) 只能用 message 工具；"
            "2) channel=feishu accountId=research target=user:ou_xiao；"
            "3) 发送纯文本消息，不要卡片。"
        )

        self.assertFalse(project_module._shared_protocol_message_is_complete(old_payload))
        self.assertEqual(project_module._extract_shared_protocol_payload(old_payload), {})

    def test_evaluate_project_actions_flags_incomplete_shared_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            session_root = Path(tmp) / "shared-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="协议巡检测试",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="验证旧 payload 会被巡检拦截",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                status="待回复",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="agent:research-shared:subagent:xiao",
                last_outbound_at=_ts(hours_offset=-1),
                last_message_id="msg-xiao",
                last_chat_id="chat-xiao",
                send_confirmation_status="已确认回执",
                send_confirmation_time=_ts(hours_offset=-1),
                send_confirmation_evidence="首轮 message 已返回 messageId + chatId。",
                **_verified_binding_kwargs("ou_xiao", "agent:research-shared:subagent:xiao"),
            )
            (session_root / "session-xiao.jsonl").write_text(
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "[Inter-session message] sourceTool=sessions_send\n现在执行重启后首轮真实调研外发。严格遵守：1) 只能用 message 工具；2) channel=feishu；3) 发完只返回真实结果。",
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            with mock.patch.object(project_module, "默认shared会话目录", session_root):
                actions = evaluate_project_actions(project_dir=project_dir, now_at=_ts())

            self.assertEqual(actions["受访对象动作"][0]["建议动作"], "停止复用并补协议")
            self.assertEqual(actions["受访对象动作"][0]["shared协议状态"], "协议不完整")

    def test_build_first_touch_plan_reports_expired_main_session_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="research-shared-peixun-openid_xiao",
                **_verified_binding_kwargs("ou_xiao", "research-shared-peixun-openid_xiao"),
            )
            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "all"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {
                                    "id": "research",
                                    "tools": {"profile": "full"},
                                },
                                {
                                    "id": "research-shared",
                                    "tools": {"profile": "full"},
                                },
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            session_root = Path(tmp) / "research-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            requester_session_key = "agent:research:feishu:direct:ou_requester"
            (session_root / "runtime-old.trajectory.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "trace.metadata",
                                "ts": "2026-05-23T06:20:00+08:00",
                                "sessionKey": requester_session_key,
                                "data": {
                                    "config": {
                                        "redacted": {
                                            "tools": {
                                                "profile": "coding",
                                                "allow": ["group:sessions", "sessions_spawn", "sessions_list"],
                                                "sessions": {"visibility": "tree"},
                                                "agentToAgent": {"enabled": True},
                                            }
                                        }
                                    }
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "context.compiled",
                                "sessionKey": requester_session_key,
                                "data": {
                                    "systemPrompt": "Tool names are case-sensitive.\n- sessions_send\n- sessions_spawn\n- sessions_list"
                                },
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                config_path=config_path,
                requester_session_key=requester_session_key,
                requester_session_root=session_root,
            )

            self.assertFalse(plan["允许发送"])
            self.assertEqual(plan["诊断状态"], "主会话权限快照过期")
            self.assertEqual(plan["建议动作"], "配置已改但当前 runtime 仍是旧值，需要重启 gateway 后再在当前主对话触发一次新 turn")
            self.assertTrue(plan["严格shared配置检查"]["静态配置是否通过"])
            self.assertEqual(plan["严格shared配置检查"]["运行时主会话检查"]["visibility"], "tree")
            self.assertIn("静态配置已通过", plan["阻止原因"])
            self.assertIn("旧权限快照", plan["阻止原因"])

    def test_build_first_touch_plan_allows_send_when_runtime_compiled_tools_include_sessions_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="research-shared-peixun-openid_xiao",
                **_verified_binding_kwargs("ou_xiao", "research-shared-peixun-openid_xiao"),
            )
            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "all"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {"id": "research", "tools": {"profile": "full"}},
                                {"id": "research-shared", "tools": {"profile": "full"}},
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            session_root = Path(tmp) / "research-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            requester_session_key = "agent:research:feishu:direct:ou_requester"
            (session_root / "runtime-ok.trajectory.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "trace.metadata",
                                "ts": "2026-05-23T10:05:37.143Z",
                                "sessionKey": requester_session_key,
                                "data": {
                                    "config": {
                                        "redacted": {
                                            "tools": {
                                                "sessions": {"visibility": "all"},
                                                "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                                            }
                                        }
                                    }
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "context.compiled",
                                "sessionKey": requester_session_key,
                                "data": {
                                    "systemPrompt": {
                                        "truncated": True,
                                        "reason": "trajectory-field-size-limit",
                                        "originalChars": 38919,
                                        "limitChars": 32768,
                                    },
                                    "tools": [
                                        {"name": "sessions_send"},
                                        {"name": "sessions_spawn"},
                                        {"name": "sessions_list"},
                                        {"name": "session_status"},
                                    ],
                                },
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                config_path=config_path,
                requester_session_key=requester_session_key,
                requester_session_root=session_root,
            )

            self.assertTrue(plan["允许发送"])
            self.assertEqual(plan["诊断状态"], "通过")
            self.assertEqual(
                plan["严格shared配置检查"]["运行时主会话检查"]["compiledToolNames"],
                ["session_status", "sessions_list", "sessions_send", "sessions_spawn"],
            )
            self.assertTrue(plan["严格shared配置检查"]["运行时主会话检查"]["systemPromptTruncated"])

    def test_build_first_touch_plan_reports_runtime_tool_detection_error_when_compiled_tools_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="research-shared-peixun-openid_xiao",
                **_verified_binding_kwargs("ou_xiao", "research-shared-peixun-openid_xiao"),
            )
            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "all"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {"id": "research", "tools": {"profile": "full"}},
                                {"id": "research-shared", "tools": {"profile": "full"}},
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            session_root = Path(tmp) / "research-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            requester_session_key = "agent:research:feishu:direct:ou_requester"
            (session_root / "runtime-missing-tools.trajectory.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "trace.metadata",
                                "ts": "2026-05-23T10:05:37.143Z",
                                "sessionKey": requester_session_key,
                                "data": {
                                    "config": {
                                        "redacted": {
                                            "tools": {
                                                "sessions": {"visibility": "all"},
                                                "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                                            }
                                        }
                                    }
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "context.compiled",
                                "sessionKey": requester_session_key,
                                "data": {
                                    "systemPrompt": {
                                        "truncated": True,
                                        "reason": "trajectory-field-size-limit",
                                        "originalChars": 38919,
                                        "limitChars": 32768,
                                    }
                                },
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                config_path=config_path,
                requester_session_key=requester_session_key,
                requester_session_root=session_root,
            )

            self.assertFalse(plan["允许发送"])
            self.assertEqual(plan["诊断状态"], "运行时工具检测异常")
            self.assertEqual(plan["建议动作"], "gateway 已生效，但当前 skill 的 runtime 工具检测证据不足，需要先修复检测链路")
            self.assertEqual(plan["严格shared配置检查"]["运行时主会话检查"]["sessionsSendVisible"], None)
            self.assertEqual(plan["严格shared配置检查"]["运行时主会话检查"]["compiledToolNames"], [])

    def test_repair_project_participants_fixes_broken_feishu_id_and_session_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="名单修复测试",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="验证修复逻辑",
                research_scope="五人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "林惠惠", "飞书标识": "user:ou_good", "纳入原因": "ou_good:测试对象"}],
            )
            participants_path = project_dir / "受访对象清单.yaml"
            payload = yaml.safe_load(participants_path.read_text(encoding="utf-8"))
            payload["受访对象列表"][0]["飞书标识"] = "user"
            payload["受访对象列表"][0]["纳入原因"] = "ou_333e42b029238ffbb8f0888fd1d119ff:龙虾内测群成员"
            payload["受访对象列表"][0]["执行会话Key"] = "research-shared-openclaw-user"
            payload["受访对象列表"][0]["会话绑定ID"] = "research:wrong"
            payload["受访对象列表"][0]["会话绑定状态"] = "已绑定"
            payload["受访对象列表"][0]["最近一次绑定确认时间"] = _ts()
            payload["受访对象列表"][0]["最近一次绑定确认依据"] = "旧会话绑定"
            payload["受访对象列表"][0]["最近一次绑定目标会话Key"] = "research-shared-openclaw-user"
            payload["受访对象列表"][0]["最近一次绑定检查结果"] = "已核验通过"
            payload["受访对象列表"][0]["当前状态"] = "待回复"
            payload["受访对象列表"][0]["最近一次发送消息ID"] = "om_bad"
            participants_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

            result = repair_project_participants(project_dir=project_dir)
            repaired_payload = yaml.safe_load(participants_path.read_text(encoding="utf-8"))
            participant = repaired_payload["受访对象列表"][0]

            self.assertEqual(result["修复人数"], 1)
            self.assertEqual(participant["飞书标识"], "user:ou_333e42b029238ffbb8f0888fd1d119ff")
            self.assertNotEqual(participant["执行会话Key"], "research-shared-openclaw-user")
            self.assertEqual(participant["会话绑定状态"], "未绑定")
            self.assertEqual(participant["会话绑定ID"], "")
            self.assertEqual(participant["当前状态"], "待创建会话")
            self.assertEqual(participant["最近一次发送消息ID"], "")

    def test_acceptance_plan_reports_expired_main_session_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="链路验收测试",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="验证链路验收",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )
            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "all"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {
                                    "id": "research",
                                    "tools": {
                                        "alsoAllow": [
                                            "sessions_spawn",
                                            "sessions_send",
                                            "sessions_list",
                                            "session_status",
                                            "feishu_conversation_binding",
                                        ],
                                    },
                                },
                                {
                                    "id": "research-shared",
                                    "tools": {
                                        "alsoAllow": ["message", "sessions_spawn", "feishu_conversation_binding", "feishu_ask_user_question"],
                                    },
                                },
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            session_root = Path(tmp) / "research-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            requester_session_key = "agent:research:feishu:direct:ou_requester"
            (session_root / "runtime-old.trajectory.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "trace.metadata",
                                "ts": "2026-05-23T06:20:00+08:00",
                                "sessionKey": requester_session_key,
                                "data": {
                                    "config": {
                                        "redacted": {
                                            "tools": {
                                                "profile": "coding",
                                                "allow": ["group:sessions", "sessions_spawn", "sessions_list"],
                                                "sessions": {"visibility": "tree"},
                                                "agentToAgent": {"enabled": True},
                                            }
                                        }
                                    }
                                },
                            },
                            ensure_ascii=False,
                        )
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            plan = build_chain_acceptance_test_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                config_path=config_path,
                requester_session_key=requester_session_key,
                requester_session_root=session_root,
            )

            self.assertFalse(plan["允许执行"])
            self.assertEqual(plan["诊断状态"], "主会话权限快照过期")
            self.assertEqual(plan["建议动作"], "配置已改但当前 runtime 仍是旧值，需要重启 gateway 后再在当前主对话触发一次新 turn")
            self.assertTrue(plan["前置检查"]["严格shared配置检查"]["静态配置是否通过"])
            self.assertEqual(plan["前置检查"]["严格shared配置检查"]["运行时主会话检查"]["visibility"], "tree")
            self.assertIn("旧权限快照", plan["阻止原因"])

    def test_build_first_touch_plan_ignores_card_flag_in_real_research_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
                project_type="链路验收",
            )

            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="agent:research-shared:subagent:xiao",
                **_verified_binding_kwargs("ou_xiao", "agent:research-shared:subagent:xiao"),
            )
            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                card_supported=False,
            )

            self.assertTrue(plan["允许发送"])
            self.assertEqual(plan["首轮触达"]["交互形态"], "文本选项")
            self.assertIn("请直接回复", plan["首轮触达"]["消息内容"])
            self.assertEqual(plan["首轮触达"]["提问方式"], "选择题")
            self.assertFalse(plan["首轮触达"]["是否降级发送"])
            self.assertEqual(plan["首轮触达"]["记录口径"], "文本选择题")

    def test_build_first_touch_plan_blocks_when_research_account_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_agent="research-shared",
                execution_session_id="session-xiao",
                execution_session_key="agent:research-shared:subagent:xiao",
                **_verified_binding_kwargs("ou_xiao", "agent:research-shared:subagent:xiao"),
            )
            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                research_account_ready=False,
            )

            self.assertFalse(plan["允许发送"])
            self.assertEqual(plan["建议动作"], "暂停并通知发起人")
            self.assertIn("research 账号当前不可用", plan["阻止原因"])

    def test_build_first_touch_plan_blocks_without_real_execution_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                execution_session_key="research-shared-peixun-openid_xiao",
                **_verified_binding_kwargs("ou_xiao", "research-shared-peixun-openid_xiao"),
            )
            plan = build_participant_outreach_plan(project_dir=project_dir, participant_name="肖宁劼")

            self.assertFalse(plan["允许发送"])
            self.assertEqual(plan["建议动作"], "先真实创建专属会话")
            self.assertIn("sessions_spawn", plan["阻止原因"])

    def test_build_chain_acceptance_plan_blocks_when_required_tools_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="链路验收阻止测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证链路验收前置检查",
                research_scope="单一受控测试对象",
                participant_source_mode="直接名单",
                participant_scope_text="仅 1 个测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "测试号", "飞书标识": "user:ou_test", "纳入原因": "受控测试账号"}],
                project_type="链路验收",
            )

            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "agents": {
                            "list": [
                                {"id": "research", "tools": {"alsoAllow": ["sessions_spawn"]}},
                                {"id": "research-shared", "tools": {"alsoAllow": ["sessions_spawn"]}},
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            plan = build_chain_acceptance_test_plan(
                project_dir=project_dir,
                participant_name="测试号",
                config_path=config_path,
            )

            self.assertFalse(plan["允许执行"])
            self.assertEqual(plan["建议动作"], "先补齐工具放行")
            self.assertIn("research: feishu_conversation_binding", plan["阻止原因"])
            self.assertIn("research-shared: feishu_conversation_binding", plan["阻止原因"])
            self.assertIn("research-shared: feishu_ask_user_question", plan["阻止原因"])

    def test_build_chain_acceptance_plan_marks_temp_empty_config_as_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="链路验收临时配置测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证错误 config-path 能被识别",
                research_scope="单一受控测试对象",
                participant_source_mode="直接名单",
                participant_scope_text="仅 1 个测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "测试号", "飞书标识": "user:ou_test", "纳入原因": "受控测试账号"}],
                project_type="链路验收",
            )

            config_path = Path(tmp) / "_temp_acceptance_config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "agents": {
                            "list": [
                                {"id": "research", "tools": {"alsoAllow": []}},
                                {"id": "research-shared", "tools": {"alsoAllow": []}},
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            plan = build_chain_acceptance_test_plan(
                project_dir=project_dir,
                participant_name="测试号",
                config_path=config_path,
            )

            self.assertFalse(plan["允许执行"])
            self.assertEqual(plan["实际检查配置路径"], str(config_path))
            self.assertIn("临时空配置", plan["阻止原因"])

    def test_build_chain_acceptance_plan_returns_two_round_shared_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="链路验收通过测试",
                initiator_name="李经理",
                initiator_feishu_id="user:ou_li",
                research_goal="验证 shared 回收链路",
                research_scope="单一受控测试对象",
                participant_source_mode="直接名单",
                participant_scope_text="仅 1 个测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "测试号", "飞书标识": "user:ou_test", "纳入原因": "受控测试账号"}],
                project_type="链路验收",
            )

            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "all"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {
                                    "id": "research",
                                    "tools": {
                                        "alsoAllow": [
                                            "sessions_spawn",
                                            "sessions_send",
                                            "sessions_list",
                                            "session_status",
                                            "feishu_conversation_binding",
                                        ],
                                    },
                                },
                                {
                                    "id": "research-shared",
                                    "tools": {
                                        "alsoAllow": [
                                            "sessions_spawn",
                                            "feishu_conversation_binding",
                                            "feishu_ask_user_question",
                                            "message",
                                        ],
                                    },
                                },
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            plan = build_chain_acceptance_test_plan(
                project_dir=project_dir,
                participant_name="测试号",
                config_path=config_path,
            )

            self.assertTrue(plan["允许执行"])
            self.assertFalse(plan["执行限制"]["是否允许注册cron"])
            self.assertEqual(plan["执行限制"]["回复时限分钟"], 5)
            self.assertFalse(plan["执行限制"]["是否允许文本降级冒充通过"])
            self.assertTrue(plan["执行限制"]["是否允许显式文本降级通过链路验收"])
            self.assertIn("首轮触达只要能真实发出并让对方明确回复即可", plan["通过标准"][0])
            self.assertEqual(plan["会话创建"]["工具"], "sessions_spawn")
            self.assertEqual(plan["会话创建"]["目标代理"], "research-shared")
            self.assertIn(str(project_dir), plan["会话创建"]["建议提示词"])
            self.assertEqual(plan["会话绑定"]["参数"]["target"], "user:ou_test")
            self.assertEqual(plan["会话绑定"]["参数"]["accountId"], "research")
            self.assertEqual(plan["首轮触达"]["工具"], "feishu_ask_user_question")
            self.assertEqual(plan["首轮触达"]["验收通过要求"], "真实触达成功（按钮卡片或短文本明确选项）")
            self.assertTrue(plan["首轮触达"]["是否允许文本降级计作通过"])
            self.assertEqual(plan["首轮触达"]["工具参数"]["questionStyle"], "buttons")
            self.assertEqual(plan["首轮触达"]["工具参数"]["target"], "user:ou_test")
            self.assertEqual(plan["首轮触达"]["工具参数"]["questions"][0]["question"], "你现在能正常看到这张测试卡片吗？")
            self.assertEqual(
                [item["label"] for item in plan["首轮触达"]["工具参数"]["questions"][0]["options"]],
                ["能看到", "看不到"],
            )
            self.assertIn("请直接回复", plan["首轮触达"]["文本降级消息"])
            self.assertEqual(plan["第二轮触达"]["工具参数"]["questions"][0]["question"], "收到，这里继续做第二步确认。现在这条链路是否仍然正常？")
            self.assertEqual(
                [item["label"] for item in plan["第二轮触达"]["工具参数"]["questions"][0]["options"]],
                ["继续正常", "到此结束"],
            )
            self.assertIn("请直接回复", plan["第二轮触达"]["文本降级消息"])
            self.assertIn("bound conversation -> <执行会话Key>", plan["回收验证"]["必须同时满足"][1])
            self.assertNotIn("实际方式: 短文本二选一", plan["回收验证"]["项目文件禁止出现"])
            self.assertEqual(plan["清理"]["解绑参数"]["action"], "unbind")
            self.assertEqual(plan["清理"]["解绑参数"]["target"], "user:ou_test")

    def test_build_parallel_chain_acceptance_plan_returns_two_participant_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="双人并行链路验收",
                initiator_name="李经理",
                initiator_feishu_id="user:ou_li",
                research_goal="验证双人并行 shared 回收链路",
                research_scope="两个受控测试对象",
                participant_source_mode="直接名单",
                participant_scope_text="仅 2 个测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[
                    {"姓名": "测试甲", "飞书标识": "user:ou_test_a", "纳入原因": "受控测试账号A"},
                    {"姓名": "测试乙", "飞书标识": "user:ou_test_b", "纳入原因": "受控测试账号B"},
                ],
                project_type="链路验收",
            )

            config_path = Path(tmp) / "openclaw.json"
            config_path.write_text(
                json.dumps(
                    {
                        "tools": {
                            "sessions": {"visibility": "all"},
                            "agentToAgent": {"enabled": True, "allow": ["research", "research-shared"]},
                        },
                        "agents": {
                            "list": [
                                {
                                    "id": "research",
                                    "tools": {
                                        "alsoAllow": [
                                            "sessions_spawn",
                                            "sessions_send",
                                            "sessions_list",
                                            "session_status",
                                            "feishu_conversation_binding",
                                        ],
                                    },
                                },
                                {
                                    "id": "research-shared",
                                    "tools": {
                                        "alsoAllow": [
                                            "sessions_spawn",
                                            "feishu_conversation_binding",
                                            "feishu_ask_user_question",
                                            "message",
                                        ],
                                    },
                                },
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            plan = build_parallel_chain_acceptance_test_plan(
                project_dir=project_dir,
                participant_names=["测试甲", "测试乙"],
                config_path=config_path,
            )

            self.assertTrue(plan["允许执行"])
            self.assertEqual(plan["执行限制"]["并行对象数"], 2)
            self.assertTrue(plan["前置检查"]["是否双人项目"])
            self.assertEqual(len(plan["对象计划列表"]), 2)
            self.assertEqual(
                [item["受访对象"] for item in plan["对象计划列表"]],
                ["测试甲", "测试乙"],
            )
            self.assertEqual(
                [item["受访对象飞书标识"] for item in plan["对象计划列表"]],
                ["user:ou_test_a", "user:ou_test_b"],
            )
            self.assertIn("互不串会话", plan["通过标准"][1])
            self.assertIn("互不串项目记录", plan["通过标准"][2])
            self.assertEqual(plan["对象计划列表"][0]["会话绑定"]["参数"]["target"], "user:ou_test_a")
            self.assertEqual(plan["对象计划列表"][1]["会话绑定"]["参数"]["target"], "user:ou_test_b")
            self.assertIn("请直接回复", plan["对象计划列表"][0]["首轮触达"]["文本降级消息"])
            self.assertIn("请直接回复", plan["对象计划列表"][1]["第二轮触达"]["文本降级消息"])
            self.assertEqual(plan["清理"]["项目文件处理"], "两位受访对象都要解绑，并把项目阶段改为验收清理完成，不创建也不保留 cron。")

    def test_reach_enough_signals_stops_followup(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="培训前体验访谈",
                initiator_name="孙经理",
                initiator_feishu_id="user:ou_sun",
                research_goal="了解培训前的真实体验",
                research_scope="单人测试样本",
                participant_source_mode="直接名单",
                participant_scope_text="核心测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "肖宁劼", "飞书标识": "user:ou_xiao", "纳入原因": "测试对象"}],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="肖宁劼",
                status="访谈中",
                summary="已拿到主要信息",
                question_mode="开放问答",
                open_question_count=1,
                collected_signals=["是否使用过", "主要使用场景或主要阻力", "培训期待或改进方向"],
            )

            plan = build_participant_outreach_plan(project_dir=project_dir, participant_name="肖宁劼")

            self.assertEqual(plan["建议动作"], "直接收口")
            self.assertTrue(plan["已达到收口条件"])
            self.assertIn("不要继续追问", plan["收口说明"])

    def test_stop_project_collects_current_info_and_cleans_cron(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            cron_jobs_path = Path(tmp) / "jobs.json"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="停止测试访谈",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证停止调研时的收口动作",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="测试对象",
                project_deadline_at=_ts(hours_offset=24),
                participants=[
                    {"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"},
                    {"姓名": "乙", "飞书标识": "user:ou_yi", "纳入原因": "成员"},
                ],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                status="已完成",
                summary="已完成访谈",
                collected_signals=["是否使用过", "主要使用场景或主要阻力"],
                execution_agent="research-shared",
                execution_session_id="session-jia",
                execution_session_key="agent:research-shared:subagent:jia",
                **_verified_binding_kwargs("ou_jia", "agent:research-shared:subagent:jia"),
            )
            update_participant(
                project_dir=project_dir,
                participant_name="乙",
                status="待回复",
                last_outbound_at=_ts(hours_offset=-2),
                execution_agent="research-shared",
                execution_session_id="session-yi",
                execution_session_key="agent:research-shared:subagent:yi",
                **_verified_binding_kwargs("ou_yi", "agent:research-shared:subagent:yi"),
                last_message_id="om_yi_1",
                last_chat_id="oc_yi_1",
                send_confirmation_status="已调用发送",
                last_card_id="card-yi",
            )

            cron_jobs_path.write_text(
                yaml.safe_dump(
                    {
                        "version": 1,
                        "jobs": [
                            {
                                "id": "job-stop-test",
                                "name": "内部访谈调研巡检-停止测试访谈",
                                "enabled": True,
                                "schedule": {"kind": "cron", "expr": "*/30 * * * *", "tz": "Asia/Shanghai"},
                                "payload": {"kind": "agentTurn", "message": "巡检"},
                                "delivery": {"mode": "none"},
                                "state": {},
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))
            project_payload["巡检设置"]["巡检任务ID"] = "job-stop-test"
            project_payload["巡检设置"]["是否已注册"] = True
            (project_dir / "项目总表.yaml").write_text(
                yaml.safe_dump(project_payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            result = stop_project_and_cleanup(
                project_dir=project_dir,
                stopped_by="涂是淦",
                stop_reason="发起人要求停止当前调研",
                cron_jobs_path=cron_jobs_path,
            )

            updated_project = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))
            updated_participants = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            cron_payload = yaml.safe_load(cron_jobs_path.read_text(encoding="utf-8"))
            report = (project_dir / "最终调研报告.md").read_text(encoding="utf-8")

            self.assertEqual(result["项目状态"], "已停止")
            self.assertEqual(result["清理巡检任务数"], 1)
            self.assertEqual(updated_project["项目状态"], "已停止")
            self.assertEqual(updated_project["当前阶段"], "已关闭")
            self.assertFalse(updated_project["巡检设置"]["是否已注册"])
            self.assertEqual(updated_project["巡检设置"]["巡检任务ID"], "")
            self.assertEqual(updated_participants["受访对象列表"][1]["当前状态"], "已超时")
            self.assertEqual(updated_participants["受访对象列表"][0]["会话绑定状态"], "已解绑")
            self.assertEqual(updated_participants["受访对象列表"][1]["会话绑定状态"], "已解绑")
            self.assertEqual(updated_participants["受访对象列表"][1]["最近一次卡片结果"], "已失效")
            self.assertEqual(cron_payload["jobs"], [])
            self.assertIn("停止收口", report)
            self.assertIn("发起人要求停止当前调研", report)

    def test_finalize_project_marks_unfinished_participants_timed_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="沟通节奏访谈",
                initiator_name="郑经理",
                initiator_feishu_id="user:ou_zheng",
                research_goal="了解沟通节奏问题",
                research_scope="销售与交付",
                participant_source_mode="直接名单",
                participant_scope_text="核心协作人",
                project_deadline_at=_ts(hours_offset=-1),
                participants=[
                    {"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "销售"},
                    {"姓名": "乙", "飞书标识": "user:ou_yi", "纳入原因": "交付"},
                ],
            )

            update_participant(project_dir=project_dir, participant_name="甲", status="已完成", summary="已完成访谈")
            update_participant(
                project_dir=project_dir,
                participant_name="乙",
                status="待回复",
                last_outbound_at=_ts(hours_offset=-10),
                execution_session_id="session-yi",
                execution_session_key="research-shared-goutong-yi",
                **_verified_binding_kwargs("ou_yi", "research-shared-goutong-yi"),
                last_message_id="om_yi_2",
                last_chat_id="oc_yi_2",
                send_confirmation_status="已调用发送",
            )

            result = finalize_project_on_deadline(project_dir=project_dir, now_at=_ts())
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))
            report = (project_dir / "最终调研报告.md").read_text(encoding="utf-8")

            self.assertEqual(result["已超时人数"], 1)
            self.assertEqual(participants_payload["受访对象列表"][1]["当前状态"], "已超时待收口")
            self.assertEqual(project_payload["当前阶段"], "分析总结")
            self.assertIn("仍有 1 位受访对象未完全收口", project_payload["分析收口"]["样本缺口说明"])
            self.assertNotIn("待补充", report)
            self.assertIn("核心发现", report)

    def test_late_reply_before_delivery_freeze_is_included_and_reanalyzed(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            deadline = _ts(hours_offset=-1)
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="晚回复补回测试",
                initiator_name="周经理",
                initiator_feishu_id="user:ou_zhou",
                research_goal="验证截止后补回",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=deadline,
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            finalize_project_on_deadline(project_dir=project_dir, now_at=_ts())
            participant = update_participant(
                project_dir=project_dir,
                participant_name="甲",
                last_inbound_at=_ts(),
                summary="截止后补充了真实使用体验",
                collected_signals=["是否使用过"],
            )
            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))

            self.assertEqual(participant["当前状态"], "超时后补回")
            self.assertTrue(participant["是否计入有效样本"])
            self.assertEqual(project_payload["项目状态"], "待交付")
            self.assertIn("晚回复补回测试", (project_dir / "最终调研报告.md").read_text(encoding="utf-8"))

    def test_reply_after_delivery_freeze_only_records_without_rewriting_status_to_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="冻结后回复测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证冻结后回复",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=-1),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            finalize_project_on_deadline(project_dir=project_dir, now_at=_ts())
            mark_delivery_complete(project_dir=project_dir, doc_url="https://example.com/doc")
            participant = update_participant(
                project_dir=project_dir,
                participant_name="甲",
                last_inbound_at=_ts(),
                summary="报告发出后才补了一句",
            )

            self.assertEqual(participant["当前状态"], "已关闭后回复")
            self.assertEqual(participant["收口方式"], "冻结后仅记录")

    def test_completed_participant_auto_unbinds_after_successful_writeback(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="完成即解绑测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证完成后自动解绑",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            participant = update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="research-shared-wancheng-jia",
                **_verified_binding_kwargs("ou_jia", "research-shared-wancheng-jia"),
                last_message_id="om_jia_1",
                last_chat_id="oc_jia_1",
                last_outbound_at=_ts(hours_offset=-1),
                send_confirmation_status="已形成可回收 shared 会话",
                last_inbound_at=_ts(),
                summary="已经明确使用场景和培训期待",
                collected_signals=["是否使用过", "主要使用场景或主要阻力", "培训期待或改进方向"],
            )
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            saved = participants_payload["受访对象列表"][0]
            note_path = Path(saved["访谈记录路径"])

            self.assertEqual(participant["当前状态"], "已完成")
            self.assertEqual(saved["当前状态"], "已完成")
            self.assertEqual(saved["会话绑定状态"], "已解绑")
            self.assertEqual(saved["会话绑定ID"], "")
            self.assertEqual(saved["最近一次业务状态"], "已完成并自动解绑")
            self.assertIn("已切回 research 主对话", saved["最近一次链路状态"])
            self.assertTrue(saved["是否已回收至research"])
            self.assertTrue(note_path.is_file())
            self.assertIn("收口完成", note_path.read_text(encoding="utf-8"))

    def test_completed_participant_auto_unbinds_when_effective_question_limit_reached(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="四问兜底解绑测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证满 4 个有效问题后自动解绑",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            participant = update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="research-shared-siwen-jia",
                **_verified_binding_kwargs("ou_jia", "research-shared-siwen-jia"),
                last_message_id="om_jia_4",
                last_chat_id="oc_jia_4",
                last_outbound_at=_ts(hours_offset=-1),
                send_confirmation_status="已形成可回收 shared 会话",
                last_inbound_at=_ts(),
                summary="虽然信号还没全齐，但已经达到四个有效问题上限",
                effective_question_count=4,
                collected_signals=["是否使用过"],
            )

            self.assertEqual(participant["当前状态"], "已完成")
            self.assertEqual(participant["会话绑定状态"], "已解绑")

    def test_ingest_participant_reply_marks_completed_and_waits_for_real_unbind(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="四问后真实解绑测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证 shared 先回写再真实解绑",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="agent:research-shared:subagent:jia",
                last_outbound_at=_ts(hours_offset=-1),
                last_message_id="om_jia_1",
                last_chat_id="oc_jia_1",
                send_confirmation_status="已形成可回收 shared 会话",
                effective_question_count=3,
                collected_signals=["是否使用过", "主要使用场景或主要阻力"],
                **_verified_binding_kwargs("ou_jia", "agent:research-shared:subagent:jia"),
            )

            result = ingest_participant_reply(
                project_dir=project_dir,
                participant_name="甲",
                reply_text="我最希望先少报错、少失败",
                reply_at=_ts(),
                assistant_text="如果只优先改一件事，你最希望先改哪类问题？A. 响应更快 B. 少报错、少失败 C. 结果更稳定一致 D. 操作链路更顺 E. 其他",
                execution_session_key="agent:research-shared:subagent:jia",
                participant_open_id="ou_jia",
                project_type="真实调研",
            )

            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]

            self.assertTrue(result["ok"])
            self.assertTrue(result["shouldUnbind"])
            self.assertEqual(participant["当前状态"], "已完成")
            self.assertEqual(participant["会话绑定状态"], "已绑定")
            self.assertEqual(participant["累计有效问题数"], 4)
            self.assertEqual(
                participant["已收集信号"],
                ["是否使用过", "主要使用场景或主要阻力", "培训期待或改进方向"],
            )

            final = project_module.finalize_participant(project_dir=project_dir, participant_name="甲", finalized_at=_ts())
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]

            self.assertTrue(final["已执行"])
            self.assertEqual(participant["会话绑定状态"], "已解绑")
            self.assertEqual(participant["最近一次业务状态"], "已完成并自动解绑")
            self.assertTrue(
                "单人有效问题上限" in participant["收口原因"] or "已覆盖是否使用过" in participant["收口原因"]
            )

    def test_ingest_participant_reply_returns_next_question_when_interview_should_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="继续追问测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证 shared 不会在首问后失联",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="agent:research-shared:subagent:jia",
                last_outbound_at=_ts(hours_offset=-1),
                last_message_id="om_jia_1",
                last_chat_id="oc_jia_1",
                send_confirmation_status="已形成可回收 shared 会话",
                **_verified_binding_kwargs("ou_jia", "agent:research-shared:subagent:jia"),
            )

            result = ingest_participant_reply(
                project_dir=project_dir,
                participant_name="甲",
                reply_text="经常用",
                reply_at=_ts(),
                assistant_text="关于这次调研涉及的主题，你现在更接近哪种情况？请直接回复：经常用 / 用过几次 / 还没真正用 / 说不清",
                execution_session_key="agent:research-shared:subagent:jia",
                participant_open_id="ou_jia",
                project_type="真实调研",
            )

            self.assertTrue(result["ok"])
            self.assertFalse(result["shouldUnbind"])
            self.assertEqual(result["nextSignal"], "主要使用场景或主要阻力")
            self.assertIn("主要更接近哪种情况", result["nextQuestion"])
            self.assertIn("稳定性 / 速度有时不理想", result["nextQuestion"])

    def test_completed_participant_does_not_unbind_when_writeback_not_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="完成待回写测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证回写失败时不解绑",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            with mock.patch.object(project_module, "_写入访谈记录", side_effect=OSError("disk full")):
                participant = update_participant(
                    project_dir=project_dir,
                    participant_name="甲",
                    execution_session_id="session-jia",
                    execution_session_key="research-shared-huixie-jia",
                    **_verified_binding_kwargs("ou_jia", "research-shared-huixie-jia"),
                    last_message_id="om_jia_1",
                    last_chat_id="oc_jia_1",
                    last_outbound_at=_ts(hours_offset=-1),
                    send_confirmation_status="已形成可回收 shared 会话",
                    last_inbound_at=_ts(),
                    summary="信息已齐，但 markdown 回写失败",
                    collected_signals=["是否使用过", "主要使用场景或主要阻力", "培训期待或改进方向"],
                )

            self.assertEqual(participant["当前状态"], "已完成待回写")
            self.assertEqual(participant["会话绑定状态"], "已绑定")
            self.assertEqual(participant["会话绑定ID"], "research:ou_jia")
            self.assertEqual(participant["最近一次业务状态"], "已完成待补偿回写")
            self.assertIn("回写失败", participant["最近一次链路状态"])
            self.assertFalse(participant["是否已回收至research"])

    def test_evaluate_project_actions_marks_completed_bound_participant_for_auto_unbind(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="自动解绑补偿测试",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="验证巡检补偿自动解绑",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )
            participants_path = project_dir / "受访对象清单.yaml"
            participants_payload = yaml.safe_load(participants_path.read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]
            participant["当前状态"] = "已完成"
            participant["执行会话ID"] = "session-jia"
            participant["执行会话Key"] = "research-shared-buchang-jia"
            participant["会话绑定ID"] = "research:ou_jia"
            participant["会话绑定状态"] = "已绑定"
            participant["最近一次绑定确认时间"] = _ts(hours_offset=-1)
            participant["最近一次绑定确认依据"] = "status 校验通过"
            participant["最近一次绑定目标会话Key"] = "research-shared-buchang-jia"
            participant["最近一次绑定检查结果"] = "已核验通过"
            participant["访谈记录路径"] = str(project_dir / "访谈记录" / "甲.md")
            participant["最近一次回收时间"] = _ts(hours_offset=-1)
            participant["是否已回收至research"] = True
            participants_path.write_text(
                yaml.safe_dump(participants_payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            actions = evaluate_project_actions(project_dir=project_dir, now_at=_ts())
            participant_action = actions["受访对象动作"][0]

            self.assertEqual(participant_action["建议动作"], "执行自动解绑")
            self.assertIn("已完成但仍占用 shared 通道", participant_action["原因"])

    def test_mark_delivery_complete_sets_freeze_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            cron_jobs_path = Path(tmp) / "jobs.json"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="交付冻结测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证交付冻结",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=-1),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            finalize_project_on_deadline(project_dir=project_dir, now_at=_ts())
            cron_jobs_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "jobs": [
                            {"id": "advance-job", "name": "内部访谈调研推进-交付冻结测试", "enabled": True},
                            {"id": "inspect-job", "name": "内部访谈调研汇报-交付冻结测试", "enabled": True},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))
            project_payload["巡检设置"]["推进任务ID"] = "advance-job"
            project_payload["巡检设置"]["汇报任务ID"] = "inspect-job"
            project_payload["巡检设置"]["是否已注册"] = True
            (project_dir / "项目总表.yaml").write_text(
                yaml.safe_dump(project_payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            result = mark_delivery_complete(
                project_dir=project_dir,
                delivered_at=_ts(),
                doc_url="https://example.com/doc",
                summary_message_id="om_123",
                cron_jobs_path=cron_jobs_path,
            )
            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))
            cron_payload = json.loads(cron_jobs_path.read_text(encoding="utf-8"))

            self.assertTrue(result["是否已发送最终报告"])
            self.assertEqual(project_payload["项目状态"], "已交付")
            self.assertTrue(project_payload["最终交付信息"]["是否已发送最终报告"])
            self.assertEqual(project_payload["最终交付信息"]["冻结版本号"], 1)
            self.assertEqual(project_payload["巡检设置"]["推进任务ID"], "")
            self.assertEqual(project_payload["巡检设置"]["汇报任务ID"], "")
            self.assertFalse(project_payload["巡检设置"]["是否已注册"])
            self.assertEqual(len(cron_payload["jobs"]), 0)
            self.assertTrue(project_payload["最终交付信息"]["冻结观察截止时间"])

    def test_mark_delivery_complete_keeps_completed_participants_unbound(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="交付后不重绑测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证交付后已完成对象保持未绑定",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人样本",
                project_deadline_at=_ts(hours_offset=-1),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="research-shared-jiaofu-jia",
                **_verified_binding_kwargs("ou_jia", "research-shared-jiaofu-jia"),
                last_message_id="om_jia_1",
                last_chat_id="oc_jia_1",
                last_outbound_at=_ts(hours_offset=-2),
                send_confirmation_status="已形成可回收 shared 会话",
                last_inbound_at=_ts(hours_offset=-1),
                summary="已完成",
                collected_signals=["是否使用过", "主要使用场景或主要阻力", "培训期待或改进方向"],
            )
            mark_delivery_complete(project_dir=project_dir, delivered_at=_ts())
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]

            self.assertEqual(participant["当前状态"], "已完成")
            self.assertEqual(participant["会话绑定状态"], "已解绑")

    def test_advance_blocks_when_any_participant_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="推进阻塞测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证推进前检查",
                research_scope="双人样本",
                participant_source_mode="直接名单",
                participant_scope_text="双人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[
                    {"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"},
                    {"姓名": "乙", "飞书标识": "user:ou_yi", "纳入原因": "成员"},
                ],
            )
            update_participant(
                project_dir=project_dir,
                    participant_name="甲",
                    status="待首发",
                    execution_session_id="session-jia",
                    execution_session_key="research-shared-tuijin-jia",
                    **_verified_binding_kwargs("ou_jia", "research-shared-tuijin-jia"),
                )

            result = advance_project(project_dir=project_dir)

            self.assertFalse(result["允许推进"])
            self.assertEqual(result["执行状态"], "已阻止")
            self.assertEqual(result["阻塞人数"], 1)
            self.assertEqual(result["阻塞对象"][0]["姓名"], "乙")

    def test_advance_blocks_when_binding_exists_but_real_session_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="推进真实会话检查",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证真实会话创建前不能首发",
                research_scope="单人样本",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_key="research-shared-tuijin-jia",
                **_verified_binding_kwargs("ou_jia", "research-shared-tuijin-jia"),
            )

            result = advance_project(project_dir=project_dir)

            self.assertFalse(result["允许推进"])
            self.assertEqual(result["执行状态"], "已阻止")
            self.assertEqual(result["阻塞人数"], 1)
            self.assertIn("未真实创建专属 shared 会话", result["阻塞对象"][0]["原因"])

    def test_register_cron_creates_advance_and_inspect_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            cron_jobs_path = Path(tmp) / "jobs.json"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="双任务注册测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证 cron 注册",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            result = register_project_check_job(project_dir=project_dir, cron_jobs_path=cron_jobs_path)
            cron_payload = json.loads(cron_jobs_path.read_text(encoding="utf-8"))
            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))

            self.assertEqual(len(cron_payload["jobs"]), 2)
            self.assertEqual(result["推进任务"]["cron表达式"], "*/10 * * * *")
            self.assertEqual(result["汇报任务"]["cron表达式"], "0 */3 * * *")
            self.assertTrue(project_payload["巡检设置"]["是否已注册"])
            self.assertTrue(project_payload["巡检设置"]["推进任务ID"])
            self.assertTrue(project_payload["巡检设置"]["汇报任务ID"])

    def test_close_project_unbinds_after_observation_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="观察期关闭测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证观察期关闭",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=-1),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                status="已关闭后回复",
                execution_session_id="session-jia",
                execution_session_key="research-shared-guancha-jia",
                **_verified_binding_kwargs("ou_jia", "research-shared-guancha-jia"),
            )
            finalize_project_on_deadline(project_dir=project_dir, now_at=_ts())
            mark_delivery_complete(project_dir=project_dir, delivered_at=_ts(hours_offset=-49))

            result = close_project(project_dir=project_dir, now_at=_ts())
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))

            self.assertEqual(result["项目状态"], "已关闭")
            self.assertEqual(participants_payload["受访对象列表"][0]["会话绑定状态"], "已解绑")
            self.assertEqual(participants_payload["受访对象列表"][0]["执行会话Key"], "")
            self.assertEqual(project_payload["当前阶段"], "已关闭")

    def test_recover_replies_backfills_yaml_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            gateway_log_path = Path(tmp) / "gateway.log"
            session_root = Path(tmp) / "sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="历史补回测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证历史补回",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_1234567890abcdef", "纳入原因": "成员"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="research-shared-openclaw-90cdef",
                **_verified_binding_kwargs("ou_1234567890abcdef", "research-shared-openclaw-90cdef"),
            )
            gateway_log_path.write_text(
                "\n".join(
                    [
                        "2026-05-22T20:02:38.668+08:00 [feishu] feishu[research]: received message from ou_1234567890abcdef in oc_xxx (p2p)",
                        "2026-05-22T20:02:38.674+08:00 [feishu] feishu[research]: routed via bound conversation ou_1234567890abcdef -> research-shared-openclaw-90cdef",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (session_root / "shared-session.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "custom_message",
                                "customType": "openclaw.runtime-context",
                                "content": "System: [2026-05-22 20:02:38 GMT+8] Feishu[research] DM | 甲 (ou_1234567890abcdef) [msg:om_1]",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "role": "user",
                                "content": [{"type": "text", "text": "已在使用，主要问题是上下文容易丢"}],
                                "timestamp": "2026-05-22T12:02:39.000Z",
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = recover_project_replies(
                project_dir=project_dir,
                gateway_log_path=gateway_log_path,
                session_root=session_root,
            )
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            note_path = Path(participants_payload["受访对象列表"][0]["访谈记录路径"])

            self.assertEqual(result["补回人数"], 1)
            self.assertEqual(participants_payload["受访对象列表"][0]["当前状态"], "访谈中")
            self.assertTrue(participants_payload["受访对象列表"][0]["最近回复时间"])
            self.assertTrue(participants_payload["受访对象列表"][0]["最近一次回收时间"])
            self.assertTrue(participants_payload["受访对象列表"][0]["是否已回收至research"])
            self.assertTrue(note_path.is_file())
            self.assertIn("上下文容易丢", note_path.read_text(encoding="utf-8"))

    def test_recover_replies_backfills_send_confirmation_from_research_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            gateway_log_path = Path(tmp) / "gateway.log"
            session_root = Path(tmp) / "shared-sessions"
            research_session_root = Path(tmp) / "research-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            research_session_root.mkdir(parents=True, exist_ok=True)
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="发送核验补偿测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证发送核验补偿",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_1234567890abcdef", "纳入原因": "成员"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="research-shared-openclaw-90cdef",
                **_verified_binding_kwargs("ou_1234567890abcdef", "research-shared-openclaw-90cdef"),
            )

            participants_path = project_dir / "受访对象清单.yaml"
            participants_payload = yaml.safe_load(participants_path.read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]
            participant["当前状态"] = "待回复"
            participant["最近发出时间"] = _ts(hours_offset=-2)
            participant["最近一次发送消息ID"] = "om_send_1"
            participant["最近一次发送chatID"] = ""
            participant["最近一次发送确认状态"] = "已调用发送"
            participants_path.write_text(
                yaml.safe_dump(participants_payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            (research_session_root / "research-session.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "toolResult",
                                    "toolName": "message",
                                    "details": {
                                        "ok": True,
                                        "messageId": "om_send_1",
                                        "chatId": "oc_send_1",
                                    },
                                },
                            },
                            ensure_ascii=False,
                        )
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = recover_project_replies(
                project_dir=project_dir,
                gateway_log_path=gateway_log_path,
                session_root=session_root,
                research_session_root=research_session_root,
            )
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]

            self.assertEqual(result["补回人数"], 0)
            self.assertEqual(result["shared发送补偿人数"], 0)
            self.assertEqual(result["发送核验补偿人数"], 1)
            self.assertEqual(participant["最近一次发送chatID"], "oc_send_1")
            self.assertEqual(participant["最近一次发送确认状态"], "发送记录存在但待人工确认")
            self.assertIn("message 工具返回", participant["最近一次发送确认依据"])

    def test_recover_replies_backfills_send_confirmation_from_shared_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            gateway_log_path = Path(tmp) / "gateway.log"
            session_root = Path(tmp) / "shared-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="shared发送补偿测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证 shared 会话发送补偿",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_1234567890abcdef", "纳入原因": "成员"}],
            )

            participants_path = project_dir / "受访对象清单.yaml"
            participants_payload = yaml.safe_load(participants_path.read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]
            participant["当前状态"] = "待绑定"
            participant["执行会话ID"] = ""
            participant["执行会话Key"] = "research-shared-openclaw-90cdef"
            participant["会话绑定ID"] = ""
            participant["会话绑定状态"] = "未绑定"
            participant["最近发出时间"] = "2026-05-23T11:24:54+08:00"
            participant["最近一次发送消息ID"] = "om_stale_old"
            participant["最近一次发送chatID"] = ""
            participant["最近一次发送确认状态"] = ""
            participants_path.write_text(
                yaml.safe_dump(participants_payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            (session_root / "shared-session.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "message",
                                "timestamp": "2026-05-23T05:08:53.270Z",
                                "message": {
                                    "role": "toolResult",
                                    "toolName": "feishu_conversation_binding",
                                    "details": {
                                        "action": "bind",
                                        "accountId": "research",
                                        "conversationId": "ou_1234567890abcdef",
                                        "已绑定": True,
                                        "绑定ID": "research:ou_1234567890abcdef",
                                        "绑定记录": {
                                            "targetSessionKey": "agent:research-shared:subagent:abc123",
                                            "agentId": "research-shared",
                                        },
                                    },
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "timestamp": "2026-05-23T05:09:10.000Z",
                                "message": {
                                    "role": "toolResult",
                                    "toolName": "feishu_conversation_binding",
                                    "details": {
                                        "action": "status",
                                        "accountId": "research",
                                        "conversationId": "ou_1234567890abcdef",
                                        "已绑定": True,
                                        "绑定记录": {
                                            "targetSessionKey": "agent:research-shared:subagent:abc123",
                                            "agentId": "research-shared",
                                        },
                                    },
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "timestamp": "2026-05-23T05:09:27.658Z",
                                "message": {
                                    "role": "toolResult",
                                    "toolName": "message",
                                    "details": {
                                        "ok": True,
                                        "messageId": "om_send_shared_1",
                                        "chatId": "oc_send_shared_1",
                                    },
                                },
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = recover_project_replies(
                project_dir=project_dir,
                gateway_log_path=gateway_log_path,
                session_root=session_root,
            )
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]

            self.assertEqual(result["shared发送补偿人数"], 1)
            self.assertEqual(result["发送核验补偿人数"], 0)
            self.assertEqual(participant["执行会话ID"], "shared-session")
            self.assertEqual(participant["执行会话Key"], "agent:research-shared:subagent:abc123")
            self.assertEqual(participant["会话绑定ID"], "research:ou_1234567890abcdef")
            self.assertEqual(participant["会话绑定状态"], "已绑定")
            self.assertEqual(participant["最近一次绑定目标会话Key"], "agent:research-shared:subagent:abc123")
            self.assertEqual(participant["最近一次绑定检查结果"], "已核验通过")
            self.assertEqual(participant["最近一次发送消息ID"], "om_send_shared_1")
            self.assertEqual(participant["最近一次发送chatID"], "oc_send_shared_1")
            self.assertEqual(participant["最近一次发送确认状态"], "已形成可回收 shared 会话")
            self.assertIn("shared 会话工具回执", participant["最近一次发送确认依据"])

    def test_update_participant_rejects_outbound_without_real_session_and_chat_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="状态校验测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证发出状态校验",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            with self.assertRaises(ValueError):
                update_participant(
                    project_dir=project_dir,
                    participant_name="甲",
                    status="待回复",
                    last_outbound_at=_ts(),
                )

            with self.assertRaises(ValueError):
                update_participant(
                    project_dir=project_dir,
                    participant_name="甲",
                    execution_session_id="session-jia",
                    execution_session_key="research-shared-jia",
                    **_verified_binding_kwargs("ou_jia", "research-shared-jia"),
                    last_outbound_at=_ts(),
                    last_message_id="om_jia_1",
                )

    def test_recover_replies_clears_half_baked_send_state_when_evidence_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            gateway_log_path = Path(tmp) / "gateway.log"
            session_root = Path(tmp) / "shared-sessions"
            research_session_root = Path(tmp) / "research-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            research_session_root.mkdir(parents=True, exist_ok=True)
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="半成品状态清理测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证半成品发送状态清理",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_1234567890abcdef", "纳入原因": "成员"}],
            )

            participants_path = project_dir / "受访对象清单.yaml"
            participants_payload = yaml.safe_load(participants_path.read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]
            participant["当前状态"] = "待回复"
            participant["执行会话ID"] = "session-jia"
            participant["执行会话Key"] = "research-shared-openclaw-90cdef"
            participant["会话绑定ID"] = "research:ou_1234567890abcdef"
            participant["会话绑定状态"] = "已绑定"
            participant["最近一次绑定确认时间"] = _ts(hours_offset=-2)
            participant["最近一次绑定确认依据"] = "status 校验通过"
            participant["最近一次绑定目标会话Key"] = "research-shared-openclaw-90cdef"
            participant["最近一次绑定检查结果"] = "已核验通过"
            participant["最近发出时间"] = _ts(hours_offset=-2)
            participant["最近一次发送消息ID"] = "om_missing_1"
            participant["最近一次发送chatID"] = ""
            participant["最近一次发送确认状态"] = ""
            participants_path.write_text(
                yaml.safe_dump(participants_payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            result = recover_project_replies(
                project_dir=project_dir,
                gateway_log_path=gateway_log_path,
                session_root=session_root,
                research_session_root=research_session_root,
            )
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]

            self.assertEqual(result["发送核验补偿人数"], 1)
            self.assertEqual(result["清理缺证据对象"], ["甲"])
            self.assertEqual(participant["最近发出时间"], "")
            self.assertEqual(participant["最近一次发送消息ID"], "")
            self.assertEqual(participant["最近一次发送chatID"], "")
            self.assertEqual(participant["最近一次发送确认状态"], "发送记录缺失")
            self.assertIn("已清理半成品状态", participant["最近一次链路状态"])

    def test_update_participant_clears_verified_binding_when_execution_session_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="旧绑定失效测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证切换 shared 会话后旧绑定失效",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                status="待首发",
                execution_session_id="session-old",
                execution_session_key="research-shared-old-jia",
                **_verified_binding_kwargs("ou_jia", "research-shared-old-jia"),
            )

            participant = update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-new",
                execution_session_key="research-shared-new-jia",
            )

            self.assertEqual(participant["执行会话Key"], "research-shared-new-jia")
            self.assertEqual(participant["会话绑定状态"], "未绑定")
            self.assertEqual(participant["会话绑定ID"], "")
            self.assertEqual(participant["最近一次绑定确认时间"], "")
            self.assertEqual(participant["最近一次绑定目标会话Key"], "")
            self.assertEqual(participant["最近一次绑定检查结果"], "执行会话已切换，旧绑定已失效")

    def test_update_participant_does_not_count_pre_send_inbound_as_shared_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="首发前入站测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证首发前入站不计回收",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_jia", "纳入原因": "成员"}],
            )

            participant = update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="research-shared-jia",
                **_verified_binding_kwargs("ou_jia", "research-shared-jia"),
                last_message_id="om_jia_1",
                last_chat_id="oc_jia_1",
                last_outbound_at="2026-05-23T19:06:00+08:00",
                send_confirmation_status="已形成可回收 shared 会话",
                last_inbound_at="2026-05-23T19:04:00+08:00",
            )

            self.assertEqual(participant["最近回复时间"], "")
            self.assertEqual(participant["最近一次回收时间"], "")
            self.assertFalse(participant["是否已回收至research"])
            self.assertEqual(participant["最近一次链路状态"], "首发前主对话消息")
            self.assertEqual(participant["最近一次业务状态"], "收到首发前入站，未计入本轮回收")

    def test_recover_replies_reports_main_dialog_route_when_reply_did_not_hit_shared(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            gateway_log_path = Path(tmp) / "gateway.log"
            session_root = Path(tmp) / "shared-sessions"
            research_session_root = Path(tmp) / "research-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            research_session_root.mkdir(parents=True, exist_ok=True)
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="主对话误路由测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证回复仍落主对话时不能误判为 shared 回收",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_1234567890abcdef", "纳入原因": "成员"}],
                project_type="链路验收",
            )
            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="agent:research-shared:subagent:jia",
                **_verified_binding_kwargs("ou_1234567890abcdef", "agent:research-shared:subagent:jia"),
                last_message_id="om_send_1",
                last_chat_id="oc_send_1",
                last_outbound_at="2026-05-23T19:06:00+08:00",
                send_confirmation_status="已形成可回收 shared 会话",
            )
            gateway_log_path.write_text(
                "\n".join(
                    [
                        "2026-05-23T19:04:36+08:00 [feishu] feishu[research]: received message from ou_1234567890abcdef in oc_xxx (p2p)",
                        "2026-05-23T19:04:36+08:00 [gateway] dispatching to agent (session=agent:research:feishu:direct:ou_1234567890abcdef)",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = recover_project_replies(
                project_dir=project_dir,
                gateway_log_path=gateway_log_path,
                session_root=session_root,
                research_session_root=research_session_root,
            )

            self.assertEqual(result["补回人数"], 0)
            self.assertEqual(result["shared已真实回收"], [])
            self.assertEqual(result["回复仍在主对话"], ["甲"])
            self.assertIn(
                {"姓名": "甲", "结果": "回复仍在主对话 / 未命中 shared"},
                result["首次回复路由核验"],
            )

    def test_recover_replies_uses_real_shared_transcript_and_auto_unbinds_completed_participant(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            gateway_log_path = Path(tmp) / "gateway.log"
            session_root = Path(tmp) / "shared-sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="真实 transcript 补偿测试",
                initiator_name="林经理",
                initiator_feishu_id="user:ou_lin",
                research_goal="验证 shared transcript 补偿后自动解绑",
                research_scope="单人",
                participant_source_mode="直接名单",
                participant_scope_text="单人",
                project_deadline_at=_ts(hours_offset=24),
                participants=[{"姓名": "甲", "飞书标识": "user:ou_1234567890abcdef", "纳入原因": "成员"}],
            )
            update_participant(
                project_dir=project_dir,
                participant_name="甲",
                execution_session_id="session-jia",
                execution_session_key="agent:research-shared:subagent:jia",
                **_verified_binding_kwargs("ou_1234567890abcdef", "agent:research-shared:subagent:jia"),
                last_message_id="om_send_1",
                last_chat_id="oc_send_1",
                last_outbound_at="2026-05-23T21:36:00+08:00",
                send_confirmation_status="已形成可回收 shared 会话",
            )
            gateway_log_path.write_text(
                "\n".join(
                    [
                        "2026-05-23T21:36:36.461+08:00 [feishu] feishu[research]: routed via bound conversation ou_1234567890abcdef -> agent:research-shared:subagent:jia",
                        "2026-05-23T21:39:10.791+08:00 [feishu] feishu[research]: routed via bound conversation ou_1234567890abcdef -> agent:research-shared:subagent:jia",
                        "2026-05-23T21:41:03.413+08:00 [feishu] feishu[research]: routed via bound conversation ou_1234567890abcdef -> agent:research-shared:subagent:jia",
                        "2026-05-23T21:46:58.955+08:00 [feishu] feishu[research]: routed via bound conversation ou_1234567890abcdef -> agent:research-shared:subagent:jia",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (session_root / "shared-session.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "assistant",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "嗨甲，我是内部调研助手。关于 openclaw / 小龙虾，你现在更接近哪种情况？请直接回复：经常用 / 用过几次 / 还没真正用 / 说不清。",
                                        }
                                    ],
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "custom_message",
                                "customType": "openclaw.runtime-context",
                                "content": "System: [2026-05-23 21:36 GMT+8] Feishu[research] DM | 甲 (ou_1234567890abcdef) [msg:om_1]",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "user",
                                    "content": [{"type": "text", "text": "基本每天都在用，用的频次非常高"}],
                                    "timestamp": "2026-05-23T13:37:27.000Z",
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "assistant",
                                    "content": [{"type": "text", "text": "NO_REPLY"}],
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "custom_message",
                                "customType": "openclaw.runtime-context",
                                "content": "System: [2026-05-23 21:39 GMT+8] Feishu[research] DM | 甲 (ou_1234567890abcdef) [msg:om_2]",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "user",
                                    "content": [{"type": "text", "text": "经常用"}],
                                    "timestamp": "2026-05-23T13:39:15.000Z",
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "assistant",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "你现在用 openclaw / 小龙虾时，主要更接近哪种情况？A. 上手或配置麻烦 B. 稳定性 / 速度有时不理想 C. 不太清楚哪些场景最该用它 D. 基本没明显卡点 E. 其他",
                                        }
                                    ],
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "custom_message",
                                "customType": "openclaw.runtime-context",
                                "content": "System: [2026-05-23 21:41 GMT+8] Feishu[research] DM | 甲 (ou_1234567890abcdef) [msg:om_3]",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "user",
                                    "content": [{"type": "text", "text": "稳定性 / 速度有时不理想"}],
                                    "timestamp": "2026-05-23T13:41:07.000Z",
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "assistant",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "如果只优先改一件事，你最希望先改哪类问题？A. 响应更快 B. 少报错、少失败 C. 结果更稳定一致 D. 操作链路更顺 E. 其他",
                                        }
                                    ],
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "custom_message",
                                "customType": "openclaw.runtime-context",
                                "content": "System: [2026-05-23 21:43 GMT+8] Feishu[research] DM | 甲 (ou_1234567890abcdef) [msg:om_4]",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "user",
                                    "content": [{"type": "text", "text": "b"}],
                                    "timestamp": "2026-05-23T13:43:17.000Z",
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "assistant",
                                    "content": [{"type": "text", "text": "感谢你，今天这轮小访谈就先到这里。"}],
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "custom_message",
                                "customType": "openclaw.runtime-context",
                                "content": "System: [2026-05-23 21:46 GMT+8] Feishu[research] DM | 甲 (ou_1234567890abcdef) [msg:om_5]",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "user",
                                    "content": [{"type": "text", "text": "好的"}],
                                    "timestamp": "2026-05-23T13:46:32.000Z",
                                },
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "custom_message",
                                "customType": "openclaw.runtime-context",
                                "content": "System: [2026-05-23 21:46 GMT+8] Feishu[research] DM | 甲 (ou_1234567890abcdef) [msg:om_6]",
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "type": "message",
                                "message": {
                                    "role": "user",
                                    "content": [{"type": "text", "text": "问完问题之后会自动解绑吗？"}],
                                    "timestamp": "2026-05-23T13:47:03.000Z",
                                },
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = recover_project_replies(
                project_dir=project_dir,
                gateway_log_path=gateway_log_path,
                session_root=session_root,
            )
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            participant = participants_payload["受访对象列表"][0]

            self.assertEqual(result["补回人数"], 1)
            self.assertEqual(participant["当前状态"], "已完成")
            self.assertEqual(participant["会话绑定状态"], "已解绑")
            self.assertEqual(participant["累计有效问题数"], 3)
            self.assertEqual(
                participant["已收集信号"],
                ["是否使用过", "主要使用场景或主要阻力", "培训期待或改进方向"],
            )
            self.assertTrue(participant["是否已达到收口条件"])
            self.assertEqual(participant["最近一次业务状态"], "已完成并自动解绑")

    def test_build_final_delivery_payload_returns_doc_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="绩效反馈访谈",
                initiator_name="何经理",
                initiator_feishu_id="user:ou_he",
                research_goal="梳理绩效反馈体验",
                research_scope="管理者与成员的绩效反馈体验",
                participant_source_mode="直接名单",
                participant_scope_text="管理者与成员",
                project_deadline_at=_ts(hours_offset=-1),
                participants=[{"姓名": "丙", "飞书标识": "user:ou_bing", "纳入原因": "成员"}],
            )

            finalize_project_on_deadline(project_dir=project_dir, now_at=_ts())
            payload = build_final_delivery_payload(project_dir=project_dir)

            self.assertEqual(payload["交付渠道"], "飞书文档+摘要消息")
            self.assertIn("绩效反馈访谈", payload["飞书文档标题"])
            self.assertIn("有效样本", payload["摘要消息"])
            self.assertEqual(payload["飞书文档创建参数"]["title"], payload["飞书文档标题"])
            self.assertEqual(payload["发起人飞书目标"], "user:ou_he")
            self.assertEqual(payload["飞书摘要消息发送参数"]["accountId"], "research")

    def test_prepare_feishu_delivery_writes_manifest_and_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp) / "workspace-research"
            project_dir = create_internal_interview_project(
                workspace_root=workspace_root,
                project_name="晋升反馈访谈",
                initiator_name="钱经理",
                initiator_feishu_id="ou_qian",
                research_goal="了解晋升反馈体验",
                research_scope="最近一次晋升评估参与人",
                participant_source_mode="直接名单",
                participant_scope_text="晋升评估参与人",
                project_deadline_at=_ts(hours_offset=-1),
                participants=[{"姓名": "丁", "飞书标识": "user:ou_ding", "纳入原因": "成员"}],
            )
            finalize_project_on_deadline(project_dir=project_dir, now_at=_ts())

            original_delivery_dir = project_module.飞书交付目录
            project_module.飞书交付目录 = Path(tmp) / "feishu-deliver"
            try:
                info = prepare_feishu_delivery(project_dir=project_dir)
            finally:
                project_module.飞书交付目录 = original_delivery_dir

            manifest_path = Path(info["交付清单路径"])
            self.assertTrue(manifest_path.is_file())
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["preferred_delivery"], "feishu_doc_then_message")
            self.assertEqual(manifest["target"]["target"], "user:ou_qian")
            self.assertEqual(manifest["target"]["accountId"], "research")
            self.assertIn("feishu_create_doc", manifest["agent_delivery_contract"]["preferred_sequence"][0]["tool"])
            self.assertTrue(Path(info["报告发送副本"]).is_file())


if __name__ == "__main__":
    unittest.main()
