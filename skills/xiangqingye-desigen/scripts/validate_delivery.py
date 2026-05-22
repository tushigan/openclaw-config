#!/usr/bin/env python3
"""最终交付前检核：只打包确认过的最终稿，并生成交付清单。"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

IMAGE_LIMIT = 10 * 1024 * 1024
FILE_LIMIT = 30 * 1024 * 1024


def read_progress(project_dir: Path) -> dict:
    progress_path = project_dir / "progress.json"
    if not progress_path.exists():
        return {}
    return json.loads(progress_path.read_text(encoding="utf-8"))


def workflow_flags(progress: dict) -> dict:
    flags = progress.setdefault("workflow_flags", {})
    flags.setdefault("head_images_required", True)
    flags.setdefault("head_images_generated", False)
    flags.setdefault("delivery_mode", "zip_file")
    flags.setdefault("delivery_ready", False)
    flags.setdefault("delivery_packaged", False)
    flags.setdefault("delivered", False)
    return flags


def size_info(path: Path) -> dict:
    size = path.stat().st_size
    return {
        "path": str(path),
        "size_bytes": size,
        "size_mb": round(size / 1024 / 1024, 2),
    }


def latest_version_dir(base: Path) -> Optional[Path]:
    if not base.exists():
        return None
    versions = [p for p in base.iterdir() if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit()]
    if not versions:
        return base
    return sorted(versions, key=lambda p: int(p.name[1:]))[-1]


def collect(project_dir: Path, head_images_required: bool = True) -> tuple[list[Path], list[str], list[str], dict]:
    files = []
    missing = []
    warnings = []
    details = {
        "head_images_required": head_images_required,
        "head_images_found": 0,
        "delivery_blockers": [],
    }

    design_dir = latest_version_dir(project_dir / "设计")
    if design_dir:
        merged = design_dir / "merged_final.png"
        if merged.exists():
            files.append(merged)
        else:
            missing.append("完整拼接长图 merged_final.png")
        segments = sorted(design_dir.glob("segment_*.png"))
        if segments:
            files.extend(segments)
        else:
            missing.append("最终分段高清图 segment_*.png")
        report = design_dir / "boundary_check_report.json"
        if report.exists():
            files.append(report)
        else:
            warnings.append("未找到分段边界检查报告 boundary_check_report.json")
    else:
        missing.append("设计目录/最终设计版本")

    head_dir = latest_version_dir(project_dir / "头图")
    if head_dir:
        heads = sorted(head_dir.glob("head_*.png"))
        if heads:
            files.extend(heads)
            details["head_images_found"] = len(heads)
        elif head_images_required:
            missing.append("头图 head_*.png")
        else:
            warnings.append("头图目录存在但未找到 head_*.png")
    elif head_images_required:
        missing.append("头图版本/最终头图")
    else:
        warnings.append("未找到头图版本；当前项目配置为不要求头图")

    for rel in ["facts.json", "asset_registry.json", "platform_profile.json", "category_profile.json", "策划/strategy_v1.md", "策划/copywriting_v1.md"]:
        path = project_dir / rel
        if path.exists():
            files.append(path)
        else:
            warnings.append(f"未找到辅助交付/归档文件: {rel}")

    unique = []
    seen = set()
    for path in files:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    details["delivery_blockers"] = list(missing)
    return unique, missing, warnings, details


def main():
    parser = argparse.ArgumentParser(description="最终交付前检核")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--allow-missing", action="store_true", help="允许缺失关键交付物，仅生成警告")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        raise SystemExit(f"项目目录不存在: {project_dir}")

    progress = read_progress(project_dir)
    flags = workflow_flags(progress)
    files, missing, warnings, details = collect(project_dir, flags.get("head_images_required", True))
    deliver_dir = project_dir / "交付"
    deliver_dir.mkdir(exist_ok=True)

    file_infos = [size_info(path) for path in files if path.exists()]
    image_over_limit = [info for info in file_infos if Path(info["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and info["size_bytes"] > IMAGE_LIMIT]

    manifest = {
        "project": project_dir.name,
        "checked_at": datetime.now().isoformat(),
        "passed": not missing or args.allow_missing,
        "missing_required": missing,
        "warnings": warnings,
        "head_images_required": details["head_images_required"],
        "head_images_found": details["head_images_found"],
        "delivery_blockers": details["delivery_blockers"],
        "files": file_infos,
        "feishu_limits": {
            "image_limit_mb": 10,
            "file_limit_mb": 30,
            "zip_split_threshold_mb": 28,
            "rule": "图片超过 10MB 不直接发图；文件超过 30MB 必须分卷；最终图保持高清无损，靠 ZIP/分卷解决发送限制。",
        },
        "image_over_10mb": image_over_limit,
        "next_action": "运行 deliver_package.sh 打包" if (not missing or args.allow_missing) else "先补齐缺失项，或询问用户是否按现状交付",
    }

    manifest_path = deliver_dir / "deliver_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"交付检核清单: {manifest_path}")

    if missing:
        print("缺少关键交付物:")
        for item in missing:
            print(f"- {item}")
        if not args.allow_missing:
            raise SystemExit(1)

    for warning in warnings:
        print(f"提醒: {warning}")
    if image_over_limit:
        print("提醒: 存在超过 10MB 的图片，必须通过文件/ZIP 发送，不能直接发图。")

    print("PASS: 交付检核完成")


if __name__ == "__main__":
    main()
