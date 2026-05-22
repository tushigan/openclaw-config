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
    resolve_project_dir,
    resolve_task_dir,
    task_asset_entries_by_role,
    update_state,
    update_task_manifest_entry,
    update_task_state,
    utc_now,
    write_json,
)


def bullet_lines(values: list[str], empty: str = "- none") -> list[str]:
    return [f"- {item}" for item in values if item] or [empty]


def local_edit_prompt_lines(task_brief: dict) -> list[str]:
    if (task_brief.get("execution_mode") or "whole_image") != "local_edit":
        return []
    base_image = task_brief.get("base_image", {})
    edit_scope = task_brief.get("edit_scope", {})
    base_path = base_image.get("absolute_path", "")
    if not base_path:
        raise SystemExit("local_edit 模式缺少 base_image.absolute_path，不能组装 prompt。")
    return [
        "Scene-locked local edit mode:",
        f"- Base image authority: {base_path}",
        "- Preserve every region of the base image that is not explicitly listed under Editable targets.",
        "Immutable elements:",
        *bullet_lines(edit_scope.get("immutable_elements", [])),
        "Editable targets:",
        *bullet_lines(edit_scope.get("editable_targets", [])),
        "Anchor objects:",
        *bullet_lines(edit_scope.get("anchor_objects", [])),
        "Spatial relation locks:",
        *bullet_lines(edit_scope.get("spatial_relations", [])),
    ]


def build_project_prompt(
    product: dict,
    ref: dict,
    direction: dict,
    custom_constraints: list[str],
) -> tuple[str, str]:
    negatives = list(direction.get("negative_constraints", [])) + custom_constraints + list(product.get("must_not_fake_details", []))
    prompt_lines = [
        f"Create a premium commercial still-life product photograph for {product.get('product_name', 'the product')}.",
        "",
        "Product fidelity requirements:",
        f"- Preserve the real outer shape: {product.get('outer_shape') or 'follow the product references faithfully'}",
        f"- Structure type: {product.get('structure_type', 'unknown')}",
        f"- Open/close state: {product.get('open_close_states', 'closed')}",
        f"- Cross-section required: {'yes' if product.get('cross_section_required') else 'no'}",
        f"- Cross-section state: {product.get('cross_section_state', 'not specified')}",
        f"- Filling type: {product.get('filling_type') or 'not specified'}",
        f"- Filling texture: {product.get('filling_texture') or 'not specified'}",
        f"- Filling flow level: {product.get('filling_flow_level') or 'not specified'}",
        f"- Shell texture: {product.get('shell_texture') or 'not specified'}",
        f"- Surface finish: {product.get('surface_finish') or 'not specified'}",
        "",
        "Visual direction:",
        f"- Goal: {direction.get('goal', 'premium still-life product photography')}",
        f"- Scene mode: {direction.get('scene_mode', 'studio_white')}",
        f"- Composition: {direction.get('composition', '')}",
        f"- Camera angle: {direction.get('camera_angle', '')}",
        f"- Lighting: {direction.get('lighting', '')}",
        f"- Background: {direction.get('background', '')}",
        f"- Mood: {ref.get('mood', '')}",
        f"- Retouch level: {ref.get('retouch_level', '')}",
        "",
        "Hard detail requirements:",
    ]
    for item in product.get("must_show_details", []):
        prompt_lines.append(f"- {item}")
    for item in product.get("deformation_rules", []):
        prompt_lines.append(f"- Do not break this rule: {item}")
    for item in product.get("key_identifiers", []):
        prompt_lines.append(f"- Preserve this identifier: {item}")
    if product.get("material_notes"):
        prompt_lines.append("- Material notes: " + "; ".join(product["material_notes"]))
    if product.get("color_notes"):
        prompt_lines.append("- Color notes: " + "; ".join(product["color_notes"]))
    if ref.get("borrow_only"):
        prompt_lines.append("- Style reference may borrow only: " + "; ".join(ref["borrow_only"]))
    if direction.get("must_keep"):
        prompt_lines.append("- Must keep: " + "; ".join(direction["must_keep"]))
    if direction.get("human_element_policy"):
        prompt_lines.append(f"- Human elements policy: {direction['human_element_policy']}")
    if direction.get("prop_policy"):
        prompt_lines.append(f"- Prop policy: {direction['prop_policy']}")
    if direction.get("motion_effect_policy"):
        prompt_lines.append(f"- Motion policy: {direction['motion_effect_policy']}")

    negative_text = "\n".join(f"- {item}" for item in negatives if item)
    prompt_lines.extend(
        [
            "",
            "Negative constraints:",
            negative_text or "- none",
            "",
            "Use the product reference images to keep anatomy, structure, thickness, material, and color identity faithful.",
            "Use the style reference images only for lighting, palette, atmosphere, and composition language.",
        ]
    )
    return "\n".join(prompt_lines).strip() + "\n", negative_text + ("\n" if negative_text else "")


