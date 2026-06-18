#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    TASK_ROLE_ORDER,
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


def text_blob(*parts: str) -> str:
    return " ".join((part or "").strip().lower() for part in parts if part).strip()


def role_paths(task_assets: dict) -> dict[str, list[str]]:
    return {
        role: [item["absolute_path"] for item in task_asset_entries_by_role(task_assets, [role])]
        for role in TASK_ROLE_ORDER
    }


def should_require_camera_plan(task_state: dict, product_profile: dict, args: argparse.Namespace) -> bool:
    explicit_output_kinds = {
        "detail_page_hero",
        "main_image",
        "hero_image",
        "kv",
        "key_visual",
    }
    haystack = text_blob(
        task_state.get("task_name", ""),
        task_state.get("task_type", ""),
        args.task_goal,
        args.output_kind,
    )
    keyword_hits = ("主图", "首图", "头图", "hero", "kv", "key visual", "cover")
    return (
        args.output_kind in explicit_output_kinds
        or any(keyword in haystack for keyword in keyword_hits)
        or product_profile.get("hero_image_required", False)
    )


def should_require_texture_plan(task_state: dict, product_profile: dict, args: argparse.Namespace) -> bool:
    haystack = text_blob(
        task_state.get("task_name", ""),
        task_state.get("task_type", ""),
        args.task_goal,
        args.output_kind,
        args.product_state_note,
        product_profile.get("category", ""),
        product_profile.get("structure_type", ""),
        product_profile.get("cross_section_state", ""),
        product_profile.get("filling_type", ""),
    )
    texture_keywords = (
        "面包",
        "饼干",
        "蛋糕",
        "夹心",
        "切面",
        "断面",
        "微距",
        "cross-section",
        "cross section",
        "filled",
        "baked",
        "烘焙",
        "food",
        "食品",
        "食物",
    )
    return (
        bool(product_profile.get("cross_section_required"))
        or bool(product_profile.get("filling_type"))
        or any(keyword in haystack for keyword in texture_keywords)
    )


def should_require_package_material_plan(
    task_state: dict,
    product_profile: dict,
    args: argparse.Namespace,
    summary: dict,
) -> bool:
    haystack = text_blob(
        task_state.get("task_name", ""),
        task_state.get("task_type", ""),
        args.task_goal,
        args.output_kind,
        args.product_state_note,
        args.scene_note,
        product_profile.get("category", ""),
        product_profile.get("outer_shape", ""),
        product_profile.get("surface_finish", ""),
    )
    package_keywords = (
        "包装",
        "包材",
        "袋",
        "盒",
        "纸盒",
        "纸袋",
        "膜",
        "铝膜",
        "铝箔",
        "塑料",
        "哑膜",
        "亮膜",
        "磨砂",
        "热封",
        "封边",
    )
    return bool(summary.get("package_material_reference_count", 0)) or any(keyword in haystack for keyword in package_keywords)


def build_camera_plan(args: argparse.Namespace) -> dict[str, object]:
    return {
        "hero_shot_intent": args.hero_shot_intent,
        "shot_priority": args.shot_priority,
        "camera_angle_lock": args.camera_angle_lock,
        "crop_and_whitespace_lock": args.crop_and_whitespace_lock,
        "lighting_direction_lock": args.lighting_direction_lock,
        "focus_anchor": args.focus_anchor,
    }


def build_texture_plan(args: argparse.Namespace) -> dict[str, object]:
    return {
        "texture_priority": args.texture_priority,
        "must_match_texture_points": args.must_match_texture_point,
        "cross_section_truth_lock": args.cross_section_truth_lock,
        "surface_finish_lock": args.surface_finish_lock,
        "fake_texture_risks": args.fake_texture_risk,
    }


def build_package_material_plan(args: argparse.Namespace) -> dict[str, object]:
    return {
        "package_material_priority": args.package_material_priority,
        "material_type_lock": args.package_material_type_lock,
        "finish_lock": args.package_finish_lock,
        "structure_detail_lock": args.package_structure_detail_lock,
        "reflection_lock": args.package_reflection_lock,
        "fake_package_material_risks": args.fake_package_material_risk,
    }


