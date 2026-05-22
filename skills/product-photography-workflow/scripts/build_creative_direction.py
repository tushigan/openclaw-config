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
    parser = argparse.ArgumentParser(description="构建待确认的创意方向")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--scene-mode", default="studio_white", help="场景模式")
    parser.add_argument("--output-kind", default="white_background_product", help="输出类型")
    parser.add_argument("--output-ratio", default="1:1", help="输出比例")
    parser.add_argument("--draft-count", type=int, default=2, help="首轮候选数量")
    parser.add_argument("--goal", default="premium still-life product photography", help="本轮目标")
    parser.add_argument("--camera-angle", default="", help="镜头角度")
    parser.add_argument("--lighting-note", default="", help="光线说明")
    parser.add_argument("--background-note", default="", help="背景说明")
    parser.add_argument("--composition-note", default="", help="构图说明")
    parser.add_argument("--prop-policy", default="no props unless explicitly requested", help="道具策略")
    parser.add_argument("--human-element-policy", default="no human elements", help="人物策略")
    parser.add_argument("--motion-effect-policy", default="no motion effects", help="动态策略")
    parser.add_argument("--must-keep", action="append", default=[], help="必须保留")
    parser.add_argument("--negative", action="append", default=[], help="负面限制")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    product_profile = read_json(project_dir / "product_profile.json", {})
    reference_analysis = read_json(project_dir / "reference_analysis.json", {})

    direction = {
        "version": "1.0",
        "project_id": read_json(project_dir / "project_state.json", {}).get("project_id", ""),
        "created_at": utc_now(),
        "status": "draft_ready_for_confirmation",
        "scene_mode": args.scene_mode,
        "output_kind": args.output_kind,
        "output_ratio": args.output_ratio,
        "draft_count": args.draft_count,
        "goal": args.goal,
        "camera_angle": args.camera_angle or reference_analysis.get("camera_angle", ""),
        "lighting": args.lighting_note or reference_analysis.get("lighting", ""),
        "background": args.background_note or reference_analysis.get("background", ""),
        "composition": args.composition_note or reference_analysis.get("composition", ""),
        "prop_policy": args.prop_policy,
        "human_element_policy": args.human_element_policy,
        "motion_effect_policy": args.motion_effect_policy,
        "must_keep": args.must_keep,
        "negative_constraints": args.negative,
        "product_constraints": {
            "structure_type": product_profile.get("structure_type", "unknown"),
            "cross_section_required": product_profile.get("cross_section_required", False),
            "filling_type": product_profile.get("filling_type", ""),
            "filling_texture": product_profile.get("filling_texture", ""),
            "deformation_rules": product_profile.get("deformation_rules", []),
            "must_show_details": product_profile.get("must_show_details", []),
            "must_not_fake_details": product_profile.get("must_not_fake_details", []),
        },
        "confirmation_questions": [
            "产品外形和结构理解是否准确？",
            "光线、背景和镜头方向是否符合预期？",
            "是否允许按这一方向进入首轮生图？",
        ],
    }
    write_json(project_dir / "creative_direction.json", direction)

    lines = [
        "# 创意方向确认单",
        "",
        f"- 输出类型：{args.output_kind}",
        f"- 输出比例：{args.output_ratio}",
        f"- 首轮候选数：{args.draft_count}",
        f"- 场景模式：{args.scene_mode}",
        f"- 目标：{args.goal}",
        f"- 镜头角度：{direction['camera_angle']}",
        f"- 光线：{direction['lighting']}",
        f"- 背景：{direction['background']}",
        f"- 构图：{direction['composition']}",
        f"- 道具策略：{args.prop_policy}",
        f"- 人物策略：{args.human_element_policy}",
        f"- 动态策略：{args.motion_effect_policy}",
        "",
        "## 产品硬约束",
        f"- 结构类型：{direction['product_constraints']['structure_type']}",
        f"- 是否必须体现切面：{'是' if direction['product_constraints']['cross_section_required'] else '否'}",
        f"- 夹心类型：{direction['product_constraints']['filling_type'] or '未填'}",
        f"- 夹心质地：{direction['product_constraints']['filling_texture'] or '未填'}",
        "",
        "## 必须保留",
        *bullet_lines(args.must_keep),
        "",
        "## 负面限制",
        *bullet_lines(args.negative),
    ]
    (project_dir / "reports" / "creative_direction.md").write_text("\n".join(lines), encoding="utf-8")

    update_state(
        project_dir,
        current_stage="creative_direction_waiting_confirm",
        stage_status="waiting_user",
        workflow_flag_updates={
            "creative_confirmed": False,
            "generation_allowed": False,
        },
    )
    append_audit(
        project_dir,
        "creative_direction_built",
        {
            "output_ratio": args.output_ratio,
            "draft_count": args.draft_count,
            "scene_mode": args.scene_mode,
        },
    )
    print(f"creative_direction={project_dir / 'creative_direction.json'}")


if __name__ == "__main__":
    main()
