from __future__ import annotations

from collections import Counter
import json
import re
import shutil
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml


终态状态 = {"已完成", "已超时", "已拒绝", "已关闭后回复", "验收通过并清理", "全回收处理完成"}
待回复状态 = {"已邀约", "待回复", "已停滞", "已停滞待回", "已超时待收口"}
待发送准备状态 = {"待联系", "待创建会话", "待绑定", "待首发", "待批次开放", "本轮冻结待后续批次"}
待发送核验状态 = {"待核验发送"}
项目阶段 = ["立项", "问题设计", "受访对象确认", "访谈进行中", "分析总结", "已关闭"]
飞书交付目录 = Path("/Users/a123/.openclaw/workspace/feishu-deliver")
默认网关日志路径 = Path("/Users/a123/.openclaw/logs/gateway.log")
默认shared会话目录 = Path("/Users/a123/.openclaw/agents/research-shared/sessions")
默认research会话目录 = Path("/Users/a123/.openclaw/agents/research/sessions")
默认cron任务路径 = Path("/Users/a123/.openclaw/cron/jobs.json")
关键收口信号 = ["是否使用过", "主要使用场景或主要阻力", "培训期待或改进方向"]
链路验收回复时限分钟 = 5
飞书open_id正则 = re.compile(r"^ou_[A-Za-z0-9_]+$")
飞书用户目标正则 = re.compile(r"^user:(ou_[A-Za-z0-9_]+)$")
飞书会话目标正则 = re.compile(r"^chat:(oc_[A-Za-z0-9_]+)$")
direct_shared会话key正则 = re.compile(r"^agent:research-shared:feishu:direct:(ou_[A-Za-z0-9_]+)$")
发送确认状态集合 = {
    "已调用发送",
    "已确认回执",
    "已确认落到目标会话",
    "已形成可回收 shared 会话",
    "已确认送达",
    "发送记录存在但待人工确认",
    "发送记录缺失",
    "核验口径冲突",
}
链路验收必需工具 = {
    "research": ["sessions_spawn", "feishu_conversation_binding"],
    "research-shared": ["sessions_spawn", "feishu_conversation_binding", "feishu_ask_user_question"],
}
默认配置文件路径 = Path("/Users/a123/.openclaw/openclaw.json")
会话工具默认profile = {
    "sessions_list": {"full", "messaging", "coding"},
    "sessions_history": {"full", "messaging", "coding"},
    "sessions_send": {"full", "messaging", "coding"},
    "session_status": {"full", "messaging", "coding"},
    "sessions_spawn": {"full", "coding"},
}
严格shared投递允许参数 = {"sessionKey", "message", "timeoutSeconds"}
严格shared投递参数冲突文案 = "工具层参数冲突：strict shared 投递请求同时携带 sessionKey 和 label，尚未真正投递。"
严格shared投递占位label文案 = "执行参数未按计划落地：strict shared 投递请求仍残留非法 label 占位值，尚未真正投递。"
严格shared会话不可达文案 = "shared 会话不可达：当前专属执行会话不存在、不可见或未就绪，尚未真正投递。"
严格shared协议不完整文案 = "shared 协议不完整：当前 inter-session payload 缺少必需字段，禁止首发，也禁止接管后续访谈。"
非法预建shared文案 = "检测到非法预建 shared：当前对象还没正式首发，但已经存在未投递 strict payload 的 live shared 会话。"
待回复发送确认门槛 = {"已确认回执", "已确认落到目标会话", "已形成可回收 shared 会话", "已确认送达"}
回复正文缺失错误 = "reply_text_missing"
回复仅元数据结果 = "reply_metadata_only"
默认自动推进间隔分钟 = 180
后台worker运行ID缺失错误 = "worker_run_id_missing"
后台worker运行ID不匹配错误 = "worker_run_id_mismatch"
后台worker超时错误 = "worker_heartbeat_timeout"
后台worker时间缺失错误 = "worker_timing_missing"


def _管理脚本路径() -> Path:
    return Path(__file__).resolve().parents[1] / "manage_internal_interview_project.py"


def _项目使用固定direct_shared真值(project_payload: dict[str, Any]) -> bool:
    return (
        str(project_payload.get("项目类型", "真实调研")).strip() == "真实调研"
        and str(project_payload.get("运行模式", "真实调研")).strip() != "链路验收"
    )


def _固定direct_shared执行会话key(participant: dict[str, Any]) -> str:
    open_id = _提取飞书open_id(participant.get("飞书标识", ""))
    if not open_id:
        return ""
    return f"agent:research-shared:feishu:direct:{open_id}"


def _看起来像direct_shared执行会话key(session_key: str) -> bool:
    return bool(direct_shared会话key正则.match(str(session_key or "").strip()))


def _看起来像helper执行会话key(session_key: str) -> bool:
    normalized = str(session_key or "").strip()
    if not normalized:
        return False
    if _看起来像direct_shared执行会话key(normalized):
        return False
    return normalized.startswith("agent:research-shared:subagent:") or normalized.startswith("research-shared-")


def _辅助执行会话已真实创建(participant: dict[str, Any]) -> bool:
    helper_id = str(participant.get("辅助执行会话ID", "")).strip() or str(participant.get("执行会话ID", "")).strip()
    helper_key = str(participant.get("辅助执行会话Key", "")).strip()
    if not helper_key and _看起来像helper执行会话key(participant.get("执行会话Key", "")):
        helper_key = str(participant.get("执行会话Key", "")).strip()
    return bool(helper_id and helper_key)


def _helper执行会话状态(participant: dict[str, Any], session_root: Path = 默认shared会话目录) -> str:
    helper_id = str(participant.get("辅助执行会话ID", "")).strip() or str(participant.get("执行会话ID", "")).strip()
    if not helper_id:
        return "未创建helper会话"
    session_file = session_root / f"{helper_id}.jsonl"
    return "helper会话存在" if session_file.exists() else "旧helper会话失活"


def _执行通道是否漂移(project_payload: dict[str, Any], participant: dict[str, Any]) -> bool:
    if not _项目使用固定direct_shared真值(project_payload):
        return False
    canonical_key = _执行会话key(project_payload, participant)
    if not canonical_key:
        return False
    current_key = str(participant.get("执行会话Key", "")).strip()
    binding_target = str(participant.get("最近一次绑定目标会话Key", "")).strip()
    return (bool(current_key) and current_key != canonical_key) or (
        bool(binding_target) and binding_target != canonical_key
    )


def _执行通道诊断(project_payload: dict[str, Any], participant: dict[str, Any], session_root: Path = 默认shared会话目录) -> dict[str, Any]:
    canonical_key = _执行会话key(project_payload, participant)
    helper_status = _helper执行会话状态(participant, session_root=session_root)
    drift = _执行通道是否漂移(project_payload, participant)
    if _绑定已核验(participant):
        verdict = "旧 helper 会话失活，但 direct shared 真值仍在" if helper_status == "旧helper会话失活" else "绑定仍有效"
    elif drift:
        verdict = "执行通道真值漂移"
    else:
        verdict = "绑定真实丢失"
    return {
        "执行通道真值类型": str(participant.get("执行通道真值类型", "")).strip() or "direct-shared",
        "canonical执行会话Key": canonical_key,
        "helper会话状态": helper_status,
        "执行通道是否漂移": drift,
        "绑定诊断": verdict,
        "绑定是否因重启后重新核验通过": _绑定已核验(participant) and str(participant.get("最近一次绑定目标会话Key", "")).strip() == canonical_key,
    }


def _默认自动推进设置() -> dict[str, Any]:
    return {
        "是否自动注册": False,
        "推进间隔分钟": 默认自动推进间隔分钟,
        "汇报模式": "every-round",
        "自动创建": False,
        "最近已汇报摘要键": "",
        "最近汇报时间": "",
        "后台执行中": False,
        "后台执行worker类型": "",
        "后台执行worker运行ID": "",
        "后台执行worker会话Key": "",
        "后台执行开始时间": "",
        "后台执行最近心跳时间": "",
        "后台执行最近摘要": "",
        "后台执行最近诊断": "",
    }


def _空推进摘要() -> dict[str, Any]:
    return {
        "执行状态": "待推进",
        "摘要": "",
        "摘要键": "",
        "更新时间": "",
        "本轮新创建会话人数": 0,
        "本轮新绑定人数": 0,
        "本轮真实发出人数": 0,
        "本轮完成跟进人数": 0,
        "本轮阻塞对象": [],
    }


def _生成后台worker运行ID() -> str:
    return f"worker-run-{uuid4().hex}"


def _后台worker前台摘要(诊断代码: str, 明细: str = "") -> str:
    if 诊断代码 == 后台worker运行ID缺失错误:
        return "上一轮后台推进状态丢失，已自动回收，等待重新启动"
    if 诊断代码 == 后台worker运行ID不匹配错误:
        return "检测到重复或串线的后台推进请求，已忽略本轮无效执行"
    if 诊断代码 == 后台worker超时错误:
        return "后台推进超时未续心跳，已回收待下一轮重启"
    if 诊断代码 == 后台worker时间缺失错误:
        return "上一轮后台推进状态不完整，已自动回收，等待重新启动"
    return 明细 or "后台推进状态异常，已自动回收，等待重新启动"


def _后台worker状态是否完整(settings: dict[str, Any]) -> bool:
    if not bool(settings.get("后台执行中")):
        return True
    worker_run_id = str(settings.get("后台执行worker运行ID", "")).strip()
    if not worker_run_id:
        return False
    last_heartbeat = str(settings.get("后台执行最近心跳时间", "")).strip()
    started_at = str(settings.get("后台执行开始时间", "")).strip()
    return bool(last_heartbeat or started_at)


def _推断后台worker诊断代码(summary: str) -> str:
    text = str(summary or "").strip()
    if not text:
        return ""
    if "缺少会话Key" in text or "缺少运行ID" in text:
        return 后台worker运行ID缺失错误
    if "缺少心跳和启动时间" in text:
        return 后台worker时间缺失错误
    if "没有心跳" in text:
        return 后台worker超时错误
    return ""


def _规范后台worker展示状态(project_payload: dict[str, Any]) -> bool:
    settings = _自动推进设置(project_payload)
    summary = str(settings.get("后台执行最近摘要", "")).strip()
    diagnostic = str(settings.get("后台执行最近诊断", "")).strip()
    resolved_code = diagnostic or _推断后台worker诊断代码(summary)
    if not resolved_code:
        return False
    friendly_summary = _后台worker前台摘要(resolved_code, summary)
    changed = False
    if summary != friendly_summary:
        settings["后台执行最近摘要"] = friendly_summary
        changed = True
    if diagnostic != resolved_code:
        settings["后台执行最近诊断"] = resolved_code
        changed = True
    return changed


def _默认访谈执行设置() -> dict[str, Any]:
    return {
        "发送账号标识": "research",
        "禁止使用用户身份发送": True,
        "账号异常处理": "暂停并通知发起人",
        "允许备用发送账号": False,
        "首轮消息工具": "message",
        "自动闭环要求": True,
    }


def _默认访谈策略() -> dict[str, Any]:
    return {
        "默认提问方式": "判断题优先",
        "默认交互形态": "文本选择题",
        "开放问答最晚触发条件": "判断题和选择题仍不足以拿到关键信息时，且一次只问1个问题",
        "首轮结构": "说明消息+1个短文本选择题",
        "单人有效问题上限": 4,
        "首轮问题上限": 1,
        "追问总上限": 2,
        "单轮最多追问": 1,
        "收口信号": list(关键收口信号),
        "卡片模式已禁用": True,
    }


def _slugify_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return token


def _项目slug(project_payload: dict[str, Any]) -> str:
    project_name = str(project_payload.get("项目名称", "")).strip()
    slug = _slugify_token(project_name)
    if slug:
        return slug
    project_id = str(project_payload.get("项目编号", "")).strip()
    if project_id:
        return _slugify_token(project_id[-6:]) or "project"
    return "project"


def _执行会话key(project_payload: dict[str, Any], participant: dict[str, Any]) -> str:
    if _项目使用固定direct_shared真值(project_payload):
        direct_key = _固定direct_shared执行会话key(participant)
        if direct_key:
            return direct_key
    project_slug = _项目slug(project_payload)
    name_slug = _slugify_token(str(participant.get("姓名", "")).strip())
    if name_slug:
        tail = name_slug
    else:
        feishu_id = _标准飞书目标(str(participant.get("飞书标识", "")).strip())
        open_id = feishu_id.split(":", 1)[-1] if ":" in feishu_id else feishu_id
        tail = open_id[-6:] if open_id else "unknown"
    return f"research-shared-{project_slug}-{tail}"


def _迁移受访对象到固定direct_shared真值(project_payload: dict[str, Any], participant: dict[str, Any]) -> None:
    truth_type = "direct-shared" if _项目使用固定direct_shared真值(project_payload) else "spawned-shared"
    participant["执行通道真值类型"] = truth_type
    participant.setdefault("辅助执行会话ID", "")
    participant.setdefault("辅助执行会话Key", "")
    if truth_type != "direct-shared":
        return

    canonical_key = _执行会话key(project_payload, participant)
    if (
        not canonical_key
        or (
            project_payload.get("项目状态") in {"已关闭", "已停止"}
            and not str(participant.get("执行会话Key", "")).strip()
            and str(participant.get("会话绑定状态", "")).strip() == "已解绑"
        )
    ):
        return
    previous_key = str(participant.get("执行会话Key", "")).strip()
    previous_binding_target = str(participant.get("最近一次绑定目标会话Key", "")).strip()
    previous_session_id = str(participant.get("执行会话ID", "")).strip()

    if previous_session_id and not str(participant.get("辅助执行会话ID", "")).strip():
        participant["辅助执行会话ID"] = previous_session_id
    if _看起来像helper执行会话key(previous_key) and not str(participant.get("辅助执行会话Key", "")).strip():
        participant["辅助执行会话Key"] = previous_key

    if canonical_key:
        participant["执行会话Key"] = canonical_key
        if previous_binding_target and _看起来像helper执行会话key(previous_binding_target):
            participant["最近一次绑定目标会话Key"] = canonical_key
            evidence = str(participant.get("最近一次绑定确认依据", "")).strip()
            if evidence and "direct shared 真值" not in evidence:
                participant["最近一次绑定确认依据"] = f"{evidence}；已迁移到固定 direct shared 真值"
            if str(participant.get("最近一次链路状态", "")).strip() in {"", "执行会话已切换，旧绑定已失效"}:
                participant["最近一次链路状态"] = "执行通道真值已迁移到固定 direct shared"


def _现在() -> datetime:
    return datetime.now().astimezone()


def _现在字符串() -> str:
    return _现在().isoformat()


def _时间字符串(value: str | None) -> str:
    if not value:
        return ""
    parsed = _解析时间(value)
    if parsed is None:
        return ""
    return parsed.isoformat()


def _解析上下文展示时间(value: str | None) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    match = re.match(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})(?::(\d{2}))? GMT([+-]\d{1,2})$", raw)
    if not match:
        return None
    seconds = match.group(3) or "00"
    offset_hours = int(match.group(4))
    offset_sign = "+" if offset_hours >= 0 else "-"
    offset_text = f"{offset_sign}{abs(offset_hours):02d}:00"
    return _解析时间(f"{match.group(1)}T{match.group(2)}:{seconds}{offset_text}")


def _解析时间(value: str | None) -> datetime | None:
    if not value:
        return None
    if re.fullmatch(r"\d{10,13}", value):
        timestamp_value = int(value)
        if len(value) == 13:
            timestamp_value = timestamp_value / 1000
        return datetime.fromtimestamp(timestamp_value).astimezone()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _提取文本片段(content: Any) -> str:
    if isinstance(content, list):
        pieces: list[str] = []
        for item in content:
            if isinstance(item, dict):
                piece = str(item.get("text") or item.get("content") or "").strip()
                if piece:
                    pieces.append(piece)
            elif isinstance(item, str):
                piece = item.strip()
                if piece:
                    pieces.append(piece)
        return "\n".join(pieces).strip()
    if isinstance(content, str):
        return content.strip()
    return ""


def _提取会话消息(entry: dict[str, Any]) -> tuple[str, str, str]:
    if entry.get("type") == "message":
        message = entry.get("message", {})
        if isinstance(message, dict):
            return (
                str(message.get("role", "")).strip(),
                _提取文本片段(message.get("content", [])),
                str(message.get("timestamp") or entry.get("timestamp") or "").strip(),
            )
    return (
        str(entry.get("role", "")).strip(),
        _提取文本片段(entry.get("content", [])),
        str(entry.get("timestamp") or "").strip(),
    )


def _单人有效问题上限(project_payload: dict[str, Any] | None = None, participant: dict[str, Any] | None = None) -> int:
    sources: list[Any] = []
    if participant is not None:
        sources.extend(
            [
                participant.get("单人有效问题上限"),
                participant.get("访谈策略", {}).get("单人有效问题上限") if isinstance(participant.get("访谈策略"), dict) else None,
            ]
        )
    if project_payload is not None:
        strategy = project_payload.get("访谈策略", {})
        dispatch = project_payload.get("派发策略", {})
        sources.extend(
            [
                strategy.get("单人有效问题上限") if isinstance(strategy, dict) else None,
                dispatch.get("单人有效问题上限") if isinstance(dispatch, dict) else None,
            ]
        )
    for value in sources:
        try:
            limit = int(value or 0)
        except (TypeError, ValueError):
            continue
        if limit > 0:
            return limit
    return 4


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


def _会话已真实创建(participant: dict[str, Any]) -> bool:
    truth_type = str(participant.get("执行通道真值类型", "")).strip()
    session_key = str(participant.get("执行会话Key", "")).strip()
    if truth_type == "direct-shared":
        return bool(session_key)
    return bool(str(participant.get("执行会话ID", "")).strip()) and bool(session_key)


def _当前绑定检查结果(participant: dict[str, Any]) -> str:
    return str(participant.get("最近一次绑定检查结果", "")).strip()


def _绑定核验字段完整(participant: dict[str, Any]) -> bool:
    current_session_key = str(participant.get("执行会话Key", "")).strip()
    verified_session_key = str(participant.get("最近一次绑定目标会话Key", "")).strip()
    check_result = _当前绑定检查结果(participant)
    return (
        bool(str(participant.get("会话绑定ID", "")).strip())
        and bool(str(participant.get("最近一次绑定确认时间", "")).strip())
        and bool(str(participant.get("最近一次绑定确认依据", "")).strip())
        and check_result in {"已核验通过", "绑定有效"}
        and bool(current_session_key)
        and current_session_key == verified_session_key
    )


def _绑定已核验(participant: dict[str, Any]) -> bool:
    return str(participant.get("会话绑定状态", "")).strip() == "已绑定" and _绑定核验字段完整(participant)


def _会话已就绪(participant: dict[str, Any]) -> bool:
    return _会话已真实创建(participant) and _绑定已核验(participant)


def _发送记录完整(participant: dict[str, Any]) -> bool:
    return (
        bool(str(participant.get("最近发出时间", "")).strip())
        and bool(str(participant.get("最近一次发送消息ID", "")).strip())
        and bool(str(participant.get("最近一次发送chatID", "")).strip())
    )


def _发送后可进入待回复(participant: dict[str, Any]) -> bool:
    return _会话已就绪(participant) and _发送记录完整(participant)


def _仍处于首发前阶段(participant: dict[str, Any]) -> bool:
    return str(participant.get("当前状态", "")).strip() in 待发送准备状态


def _当前发送确认状态(participant: dict[str, Any]) -> str:
    raw = str(participant.get("最近一次发送确认状态", "")).strip()
    return raw if raw in 发送确认状态集合 else ""


def _发送已确认(participant: dict[str, Any]) -> bool:
    return _当前发送确认状态(participant) in {"已确认落到目标会话", "已形成可回收 shared 会话", "已确认送达"}


def _发送确认达到待回复门槛(participant: dict[str, Any]) -> bool:
    return _当前发送确认状态(participant) in 待回复发送确认门槛


def _推导默认发送确认状态(participant: dict[str, Any]) -> str:
    current = _当前发送确认状态(participant)
    if current:
        return current
    if not _发送记录完整(participant):
        return ""
    return "已调用发送"


def _清空绑定核验字段(participant: dict[str, Any], reason: str = "") -> None:
    participant["会话绑定ID"] = ""
    participant["会话绑定状态"] = "未绑定"
    participant["最近一次绑定确认时间"] = ""
    participant["最近一次绑定确认依据"] = ""
    participant["最近一次绑定目标会话Key"] = ""
    participant["最近一次绑定检查结果"] = reason or ""


def _清空发送证据字段(participant: dict[str, Any]) -> None:
    participant["最近发出时间"] = ""
    participant["最近一次发送消息ID"] = ""
    participant["最近一次发送chatID"] = ""
    participant["最近一次发送确认状态"] = ""
    participant["最近一次发送确认时间"] = ""
    participant["最近一次发送确认依据"] = ""
    participant["最近一次卡片ID"] = ""
    participant["最近一次卡片结果"] = ""


def _回退误触发待命shared(participant: dict[str, Any], reason: str | None = None, fallback_status: str = "待创建会话") -> None:
    participant["执行会话ID"] = ""
    participant["辅助执行会话ID"] = ""
    participant["辅助执行会话Key"] = ""
    if str(participant.get("执行通道真值类型", "")).strip() != "direct-shared":
        participant["执行会话Key"] = ""
    _清空绑定核验字段(participant, reason="误触发待命 shared，会话已作废")
    _清空发送证据字段(participant)
    participant["最近回复时间"] = ""
    participant["最近一次回收时间"] = ""
    participant["是否已回收至research"] = False
    participant["当前状态"] = "待绑定" if _会话已真实创建(participant) else fallback_status
    participant["最近一次业务状态"] = "检测到非法预建 shared，已回退待正式批次重建"
    participant["最近一次链路状态"] = reason or "误触发待命 shared，会话已作废"
    participant["访谈轮次记录"] = [
        item
        for item in participant.get("访谈轮次记录", [])
        if isinstance(item, dict) and str(item.get("动作", "")).strip() not in {"发出消息", "收到回复", "收到首发前消息"}
    ]


def _规范绑定状态(target: dict[str, Any], requested_status: str) -> str:
    status = str(requested_status).strip()
    if status != "已绑定":
        return status
    if _绑定核验字段完整(target):
        return "已绑定"
    check_result = _当前绑定检查结果(target)
    if check_result and check_result not in {"待核验", "已核验通过", "绑定有效"}:
        return "绑定异常"
    return "待核验"


def _校验发送状态(participant: dict[str, Any]) -> None:
    current_status = str(participant.get("当前状态", "")).strip()
    send_time = str(participant.get("最近发出时间", "")).strip()
    message_id = str(participant.get("最近一次发送消息ID", "")).strip()
    chat_id = str(participant.get("最近一次发送chatID", "")).strip()
    if message_id and not chat_id:
        raise ValueError("没有 chatId 时不能只写最近一次发送消息ID。")
    if chat_id and not message_id:
        raise ValueError("没有 messageId 时不能只写最近一次发送chatID。")
    if participant.get("最近一次发送确认状态") and not _当前发送确认状态(participant):
        raise ValueError("最近一次发送确认状态不在允许集合内。")
    if send_time:
        if not _会话已真实创建(participant):
            raise ValueError("没有真实执行会话ID/执行会话Key 时，不能记录最近发出时间。")
        if not _绑定已核验(participant):
            raise ValueError("未完成绑定核验时，不能记录最近发出时间。")
        if not message_id or not chat_id:
            raise ValueError("没有 messageId + chatId 时，不能记录最近发出时间。")
    if current_status == "待首发" and not _会话已就绪(participant):
        raise ValueError("只有真实创建并完成绑定核验的专属 shared 会话，才能进入待首发。")
    if current_status == "待核验发送" and not _发送后可进入待回复(participant):
        raise ValueError("只有真实会话、绑定已核验且已拿到 messageId + chatId 时，才能进入待核验发送。")
    if current_status == "待回复" and not _发送后可进入待回复(participant):
        raise ValueError("只有真实会话、绑定已核验且已拿到 messageId + chatId 时，才能进入待回复。")
    if current_status == "待回复" and not _发送确认达到待回复门槛(participant):
        raise ValueError("发送确认状态低于已确认回执时，不能进入待回复。")


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
    if 飞书用户目标正则.match(raw) or 飞书会话目标正则.match(raw):
        return raw
    if 飞书open_id正则.match(raw):
        return f"user:{raw}"
    if raw.startswith("oc_"):
        return f"chat:{raw}"
    return raw