def build_task_prompt(
    *,
    product: dict,
    ref: dict,
    task_state: dict,
    task_brief: dict,
    task_assets: dict,
    custom_constraints: list[str],
) -> tuple[str, str]:
    negatives = list(task_brief.get("must_avoid", [])) + custom_constraints + list(product.get("must_not_fake_details", []))
    must_show = list(task_brief.get("must_show", [])) + list(product.get("must_show_details", []))
    execution_mode = task_brief.get("execution_mode") or "whole_image"
    reference_paths = task_brief.get("reference_paths", {})
    page_draft_refs = reference_paths.get("page_draft", [])
    composition_refs = reference_paths.get("composition_reference", [])
    scene_refs = reference_paths.get("scene_reference", [])
    style_refs = reference_paths.get("style_reference", [])
    lighting_refs = reference_paths.get("lighting_reference", [])
    state_refs = reference_paths.get("product_state_reference", [])
    other_refs = reference_paths.get("other_reference", [])
    active_layout_refs = 1 if composition_refs else 0
    style_and_lighting_refs = len(style_refs) + len(lighting_refs)

    prompt_lines = [
        f"Create a premium commercial product photography image for {product.get('product_name', 'the product')}.",
        "",
        "Task intent:",
        f"- Task name: {task_state.get('task_name', '')}",
        f"- Task type: {task_state.get('task_type', '')}",
        f"- Task goal: {task_brief.get('goal') or task_state.get('goal', '') or 'not specified'}",
        f"- Output ratio: {task_brief.get('output_ratio') or task_state.get('output_ratio', '') or 'not specified'}",
        f"- Execution mode: {execution_mode}",
        "",
        "Stable product truth:",
        f"- Preserve the real outer shape: {product.get('outer_shape') or 'follow the product references faithfully'}",
        f"- Structure type: {product.get('structure_type', 'unknown')}",
        f"- Open/close state: {product.get('open_close_states', 'closed')}",
        f"- Cross-section required: {'yes' if product.get('cross_section_required') else 'no'}",
        f"- Cross-section state: {product.get('cross_section_state', 'not specified')}",
        f"- Filling type: {product.get('filling_type') or 'not specified'}",
        f"- Filling texture: {product.get('filling_texture') or 'not specified'}",
        f"- Shell texture: {product.get('shell_texture') or 'not specified'}",
        "",
        "Task-specific direction:",
        f"- Page draft note: {task_brief.get('page_draft_note') or 'none'}",
        f"- Composition note: {task_brief.get('composition_note') or 'none'}",
        f"- Scene note: {task_brief.get('scene_note') or 'none'}",
        f"- Product state note: {task_brief.get('product_state_note') or 'none'}",
        f"- Placement note: {task_brief.get('placement_note') or 'none'}",
        f"- Global lighting language: {ref.get('lighting') or 'follow the strongest style reference'}",
        f"- Global background language: {ref.get('background') or 'match the task references'}",
        f"- Global composition language: {ref.get('composition') or 'match the task references'}",
        "",
    ]
    prompt_lines.extend(local_edit_prompt_lines(task_brief))
    prompt_lines.extend(
        [
            "",
            "Reference authority resolution:",
            "- Product truth authority: Real product photos always win for anatomy, proportions, materials, filling structure, and product identity.",
            *(
                [
                    "- Base image authority: 1 locked base image. Preserve its overall scene, framing, props, and all immutable regions unless the editable target explicitly overrides them."
                ]
                if execution_mode == "local_edit"
                else []
            ),
            f"- Layout authority: {active_layout_refs} active layout reference(s). Use only the most recently registered composition reference for placement, crop, camera angle, and arrangement. Older composition references and page drafts are secondary planning hints only.",
            f"- Style and lighting authority: {style_and_lighting_refs} image(s). Use them only for tone, palette, light direction, retouch feel, and atmosphere. Do not import foreign products, props, packaging, or geometry from them.",
            f"- Scene authority: {len(scene_refs)} image(s). Use them only for environment mood, background treatment, and prop language.",
            f"- Product state authority: {len(state_refs)} image(s). Use them only for open/closed state, cut exposure, filling reveal, and break pattern while keeping the real product anatomy faithful.",
            "",
            "Reference usage policy:",
            f"- Page draft references: {len(page_draft_refs)} image(s); use only for layout blocks, whitespace, and placement hierarchy.",
            f"- Composition references: {len(composition_refs)} image(s); use for camera framing, crop logic, and prop arrangement rhythm only. The newest one is the sole active layout image.",
            f"- Style references: {len(style_refs)} image(s); use only for style language, palette, retouch feel, and visual polish.",
            f"- Lighting references: {len(lighting_refs)} image(s); use only for light direction, contrast rolloff, highlight behavior, and shadow mood.",
            f"- Scene reference images: {len(scene_refs)} image(s); use for environment mood, background treatment, and scene styling only.",
            f"- Product state references: {len(state_refs)} image(s); use for cut-open state, filling exposure, and pose specifics only.",
            f"- Other references: {len(other_refs)} image(s); treat as auxiliary hints only.",
            "- The real product photos remain the single source of truth for anatomy, proportions, materials, and true product identity.",
            "",
            "Must show:",
            *bullet_lines(must_show),
            "",
            "Do not fake:",
            *bullet_lines(product.get("deformation_rules", []) + product.get("must_not_fake_details", [])),
            "",
            "Negative constraints:",
            *bullet_lines(negatives),
            "",
            "Instruction priority:",
            *(
                [
                    "- First preserve the base image scene and every immutable element.",
                    "- Then modify only the editable targets while keeping the listed anchor objects and spatial relations intact.",
                    "- Then keep product truth accurate.",
                    "- Then borrow tone and atmosphere from references without copying foreign products or packaging.",
                ]
                if execution_mode == "local_edit"
                else [
                    "- First keep product truth accurate.",
                    "- Then satisfy the task brief for this image.",
                    "- Then borrow tone and atmosphere from references without copying foreign products or packaging.",
                ]
            ),
        ]
    )
    negative_text = "\n".join(f"- {item}" for item in negatives if item)
    return "\n".join(prompt_lines).strip() + "\n", negative_text + ("\n" if negative_text else "")


