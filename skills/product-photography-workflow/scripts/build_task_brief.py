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
    load_task_state,
    read_json,
    relative_to_project,
    resolve_asset_input,
    resolve_project_dir,
    resolve_task_dir,
    summarize_task_assets,
    task_asset_entries_by_role,
    update_task_manifest_entry,
    update_task_state,
    utc_now,
    write_json,
)


def bullet_lines(values: list[str]) -> list[str]:
    return [f"- {item}" for item in values] or ["- 无"]


def base_image_payload(project_dir: Path, value: str) -> dict[str, str]:
    if not value:
        return {}
    source = resolve_asset_input(value)
    return {
        "path": relative_to_project(project_dir, source),
        "absolute_path": str(source),
        "exists": source.exists(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="构建任务级拍摄简报")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-id", required=True, help="任务 ID 或任务目录")
    parser.add_argument("--task-goal", default="", help="任务目标")
    parser.add_argument("--output-ratio", default="", help="输出比例")
    parser.add_argument("--output-kind", default="detail_page_support", help="输出类型")
    parser.add_argument("--page-draft-note", default="", help="页面草图说明")
    parser.add_argument("--composition-note", default="", help="构图说明")
    parser.add_argument("--scene-note", default="", help="场景说明")
    parser.add_argument("--product-state-note", default="", help="产品状态说明")
    parser.add_argument("--placement-note", default="", help="产品摆放/留白说明")
    parser.add_argument("--execution-mode", default="whole_image", choices=["whole_image", "local_edit"], help="任务执行模式")
    parser.add_argument("--base-image", default="", help="局部编辑母版图")
    parser.add_argument("--editable-target", action="append", default=[], help="允许改动的局部目标")
    parser.add_argument("--immutable-element", action="append", default=[], help="必须保持不变的元素")
    parser.add_argument("--anchor-object", action="append", default=[], help="空间锚点")
    parser.add_argument("--spatial-relation", action="append", default=[], help="必须保持的空间关系")
    parser.add_argument("--must-show", action="append", default=[], help="必须出现")
    parser.add_argument("--must-avoid", action="append", default=[], help="必须避免")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    task_dir = resolve_task_dir(project_dir, args.task_id)
    task_state = load_task_state(task_dir)
    task_assets = read_json(task_dir / "task_assets.json", {})
    product_profile = read_json(project_dir / "product_profile.json", {})
    summary = summarize_task_assets(task_assets)
    execution_mode = args.execution_mode or "whole_image"
    base_image = base_image_payload(project_dir, args.base_image)
    if execution_mode == "local_edit" and not base_image:
        raise SystemExit("local_edit 模式必须提供 --base-image。")

    brief = {
        "version": "1.1",
        "project_id": task_state["project_id"],
        "task_id": task_state["task_id"],
        "task_name": task_state["task_name"],
        "task_type": task_state["task_type"],
        "created_at": read_json(task_dir / "task_brief.json", {}).get("created_at", utc_now()),
        "updated_at": utc_now(),
        "status": "draft_ready_for_confirmation",
        "goal": args.task_goal or task_state.get("goal", ""),
        "output_kind": args.output_kind,
        "output_ratio": args.output_ratio or task_state.get("output_ratio", ""),
        "page_draft_note": args.page_draft_note,
        "composition_note": args.composition_note,
        "scene_note": args.scene_note,
        "product_state_note": args.product_state_note,
        "placement_note": args.placement_note,
        "execution_mode": execution_mode,
        "base_image": base_image,
        "edit_scope": {
            "editable_targets": args.editable_target,
            "immutable_elements": args.immutable_element,
            "anchor_objects": args.anchor_object,
            "spatial_relations": args.spatial_relation,
        },
        "must_show": args.must_show,
        "must_avoid": args.must_avoid,
        "references_summary": summary,
        "reference_roles_present": summary.get("distinct_roles", []),
        "product_constraints_snapshot": {
            "product_name": product_profile.get("product_name", ""),
            "outer_shape": product_profile.get("outer_shape", ""),
            "structure_type": product_profile.get("structure_type", ""),
            "cross_section_required": product_profile.get("cross_section_required", False),
            "cross_section_state": product_profile.get("cross_section_state", ""),
            "filling_type": product_profile.get("filling_type", ""),
            "filling_texture": product_profile.get("filling_texture", ""),
            "must_show_details": product_profile.get("must_show_details", []),
            "must_not_fake_details": product_profile.get("must_not_fake_details", []),
            "deformation_rules": product_profile.get("deformation_rules", []),
        },
        "reference_paths": {
            "page_draft": [item["absolute_path"] for item in task_asset_entries_by_role(task_assets, ["page_draft"])],
            "composition_reference": [item["absolute_path"] for item in task_asset_entries_by_role(task_assets, ["composition_reference"])],
            "scene_reference": [item["absolute_path"] for item in task_asset_entries_by_role(task_assets, ["scene_reference"])],
            "style_reference": [item["absolute_path"] for item in task_asset_entries_by_role(task_assets, ["style_reference"])],
            "lighting_reference": [item["absolute_path"] for item in task_asset_entries_by_role(task_assets, ["lighting_reference"])],
            "product_state_reference": [item["absolute_path"] for item in task_asset_entries_by_role(task_assets, ["product_state_reference"])],
            "other_reference": [item["absolute_path"] for item in task_asset_entries_by_role(task_assets, ["other_reference"])],
        },
        "confirmation": {},
    }
    write_json(task_dir / "task_brief.json", brief)

    report_lines = [
        f"# 任务简报：{task_state['task_name']}",
        "",
        f"- 任务类型：{task_state['task_type']}",
        f"- 任务目标：{brief['goal'] or '未填'}",
        f"- 输出类型：{args.output_kind}",
        f"- 输出比例：{brief['output_ratio'] or '未填'}",
        f"- 执行模式：{execution_mode}",
        "",
        "## 任务参考图识别",
        *bullet_lines([f"{role}: {summary.get(f'{role}_count', 0)} 张" for role in summary.get("distinct_roles", [])]),
        "",
        "## 页面草图说明",
        *bullet_lines([args.page_draft_note] if args.page_draft_note else []),
        "",
        "## 构图说明",
        *bullet_lines([args.composition_note] if args.composition_note else []),
        "",
        "## 场景说明",
        *bullet_lines([args.scene_note] if args.scene_note else []),
        "",
        "## 产品状态说明",
        *bullet_lines([args.product_state_note] if args.product_state_note else []),
        "",
        "## 摆放/留白说明",
        *bullet_lines([args.placement_note] if args.placement_note else []),
        "",
        "## 局部替换约束",
        *bullet_lines(
            ([f"母版图：{base_image.get('absolute_path', '')}"] if base_image else [])
            + [f"可修改：{item}" for item in args.editable_target]
            + [f"保持不变：{item}" for item in args.immutable_element]
            + [f"锚点：{item}" for item in args.anchor_object]
            + [f"空间关系：{item}" for item in args.spatial_relation]
        ),
        "",
        "## 必须出现",
        *bullet_lines(args.must_show),
        "",
        "## 必须避免",
        *bullet_lines(args.must_avoid),
    ]
    (task_dir / "reports" / "task_summary.md").write_text("\n".join(report_lines), encoding="utf-8")

    update_task_state(
        task_dir,
        current_stage="task_brief_waiting_confirm",
        stage_status="waiting_user",
        workflow_flag_updates={
            "references_classified": bool(summary.get("distinct_roles")),
            "brief_confirmed": False,
            "generation_allowed": False,
        },
        field_updates={
            "goal": brief["goal"],
            "output_ratio": brief["output_ratio"],
        },
    )
    update_task_manifest_entry(
        project_dir,
        task_state["task_id"],
        {
            "status": "waiting_confirmation",
            "output_ratio": brief["output_ratio"],
        },
    )
    append_audit(
        project_dir,
        "task_brief_built",
        {
            "task_id": task_state["task_id"],
            "output_kind": args.output_kind,
            "output_ratio": brief["output_ratio"],
            "execution_mode": execution_mode,
        },
    )
    print(f"task_brief={task_dir / 'task_brief.json'}")


if __name__ == "__main__":
    main()
