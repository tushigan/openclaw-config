#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
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
    return parser.parse_args()


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
    if split_enabled:
        instructions = [
            "1. Put the .zip file and all .z01/.z02 parts in the same folder.",
            f"2. Extract from the main file: unzip {archive_path.name}",
            "3. Split packaging does not change PSD content or layers.",
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


def write_summary(out_dir: Path, source: str, package_info: dict[str, object] | None) -> Path:
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
    summary_path = write_summary(out_dir, args.source, package_info)

    print(f"[Delivery] PSD: {out_dir / 'layered-output.psd'}")
    print(f"[Delivery] Preview: {out_dir / 'reverse-preview.png'}")
    if package_info:
        print(f"[Delivery] Package: {package_info['archive']}")
        print(f"[Delivery] Package Parts: {len(package_info['parts'])}")
    print(f"[Delivery] Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