def missing_camera_plan_fields(camera_plan: dict[str, object]) -> list[str]:
    required = {
        "hero_shot_intent": "hero_shot_intent",
        "shot_priority": "shot_priority",
        "camera_angle_lock": "camera_angle_lock",
        "crop_and_whitespace_lock": "crop_and_whitespace_lock",
        "lighting_direction_lock": "lighting_direction_lock",
        "focus_anchor": "focus_anchor",
    }
    missing = []
    for key, label in required.items():
        value = camera_plan.get(key)
        if isinstance(value, list):
            if not value:
                missing.append(label)
        elif not value:
            missing.append(label)
    return missing


def missing_texture_plan_fields(texture_plan: dict[str, object]) -> list[str]:
    required = {
        "texture_priority": "texture_priority",
        "must_match_texture_points": "must_match_texture_points",
        "cross_section_truth_lock": "cross_section_truth_lock",
        "surface_finish_lock": "surface_finish_lock",
        "fake_texture_risks": "fake_texture_risks",
    }
    missing = []
    for key, label in required.items():
        value = texture_plan.get(key)
        if isinstance(value, list):
            if not value:
                missing.append(label)
        elif not value:
            missing.append(label)
    return missing


def missing_package_material_plan_fields(package_material_plan: dict[str, object]) -> list[str]:
    required = {
        "package_material_priority": "package_material_priority",
        "material_type_lock": "material_type_lock",
        "finish_lock": "finish_lock",
        "structure_detail_lock": "structure_detail_lock",
        "reflection_lock": "reflection_lock",
        "fake_package_material_risks": "fake_package_material_risks",
    }
    missing = []
    for key, label in required.items():
        value = package_material_plan.get(key)
        if isinstance(value, list):
            if not value:
                missing.append(label)
        elif not value:
            missing.append(label)
    return missing


