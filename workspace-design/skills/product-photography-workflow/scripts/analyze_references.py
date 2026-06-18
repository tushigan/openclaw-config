#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    append_audit,
    read_json,
    resolve_project_dir,
    update_state,
    utc_now,
    write_json,
)


def bullet_lines(values: list[str]) -> list[str]:
    return [f"- {item}" for item in values] or ["- 无"]


def main() -> None:
    parser = argparse.ArgumentParser(description="整理参考图风格结论")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--style-note", action="append", default=[], help="总体风格描述")
    parser.add_argument("--composition", default="clean product-focused still life with negative space", help="构图结论")
    parser.add_argument("--lighting", default="soft commercial light", help="光线结论")
    parser.add_argument("--background", default="clean minimal background", help="背景结论")
    parser.add_argument("--camera-angle", default="slightly elevated product angle", help="镜头角度")
    parser.add_argument("--retouch-level", default="polished but realistic", help="修图强度")
    parser.add_argument("--mood", default="premium, clean, appetizing", help="气质")
    parser.add_argument("--borrow-only", action="append", default=[], help="只借鉴什么")
    parser.add_argument("--avoid", action="append", default=[], help="要避开什么")
    parser.add_argument("--scene-mode", default="studio_white", help="推荐场景模式")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    assets_manifest = read_json(project_dir / "assets_manifest.json", {})
    reference_assets = assets_manifest.get("reference_assets", [])

    analysis = {
        "version": "1.0",
        "project_id": read_json(project_dir / "project_state.json", {}).get("project_id", ""),
        "created_at": utc_now(),
        "scene_mode_recommendation": args.scene_mode,
        "style_notes": args.style_note,
        "composition": args.composition,
        "lighting": args.lighting,
        "background": args.background,
        "camera_angle": args.camera_angle,
        "retouch_level": args.retouch_level,
        "mood": args.mood,
        "borrow_only": args.borrow_only,
        "avoid": args.avoid,
        "reference_assets": [
            {
                "role": item.get("role", ""),
                "path": item.get("path", ""),
            }
            for item in reference_assets
        ],
    }
    write_json(project_dir / "reference_analysis.json", analysis)

    lines = [
        "# 参考风格总结",
        "",
        f"- 推荐场景模式：{args.scene_mode}",
        f"- 构图：{args.composition}",
        f"- 光线：{args.lighting}",
        f"- 背景：{args.background}",
        f"- 镜头角度：{args.camera_angle}",
        f"- 修图强度：{args.retouch_level}",
        f"- 气质：{args.mood}",
        "",
        "## 风格摘要",
        *bullet_lines(args.style_note),
        "",
        "## 只借鉴",
        *bullet_lines(args.borrow_only),
        "",
        "## 明确避免",
        *bullet_lines(args.avoid),
    ]
    (project_dir / "reports" / "reference_summary.md").write_text("\n".join(lines), encoding="utf-8")

    update_state(
        project_dir,
        current_stage="reference_analysis_ready",
        stage_status="ready",
    )
    append_audit(
        project_dir,
        "reference_analysis_built",
        {
            "reference_count": len(reference_assets),
            "scene_mode": args.scene_mode,
        },
    )
    print(f"reference_analysis={project_dir / 'reference_analysis.json'}")


if __name__ == "__main__":
    main()