def main() -> None:
    parser = argparse.ArgumentParser(description="组装产品摄影生图 prompt")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-id", default="", help="任务 ID 或任务目录；传入时走 V2 任务模式")
    parser.add_argument("--version", default="", help="prompt 版本；任务模式默认使用当前 selected version")
    parser.add_argument("--custom-constraint", action="append", default=[], help="额外负面限制")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    product_profile = read_json(project_dir / "product_profile.json", {})
    reference_analysis = read_json(project_dir / "reference_analysis.json", {})

    if args.task_id:
        task_dir = resolve_task_dir(project_dir, args.task_id)
        task_state = load_task_state(task_dir)
        if not task_state.get("workflow_flags", {}).get("brief_confirmed", False):
            raise SystemExit("task brief 尚未确认，不能组装任务级 prompt。")

        task_brief = read_json(task_dir / "task_brief.json", {})
        task_assets = read_json(task_dir / "task_assets.json", {})
        version_id = args.version or task_state.get("selected_version_id") or task_state.get("latest_version_id") or "V001"
        prompt_text, negative_text = build_task_prompt(
            product=product_profile,
            ref=reference_analysis,
            task_state=task_state,
            task_brief=task_brief,
            task_assets=task_assets,
            custom_constraints=args.custom_constraint,
        )
        prompt_path = task_dir / "prompts" / f"prompt_{version_id}.md"
        negative_path = task_dir / "prompts" / f"negative_prompt_{version_id}.md"
        prompt_path.write_text(prompt_text, encoding="utf-8")
        negative_path.write_text(negative_text, encoding="utf-8")

        package = {
            "version": "2.0",
            "project_id": task_state.get("project_id", ""),
            "task_id": task_state.get("task_id", ""),
            "created_at": utc_now(),
            "prompt_file": str(prompt_path),
            "negative_prompt_file": str(negative_path),
            "prompt_version": version_id,
            "reference_roles_present": task_brief.get("reference_roles_present", []),
            "selected_version_id": version_id,
        }
        write_json(task_dir / "prompts" / "prompt_package.json", package)
        update_task_state(
            task_dir,
            current_stage="task_prompt_ready",
            stage_status="ready",
        )
        update_task_manifest_entry(
            project_dir,
            task_state["task_id"],
            {
                "status": "prompt_ready",
                "selected_version_id": version_id,
                "latest_version_id": version_id,
            },
        )
        update_state(
            project_dir,
            current_stage="task_prompt_ready",
            stage_status="ready",
            active_task_id=task_state["task_id"],
        )
        append_audit(
            project_dir,
            "task_prompt_package_built",
            {
                "task_id": task_state["task_id"],
                "prompt_file": str(prompt_path),
                "prompt_version": version_id,
            },
        )
        print(f"task_id={task_state['task_id']}")
        print(f"prompt_file={prompt_path}")
        return

    creative_direction = read_json(project_dir / "creative_direction.json", {})
    version = args.version or "v1"
    prompt_text, negative_text = build_project_prompt(
        product_profile,
        reference_analysis,
        creative_direction,
        args.custom_constraint,
    )
    prompt_path = project_dir / "prompts" / f"prompt_{version}.md"
    negative_path = project_dir / "prompts" / "negative_prompt.md"
    prompt_path.write_text(prompt_text, encoding="utf-8")
    negative_path.write_text(negative_text, encoding="utf-8")

    package = {
        "version": "1.0",
        "project_id": read_json(project_dir / "project_state.json", {}).get("project_id", ""),
        "created_at": utc_now(),
        "prompt_file": str(prompt_path),
        "negative_prompt_file": str(negative_path),
        "prompt_version": version,
    }
    write_json(project_dir / "prompts" / "prompt_package.json", package)
    update_state(
        project_dir,
        current_stage="prompt_package_ready",
        stage_status="ready",
    )
    append_audit(
        project_dir,
        "prompt_package_built",
        {
            "prompt_file": str(prompt_path),
            "prompt_version": version,
        },
    )
    print(f"prompt_file={prompt_path}")


if __name__ == "__main__":
    main()
