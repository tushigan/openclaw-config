#!/usr/bin/env python3
"""Export an OpenClaw session as a shareable debugging markdown report.

The generated report follows the chat-export style:
- AI analysis / issue localization summary
- Full chat transcript with tool calls and tool outputs
- Recent backend gateway logs

It also keeps the raw OpenClaw trajectory bundle next to the export for deeper inspection.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def filename_part(text: str, fallback: str = "session") -> str:
    """Keep readable Unicode in filenames while removing path-hostile characters."""
    text = re.sub(r"[\\/:*?\"<>|\s]+", "-", text.strip())
    text = re.sub(r"-+", "-", text).strip("-.")
    return text or fallback


def slugify(text: str, fallback: str = "session") -> str:
    """Convert arbitrary text into a stable ASCII-ish filename slug."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or fallback


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def resolve_current_session_key() -> str | None:
    """Resolve an active session, falling back to the most recently updated session."""
    for cmd in (
        ["openclaw", "sessions", "--active", "180", "--limit", "10", "--json"],
        ["openclaw", "sessions", "--limit", "10", "--json"],
    ):
        res = run(cmd)
        if res.returncode != 0:
            continue
        try:
            sessions = (json.loads(res.stdout).get("sessions") or [])
        except Exception:
            sessions = []
        if sessions:
            return sessions[0].get("key")
    return None


def format_timestamp(value: str | None) -> str:
    if not value:
        return "unknown-time"
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    except Exception:
        return value


def text_from_content_parts(parts: Any) -> tuple[str, list[str]]:
    """Extract text and attachment markers from OpenClaw/Anthropic-style content blocks."""
    if isinstance(parts, str):
        return parts, []
    if not isinstance(parts, list):
        return str(parts) if parts else "", []

    text_chunks: list[str] = []
    attachments: list[str] = []
    for part in parts:
        if isinstance(part, str):
            text_chunks.append(part)
            continue
        if not isinstance(part, dict):
            continue
        ptype = part.get("type")
        if ptype == "text":
            text_chunks.append(str(part.get("text", "")))
        elif ptype in {"image", "input_image"}:
            source = part.get("source") or part.get("image") or {}
            if isinstance(source, dict):
                label = source.get("path") or source.get("media_id") or source.get("url") or "inline-image"
            else:
                label = source or "inline-image"
            attachments.append(f"[Image: {label}]")
        elif ptype == "toolCall":
            # Tool calls are emitted as separate tool.call events; avoid duplicating here.
            continue
    return "".join(text_chunks), attachments


def tool_result_text(data: dict[str, Any]) -> str:
    if "result" in data:
        return str(data.get("result", ""))
    message = data.get("message", {})
    content = message.get("content", data.get("content", ""))
    text, attachments = text_from_content_parts(content)
    if attachments:
        return "\n".join(attachments + ([text] if text else []))
    return text


