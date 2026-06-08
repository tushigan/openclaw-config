#!/usr/bin/env python3
"""Export an OpenClaw session trajectory bundle plus recent gateway logs.

Creates a timestamped output directory under .openclaw/trajectory-exports and
writes a markdown report that points at the exported bundle and recent logs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from export_chat_report import resolve_current_session_key as resolve_chat_current_session_key


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "session"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export session trajectory + logs to a markdown report")
    ap.add_argument("--workspace", default=os.getcwd(), help="Workspace root")
    ap.add_argument("--session-key", default="current", help="Session key to export; use 'current' to auto-resolve")
    ap.add_argument("--agent", "--agent-id", dest="agent_id", default=None, help="Agent id to prefer when resolving --session-key current")
    ap.add_argument("--chat-type", choices=["direct", "group", "channel"], default=None, help="Chat type to prefer when resolving --session-key current")
    ap.add_argument("--peer-id", default=None, help="Peer/chat id to prefer when resolving --session-key current, such as ou_xxx or oc_xxx")
    ap.add_argument("--issue", required=True, help="Short issue title")
    ap.add_argument("--output", default=None, help="Output folder name inside .openclaw/trajectory-exports")
    ap.add_argument("--log-lines", type=int, default=200, help="How many gateway log lines to capture")
    ap.add_argument("--max-bytes", type=int, default=250000, help="Max bytes when tailing gateway logs")
    ap.add_argument("--no-logs", action="store_true", help="Skip gateway log capture")
    args = ap.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    session_key = args.session_key
    if session_key == "current":
        resolved = resolve_chat_current_session_key(
            workspace=workspace,
            cwd=Path.cwd(),
            agent_id=args.agent_id,
            chat_type=args.chat_type,
            peer_id=args.peer_id,
        )
        if not resolved:
            sys.stderr.write("Failed to auto-resolve current session key. Pass --session-key explicitly.\n")
            return 2
        session_key = resolved

    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = slugify(args.issue)
    session_slug = slugify(session_key.split(":")[-1])
    out_name = args.output or f"{base}__{session_slug}__{ts}"
    export_root = workspace / ".openclaw" / "trajectory-exports"
    export_root.mkdir(parents=True, exist_ok=True)

    export_cmd = [
        "openclaw",
        "sessions",
        "export-trajectory",
        "--session-key",
        session_key,
        "--workspace",
        str(workspace),
        "--output",
        out_name,
        "--json",
    ]
    export_res = run(export_cmd, cwd=workspace)
    if export_res.returncode != 0:
        sys.stderr.write(export_res.stdout)
        sys.stderr.write(export_res.stderr)
        return export_res.returncode

    try:
        export_data = json.loads(export_res.stdout.strip().splitlines()[-1])
    except Exception:
        export_data = {"raw": export_res.stdout.strip()}

    output_dir = Path(export_data.get("outputDir") or export_root / out_name)
    output_dir.mkdir(parents=True, exist_ok=True)

    log_text = ""
    if not args.no_logs:
        logs_res = run([
            "openclaw",
            "logs",
            "--limit",
            str(args.log_lines),
            "--max-bytes",
            str(args.max_bytes),
            "--plain",
            "--local-time",
        ], cwd=workspace)
        log_text = (logs_res.stdout or logs_res.stderr or "").strip()

    manifest = output_dir / "manifest.json"
    if manifest.exists():
        try:
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            manifest_data = None
    else:
        manifest_data = None

    report = output_dir / "report.md"
    lines = [
        f"# Session Debug Export",
        "",
        f"- Session: `{session_key}`",
        f"- Issue: `{args.issue}`",
        f"- Exported at: `{ts}`",
        f"- Output dir: `{output_dir}`",
        "",
        "## Bundle",
        "",
        f"- Trajectory bundle: `{output_dir}`",
        f"- Manifest: `{manifest.name if manifest.exists() else 'missing'}`",
        f"- Events: `events.jsonl`",
        f"- Metadata: `metadata.json`",
        f"- Tools: `tools.json`",
        f"- Prompts: `prompts.json`",
        f"- System prompt: `system-prompt.txt`",
        "",
        "## Notes",
        "",
        "Use this bundle as the single input for AI debugging. If the issue is hard to pin down, start with:",
        "1. `manifest.json` for the export shape",
        "2. `events.jsonl` for the full trajectory",
        "3. recent gateway logs for backend errors or retries",
    ]
    if manifest_data and isinstance(manifest_data, dict):
        lines.extend(["", "## Export Summary", ""])
        for key in ("sessionId", "eventCount", "runtimeEventCount", "transcriptEventCount"):
            if key in manifest_data:
                lines.append(f"- {key}: `{manifest_data[key]}`")

    if log_text:
        lines.extend(["", "## Recent Gateway Logs", "", "```log", log_text[:20000], "```"])

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "sessionKey": session_key,
        "outputDir": str(output_dir),
        "report": str(report),
        "export": export_data,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
