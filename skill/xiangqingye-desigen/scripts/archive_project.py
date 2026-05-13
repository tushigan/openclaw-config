#!/usr/bin/env python3
"""项目结束后的归档整理：保留最终稿，移动过程稿。"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

KEEP_NAMES = {
    "facts.json",
    "asset_registry.json",
    "platform_profile.json",
    "category_profile.json",
    "style_guide.png",
}
KEEP_DIRS = {"交付"}


def safe_move(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        stem = dst.stem
        suffix = dst.suffix
        dst = dst.with_name(f"{stem}_{datetime.now().strftime('%H%M%S')}{suffix}")
    shutil.move(str(src), str(dst))


def main():
    parser = argparse.ArgumentParser(description="整理已结束项目")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--archive-dir", default="", help="过程稿归档目录，默认 项目目录/过程稿归档")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不移动文件")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        raise SystemExit(f"项目目录不存在: {project_dir}")

    archive_dir = Path(args.archive_dir) if args.archive_dir else project_dir / "过程稿归档"
    moves = []

    for child in project_dir.iterdir():
        if child.name in KEEP_NAMES or child.name in KEEP_DIRS or child.name == archive_dir.name:
            continue
        if child.name in {"设计", "头图", "策划"}:
            continue
        if child.name == "手稿" or child.name == "参考":
            moves.append((child, archive_dir / child.name))

    report = {
        "project": project_dir.name,
        "archive_dir": str(archive_dir),
        "dry_run": args.dry_run,
        "moves": [{"from": str(src), "to": str(dst)} for src, dst in moves],
        "kept": sorted(list(KEEP_NAMES | KEEP_DIRS | {"设计", "头图", "策划"})),
        "rule": "仅在用户确认项目结束后执行；保留最终稿、交付包和核心项目文件，过程稿移动到归档目录。",
    }

    report_path = project_dir / "交付" / "project_archive_report.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.dry_run:
        for src, dst in moves:
            safe_move(src, dst)

    print(f"项目整理报告: {report_path}")
    for move in report["moves"]:
        print(f"- {move['from']} -> {move['to']}")
    if args.dry_run:
        print("DRY RUN: 未移动任何文件")


if __name__ == "__main__":
    main()
