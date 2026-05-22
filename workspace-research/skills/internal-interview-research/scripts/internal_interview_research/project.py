from __future__ import annotations

import json
import shutil
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml


终态状态 = {"已完成", "已超时", "已拒绝"}
待回复状态 = {"已邀约", "待回复", "已停滞"}
项目阶段 = ["立项", "问题设计", "受访对象确认", "访谈进行中", "分析总结", "已关闭"]
飞书交付目录 = Path("/Users/a123/.openclaw/workspace/feishu-deliver")
关键收口信号 = ["是否使用过", "主要使用场景或主要阻力", "培训期待或改进方向"]


def _默认访谈执行设置() -> dict[str, Any]:
    return {
        "发送账号标识": "research",
        "禁止使用用户身份发送": True,
        "账号异常处理": "暂停并通知发起人",
        "允许备用发送账号": False,
    }


def _默认访谈策略() -> dict[str, Any]:
    return {
        "默认提问方式": "判断题优先",
        "默认交互形态": "按钮卡片优先",
        "开放问答最晚触发条件": "按钮题和选择题仍不足以拿到关键信息时，且一次只问1个问题",
        "首轮结构": "说明消息+1个判断题卡片",
        "单人有效问题上限": 4,
        "首轮问题上限": 2,
        "追问总上限": 2,
        "单轮最多追问": 1,
        "收口信号": list(关键收口信号),
    }


def _现在() -> datetime:
    return datetime.now().astimezone()


def _现在字符串() -> str:
    return _现在().isoformat()


