#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PIPELINE_SCRIPTS = SKILL_ROOT / "omni-vision-psd-extractor" / "omni-vision-psd-extractor" / "scripts"
sys.path.insert(0, str(PIPELINE_SCRIPTS))

from runtime_config import default_output_base, load_runtime_env  # noqa: E402


DEFAULT_PACKAGE_SPLIT_MB = 25
DEFAULT_PACKAGE_NAME = "layered-output-delivery.zip"
DEFAULT_PROMPT_APPEND_FILE = PIPELINE_SCRIPTS.parent / "references" / "万物提取.md"
DEFAULT_BG_PROMPT = (
    "【极其重要：绝对禁止凭空生成完全不同的风景！必须严格保持原图中的背景结构、光影和色彩不变，"
    "仅仅智能脑补被移除的前景区域。】将图片中的背景提取出来，需要将前景所有元素全部剔除，只保留背景。"
)
DEFAULT_FG_PROMPT = (
    "将图片中除了背景之外的所有前景元素全部提取出来。"
    "【极其重要：强制将背景全部填充为纯正的绿幕（纯绿色，Hex: #00FF00）！绝对不要生成假透明像素方格背景！】"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw delivery wrapper for 111omni PSD extraction")
    parser.add_argument("--source", default="auto", help="Local absolute image path, HTTPS URL, or auto")
    parser.add_argument("--out-dir", help="Output directory; defaults to workspace-design outputs")
    parser.add_argument("--conv-id", default=None, help="Optional Antigravity conversation id for auto source")
    parser.add_argument("--bg-prompt", default=DEFAULT_BG_PROMPT)
    parser.add_argument("--fg-prompt", default=DEFAULT_FG_PROMPT)
    parser.add_argument("--fg-elements", default=None, help="Comma-separated foreground element list for N-layer mode")
    parser.add_argument("--prompt-append-file", default=str(DEFAULT_PROMPT_APPEND_FILE))
    parser.add_argument("--no-prompt-append", action="store_true")
    parser.add_argument("--package-split-mb", type=int, default=DEFAULT_PACKAGE_SPLIT_MB)
    parser.add_argument("--no-package", action="store_true")
    parser.add_argument("--feishu-target", default=os.getenv("OPENCLAW_FEISHU_TARGET", ""), help="Explicit Feishu target: user:ou_xxx or chat:oc_xxx")
    parser.add_argument("--feishu-user-id", default=os.getenv("OPENCLAW_FEISHU_USER_ID", os.getenv("FEISHU_USER_ID", "")), help="Feishu user open_id for direct delivery")
    parser.add_argument("--feishu-chat-id", default=os.getenv("OPENCLAW_FEISHU_CHAT_ID", os.getenv("FEISHU_CHAT_ID", "")), help="Feishu chat_id for group delivery")
    parser.add_argument("--feishu-account-id", default=os.getenv("OPENCLAW_FEISHU_ACCOUNT_ID", ""), help="Feishu account id for audit metadata")
    parser.add_argument(
        "--source-session-key",
        default=(
            os.getenv("OPENCLAW_SOURCE_SESSION_KEY")
            or os.getenv("OPENCLAW_MCP_SESSION_KEY")
            or os.getenv("OPENCLAW_SESSION_KEY")
            or os.getenv("CLAUDE_AI_SESSION_KEY")
            or os.getenv("CLAUDE_WEB_SESSION_KEY")
            or ""
        ),
        help="OpenClaw session key used to derive Feishu target",
    )
    parser.add_argument("--no-send", action="store_true", help="Do not send files even when a Feishu target is available")
    parser.add_argument("--no-send-preview", action="store_true", help="Send package files only, not reverse-preview.png")
    return parser.parse_args()


def normalize_feishu_target(target: str) -> str:
    target = (target or "").strip()
    if target.startswith("user:") or target.startswith("chat:"):
        return target
    if target.startswith("ou_"):
        return f"user:{target}"
    if target.startswith("oc_"):
        return f"chat:{target}"
    return ""


def target_from_source_session_key(source_session_key: str) -> dict[str, str]:
    parts = (source_session_key or "").strip().split(":")
    if len(parts) >= 5 and parts[0] == "agent" and parts[2] == "feishu":
        chat_type = parts[3]
        peer_id = ":".join(parts[4:])
        if chat_type == "direct" and peer_id.startswith("ou_"):
            return {"target": f"user:{peer_id}", "user_id": peer_id, "chat_id": "", "target_source": "source_session_key"}
        if chat_type == "group" and peer_id.startswith("oc_"):
            return {"target": f"chat:{peer_id}", "user_id": "", "chat_id": peer_id, "target_source": "source_session_key"}
    return {"target": "", "user_id": "", "chat_id": "", "target_source": ""}


def resolve_delivery_target(
    *,
    feishu_target: str,
    feishu_user_id: str,
    feishu_chat_id: str,
    feishu_account_id: str,
    source_session_key: str,
) -> dict[str, str]:
    target = normalize_feishu_target(feishu_target)
    user_id = (feishu_user_id or "").strip()
    chat_id = (feishu_chat_id or "").strip()
    target_source = ""

    if not target and user_id:
        target = f"user:{user_id}"
        target_source = "feishu_user_id"
    elif not target and chat_id:
        target = f"chat:{chat_id}"
        target_source = "feishu_chat_id"
    elif target.startswith("user:"):
        user_id = target.split(":", 1)[1]
        chat_id = ""
        target_source = "feishu_target"
    elif target.startswith("chat:"):
        chat_id = target.split(":", 1)[1]
        user_id = ""
        target_source = "feishu_target"

    if not target:
        resolved = target_from_source_session_key(source_session_key)
        target = resolved["target"]
        user_id = resolved["user_id"]
        chat_id = resolved["chat_id"]
        target_source = resolved["target_source"]

    return {
        "target": target,
        "user_id": user_id,
        "chat_id": chat_id,
        "account_id": (feishu_account_id or "").strip(),
        "source_session_key": (source_session_key or "").strip(),
        "target_source": target_source or ("missing" if not target else "explicit"),
        "channel": "feishu",
    }


def build_out_dir(requested: str | None) -> Path:
    if requested:
        return Path(requested).expanduser().resolve()
    return (default_output_base() / f"job_{int(time.time())}").resolve()


def build_pipeline_command(args: argparse.Namespace, out_dir: Path) -> list[str]:
    cmd = [
        sys.executable,
        str(PIPELINE_SCRIPTS / "run_omni_pipeline.py"),
        "--source",
        args.source,
        "--out-dir",
        str(out_dir),
        "--auto-extract",
        "--bg-prompt",
        args.bg_prompt,
    ]
    if args.fg_elements:
        cmd.extend(["--fg-elements", args.fg_elements])
    else:
        cmd.extend(["--fg-prompt", args.fg_prompt])
    if args.conv_id:
        cmd.extend(["--conv-id", args.conv_id])
    if not args.no_prompt_append and args.prompt_append_file:
        cmd.extend(["--prompt-append-file", args.prompt_append_file])
    return cmd


def cleanup_old_package_files(archive_path: Path) -> None:
    prefix = archive_path.stem
    for candidate in archive_path.parent.iterdir():
        if candidate.name == archive_path.name or candidate.name.startswith(f"{prefix}.z"):
            candidate.unlink(missing_ok=True)


def validate_delivery_package(out_dir: Path, archive_path: Path, split_enabled: bool) -> dict[str, object]:
    if split_enabled:
        with tempfile.TemporaryDirectory(prefix="omni-delivery-validate-") as tmp:
            combined = Path(tmp) / "combined.zip"
            merge_cmd = ["zip", "-q", "-s", "0", archive_path.name, "--out", str(combined)]
            merge = subprocess.run(merge_cmd, cwd=out_dir, text=True, capture_output=True)
            if merge.returncode != 0:
                return {
                    "ok": False,
                    "mode": "split",
                    "error": "failed_to_merge_split_zip",
                    "stdout": merge.stdout,
                    "stderr": merge.stderr,
                    "command": " ".join(merge_cmd),
                }
            test_cmd = ["unzip", "-t", str(combined)]
            test = subprocess.run(test_cmd, text=True, capture_output=True)
    else:
        test_cmd = ["unzip", "-t", str(archive_path)]
        test = subprocess.run(test_cmd, text=True, capture_output=True)

    return {
        "ok": test.returncode == 0,
        "mode": "split" if split_enabled else "single",
        "error": "" if test.returncode == 0 else "zip_validation_failed",
        "stdout": test.stdout,
        "stderr": test.stderr,
        "command": " ".join(test_cmd),
    }


def make_delivery_package(out_dir: Path, split_mb: int) -> dict[str, object]:
    psd_path = out_dir / "layered-output.psd"
    archive_path = out_dir / DEFAULT_PACKAGE_NAME
    readme_path = out_dir / "delivery-package.README.txt"
    cleanup_old_package_files(archive_path)

    split_bytes = split_mb * 1024 * 1024
    cmd = ["zip", "-q"]
    split_enabled = psd_path.stat().st_size > split_bytes
    if split_enabled:
        cmd.extend(["-s", f"{split_mb}m"])
    cmd.extend([str(archive_path), psd_path.name])
    subprocess.run(cmd, cwd=out_dir, check=True)

    parts = sorted(
        str(path)
        for path in archive_path.parent.iterdir()
        if path.name == archive_path.name or path.name.startswith(f"{archive_path.stem}.z")
    )
    validation = validate_delivery_package(out_dir, archive_path, split_enabled)
    if not validation["ok"]:
        raise RuntimeError(f"Delivery package validation failed: {validation['error']}")

    if split_enabled:
        instructions = [
            "1. Put the .zip file and all .z01/.z02 parts in the same folder.",
            f"2. Extract from the main file: unzip {archive_path.name}",
            "3. Split packaging does not change PSD content or layers.",
            "4. Every listed part is required. Missing any .z* part makes the package unusable.",
        ]
    else:
        instructions = [
            "1. Extract this zip file directly.",
            f"2. Extract command: unzip {archive_path.name}",
            "3. Compression does not change PSD content or layers.",
        ]
    readme_path.write_text("\n".join(instructions) + "\n", encoding="utf-8")

    return {
        "enabled": True,
        "split": split_enabled,
        "splitSizeMb": split_mb,
        "archive": str(archive_path),
        "parts": parts,
        "deliveryFiles": parts,
        "requiredForExtraction": parts,
        "mustSendAllParts": split_enabled,
        "validation": validation,
        "readme": str(readme_path),
        "extractCommand": f"unzip {archive_path.name}",
    }


def ensure_outputs(out_dir: Path) -> None:
    required = [
        out_dir / "layered-output.psd",
        out_dir / "reverse-preview.png",
        out_dir / "manifest.json",
        out_dir / "scene.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing expected output files: " + ", ".join(missing))


def lark_target_args(delivery_target: dict[str, str]) -> list[str]:
    if delivery_target.get("chat_id"):
        return ["--chat-id", delivery_target["chat_id"]]
    if delivery_target.get("user_id"):
        return ["--user-id", delivery_target["user_id"]]
    return []


def send_file_to_feishu(path: Path, delivery_target: dict[str, str], *, kind: str) -> dict[str, object]:
    target_args = lark_target_args(delivery_target)
    if not target_args:
        return {"ok": False, "path": str(path), "kind": kind, "error": "missing_delivery_target"}

    npx_cmd = "npx.cmd" if sys.platform.startswith("win") else "npx"
    media_flag = "--image" if kind == "image" else "--file"
    cmd = [
        npx_cmd,
        "-y",
        "lark-cli",
        "im",
        "+messages-send",
        "--as",
        "bot",
        *target_args,
        media_flag,
        str(path),
        "--idempotency-key",
        f"omni-{uuid.uuid4().hex}",
    ]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=240, stdin=subprocess.DEVNULL)
    return {
        "ok": result.returncode == 0,
        "path": str(path),
        "kind": kind,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def send_delivery_outputs(out_dir: Path, package_info: dict[str, object] | None, delivery_target: dict[str, str], send_preview: bool) -> dict[str, object]:
    if not delivery_target.get("target"):
        return {
            "attempted": False,
            "status": "pending_target_resolution",
            "error": "missing_delivery_target",
            "target": delivery_target,
            "sent": [],
        }

    send_items: list[tuple[Path, str]] = []
    preview_path = out_dir / "reverse-preview.png"
    if send_preview and preview_path.exists():
        send_items.append((preview_path, "image"))

    if package_info:
        for item in package_info.get("deliveryFiles", []):
            send_items.append((Path(str(item)), "file"))

    sent = [send_file_to_feishu(path, delivery_target, kind=kind) for path, kind in send_items]
    ok = bool(sent) and all(item.get("ok") for item in sent)
    return {
        "attempted": True,
        "status": "sent" if ok else "failed",
        "error": "" if ok else "send_failed",
        "target": delivery_target,
        "sent": sent,
    }


def write_summary(
    out_dir: Path,
    source: str,
    package_info: dict[str, object] | None,
    delivery_target: dict[str, str],
    send_result: dict[str, object] | None,
) -> Path:
    summary_path = out_dir / "result-summary.json"
    payload = {
        "status": "success",
        "source": source,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "paths": {
            "outDir": str(out_dir),
            "psd": str(out_dir / "layered-output.psd"),
            "preview": str(out_dir / "reverse-preview.png"),
            "manifest": str(out_dir / "manifest.json"),
            "scene": str(out_dir / "scene.json"),
        },
        "delivery": {
            "kind": "111omni-n-layer-psd",
            "message": "Original 111omni extraction logic with Mac runtime path adaptation.",
            "target": delivery_target,
            "sendResult": send_result or {
                "attempted": False,
                "status": "not_attempted",
                "error": "",
                "target": delivery_target,
                "sent": [],
            },
        },
    }
    if package_info:
        payload["deliveryPackage"] = package_info
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path


def main() -> int:
    args = parse_args()
    out_dir = build_out_dir(args.out_dir)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    delivery_target = resolve_delivery_target(
        feishu_target=args.feishu_target,
        feishu_user_id=args.feishu_user_id,
        feishu_chat_id=args.feishu_chat_id,
        feishu_account_id=args.feishu_account_id,
        source_session_key=args.source_session_key,
    )

    env = load_runtime_env()
    cmd = build_pipeline_command(args, out_dir)
    print("[Delivery] Starting 111omni pipeline...")
    print(f"[Delivery] Output directory: {out_dir}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        return result.returncode

    ensure_outputs(out_dir)
    package_info = None
    if not args.no_package:
        package_info = make_delivery_package(out_dir, args.package_split_mb)
    send_result = None
    if not args.no_send and delivery_target.get("target"):
        send_result = send_delivery_outputs(out_dir, package_info, delivery_target, send_preview=not args.no_send_preview)
    summary_path = write_summary(out_dir, args.source, package_info, delivery_target, send_result)

    print(f"[Delivery] PSD: {out_dir / 'layered-output.psd'}")
    print(f"[Delivery] Preview: {out_dir / 'reverse-preview.png'}")
    if package_info:
        print(f"[Delivery] Package: {package_info['archive']}")
        print(f"[Delivery] Package Parts: {len(package_info['parts'])}")
        print("[Delivery] Required files to send together:")
        for file_path in package_info["deliveryFiles"]:
            print(f"  - {file_path}")
    if send_result:
        print(f"[Delivery] Feishu send status: {send_result['status']} target={delivery_target['target']}")
    print(f"[Delivery] Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