def parse_events_to_messages(events_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse trajectory events into displayable chat messages and export stats."""
    messages: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "events": 0,
        "user": 0,
        "assistant": 0,
        "tool_calls": 0,
        "tool_results": 0,
        "tool_errors": 0,
        "tools": Counter(),
        "model": None,
        "provider": None,
    }

    if not events_path.exists():
        return messages, stats

    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            stats["events"] += 1
            etype = event.get("type")
            ts = event.get("ts") or event.get("timestamp")
            data = event.get("data", {}) or {}
            stats["model"] = stats["model"] or event.get("modelId")
            stats["provider"] = stats["provider"] or event.get("provider")

            if etype == "user.message":
                message = data.get("message", {})
                text, attachments = text_from_content_parts(message.get("content", []))
                messages.append({
                    "role": "user",
                    "timestamp": ts,
                    "content": text.strip(),
                    "attachments": attachments,
                })
                stats["user"] += 1

            elif etype == "assistant.message":
                message = data.get("message", {})
                text, _ = text_from_content_parts(message.get("content", []))
                if text.strip():
                    messages.append({
                        "role": "assistant",
                        "timestamp": ts,
                        "content": text.strip(),
                    })
                    stats["assistant"] += 1

            elif etype == "tool.call":
                name = data.get("name") or data.get("toolName") or "unknown"
                messages.append({
                    "role": "tool_call",
                    "timestamp": ts,
                    "tool": name,
                    "input": data.get("arguments", data.get("input", {})),
                })
                stats["tool_calls"] += 1
                stats["tools"][name] += 1

            elif etype == "tool.result":
                message = data.get("message", {})
                name = data.get("name") or data.get("toolName") or message.get("toolName") or "unknown"
                error = data.get("error") or message.get("error")
                output = tool_result_text(data)
                messages.append({
                    "role": "tool_result",
                    "timestamp": ts,
                    "tool": name,
                    "output": output,
                    "error": error,
                })
                stats["tool_results"] += 1
                if error or re.search(r"\b(error|failed|timeout|timed out|exception)\b", output, re.I):
                    stats["tool_errors"] += 1

    return messages, stats


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def find_signals(messages: list[dict[str, Any]], logs: str) -> dict[str, list[str]]:
    """Find likely debugging signals without treating documentation reads as failures."""
    corpus_parts: list[str] = [logs]
    signal_tools = {"exec", "process", "image", "run_command", "bash", "browser", "mcp", "openclaw"}
    for msg in messages:
        if msg.get("role") != "tool_result":
            continue
        tool = str(msg.get("tool") or "").lower()
        output = str(msg.get("output") or "")
        if msg.get("error") or tool in signal_tools:
            corpus_parts.append(output)
    corpus = strip_ansi("\n".join(corpus_parts))

    patterns = {
        "errors": r"(?im)^.*\b(error|failed|exception|traceback|timed out|timeout)\b.*$",
        "fallbacks": r"(?im)^.*\b(fallback|failover|recovery|retry|降级|回退|重试)\b.*$",
        "long_running": r"(?im)^.*\b(long-running|queued_behind_active_work|event_loop_delay|queueDepth|still running)\b.*$",
        "slow_gateway": r"(?im)^.*\b(gateway/ws|node\.list|chat\.history)\b.*(?:[1-9][0-9]{3,}ms).*$",
    }
    signals: dict[str, list[str]] = {}
    for key, pattern in patterns.items():
        seen: list[str] = []
        for match in re.findall(pattern, corpus):
            # re.findall with capture groups returns captured tuple/string, so use finditer instead below.
            pass
        for m in re.finditer(pattern, corpus):
            line = m.group(0).strip()
            if line and line not in seen:
                seen.append(line[:500])
            if len(seen) >= 8:
                break
        signals[key] = seen
    return signals


def generate_analysis(
    issue_title: str,
    session_key: str,
    stats: dict[str, Any],
    logs: str,
    messages: list[dict[str, Any]],
) -> str:
    signals = find_signals(messages, logs)
    tools = stats.get("tools") or Counter()
    top_tools = ", ".join(f"{name}×{count}" for name, count in tools.most_common(8)) or "none"

    likely_causes: list[str] = []
    if signals["errors"]:
        likely_causes.append("工具或上游服务存在错误 / 超时，需要优先查看 Tool Output 和 Backend Logs 中的 error/timeout 行。")
    if signals["fallbacks"]:
        likely_causes.append("执行链路触发 fallback/failover/retry，说明主链路不稳定或被上游拒绝，结果可能来自降级路径。")
    if signals["long_running"]:
        likely_causes.append("存在 long-running / queued_behind_active_work / event_loop_delay，可能是后台队列、事件循环或长工具调用导致响应延迟。")
    if signals["slow_gateway"]:
        likely_causes.append("Backend Logs 出现高耗时 gateway/ws 请求，可能影响前端感知速度或消息同步。")
    if not likely_causes:
        likely_causes.append("未在导出内容中发现明显 error/timeout/fallback/long-running 信号，可从完整聊天记录和原始 events.jsonl 继续人工定位。")

    lines = [
        "### 定位摘要",
        "",
        f"- **问题标题**：{issue_title}",
        f"- **Session Key**：`{session_key}`",
        f"- **模型/提供方**：`{stats.get('provider') or 'unknown'}` / `{stats.get('model') or 'unknown'}`",
        f"- **事件数**：{stats.get('events', 0)}；用户消息 {stats.get('user', 0)}；AI 消息 {stats.get('assistant', 0)}；工具调用 {stats.get('tool_calls', 0)}；工具结果 {stats.get('tool_results', 0)}；疑似工具错误 {stats.get('tool_errors', 0)}",
        f"- **高频工具**：{top_tools}",
        "",
        "### 初步判断",
        "",
    ]
    lines.extend(f"- {cause}" for cause in likely_causes)

    def section(title: str, key: str) -> None:
        values = signals.get(key) or []
        lines.extend(["", f"### {title}", ""])
        if not values:
            lines.append("- 未发现明显信号。")
        else:
            for value in values:
                lines.append(f"- `{value}`")

    section("错误 / 超时信号", "errors")
    section("Fallback / Retry 信号", "fallbacks")
    section("队列 / 长运行信号", "long_running")
    section("慢网关信号", "slow_gateway")

    lines.extend([
        "",
        "### 建议下一步",
        "",
        "1. 先看上面的错误/超时信号，确认是否与用户报障时间点一致。",
        "2. 再看聊天记录中相邻的 Tool Call / Tool Output，确认触发参数、路径、模型和降级链路。",
        "3. 如果本 md 不够定位，继续查看同目录原始 `events.jsonl`、`manifest.json`、`metadata.json`。",
    ])
    return "\n".join(lines)


def fence_text(text: str, limit: int | None = None) -> str:
    text = str(text or "")
    if limit and len(text) > limit:
        text = text[:limit] + f"\n...[truncated {len(text) - limit} chars]"
    return text.replace("```", "``\\`")


def generate_markdown_report(
    session_key: str,
    agent_name: str,
    issue_title: str,
    messages: list[dict[str, Any]],
    logs: str,
    analysis: str,
    export_dir: Path,
) -> str:
    lines = [
        f"# Chat with {agent_name}",
        "",
        "## AI Analysis",
        "",
        analysis,
        "",
        "---",
        "",
        "## Export Metadata",
        "",
        f"- Issue: `{issue_title}`",
        f"- Session: `{session_key}`",
        f"- Raw trajectory bundle: `{export_dir}`",
        f"- Generated at: `{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z`",
        "",
        "---",
        "",
    ]

    for msg in messages:
        role = msg.get("role")
        timestamp = format_timestamp(msg.get("timestamp"))

        if role == "user":
            lines.extend([f"## You ({timestamp})", ""])
            for attachment in msg.get("attachments", []):
                lines.append(attachment)
            if msg.get("content"):
                lines.append(msg["content"])
            lines.append("")

        elif role == "assistant":
            lines.extend([f"## {agent_name} ({timestamp})", "", msg.get("content", ""), ""])

        elif role == "tool_call":
            tool_name = msg.get("tool", "unknown")
            lines.extend([
                f"## {agent_name} ({timestamp})",
                "",
                f"🔧 **Tool Call**: `{tool_name}` ({tool_name})",
                "**Input**:",
                "```json",
                fence_text(json.dumps(msg.get("input", {}), indent=2, ensure_ascii=False), 12000),
                "```",
                "",
            ])

        elif role == "tool_result":
            tool_name = msg.get("tool", "unknown")
            lines.extend([f"## Tool ({timestamp})", ""])
            if msg.get("error"):
                lines.extend([
                    f"❌ **Tool Error**: `{tool_name}` ({tool_name})",
                    f"**Error**: {msg.get('error')}",
                    "",
                ])
            lines.extend([
                f"📦 **Tool Output**: `{tool_name}` ({tool_name})",
                "**Output**:",
                "```text",
                fence_text(msg.get("output", ""), 12000),
                "```",
                "",
            ])

    if logs:
        lines.extend([
            "",
            "## Backend Logs",
            "",
            "```log",
            fence_text(strip_ansi(logs), 30000),
            "```",
        ])

    return "\n".join(lines).rstrip() + "\n"


def read_manifest(output_dir: Path) -> dict[str, Any]:
    try:
        return json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Export OpenClaw session as a chat-style markdown debug report")
    ap.add_argument("--workspace", default=os.getcwd(), help="Workspace/state root used by openclaw sessions export-trajectory")
    ap.add_argument("--session-key", default="current", help="Session key to export; use 'current' to auto-resolve")
    ap.add_argument("--issue", required=True, help="Short issue title, used in report and filename")
    ap.add_argument("--agent-name", default="小爪", help="Agent display name in chat headings")
    ap.add_argument("--output-dir", default=None, help="Report output directory; default: ~/Downloads")
    ap.add_argument("--log-lines", type=int, default=300, help="How many gateway log lines to capture")
    ap.add_argument("--max-bytes", type=int, default=400000, help="Max bytes when capturing gateway logs")
    ap.add_argument("--no-logs", action="store_true", help="Skip backend log capture")
    args = ap.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    session_key = args.session_key
    if session_key == "current":
        session_key = resolve_current_session_key()
        if not session_key:
            sys.stderr.write("Failed to auto-resolve current session key. Pass --session-key explicitly.\n")
            return 2

    generated_ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    issue_slug = slugify(args.issue, "issue")
    session_slug = slugify(session_key.split(":")[-1], "session")
    bundle_name = f"{generated_ts}__{issue_slug}__{session_slug}"

    export_res = run([
        "openclaw", "sessions", "export-trajectory",
        "--session-key", session_key,
        "--workspace", str(workspace),
        "--output", bundle_name,
        "--json",
    ], cwd=workspace)
    if export_res.returncode != 0:
        sys.stderr.write(export_res.stdout)
        sys.stderr.write(export_res.stderr)
        return export_res.returncode

    try:
        export_data = json.loads(export_res.stdout.strip().splitlines()[-1])
    except Exception:
        export_data = {}
    output_dir = Path(export_data.get("outputDir") or workspace / ".openclaw" / "trajectory-exports" / bundle_name)

    messages, stats = parse_events_to_messages(output_dir / "events.jsonl")
    manifest = read_manifest(output_dir)
    stats["events"] = manifest.get("eventCount", stats.get("events", 0))

    logs = ""
    if not args.no_logs:
        logs_res = run([
            "openclaw", "logs",
            "--limit", str(args.log_lines),
            "--max-bytes", str(args.max_bytes),
            "--plain",
            "--local-time",
        ], cwd=workspace)
        logs = (logs_res.stdout or logs_res.stderr or "").strip()

    analysis = generate_analysis(args.issue, session_key, stats, logs, messages)
    report = generate_markdown_report(
        session_key=session_key,
        agent_name=args.agent_name,
        issue_title=args.issue,
        messages=messages,
        logs=logs,
        analysis=analysis,
        export_dir=output_dir,
    )

    report_dir = Path(args.output_dir or Path.home() / "Downloads").expanduser()
    report_dir.mkdir(parents=True, exist_ok=True)
    report_name = f"chat-export-{filename_part(args.agent_name, 'agent')}-{issue_slug}-{generated_ts}.md"
    report_path = report_dir / report_name
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps({
        "sessionKey": session_key,
        "issue": args.issue,
        "outputFile": str(report_path),
        "rawBundleDir": str(output_dir),
        "messageCount": len(messages),
        "eventCount": stats.get("events"),
        "toolErrorSignals": stats.get("tool_errors"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