def build_planning_warnings(
    *,
    require_camera_plan: bool,
    require_texture_plan: bool,
    require_package_material_plan: bool,
    camera_plan: dict[str, object],
    texture_plan: dict[str, object],
    package_material_plan: dict[str, object],
) -> list[str]:
    warnings: list[str] = []
    if require_camera_plan:
        missing = missing_camera_plan_fields(camera_plan)
        if missing:
            warnings.append(
                "camera_plan 缺失关键字段："
                + ", ".join(missing)
                + "。当前任务涉及主图/首图类输出，若不补角度故事板或对应计划，机位、裁切、留白和主光方向存在跑偏风险。"
            )
    if require_texture_plan:
        missing = missing_texture_plan_fields(texture_plan)
        if missing:
            warnings.append(
                "texture_plan 缺失关键字段："
                + ", ".join(missing)
                + "。当前任务涉及食物切面或材质真相，若不补质感身份板或对应计划，孔洞、夹心、断裂边和表面质感容易变假。"
            )
    if require_package_material_plan:
        missing = missing_package_material_plan_fields(package_material_plan)
        if missing:
            warnings.append(
                "package_material_plan 缺失关键字段："
                + ", ".join(missing)
                + "。当前任务涉及包装或包材材质，若不补包材材质身份板或对应计划，膜感、反光、封边和厚薄挺度容易跑偏。"
            )
    return warnings


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
    parser.add_argument("--hero-shot-intent", default="", help="主图镜头意图")
    parser.add_argument("--shot-priority", action="append", default=[], help="镜头优先级")
    parser.add_argument("--camera-angle-lock", default="", help="机位锁定说明")
    parser.add_argument("--crop-and-whitespace-lock", default="", help="裁切与留白锁定说明")
    parser.add_argument("--lighting-direction-lock", default="", help="主光方向锁定说明")
    parser.add_argument("--focus-anchor", default="", help="焦点锚点")
    parser.add_argument("--texture-priority", action="append", default=[], help="质感优先级")
    parser.add_argument("--must-match-texture-point", action="append", default=[], help="必须匹配的质感点")
    parser.add_argument("--cross-section-truth-lock", default="", help="切面真相锁定说明")
    parser.add_argument("--surface-finish-lock", default="", help="表面完成度锁定说明")
    parser.add_argument("--fake-texture-risk", action="append", default=[], help="假质感风险")
    parser.add_argument("--package-material-priority", action="append", default=[], help="包材材质优先级")
    parser.add_argument("--package-material-type-lock", default="", help="包材类型锁定说明")
    parser.add_argument("--package-finish-lock", default="", help="包材表面完成度锁定说明")
    parser.add_argument("--package-structure-detail-lock", default="", help="包材结构细节锁定说明")
    parser.add_argument("--package-reflection-lock", default="", help="包材反光方式锁定说明")
    parser.add_argument("--fake-package-material-risk", action="append", default=[], help="假包材风险")
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
    camera_plan = build_camera_plan(args)
    texture_plan = build_texture_plan(args)
    package_material_plan = build_package_material_plan(args)
    planning_warnings = build_planning_warnings(
        require_camera_plan=should_require_camera_plan(task_state, product_profile, args),
        require_texture_plan=should_require_texture_plan(task_state, product_profile, args),
        require_package_material_plan=should_require_package_material_plan(task_state, product_profile, args, summary),
        camera_plan=camera_plan,
        texture_plan=texture_plan,
        package_material_plan=package_material_plan,
    )
    camera_preview_required = execution_mode != "local_edit"
    if execution_mode == "local_edit" and not base_image:
        raise SystemExit("local_edit 模式必须提供 --base-image。")

    brief = {
        "version": "1.4",
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
        "camera_preview_required": camera_preview_required,
        "camera_plan": camera_plan,
        "texture_plan": texture_plan,
        "package_material_plan": package_material_plan,
        "planning_warnings": planning_warnings,
        "product_constraints_snapshot": {
            "product_name": product_profile.get("product_name", ""),
            "category": product_profile.get("category", ""),
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
        "reference_paths": role_paths(task_assets),
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
        "## 机位定稿计划",
        *bullet_lines(
            ([f"主图意图：{camera_plan['hero_shot_intent']}"] if camera_plan["hero_shot_intent"] else [])
            + [f"镜头优先级：{item}" for item in camera_plan["shot_priority"]]
            + ([f"机位锁定：{camera_plan['camera_angle_lock']}"] if camera_plan["camera_angle_lock"] else [])
            + ([f"裁切与留白：{camera_plan['crop_and_whitespace_lock']}"] if camera_plan["crop_and_whitespace_lock"] else [])
            + ([f"主光方向：{camera_plan['lighting_direction_lock']}"] if camera_plan["lighting_direction_lock"] else [])
            + ([f"焦点锚点：{camera_plan['focus_anchor']}"] if camera_plan["focus_anchor"] else [])
        ),
        "",
        "## 机位定稿规则",
        *bullet_lines(
            ["当前任务必须先生成并确认机位定稿图，再允许进入最终生图。"]
            if camera_preview_required
            else ["当前任务为局部替换模式，可跳过机位定稿图流程。"]
        ),
        "",
        "## 质感身份板计划",
        *bullet_lines(
            [f"质感优先级：{item}" for item in texture_plan["texture_priority"]]
            + [f"必须匹配：{item}" for item in texture_plan["must_match_texture_points"]]
            + ([f"切面真相锁定：{texture_plan['cross_section_truth_lock']}"] if texture_plan["cross_section_truth_lock"] else [])
            + ([f"表面完成度锁定：{texture_plan['surface_finish_lock']}"] if texture_plan["surface_finish_lock"] else [])
            + [f"假质感风险：{item}" for item in texture_plan["fake_texture_risks"]]
        ),
        "",
        "## 包材材质身份板计划",
        *bullet_lines(
            [f"包材优先级：{item}" for item in package_material_plan["package_material_priority"]]
            + ([f"包材类型锁定：{package_material_plan['material_type_lock']}"] if package_material_plan["material_type_lock"] else [])
            + ([f"包材表面完成度：{package_material_plan['finish_lock']}"] if package_material_plan["finish_lock"] else [])
            + ([f"包材结构细节：{package_material_plan['structure_detail_lock']}"] if package_material_plan["structure_detail_lock"] else [])
            + ([f"包材反光方式：{package_material_plan['reflection_lock']}"] if package_material_plan["reflection_lock"] else [])
            + [f"假包材风险：{item}" for item in package_material_plan["fake_package_material_risks"]]
        ),
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
        "",
        "## 规划提醒",
        *bullet_lines(planning_warnings),
    ]
    (task_dir / "reports" / "task_summary.md").write_text("\n".join(report_lines), encoding="utf-8")

    update_task_state(
        task_dir,
        current_stage="task_brief_waiting_confirm",
        stage_status="waiting_user",
        workflow_flag_updates={
            "references_classified": bool(summary.get("distinct_roles")),
            "brief_confirmed": False,
            "camera_preview_required": camera_preview_required,
            "camera_preview_confirmed": False,
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