def _提取飞书open_id(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    matched_user = 飞书用户目标正则.match(raw)
    if matched_user:
        return matched_user.group(1)
    if 飞书open_id正则.match(raw):
        return raw
    return ""


def _标准受访对象飞书标识(value: str) -> str:
    open_id = _提取飞书open_id(value)
    if not open_id:
        raise ValueError(f"非法飞书标识：{value}")
    return f"user:{open_id}"


def _尝试修复受访对象飞书标识(feishu_id: str, inclusion_reason: str) -> str:
    open_id = _提取飞书open_id(feishu_id)
    if not open_id:
        match = re.search(r"(ou_[A-Za-z0-9]+)", str(inclusion_reason or ""))
        if match:
            open_id = match.group(1)
    return f"user:{open_id}" if open_id else ""


def _agent_配置项(config_path: Path, agent_id: str) -> dict[str, Any]:
    payload = _读取结构化文件(config_path)
    agents_section = payload.get("agents", {})
    if not isinstance(agents_section, dict):
        return {}
    agent_list = agents_section.get("list", [])
    if not isinstance(agent_list, list):
        return {}
    for agent in agent_list:
        if isinstance(agent, dict) and agent.get("id") == agent_id:
            return agent
    return {}


def _读取_agent_工具配置(config_path: Path, agent_id: str) -> dict[str, Any]:
    agent = _agent_配置项(config_path, agent_id)
    tools = agent.get("tools", {})
    return tools if isinstance(tools, dict) else {}


def _读取全局工具配置(config_path: Path) -> dict[str, Any]:
    payload = _读取结构化文件(config_path)
    tools = payload.get("tools", {})
    return tools if isinstance(tools, dict) else {}


def _agent_工具已放行(config_path: Path, agent_id: str, tool_name: str) -> bool:
    tools = _读取_agent_工具配置(config_path, agent_id)
    deny = {str(item).strip() for item in tools.get("deny", []) if str(item).strip()}
    if tool_name in deny:
        return False
    allow = {str(item).strip() for item in tools.get("allow", []) if str(item).strip()}
    also_allow = {str(item).strip() for item in tools.get("alsoAllow", []) if str(item).strip()}
    if tool_name in allow or tool_name in also_allow:
        return True
    if allow:
        return False
    profile = str(tools.get("profile", "")).strip()
    if profile == "full":
        return True
    return profile in 会话工具默认profile.get(tool_name, set())


def _读取全局会话可见性(config_path: Path) -> str:
    tools = _读取全局工具配置(config_path)
    sessions = tools.get("sessions", {})
    if not isinstance(sessions, dict):
        return "tree"
    visibility = str(sessions.get("visibility", "")).strip()
    return visibility or "tree"


def _读取全局agent_to_agent配置(config_path: Path) -> dict[str, Any]:
    tools = _读取全局工具配置(config_path)
    agent_to_agent = tools.get("agentToAgent", {})
    return agent_to_agent if isinstance(agent_to_agent, dict) else {}


def _agent_to_agent_allow命中(allow_patterns: list[str], agent_id: str) -> bool:
    if not allow_patterns:
        return True
    for pattern in allow_patterns:
        raw = str(pattern or "").strip()
        if not raw:
            continue
        if raw == "*":
            return True
        if "*" not in raw:
            if raw == agent_id:
                return True
            continue
        escaped = re.escape(raw).replace(r"\*", ".*")
        if re.fullmatch(escaped, agent_id, re.IGNORECASE):
            return True
    return False


def _读取_agent_放行工具(config_path: Path, agent_id: str) -> list[str]:
    tools = _读取_agent_工具配置(config_path, agent_id)
    allowed = set()
    for key in ("allow", "alsoAllow"):
        values = tools.get(key, [])
        if isinstance(values, list):
            allowed.update(str(item).strip() for item in values if str(item).strip())
    return sorted(allowed)


def _检查链路验收工具放行(config_path: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for agent_id, required_tools in 链路验收必需工具.items():
        allowed_tools = _读取_agent_放行工具(config_path, agent_id)
        missing = [tool for tool in required_tools if tool not in allowed_tools]
        reports.append(
            {
                "代理": agent_id,
                "必需工具": required_tools,
                "已放行工具": allowed_tools,
                "缺少工具": missing,
                "是否通过": len(missing) == 0,
            }
        )
    return reports


def _提取编译后工具名(compiled_tools: Any) -> list[str]:
    if not isinstance(compiled_tools, list):
        return []
    names: set[str] = set()
    for item in compiled_tools:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if name:
            names.add(name)
    return sorted(names)


def _读取运行时主会话检查(
    requester_session_key: str | None,
    requester_session_root: Path = 默认research会话目录,
) -> dict[str, Any]:
    session_key = str(requester_session_key or "").strip()
    result: dict[str, Any] = {
        "状态": "未提供",
        "requesterSessionKey": session_key,
        "sessionRoot": str(requester_session_root),
        "visibility": "",
        "sessionsSendVisible": None,
        "agentToAgentEnabled": None,
        "compiledToolsCount": 0,
        "compiledToolNames": [],
        "runtimeEvidenceSource": "",
        "systemPromptTruncated": False,
        "来源文件": "",
        "快照时间": "",
    }
    if not session_key:
        return result
    if not requester_session_root.exists():
        result["状态"] = "会话目录不存在"
        return result

    latest_snapshot: dict[str, Any] | None = None
    latest_at: datetime | None = None
    for session_file in requester_session_root.rglob("*.trajectory.jsonl"):
        metadata: dict[str, Any] | None = None
        compiled_payload: dict[str, Any] | None = None
        try:
            for raw_line in session_file.read_text(encoding="utf-8").splitlines():
                try:
                    entry = json.loads(raw_line)
                except Exception:
                    continue
                if str(entry.get("sessionKey", "")).strip() != session_key:
                    continue
                if entry.get("type") == "trace.metadata":
                    metadata = entry
                elif entry.get("type") == "context.compiled":
                    data = entry.get("data", {})
                    compiled_payload = data if isinstance(data, dict) else {}
        except Exception:
            continue
        if metadata is None:
            continue
        candidate_at = _解析时间(str(metadata.get("ts", "")).strip())
        if candidate_at is None:
            candidate_at = _解析时间(str(metadata.get("data", {}).get("capturedAt", "")).strip())
        if latest_at is None or (candidate_at is not None and candidate_at > latest_at):
            latest_at = candidate_at
            latest_snapshot = {
                "metadata": metadata,
                "compiled": compiled_payload or {},
                "path": str(session_file),
            }

    if latest_snapshot is None:
        result["状态"] = "未找到"
        return result

    metadata = latest_snapshot["metadata"]
    tools = (
        metadata.get("data", {})
        .get("config", {})
        .get("redacted", {})
        .get("tools", {})
    )
    if not isinstance(tools, dict):
        tools = {}
    sessions = tools.get("sessions", {})
    if not isinstance(sessions, dict):
        sessions = {}
    agent_to_agent = tools.get("agentToAgent", {})
    if not isinstance(agent_to_agent, dict):
        agent_to_agent = {}

    result["状态"] = "已找到"
    result["visibility"] = str(sessions.get("visibility", "")).strip() or "tree"
    result["agentToAgentEnabled"] = bool(agent_to_agent.get("enabled", False))
    compiled_payload = latest_snapshot.get("compiled", {})
    if not isinstance(compiled_payload, dict):
        compiled_payload = {}
    compiled_tool_names = _提取编译后工具名(compiled_payload.get("tools"))
    system_prompt = compiled_payload.get("systemPrompt")
    result["compiledToolsCount"] = len(compiled_tool_names)
    result["compiledToolNames"] = compiled_tool_names
    result["runtimeEvidenceSource"] = "context.compiled.tools" if compiled_tool_names else ""
    result["systemPromptTruncated"] = isinstance(system_prompt, dict) and bool(system_prompt.get("truncated"))
    if compiled_tool_names:
        result["sessionsSendVisible"] = "sessions_send" in compiled_tool_names
    result["来源文件"] = str(latest_snapshot.get("path", "") or "")
    result["快照时间"] = (
        latest_at.isoformat()
        if latest_at is not None
        else str(metadata.get("ts", "")).strip()
    )
    return result


def _共享投递诊断建议动作(诊断状态: str) -> str:
    if 诊断状态 == "主会话权限快照过期":
        return "配置已改但当前 runtime 仍是旧值，需要重启 gateway 后再在当前主对话触发一次新 turn"
    if 诊断状态 == "静态配置缺失":
        return "先修正 shared 投递配置并重启 gateway"
    if 诊断状态 == "运行时工具检测异常":
        return "gateway 已生效，但当前 skill 的 runtime 工具检测证据不足，需要先修复检测链路"
    if 诊断状态 == "shared 投递未放行":
        return "当前主会话 runtime 工具清单里缺少 shared 投递必需工具，需要检查 research 主会话工具暴露"
    return "先补齐 shared 投递前置条件"


def _检查严格shared投递配置(
    config_path: Path,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
) -> dict[str, Any]:
    if not config_path.exists():
        return {
            "是否通过": False,
            "静态配置是否通过": False,
            "诊断状态": "静态配置缺失",
            "建议动作": _共享投递诊断建议动作("静态配置缺失"),
            "阻止原因": [f"找不到配置文件：{config_path}"],
            "research": {},
            "research-shared": {},
            "运行时主会话检查": _读取运行时主会话检查(
                requester_session_key=requester_session_key,
                requester_session_root=requester_session_root,
            ),
        }

    research_required = ["sessions_spawn", "sessions_send", "sessions_list", "session_status"]
    shared_required = ["message"]
    global_visibility = _读取全局会话可见性(config_path)
    agent_to_agent = _读取全局agent_to_agent配置(config_path)
    global_agent_to_agent_enabled = agent_to_agent.get("enabled") is True
    agent_to_agent_allow = [
        str(item).strip()
        for item in agent_to_agent.get("allow", [])
        if str(item).strip()
    ] if isinstance(agent_to_agent.get("allow", []), list) else []
    research_missing = [tool for tool in research_required if not _agent_工具已放行(config_path, "research", tool)]
    shared_missing = [tool for tool in shared_required if not _agent_工具已放行(config_path, "research-shared", tool)]

    reasons: list[str] = []
    if global_visibility != "all":
        reasons.append(
            "tools.sessions.visibility 不是 all，当前会触发 Session send visibility is restricted"
        )
    if not global_agent_to_agent_enabled:
        reasons.append("tools.agentToAgent.enabled 不是 true，当前跨 agent shared 投递不会放行")
    elif not (
        _agent_to_agent_allow命中(agent_to_agent_allow, "research")
        and _agent_to_agent_allow命中(agent_to_agent_allow, "research-shared")
    ):
        reasons.append("research -> research-shared 不在 tools.agentToAgent.allow 内")
    if research_missing:
        reasons.append("research 缺少会话工具：" + "、".join(research_missing))
    if shared_missing:
        reasons.append("research-shared 缺少发送工具：" + "、".join(shared_missing))

    static_ok = len(reasons) == 0
    runtime_check = _读取运行时主会话检查(
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
    )
    diagnosis_status = "通过"
    if not static_ok:
        diagnosis_status = "静态配置缺失"
    elif runtime_check.get("状态") == "已找到":
        runtime_visibility = str(runtime_check.get("visibility", "")).strip() or "tree"
        sessions_send_visible = runtime_check.get("sessionsSendVisible")
        runtime_agent_to_agent_enabled = runtime_check.get("agentToAgentEnabled")
        compiled_tool_names = [
            str(item).strip()
            for item in runtime_check.get("compiledToolNames", [])
            if str(item).strip()
        ]
        required_runtime_tools = ["sessions_send", "sessions_spawn", "sessions_list", "session_status"]
        missing_runtime_tools = [tool for tool in required_runtime_tools if tool not in compiled_tool_names]
        if runtime_visibility != "all":
            diagnosis_status = "主会话权限快照过期"
            reasons.append(
                f"静态配置已通过，但当前 research 主会话运行时权限仍是 {runtime_visibility}，旧权限快照未刷新。需要重启 gateway 后再在当前主对话触发一次新 turn。"
            )
        elif runtime_agent_to_agent_enabled is False:
            diagnosis_status = "主会话权限快照过期"
            reasons.append(
                "静态配置已通过，但当前 research 主会话运行时 agent-to-agent messaging 仍未启用，旧权限快照未刷新。需要重启 gateway 后再在当前主对话触发一次新 turn。"
            )
        elif sessions_send_visible is None:
            diagnosis_status = "运行时工具检测异常"
            reasons.append(
                "静态配置已通过，但当前 research 主会话缺少可判定的 context.compiled.tools 证据，暂时无法可靠判断 shared 投递工具是否真正可见。"
            )
        elif missing_runtime_tools:
            diagnosis_status = "shared 投递未放行"
            reasons.append(
                "静态配置已通过，但当前 research 主会话 runtime 工具清单仍缺少："
                + "、".join(missing_runtime_tools)
            )
        elif sessions_send_visible is False:
            diagnosis_status = "shared 投递未放行"
            reasons.append(
                "静态配置已通过，但当前 research 主会话 runtime 工具清单里确实没有 sessions_send。"
            )
    elif session_key := str(requester_session_key or "").strip():
        if runtime_check.get("状态") == "未找到":
            diagnosis_status = "运行时工具检测异常"
            reasons.append(
                f"静态配置已通过，但未找到当前 research 主会话 {session_key} 的运行时快照，暂时无法可靠判断 shared 投递工具是否真正可见。"
            )

    return {
        "是否通过": len(reasons) == 0,
        "静态配置是否通过": static_ok,
        "诊断状态": diagnosis_status,
        "建议动作": _共享投递诊断建议动作(diagnosis_status),
        "阻止原因": reasons,
        "诊断摘要": {
            "静态层": "通过" if static_ok else "失败",
            "运行时层": (
                "未检查"
                if runtime_check.get("状态") == "未提供"
                else "通过" if diagnosis_status == "通过" else diagnosis_status
            ),
            "结论分类": diagnosis_status,
        },
        "全局": {
            "sessionsVisibility": global_visibility,
            "agentToAgentEnabled": global_agent_to_agent_enabled,
            "agentToAgentAllow": agent_to_agent_allow,
        },
        "research": {
            "缺少工具": research_missing,
        },
        "research-shared": {
            "缺少工具": shared_missing,
        },
        "运行时主会话检查": runtime_check,
    }


def _生成唯一执行会话keys(
    project_payload: dict[str, Any],
    participants: list[dict[str, Any]],
    force_reset_existing: bool = False,
) -> None:
    if _项目使用固定direct_shared真值(project_payload):
        for participant in participants:
            participant["执行通道真值类型"] = "direct-shared"
            candidate = _执行会话key(project_payload, participant)
            if candidate:
                participant["执行会话Key"] = candidate
        return

    used: set[str] = set()
    for participant in participants:
        existing = str(participant.get("执行会话Key", "")).strip()
        candidate = existing
        if (
            force_reset_existing
            or not existing
            or existing == "research-shared-openclaw-user"
            or existing in used
        ):
            candidate = _执行会话key(project_payload, participant)
        suffix = 2
        while candidate in used:
            candidate = f"{_执行会话key(project_payload, participant)}-{suffix}"
            suffix += 1
        participant["执行会话Key"] = candidate
        used.add(candidate)


def _疑似临时空配置(config_path: Path, tool_reports: list[dict[str, Any]]) -> bool:
    if config_path == 默认配置文件路径:
        return False
    if "temp" not in config_path.name.lower():
        return False
    if not tool_reports:
        return False
    return all(not report.get("已放行工具") for report in tool_reports)


def _标准受访对象(record: dict[str, Any]) -> dict[str, Any]:
    collected_signals = record.get("已收集信号", [])
    if not isinstance(collected_signals, list):
        collected_signals = []
    return {
        "姓名": record.get("姓名", "").strip(),
        "飞书标识": record.get("飞书标识", "").strip(),
        "纳入原因": record.get("纳入原因", "").strip(),
        "当前状态": record.get("当前状态", "待创建会话"),
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
        "执行通道真值类型": record.get("执行通道真值类型", "direct-shared"),
        "执行会话代理": record.get("执行会话代理", "research-shared"),
        "执行会话ID": record.get("执行会话ID", ""),
        "执行会话Key": record.get("执行会话Key", ""),
        "辅助执行会话ID": record.get("辅助执行会话ID", ""),
        "辅助执行会话Key": record.get("辅助执行会话Key", ""),
        "会话绑定ID": record.get("会话绑定ID", ""),
        "会话绑定状态": record.get("会话绑定状态", "未绑定"),
        "最近一次绑定确认时间": record.get("最近一次绑定确认时间", ""),
        "最近一次绑定确认依据": record.get("最近一次绑定确认依据", ""),
        "最近一次绑定目标会话Key": record.get("最近一次绑定目标会话Key", ""),
        "最近一次绑定检查结果": record.get("最近一次绑定检查结果", ""),
        "最近一次发送消息ID": record.get("最近一次发送消息ID", ""),
        "最近一次发送chatID": record.get("最近一次发送chatID", ""),
        "最近一次发送确认状态": record.get("最近一次发送确认状态", ""),
        "最近一次发送确认时间": record.get("最近一次发送确认时间", ""),
        "最近一次发送确认依据": record.get("最近一次发送确认依据", ""),
        "最近一次卡片ID": record.get("最近一次卡片ID", ""),
        "最近一次卡片结果": record.get("最近一次卡片结果", ""),
        "最近一次回收时间": record.get("最近一次回收时间", ""),
        "是否已回收至research": bool(record.get("是否已回收至research", False)),
        "最近一次提问方式": record.get("最近一次提问方式", ""),
        "最近一次卡片类型": record.get("最近一次卡片类型", ""),
        "累计按钮题次数": int(record.get("累计按钮题次数", 0) or 0),
        "累计选择题次数": int(record.get("累计选择题次数", 0) or 0),
        "累计开放题次数": int(record.get("累计开放题次数", 0) or 0),
        "累计有效问题数": int(record.get("累计有效问题数", 0) or 0),
        "最近一次业务状态": record.get("最近一次业务状态", ""),
        "最近一次链路状态": record.get("最近一次链路状态", ""),
        "超时原因": record.get("超时原因", ""),
        "收口方式": record.get("收口方式", ""),
        "是否计入有效样本": bool(record.get("是否计入有效样本", False)),
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
        if status in {"待联系", "待创建会话", "待绑定", "待首发", "待批次开放", "本轮冻结待后续批次"}:
            counts["待联系人数"] += 1
        elif status in {"已邀约", "待回复", "待核验发送"}:
            counts["待回复人数"] += 1
        elif status in {"访谈中", "超时后补回", "已完成待回写"}:
            counts["访谈中人数"] += 1
        elif status in {"已完成", "验收通过并清理", "全回收处理完成"}:
            counts["已完成人数"] += 1
        elif status in {"已停滞", "已停滞待回"}:
            counts["已停滞人数"] += 1
        elif status in {"已超时", "已超时待收口"}:
            counts["已超时人数"] += 1
        elif status == "已拒绝":
            counts["已拒绝人数"] += 1
    return counts


def _统计当前活跃受访对象数(participants: list[dict[str, Any]]) -> int:
    active_statuses = {"已邀约", "待回复", "待核验发送", "访谈中", "已停滞", "已停滞待回", "已超时待收口", "超时后补回", "已完成待回写"}
    return sum(1 for participant in participants if participant.get("当前状态", "") in active_statuses)


def _是否项目已冻结(project_payload: dict[str, Any]) -> bool:
    return bool(project_payload.get("最终交付信息", {}).get("是否已发送最终报告", False))


def _是否计入有效样本(participant: dict[str, Any]) -> bool:
    if bool(participant.get("是否计入有效样本", False)):
        return True
    return participant.get("当前状态", "") in {"已完成", "超时后补回", "验收通过并清理", "全回收处理完成"}


def _去重信号(signals: list[str]) -> list[str]:
    return list(dict.fromkeys(signal for signal in signals if signal))


def _已命中收口信号(participant: dict[str, Any]) -> list[str]:
    signals = participant.get("已收集信号", [])
    if not isinstance(signals, list):
        return []
    normalized = {str(signal).strip() for signal in signals if str(signal).strip()}
    return [signal for signal in 关键收口信号 if signal in normalized]


def _是否达到收口条件(participant: dict[str, Any], question_limit: int | None = None) -> bool:
    if participant.get("是否已达到收口条件", False):
        return True
    if len(_已命中收口信号(participant)) >= len(关键收口信号):
        return True
    limit = question_limit or _单人有效问题上限(participant=participant)
    return int(participant.get("累计有效问题数", 0) or 0) >= limit


def _更新收口状态(participant: dict[str, Any], question_limit: int | None = None) -> None:
    hit_signals = _已命中收口信号(participant)
    limit = question_limit or _单人有效问题上限(participant=participant)
    hit_signal_enough = len(hit_signals) >= len(关键收口信号)
    hit_question_limit = int(participant.get("累计有效问题数", 0) or 0) >= limit
    enough = hit_signal_enough or hit_question_limit
    participant["是否已达到收口条件"] = enough
    if hit_signal_enough:
        participant["收口原因"] = "已覆盖是否使用过、主要使用场景或主要阻力、培训期待或改进方向，不要继续追问。"
    elif hit_question_limit:
        participant["收口原因"] = f"已达到单人有效问题上限 {limit}，不要继续追问。"
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
    project_type: str = "真实调研",
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
        "项目类型": project_type,
        "运行模式": "真实调研",
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
        "执行架构": {
            "发起代理": "research",
            "访谈代理": "research-shared",
            "会话粒度": "每人一会话",
            "结果回收目标": "research",
        },
        "访谈执行设置": _默认访谈执行设置(),
        "访谈策略": _默认访谈策略(),
        "派发策略": {
            "派发模式": "一次性全发",
            "首轮交互形态": "文本选择题",
            "每批人数": 10,
            "批间隔分钟": 10,
            "单人同时待答问题数上限": 1,
            "单人有效问题上限": 4,
        },
        "派发批次记录": [],
        "批次状态": "未生成",
        "当前活跃受访对象数": _统计当前活跃受访对象数(participants),
        "跟进策略": {
            "首次跟进间隔小时": 6,
            "第二次跟进间隔小时": 12,
            "最终截止提醒提前小时": 6,
            "最大跟进次数": 2,
        },
        "截止时间变更记录": [],
        "巡检设置": {
            "巡检间隔分钟": 默认自动推进间隔分钟,
            "巡检任务ID": "",
            "推进任务ID": "",
            "汇报任务ID": "",
            "是否已注册": False,
            "上次巡检时间": "",
            "下次建议巡检时间": "",
        },
        "自动推进设置": _默认自动推进设置(),
        "当前批次序号": 0,
        "当前批次状态": "待推进",
        "当前批次对象列表": [],
        "上次推进结果摘要": _空推进摘要(),
        "下次自动推进时间": "",
        "最终交付信息": {
            "交付渠道": "飞书文档+摘要消息",
            "发起人飞书标识": initiator_feishu_id,
            "飞书文档标题": f"{project_name} - 内部访谈调研报告",
            "摘要消息状态": "待生成",
            "最近交付时间": "",
            "是否已发送最终报告": False,
            "最终报告发送时间": "",
            "冻结观察期小时": 48,
            "冻结观察截止时间": "",
            "冻结版本号": 0,
            "交付账号标识": "research",
        },
        "样本概况": _统计样本(participants),
        "分析收口": {
            "是否允许带缺口收口": True,
            "收口触发条件": "全部完成或到达截止时间",
            "样本缺口说明": "",
            "最终收口时间": "",
            "最新分析时间": "",
        },
        "停止信息": {
            "是否已停止": False,
            "停止时间": "",
            "停止原因": "",
            "停止人": "",
        },
}


def _受访对象清单(project_payload: dict[str, Any], participants: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [_标准受访对象(participant) for participant in participants]
    _生成唯一执行会话keys(project_payload, normalized)
    question_limit = _单人有效问题上限(project_payload=project_payload)
    for participant in normalized:
        if participant.get("当前状态") == "待联系":
            participant["当前状态"] = "待创建会话"
        _更新收口状态(participant, question_limit=question_limit)
    return {
        "项目名称": project_payload.get("项目名称", ""),
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
    _补全项目默认字段(project_dir, project_payload, participants_payload)
    return project_payload, participants_payload


def _写回项目(project_dir: Path, project_payload: dict[str, Any], participants_payload: dict[str, Any]) -> None:
    _补全项目默认字段(project_dir, project_payload, participants_payload)
    participants_payload["更新时间"] = _现在字符串()
    project_payload["样本概况"] = _统计样本(participants_payload["受访对象列表"])
    project_payload["当前活跃受访对象数"] = _统计当前活跃受访对象数(participants_payload["受访对象列表"])
    _写入_yaml(project_dir / "项目总表.yaml", project_payload)
    _写入_yaml(project_dir / "受访对象清单.yaml", participants_payload)


def _补全项目默认字段(project_dir: Path, project_payload: dict[str, Any], participants_payload: dict[str, Any]) -> None:
    project_payload.setdefault("项目目录", str(project_dir))
    project_payload.setdefault("项目类型", "真实调研")
    project_payload.setdefault("运行模式", "真实调研")
    project_payload.setdefault("执行架构", {})
    project_payload["执行架构"].setdefault("发起代理", "research")
    project_payload["执行架构"].setdefault("访谈代理", "research-shared")
    project_payload["执行架构"].setdefault("会话粒度", "每人一会话")
    project_payload["执行架构"].setdefault("结果回收目标", "research")
    project_payload.setdefault("访谈执行设置", {})
    for key, value in _默认访谈执行设置().items():
        project_payload["访谈执行设置"].setdefault(key, value)
    project_payload.setdefault("访谈策略", {})
    for key, value in _默认访谈策略().items():
        project_payload["访谈策略"].setdefault(key, value)
    project_payload.setdefault("派发策略", {})
    project_payload["派发策略"].setdefault("派发模式", "一次性全发")
    project_payload["派发策略"].setdefault("首轮交互形态", "文本选择题")
    project_payload["派发策略"].setdefault("每批人数", 10)
    project_payload["派发策略"].setdefault("批间隔分钟", 10)
    project_payload["派发策略"].setdefault("单人同时待答问题数上限", 1)
    project_payload["派发策略"].setdefault("单人有效问题上限", 4)
    project_payload.setdefault("派发批次记录", [])
    project_payload.setdefault("批次状态", "未生成")
    project_payload.setdefault("巡检设置", {})
    project_payload["巡检设置"].setdefault("巡检间隔分钟", 默认自动推进间隔分钟)
    project_payload["巡检设置"].setdefault("巡检任务ID", "")
    project_payload["巡检设置"].setdefault("推进任务ID", "")
    project_payload["巡检设置"].setdefault("汇报任务ID", "")
    project_payload["巡检设置"].setdefault("是否已注册", False)
    project_payload["巡检设置"].setdefault("上次巡检时间", "")
    project_payload["巡检设置"].setdefault("下次建议巡检时间", "")
    project_payload.setdefault("自动推进设置", {})
    for key, value in _默认自动推进设置().items():
        project_payload["自动推进设置"].setdefault(key, deepcopy(value) if isinstance(value, dict) else value)
    project_payload.setdefault("当前批次序号", 0)
    project_payload.setdefault("当前批次状态", "待推进")
    project_payload.setdefault("当前批次对象列表", [])
    project_payload.setdefault("上次推进结果摘要", {})
    for key, value in _空推进摘要().items():
        project_payload["上次推进结果摘要"].setdefault(key, deepcopy(value) if isinstance(value, dict) else value)
    project_payload.setdefault("下次自动推进时间", "")
    project_payload.setdefault("最终交付信息", {})
    project_payload["最终交付信息"].setdefault("交付渠道", "飞书文档+摘要消息")
    project_payload["最终交付信息"].setdefault("摘要消息状态", "待生成")
    project_payload["最终交付信息"].setdefault("最近交付时间", "")
    project_payload["最终交付信息"].setdefault("是否已发送最终报告", False)
    project_payload["最终交付信息"].setdefault("最终报告发送时间", "")
    project_payload["最终交付信息"].setdefault("冻结观察期小时", 48)
    project_payload["最终交付信息"].setdefault("冻结观察截止时间", "")
    project_payload["最终交付信息"].setdefault("冻结版本号", 0)
    project_payload["最终交付信息"].setdefault("交付账号标识", "research")
    participants_payload.setdefault("受访对象列表", [])
    for participant in participants_payload["受访对象列表"]:
        normalized = _标准受访对象(participant)
        participant.clear()
        participant.update(normalized)
        _迁移受访对象到固定direct_shared真值(project_payload, participant)
        if participant.get("当前状态") == "待联系":
            participant["当前状态"] = "待创建会话"
        if _辅助执行会话已真实创建(participant) and participant.get("当前状态") == "待创建会话":
            participant["当前状态"] = "待绑定"
        if _会话已就绪(participant) and participant.get("当前状态") in {"待创建会话", "待绑定"}:
            participant["当前状态"] = "待首发"
        participant["最近一次发送确认状态"] = _推导默认发送确认状态(participant)
        if _发送后可进入待回复(participant) and participant.get("当前状态") in {"待创建会话", "待绑定", "待首发", "待联系"}:
            participant["当前状态"] = "待回复" if _发送确认达到待回复门槛(participant) else "待核验发送"
        if not participant.get("访谈记录路径") and participant.get("姓名"):
            participant["访谈记录路径"] = str(project_dir / "访谈记录" / f"{participant['姓名']}.md")
        try:
            _校验发送状态(participant)
        except ValueError as exc:
            participant["最近一次链路状态"] = participant.get("最近一次链路状态") or f"历史记录待补偿核验：{exc}"
            participant["最近一次业务状态"] = participant.get("最近一次业务状态") or "历史记录待补偿核验"
    if project_payload.get("项目状态") not in {"已关闭", "已停止"}:
        _生成唯一执行会话keys(project_payload, participants_payload["受访对象列表"])


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
    project_type: str = "真实调研",
) -> Path:
    participants = participants or []
    normalized_participants: list[dict[str, Any]] = []
    for participant in participants:
        normalized = dict(participant)
        normalized["飞书标识"] = _标准受访对象飞书标识(normalized.get("飞书标识", ""))
        normalized_participants.append(normalized)
    participants = normalized_participants
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
        project_type=project_type,
    )
    participants_payload = _受访对象清单(project_payload, participants)

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
    interval_minutes = int(project_payload.get("巡检设置", {}).get("巡检间隔分钟", 默认自动推进间隔分钟) or 默认自动推进间隔分钟)
    project_payload["巡检设置"]["下次建议巡检时间"] = (_现在() + timedelta(minutes=interval_minutes)).isoformat()
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
    business_status: str | None = None,
    link_status: str | None = None,
    timeout_reason: str | None = None,
    closure_method: str | None = None,
    count_as_effective_sample: bool | None = None,
    collected_signals: list[str] | None = None,
    sender_account: str | None = None,
    first_message_tool: str | None = None,
    conversation_account: str | None = None,
    execution_channel_truth_type: str | None = None,
    execution_agent: str | None = None,
    execution_session_id: str | None = None,
    execution_session_key: str | None = None,
    helper_execution_session_id: str | None = None,
    helper_execution_session_key: str | None = None,
    conversation_binding_id: str | None = None,
    conversation_binding_status: str | None = None,
    binding_confirmed_at: str | None = None,
    binding_confirmation_evidence: str | None = None,
    binding_target_session_key: str | None = None,
    binding_check_result: str | None = None,
    last_message_id: str | None = None,
    last_chat_id: str | None = None,
    send_confirmation_status: str | None = None,
    send_confirmation_time: str | None = None,
    send_confirmation_evidence: str | None = None,
    last_card_id: str | None = None,
    last_card_result: str | None = None,
    last_recovered_at: str | None = None,
    recovered_to_research: bool | None = None,
    closure_reached: bool | None = None,
    closure_reason: str | None = None,
    auto_unbind_on_completion: bool = True,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    deadline = _解析时间(project_payload.get("项目截止时间", ""))
    frozen = _是否项目已冻结(project_payload)
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
        target["飞书标识"] = _标准受访对象飞书标识(feishu_id) if str(feishu_id).strip() else ""
    if note_path is not None:
        target["访谈记录路径"] = note_path
    if summary is not None:
        target["完成摘要"] = summary
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
    if business_status is not None:
        target["最近一次业务状态"] = business_status
    if link_status is not None:
        target["最近一次链路状态"] = link_status
    if timeout_reason is not None:
        target["超时原因"] = timeout_reason
    if closure_method is not None:
        target["收口方式"] = closure_method
    if count_as_effective_sample is not None:
        target["是否计入有效样本"] = count_as_effective_sample
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
    if execution_channel_truth_type is not None:
        target["执行通道真值类型"] = execution_channel_truth_type
    previous_execution_session_id = str(target.get("执行会话ID", "")).strip()
    previous_execution_session_key = str(target.get("执行会话Key", "")).strip()
    previous_helper_session_id = str(target.get("辅助执行会话ID", "")).strip()
    previous_helper_session_key = str(target.get("辅助执行会话Key", "")).strip()
    if execution_agent is not None:
        target["执行会话代理"] = execution_agent
    if execution_session_id is not None:
        target["执行会话ID"] = execution_session_id
    if execution_session_key is not None:
        target["执行会话Key"] = execution_session_key
    if helper_execution_session_id is not None:
        target["辅助执行会话ID"] = helper_execution_session_id
    elif execution_session_id is not None:
        target["辅助执行会话ID"] = execution_session_id
    if helper_execution_session_key is not None:
        target["辅助执行会话Key"] = helper_execution_session_key
    elif execution_session_key is not None and _看起来像helper执行会话key(execution_session_key):
        target["辅助执行会话Key"] = execution_session_key
    canonical_session_changed = execution_session_key is not None and str(execution_session_key).strip() != previous_execution_session_key
    helper_session_changed = (
        (execution_session_id is not None and str(target.get("执行会话ID", "")).strip() != previous_execution_session_id)
        or (helper_execution_session_id is not None and str(target.get("辅助执行会话ID", "")).strip() != previous_helper_session_id)
        or (helper_execution_session_key is not None and str(target.get("辅助执行会话Key", "")).strip() != previous_helper_session_key)
    )
    if canonical_session_changed:
        _清空绑定核验字段(target, reason="执行会话已切换，旧绑定已失效")
        _清空发送证据字段(target)
        if status is None:
            target["当前状态"] = "待绑定" if _会话已真实创建(target) else "待创建会话"
    elif helper_session_changed and status is None and target.get("当前状态") == "待创建会话":
        target["当前状态"] = "待绑定" if _会话已真实创建(target) else "待创建会话"
    if conversation_binding_id is not None:
        target["会话绑定ID"] = conversation_binding_id
    if binding_confirmed_at is not None:
        target["最近一次绑定确认时间"] = binding_confirmed_at
    if binding_confirmation_evidence is not None:
        target["最近一次绑定确认依据"] = binding_confirmation_evidence
    if binding_target_session_key is not None:
        target["最近一次绑定目标会话Key"] = binding_target_session_key
    if binding_check_result is not None:
        target["最近一次绑定检查结果"] = binding_check_result
    if conversation_binding_status is not None:
        normalized_binding_status = _规范绑定状态(target, conversation_binding_status)
        target["会话绑定状态"] = normalized_binding_status
        if normalized_binding_status in {"未绑定", "已解绑"}:
            target["会话绑定ID"] = ""
            if normalized_binding_status == "已解绑":
                target["最近一次绑定检查结果"] = target.get("最近一次绑定检查结果") or "已解绑"
    elif canonical_session_changed and not target.get("会话绑定状态"):
        target["会话绑定状态"] = "未绑定"
    if last_outbound_at is not None:
        target["最近发出时间"] = last_outbound_at
        if last_outbound_at:
            target.setdefault("访谈轮次记录", []).append({"时间": last_outbound_at, "动作": "发出消息"})
    if last_message_id is not None:
        target["最近一次发送消息ID"] = last_message_id
    if last_chat_id is not None:
        target["最近一次发送chatID"] = last_chat_id
    if send_confirmation_status is not None:
        target["最近一次发送确认状态"] = send_confirmation_status
    if send_confirmation_time is not None:
        target["最近一次发送确认时间"] = send_confirmation_time
    if send_confirmation_evidence is not None:
        target["最近一次发送确认依据"] = send_confirmation_evidence
    if last_card_id is not None:
        target["最近一次卡片ID"] = last_card_id
    if last_card_result is not None:
        target["最近一次卡片结果"] = last_card_result
    if last_recovered_at is not None:
        target["最近一次回收时间"] = last_recovered_at
    if recovered_to_research is not None:
        target["是否已回收至research"] = recovered_to_research
    if closure_reached is not None:
        target["是否已达到收口条件"] = closure_reached
    if closure_reason is not None:
        target["收口原因"] = closure_reason

    explicit_status = status is not None
    inbound_time = _解析时间(last_inbound_at) if last_inbound_at else None
    send_time_for_inbound = _解析时间(target.get("最近发出时间", ""))
    inbound_before_first_touch = bool(inbound_time and send_time_for_inbound and inbound_time < send_time_for_inbound)
    target["最近一次发送确认状态"] = _推导默认发送确认状态(target)
    if not explicit_status:
        if _辅助执行会话已真实创建(target) and target.get("当前状态") == "待创建会话":
            target["当前状态"] = "待绑定"
        if _会话已就绪(target) and target.get("当前状态") in {"待创建会话", "待绑定"}:
            target["当前状态"] = "待首发"
        if _发送后可进入待回复(target) and target.get("当前状态") in {"待创建会话", "待绑定", "待首发", "待联系"}:
            target["当前状态"] = "待回复" if _发送确认达到待回复门槛(target) else "待核验发送"
    if target.get("最近发出时间") and not business_status and not inbound_time:
        target["最近一次业务状态"] = "首轮已确认发出，等待回复" if _发送已确认(target) else "已调用发送，等待确认"
        if not link_status:
            target["最近一次链路状态"] = "已形成可回收 shared 会话" if _发送已确认(target) else "已调用发送，待按 chatId/messageId 核验"
    if inbound_time:
        if last_inbound_at:
            target.setdefault("访谈轮次记录", []).append(
                {"时间": inbound_time.isoformat(), "动作": "收到回复" if not inbound_before_first_touch else "收到首发前消息"}
            )
        if inbound_before_first_touch:
            target["最近一次链路状态"] = "首发前主对话消息"
            target["最近一次业务状态"] = "收到首发前入站，未计入本轮回收"
            target["是否已回收至research"] = False
        else:
            target["最近回复时间"] = inbound_time.isoformat()
            target["最近一次链路状态"] = "回复已进入专属shared会话"
            target["最近一次回收时间"] = inbound_time.isoformat()
            target["是否已回收至research"] = True
            if target.get("最近一次发送消息ID") and target.get("最近一次发送chatID"):
                target["最近一次发送确认状态"] = "已确认送达"
                target["最近一次发送确认时间"] = inbound_time.isoformat()
                target["最近一次发送确认依据"] = (
                    target.get("最近一次发送确认依据") or "已收到对方回复，可确认前序首轮消息已送达。"
                )
            if frozen and not explicit_status:
                target["当前状态"] = "已关闭后回复"
                target["最近一次业务状态"] = "最终报告发送后收到回复"
                target["收口方式"] = "冻结后仅记录"
            elif deadline and inbound_time > deadline and target.get("当前状态") in {"已超时待收口", "已超时", "待回复", "已邀约", "已停滞", "已停滞待回", "待联系"} and not explicit_status:
                target["当前状态"] = "超时后补回"
                target["最近一次业务状态"] = "截止后补回"
                target["是否计入有效样本"] = True
                target["收口方式"] = target.get("收口方式") or "截止后补回，待刷新分析"
            elif target.get("当前状态") in {"待创建会话", "待绑定", "待首发", "待回复", "已邀约", "已停滞", "已停滞待回"} and not explicit_status:
                target["当前状态"] = "访谈中"
                target["最近一次业务状态"] = "已收到回复"
                target["是否计入有效样本"] = True
            if not target.get("访谈记录路径"):
                target["访谈记录路径"] = str(project_dir / "访谈记录" / f"{target.get('姓名', '')}.md")

    question_limit = _单人有效问题上限(project_payload=project_payload, participant=target)
    _更新收口状态(target, question_limit=question_limit)
    _迁移受访对象到固定direct_shared真值(project_payload, target)
    if target.get("是否已达到收口条件") and not explicit_status and target.get("当前状态") in {"访谈中", "超时后补回", "待回复", "已停滞待回"}:
        target["当前状态"] = "已完成"
        target["收口方式"] = target.get("收口方式") or "达到默认收口条件"
        target["是否计入有效样本"] = True

    _校验发送状态(target)

    if auto_unbind_on_completion and _需要自动解绑已完成对象(target):
        _自动解绑已完成对象(
            project_dir=project_dir,
            participant=target,
            finalized_at=target.get("最近一次回收时间") or target.get("最近回复时间") or _现在字符串(),
        )

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

    if inbound_time and not inbound_before_first_touch and deadline and inbound_time > deadline and not frozen:
        analyze_project(project_dir=project_dir, now_at=inbound_time.isoformat())

    return deepcopy(target)


def finalize_participant(project_dir: Path, participant_name: str, finalized_at: str | None = None) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    target = None
    for participant in participants_payload.get("受访对象列表", []):
        if participant.get("姓名") == participant_name:
            target = participant
            break
    if target is None:
        raise KeyError(f"未找到受访对象：{participant_name}")

    result = _自动解绑已完成对象(
        project_dir=project_dir,
        participant=target,
        finalized_at=finalized_at or target.get("最近一次回收时间") or target.get("最近回复时间") or _现在字符串(),
    )
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "项目名称": project_payload.get("项目名称", ""),
        "姓名": participant_name,
        "当前状态": target.get("当前状态", ""),
        "会话绑定状态": target.get("会话绑定状态", ""),
        **result,
    }


def ingest_participant_reply(
    project_dir: Path,
    participant_name: str,
    reply_text: str,
    reply_at: str | None = None,
    assistant_text: str | None = None,
    execution_session_key: str | None = None,
    participant_open_id: str | None = None,
    project_type: str | None = None,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    target = None
    for participant in participants_payload.get("受访对象列表", []):
        if participant.get("姓名") == participant_name:
            target = participant
            break
    if target is None:
        raise KeyError(f"未找到受访对象：{participant_name}")

    expected_project_type = str(project_payload.get("项目类型", "真实调研")).strip() or "真实调研"
    expected_session_key = str(target.get("执行会话Key", "")).strip()
    expected_open_id = _提取飞书open_id(target.get("飞书标识", ""))
    if project_type and str(project_type).strip() != expected_project_type:
        return {
            "ok": False,
            "错误": "项目上下文漂移",
            "详情": f"project_type={project_type} 与项目文件中的 {expected_project_type} 不一致",
        }
    if execution_session_key and str(execution_session_key).strip() != expected_session_key:
        return {
            "ok": False,
            "错误": "项目上下文漂移",
            "详情": f"execution_session_key={execution_session_key} 与项目文件中的 {expected_session_key} 不一致",
        }
    if participant_open_id and str(participant_open_id).strip() != expected_open_id:
        return {
            "ok": False,
            "错误": "项目上下文漂移",
            "详情": f"participant_open_id={participant_open_id} 与项目文件中的 {expected_open_id} 不一致",
        }

    reply_at_text = _时间字符串(reply_at) or _现在字符串()
    prompt_text = str(assistant_text or "").strip()
    normalized_reply = str(reply_text or "").strip()
    if not normalized_reply:
        return {
            "ok": False,
            "错误": 回复正文缺失错误,
            "详情": "当前消息未附正文",
            "shouldUnbind": False,
            "nextQuestion": "",
            "nextSignal": "",
        }
    prompt_target = _识别访谈问题目标(prompt_text)
    fallback_signals = _从回复文本提取信号(normalized_reply)
    recognized_signals = [prompt_target] if prompt_target else fallback_signals
    is_process_message = _是否非调研流程消息(normalized_reply)
    existing_count = int(target.get("累计有效问题数", 0) or 0)
    next_count = existing_count if is_process_message else existing_count + 1
    merged_signals = _去重信号(
        list(target.get("已收集信号", []) or []) + [str(item).strip() for item in recognized_signals if str(item).strip()]
    )

    note_lines = [
        f"## 收到回复 {reply_at_text}",
        f"- 上一问：{prompt_text or '未提供'}",
        f"- 用户回复：{normalized_reply or '空回复'}",
        f"- 是否计入有效问题数：{'否' if is_process_message else '是'}",
        f"- 累计有效问题数：{next_count}",
        f"- 识别信号：{('、'.join(recognized_signals) if recognized_signals else '无')}",
    ]
    try:
        note_path = _写入访谈记录(project_dir, target, note_lines)
    except Exception as exc:
        update_participant(
            project_dir=project_dir,
            participant_name=participant_name,
            last_inbound_at=reply_at_text,
            business_status="已收到回复但回写失败",
            link_status=f"shared 会话回写失败：{exc}",
            recovered_to_research=False,
            last_recovered_at=reply_at_text,
            auto_unbind_on_completion=False,
        )
        return {
            "ok": False,
            "错误": "回写失败",
            "详情": str(exc),
            "shouldUnbind": False,
        }

    business_status = "收到非调研流程消息，未计入有效问题数" if is_process_message else "已收到回复并完成正式回写"
    link_status = "shared 会话已接收非调研流程消息" if is_process_message else "回复已进入专属shared会话"
    updated = update_participant(
        project_dir=project_dir,
        participant_name=participant_name,
        note_path=str(note_path),
        last_inbound_at=reply_at_text,
        effective_question_count=next_count,
        collected_signals=merged_signals if merged_signals else None,
        business_status=business_status,
        link_status=link_status,
        recovered_to_research=not is_process_message,
        last_recovered_at=reply_at_text,
        count_as_effective_sample=False if is_process_message else True,
        auto_unbind_on_completion=False,
    )
    should_unbind = _需要自动解绑已完成对象(updated)
    next_signal, next_question = _下一轮问题文本(project_payload=project_payload, participant=updated, reply_text=normalized_reply)
    return {
        "ok": True,
        "姓名": participant_name,
        "当前状态": updated.get("当前状态", ""),
        "会话绑定状态": updated.get("会话绑定状态", ""),
        "是否非调研流程消息": is_process_message,
        "累计有效问题数": int(updated.get("累计有效问题数", 0) or 0),
        "已收集信号": updated.get("已收集信号", []),
        "是否达到收口条件": bool(updated.get("是否已达到收口条件", False)),
        "收口原因": updated.get("收口原因", ""),
        "shouldUnbind": should_unbind,
        "结束提示": _收口结束提示() if should_unbind else "",
        "nextSignal": "" if should_unbind or is_process_message else next_signal,
        "nextQuestion": "" if should_unbind or is_process_message else next_question,
        "访谈记录路径": str(note_path),
    }


def repair_project_participants(project_dir: Path) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    participants = participants_payload.get("受访对象列表", [])
    repaired_count = 0
    reset_count = 0
    unresolved: list[str] = []

    for participant in participants:
        original_feishu = str(participant.get("飞书标识", "")).strip()
        repaired_feishu = _尝试修复受访对象飞书标识(
            original_feishu,
            str(participant.get("纳入原因", "")).strip(),
        )
        changed = False
        if repaired_feishu and repaired_feishu != original_feishu:
            participant["飞书标识"] = repaired_feishu
            changed = True
        elif not repaired_feishu:
            unresolved.append(str(participant.get("姓名", "")).strip() or "未命名受访对象")
            participant["飞书标识"] = ""
            changed = True

        participant.setdefault("_需要重置链路", False)
        if changed or participant.get("执行会话Key") == "research-shared-openclaw-user":
            participant["_需要重置链路"] = True
            repaired_count += 1

    _生成唯一执行会话keys(project_payload, participants, force_reset_existing=True)

    for participant in participants:
        if not participant.pop("_需要重置链路", False):
            continue
        participant["执行会话ID"] = ""
        participant["辅助执行会话ID"] = ""
        participant["辅助执行会话Key"] = ""
        participant["会话绑定ID"] = ""
        participant["会话绑定状态"] = "未绑定"
        participant["最近一次绑定确认时间"] = ""
        participant["最近一次绑定确认依据"] = ""
        participant["最近一次绑定目标会话Key"] = ""
        participant["最近一次绑定检查结果"] = ""
        participant["最近发出时间"] = ""
        participant["最近回复时间"] = ""
        participant["最近一次发送消息ID"] = ""
        participant["最近一次发送chatID"] = ""
        participant["最近一次发送确认状态"] = ""
        participant["最近一次发送确认时间"] = ""
        participant["最近一次发送确认依据"] = ""
        participant["最近一次卡片ID"] = ""
        participant["最近一次卡片结果"] = ""
        participant["最近一次回收时间"] = ""
        participant["是否已回收至research"] = False
        participant["首条消息工具"] = ""
        participant["最近一次提问方式"] = ""
        participant["最近一次卡片类型"] = ""
        participant["最近一次业务状态"] = "名单修复后待重建专属 shared 会话"
        participant["最近一次链路状态"] = "名单修复后已清理错误绑定/半成品发送状态"
        participant["访谈轮次记录"] = [
            item
            for item in participant.get("访谈轮次记录", [])
            if isinstance(item, dict) and str(item.get("动作", "")).strip() not in {"发出消息", "收到回复"}
        ]
        if participant.get("飞书标识"):
            participant["当前状态"] = "待创建会话"
        else:
            participant["当前状态"] = "待创建会话"
        reset_count += 1

    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "项目名称": project_payload.get("项目名称", ""),
        "修复人数": repaired_count,
        "重置链路人数": reset_count,
        "未能修复对象": unresolved,
    }


def _首轮说明消息(project_payload: dict[str, Any], participant: dict[str, Any]) -> str:
    project_name = project_payload.get("项目名称", "")
    return (
        f"嗨{participant.get('姓名', '')}，我是内部调研助手。"
        f"这边在做“{project_name}”的小范围内部访谈，只占用你 1 分钟做个很轻的了解。"
        "直接回复一个选项就行，不需要长篇回复。"
    )


def _首轮文本选择题(project_payload: dict[str, Any], participant: dict[str, Any]) -> dict[str, Any]:
    question = "关于这次调研涉及的主题，你现在更接近哪种情况？"
    options = ["已在使用", "知道但少用", "还没开始", "说不清"]
    return {
        "类型": "文本选择题",
        "question": question,
        "options": options,
        "说明": _首轮说明消息(project_payload, participant),
    }


def _文本选择题消息(question: dict[str, Any]) -> str:
    options = [str(item).strip() for item in question.get("options", []) if str(item).strip()]
    return f"{question.get('question', '')}\n请直接回复：{' / '.join(options)}"


def _首轮完整文本消息(project_payload: dict[str, Any], participant: dict[str, Any], question: dict[str, Any]) -> str:
    return f"{_首轮说明消息(project_payload, participant)}\n\n{_文本选择题消息(question)}"


def _构建首轮文本消息参数(participant: dict[str, Any], question: dict[str, Any], send_account: str) -> dict[str, Any]:
    return {
        "action": "send",
        "channel": "feishu",
        "accountId": send_account,
        "target": participant.get("飞书标识", ""),
        "message": _文本选择题消息(question),
    }


def _下一轮信号目标(participant: dict[str, Any]) -> str:
    collected = {str(item).strip() for item in participant.get("已收集信号", []) if str(item).strip()}
    for signal in 关键收口信号:
        if signal not in collected:
            return signal
    return ""


def _是否已使用过类型回复(reply_text: str) -> bool:
    normalized = _标准化短文本(reply_text)
    return any(keyword in normalized for keyword in ["经常用", "每天都在用", "用过几次", "已在使用", "知道但少用"])


def _下一轮问题文本(project_payload: dict[str, Any], participant: dict[str, Any], reply_text: str = "") -> tuple[str, str]:
    next_signal = _下一轮信号目标(participant)
    if next_signal == "主要使用场景或主要阻力":
        if _是否已使用过类型回复(reply_text):
            return (
                next_signal,
                "你现在用 openclaw / 小龙虾时，主要更接近哪种情况？\n"
                "请直接回复：上手或配置麻烦 / 稳定性 / 速度有时不理想 / 不太清楚哪些场景最该用它 / 基本没明显卡点 / 其他",
            )
        return (
            next_signal,
            "你现在没真正用起来，最主要卡在哪？\n"
            "请直接回复：不知道怎么开始 / 没时间试 / 场景不明确 / 遇到过问题 / 其他",
        )
    if next_signal == "培训期待或改进方向":
        return (
            next_signal,
            "如果只优先改一件事，你最希望先改哪类问题？\n"
            "请直接回复：响应更快 / 少报错、少失败 / 结果更稳定一致 / 操作链路更顺 / 其他",
        )
    return "", ""


def _构建shared协议载荷(
    project_dir: Path,
    project_payload: dict[str, Any],
    participant: dict[str, Any],
    send_account: str,
    question: dict[str, Any],
    participant_command: str,
    ingest_reply_command: str,
    finalize_command: str,
) -> dict[str, Any]:
    open_id = _提取飞书open_id(participant.get("飞书标识", ""))
    text_message = _首轮完整文本消息(project_payload, participant, question)
    return {
        "protocol_version": "internal-interview-shared/v1",
        "project_dir": str(project_dir),
        "project_type": str(project_payload.get("项目类型", "真实调研")).strip() or "真实调研",
        "participant_name": str(participant.get("姓名", "")).strip(),
        "participant_open_id": open_id,
        "execution_session_key": str(participant.get("执行会话Key", "")).strip(),
        "first_touch_message": {
            "action": "send",
            "channel": "feishu",
            "accountId": send_account,
            "target": participant.get("飞书标识", ""),
            "message": text_message,
        },
        "send_writeback_command": participant_command,
        "ingest_reply_command": ingest_reply_command,
        "finalize_participant_command": finalize_command,
        "unbind_rule": {
            "required": True,
            "accountId": send_account,
            "target": f"user:{open_id}" if open_id else "",
            "action": "unbind",
        },
    }


def _extract_shared_protocol_payload(message_text: str) -> dict[str, Any]:
    raw = str(message_text or "")
    match = re.search(
        r"\[internal-interview-shared-payload/v1\]\s*(\{.*?\})\s*\[/internal-interview-shared-payload/v1\]",
        raw,
        re.DOTALL,
    )
    if not match:
        return {}
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _shared_protocol_message_is_complete(message_text: str) -> bool:
    payload = _extract_shared_protocol_payload(message_text)
    required_keys = {
        "protocol_version",
        "project_dir",
        "project_type",
        "participant_name",
        "participant_open_id",
        "execution_session_key",
        "first_touch_message",
        "ingest_reply_command",
        "finalize_participant_command",
        "unbind_rule",
    }
    if not payload or payload.get("protocol_version") != "internal-interview-shared/v1":
        return False
    if not required_keys.issubset(payload.keys()):
        return False
    if not isinstance(payload.get("first_touch_message"), dict):
        return False
    if not isinstance(payload.get("unbind_rule"), dict):
        return False
    return True


def _检查shared协议状态(participant: dict[str, Any], session_root: Path | None = None) -> dict[str, str | bool]:
    if session_root is None:
        session_root = 默认shared会话目录
    helper_session_id = str(participant.get("辅助执行会话ID", "")).strip() or str(participant.get("执行会话ID", "")).strip()
    if not helper_session_id:
        return {"状态": "未创建helper会话", "是否完整": False, "是否已投递": False, "原因": "当前对象还没有 helper shared 会话"}
    session_file = session_root / f"{helper_session_id}.jsonl"
    if not session_file.exists():
        return {"状态": "未找到helper会话文件", "是否完整": False, "是否已投递": False, "原因": f"缺少 helper shared 会话文件：{session_file}"}

    last_inter_session_message = ""
    saw_spawn_bootstrap = False
    try:
        lines = session_file.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return {"状态": "读取失败", "是否完整": False, "是否已投递": False, "原因": str(exc)}
    for raw_line in lines:
        try:
            entry = json.loads(raw_line)
        except Exception:
            continue
        role, message_text, _ = _提取会话消息(entry)
        if role != "user":
            continue
        if "[Inter-session message]" in message_text:
            last_inter_session_message = message_text
        elif "[Subagent Context]" in message_text:
            saw_spawn_bootstrap = True
    if not last_inter_session_message:
        reason = "当前 shared 会话仅被创建，尚未收到正式 strict payload 投递" if saw_spawn_bootstrap else "shared 会话里还没有 inter-session payload 记录"
        return {"状态": "未收到正式投递", "是否完整": False, "是否已投递": False, "原因": reason}
    if _shared_protocol_message_is_complete(last_inter_session_message):
        return {"状态": "协议完整", "是否完整": True, "是否已投递": True, "原因": "最近一条 inter-session payload 已包含完整 strict shared 协议"}
    return {"状态": "协议不完整", "是否完整": False, "是否已投递": True, "原因": "最近一条 inter-session payload 缺少 strict shared 协议字段"}


def _是否非法预建shared(participant: dict[str, Any], protocol_check: dict[str, str | bool] | None = None) -> bool:
    if not _辅助执行会话已真实创建(participant):
        return False
    if _发送记录完整(participant):
        return False
    if not _仍处于首发前阶段(participant):
        return False
    protocol = protocol_check or _检查shared协议状态(participant)
    return str(protocol.get("状态", "")).strip() == "未收到正式投递" and not bool(protocol.get("是否已投递", False))


def _是否需要回退半成品shared(participant: dict[str, Any], protocol_check: dict[str, str | bool] | None = None) -> bool:
    if not _辅助执行会话已真实创建(participant):
        return False
    if _发送记录完整(participant):
        return False
    protocol = protocol_check or _检查shared协议状态(participant)
    if _是否非法预建shared(participant, protocol_check=protocol):
        return True
    status = str(participant.get("当前状态", "")).strip()
    protocol_status = str(protocol.get("状态", "")).strip()
    return status in {"本轮冻结待后续批次", "待批次开放"} and protocol_status in {"未收到正式投递", "未找到helper会话文件"}


def _构建shared首轮投递消息(
    project_dir: Path,
    project_payload: dict[str, Any],
    participant: dict[str, Any],
    send_account: str,
    question: dict[str, Any],
) -> str:
    text_message = _首轮完整文本消息(project_payload, participant, question)
    open_id = _提取飞书open_id(participant.get("飞书标识", ""))
    question_limit = _单人有效问题上限(project_payload=project_payload, participant=participant)
    message_payload = {
        "action": "send",
        "channel": "feishu",
        "accountId": send_account,
        "target": participant.get("飞书标识", ""),
        "message": text_message,
    }
    participant_command = (
        f"python3 /Users/a123/.openclaw/workspace-research/skills/internal-interview-research/scripts/"
        f"manage_internal_interview_project.py participant "
        f"--project-dir {json.dumps(str(project_dir), ensure_ascii=False)} "
        f"--name {json.dumps(participant.get('姓名', ''), ensure_ascii=False)} "
        f"--status 待回复 "
        f"--sender-account {json.dumps(send_account, ensure_ascii=False)} "
        f"--first-message-tool message "
        f"--conversation-account {json.dumps(send_account, ensure_ascii=False)} "
        f"--execution-channel-truth-type {json.dumps(participant.get('执行通道真值类型', 'direct-shared'), ensure_ascii=False)} "
        f"--execution-agent research-shared "
        f"--execution-session-id {json.dumps(participant.get('执行会话ID', ''), ensure_ascii=False)} "
        f"--execution-session-key {json.dumps(participant.get('执行会话Key', ''), ensure_ascii=False)} "
        f"--helper-execution-session-id {json.dumps(participant.get('辅助执行会话ID', participant.get('执行会话ID', '')), ensure_ascii=False)} "
        f"--helper-execution-session-key {json.dumps(participant.get('辅助执行会话Key', ''), ensure_ascii=False)} "
        f"--conversation-binding-id {json.dumps(participant.get('会话绑定ID', ''), ensure_ascii=False)} "
        f"--conversation-binding-status 已绑定 "
        f"--binding-confirmed-at <bindingConfirmedAt> "
        f"--binding-confirmation-evidence {json.dumps('status 校验通过，targetSessionKey 与执行会话Key 一致', ensure_ascii=False)} "
        f"--binding-target-session-key {json.dumps(participant.get('执行会话Key', ''), ensure_ascii=False)} "
        f"--binding-check-result 已核验通过 "
        f"--question-mode 文本选择题 "
        f"--choice-question-count {int(participant.get('累计选择题次数', 0) or 0) + 1} "
        f"--effective-question-count {int(participant.get('累计有效问题数', 0) or 0) + 1} "
        f"--business-status {json.dumps('首轮已确认发出，等待回复', ensure_ascii=False)} "
        f"--link-status {json.dumps('已形成可回收 shared 会话', ensure_ascii=False)} "
        f"--last-message-id <messageId> "
        f"--last-chat-id <chatId> "
        f"--send-confirmation-status {json.dumps('已确认回执', ensure_ascii=False)} "
        f"--send-confirmation-time <sendTime> "
        f"--send-confirmation-evidence {json.dumps('shared 会话 message 工具真实返回 messageId + chatId', ensure_ascii=False)} "
        f"--last-outbound-at <sendTime>"
    )
    ingest_reply_command = (
        f"python3 /Users/a123/.openclaw/workspace-research/skills/internal-interview-research/scripts/"
        f"manage_internal_interview_project.py ingest-reply "
        f"--project-dir {json.dumps(str(project_dir), ensure_ascii=False)} "
        f"--name {json.dumps(participant.get('姓名', ''), ensure_ascii=False)} "
        f"--reply-text <latestUserReply> "
        f"--reply-at <replyAt> "
        f"--assistant-text <lastQuestionText> "
        f"--execution-session-key {json.dumps(participant.get('执行会话Key', ''), ensure_ascii=False)} "
        f"--participant-open-id {json.dumps(open_id, ensure_ascii=False)} "
        f"--project-type {json.dumps(project_payload.get('项目类型', '真实调研'), ensure_ascii=False)}"
    )
    finalize_command = (
        f"python3 /Users/a123/.openclaw/workspace-research/skills/internal-interview-research/scripts/"
        f"manage_internal_interview_project.py finalize-participant "
        f"--project-dir {json.dumps(str(project_dir), ensure_ascii=False)} "
        f"--name {json.dumps(participant.get('姓名', ''), ensure_ascii=False)} "
        f"--finalized-at <replyAt>"
    )
    protocol_payload = _构建shared协议载荷(
        project_dir=project_dir,
        project_payload=project_payload,
        participant=participant,
        send_account=send_account,
        question=question,
        participant_command=participant_command,
        ingest_reply_command=ingest_reply_command,
        finalize_command=finalize_command,
    )
    return (
        f"你现在是 {participant.get('姓名', '')} 这条专属 research-shared 会话。"
        "\n如果这条 inter-session 指令里没有完整的 strict payload，直接回复“shared 协议不完整”，不要首发，也不要接管后续访谈。"
        "\n[internal-interview-shared-payload/v1]"
        f"\n{json.dumps(protocol_payload, ensure_ascii=False, indent=2)}"
        "\n[/internal-interview-shared-payload/v1]"
        f"\n项目名称：{project_payload.get('项目名称', '')}"
        f"\n项目目录：{project_dir}"
        f"\n项目类型：{project_payload.get('项目类型', '真实调研')}"
        f"\n受访对象：{participant.get('姓名', '')}"
        f"\n受访对象open_id：{open_id}"
        f"\n执行会话Key：{participant.get('执行会话Key', '')}"
        f"\n当前收口规则：命中三类收口信号，或累计有效问题数达到 {question_limit}，任一满足就收口并自动解绑。"
        "\n先校验上面这些上下文是否齐全；缺任何一项，直接回复“项目上下文缺失”，不要继续访谈。"
        "\n禁止读取其他项目文件来补上下文；如果你读到的项目路径与上面的项目目录不一致，直接回复“项目上下文漂移”，不要继续访谈。"
        f"\n只允许做三步："
        f"\n1. 先用 `message` 工具按下面参数真实发出首轮文本访谈，不要改 accountId、target、message："
        f"\n{json.dumps(message_payload, ensure_ascii=False, indent=2)}"
        "\n2. 如果 `message` 返回 `ok=true` 且同时带有 `messageId` 和 `chatId`，"
        "再立刻用 `exec` 执行下面这条正式回写命令，把发送结果正式回写项目文件；"
        "如果没拿到 `messageId + chatId`，不要回写待回复，只回复失败原因。"
        f"\n{participant_command}"
        "\n3. 从现在开始，这条 shared 会话后续每次收到用户回复时，都必须先做正式回写，再决定是否继续追问。"
        "\n3.1 如果当前 turn 同时存在真实 `user` 文本和 `openclaw.runtime-context`，真实 `user` 文本是唯一正文真值。"
        "`openclaw.runtime-context` 只允许用来提取 `<replyAt>`、`message_id`、`sender_id`。"
        "先从真实 `user` 文本提取 `<latestUserReply>`，再把你上一条真正发给用户的问题文本填到 `<lastQuestionText>`。"
        "\n3.2 如果当前消息没有真实 `user` 正文，不要猜，也不要说“没看到正文”。"
        "必须直接返回结构化错误：`{\"ok\": false, \"错误\": \"reply_text_missing\", \"详情\": \"当前消息未附正文\"}`。"
        "\n3.3 立刻用 `exec` 执行下面这条正式回写命令；如果返回 `ok=false`，停止访谈，只说明“项目回写失败”。"
        f"\n{ingest_reply_command}"
        "\n3.4 如果回写结果里 `shouldUnbind=true`："
        "\n- 先向用户发送结束提示，固定口径必须包含：本次调研已完成 / 后续补充不再纳入记录 / 当前私聊已切回 research 主对话"
        f"\n- 再调用 `feishu_conversation_binding` 执行 `action=unbind, accountId={send_account}, target=user:{open_id}`"
        "\n- 只有解绑工具成功后，才能再执行下面这条命令，把项目文件正式写成已解绑："
        f"\n{finalize_command}"
        "\n- 完成后不要继续追问。"
        "\n3.5 如果回写结果里 `是否非调研流程消息=true`：只短提示“当前这条私聊用于本次调研回收；非调研问题请到 `research` 主对话单独提”，不要继续展开，也不要计入有效问题数。"
        "\n最后只回复一段 JSON，必须包含：ok、messageId、chatId、sendTime。"
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
    option_text = " / ".join(
        str(item.get("text") or item.get("label") or "").strip()
        for item in options
        if str(item.get("text") or item.get("label") or "").strip()
    )
    return f"{card.get('question', '')}\n请直接回复：{option_text}"


def _待派发状态集合() -> set[str]:
    return {"待创建会话", "待绑定", "待首发", "待联系"}


def _派发候选对象(participants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [participant for participant in participants if participant.get("当前状态", "待创建会话") in _待派发状态集合()]


def _派发阻塞对象(participants: list[dict[str, Any]], session_root: Path | None = None) -> list[dict[str, Any]]:
    blocked: list[dict[str, Any]] = []
    for participant in participants:
        status = participant.get("当前状态", "待创建会话")
        if status not in _待派发状态集合():
            continue
        protocol_check = _检查shared协议状态(participant, session_root=session_root)
        if not participant.get("飞书标识"):
            blocked.append({"姓名": participant.get("姓名", ""), "原因": "受访对象缺少飞书标识"})
        elif not _提取飞书open_id(participant.get("飞书标识", "")):
            blocked.append({"姓名": participant.get("姓名", ""), "原因": "受访对象飞书标识不合法"})
        elif _是否需要回退半成品shared(participant, protocol_check=protocol_check):
            blocked.append({"姓名": participant.get("姓名", ""), "原因": f"{非法预建shared文案} 当前应先回退清理后再按正式批次重建。"})
        elif not participant.get("执行会话Key"):
            blocked.append({"姓名": participant.get("姓名", ""), "原因": "未生成执行会话Key"})
        elif not _绑定已核验(participant):
            blocked.append({"姓名": participant.get("姓名", ""), "原因": "未完成固定 direct shared 通道绑定核验"})
    return blocked


def _规范cron表达式(interval_minutes: int) -> str:
    interval = int(interval_minutes or 0)
    if interval <= 0:
        raise ValueError("interval_minutes 必须大于 0")
    if interval < 60:
        return f"*/{interval} * * * *"
    if interval == 60:
        return "0 * * * *"
    if interval % 60 == 0:
        hours = interval // 60
        if hours == 24:
            return "0 0 * * *"
        return f"0 */{hours} * * *"
    return f"*/{interval} * * * *"


def _需要自动注册推进任务(project_payload: dict[str, Any], participants: list[dict[str, Any]]) -> bool:
    if str(project_payload.get("项目类型", "真实调研")).strip() != "真实调研":
        return False
    if project_payload.get("运行模式") == "链路验收":
        return False
    if not project_payload.get("项目截止时间"):
        return False
    if str(project_payload.get("受访对象来源方式", "")).strip() != "直接名单":
        return False
    if project_payload.get("建议名单待确认"):
        return False
    if project_payload.get("停止信息", {}).get("是否已停止"):
        return False
    if _是否项目已冻结(project_payload):
        return False
    actionable_statuses = {"待创建会话", "待绑定", "待首发", "待核验发送", "待回复", "访谈中"}
    return any(str(item.get("当前状态", "")).strip() in actionable_statuses for item in participants)


def _发送确认不足回退状态(participant: dict[str, Any]) -> str:
    if _发送记录完整(participant) and _会话已就绪(participant):
        return "待核验发送"
    return "待首发"


def _回退发送确认不足对象(participants: list[dict[str, Any]]) -> list[str]:
    rewound: list[str] = []
    for participant in participants:
        if str(participant.get("当前状态", "")).strip() != "待回复":
            continue
        if _发送确认达到待回复门槛(participant):
            continue
        participant["当前状态"] = _发送确认不足回退状态(participant)
        participant["最近一次业务状态"] = "历史发送确认不足，已回退待补核验"
        participant["最近一次链路状态"] = "历史发送确认不足，已回退待补核验"
        rewound.append(str(participant.get("姓名", "")).strip())
    return rewound


def _同步当前批次信息(
    project_payload: dict[str, Any],
    participants: list[dict[str, Any]],
    dispatch_plan: dict[str, Any] | None = None,
) -> None:
    batch_size = int(project_payload.get("派发策略", {}).get("每批人数", 10) or 10)
    active_pending_statuses = {"待创建会话", "待绑定", "待首发", "待核验发送"}
    current_batch: list[str] = []
    if dispatch_plan:
        current_batch = [
            str(item.get("姓名", "")).strip()
            for item in dispatch_plan.get("首轮对象列表", [])
            if str(item.get("姓名", "")).strip()
        ]
        if not current_batch:
            first_batch = (dispatch_plan.get("批次列表") or [{}])[0]
            current_batch = [
                str(item.get("姓名", "")).strip()
                for item in first_batch.get("成员", [])
                if str(item.get("姓名", "")).strip()
            ]
    if not current_batch:
        current_batch = [
            str(participant.get("姓名", "")).strip()
            for participant in participants
            if str(participant.get("当前状态", "")).strip() in active_pending_statuses
        ][:batch_size]
    if dispatch_plan:
        batches = dispatch_plan.get("批次列表") or []
        if batches:
            project_payload["当前批次序号"] = int(batches[0].get("批次序号", 1) or 1)
        else:
            project_payload["当前批次序号"] = 1 if current_batch else 0
    else:
        project_payload["当前批次序号"] = 1 if current_batch else 0
    project_payload["当前批次对象列表"] = current_batch
    if current_batch:
        project_payload["当前批次状态"] = "待推进"
    elif any(str(item.get("当前状态", "")).strip() == "待回复" for item in participants):
        project_payload["当前批次状态"] = "等待回复"
    else:
        project_payload["当前批次状态"] = "无待推进对象"


def _构建首轮执行合同(project_dir: Path, participant: dict[str, Any]) -> dict[str, Any]:
    script_path = _管理脚本路径()
    participant_name = str(participant.get("姓名", "")).strip()
    project_dir_text = str(project_dir)
    return {
        "姓名": participant_name,
        "当前状态": str(participant.get("当前状态", "")).strip(),
        "动作类型": "strict-shared-首轮派发",
        "必须执行到": "shared 首发完成并完成发送核验回写",
        "outreachPlan命令": (
            f"python3 {script_path} outreach-plan --project-dir '{project_dir_text}' --name '{participant_name}'"
        ),
        "执行步骤": [
            "创建或确认专属 shared 会话",
            "绑定并执行 status verify",
            "只用 outreach-plan 给出的 sessionKey 投递 strict payload",
            "由 shared 会话实际调用 message(accountId=research) 发出首轮",
            "拿到 ok + messageId + chatId 后回写项目文件",
        ],
        "禁止事项": [
            "禁止手写 sessions_send 参数",
            "禁止追加 label",
            "禁止泄漏 NO_REPLY 或内部待机文案",
        ],
    }


def _构建跟进行动合同(project_dir: Path, action: dict[str, str]) -> dict[str, Any]:
    script_path = _管理脚本路径()
    participant_name = str(action.get("姓名", "")).strip()
    action_name = str(action.get("建议动作", "")).strip()
    return {
        "姓名": participant_name,
        "当前状态": str(action.get("当前状态", "")).strip(),
        "动作类型": action_name,
        "inspect命令": f"python3 {script_path} inspect --project-dir '{project_dir}'",
        "执行约束": "先读取 inspect/advance 结果，再按项目文件真实状态执行，不得临场改口径。",
    }


def _构建推进摘要(
    *,
    status: str,
    now: datetime,
    current_batch: list[str],
    blocked: list[dict[str, Any]],
    rewound: list[str],
    auto_unbound: list[str] | None = None,
    followups: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    followups = followups or []
    auto_unbound = auto_unbound or []
    summary = _空推进摘要()
    summary["执行状态"] = status
    summary["更新时间"] = now.isoformat()
    summary["本轮完成跟进人数"] = len(followups)
    summary["本轮阻塞对象"] = blocked
    detail_parts: list[str] = []
    if current_batch:
        detail_parts.append(f"当前批次 {len(current_batch)} 人：{'、'.join(current_batch)}")
    if rewound:
        detail_parts.append(f"发送确认回退 {len(rewound)} 人")
    if auto_unbound:
        detail_parts.append(f"自动解绑 {len(auto_unbound)} 人")
    if blocked:
        detail_parts.append(f"阻塞 {len(blocked)} 人")
    summary_text = "；".join(detail_parts) if detail_parts else status
    summary["摘要"] = summary_text
    summary["摘要键"] = f"{status}|{'/'.join(current_batch)}|{len(rewound)}|{len(auto_unbound)}|{len(blocked)}|{len(followups)}"
    return summary


def _自动推进设置(project_payload: dict[str, Any]) -> dict[str, Any]:
    settings = project_payload.setdefault("自动推进设置", {})
    for key, value in _默认自动推进设置().items():
        settings.setdefault(key, deepcopy(value) if isinstance(value, dict) else value)
    return settings


def _标准后台worker类型(trigger: str | None) -> str:
    normalized = str(trigger or "manual").strip()
    if normalized in {"cron", "cron-worker"}:
        return "cron-worker"
    return "manual-worker"


def _后台worker活跃(project_payload: dict[str, Any]) -> bool:
    return bool(_自动推进设置(project_payload).get("后台执行中"))


def _后台worker过期信息(project_payload: dict[str, Any], *, now_at: str | None = None) -> dict[str, str]:
    settings = _自动推进设置(project_payload)
    if not bool(settings.get("后台执行中")):
        return {}
    worker_run_id = str(settings.get("后台执行worker运行ID", "")).strip()
    if not worker_run_id:
        return {"code": 后台worker运行ID缺失错误, "detail": "后台 worker 缺少运行ID，视为失活。"}
    last_heartbeat = _解析时间(str(settings.get("后台执行最近心跳时间", "")).strip())
    started_at = _解析时间(str(settings.get("后台执行开始时间", "")).strip())
    anchor_time = last_heartbeat or started_at
    if anchor_time is None:
        return {"code": 后台worker时间缺失错误, "detail": "后台 worker 缺少心跳和启动时间，视为失活。"}
    current_time = _解析时间(now_at) if now_at else _现在()
    threshold_minutes = max(
        int(settings.get("推进间隔分钟", 默认自动推进间隔分钟) or 默认自动推进间隔分钟),
        15,
    )
    if current_time - anchor_time > timedelta(minutes=threshold_minutes):
        return {
            "code": 后台worker超时错误,
            "detail": f"后台 worker 超过 {threshold_minutes} 分钟没有心跳，视为失活。",
        }
    return {}


def _清理失活后台worker(
    project_dir: Path,
    project_payload: dict[str, Any],
    participants_payload: dict[str, Any],
    *,
    code: str,
    detail: str,
    now_at: str | None = None,
) -> None:
    settings = _自动推进设置(project_payload)
    current_time = _时间字符串(now_at) or _现在字符串()
    settings["后台执行中"] = False
    settings["后台执行worker类型"] = ""
    settings["后台执行worker运行ID"] = ""
    settings["后台执行worker会话Key"] = ""
    settings["后台执行开始时间"] = ""
    settings["后台执行最近心跳时间"] = current_time
    settings["后台执行最近摘要"] = _后台worker前台摘要(code, detail)
    settings["后台执行最近诊断"] = code
    _写回项目(project_dir, project_payload, participants_payload)


def _当前批次真实快照(project_payload: dict[str, Any], participants: list[dict[str, Any]]) -> dict[str, Any]:
    payload_copy = deepcopy(project_payload)
    _同步当前批次信息(payload_copy, participants)
    return {
        "当前批次序号": int(payload_copy.get("当前批次序号", 0) or 0),
        "当前批次状态": str(payload_copy.get("当前批次状态", "")).strip(),
        "当前批次对象列表": list(payload_copy.get("当前批次对象列表", [])),
    }


def _当前批次是否与真实状态一致(project_payload: dict[str, Any], participants: list[dict[str, Any]]) -> bool:
    expected = _当前批次真实快照(project_payload, participants)
    return (
        int(project_payload.get("当前批次序号", 0) or 0) == expected["当前批次序号"]
        and str(project_payload.get("当前批次状态", "")).strip() == expected["当前批次状态"]
        and list(project_payload.get("当前批次对象列表", [])) == expected["当前批次对象列表"]
    )


def _读取cron任务列表(cron_jobs_path: Path | None) -> list[dict[str, Any]]:
    path = cron_jobs_path or 默认cron任务路径
    if not path.exists():
        return []
    payload = _读取结构化文件(path)
    if not isinstance(payload, dict):
        return []
    jobs = payload.get("jobs", [])
    if not isinstance(jobs, list):
        return []
    return [job for job in jobs if isinstance(job, dict)]


def _查找项目cron任务(project_payload: dict[str, Any], jobs: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    advance_id = str(project_payload.get("巡检设置", {}).get("推进任务ID", "")).strip()
    inspect_id = str(project_payload.get("巡检设置", {}).get("汇报任务ID", "")).strip()
    project_name = str(project_payload.get("项目名称", "")).strip()
    advance_name = f"内部访谈调研推进-{project_name}"
    inspect_name = f"内部访谈调研汇报-{project_name}"
    advance_job = None
    inspect_job = None
    for job in jobs:
        job_id = str(job.get("id", "")).strip()
        job_name = str(job.get("name", "")).strip()
        if advance_job is None and ((advance_id and job_id == advance_id) or job_name == advance_name):
            advance_job = job
        if inspect_job is None and ((inspect_id and job_id == inspect_id) or job_name == inspect_name):
            inspect_job = job
    return advance_job, inspect_job


def _是否worker推进prompt(message: str) -> bool:
    text = str(message or "").strip()
    return (
        "run-batch-worker" in text
        and "--status prepare" in text
        and "每次 exec 只允许一条命令" in text
        and "禁止使用 &&" in text
    )


def _是否inspect汇报prompt(message: str) -> bool:
    text = str(message or "").strip()
    return "inspect --project-dir" in text and "不要执行首轮外发" in text


def _诊断项目cron配置(project_payload: dict[str, Any], cron_jobs_path: Path | None = None) -> dict[str, Any]:
    if not bool(project_payload.get("巡检设置", {}).get("是否已注册")):
        return {"状态": "未注册", "问题": []}
    jobs = _读取cron任务列表(cron_jobs_path)
    if not jobs:
        return {"状态": "异常", "问题": ["cron 任务缺失：未找到 jobs.json 或任务列表为空"]}

    advance_job, inspect_job = _查找项目cron任务(project_payload, jobs)
    issues: list[str] = []
    expected_interval = int(
        project_payload.get("自动推进设置", {}).get("推进间隔分钟", 默认自动推进间隔分钟)
        or 默认自动推进间隔分钟
    )
    inspect_interval = int(
        project_payload.get("巡检设置", {}).get("巡检间隔分钟", expected_interval) or expected_interval
    )
    if inspect_interval != expected_interval:
        issues.append(
            f"cron 间隔配置漂移：巡检设置={inspect_interval} 分钟，但自动推进设置={expected_interval} 分钟"
        )
    expected_expr = _规范cron表达式(expected_interval)
    if advance_job is None:
        issues.append("cron 运行归属错误：未找到当前项目的推进任务")
    else:
        if str(advance_job.get("agentId", "")).strip() != "research":
            issues.append("cron 运行归属错误：推进任务 agentId 不是 research")
        if str(advance_job.get("schedule", {}).get("expr", "")).strip() != expected_expr:
            issues.append(
                f"cron 间隔配置漂移：推进任务 expr={str(advance_job.get('schedule', {}).get('expr', '')).strip() or '<empty>'}，期望 {expected_expr}"
            )
        if not _是否worker推进prompt(str(advance_job.get("payload", {}).get("message", ""))):
            issues.append("旧 prompt 未刷新：推进任务仍未使用 run-batch-worker --status prepare")
    if inspect_job is None:
        issues.append("cron 运行归属错误：未找到当前项目的汇报任务")
    else:
        if str(inspect_job.get("agentId", "")).strip() != "research":
            issues.append("cron 运行归属错误：汇报任务 agentId 不是 research")
        if str(inspect_job.get("schedule", {}).get("expr", "")).strip() != expected_expr:
            issues.append(
                f"cron 间隔配置漂移：汇报任务 expr={str(inspect_job.get('schedule', {}).get('expr', '')).strip() or '<empty>'}，期望 {expected_expr}"
            )
        if not _是否inspect汇报prompt(str(inspect_job.get("payload", {}).get("message", ""))):
            issues.append("旧 prompt 未刷新：汇报任务仍未使用 inspect 静默汇报模板")

    return {
        "状态": "正常" if not issues else "异常",
        "问题": issues,
        "推进任务agentId": str((advance_job or {}).get("agentId", "")).strip(),
        "汇报任务agentId": str((inspect_job or {}).get("agentId", "")).strip(),
        "期望cron表达式": expected_expr,
    }


def _后台worker命令(
    *,
    project_dir: Path,
    trigger: str,
    status: str,
    worker_run_id: str | None = None,
    cron_jobs_path: Path | None = None,
) -> str:
    manage_script = _管理脚本路径()
    command = (
        f"python3 {manage_script} run-batch-worker --project-dir '{project_dir}' "
        f"--trigger {trigger} --status {status}"
    )
    if worker_run_id:
        command += f" --worker-run-id '{worker_run_id}'"
    if cron_jobs_path is not None:
        command += f" --cron-jobs-path '{cron_jobs_path}'"
    return command


def _是否需要启动后台worker(advance_result: dict[str, Any]) -> bool:
    if not bool(advance_result.get("允许推进")):
        return False
    return any(
        bool(advance_result.get(key))
        for key in ("执行合同", "跟进行动", "自动解绑对象", "待补偿回写对象")
    )


def _构建后台worker合同(
    *,
    project_dir: Path,
    project_payload: dict[str, Any],
    trigger: str,
    advance_result: dict[str, Any],
    cron_jobs_path: Path | None = None,
) -> dict[str, Any]:
    settings = _自动推进设置(project_payload)
    should_start = not _后台worker活跃(project_payload) and _是否需要启动后台worker(advance_result)
    worker_type = _标准后台worker类型(trigger)
    worker_run_id = _生成后台worker运行ID() if should_start else ""
    return {
        "项目名称": project_payload.get("项目名称", ""),
        "状态": "后台仍在执行" if _后台worker活跃(project_payload) else ("待启动后台worker" if should_start else "无需启动后台worker"),
        "后台执行中": bool(settings.get("后台执行中")),
        "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
        "后台执行worker运行ID": str(settings.get("后台执行worker运行ID", "")).strip(),
        "后台执行worker会话Key": str(settings.get("后台执行worker会话Key", "")).strip(),
        "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
        "workerRunId": worker_run_id,
        "是否启动后台worker": should_start,
        "worker类型": worker_type,
        "sessionTarget": "isolated",
        "agentId": "research",
        "即时回复": "已转后台执行，本轮结束或遇阻塞后汇报",
        "启动命令": _后台worker命令(
            project_dir=project_dir,
            trigger=worker_type,
            status="started",
            worker_run_id=worker_run_id,
            cron_jobs_path=cron_jobs_path,
        ),
        "心跳命令": _后台worker命令(
            project_dir=project_dir,
            trigger=worker_type,
            status="heartbeat",
            worker_run_id=worker_run_id,
            cron_jobs_path=cron_jobs_path,
        ),
        "完成命令": _后台worker命令(
            project_dir=project_dir,
            trigger=worker_type,
            status="finished",
            worker_run_id=worker_run_id,
            cron_jobs_path=cron_jobs_path,
        ),
        "advance结果": advance_result,
    }


def build_manual_continue_worker_contract(
    project_dir: Path,
    trigger: str = "manual",
    now_at: str | None = None,
    config_path: Path = 默认配置文件路径,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
    cron_jobs_path: Path | None = None,
) -> dict[str, Any]:
    advance_result = advance_project(
        project_dir=project_dir,
        now_at=now_at,
        config_path=config_path,
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
        cron_jobs_path=cron_jobs_path,
    )
    project_payload, _ = _读取项目(project_dir)
    return _构建后台worker合同(
        project_dir=project_dir,
        project_payload=project_payload,
        trigger=trigger,
        advance_result=advance_result,
        cron_jobs_path=cron_jobs_path,
    )


def run_project_batch_worker(
    project_dir: Path,
    trigger: str = "manual",
    status: str = "prepare",
    worker_run_id: str | None = None,
    worker_session_key: str | None = None,
    summary: str | None = None,
    now_at: str | None = None,
    config_path: Path = 默认配置文件路径,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
    cron_jobs_path: Path | None = None,
) -> dict[str, Any]:
    normalized_status = str(status or "prepare").strip() or "prepare"
    project_payload, participants_payload = _读取项目(project_dir)
    if _规范后台worker展示状态(project_payload):
        _写回项目(project_dir, project_payload, participants_payload)
        project_payload, participants_payload = _读取项目(project_dir)
    participants = participants_payload.get("受访对象列表", [])
    settings = _自动推进设置(project_payload)
    worker_type = _标准后台worker类型(trigger)
    current_run_id = str(settings.get("后台执行worker运行ID", "")).strip()
    current_key = str(settings.get("后台执行worker会话Key", "")).strip()
    provided_run_id = str(worker_run_id or "").strip()
    now_text = _时间字符串(now_at) or _现在字符串()
    summary_text = str(summary or "").strip()
    stale_info = _后台worker过期信息(project_payload, now_at=now_at)
    if stale_info:
        _清理失活后台worker(
            project_dir,
            project_payload,
            participants_payload,
            code=str(stale_info.get("code", "")).strip(),
            detail=str(stale_info.get("detail", "")).strip(),
            now_at=now_at,
        )
        project_payload, participants_payload = _读取项目(project_dir)
        participants = participants_payload.get("受访对象列表", [])
        settings = _自动推进设置(project_payload)
        current_run_id = str(settings.get("后台执行worker运行ID", "")).strip()
        current_key = str(settings.get("后台执行worker会话Key", "")).strip()

    if normalized_status == "prepare":
        if _后台worker活跃(project_payload):
            return {
                "项目名称": project_payload.get("项目名称", ""),
                "状态": "后台仍在执行",
                "是否启动后台worker": False,
                "后台执行中": True,
                "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
                "后台执行worker运行ID": current_run_id,
                "后台执行worker会话Key": current_key,
                "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
            }
        advance_result = advance_project(
            project_dir=project_dir,
            now_at=now_at,
            config_path=config_path,
            requester_session_key=requester_session_key,
            requester_session_root=requester_session_root,
            cron_jobs_path=cron_jobs_path,
        )
        project_payload, _ = _读取项目(project_dir)
        return _构建后台worker合同(
            project_dir=project_dir,
            project_payload=project_payload,
            trigger=trigger,
            advance_result=advance_result,
            cron_jobs_path=cron_jobs_path,
        )

    if normalized_status == "started":
        if not provided_run_id:
            return {
                "项目名称": project_payload.get("项目名称", ""),
                "状态": "阻塞",
                "错误": 后台worker运行ID缺失错误,
                "说明": _后台worker前台摘要(后台worker运行ID缺失错误),
                "后台执行中": bool(settings.get("后台执行中")),
                "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
                "后台执行worker运行ID": current_run_id,
                "后台执行worker会话Key": current_key,
                "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
            }
        if _后台worker活跃(project_payload) and current_run_id and current_run_id != provided_run_id:
            return {
                "项目名称": project_payload.get("项目名称", ""),
                "状态": "阻塞",
                "错误": 后台worker运行ID不匹配错误,
                "说明": _后台worker前台摘要(后台worker运行ID不匹配错误),
                "是否启动后台worker": False,
                "后台执行中": True,
                "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
                "后台执行worker运行ID": current_run_id,
                "后台执行worker会话Key": current_key,
                "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
            }
        settings["后台执行中"] = True
        settings["后台执行worker类型"] = worker_type
        settings["后台执行worker运行ID"] = provided_run_id
        settings["后台执行worker会话Key"] = str(worker_session_key or current_key).strip()
        settings["后台执行最近诊断"] = ""
        if not str(settings.get("后台执行开始时间", "")).strip():
            settings["后台执行开始时间"] = now_text
        settings["后台执行最近心跳时间"] = now_text
        if summary_text:
            settings["后台执行最近摘要"] = summary_text
        _写回项目(project_dir, project_payload, participants_payload)

        advance_result = advance_project(
            project_dir=project_dir,
            now_at=now_at,
            config_path=config_path,
            requester_session_key=requester_session_key,
            requester_session_root=requester_session_root,
            cron_jobs_path=cron_jobs_path,
        )
        project_payload, participants_payload = _读取项目(project_dir)
        return {
            "项目名称": project_payload.get("项目名称", ""),
            "状态": "后台执行中",
            "后台执行中": True,
            "后台执行worker类型": str(_自动推进设置(project_payload).get("后台执行worker类型", "")).strip(),
            "后台执行worker运行ID": str(_自动推进设置(project_payload).get("后台执行worker运行ID", "")).strip(),
            "后台执行worker会话Key": str(_自动推进设置(project_payload).get("后台执行worker会话Key", "")).strip(),
            "后台执行最近摘要": str(_自动推进设置(project_payload).get("后台执行最近摘要", "")).strip(),
            "advance结果": advance_result,
            "当前批次是否与真实状态一致": _当前批次是否与真实状态一致(
                project_payload, participants_payload.get("受访对象列表", [])
            ),
        }

    if normalized_status == "heartbeat":
        if not provided_run_id:
            return {
                "项目名称": project_payload.get("项目名称", ""),
                "状态": "阻塞",
                "错误": 后台worker运行ID缺失错误,
                "说明": _后台worker前台摘要(后台worker运行ID缺失错误),
                "后台执行中": bool(settings.get("后台执行中")),
                "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
                "后台执行worker运行ID": current_run_id,
                "后台执行worker会话Key": current_key,
                "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
            }
        if not _后台worker活跃(project_payload) or current_run_id != provided_run_id:
            return {
                "项目名称": project_payload.get("项目名称", ""),
                "状态": "阻塞",
                "错误": 后台worker运行ID不匹配错误,
                "说明": _后台worker前台摘要(后台worker运行ID不匹配错误),
                "后台执行中": bool(settings.get("后台执行中")),
                "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
                "后台执行worker运行ID": current_run_id,
                "后台执行worker会话Key": current_key,
                "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
            }
        if worker_session_key:
            settings["后台执行worker会话Key"] = str(worker_session_key).strip()
        if not str(settings.get("后台执行worker类型", "")).strip():
            settings["后台执行worker类型"] = worker_type
        settings["后台执行最近心跳时间"] = now_text
        if summary_text:
            settings["后台执行最近摘要"] = summary_text
        _写回项目(project_dir, project_payload, participants_payload)
        return {
            "项目名称": project_payload.get("项目名称", ""),
            "状态": "后台心跳已更新",
            "后台执行中": bool(settings.get("后台执行中")),
            "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
            "后台执行worker运行ID": str(settings.get("后台执行worker运行ID", "")).strip(),
            "后台执行worker会话Key": str(settings.get("后台执行worker会话Key", "")).strip(),
            "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
        }

    if normalized_status == "finished":
        if not provided_run_id:
            return {
                "项目名称": project_payload.get("项目名称", ""),
                "状态": "阻塞",
                "错误": 后台worker运行ID缺失错误,
                "说明": _后台worker前台摘要(后台worker运行ID缺失错误),
                "后台执行中": bool(settings.get("后台执行中")),
                "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
                "后台执行worker运行ID": current_run_id,
                "后台执行worker会话Key": current_key,
                "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
            }
        if not _后台worker活跃(project_payload) or current_run_id != provided_run_id:
            return {
                "项目名称": project_payload.get("项目名称", ""),
                "状态": "阻塞",
                "错误": 后台worker运行ID不匹配错误,
                "说明": _后台worker前台摘要(后台worker运行ID不匹配错误),
                "后台执行中": bool(settings.get("后台执行中")),
                "后台执行worker类型": str(settings.get("后台执行worker类型", "")).strip(),
                "后台执行worker运行ID": current_run_id,
                "后台执行worker会话Key": current_key,
                "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
            }
        if summary_text:
            settings["后台执行最近摘要"] = summary_text
        settings["后台执行最近心跳时间"] = now_text
        settings["后台执行中"] = False
        settings["后台执行worker类型"] = ""
        settings["后台执行worker运行ID"] = ""
        settings["后台执行worker会话Key"] = ""
        settings["后台执行开始时间"] = ""
        settings["后台执行最近诊断"] = ""
        _同步当前批次信息(project_payload, participants)
        project_payload["下次自动推进时间"] = project_payload.get("巡检设置", {}).get("下次建议巡检时间", "")
        _写回项目(project_dir, project_payload, participants_payload)
        return {
            "项目名称": project_payload.get("项目名称", ""),
            "状态": "后台执行已结束",
            "后台执行中": False,
            "后台执行最近摘要": str(settings.get("后台执行最近摘要", "")).strip(),
            "当前批次是否与真实状态一致": _当前批次是否与真实状态一致(project_payload, participants),
            "当前批次状态": project_payload.get("当前批次状态", ""),
            "当前批次对象列表": project_payload.get("当前批次对象列表", []),
        }

    raise ValueError(f"不支持的 worker 状态：{normalized_status}")


def _更新项目派发状态(project_payload: dict[str, Any], participants: list[dict[str, Any]], mode: str) -> None:
    project_payload.setdefault("派发策略", {})
    project_payload["派发策略"]["派发模式"] = mode
    project_payload["派发策略"]["首轮交互形态"] = "文本选择题"
    project_payload["派发策略"]["单人同时待答问题数上限"] = 1
    project_payload["派发策略"]["单人有效问题上限"] = 4
    project_payload["当前活跃受访对象数"] = _统计当前活跃受访对象数(participants)


def _写入访谈记录(project_dir: Path, participant: dict[str, Any], lines: list[str]) -> Path:
    note_path = Path(participant.get("访谈记录路径") or project_dir / "访谈记录" / f"{participant.get('姓名', '')}.md")
    note_path.parent.mkdir(parents=True, exist_ok=True)
    existing = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
    block = "\n".join(line for line in lines if str(line).strip())
    if existing:
        content = existing.rstrip() + "\n\n" + block + "\n"
    else:
        content = f"# {participant.get('姓名', '')} 访谈记录\n\n" + block + "\n"
    note_path.write_text(content, encoding="utf-8")
    return note_path


def _收口结束提示() -> str:
    return "本次调研已完成。后续再发与该调研相关的补充不再纳入记录。当前私聊已切回 research 主对话。"


def _需要自动解绑已完成对象(participant: dict[str, Any]) -> bool:
    status = str(participant.get("当前状态", "")).strip()
    return status in {"已完成", "已完成待回写", "验收通过并清理", "全回收处理完成"} and _绑定已核验(participant)


def _写入完成回写记录(project_dir: Path, participant: dict[str, Any], finalized_at: str) -> Path:
    lines = [
        f"## 收口完成 {finalized_at}",
        f"- 当前状态：{participant.get('当前状态', '').strip() or '已完成'}",
        f"- 完成摘要：{str(participant.get('完成摘要', '')).strip() or '本轮访谈已达到收口条件。'}",
        f"- 收口方式：{str(participant.get('收口方式', '')).strip() or '达到默认收口条件'}",
        f"- 结束提示：{_收口结束提示()}",
    ]
    return _写入访谈记录(project_dir, participant, lines)


def _自动解绑已完成对象(project_dir: Path, participant: dict[str, Any], finalized_at: str | None = None) -> dict[str, Any]:
    if not _需要自动解绑已完成对象(participant):
        return {"已执行": False, "原因": "当前对象不满足自动解绑条件"}

    finished_at = _时间字符串(finalized_at) or participant.get("最近一次回收时间") or participant.get("最近回复时间") or _现在字符串()
    try:
        note_path = _写入完成回写记录(project_dir, participant, finished_at)
    except Exception as exc:
        participant["当前状态"] = "已完成待回写"
        participant["最近一次业务状态"] = "已完成待补偿回写"
        participant["最近一次链路状态"] = f"收口完成但回写失败：{exc}"
        participant["是否已回收至research"] = False
        return {
            "已执行": False,
            "原因": "回写失败",
            "错误": str(exc),
        }

    participant["访谈记录路径"] = str(note_path)
    participant["最近一次回收时间"] = finished_at
    participant["是否已回收至research"] = True
    participant["会话绑定状态"] = "已解绑"
    participant["会话绑定ID"] = ""
    participant["最近一次绑定检查结果"] = participant.get("最近一次绑定检查结果") or "已核验通过"
    participant["最近一次业务状态"] = "已完成并自动解绑"
    participant["最近一次链路状态"] = "收口完成，已切回 research 主对话"
    return {
        "已执行": True,
        "结束提示": _收口结束提示(),
        "完成时间": finished_at,
        "访谈记录路径": str(note_path),
    }


def _标准化短文本(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def _是否非调研流程消息(reply_text: str) -> bool:
    normalized = _标准化短文本(reply_text)
    if not normalized:
        return True
    if normalized.startswith("[inter-sessionmessage]") or "sourcesession=" in normalized:
        return True
    if "replytargetofcurrentusermessage" in normalized:
        return True
    if normalized in {"好", "好的", "收到", "ok", "okay", "嗯", "嗯嗯", "行", "知道了"}:
        return True
    return any(
        keyword in normalized
        for keyword in [
            "怎么没有反应",
            "问完问题之后会自动解绑",
            "会自动解绑吗",
            "自动解绑吗",
            "为什么没反应",
        ]
    )


def _识别访谈问题目标(assistant_text: str) -> str:
    normalized = _标准化短文本(assistant_text)
    if not normalized or normalized == "noreply":
        return ""
    if any(
        keyword in normalized
        for keyword in [
            "你现在更接近哪种情况",
            "请直接回复：经常用/用过几次/还没真正用/说不清",
            "请直接回复：已在使用/知道但少用/还没开始/说不清",
            "关于这次调研涉及的主题",
        ]
    ):
        return "是否使用过"
    if any(
        keyword in normalized
        for keyword in [
            "主要更接近哪种情况",
            "主要卡点",
            "上手或配置麻烦",
            "稳定性/速度有时不理想",
            "不太清楚哪些场景最该用它",
            "基本没明显卡点",
        ]
    ):
        return "主要使用场景或主要阻力"
    if any(
        keyword in normalized
        for keyword in [
            "如果只优先改一件事",
            "最希望先改哪类问题",
            "响应更快",
            "少报错、少失败",
            "结果更稳定一致",
            "操作链路更顺",
        ]
    ):
        return "培训期待或改进方向"
    return ""


def _从回复文本提取信号(reply_text: str) -> list[str]:
    normalized = _标准化短文本(reply_text)
    signals: list[str] = []
    if any(
        keyword in normalized
        for keyword in ["经常用", "每天都在用", "用过几次", "已在使用", "知道但少用", "还没开始", "还没真正用", "说不清"]
    ):
        signals.append("是否使用过")
    if any(
        keyword in normalized
        for keyword in ["问题", "卡点", "阻力", "上下文", "稳定性", "速度", "配置麻烦", "场景", "报错", "失败"]
    ):
        signals.append("主要使用场景或主要阻力")
    if any(
        keyword in normalized
        for keyword in ["希望", "建议", "优先", "培训", "改进", "想要", "先改"]
    ):
        signals.append("培训期待或改进方向")
    return _去重信号(signals)


def _生成补回摘要(valid_entries: list[dict[str, Any]]) -> str:
    snippets = [str(item.get("text", "")).strip() for item in valid_entries if str(item.get("text", "")).strip()]
    if not snippets:
        return ""
    return "；".join(snippets[:3])[:200]


def _扫描补回候选(
    participants: list[dict[str, Any]],
    gateway_log_path: Path,
    session_root: Path,
) -> dict[str, list[dict[str, Any]]]:
    participant_by_openid: dict[str, dict[str, Any]] = {}
    for participant in participants:
        feishu_target = _标准飞书目标(participant.get("飞书标识", ""))
        open_id = feishu_target.split(":", 1)[-1] if ":" in feishu_target else feishu_target
        if open_id:
            participant_by_openid[open_id] = participant

    candidate_openids: set[str] = set()
    if gateway_log_path.exists():
        for line in gateway_log_path.read_text(encoding="utf-8").splitlines():
            if "routed via bound conversation" not in line or "feishu[research]" not in line:
                continue
            match = re.search(r"bound conversation (ou_[a-zA-Z0-9]+)", line)
            if match and match.group(1) in participant_by_openid:
                candidate_openids.add(match.group(1))

    recovered: list[dict[str, Any]] = []
    metadata_only: list[dict[str, Any]] = []
    if not candidate_openids or not session_root.exists():
        return {"recovered": recovered, "metadata_only": metadata_only}

    for session_file in session_root.rglob("*.jsonl"):
        try:
            lines = session_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        current_openid = ""
        current_timestamp = ""
        last_assistant_text = ""
        pending_metadata: dict[str, Any] | None = None
        for raw_line in lines:
            try:
                entry = json.loads(raw_line)
            except Exception:
                continue
            if entry.get("customType") == "openclaw.runtime-context":
                if pending_metadata and pending_metadata.get("open_id") in candidate_openids:
                    participant = participant_by_openid.get(str(pending_metadata.get("open_id", "")).strip())
                    if participant:
                        metadata_only.append(
                            {
                                "open_id": pending_metadata["open_id"],
                                "participant": participant,
                                "timestamp": pending_metadata.get("timestamp", ""),
                                "session_file": str(session_file),
                                "assistant_text": last_assistant_text,
                            }
                        )
                content = str(entry.get("content", ""))
                match = re.search(r"Feishu\[research\].*\((ou_[a-zA-Z0-9]+)\)", content)
                if not match:
                    match = re.search(r'"sender_id"\s*:\s*"(ou_[a-zA-Z0-9]+)"', content)
                if match:
                    current_openid = match.group(1)
                ts_match = re.search(r"\[(\d{4}-\d{2}-\d{2} [^\]]+)\]", content)
                if ts_match:
                    current_timestamp = ts_match.group(1)
                pending_metadata = {
                    "open_id": current_openid,
                    "timestamp": current_timestamp,
                }
                continue
            role, message_text, message_timestamp = _提取会话消息(entry)
            if role == "assistant":
                if message_text and _标准化短文本(message_text) != "noreply":
                    last_assistant_text = message_text
                continue
            if role != "user" or current_openid not in candidate_openids:
                continue
            reply_text = message_text
            if not reply_text:
                continue
            participant = participant_by_openid.get(current_openid)
            if participant:
                recovered_at = _时间字符串(message_timestamp) or _时间字符串(current_timestamp) or (
                    _解析上下文展示时间(current_timestamp).isoformat() if _解析上下文展示时间(current_timestamp) else ""
                )
                recovered.append(
                    {
                        "open_id": current_openid,
                        "participant": participant,
                        "text": reply_text,
                        "timestamp": recovered_at,
                        "session_file": str(session_file),
                        "assistant_text": last_assistant_text,
                    }
                )
                pending_metadata = None
        if pending_metadata and pending_metadata.get("open_id") in candidate_openids:
            participant = participant_by_openid.get(str(pending_metadata.get("open_id", "")).strip())
            if participant:
                metadata_only.append(
                    {
                        "open_id": pending_metadata["open_id"],
                        "participant": participant,
                        "timestamp": pending_metadata.get("timestamp", ""),
                        "session_file": str(session_file),
                        "assistant_text": last_assistant_text,
                    }
                )
    return {"recovered": recovered, "metadata_only": metadata_only}


def _扫描网关回复路由(
    participants: list[dict[str, Any]],
    gateway_log_path: Path,
) -> dict[str, dict[str, str | bool]]:
    route_map: dict[str, dict[str, str | bool]] = {}
    for participant in participants:
        open_id = _提取飞书open_id(participant.get("飞书标识", ""))
        if not open_id:
            continue
        route_map[open_id] = {
            "bound": False,
            "boundSessionKey": "",
            "main": False,
        }
    if not gateway_log_path.exists():
        return route_map

    for line in gateway_log_path.read_text(encoding="utf-8").splitlines():
        bound_match = re.search(r"bound conversation (ou_[A-Za-z0-9_]+)(?: -> ([^,\s]+))?", line)
        if bound_match and bound_match.group(1) in route_map:
            route_map[bound_match.group(1)]["bound"] = True
            if bound_match.group(2):
                route_map[bound_match.group(1)]["boundSessionKey"] = bound_match.group(2)
            continue
        main_match = re.search(r"session=agent:research:feishu:direct:(ou_[A-Za-z0-9_]+)", line)
        if main_match and main_match.group(1) in route_map:
            route_map[main_match.group(1)]["main"] = True
    return route_map


def _扫描shared发送记录(
    participants: list[dict[str, Any]],
    session_root: Path,
) -> dict[str, dict[str, str]]:
    participant_by_openid: dict[str, dict[str, Any]] = {}
    for participant in participants:
        feishu_target = _标准飞书目标(participant.get("飞书标识", ""))
        open_id = feishu_target.split(":", 1)[-1] if ":" in feishu_target else feishu_target
        if open_id:
            participant_by_openid[open_id] = participant

    if not session_root.exists():
        return {}

    records: dict[str, dict[str, str]] = {}
    for session_file in session_root.rglob("*.jsonl"):
        try:
            lines = session_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        current_open_id = ""
        current_binding_id = ""
        bind_session_key = ""
        status_session_key = ""
        binding_confirmed_at = ""
        binding_evidence = ""
        binding_check_result = ""
        for raw_line in lines:
            try:
                entry = json.loads(raw_line)
            except Exception:
                continue
            if entry.get("type") != "message":
                continue
            message = entry.get("message", {})
            if not isinstance(message, dict):
                continue
            if message.get("role") != "toolResult":
                continue
            tool_name = message.get("toolName")
            details = message.get("details", {})
            if not isinstance(details, dict):
                continue
            if tool_name == "feishu_conversation_binding":
                action = str(details.get("action", "")).strip()
                open_id = str(details.get("conversationId", "")).strip()
                if open_id in participant_by_openid:
                    current_open_id = open_id
                    binding_record = details.get("绑定记录", {})
                    if isinstance(binding_record, dict):
                        target_session_key = str(binding_record.get("targetSessionKey", "")).strip()
                    else:
                        target_session_key = ""
                    if action == "bind":
                        current_binding_id = str(details.get("绑定ID", "")).strip()
                        bind_session_key = target_session_key
                        binding_check_result = "待status复核" if details.get("已绑定") else "绑定异常"
                    elif action == "status":
                        status_session_key = target_session_key
                        if details.get("已绑定") and bind_session_key and bind_session_key == status_session_key:
                            binding_confirmed_at = _时间字符串(str(entry.get("timestamp", "")).strip()) or _现在字符串()
                            binding_evidence = (
                                f"shared 会话绑定核验：conversationId={open_id}，"
                                f"targetSessionKey={status_session_key}，来源={session_file}"
                            )
                            binding_check_result = "已核验通过"
                        elif details.get("已绑定"):
                            binding_check_result = "目标会话不一致"
                continue
            if tool_name != "message" or current_open_id not in participant_by_openid:
                continue
            if details.get("ok") is not True:
                continue
            if binding_check_result != "已核验通过" or not status_session_key:
                continue
            message_id = str(details.get("messageId", "")).strip()
            chat_id = str(details.get("chatId", "")).strip()
            if not message_id or not chat_id:
                continue
            records[current_open_id] = {
                "messageId": message_id,
                "chatId": chat_id,
                "session_file": str(session_file),
                "executionSessionId": session_file.stem,
                "executionSessionKey": status_session_key,
                "helperSessionId": session_file.stem,
                "helperSessionKey": "",
                "bindingId": current_binding_id,
                "bindingStatus": "已绑定",
                "bindingConfirmedAt": binding_confirmed_at,
                "bindingEvidence": binding_evidence,
                "bindingTargetSessionKey": status_session_key,
                "bindingCheckResult": binding_check_result,
                "timestamp": _时间字符串(str(entry.get("timestamp", "")).strip()) or _现在字符串(),
            }
    return records


def _构建首轮提问工具参数(
    participant: dict[str, Any],
    card: dict[str, Any],
    send_account: str,
) -> dict[str, Any]:
    return {
        "accountId": send_account,
        "target": participant.get("飞书标识", ""),
        "questionStyle": "buttons",
        "questions": [
            {
                "question": card.get("question", ""),
                "header": "是否使用过",
                "options": [
                    {
                        "label": str(option.get("text", "")).strip(),
                        "description": f"选择“{str(option.get('text', '')).strip()}”",
                    }
                    for option in card.get("options", [])
                ],
                "multiSelect": False,
            }
        ],
    }


def _构建链路验收按钮题参数(
    target: str,
    send_account: str,
    question: str,
    header: str,
    option_labels: list[str],
) -> dict[str, Any]:
    return {
        "accountId": send_account,
        "target": target,
        "questionStyle": "buttons",
        "questions": [
            {
                "question": question,
                "header": header,
                "options": [
                    {
                        "label": label,
                        "description": f"点击“{label}”",
                    }
                    for label in option_labels
                ],
                "multiSelect": False,
            }
        ],
    }


def _校验严格shared投递工具参数(tool_args: dict[str, Any]) -> dict[str, Any]:
    session_key = str(tool_args.get("sessionKey", "")).strip()
    if not session_key:
        raise ValueError("strict shared 投递缺少 sessionKey，尚未真正投递。")
    if "message" not in tool_args or not str(tool_args.get("message", "")).strip():
        raise ValueError("strict shared 投递缺少 message，尚未真正投递。")

    if "label" in tool_args:
        raw_label = tool_args.get("label")
        normalized_label = str(raw_label or "").strip()
        if normalized_label in {"", "."}:
            raise ValueError(严格shared投递占位label文案)
        raise ValueError(严格shared投递参数冲突文案)

    sanitized: dict[str, Any] = {
        "sessionKey": session_key,
        "message": tool_args["message"],
    }
    if "timeoutSeconds" in tool_args and tool_args.get("timeoutSeconds") is not None:
        sanitized["timeoutSeconds"] = int(tool_args["timeoutSeconds"])
    return sanitized


def _构建严格shared投递工具参数(session_key: str, message: str, timeout_seconds: int = 180) -> dict[str, Any]:
    return _校验严格shared投递工具参数(
        {
            "sessionKey": session_key,
            "message": message,
            "timeoutSeconds": timeout_seconds,
        }
    )


def _链路验收会话提示词(project_dir: Path, project_payload: dict[str, Any], participant: dict[str, Any]) -> str:
    return (
        "你现在负责一次内部访谈链路验收，不做真实调研，只验证会话创建、飞书绑定、首轮消息发送、"
        "回复是否回到同一条 shared 会话，以及收到回复后能否继续发第二轮消息。"
        f"\n项目名称：{project_payload.get('项目名称', '')}"
        f"\n项目目录：{project_dir}"
        f"\n受访对象：{participant.get('姓名', '')}"
        f"\n受访对象飞书标识：{participant.get('飞书标识', '')}"
        "\n执行约束：按钮卡片优先；如果按钮卡片发送失败，允许改成短文本明确选项；单人有效问题上限 2，不创建 cron，不展开真实访谈内容。"
        "\n收口条件：完成两轮结构化触达后即可结束，并把结果回写项目文件。"
    )


def _构建单人链路验收计划(
    project_dir: Path,
    project_payload: dict[str, Any],
    participants: list[dict[str, Any]],
    participant: dict[str, Any],
    config_path: Path,
    expected_participant_count: int,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
    tool_reports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    tool_reports = tool_reports if tool_reports is not None else (_检查链路验收工具放行(config_path) if config_path.exists() else [])
    strict_shared_check = _检查严格shared投递配置(
        config_path=config_path,
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
    )
    missing_tools = [
        f"{report['代理']}: {tool}"
        for report in tool_reports
        for tool in report.get("缺少工具", [])
    ]
    blocked_reasons: list[str] = []
    if not participant.get("飞书标识"):
        blocked_reasons.append("受控测试对象缺少飞书标识")
    if not project_payload.get("项目截止时间"):
        blocked_reasons.append("当前项目缺少截止时间")
    if expected_participant_count == 1 and len(participants) != 1:
        blocked_reasons.append("链路验收项目必须保持单样本，只允许 1 位受访对象")
    if expected_participant_count == 2 and len(participants) != 2:
        blocked_reasons.append("双人并行链路验收项目必须保持 2 位受控测试对象")
    if project_payload.get("巡检设置", {}).get("是否已注册"):
        blocked_reasons.append("当前项目已注册巡检任务，链路验收不允许混入 cron")
    if not config_path.exists():
        blocked_reasons.append(f"找不到配置文件，无法验证工具放行：{config_path}")
    if _疑似临时空配置(config_path, tool_reports):
        blocked_reasons.append(f"传入的配置文件是临时空配置，不可用于验收：{config_path}")
    if missing_tools:
        blocked_reasons.append("工具放行不完整：" + "、".join(missing_tools))
    if not strict_shared_check.get("是否通过"):
        blocked_reasons.extend(strict_shared_check.get("阻止原因", []))

    target = participant.get("飞书标识", "")
    send_account = str(project_payload.get("访谈执行设置", {}).get("发送账号标识", "research")).strip() or "research"
    first_question = "你现在能正常看到这张测试卡片吗？"
    first_options = ["能看到", "看不到"]
    second_question = "收到，这里继续做第二步确认。现在这条链路是否仍然正常？"
    second_options = ["继续正常", "到此结束"]

    前置检查: dict[str, Any] = {
        "是否存在截止时间": bool(project_payload.get("项目截止时间")),
        "是否已注册巡检": bool(project_payload.get("巡检设置", {}).get("是否已注册")),
        "工具放行检查": tool_reports,
        "严格shared配置检查": strict_shared_check,
    }
    if expected_participant_count == 1:
        前置检查["是否单样本项目"] = len(participants) == 1
    elif expected_participant_count == 2:
        前置检查["是否双人项目"] = len(participants) == 2

    return {
        "项目名称": project_payload.get("项目名称", ""),
        "项目目录": str(project_dir),
        "实际检查配置路径": str(config_path),
        "受访对象": participant.get("姓名", ""),
        "受访对象飞书标识": target,
        "建议动作": (
            "开始链路验收"
            if not blocked_reasons
            else strict_shared_check.get("建议动作", "先补齐工具放行")
            if not missing_tools
            else "先补齐工具放行"
        ),
        "允许执行": len(blocked_reasons) == 0,
        "阻止原因": "；".join(blocked_reasons),
        "诊断状态": strict_shared_check.get("诊断状态", "通过") if blocked_reasons else "通过",
        "执行限制": {
            "是否允许注册cron": False,
            "回复时限分钟": 链路验收回复时限分钟,
            "单人有效问题上限": 2,
            "禁止测试对象类型": "真实调研员工",
            "是否允许文本降级冒充通过": False,
            "是否允许显式文本降级通过链路验收": True,
        },
        "通过标准": [
            "首轮触达只要能真实发出并让对方明确回复即可；优先按钮卡片，失败时允许短文本明确选项",
            "受控对象回复必须进入同一条执行会话Key 对应的专属 shared 会话",
            "同一条 shared 会话必须能继续发出第 2 轮结构化消息；可以是按钮卡片，也可以是短文本明确选项",
            "项目回写必须体现真实发送方式；如果是文本降级，就写成降级发送，不能伪装成按钮卡片成功",
        ],
        "前置检查": 前置检查,
        "严格shared配置检查": strict_shared_check,
        "会话创建": {
            "工具": "sessions_spawn",
            "目标代理": "research-shared",
            "最小上下文": {
                "项目名称": project_payload.get("项目名称", ""),
                "项目目录": str(project_dir),
                "受访对象": participant.get("姓名", ""),
                "受访对象飞书标识": target,
                "当前目标": "仅做链路验收，不做真实调研",
                "提问策略": "按钮卡片优先",
                "单人有效问题上限": 2,
                "收口条件": "完成两轮卡片即可结束",
            },
            "建议提示词": _链路验收会话提示词(project_dir, project_payload, participant),
        },
        "会话绑定": {
            "工具": "feishu_conversation_binding",
            "参数": {
                "action": "bind",
                "accountId": send_account,
                "target": target,
                "targetSessionKey": "<执行会话Key>",
                "agentId": "research-shared",
                "label": participant.get("姓名", ""),
                "boundBy": "research",
            },
            "校验参数": {
                "action": "status",
                "accountId": send_account,
                "target": target,
            },
        },
        "绑定核验": {
            "必须同时满足": [
                "同轮先拿到 feishu_conversation_binding(action=bind) 成功回执",
                "再立刻执行 feishu_conversation_binding(action=status) 复核同一 accountId + target",
                "status 返回的 绑定记录.targetSessionKey 必须与 <执行会话Key> 完全一致",
            ],
            "项目文件必须回写": [
                "最近一次绑定确认时间",
                "最近一次绑定确认依据",
                "最近一次绑定目标会话Key",
                "最近一次绑定检查结果=已核验通过",
            ],
        },
        "首轮触达": {
            "说明消息": "这是内部访谈链路验收测试，只需点一下，不涉及真实调研内容。",
            "工具": "feishu_ask_user_question",
            "验收通过要求": "真实触达成功（按钮卡片或短文本明确选项）",
            "是否允许文本降级计作通过": True,
            "工具参数": _构建链路验收按钮题参数(
                target=target,
                send_account=send_account,
                question=first_question,
                header="链路验收-第一轮",
                option_labels=first_options,
            ),
            "文本降级消息": _判断题文本降级消息(
                {
                    "question": first_question,
                    "options": [{"label": label} for label in first_options],
                }
            ),
            "发送后建议回写": {
                "当前状态": "待回复",
                "最近一次提问方式": "判断题",
                "最近一次卡片类型": "按钮卡片",
                "累计按钮题次数": int(participant.get("累计按钮题次数", 0) or 0) + 1,
                "累计有效问题数": int(participant.get("累计有效问题数", 0) or 0) + 1,
                "发送账号标识": send_account,
                "首条消息工具": "feishu_ask_user_question",
                "会话归属账号": send_account,
                "最近一次发送消息ID": "<messageId>",
                "最近一次卡片ID": "<questionId>",
            },
        },
        "回收验证": {
            "必须同时满足": [
                "sessions_history 或对应会话记录里，受控对象回复必须进入执行会话Key 对应的专属 shared 会话",
                "入站日志必须出现 bound conversation -> <执行会话Key> 这一类路由证据",
                "受访对象清单必须回写 最近一次卡片结果或最近一次消息结果 / 最近一次回收时间 / 是否已回收至research=true",
            ],
            "首次回复时间守卫": "任何 最近回复时间 < 最近发出时间 的消息，都只能记为首发前主对话消息，不能计作本轮 shared 回收",
            "失败判定": [
                "gateway 日志只出现 dispatching to agent (session=agent:research:feishu:direct:...)，判定为 回复仍落主对话",
                "shared transcript 没有真实入站消息时，不能补写成 shared 回收成功",
            ],
            "项目文件禁止出现": [
                "card.create code=200861",
                "V2 卡片不支持 action",
            ],
            "项目文件回写核对": [
                "最近一次卡片结果",
                "最近一次回收时间",
                "是否已回收至research",
            ],
            "回收后建议回写": {
                "当前状态": "访谈中",
                "最近回复时间": "<replyAt>",
                "最近一次卡片结果": "<按钮结果>",
                "最近一次回收时间": "<replyAt>",
                "是否已回收至research": True,
            },
        },
        "第二轮触达": {
            "工具": "feishu_ask_user_question",
            "工具参数": _构建链路验收按钮题参数(
                target=target,
                send_account=send_account,
                question=second_question,
                header="链路验收-第二轮",
                option_labels=second_options,
            ),
            "文本降级消息": _判断题文本降级消息(
                {
                    "question": second_question,
                    "options": [{"label": label} for label in second_options],
                }
            ),
        },
        "清理": {
            "解绑工具": "feishu_conversation_binding",
            "解绑参数": {
                "action": "unbind",
                "accountId": send_account,
                "target": target,
            },
            "项目文件处理": "把会话绑定状态改为已解绑，不创建也不保留 cron。",
            "清理后建议回写": {
                "会话绑定状态": "已解绑",
                "会话绑定ID": "",
                "是否已回收至research": True,
            },
        },
    }


def build_chain_acceptance_test_plan(
    project_dir: Path,
    participant_name: str,
    config_path: Path = 默认配置文件路径,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    participants = participants_payload.get("受访对象列表", [])
    participant = None
    for item in participants:
        if item.get("姓名") == participant_name:
            participant = _标准受访对象(item)
            break
    if participant is None:
        raise KeyError(f"未找到受访对象：{participant_name}")
    return _构建单人链路验收计划(
        project_dir=project_dir,
        project_payload=project_payload,
        participants=participants,
        participant=participant,
        config_path=config_path,
        expected_participant_count=1,
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
    )


def build_parallel_chain_acceptance_test_plan(
    project_dir: Path,
    participant_names: list[str],
    config_path: Path = 默认配置文件路径,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    participants = participants_payload.get("受访对象列表", [])
    selected_names = [str(name).strip() for name in participant_names if str(name).strip()]
    seen: set[str] = set()
    deduped_names: list[str] = []
    for name in selected_names:
        if name in seen:
            continue
        seen.add(name)
        deduped_names.append(name)

    selected_participants: list[dict[str, Any]] = []
    for name in deduped_names:
        matched = None
        for item in participants:
            if item.get("姓名") == name:
                matched = _标准受访对象(item)
                break
        if matched is None:
            raise KeyError(f"未找到受访对象：{name}")
        selected_participants.append(matched)

    tool_reports = _检查链路验收工具放行(config_path) if config_path.exists() else []
    strict_shared_check = _检查严格shared投递配置(
        config_path=config_path,
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
    )
    blocked_reasons: list[str] = []
    if len(deduped_names) != 2:
        blocked_reasons.append("双人并行链路验收必须且只允许指定 2 位受控测试对象")
    if len(participants) != 2:
        blocked_reasons.append("双人并行链路验收项目必须保持 2 位受控测试对象")
    if project_payload.get("巡检设置", {}).get("是否已注册"):
        blocked_reasons.append("当前项目已注册巡检任务，链路验收不允许混入 cron")
    if not project_payload.get("项目截止时间"):
        blocked_reasons.append("当前项目缺少截止时间")
    if not config_path.exists():
        blocked_reasons.append(f"找不到配置文件，无法验证工具放行：{config_path}")
    if _疑似临时空配置(config_path, tool_reports):
        blocked_reasons.append(f"传入的配置文件是临时空配置，不可用于验收：{config_path}")
    missing_tools = [
        f"{report['代理']}: {tool}"
        for report in tool_reports
        for tool in report.get("缺少工具", [])
    ]
    if missing_tools:
        blocked_reasons.append("工具放行不完整：" + "、".join(missing_tools))
    if not strict_shared_check.get("是否通过"):
        blocked_reasons.extend(strict_shared_check.get("阻止原因", []))

    participant_plans = [
        _构建单人链路验收计划(
            project_dir=project_dir,
            project_payload=project_payload,
            participants=participants,
            participant=participant,
            config_path=config_path,
            expected_participant_count=2,
            requester_session_key=requester_session_key,
            requester_session_root=requester_session_root,
            tool_reports=tool_reports,
        )
        for participant in selected_participants
    ]

    unique_blocked_reasons = list(dict.fromkeys(blocked_reasons + [item["阻止原因"] for item in participant_plans if item.get("阻止原因")]))

    return {
        "项目名称": project_payload.get("项目名称", ""),
        "项目目录": str(project_dir),
        "实际检查配置路径": str(config_path),
        "受访对象列表": deduped_names,
        "建议动作": (
            "开始双人并行链路验收"
            if not unique_blocked_reasons
            else strict_shared_check.get("建议动作", "先补齐工具放行")
            if not missing_tools
            else "先补齐工具放行"
        ),
        "允许执行": len(unique_blocked_reasons) == 0 and len(participant_plans) == 2,
        "阻止原因": "；".join([reason for reason in unique_blocked_reasons if reason]),
        "诊断状态": strict_shared_check.get("诊断状态", "通过") if unique_blocked_reasons else "通过",
        "执行限制": {
            "是否允许注册cron": False,
            "回复时限分钟": 链路验收回复时限分钟,
            "单人有效问题上限": 2,
            "禁止测试对象类型": "真实调研员工",
            "是否允许文本降级冒充通过": False,
            "是否允许显式文本降级通过链路验收": True,
            "并行对象数": 2,
        },
        "通过标准": [
            "两位受控对象都要有独立的执行会话ID 和执行会话Key",
            "两位受控对象的回复都必须进入各自同一条专属 shared 会话，互不串会话",
            "两位受控对象的回写都必须落到各自名下，互不串项目记录",
            "两位受控对象在收到首轮回复后，都必须能从对应 shared 会话继续发出第 2 轮结构化消息",
            "清理阶段必须把两位受访对象都解绑，并把项目阶段改为验收清理完成",
        ],
        "前置检查": {
            "是否双人项目": len(participants) == 2,
            "是否存在截止时间": bool(project_payload.get("项目截止时间")),
            "是否已注册巡检": bool(project_payload.get("巡检设置", {}).get("是否已注册")),
            "工具放行检查": tool_reports,
            "严格shared配置检查": strict_shared_check,
        },
        "对象计划列表": participant_plans,
        "清理": {
            "项目文件处理": "两位受访对象都要解绑，并把项目阶段改为验收清理完成，不创建也不保留 cron。",
        },
    }


def build_participant_outreach_plan(
    project_dir: Path,
    participant_name: str,
    research_account_ready: bool = True,
    card_supported: bool = True,
    config_path: Path = 默认配置文件路径,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
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
    question_limit = _单人有效问题上限(project_payload=project_payload, participant=participant)
    strict_shared_check = _检查严格shared投递配置(
        config_path=config_path,
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
    )
    has_valid_target = bool(_提取飞书open_id(participant.get("飞书标识", "")))
    can_create_live_shared_now = bool(
        research_account_ready
        and project_payload.get("项目截止时间")
        and has_valid_target
        and not _是否达到收口条件(participant, question_limit=question_limit)
        and strict_shared_check.get("是否通过")
    )

    base_plan = {
        "项目名称": project_payload.get("项目名称", ""),
        "受访对象": participant.get("姓名", ""),
        "发送账号标识": execution_settings.get("发送账号标识", "research"),
        "禁止工具": ["feishu_im_user_message"],
        "已达到收口条件": _是否达到收口条件(participant, question_limit=question_limit),
        "执行通道真值类型": participant.get("执行通道真值类型", "direct-shared"),
        "执行会话代理": participant.get("执行会话代理", "research-shared"),
        "执行会话ID": participant.get("执行会话ID", ""),
        "执行会话Key": participant.get("执行会话Key", ""),
        "辅助执行会话ID": participant.get("辅助执行会话ID", ""),
        "辅助执行会话Key": participant.get("辅助执行会话Key", ""),
        "会话绑定状态": participant.get("会话绑定状态", "未绑定"),
        "会话绑定ID": participant.get("会话绑定ID", ""),
        "最近一次绑定确认时间": participant.get("最近一次绑定确认时间", ""),
        "最近一次绑定目标会话Key": participant.get("最近一次绑定目标会话Key", ""),
        "最近一次绑定检查结果": participant.get("最近一次绑定检查结果", ""),
        "最近一次发送确认状态": participant.get("最近一次发送确认状态", ""),
        "严格shared配置检查": strict_shared_check,
        "诊断状态": strict_shared_check.get("诊断状态", "通过"),
        "禁止预建待命会话": True,
        "是否允许立即创建live shared": can_create_live_shared_now,
        "是否允许立即首发": False,
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
    if not _提取飞书open_id(participant.get("飞书标识", "")):
        return {
            **base_plan,
            "允许发送": False,
            "建议动作": "先修复受访对象名单",
            "阻止原因": "受访对象飞书标识不合法，必须先修正为 user:ou_xxx 后才能继续。",
        }
    if _是否达到收口条件(participant, question_limit=question_limit):
        return {
            **base_plan,
            "允许发送": True,
            "是否允许立即首发": True,
            "建议动作": "直接收口",
            "收口说明": participant.get("收口原因") or "已拿到足够信号，不要继续追问。",
            "收口消息": "谢谢，信息已经足够了。我先整理这轮结论，后面如有必要再补充联系你。",
        }
    if not participant.get("执行会话Key") or not _绑定已核验(participant):
        return {
            **base_plan,
            "允许发送": False,
            "建议动作": "先创建并核验 fixed direct shared 绑定",
            "阻止原因": "当前受访对象还没有完成固定 direct shared 通道绑定核验，禁止直接外发。",
        }
    if not strict_shared_check.get("是否通过"):
        return {
            **base_plan,
            "允许发送": False,
            "建议动作": strict_shared_check.get("建议动作", "先打通 shared 会话投递权限"),
            "阻止原因": "；".join(strict_shared_check.get("阻止原因", [])),
        }

    intro = _首轮说明消息(project_payload, participant)
    first_touch_question = _首轮文本选择题(project_payload, participant)
    tool_name = "sessions_send"
    full_text_message = _首轮完整文本消息(project_payload, participant, first_touch_question)
    shared_protocol_message = _构建shared首轮投递消息(
        project_dir=project_dir,
        project_payload=project_payload,
        participant=participant,
        send_account=base_plan["发送账号标识"],
        question=first_touch_question,
    )
    strict_protocol_payload = _extract_shared_protocol_payload(shared_protocol_message)
    strict_send_tool_args = _构建严格shared投递工具参数(
        session_key=str(participant.get("执行会话Key", "")).strip(),
        message=shared_protocol_message,
        timeout_seconds=180,
    )

    return {
        **base_plan,
        "允许发送": True,
        "是否允许立即首发": True,
        "建议动作": "发起首次邀约" if participant.get("当前状态") == "待联系" else "继续轻量跟进",
        "运行模式": project_payload.get("运行模式", "真实调研"),
        "说明消息": intro,
        "后续规则": {
            "默认提问方式": strategy.get("默认提问方式", "判断题优先"),
            "默认交互形态": strategy.get("默认交互形态", "文本选择题"),
            "开放问答最晚触发条件": strategy.get("开放问答最晚触发条件", ""),
            "单人有效问题上限": strategy.get("单人有效问题上限", 4),
            "单轮最多追问": strategy.get("单轮最多追问", 1),
        },
        "首轮触达": {
            "提问方式": "选择题",
            "交互形态": "文本选项",
            "信息目标": "是否使用过",
            "工具": tool_name,
            "是否降级发送": False,
            "记录口径": "文本选择题",
            "工具参数": strict_send_tool_args,
            "唯一执行参数真值": "首轮触达.工具参数",
            "执行期失败口径": {
                "工具层参数冲突": 严格shared投递参数冲突文案,
                "shared 会话不可达": 严格shared会话不可达文案,
                "shared 协议不完整": 严格shared协议不完整文案,
            },
            "严格协议载荷": strict_protocol_payload,
            "禁止手写临时消息": True,
            "共享会话消息工具": "message",
            "共享会话消息参数": {
                "action": "send",
                "channel": "feishu",
                "accountId": base_plan["发送账号标识"],
                "target": participant.get("飞书标识", ""),
                "message": full_text_message,
            },
            "消息内容": full_text_message,
            "固定选项": first_touch_question["options"],
        },
        "发送后核验": {
            "状态分层": [
                "research 侧 sessions_send 成功，不等于已经外发成功",
                "只有 shared 会话里真实 message 返回 ok=true + messageId + chatId，才能记为 已确认回执",
                "只有消息由该专属 shared 会话真实发出且绑定已生效，才能记为 已形成可回收 shared 会话",
            ],
            "核验必须使用": ["shared 会话 message 返回的 messageId", "shared 会话 message 返回的 chatId"],
            "禁止核验方式": ["feishu_im_user_get_messages(open_id=...)", "research 直发 message 兜底"],
            "共享会话必须返回字段": ["ok", "messageId", "chatId", "sendTime"],
            "发送后必须回写": [
                "最近一次发送消息ID",
                "最近一次发送chatID",
                "最近一次发送确认状态",
                "最近一次发送确认时间",
                "最近一次发送确认依据",
            ],
        },
    }


def build_dispatch_plan(
    project_dir: Path,
    batch_size: int | None = None,
    batch_interval_minutes: int = 10,
    config_path: Path = 默认配置文件路径,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    participants = participants_payload.get("受访对象列表", [])
    candidates = _派发候选对象(participants)
    blocked = _派发阻塞对象(candidates, session_root=默认shared会话目录)
    strict_shared_check = _检查严格shared投递配置(
        config_path=config_path,
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
    )
    if candidates and not strict_shared_check.get("是否通过"):
        blocked.extend(
            {
                "姓名": item.get("姓名", ""),
                "原因": "；".join(strict_shared_check.get("阻止原因", [])),
            }
            for item in candidates
        )
    dispatchable = [
        item
        for item in candidates
        if _绑定已核验(item)
        and item.get("执行会话Key")
        and item.get("执行会话ID")
        and strict_shared_check.get("是否通过")
        and not _是否非法预建shared(item, protocol_check=_检查shared协议状态(item))
    ]
    allow_create_live_shared_now = bool(candidates) and bool(strict_shared_check.get("是否通过")) and not blocked
    allow_first_touch_now = bool(dispatchable) and not blocked

    if batch_size is None:
        _更新项目派发状态(project_payload, participants, "一次性全发")
        project_payload["派发批次记录"] = []
        if dispatchable:
            project_payload["批次状态"] = "待首发"
        elif blocked:
            project_payload["批次状态"] = "待就绪"
        else:
            project_payload["批次状态"] = "无待首发对象"
        _写回项目(project_dir, project_payload, participants_payload)
        return {
            "项目名称": project_payload.get("项目名称", ""),
            "运行模式": project_payload.get("运行模式", "真实调研"),
            "派发模式": "一次性全发",
            "首轮发送人数": len(dispatchable),
            "禁止预建待命会话": True,
            "是否允许立即创建live shared": allow_create_live_shared_now,
            "是否允许立即首发": allow_first_touch_now,
            "首轮对象列表": [
                {
                    "姓名": item.get("姓名", ""),
                    "飞书标识": item.get("飞书标识", ""),
                    "执行会话Key": item.get("执行会话Key", ""),
                    "是否允许立即创建live shared": True,
                    "是否允许立即首发": True,
                }
                for item in dispatchable
            ],
            "批次数": 0,
            "每批人数": 0,
            "批间隔分钟": 0,
            "阻塞人数": len(blocked),
            "阻塞对象": blocked,
            "批次列表": [],
        }

    batches: list[dict[str, Any]] = []
    for index in range(0, len(dispatchable), batch_size):
        batch_members = dispatchable[index : index + batch_size]
        batches.append(
            {
                "批次序号": len(batches) + 1,
                "计划发送人数": len(batch_members),
                "建议发送时间偏移分钟": len(batches) * batch_interval_minutes,
                "状态": "待发送",
                "成员": [
                    {
                        "姓名": item.get("姓名", ""),
                        "飞书标识": item.get("飞书标识", ""),
                        "执行会话Key": item.get("执行会话Key", ""),
                    }
                    for item in batch_members
                ],
            }
        )

    _更新项目派发状态(project_payload, participants, "分批限流")
    project_payload["派发策略"]["每批人数"] = batch_size
    project_payload["派发策略"]["批间隔分钟"] = batch_interval_minutes
    project_payload["派发批次记录"] = batches
    project_payload["批次状态"] = "已生成" if batches else ("待就绪" if blocked else "无待首发对象")
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "项目名称": project_payload.get("项目名称", ""),
        "运行模式": project_payload.get("运行模式", "真实调研"),
        "派发模式": "分批限流",
        "禁止预建待命会话": True,
        "是否允许立即创建live shared": allow_create_live_shared_now,
        "是否允许立即首发": allow_first_touch_now,
        "批次数": len(batches),
        "每批人数": batch_size,
        "批间隔分钟": batch_interval_minutes,
        "可派发人数": len(dispatchable),
        "阻塞人数": len(blocked),
        "阻塞对象": blocked,
        "批次列表": batches,
    }


def advance_project(
    project_dir: Path,
    now_at: str | None = None,
    config_path: Path = 默认配置文件路径,
    requester_session_key: str | None = None,
    requester_session_root: Path = 默认research会话目录,
    cron_jobs_path: Path | None = None,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    now = _解析时间(now_at) if now_at else _现在()
    if now is None:
        now = _现在()
    if project_payload.get("停止信息", {}).get("是否已停止"):
        return {"允许推进": False, "执行状态": "已停止", "阻塞人数": 0, "阻塞对象": []}
    if _是否项目已冻结(project_payload):
        return {"允许推进": False, "执行状态": "已冻结", "阻塞人数": 0, "阻塞对象": []}
    if not project_payload.get("项目截止时间"):
        return {"允许推进": False, "执行状态": "缺少截止时间", "阻塞人数": 0, "阻塞对象": []}

    participants = participants_payload.get("受访对象列表", [])
    rewound_waiting = _回退发送确认不足对象(participants)

    auto_unbound: list[str] = []
    pending_writeback: list[str] = []
    for participant in participants:
        if not _需要自动解绑已完成对象(participant):
            continue
        result = _自动解绑已完成对象(
            project_dir=project_dir,
            participant=participant,
            finalized_at=participant.get("最近一次回收时间") or participant.get("最近回复时间") or now.isoformat(),
        )
        if result.get("已执行"):
            auto_unbound.append(str(participant.get("姓名", "")).strip())
        else:
            pending_writeback.append(str(participant.get("姓名", "")).strip())
    if rewound_waiting or auto_unbound or pending_writeback:
        _写回项目(project_dir, project_payload, participants_payload)

    strict_shared_check = _检查严格shared投递配置(
        config_path=config_path,
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
    )

    batch_size = int(project_payload.get("派发策略", {}).get("每批人数", 10) or 10)
    batch_interval = int(project_payload.get("派发策略", {}).get("批间隔分钟", 10) or 10)
    dispatch_plan = build_dispatch_plan(
        project_dir=project_dir,
        batch_size=batch_size,
        batch_interval_minutes=batch_interval,
        config_path=config_path,
        requester_session_key=requester_session_key,
        requester_session_root=requester_session_root,
    )
    _同步当前批次信息(project_payload, participants, dispatch_plan=dispatch_plan)

    auto_register_result = {
        "已创建": False,
        "推进任务ID": str(project_payload.get("巡检设置", {}).get("推进任务ID", "")).strip(),
        "汇报任务ID": str(project_payload.get("巡检设置", {}).get("汇报任务ID", "")).strip(),
    }
    if (
        cron_jobs_path is not None
        and not bool(project_payload.get("巡检设置", {}).get("是否已注册"))
        and _需要自动注册推进任务(project_payload, participants)
    ):
        register_result = register_project_check_job(
            project_dir=project_dir,
            cron_jobs_path=cron_jobs_path,
            interval_minutes=int(
                project_payload.get("自动推进设置", {}).get("推进间隔分钟", 默认自动推进间隔分钟)
                or 默认自动推进间隔分钟
            ),
            report_mode=str(project_payload.get("自动推进设置", {}).get("汇报模式", "every-round")).strip() or "every-round",
            auto_created=True,
        )
        project_payload, participants_payload = _读取项目(project_dir)
        participants = participants_payload.get("受访对象列表", [])
        auto_register_result = {
            "已创建": True,
            "推进任务ID": register_result["推进任务"]["任务ID"],
            "汇报任务ID": register_result["汇报任务"]["任务ID"],
        }

    blocked = list(dispatch_plan.get("阻塞对象", []))
    if dispatch_plan.get("首轮对象列表"):
        current_batch_names = [str(item.get("姓名", "")).strip() for item in dispatch_plan.get("首轮对象列表", [])]
    else:
        first_batch = (dispatch_plan.get("批次列表") or [{}])[0]
        current_batch_names = [str(item.get("姓名", "")).strip() for item in first_batch.get("成员", [])]
    _同步当前批次信息(project_payload, participants, dispatch_plan=dispatch_plan)

    followup_actions: list[dict[str, str]] = []
    for action in evaluate_project_actions(project_dir=project_dir, now_at=now.isoformat()).get("受访对象动作", []):
        action_name = str(action.get("建议动作", "")).strip()
        if action_name in {"第一次跟进", "第二次跟进", "最终截止提醒", "到期封口", "刷新分析", "执行自动解绑", "补偿回写后解绑"}:
            followup_actions.append(action)

    execution_contract = [_构建首轮执行合同(project_dir=project_dir, participant=participant) for participant in participants if str(participant.get("姓名", "")).strip() in current_batch_names]
    execution_contract.extend(_构建跟进行动合同(project_dir=project_dir, action=action) for action in followup_actions)

    execution_status = "待执行当前批次"
    if blocked and not execution_contract:
        execution_status = "已阻止"
    elif not execution_contract and not followup_actions:
        execution_status = "无待推进动作"
    elif pending_writeback or auto_unbound:
        execution_status = "已补偿完成对象收尾"

    summary = _构建推进摘要(
        status=execution_status,
        now=now,
        current_batch=current_batch_names,
        blocked=blocked,
        rewound=rewound_waiting,
        auto_unbound=auto_unbound,
        followups=followup_actions,
    )
    project_payload["上次推进结果摘要"] = summary
    project_payload["自动推进设置"]["是否自动注册"] = bool(project_payload.get("巡检设置", {}).get("是否已注册"))
    project_payload["下次自动推进时间"] = project_payload.get("巡检设置", {}).get("下次建议巡检时间", "")
    _写回项目(project_dir, project_payload, participants_payload)

    if blocked and not execution_contract:
        return {
            "允许推进": False,
            "执行状态": execution_status,
            "阻塞人数": len(blocked),
            "阻塞对象": blocked,
            "发送确认回退人数": len(rewound_waiting),
            "自动解绑对象": auto_unbound,
            "待补偿回写对象": pending_writeback,
            "自动注册结果": auto_register_result,
            "当前批次状态": project_payload.get("当前批次状态", ""),
            "当前批次对象列表": project_payload.get("当前批次对象列表", []),
            "本轮汇报摘要": summary,
        }

    return {
        "允许推进": True,
        "执行状态": execution_status,
        "发送确认回退人数": len(rewound_waiting),
        "发送确认回退对象": rewound_waiting,
        "自动解绑对象": auto_unbound,
        "待补偿回写对象": pending_writeback,
        "当前批次序号": project_payload.get("当前批次序号", 0),
        "当前批次状态": project_payload.get("当前批次状态", ""),
        "当前批次对象列表": project_payload.get("当前批次对象列表", []),
        "执行合同": execution_contract,
        "跟进行动": followup_actions,
        "严格shared检查": strict_shared_check,
        "自动注册结果": auto_register_result,
        "本轮汇报摘要": summary,
        "本轮新创建会话人数": 0,
        "本轮新绑定人数": 0,
        "本轮真实发出人数": 0,
        "本轮完成跟进人数": len(followup_actions),
        "本轮阻塞对象": blocked,
    }


def _构建分析摘要(project_payload: dict[str, Any], participants: list[dict[str, Any]], grouped: bool = False) -> dict[str, Any]:
    effective_participants = [item for item in participants if _是否计入有效样本(item)]
    summary = _统计样本(participants)
    signal_counter = Counter(
        signal
        for participant in effective_participants
        for signal in participant.get("已收集信号", [])
        if str(signal).strip()
    )
    completed_summaries = [
        f"- {participant.get('姓名', '')}：{participant.get('完成摘要', '').strip() or '已回收有效信息'}"
        for participant in effective_participants
    ]
    high_frequency = [
        f"- {signal}：{count} 人提及"
        for signal, count in signal_counter.most_common()
    ] or ["- 暂未形成可统计的高频信号"]
    risks = []
    if summary["待回复人数"] > 0 or summary["已超时人数"] > 0 or summary["已停滞人数"] > 0:
        risks.append(
            f"- 当前仍有 {summary['待回复人数'] + summary['已超时人数'] + summary['已停滞人数']} 位对象未完全收口，结论需结合样本缺口理解。"
        )
    if not grouped:
        risks.append("- 当前按整体样本汇总，未启用部门或角色分组。")

    suggestions = [
        f"- 优先围绕已回收的 {len(effective_participants)} 份有效样本输出阶段结论。",
        "- 对仍未回复或停滞的对象，只补最关键的一问，不再展开长追问。",
    ]
    if summary["已超时人数"] > 0:
        suggestions.append("- 在最终报告发送前，如收到超时后补回的回复，立即刷新分析和交付草案。")

    gap_count = summary["待联系人数"] + summary["待回复人数"] + summary["已停滞人数"] + summary["已超时人数"]
    if gap_count > 0:
        gap_text = f"仍有 {gap_count} 位受访对象未完全收口，结论基于当前已回收样本输出。"
    else:
        gap_text = "所有受访对象已完成、已拒绝或已完成冻结后的记录处理。"

    return {
        "样本统计": summary,
        "有效样本数": len(effective_participants),
        "样本缺口说明": gap_text,
        "核心发现": completed_summaries or ["- 暂无已回收样本，当前只能输出空白框架。"],
        "高频问题": high_frequency,
        "期待与建议": suggestions,
        "风险与反例": risks or ["- 暂无额外风险说明。"],
    }


def analyze_project(
    project_dir: Path,
    now_at: str | None = None,
    group_by_org_info: bool = False,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    now = _解析时间(now_at) if now_at else _现在()
    if now is None:
        now = _现在()
    participants = participants_payload.get("受访对象列表", [])
    analysis = _构建分析摘要(project_payload, participants, grouped=group_by_org_info)
    summary = analysis["样本统计"]

    report = (
        f"# {project_payload['项目名称']} 最终调研报告\n\n"
        "## 一、调研目标\n\n"
        f"- {project_payload['调研目标']}\n\n"
        "## 二、样本覆盖\n\n"
        f"- 总人数：{summary['总人数']}\n"
        f"- 有效样本：{analysis['有效样本数']}\n"
        f"- 已完成：{summary['已完成人数']}\n"
        f"- 访谈中：{summary['访谈中人数']}\n"
        f"- 待回复：{summary['待回复人数']}\n"
        f"- 已超时：{summary['已超时人数']}\n"
        f"- 已拒绝：{summary['已拒绝人数']}\n\n"
        "## 三、核心发现\n\n"
        + "\n".join(analysis["核心发现"])
        + "\n\n## 四、高频问题/阻力\n\n"
        + "\n".join(analysis["高频问题"])
        + "\n\n## 五、期待与建议\n\n"
        + "\n".join(analysis["期待与建议"])
        + "\n\n## 六、样本缺口与风险\n\n"
        + f"- {analysis['样本缺口说明']}\n"
        + ("\n".join(analysis["风险与反例"]) if analysis["风险与反例"] else "")
        + "\n\n## 七、建议动作\n\n"
        + "\n".join(analysis["期待与建议"])
        + "\n"
    )
    stage_summary = (
        f"# {project_payload['项目名称']} 阶段总结\n\n"
        f"## 当前阶段\n\n- {project_payload.get('当前阶段', '分析总结')}\n\n"
        "## 关键进展\n\n"
        f"- 已形成 {analysis['有效样本数']} 份有效样本分析。\n\n"
        "## 风险与缺口\n\n"
        f"- {analysis['样本缺口说明']}\n\n"
        "## 下一步动作\n\n"
        + "\n".join(analysis["期待与建议"])
        + "\n"
    )

    project_payload["当前阶段"] = "分析总结"
    if project_payload.get("项目状态") != "已停止":
        project_payload["项目状态"] = "待交付"
    project_payload["分析收口"]["样本缺口说明"] = analysis["样本缺口说明"]
    project_payload["分析收口"]["最新分析时间"] = now.isoformat()
    _写入文本(project_dir / "最终调研报告.md", report)
    _写入文本(project_dir / "阶段总结.md", stage_summary)
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "项目名称": project_payload.get("项目名称", ""),
        "有效样本数": analysis["有效样本数"],
        "样本缺口说明": analysis["样本缺口说明"],
        "是否启用分组": group_by_org_info,
        "分析时间": now.isoformat(),
    }


def mark_delivery_complete(
    project_dir: Path,
    delivered_at: str | None = None,
    doc_url: str | None = None,
    summary_message_id: str | None = None,
    cron_jobs_path: Path | None = None,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    delivered = _解析时间(delivered_at) if delivered_at else _现在()
    if delivered is None:
        delivered = _现在()

    auto_unbound_count = 0
    pending_writeback_count = 0
    for participant in participants_payload.get("受访对象列表", []):
        if not _需要自动解绑已完成对象(participant):
            continue
        result = _自动解绑已完成对象(project_dir=project_dir, participant=participant, finalized_at=delivered.isoformat())
        if result.get("已执行"):
            auto_unbound_count += 1
        else:
            pending_writeback_count += 1

    final_info = project_payload.setdefault("最终交付信息", {})
    final_info["是否已发送最终报告"] = True
    final_info["最终报告发送时间"] = delivered.isoformat()
    freeze_hours = int(final_info.get("冻结观察期小时", 48) or 48)
    final_info["冻结观察截止时间"] = (delivered + timedelta(hours=freeze_hours)).isoformat()
    final_info["冻结版本号"] = int(final_info.get("冻结版本号", 0) or 0) + 1
    final_info["最近交付时间"] = delivered.isoformat()
    final_info["摘要消息状态"] = "已发送"
    if doc_url is not None:
        final_info["最终文档链接"] = doc_url
    if summary_message_id is not None:
        final_info["摘要消息ID"] = summary_message_id

    if project_payload.get("项目状态") != "已停止":
        project_payload["项目状态"] = "已交付"
    removed_jobs = 0
    if cron_jobs_path is not None and cron_jobs_path.exists():
        cron_payload = _读取结构化文件(cron_jobs_path) or {"version": 1, "jobs": []}
        jobs = cron_payload.get("jobs", [])
        tracked_ids = {
            str(project_payload.get("巡检设置", {}).get("巡检任务ID", "")).strip(),
            str(project_payload.get("巡检设置", {}).get("推进任务ID", "")).strip(),
            str(project_payload.get("巡检设置", {}).get("汇报任务ID", "")).strip(),
        }
        tracked_ids.discard("")
        tracked_names = {
            f"内部访谈调研推进-{project_payload.get('项目名称', '')}",
            f"内部访谈调研汇报-{project_payload.get('项目名称', '')}",
            f"内部访谈调研巡检-{project_payload.get('项目名称', '')}",
        }
        kept_jobs = []
        for job in jobs:
            if job.get("id") in tracked_ids or job.get("name") in tracked_names:
                removed_jobs += 1
                continue
            kept_jobs.append(job)
        cron_payload["jobs"] = kept_jobs
        cron_jobs_path.write_text(json.dumps(cron_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    project_payload["巡检设置"]["巡检任务ID"] = ""
    project_payload["巡检设置"]["推进任务ID"] = ""
    project_payload["巡检设置"]["汇报任务ID"] = ""
    project_payload["巡检设置"]["是否已注册"] = False
    project_payload["巡检设置"]["下次建议巡检时间"] = ""
    project_payload["自动推进设置"]["是否自动注册"] = False
    project_payload["下次自动推进时间"] = ""
    project_payload["当前批次状态"] = "已交付冻结"
    project_payload["当前批次对象列表"] = []
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "项目名称": project_payload.get("项目名称", ""),
        "是否已发送最终报告": True,
        "最终报告发送时间": delivered.isoformat(),
        "冻结版本号": final_info["冻结版本号"],
        "清理巡检任务数": removed_jobs,
        "自动解绑人数": auto_unbound_count,
        "待补偿回写人数": pending_writeback_count,
    }


def evaluate_project_actions(
    project_dir: Path,
    now_at: str | None = None,
    cron_jobs_path: Path | None = None,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    if _规范后台worker展示状态(project_payload):
        _写回项目(project_dir, project_payload, participants_payload)
        project_payload, participants_payload = _读取项目(project_dir)
    stale_info = _后台worker过期信息(project_payload, now_at=now_at)
    if stale_info:
        _清理失活后台worker(
            project_dir,
            project_payload,
            participants_payload,
            code=str(stale_info.get("code", "")).strip(),
            detail=str(stale_info.get("detail", "")).strip(),
            now_at=now_at,
        )
        project_payload, participants_payload = _读取项目(project_dir)
    now = _解析时间(now_at) if now_at else _现在()
    if now is None:
        now = _现在()
    deadline = _解析时间(project_payload.get("项目截止时间", ""))
    frozen = _是否项目已冻结(project_payload)
    strategy = project_payload.get("跟进策略", {})
    auto_settings = _自动推进设置(project_payload)
    first_hours = int(strategy.get("首次跟进间隔小时", 6))
    second_hours = int(strategy.get("第二次跟进间隔小时", 12))
    final_hours = int(strategy.get("最终截止提醒提前小时", 6))
    cron_diag = _诊断项目cron配置(project_payload, cron_jobs_path=cron_jobs_path)

    project_actions: list[dict[str, str]] = []
    participant_actions: list[dict[str, str]] = []

    if not deadline:
        project_actions.append({"建议动作": "补充截止时间", "原因": "尚未提供项目截止时间，自动访谈仍被阻止"})
    if project_payload.get("建议名单待确认"):
        project_actions.append({"建议动作": "确认建议名单", "原因": "当前是范围建议模式，需先确认受访对象名单"})
    if deadline and now >= deadline and not frozen:
        project_actions.append({"建议动作": "进入截止收口", "原因": "已达到项目截止时间"})
    if cron_diag.get("状态") == "异常":
        project_actions.append(
            {
                "建议动作": "修复 cron 运行归属与 prompt",
                "原因": "；".join([str(item).strip() for item in cron_diag.get("问题", []) if str(item).strip()]),
            }
        )

    for participant in participants_payload.get("受访对象列表", []):
        action = "继续等待"
        reason = "当前无需动作"
        status = participant.get("当前状态", "待联系")
        protocol_check = _检查shared协议状态(participant)
        channel_diag = _执行通道诊断(project_payload, participant)

        has_live_shared_session = _辅助执行会话已真实创建(participant) or bool(str(participant.get("会话绑定ID", "")).strip())
        if _是否需要回退半成品shared(participant, protocol_check=protocol_check):
            action = "回退清理后再按正式批次重建"
            reason = f"{非法预建shared文案} {str(protocol_check.get('原因', '')).strip()}".strip()
        elif (
            has_live_shared_session
            and status in {"待回复", "访谈中"}
            and str(protocol_check.get("状态", "")) == "协议不完整"
        ):
            action = "停止复用并补协议"
            reason = str(protocol_check.get("原因", "")).strip() or "shared 协议不完整，不能继续依赖当前会话"
        elif status == "已完成待回写":
            action = "补偿回写后解绑"
            reason = "对象已达到收口条件，但 YAML/Markdown 回写还未完整落盘"
        elif _需要自动解绑已完成对象(participant):
            action = "执行自动解绑"
            reason = "对象已完成但仍占用 shared 通道，应立即退回 research 主对话"
        elif status == "已关闭后回复":
            action = "只做记录"
            reason = "最终报告已发送，晚到回复不再改主报告"
        elif deadline and now >= deadline and status not in 终态状态 and status != "超时后补回":
            action = "到期封口"
            reason = "已到项目截止时间"
        elif status == "待联系" and project_payload.get("是否可直接开始批量访谈"):
            action = "发起首次邀约"
            reason = "已具备自动访谈条件"
        elif status == "已停滞待回":
            action = "继续等待"
            reason = "对方已说明稍后回复，当前不追加追问"
        elif status == "超时后补回":
            action = "刷新分析"
            reason = "截止后补回已到达，需刷新阶段分析与交付草案"
        elif status == "待核验发送":
            action = "核验发送结果"
            reason = "已有 messageId + chatId，但发送确认状态仍低于已确认回执"
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
                "shared协议状态": str(protocol_check.get("状态", "")),
                "执行通道真值类型": channel_diag["执行通道真值类型"],
                "canonical执行会话Key": channel_diag["canonical执行会话Key"],
                "helper会话状态": channel_diag["helper会话状态"],
                "执行通道是否漂移": channel_diag["执行通道是否漂移"],
                "绑定诊断": channel_diag["绑定诊断"],
                "绑定是否因重启后重新核验通过": channel_diag["绑定是否因重启后重新核验通过"],
            }
        )

    project_payload["巡检设置"]["上次巡检时间"] = now.isoformat()
    project_payload["巡检设置"]["下次建议巡检时间"] = (
        now
        + timedelta(
            minutes=int(
                project_payload["巡检设置"].get("巡检间隔分钟", 默认自动推进间隔分钟)
                or 默认自动推进间隔分钟
            )
        )
    ).isoformat()
    _写回项目(project_dir, project_payload, participants_payload)

    return {
        "项目名称": project_payload.get("项目名称", ""),
        "当前阶段": project_payload.get("当前阶段", ""),
        "是否建议自动注册": _需要自动注册推进任务(project_payload, participants_payload.get("受访对象列表", []))
        and not bool(project_payload.get("巡检设置", {}).get("是否已注册")),
        "cron诊断": cron_diag,
        "后台执行中": bool(auto_settings.get("后台执行中")),
        "后台执行worker类型": str(auto_settings.get("后台执行worker类型", "")).strip(),
        "后台执行worker运行ID": str(auto_settings.get("后台执行worker运行ID", "")).strip(),
        "后台执行worker会话Key": str(auto_settings.get("后台执行worker会话Key", "")).strip(),
        "后台执行最近摘要": str(auto_settings.get("后台执行最近摘要", "")).strip(),
        "后台执行最近诊断": str(auto_settings.get("后台执行最近诊断", "")).strip(),
        "后台执行状态是否完整": _后台worker状态是否完整(auto_settings),
        "当前批次状态": project_payload.get("当前批次状态", ""),
        "当前批次对象列表": project_payload.get("当前批次对象列表", []),
        "当前批次是否与真实状态一致": _当前批次是否与真实状态一致(
            project_payload, participants_payload.get("受访对象列表", [])
        ),
        "是否存在发送确认不足": any(
            str(item.get("当前状态", "")).strip() in {"待回复", "待核验发送"} and not _发送确认达到待回复门槛(item)
            for item in participants_payload.get("受访对象列表", [])
        ),
        "上次推进结果摘要": project_payload.get("上次推进结果摘要", {}),
        "项目动作": project_actions,
        "受访对象动作": participant_actions,
        "执行通道概览": [
            {
                "姓名": participant.get("姓名", ""),
                **_执行通道诊断(project_payload, participant),
            }
            for participant in participants_payload.get("受访对象列表", [])
        ],
    }


def cleanup_prebuilt_shared_sessions(
    project_dir: Path,
    session_root: Path = 默认shared会话目录,
    participant_names: list[str] | None = None,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    requested_names = {str(name).strip() for name in (participant_names or []) if str(name).strip()}
    cleaned: list[str] = []
    for participant in participants_payload.get("受访对象列表", []):
        participant_name = str(participant.get("姓名", "")).strip()
        if requested_names and participant_name not in requested_names:
            continue
        protocol_check = _检查shared协议状态(participant, session_root=session_root)
        if not _是否需要回退半成品shared(participant, protocol_check=protocol_check):
            continue
        reason = f"误触发待命 shared，会话已作废；{str(protocol_check.get('原因', '')).strip()}".strip("；")
        _回退误触发待命shared(participant, reason=reason)
        cleaned.append(participant_name)

    if cleaned:
        _写回项目(project_dir, project_payload, participants_payload)

    return {
        "项目名称": project_payload.get("项目名称", ""),
        "清理人数": len(cleaned),
        "清理对象": cleaned,
        "扫描shared会话目录": str(session_root),
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
            participant["当前状态"] = "已超时待收口"
            participant["完成摘要"] = participant.get("完成摘要") or "截止时间已到，未能完成访谈。"
            participant["超时原因"] = participant.get("超时原因") or "截止时间已到但尚未完成访谈"
            participant["收口方式"] = participant.get("收口方式") or "截止收口，等待是否有晚到补回"
            timed_out_count += 1

    project_payload["当前阶段"] = "分析总结"
    project_payload["项目状态"] = "待交付"
    project_payload["分析收口"]["最终收口时间"] = now.isoformat()
    _写回项目(project_dir, project_payload, participants_payload)
    analysis = analyze_project(project_dir=project_dir, now_at=now.isoformat())
    return {
        "已超时人数": timed_out_count,
        "项目状态": project_payload["项目状态"],
        "有效样本数": analysis["有效样本数"],
    }


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
            participant["超时原因"] = participant.get("超时原因") or "项目被手动停止"
            participant["收口方式"] = "手动停止收口"
            timed_out_count += 1
        participant["会话绑定状态"] = "已解绑"
        participant["会话绑定ID"] = ""
        participant["最近一次绑定确认时间"] = ""
        participant["最近一次绑定确认依据"] = ""
        participant["最近一次绑定目标会话Key"] = ""
        participant["最近一次绑定检查结果"] = "已解绑"
        participant["执行会话ID"] = ""
        participant["辅助执行会话ID"] = ""
        participant["辅助执行会话Key"] = ""
        participant["执行会话Key"] = ""
        participant["最近发出时间"] = ""
        participant["最近一次发送消息ID"] = ""
        participant["最近一次发送chatID"] = ""
        participant["最近一次发送确认状态"] = ""
        participant["最近一次发送确认时间"] = ""
        participant["最近一次发送确认依据"] = ""
        if participant.get("最近一次卡片ID"):
            participant["最近一次卡片结果"] = "已失效"
        participant["是否已回收至research"] = True
        participant["最近一次回收时间"] = now.isoformat()

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
        tracked_job_ids = {
            str(project_payload.get("巡检设置", {}).get("巡检任务ID", "")).strip(),
            str(project_payload.get("巡检设置", {}).get("推进任务ID", "")).strip(),
            str(project_payload.get("巡检设置", {}).get("汇报任务ID", "")).strip(),
        }
        tracked_job_ids.discard("")
        target_names = {
            f"内部访谈调研巡检-{project_payload.get('项目名称', '')}",
            f"内部访谈调研推进-{project_payload.get('项目名称', '')}",
            f"内部访谈调研汇报-{project_payload.get('项目名称', '')}",
        }
        kept_jobs = []
        for job in jobs:
            if job.get("id") in tracked_job_ids or job.get("name") in target_names:
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
    project_payload["巡检设置"]["推进任务ID"] = ""
    project_payload["巡检设置"]["汇报任务ID"] = ""
    project_payload["巡检设置"]["是否已注册"] = False
    project_payload["巡检设置"]["下次建议巡检时间"] = ""
    project_payload["自动推进设置"]["是否自动注册"] = False
    project_payload["下次自动推进时间"] = ""
    project_payload["当前批次状态"] = "已停止"
    project_payload["当前批次对象列表"] = []

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


def close_project(project_dir: Path, now_at: str | None = None) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    now = _解析时间(now_at) if now_at else _现在()
    if now is None:
        now = _现在()

    final_info = project_payload.get("最终交付信息", {})
    freeze_deadline = _解析时间(final_info.get("冻结观察截止时间", ""))
    if freeze_deadline is None:
        delivered_at = _解析时间(final_info.get("最终报告发送时间", ""))
        hours = int(final_info.get("冻结观察期小时", 48) or 48)
        if delivered_at is not None:
            freeze_deadline = delivered_at + timedelta(hours=hours)
            final_info["冻结观察截止时间"] = freeze_deadline.isoformat()
    if freeze_deadline is not None and now < freeze_deadline:
        return {
            "项目状态": project_payload.get("项目状态", ""),
            "允许关闭": False,
            "冻结观察截止时间": freeze_deadline.isoformat(),
        }

    closed_count = 0
    for participant in participants_payload.get("受访对象列表", []):
        participant["会话绑定状态"] = "已解绑"
        participant["会话绑定ID"] = ""
        participant["最近一次绑定确认时间"] = ""
        participant["最近一次绑定确认依据"] = ""
        participant["最近一次绑定目标会话Key"] = ""
        participant["最近一次绑定检查结果"] = "已解绑"
        participant["执行会话ID"] = ""
        participant["辅助执行会话ID"] = ""
        participant["辅助执行会话Key"] = ""
        participant["执行会话Key"] = ""
        participant["最近发出时间"] = ""
        participant["最近一次发送消息ID"] = ""
        participant["最近一次发送chatID"] = ""
        participant["最近一次发送确认状态"] = ""
        participant["最近一次发送确认时间"] = ""
        participant["最近一次发送确认依据"] = ""
        if participant.get("当前状态") not in {"已完成", "已拒绝", "已关闭后回复"}:
            participant["当前状态"] = "已关闭"
        participant["最近一次回收时间"] = now.isoformat()
        participant["是否已回收至research"] = True
        closed_count += 1

    project_payload["当前阶段"] = "已关闭"
    if project_payload.get("项目状态") != "已停止":
        project_payload["项目状态"] = "已关闭"
    project_payload["自动推进设置"]["是否自动注册"] = False
    project_payload["下次自动推进时间"] = ""
    project_payload["当前批次状态"] = "已关闭"
    project_payload["当前批次对象列表"] = []
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "项目状态": project_payload["项目状态"],
        "允许关闭": True,
        "关闭人数": closed_count,
    }


def recover_project_replies(
    project_dir: Path,
    gateway_log_path: Path = 默认网关日志路径,
    session_root: Path = 默认shared会话目录,
    research_session_root: Path = 默认research会话目录,
) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    participants = participants_payload.get("受访对象列表", [])
    shared_send_records = _扫描shared发送记录(participants, session_root=session_root)
    recover_scan = _扫描补回候选(participants, gateway_log_path=gateway_log_path, session_root=session_root)
    recovered_items = recover_scan["recovered"]
    metadata_only_items = recover_scan["metadata_only"]
    route_map = _扫描网关回复路由(participants, gateway_log_path=gateway_log_path)
    recovered_by_name: dict[str, list[dict[str, Any]]] = {}
    for item in recovered_items:
        recovered_by_name.setdefault(str(item["participant"].get("姓名", "")).strip(), []).append(item)
    metadata_only_names = sorted(
        {
            str(item.get("participant", {}).get("姓名", "")).strip()
            for item in metadata_only_items
            if str(item.get("participant", {}).get("姓名", "")).strip()
        }
    )

    shared_send_compensated = 0
    for participant in participants_payload.get("受访对象列表", []):
        feishu_target = _标准飞书目标(participant.get("飞书标识", ""))
        open_id = feishu_target.split(":", 1)[-1] if ":" in feishu_target else feishu_target
        record = shared_send_records.get(open_id)
        if not record:
            continue
        route_info = route_map.get(open_id or "", {})
        canonical_session_key = _固定direct_shared执行会话key(participant) or participant.get("执行会话Key", "")
        routed_session_key = str(route_info.get("boundSessionKey", "")).strip()
        target_session_key = routed_session_key or canonical_session_key or record.get("bindingTargetSessionKey", "") or record["executionSessionKey"]
        update_participant(
            project_dir=project_dir,
            participant_name=participant.get("姓名", ""),
            last_outbound_at=record["timestamp"],
            execution_session_id=record["executionSessionId"],
            execution_session_key=target_session_key,
            helper_execution_session_id=record.get("helperSessionId", "") or record["executionSessionId"],
            helper_execution_session_key=participant.get("辅助执行会话Key", "") or record.get("helperSessionKey", ""),
            conversation_binding_id=record["bindingId"] or participant.get("会话绑定ID", ""),
            conversation_binding_status=record["bindingStatus"] or participant.get("会话绑定状态", ""),
            binding_confirmed_at=record.get("bindingConfirmedAt", "") or participant.get("最近一次绑定确认时间", ""),
            binding_confirmation_evidence=record.get("bindingEvidence", "") or participant.get("最近一次绑定确认依据", ""),
            binding_target_session_key=target_session_key,
            binding_check_result=record.get("bindingCheckResult", "") or participant.get("最近一次绑定检查结果", ""),
            last_message_id=record["messageId"],
            last_chat_id=record["chatId"],
            send_confirmation_status="已形成可回收 shared 会话",
            send_confirmation_time=record["timestamp"],
            send_confirmation_evidence=(
                f"shared 会话工具回执：messageId={record['messageId']}，"
                f"chatId={record['chatId']}，来源={record['session_file']}"
            ),
        )
        shared_send_compensated += 1

    recovered_count = 0
    shared_recovered_names: list[str] = []
    for participant_name, items in recovered_by_name.items():
        if not participant_name:
            continue
        participant = items[0]["participant"]
        last_outbound_at = _解析时间(str(participant.get("最近发出时间", "")).strip())
        seen_times = [
            parsed
            for parsed in [
                _解析时间(str(participant.get("最近一次回收时间", "")).strip()),
                _解析时间(str(participant.get("最近回复时间", "")).strip()),
            ]
            if parsed is not None
        ]
        last_seen_at = max(seen_times) if seen_times else None
        sorted_items = sorted(items, key=lambda item: str(item.get("timestamp", "")).strip())
        valid_entries: list[dict[str, Any]] = []
        ignored_entries: list[dict[str, Any]] = []
        handled_targets: set[str] = set()
        for item in sorted_items:
            reply_at_text = _时间字符串(str(item.get("timestamp", "")).strip()) or _现在字符串()
            reply_at = _解析时间(reply_at_text)
            if last_outbound_at is not None and reply_at is not None and reply_at < last_outbound_at:
                continue
            if last_seen_at is not None and reply_at is not None and reply_at <= last_seen_at:
                continue
            assistant_text = str(item.get("assistant_text", "")).strip()
            reply_text = str(item.get("text", "")).strip()
            prompt_target = _识别访谈问题目标(assistant_text)
            fallback_signals = _从回复文本提取信号(reply_text)
            if _是否非调研流程消息(reply_text):
                ignored_entries.append({**item, "timestamp": reply_at_text})
                continue
            signal_key = prompt_target or "|".join(fallback_signals)
            if signal_key and signal_key in handled_targets:
                ignored_entries.append({**item, "timestamp": reply_at_text})
                continue
            if not prompt_target and not fallback_signals and not assistant_text and len(_标准化短文本(reply_text)) < 4:
                ignored_entries.append({**item, "timestamp": reply_at_text})
                continue
            if signal_key:
                handled_targets.add(signal_key)
            valid_entries.append(
                {
                    **item,
                    "timestamp": reply_at_text,
                    "signals": [prompt_target] if prompt_target else fallback_signals,
                }
            )
        if not valid_entries:
            continue
        last_valid_at = valid_entries[-1]["timestamp"] if valid_entries else _现在字符串()
        note_lines = [f"## 补偿回收 {last_valid_at}", f"- 来源会话：{str(items[0].get('session_file', '')).strip()}"]
        for item in valid_entries:
            note_lines.append(f"- 有效回复：{str(item.get('text', '')).strip()}")
        for item in ignored_entries:
            note_lines.append(f"- 忽略消息：{str(item.get('text', '')).strip()}")
        note_path = _写入访谈记录(
            project_dir,
            participant,
            note_lines,
        )
        effective_count = int(participant.get("累计有效问题数", 0) or 0) + len(valid_entries)
        collected_signals = _去重信号(
            [
                str(signal).strip()
                for item in valid_entries
                for signal in item.get("signals", [])
                if str(signal).strip()
            ]
        )
        summary_text = participant.get("完成摘要") or _生成补回摘要(valid_entries) or f"历史补回：{str(items[-1].get('text', '')).strip()[:80]}"
        update_participant(
            project_dir=project_dir,
            participant_name=participant_name,
            note_path=str(note_path),
            summary=summary_text,
            last_inbound_at=last_valid_at,
            effective_question_count=effective_count,
            collected_signals=collected_signals,
            business_status="收到回复并完成历史补回",
            link_status="历史补回成功",
            recovered_to_research=True,
            last_recovered_at=last_valid_at,
        )
        recovered_count += 1
        shared_recovered_names.append(participant_name)

    project_payload, participants_payload = _读取项目(project_dir)
    participant_by_message_id: dict[str, dict[str, Any]] = {}
    participants_by_name: dict[str, dict[str, Any]] = {}
    for participant in participants_payload.get("受访对象列表", []):
        participants_by_name[str(participant.get("姓名", "")).strip()] = participant
        message_id = str(participant.get("最近一次发送消息ID", "")).strip()
        if message_id:
            participant_by_message_id[message_id] = participant

    send_records: dict[str, dict[str, str]] = {}
    if research_session_root.exists():
        for session_file in research_session_root.rglob("*.jsonl"):
            try:
                lines = session_file.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for raw_line in lines:
                try:
                    entry = json.loads(raw_line)
                except Exception:
                    continue
                if entry.get("type") != "message":
                    continue
                message = entry.get("message", {})
                if not isinstance(message, dict):
                    continue
                if message.get("role") != "toolResult" or message.get("toolName") != "message":
                    continue
                details = message.get("details", {})
                if not isinstance(details, dict):
                    continue
                message_id = str(details.get("messageId", "")).strip()
                chat_id = str(details.get("chatId", "")).strip()
                if not message_id or not chat_id:
                    continue
                send_records[message_id] = {
                    "chatId": chat_id,
                    "session_file": str(session_file),
                }

    send_compensated = 0
    cleaned_missing_records: list[str] = []
    now_text = _现在字符串()
    for message_id, participant in participant_by_message_id.items():
        record = send_records.get(message_id)
        if record:
            current_chat_id = str(participant.get("最近一次发送chatID", "")).strip()
            current_confirm = _当前发送确认状态(participant)
            if current_chat_id and current_confirm == "已形成可回收 shared 会话":
                continue
            confirmation_status = "已确认送达" if participant.get("最近回复时间") or participant.get("最近一次回收时间") else "发送记录存在但待人工确认"
            update_participant(
                project_dir=project_dir,
                participant_name=participant.get("姓名", ""),
                status="待回复" if confirmation_status in 待回复发送确认门槛 else "待核验发送",
                last_chat_id=participant.get("最近一次发送chatID") or record["chatId"],
                send_confirmation_status=confirmation_status,
                send_confirmation_time=now_text,
                send_confirmation_evidence=(
                    f"message 工具返回：messageId={message_id}，chatId={record['chatId']}，来源={record['session_file']}"
                ),
            )
            send_compensated += 1
        elif not _当前发送确认状态(participant) or not str(participant.get("最近一次发送chatID", "")).strip():
            fallback_status = "待首发" if _会话已就绪(participant) else "待绑定"
            update_participant(
                project_dir=project_dir,
                participant_name=participant.get("姓名", ""),
                status=fallback_status,
                last_outbound_at="",
                last_message_id="",
                last_chat_id="",
                send_confirmation_status="发送记录缺失",
                send_confirmation_time=now_text,
                send_confirmation_evidence=f"未在 research 会话目录中找到 messageId={message_id} 的发送记录。",
                business_status="发送记录缺失，待人工确认",
                link_status="发送记录缺失，已清理半成品状态",
            )
            cleaned_missing_records.append(str(participant.get("姓名", "")).strip())
            send_compensated += 1

    project_payload, participants_payload = _读取项目(project_dir)
    shared_recovered = sorted({name for name in shared_recovered_names if name})
    main_dialog_replies: list[str] = []
    route_verdicts: list[dict[str, str]] = []
    for participant in participants_payload.get("受访对象列表", []):
        name = str(participant.get("姓名", "")).strip()
        open_id = _提取飞书open_id(participant.get("飞书标识", ""))
        route_info = route_map.get(open_id or "", {})
        if name in shared_recovered:
            route_verdicts.append({"姓名": name, "结果": "shared 已真实回收"})
            continue
        if name in metadata_only_names:
            route_verdicts.append({"姓名": name, "结果": 回复仅元数据结果})
            continue
        if route_info.get("main"):
            main_dialog_replies.append(name)
            route_verdicts.append({"姓名": name, "结果": "回复仍在主对话 / 未命中 shared"})
            continue
        if route_info.get("bound"):
            route_verdicts.append({"姓名": name, "结果": "发现绑定路由证据，但 shared transcript 未找到入站"})

    return {
        "项目名称": project_payload.get("项目名称", ""),
        "补回人数": recovered_count,
        "shared发送补偿人数": shared_send_compensated,
        "发送核验补偿人数": send_compensated,
        "清理缺证据对象": cleaned_missing_records,
        "shared已真实回收": shared_recovered,
        "仅元数据通知": metadata_only_names,
        "回复仍在主对话": sorted(name for name in main_dialog_replies if name),
        "首次回复路由核验": route_verdicts,
        "扫描会话目录": str(session_root),
        "扫描网关日志": str(gateway_log_path),
        "扫描research会话目录": str(research_session_root),
    }


def build_final_delivery_payload(project_dir: Path) -> dict[str, Any]:
    project_payload, participants_payload = _读取项目(project_dir)
    summary = _统计样本(participants_payload.get("受访对象列表", []))
    effective_sample_count = sum(1 for item in participants_payload.get("受访对象列表", []) if _是否计入有效样本(item))
    gap_text = project_payload.get("分析收口", {}).get("样本缺口说明", "") or "暂无样本缺口说明。"
    report_path = project_dir / "最终调研报告.md"
    report_markdown = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    target = _标准飞书目标(project_payload.get("最终交付信息", {}).get("发起人飞书标识", ""))
    delivery_account = str(project_payload.get("最终交付信息", {}).get("交付账号标识", "research")).strip() or "research"
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
            "accountId": delivery_account,
            "target": target,
            "message": (
                f"【{project_payload.get('项目名称', '')}】内部访谈调研已收口。"
                f"有效样本 {effective_sample_count}/{summary['总人数']}，"
                f"已超时 {summary['已超时人数']}，已拒绝 {summary['已拒绝人数']}。"
                "飞书文档创建完成后，请把文档链接附在本消息后发送给发起人。"
            ),
        },
        "摘要消息": (
            f"【{project_payload.get('项目名称', '')}】内部访谈调研已收口。"
            f"有效样本 {effective_sample_count}/{summary['总人数']}，"
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
    if not _是否项目已冻结(project_payload):
        analyze_project(project_dir=project_dir)
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
            "accountId": str(project_payload.get("最终交付信息", {}).get("交付账号标识", "research")).strip() or "research",
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
                        "accountId": str(project_payload.get("最终交付信息", {}).get("交付账号标识", "research")).strip() or "research",
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
                        "accountId": str(project_payload.get("最终交付信息", {}).get("交付账号标识", "research")).strip() or "research",
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
    interval_minutes: int = 默认自动推进间隔分钟,
    report_mode: str = "every-round",
    auto_created: bool = False,
    agent_id: str = "research",
) -> dict[str, Any]:
    if cron_jobs_path.exists():
        cron_payload = json.loads(cron_jobs_path.read_text(encoding="utf-8"))
    else:
        cron_payload = {"version": 1, "jobs": []}

    project_payload, participants_payload = _读取项目(project_dir)
    jobs = cron_payload.setdefault("jobs", [])
    manage_script = _管理脚本路径()
    normalized_interval_expr = _规范cron表达式(interval_minutes)
    normalized_report_mode = str(report_mode or "every-round").strip() or "every-round"

    def upsert_job(name: str, expr: str, message: str) -> dict[str, Any]:
        now_ms = int(_现在().timestamp() * 1000)
        existing = None
        for job in jobs:
            if job.get("name") == name:
                existing = job
                break
        if existing is None:
            job = {
                "id": str(uuid4()),
                "agentId": agent_id,
                "name": name,
                "enabled": True,
                "createdAtMs": now_ms,
                "updatedAtMs": now_ms,
                "schedule": {
                    "kind": "cron",
                    "expr": expr,
                    "tz": "Asia/Shanghai",
                    "staggerMs": 0,
                },
                "sessionTarget": "isolated",
                "wakeMode": "now",
                "payload": {
                    "kind": "agentTurn",
                    "message": message,
                    "lightContext": True,
                },
                "delivery": {"mode": "none"},
                "state": {
                    "projectDir": str(project_dir),
                    "reportMode": normalized_report_mode,
                    "autoCreated": auto_created,
                },
            }
            jobs.append(job)
            return job
        existing["agentId"] = agent_id
        existing["payload"]["message"] = message
        existing["schedule"]["expr"] = expr
        existing["updatedAtMs"] = now_ms
        existing.setdefault("state", {})
        existing["state"]["projectDir"] = str(project_dir)
        existing["state"]["reportMode"] = normalized_report_mode
        existing["state"]["autoCreated"] = auto_created
        return existing

    advance_prompt = (
        "你是 research 调研推进后台 worker。"
        f"先运行：python3 {manage_script} run-batch-worker --project-dir '{project_dir}' --trigger cron --status prepare --cron-jobs-path '{cron_jobs_path}'。"
        "如果返回“后台仍在执行”，本轮静默结束。"
        "如果返回“是否启动后台worker=true”，只能继续执行 prepare 结果里的 `启动命令`、`心跳命令`、`完成命令`；禁止自己补 worker 标识。"
        "然后只按 advance结果.执行合同 和 advance结果.跟进行动 执行整轮推进。"
        "本轮结束后运行 prepare 结果里的 `完成命令`。"
        "每次 exec 只允许一条命令，先看结果再执行下一条。"
        "禁止使用 &&、;、|、printf 或 here-doc 拼接多条命令。"
        "禁止临场手写 sessions_send / bind / status / writeback 参数，禁止把 NO_REPLY、待命 completion 或内部补偿文案发给用户。"
    )
    inspect_prompt = (
        "你是 research 调研汇报。"
        f"先运行：python3 {manage_script} inspect --project-dir '{project_dir}'。"
        f"汇报模式={normalized_report_mode}。"
        "只在本轮有进展、阻塞变化或里程碑变化时给发起人发送短汇报；否则静默。"
        "不要执行首轮外发，不要拼任何 sessions_send 参数。"
    )

    advance_job = upsert_job(
        name=f"内部访谈调研推进-{project_payload['项目名称']}",
        expr=normalized_interval_expr,
        message=advance_prompt,
    )
    inspect_job = upsert_job(
        name=f"内部访谈调研汇报-{project_payload['项目名称']}",
        expr=normalized_interval_expr,
        message=inspect_prompt,
    )

    cron_jobs_path.write_text(json.dumps(cron_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    project_payload["巡检设置"]["巡检间隔分钟"] = interval_minutes
    project_payload["巡检设置"]["巡检任务ID"] = inspect_job["id"]
    project_payload["巡检设置"]["推进任务ID"] = advance_job["id"]
    project_payload["巡检设置"]["汇报任务ID"] = inspect_job["id"]
    project_payload["巡检设置"]["是否已注册"] = True
    project_payload["巡检设置"]["下次建议巡检时间"] = (_现在() + timedelta(minutes=interval_minutes)).isoformat()
    project_payload["自动推进设置"]["是否自动注册"] = True
    project_payload["自动推进设置"]["推进间隔分钟"] = interval_minutes
    project_payload["自动推进设置"]["汇报模式"] = normalized_report_mode
    project_payload["自动推进设置"]["自动创建"] = bool(auto_created)
    project_payload["当前批次状态"] = project_payload.get("当前批次状态", "") or "待推进"
    project_payload["上次推进结果摘要"]["执行状态"] = project_payload["上次推进结果摘要"].get("执行状态") or "待推进"
    project_payload["下次自动推进时间"] = project_payload["巡检设置"]["下次建议巡检时间"]
    _写回项目(project_dir, project_payload, participants_payload)
    return {
        "推进任务": {
            "任务ID": advance_job["id"],
            "任务名称": advance_job["name"],
            "cron表达式": advance_job["schedule"]["expr"],
        },
        "汇报任务": {
            "任务ID": inspect_job["id"],
            "任务名称": inspect_job["name"],
            "cron表达式": inspect_job["schedule"]["expr"],
        },
        "汇报模式": normalized_report_mode,
        "自动创建": bool(auto_created),
    }