def _解析时间(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _写入_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _读取_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _读取结构化文件(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return yaml.safe_load(raw) or {}


def _写入文本(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _项目编号(project_name: str) -> str:
    return f"research-{_现在().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6]}"


def _唯一文件路径(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-v{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _标准飞书目标(open_id_or_target: str) -> str:
    raw = str(open_id_or_target or "").strip()
    if not raw:
        return ""
    if raw.startswith(("user:", "chat:")):
        return raw
    if raw.startswith("ou_"):
        return f"user:{raw}"
    if raw.startswith("oc_"):
        return f"chat:{raw}"
    return raw


def _标准受访对象(record: dict[str, Any]) -> dict[str, Any]:
    collected_signals = record.get("已收集信号", [])
    if not isinstance(collected_signals, list):
        collected_signals = []
    return {
        "姓名": record.get("姓名", "").strip(),
        "飞书标识": record.get("飞书标识", "").strip(),
        "纳入原因": record.get("纳入原因", "").strip(),
        "当前状态": record.get("当前状态", "待联系"),
        "最近发出时间": record.get("最近发出时间", ""),
        "最近回复时间": record.get("最近回复时间", ""),
        "已跟进次数": int(record.get("已跟进次数", 0) or 0),
        "访谈记录路径": record.get("访谈记录路径", ""),
        "完成摘要": record.get("完成摘要", ""),
        "截止提醒已发送": bool(record.get("截止提醒已发送", False)),
        "访谈轮次记录": list(record.get("访谈轮次记录", [])),
        "发送账号标识": record.get("发送账号标识", "research"),
        "首条消息工具": record.get("首条消息工具", ""),
        "会话归属账号": record.get("会话归属账号", "research"),
        "最近一次提问方式": record.get("最近一次提问方式", ""),
        "最近一次卡片类型": record.get("最近一次卡片类型", ""),
        "累计按钮题次数": int(record.get("累计按钮题次数", 0) or 0),
        "累计选择题次数": int(record.get("累计选择题次数", 0) or 0),
        "累计开放题次数": int(record.get("累计开放题次数", 0) or 0),
        "累计有效问题数": int(record.get("累计有效问题数", 0) or 0),
        "已收集信号": list(dict.fromkeys(str(item).strip() for item in collected_signals if str(item).strip())),
        "是否已达到收口条件": bool(record.get("是否已达到收口条件", False)),
        "收口原因": record.get("收口原因", ""),
    }


def _统计样本(participants: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "总人数": len(participants),
        "待联系人数": 0,
        "待回复人数": 0,
        "访谈中人数": 0,
        "已完成人数": 0,
        "已停滞人数": 0,
        "已超时人数": 0,
        "已拒绝人数": 0,
    }
    for participant in participants:
        status = participant.get("当前状态", "待联系")
        if status == "待联系":
            counts["待联系人数"] += 1
        elif status in {"已邀约", "待回复"}:
            counts["待回复人数"] += 1
        elif status == "访谈中":
            counts["访谈中人数"] += 1
        elif status == "已完成":
            counts["已完成人数"] += 1
        elif status == "已停滞":
            counts["已停滞人数"] += 1
        elif status == "已超时":
            counts["已超时人数"] += 1
        elif status == "已拒绝":
            counts["已拒绝人数"] += 1
    return counts


def _去重信号(signals: list[str]) -> list[str]:
    return list(dict.fromkeys(signal for signal in signals if signal))


def _已命中收口信号(participant: dict[str, Any]) -> list[str]:
    signals = participant.get("已收集信号", [])
    if not isinstance(signals, list):
        return []
    normalized = {str(signal).strip() for signal in signals if str(signal).strip()}
    return [signal for signal in 关键收口信号 if signal in normalized]


def _是否达到收口条件(participant: dict[str, Any]) -> bool:
    if participant.get("是否已达到收口条件", False):
        return True
    return len(_已命中收口信号(participant)) >= len(关键收口信号)


def _更新收口状态(participant: dict[str, Any]) -> None:
    hit_signals = _已命中收口信号(participant)
    enough = len(hit_signals) >= len(关键收口信号)
    participant["是否已达到收口条件"] = enough
    if enough:
        participant["收口原因"] = "已覆盖是否使用过、主要使用场景或主要阻力、培训期待或改进方向，不要继续追问。"
    elif not participant.get("收口原因"):
        participant["收口原因"] = ""


def _是否可开始自动访谈(
    project_deadline_at: str,
    participant_source_mode: str,
    participants: list[dict[str, Any]],
    suggestions_pending: bool,
) -> bool:
    return bool(project_deadline_at) and participant_source_mode == "直接名单" and not suggestions_pending and len(participants) > 0


def _项目总表(
    project_dir: Path,
    project_name: str,
    initiator_name: str,
    initiator_feishu_id: str,
    research_goal: str,
    research_scope: str,
    participant_source_mode: str,
    participant_scope_text: str,
    project_deadline_at: str,
    participants: list[dict[str, Any]],
) -> dict[str, Any]:
    suggestions_pending = participant_source_mode == "范围建议"
    auto_ready = _是否可开始自动访谈(
        project_deadline_at=project_deadline_at,
        participant_source_mode=participant_source_mode,
        participants=participants,
        suggestions_pending=suggestions_pending,
    )
    return {
        "项目名称": project_name,
        "项目编号": _项目编号(project_name),
        "项目目录": str(project_dir),
        "发起人": {
            "姓名": initiator_name,
            "飞书标识": initiator_feishu_id,
        },
        "调研目标": research_goal,
        "调研范围": research_scope,
        "受访对象来源方式": participant_source_mode,
        "受访对象范围说明": participant_scope_text,
        "建议名单待确认": suggestions_pending,
        "是否可进入自动访谈": bool(project_deadline_at) and not suggestions_pending,
        "是否可直接开始批量访谈": auto_ready,
        "项目开始时间": _现在字符串(),
        "项目截止时间": project_deadline_at,
        "当前阶段": "立项",
        "项目状态": "进行中",
        "访谈执行设置": _默认访谈执行设置(),
        "访谈策略": _默认访谈策略(),
        "跟进策略": {
            "首次跟进间隔小时": 6,
            "第二次跟进间隔小时": 12,
            "最终截止提醒提前小时": 6,
            "最大跟进次数": 2,
        },
        "截止时间变更记录": [],
        "巡检设置": {
            "巡检间隔分钟": 30,
            "巡检任务ID": "",
            "是否已注册": False,
            "上次巡检时间": "",
            "下次建议巡检时间": "",
        },
        "最终交付信息": {
            "交付渠道": "飞书文档+摘要消息",
            "发起人飞书标识": initiator_feishu_id,
            "飞书文档标题": f"{project_name} - 内部访谈调研报告",
            "摘要消息状态": "待生成",
            "最近交付时间": "",
        },
        "样本概况": _统计样本(participants),
        "分析收口": {
            "是否允许带缺口收口": True,
            "收口触发条件": "全部完成或到达截止时间",
            "样本缺口说明": "",
            "最终收口时间": "",
        },
        "停止信息": {
            "是否已停止": False,
            "停止时间": "",
            "停止原因": "",
            "停止人": "",
        },
    }


def _受访对象清单(project_name: str, participants: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [_标准受访对象(participant) for participant in participants]
    for participant in normalized:
        _更新收口状态(participant)
    return {
        "项目名称": project_name,
        "更新时间": _现在字符串(),
        "受访对象列表": normalized,
    }


def _发起人纪要模板(project_name: str, initiator_name: str, research_goal: str, research_scope: str) -> str:
    return (
        f"# {project_name} 发起人访谈纪要\n\n"
        f"## 发起人\n\n- 姓名：{initiator_name}\n\n"
        f"## 调研目标\n\n{research_goal}\n\n"
        f"## 调研范围\n\n{research_scope}\n\n"
        "## 成功标准\n\n- 待补充\n\n"
        "## 已确认限制\n\n- 待补充\n\n"
        "## 待确认问题\n\n- 待补充\n"
    )


def _问题清单模板(project_name: str) -> str:
    return (
        f"# {project_name} 调研问题清单\n\n"
        "## 核心问题\n\n- 待补充\n\n"
        "## 追问问题\n\n- 待补充\n\n"
        "## 不问边界\n\n- 待补充\n\n"
        "## 访谈结束判断标准\n\n- 关键问题已覆盖\n- 样本内主要分歧已显现\n"
    )


def _阶段总结模板(project_name: str) -> str:
    return (
        f"# {project_name} 阶段总结\n\n"
        "## 当前阶段\n\n- 立项\n\n"
        "## 关键进展\n\n- 待补充\n\n"
        "## 风险与缺口\n\n- 待补充\n\n"
        "## 下一步动作\n\n- 待补充\n"
    )


def _最终报告模板(project_name: str) -> str:
    return (
        f"# {project_name} 最终调研报告\n\n"
        "## 一、调研目标\n\n- 待补充\n\n"
        "## 二、样本覆盖\n\n- 总人数：0\n- 已完成：0\n- 已超时：0\n- 已拒绝：0\n\n"
        "## 三、核心发现\n\n- 待补充\n\n"
        "## 四、样本缺口\n\n- 待补充\n\n"
        "## 五、建议动作\n\n- 待补充\n"
    )


def _确保项目目录(project_dir: Path) -> None:
    if project_dir.exists():
        raise FileExistsError(f"项目目录已存在：{project_dir}")
    for relative in ("访谈记录", "输出", "附件"):
        (project_dir / relative).mkdir(parents=True, exist_ok=True)


def _读取项目(project_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    project_payload = _读取_yaml(project_dir / "项目总表.yaml")
    participants_payload = _读取_yaml(project_dir / "受访对象清单.yaml")
    return project_payload, participants_payload


def _写回项目(project_dir: Path, project_payload: dict[str, Any], participants_payload: dict[str, Any]) -> None:
    participants_payload["更新时间"] = _现在字符串()
    project_payload["样本概况"] = _统计样本(participants_payload["受访对象列表"])
    _写入_yaml(project_dir / "项目总表.yaml", project_payload)
    _写入_yaml(project_dir / "受访对象清单.yaml", participants_payload)


def create_internal_interview_project(
    workspace_root: Path,
    project_name: str,
    initiator_name: str,
    initiator_feishu_id: str,
    research_goal: str,
    research_scope: str,
    participant_source_mode: str,
    participant_scope_text: str,
    project_deadline_at: str,
    participants: list[dict[str, Any]] | None = None,
) -> Path:
    participants = participants or []
    project_dir = workspace_root / "projects" / project_name
    _确保项目目录(project_dir)

    project_payload = _项目总表(
        project_dir=project_dir,
        project_name=project_name,
        initiator_name=initiator_name,
        initiator_feishu_id=initiator_feishu_id,
        research_goal=research_goal,
        research_scope=research_scope,
        participant_source_mode=participant_source_mode,
        participant_scope_text=participant_scope_text,
        project_deadline_at=project_deadline_at,
        participants=participants,
    )
    participants_payload = _受访对象清单(project_name, participants)

    _写入_yaml(project_dir / "项目总表.yaml", project_payload)
    _写入_yaml(project_dir / "受访对象清单.yaml", participants_payload)
    _写入文本(
        project_dir / "发起人访谈纪要.md",
        _发起人纪要模板(project_name, initiator_name, research_goal, research_scope),
    )
    _写入文本(project_dir / "调研问题清单.md", _问题清单模板(project_name))
    _写入文本(project_dir / "阶段总结.md", _阶段总结模板(project_name))
    _写入文本(project_dir / "最终调研报告.md", _最终报告模板(project_name))
    return project_dir


def update_project_deadline(
    project_dir: Path,
    new_deadline_at: str,
    changed_by: str,
    reason: str,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    old_deadline = project_payload.get("项目截止时间", "")
    record = {
        "原截止时间": old_deadline,
        "新截止时间": new_deadline_at,
        "变更时间": _现在字符串(),
        "变更原因": reason,
        "变更人": changed_by,
    }
    project_payload.setdefault("截止时间变更记录", []).append(record)
    project_payload["项目截止时间"] = new_deadline_at
    suggestions_pending = bool(project_payload.get("建议名单待确认", False))
    participants = participants_payload.get("受访对象列表", [])
    project_payload["是否可进入自动访谈"] = bool(new_deadline_at) and not suggestions_pending
    project_payload["是否可直接开始批量访谈"] = _是否可开始自动访谈(
        project_deadline_at=new_deadline_at,
        participant_source_mode=project_payload.get("受访对象来源方式", ""),
        participants=participants,
        suggestions_pending=suggestions_pending,
    )
    project_payload["巡检设置"]["下次建议巡检时间"] = (_现在() + timedelta(minutes=30)).isoformat()
    _写回项目(project_dir, project_payload, participants_payload)
    return record


def update_participant(
    project_dir: Path,
    participant_name: str,
    status: str | None = None,
    feishu_id: str | None = None,
    note_path: str | None = None,
    summary: str | None = None,
    last_outbound_at: str | None = None,
    last_inbound_at: str | None = None,
    followup_count: int | None = None,
    inclusion_reason: str | None = None,
    deadline_reminder_sent: bool | None = None,
    confirm_suggested_list: bool | None = None,
    question_mode: str | None = None,
    card_type: str | None = None,
    button_question_count: int | None = None,
    choice_question_count: int | None = None,
    open_question_count: int | None = None,
    effective_question_count: int | None = None,
    collected_signals: list[str] | None = None,
    sender_account: str | None = None,
    first_message_tool: str | None = None,
    conversation_account: str | None = None,
    closure_reached: bool | None = None,
    closure_reason: str | None = None,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    target = None
    for participant in participants_payload.get("受访对象列表", []):
        if participant.get("姓名") == participant_name:
            target = participant
            break
    if target is None:
        raise KeyError(f"未找到受访对象：{participant_name}")

    if status is not None:
        target["当前状态"] = status
    if feishu_id is not None:
        target["飞书标识"] = feishu_id
    if note_path is not None:
        target["访谈记录路径"] = note_path
    if summary is not None:
        target["完成摘要"] = summary
    if last_outbound_at is not None:
        target["最近发出时间"] = last_outbound_at
        target.setdefault("访谈轮次记录", []).append({"时间": last_outbound_at, "动作": "发出消息"})
    if last_inbound_at is not None:
        target["最近回复时间"] = last_inbound_at
        target.setdefault("访谈轮次记录", []).append({"时间": last_inbound_at, "动作": "收到回复"})
    if followup_count is not None:
        target["已跟进次数"] = int(followup_count)
    if inclusion_reason is not None:
        target["纳入原因"] = inclusion_reason
    if deadline_reminder_sent is not None:
        target["截止提醒已发送"] = deadline_reminder_sent
    if question_mode is not None:
        target["最近一次提问方式"] = question_mode
    if card_type is not None:
        target["最近一次卡片类型"] = card_type
    if button_question_count is not None:
        target["累计按钮题次数"] = int(button_question_count)
    if choice_question_count is not None:
        target["累计选择题次数"] = int(choice_question_count)
    if open_question_count is not None:
        target["累计开放题次数"] = int(open_question_count)
    if effective_question_count is not None:
        target["累计有效问题数"] = int(effective_question_count)
    if collected_signals is not None:
        existing = target.get("已收集信号", [])
        if not isinstance(existing, list):
            existing = []
        target["已收集信号"] = _去重信号(existing + [str(item).strip() for item in collected_signals if str(item).strip()])
    if sender_account is not None:
        target["发送账号标识"] = sender_account
    if first_message_tool is not None:
        target["首条消息工具"] = first_message_tool
    if conversation_account is not None:
        target["会话归属账号"] = conversation_account
    if closure_reached is not None:
        target["是否已达到收口条件"] = closure_reached
    if closure_reason is not None:
        target["收口原因"] = closure_reason

    _更新收口状态(target)

    if target.get("当前状态") in {"访谈中", "已完成"} and project_payload.get("当前阶段") in {"立项", "问题设计", "受访对象确认"}:
        project_payload["当前阶段"] = "访谈进行中"
    if confirm_suggested_list:
        project_payload["建议名单待确认"] = False

    suggestions_pending = bool(project_payload.get("建议名单待确认", False))
    project_payload["是否可进入自动访谈"] = bool(project_payload.get("项目截止时间")) and not suggestions_pending
    project_payload["是否可直接开始批量访谈"] = _是否可开始自动访谈(
        project_deadline_at=project_payload.get("项目截止时间", ""),
        participant_source_mode=project_payload.get("受访对象来源方式", ""),
        participants=participants_payload.get("受访对象列表", []),
        suggestions_pending=suggestions_pending,
    )
    _写回项目(project_dir, project_payload, participants_payload)
    return deepcopy(target)


def _首轮说明消息(project_payload: dict[str, Any], participant: dict[str, Any]) -> str:
    project_name = project_payload.get("项目名称", "")
    return (
        f"嗨{participant.get('姓名', '')}，我是 research。"
        f"这边在做“{project_name}”的小范围内部访谈，只占用你 1 分钟做个很轻的了解。"
        "你点一下选项就行，不需要长篇回复。"
    )


def _判断题按钮卡片(project_payload: dict[str, Any], participant: dict[str, Any]) -> dict[str, Any]:
    question = "最近 7 天，你有实际用过这次调研涉及的产品或流程吗？"
    options = [
        {"text": "用过", "value": "是否使用过:用过"},
        {"text": "还没用", "value": "是否使用过:还没用"},
    ]
    payload = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"{participant.get('姓名', '')} 轻量访谈"},
            "template": "blue",
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**{question}**"}},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": option["text"]},
                        "type": "primary" if index == 0 else "default",
                        "value": {
                            "项目名称": project_payload.get("项目名称", ""),
                            "受访对象": participant.get("姓名", ""),
                            "提问方式": "判断题",
                            "答案": option["text"],
                            "信号": "是否使用过",
                        },
                    }
                    for index, option in enumerate(options)
                ],
            },
            {
                "tag": "note",
                "elements": [
                    {"tag": "plain_text", "content": "点一下就行，不需要长篇回复。"}
                ],
            },
        ],
    }
    return {
        "类型": "判断题按钮卡片",
        "question": question,
        "options": options,
        "payload": payload,
    }


def _判断题文本降级消息(card: dict[str, Any]) -> str:
    options = card.get("options", [])
    option_text = " / ".join(str(item.get("text", "")).strip() for item in options if str(item.get("text", "")).strip())
    return f"{card.get('question', '')}\n请直接回复：{option_text}"


def build_participant_outreach_plan(
    project_dir: Path,
    participant_name: str,
    research_account_ready: bool = True,
    card_supported: bool = True,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    participant = None
    for item in participants_payload.get("受访对象列表", []):
        if item.get("姓名") == participant_name:
            participant = _标准受访对象(item)
            break
    if participant is None:
        raise KeyError(f"未找到受访对象：{participant_name}")

    execution_settings = project_payload.get("访谈执行设置", _默认访谈执行设置())
    strategy = project_payload.get("访谈策略", _默认访谈策略())

    base_plan = {
        "项目名称": project_payload.get("项目名称", ""),
        "受访对象": participant.get("姓名", ""),
        "发送账号标识": execution_settings.get("发送账号标识", "research"),
        "禁止工具": ["feishu_im_user_message"],
        "已达到收口条件": _是否达到收口条件(participant),
    }

    if not research_account_ready:
        return {
            **base_plan,
            "允许发送": False,
            "建议动作": "暂停并通知发起人",
            "阻止原因": "research 账号当前不可用，不能切到你的个人身份，也不允许备用账号代发。",
        }
    if not project_payload.get("项目截止时间"):
        return {
            **base_plan,
            "允许发送": False,
            "建议动作": "暂停并通知发起人",
            "阻止原因": "当前缺少项目截止时间，自动访谈仍被阻止。",
        }
    if not participant.get("飞书标识"):
        return {
            **base_plan,
            "允许发送": False,
            "建议动作": "补充受访对象信息",
            "阻止原因": "受访对象缺少飞书标识，当前不能发起私聊。",
        }
    if _是否达到收口条件(participant):
        return {
            **base_plan,
            "允许发送": True,
            "建议动作": "直接收口",
            "收口说明": participant.get("收口原因") or "已拿到足够信号，不要继续追问。",
            "收口消息": "谢谢，信息已经足够了。我先整理这轮结论，后面如有必要再补充联系你。",
        }

    intro = _首轮说明消息(project_payload, participant)
    first_touch_card = _判断题按钮卡片(project_payload, participant)
    interaction_mode = "按钮卡片" if card_supported else "文本选项"

    return {
        **base_plan,
        "允许发送": True,
        "建议动作": "发起首次邀约" if participant.get("当前状态") == "待联系" else "继续轻量跟进",
        "说明消息": intro,
        "后续规则": {
            "默认提问方式": strategy.get("默认提问方式", "判断题优先"),
            "默认交互形态": strategy.get("默认交互形态", "按钮卡片优先"),
            "开放问答最晚触发条件": strategy.get("开放问答最晚触发条件", ""),
            "单人有效问题上限": strategy.get("单人有效问题上限", 4),
            "单轮最多追问": strategy.get("单轮最多追问", 1),
        },
        "首轮触达": {
            "提问方式": "判断题",
            "交互形态": interaction_mode,
            "信息目标": "是否使用过",
            "卡片": first_touch_card,
            "文本降级消息": _判断题文本降级消息(first_touch_card),
        },
    }


def evaluate_project_actions(project_dir: Path, now_at: str | None = None) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    now = _解析时间(now_at) if now_at else _现在()
    if now is None:
        now = _现在()
    deadline = _解析时间(project_payload.get("项目截止时间", ""))
    strategy = project_payload.get("跟进策略", {})
    first_hours = int(strategy.get("首次跟进间隔小时", 6))
    second_hours = int(strategy.get("第二次跟进间隔小时", 12))
    final_hours = int(strategy.get("最终截止提醒提前小时", 6))

    project_actions: list[dict[str, str]] = []
    participant_actions: list[dict[str, str]] = []

    if not deadline:
        project_actions.append({"建议动作": "补充截止时间", "原因": "尚未提供项目截止时间，自动访谈仍被阻止"})
    if project_payload.get("建议名单待确认"):
        project_actions.append({"建议动作": "确认建议名单", "原因": "当前是范围建议模式，需先确认受访对象名单"})
    if deadline and now >= deadline:
        project_actions.append({"建议动作": "进入截止收口", "原因": "已达到项目截止时间"})

    for participant in participants_payload.get("受访对象列表", []):
        action = "继续等待"
        reason = "当前无需动作"
        status = participant.get("当前状态", "待联系")

        if deadline and now >= deadline and status not in 终态状态:
            action = "到期封口"
            reason = "已到项目截止时间"
        elif status == "待联系" and project_payload.get("是否可直接开始批量访谈"):
            action = "发起首次邀约"
            reason = "已具备自动访谈条件"
        elif deadline and status in 待回复状态:
            remaining_hours = (deadline - now).total_seconds() / 3600
            if remaining_hours <= final_hours and not participant.get("截止提醒已发送", False):
                action = "最终截止提醒"
                reason = f"距离截止不足 {final_hours} 小时"
            else:
                last_outbound = _解析时间(participant.get("最近发出时间", ""))
                followups = int(participant.get("已跟进次数", 0) or 0)
                if last_outbound:
                    elapsed_hours = (now - last_outbound).total_seconds() / 3600
                    if followups <= 0 and elapsed_hours >= first_hours:
                        action = "第一次跟进"
                        reason = f"距离上次发出消息已超过 {first_hours} 小时"
                    elif followups == 1 and elapsed_hours >= second_hours:
                        action = "第二次跟进"
                        reason = f"距离上次发出消息已超过 {second_hours} 小时"

        participant_actions.append(
            {
                "姓名": participant.get("姓名", ""),
                "当前状态": status,
                "建议动作": action,
                "原因": reason,
            }
        )

    project_payload["巡检设置"]["上次巡检时间"] = now.isoformat()
    project_payload["巡检设置"]["下次建议巡检时间"] = (now + timedelta(minutes=int(project_payload["巡检设置"].get("巡检间隔分钟", 30)))).isoformat()
    _写回项目(project_dir, project_payload, participants_payload)

    return {
        "项目名称": project_payload.get("项目名称", ""),
        "当前阶段": project_payload.get("当前阶段", ""),
        "项目动作": project_actions,
        "受访对象动作": participant_actions,
    }


def finalize_project_on_deadline(project_dir: Path, now_at: str | None = None) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    now = _解析时间(now_at) if now_at else _现在()
    if now is None:
        now = _现在()
    deadline = _解析时间(project_payload.get("项目截止时间", ""))
    if deadline and now < deadline:
        return {"已超时人数": 0, "项目状态": project_payload.get("项目状态", "")}

    timed_out_count = 0
    for participant in participants_payload.get("受访对象列表", []):
        if participant.get("当前状态") not in 终态状态:
            participant["当前状态"] = "已超时"
            participant["完成摘要"] = participant.get("完成摘要") or "截止时间已到，未能完成访谈。"
            timed_out_count += 1

    summary = _统计样本(participants_payload.get("受访对象列表", []))
    gap_count = summary["已超时人数"] + summary["待回复人数"] + summary["待联系人数"] + summary["已停滞人数"]
    if gap_count > 0:
        gap_text = f"仍有 {gap_count} 位受访对象未完成，结论基于当前已回收样本输出。"
    else:
        gap_text = "所有受访对象已完成或已明确拒绝，当前结论不存在样本缺口。"

    project_payload["当前阶段"] = "分析总结"
    project_payload["项目状态"] = "待交付"
    project_payload["分析收口"]["样本缺口说明"] = gap_text
    project_payload["分析收口"]["最终收口时间"] = now.isoformat()

    report = (
        f"# {project_payload['项目名称']} 最终调研报告\n\n"
        "## 一、调研目标\n\n"
        f"- {project_payload['调研目标']}\n\n"
        "## 二、样本覆盖\n\n"
        f"- 总人数：{summary['总人数']}\n"
        f"- 已完成：{summary['已完成人数']}\n"
        f"- 已超时：{summary['已超时人数']}\n"
        f"- 已拒绝：{summary['已拒绝人数']}\n\n"
        "## 三、核心发现\n\n- 待补充\n\n"
        "## 四、样本缺口\n\n"
        f"- {gap_text}\n\n"
        "## 五、建议动作\n\n- 待补充\n"
    )
    _写入文本(project_dir / "最终调研报告.md", report)
    _写回项目(project_dir, project_payload, participants_payload)
    return {"已超时人数": timed_out_count, "项目状态": project_payload["项目状态"]}


def stop_project_and_cleanup(
    project_dir: Path,
    stopped_by: str,
    stop_reason: str,
    cron_jobs_path: Path | None = None,
    now_at: str | None = None,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    now = _解析时间(now_at) if now_at else _现在()
    if now is None:
        now = _现在()

    timed_out_count = 0
    for participant in participants_payload.get("受访对象列表", []):
        if participant.get("当前状态") not in 终态状态:
            participant["当前状态"] = "已超时"
            participant["完成摘要"] = participant.get("完成摘要") or "项目被手动停止，当前访谈按现有样本收口。"
            timed_out_count += 1

    summary = _统计样本(participants_payload.get("受访对象列表", []))
    gap_count = summary["已超时人数"] + summary["待回复人数"] + summary["待联系人数"] + summary["已停滞人数"]
    if gap_count > 0:
        gap_text = f"项目已手动停止，仍有 {gap_count} 位受访对象未完成，结论基于当前已回收样本输出。"
    else:
        gap_text = "项目已手动停止，当前样本已足够形成阶段结论。"

    removed_jobs = 0
    if cron_jobs_path is not None:
        cron_payload = _读取结构化文件(cron_jobs_path) or {"version": 1, "jobs": []}
        jobs = cron_payload.get("jobs", [])
        tracked_job_id = project_payload.get("巡检设置", {}).get("巡检任务ID", "")
        target_name = f"内部访谈调研巡检-{project_payload.get('项目名称', '')}"
        kept_jobs = []
        for job in jobs:
            if job.get("id") == tracked_job_id or job.get("name") == target_name:
                removed_jobs += 1
                continue
            kept_jobs.append(job)
        cron_payload["jobs"] = kept_jobs
        cron_jobs_path.write_text(json.dumps(cron_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    project_payload["当前阶段"] = "已关闭"
    project_payload["项目状态"] = "已停止"
    project_payload["分析收口"]["样本缺口说明"] = gap_text
    project_payload["分析收口"]["最终收口时间"] = now.isoformat()
    project_payload["停止信息"] = {
        "是否已停止": True,
        "停止时间": now.isoformat(),
        "停止原因": stop_reason,
        "停止人": stopped_by,
    }
    project_payload["巡检设置"]["巡检任务ID"] = ""
    project_payload["巡检设置"]["是否已注册"] = False
    project_payload["巡检设置"]["下次建议巡检时间"] = ""

    report = (
        f"# {project_payload['项目名称']} 最终调研报告\n\n"
        "## 一、调研目标\n\n"
        f"- {project_payload['调研目标']}\n\n"
        "## 二、停止收口\n\n"
        f"- 停止时间：{now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"- 停止人：{stopped_by}\n"
        f"- 停止原因：{stop_reason}\n\n"
        "## 三、样本覆盖\n\n"
        f"- 总人数：{summary['总人数']}\n"
        f"- 已完成：{summary['已完成人数']}\n"
        f"- 已超时：{summary['已超时人数']}\n"
        f"- 已拒绝：{summary['已拒绝人数']}\n\n"
        "## 四、核心发现\n\n- 待补充\n\n"
        "## 五、样本缺口\n\n"
        f"- {gap_text}\n\n"
        "## 六、建议动作\n\n- 待补充\n"
    )
    _写入文本(project_dir / "最终调研报告.md", report)
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "项目状态": project_payload["项目状态"],
        "已超时人数": timed_out_count,
        "清理巡检任务数": removed_jobs,
        "停止时间": now.isoformat(),
    }


def build_final_delivery_payload(project_dir: Path) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    summary = _统计样本(participants_payload.get("受访对象列表", []))
    gap_text = project_payload.get("分析收口", {}).get("样本缺口说明", "") or "暂无样本缺口说明。"
    report_path = project_dir / "最终调研报告.md"
    report_markdown = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    target = _标准飞书目标(project_payload.get("最终交付信息", {}).get("发起人飞书标识", ""))
    payload = {
        "交付渠道": project_payload.get("最终交付信息", {}).get("交付渠道", "飞书文档+摘要消息"),
        "飞书文档标题": project_payload.get("最终交付信息", {}).get("飞书文档标题", f"{project_payload.get('项目名称', '')} - 内部访谈调研报告"),
        "飞书文档建议内容路径": str(report_path),
        "飞书文档Markdown内容": report_markdown,
        "飞书文档创建参数": {
            "title": project_payload.get("最终交付信息", {}).get("飞书文档标题", f"{project_payload.get('项目名称', '')} - 内部访谈调研报告"),
            "markdown": report_markdown,
        },
        "飞书摘要消息发送参数": {
            "action": "send",
            "channel": "feishu",
            "accountId": "main",
            "target": target,
            "message": (
                f"【{project_payload.get('项目名称', '')}】内部访谈调研已收口。"
                f"样本覆盖 {summary['已完成人数']}/{summary['总人数']}，"
                f"已超时 {summary['已超时人数']}，已拒绝 {summary['已拒绝人数']}。"
                "飞书文档创建完成后，请把文档链接附在本消息后发送给发起人。"
            ),
        },
        "摘要消息": (
            f"【{project_payload.get('项目名称', '')}】内部访谈调研已收口。"
            f"样本覆盖 {summary['已完成人数']}/{summary['总人数']}，"
            f"已超时 {summary['已超时人数']}，已拒绝 {summary['已拒绝人数']}。"
            f"当前样本缺口：{gap_text}"
        ),
        "发起人飞书目标": target,
    }
    project_payload["最终交付信息"]["摘要消息状态"] = "已生成"
    project_payload["最终交付信息"]["最近交付时间"] = _现在字符串()
    _写回项目(project_dir, project_payload, participants_payload)
    return payload


def prepare_feishu_delivery(project_dir: Path) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    delivery_payload = build_final_delivery_payload(project_dir)
    report_path = project_dir / "最终调研报告.md"
    if not report_path.exists():
        raise FileNotFoundError(f"缺少最终调研报告：{report_path}")

    飞书交付目录.mkdir(parents=True, exist_ok=True)
    copied_report = _唯一文件路径(飞书交付目录 / f"{project_payload['项目名称']}-最终调研报告.md")
    shutil.copy2(report_path, copied_report)

    summary_text_path = project_dir / "输出" / "飞书摘要消息.txt"
    _写入文本(summary_text_path, str(delivery_payload["摘要消息"]).strip() + "\n")

    doc_markdown_path = project_dir / "输出" / "飞书文档正文.md"
    _写入文本(doc_markdown_path, str(delivery_payload["飞书文档Markdown内容"]))

    manifest = {
        "项目名称": project_payload["项目名称"],
        "project_dir": str(project_dir),
        "delivery_status": "待发送",
        "preferred_delivery": "feishu_doc_then_message",
        "fallback_delivery": "message_file_then_text",
        "target": {
            "channel": "feishu",
            "target": delivery_payload["发起人飞书目标"],
            "accountId": "main",
        },
        "deliverables": {
            "report_markdown_path": str(report_path),
            "report_copy_for_feishu": str(copied_report),
            "summary_text_path": str(summary_text_path),
            "doc_markdown_path": str(doc_markdown_path),
        },
        "agent_delivery_contract": {
            "completion_requires_tool_success": True,
            "preferred_sequence": [
                {
                    "tool": "feishu_create_doc",
                    "arguments": delivery_payload["飞书文档创建参数"],
                    "success_expectation": "返回 doc_id、url 或 task_id。若返回 task_id，继续轮询同工具直到文档创建成功。",
                },
                {
                    "tool": "message",
                    "arguments_template": {
                        "action": "send",
                        "channel": "feishu",
                        "accountId": "main",
                        "target": delivery_payload["发起人飞书目标"],
                        "message": delivery_payload["摘要消息"] + "\n文档创建成功后，把文档链接附在这条消息中一并发送。",
                    },
                    "success_expectation": "返回 ok=true 以及 messageId/chatId。",
                },
            ],
            "fallback_sequence": [
                {
                    "tool": "message",
                    "arguments": {
                        "action": "send",
                        "channel": "feishu",
                        "accountId": "main",
                        "target": delivery_payload["发起人飞书目标"],
                        "media": str(copied_report),
                        "mimeType": "text/markdown",
                        "message": delivery_payload["摘要消息"],
                    },
                    "success_expectation": "文档工具不可用或当前缺少用户上下文时，至少发出 Markdown 报告附件和摘要消息。",
                }
            ],
            "forbidden_claims_before_success": ["已发送", "已发飞书", "已交付"],
        },
    }

    manifest_path = project_dir / "输出" / "飞书交付清单.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    project_payload["最终交付信息"]["交付清单路径"] = str(manifest_path)
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "交付清单路径": str(manifest_path),
        "报告发送副本": str(copied_report),
        "摘要消息路径": str(summary_text_path),
        "优先交付方式": "先创建飞书文档，再发送摘要消息；失败时退回 Markdown 附件发送",
    }


def register_project_check_job(
    project_dir: Path,
    cron_jobs_path: Path,
    interval_minutes: int = 30,
    agent_id: str = "research",
) -> dict[str, Any]:
    if cron_jobs_path.exists():
        cron_payload = json.loads(cron_jobs_path.read_text(encoding="utf-8"))
    else:
        cron_payload = {"version": 1, "jobs": []}

    project_payload, participants_payload = _读取项目(project_dir)
    existing = None
    for job in cron_payload.get("jobs", []):
        if job.get("name") == f"内部访谈调研巡检-{project_payload['项目名称']}":
            existing = job
            break

    prompt = (
        "你是 research 调研巡检。"
        f"请先读取 {project_dir / '项目总表.yaml'} 与 {project_dir / '受访对象清单.yaml'}，"
        "按项目里的截止时间与跟进策略判断是否需要第一次跟进、第二次跟进、最终截止提醒或到期封口；"
        "如果需要，先更新项目文件，再继续后续动作。"
    )

    if existing is None:
        job = {
            "id": str(uuid4()),
            "name": f"内部访谈调研巡检-{project_payload['项目名称']}",
            "enabled": True,
            "createdAtMs": int(_现在().timestamp() * 1000),
            "schedule": {
                "kind": "cron",
                "expr": f"*/{interval_minutes} * * * *",
                "tz": "Asia/Shanghai",
                "staggerMs": 0,
            },
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": prompt,
                "lightContext": True,
            },
            "delivery": {"mode": "none"},
            "state": {},
        }
        cron_payload.setdefault("jobs", []).append(job)
    else:
        existing["payload"]["message"] = prompt
        existing["schedule"]["expr"] = f"*/{interval_minutes} * * * *"
        job = existing

    cron_jobs_path.write_text(json.dumps(cron_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    project_payload["巡检设置"]["巡检间隔分钟"] = interval_minutes
    project_payload["巡检设置"]["巡检任务ID"] = job["id"]
    project_payload["巡检设置"]["是否已注册"] = True
    project_payload["巡检设置"]["下次建议巡检时间"] = (_现在() + timedelta(minutes=interval_minutes)).isoformat()
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "巡检任务ID": job["id"],
        "任务名称": job["name"],
        "cron表达式": job["schedule"]["expr"],
    }
