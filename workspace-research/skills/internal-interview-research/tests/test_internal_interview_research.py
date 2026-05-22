import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import internal_interview_research.project as project_module  # type: ignore
from internal_interview_research.project import (  # type: ignore
    build_final_delivery_payload,
    build_participant_outreach_plan,
    create_internal_interview_project,
    finalize_project_on_deadline,
    evaluate_project_actions,
    prepare_feishu_delivery,
    stop_project_and_cleanup,
    update_participant,
    update_project_deadline,
)


def _ts(hours_offset: int = 0) -> str:
    return (datetime.now().astimezone() + timedelta(hours=hours_offset)).isoformat()


class InternalInterviewResearchTests(unittest.TestCase):
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
            self.assertEqual(participants_payload["受访对象列表"][0]["当前状态"], "待联系")
            self.assertEqual(project_payload["访谈执行设置"]["发送账号标识"], "research")
            self.assertTrue(project_payload["访谈执行设置"]["禁止使用用户身份发送"])
            self.assertEqual(project_payload["访谈策略"]["默认提问方式"], "判断题优先")
            self.assertEqual(project_payload["访谈策略"]["默认交互形态"], "按钮卡片优先")
            self.assertEqual(project_payload["访谈策略"]["首轮结构"], "说明消息+1个判断题卡片")
            self.assertEqual(project_payload["访谈策略"]["单人有效问题上限"], 4)
            self.assertEqual(participants_payload["受访对象列表"][0]["最近一次提问方式"], "")
            self.assertEqual(participants_payload["受访对象列表"][0]["累计按钮题次数"], 0)
            self.assertEqual(participants_payload["受访对象列表"][0]["累计选择题次数"], 0)
            self.assertEqual(participants_payload["受访对象列表"][0]["累计开放题次数"], 0)

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
            )
            actions = evaluate_project_actions(project_dir=project_dir, now_at=_ts())
            self.assertEqual(actions["受访对象动作"][0]["建议动作"], "第一次跟进")

            update_participant(
                project_dir=project_dir,
                participant_name="吴一",
                status="待回复",
                last_outbound_at=_ts(hours_offset=-13),
                followup_count=1,
            )
            actions = evaluate_project_actions(project_dir=project_dir, now_at=_ts())
            self.assertEqual(actions["受访对象动作"][0]["建议动作"], "第二次跟进")

    def test_build_first_touch_plan_uses_research_button_card(self):
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

            plan = build_participant_outreach_plan(project_dir=project_dir, participant_name="肖宁劼")

            self.assertTrue(plan["允许发送"])
            self.assertEqual(plan["发送账号标识"], "research")
            self.assertIn("feishu_im_user_message", plan["禁止工具"])
            self.assertEqual(plan["首轮触达"]["提问方式"], "判断题")
            self.assertEqual(plan["首轮触达"]["交互形态"], "按钮卡片")
            self.assertEqual(len(plan["首轮触达"]["卡片"]["options"]), 2)
            self.assertIn("只占用你 1 分钟", plan["说明消息"])

    def test_build_first_touch_plan_falls_back_to_text_options_when_card_unavailable(self):
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

            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                card_supported=False,
            )

            self.assertTrue(plan["允许发送"])
            self.assertEqual(plan["首轮触达"]["交互形态"], "文本选项")
            self.assertIn("请直接回复", plan["首轮触达"]["文本降级消息"])
            self.assertEqual(plan["首轮触达"]["提问方式"], "判断题")

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

            plan = build_participant_outreach_plan(
                project_dir=project_dir,
                participant_name="肖宁劼",
                research_account_ready=False,
            )

            self.assertFalse(plan["允许发送"])
            self.assertEqual(plan["建议动作"], "暂停并通知发起人")
            self.assertIn("research 账号当前不可用", plan["阻止原因"])

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
            )
            update_participant(
                project_dir=project_dir,
                participant_name="乙",
                status="待回复",
                last_outbound_at=_ts(hours_offset=-2),
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
            update_participant(project_dir=project_dir, participant_name="乙", status="待回复", last_outbound_at=_ts(hours_offset=-10))

            result = finalize_project_on_deadline(project_dir=project_dir, now_at=_ts())
            participants_payload = yaml.safe_load((project_dir / "受访对象清单.yaml").read_text(encoding="utf-8"))
            project_payload = yaml.safe_load((project_dir / "项目总表.yaml").read_text(encoding="utf-8"))

            self.assertEqual(result["已超时人数"], 1)
            self.assertEqual(participants_payload["受访对象列表"][1]["当前状态"], "已超时")
            self.assertEqual(project_payload["当前阶段"], "分析总结")
            self.assertIn("仍有 1 位受访对象未完成", project_payload["分析收口"]["样本缺口说明"])

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
            self.assertIn("样本覆盖", payload["摘要消息"])
            self.assertEqual(payload["飞书文档创建参数"]["title"], payload["飞书文档标题"])
            self.assertEqual(payload["发起人飞书目标"], "user:ou_he")

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
            self.assertIn("feishu_create_doc", manifest["agent_delivery_contract"]["preferred_sequence"][0]["tool"])
            self.assertTrue(Path(info["报告发送副本"]).is_file())


if __name__ == "__main__":
    unittest.main()
