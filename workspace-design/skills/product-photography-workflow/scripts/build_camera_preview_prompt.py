#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    TASK_CAMERA_PREVIEW_FILE,
    append_audit,
    load_task_state,
    next_camera_preview_id,
    read_json,
    resolve_project_dir,
    resolve_task_dir,
    update_state,
    update_task_manifest_entry,
    update_task_state,
    utc_now,
    write_json,
)


def bullet_lines(values: list[str], empty: str = "- 无") -> list[str]:
    return [f"- {item}" for item in values if item] or [empty]


def main() -> None:
    parser = argparse.ArgumentParser(description="生成机位定稿图的固定提示词")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-id", required=True, help="任务 ID 或任务目录")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    task_dir = resolve_task_dir(project_dir, args.task_id)
    task_state = load_task_state(task_dir)
    task_brief = read_json(task_dir / "task_brief.json", {})
    product_profile = read_json(project_dir / "product_profile.json", {})
    preview_manifest_path = task_dir / TASK_CAMERA_PREVIEW_FILE
    preview_manifest = read_json(preview_manifest_path, {})

    if not task_state.get("workflow_flags", {}).get("brief_confirmed", False):
        raise SystemExit("任务简报尚未确认，不能生成机位定稿图提示词。")

    if not task_brief.get("camera_preview_required", False):
        raise SystemExit("当前任务不需要机位定稿图，可直接走最终生图。")

    preview_id = next_camera_preview_id(task_dir)
    prompt_path = task_dir / "prompts" / f"camera_preview_{preview_id}.md"
    prompt_lines = [
        f"请为“{product_profile.get('product_name', '该产品')}”生成一张机位定稿图。",
        "",
        "这是机位确认图，不是最终成图。",
        "",
        "## 固定提示词骨架",
        "",
        "### 1. 出图目标",
        f"- 任务名称：{task_state.get('task_name', '')}",
        f"- 任务目标：{task_brief.get('goal') or task_state.get('goal', '') or '未填写'}",
        f"- 输出比例：{task_brief.get('output_ratio') or task_state.get('output_ratio', '') or '未填写'}",
        "- 图像类型：机位定稿图",
        "- 背景要求：纯白背景",
        "",
        "### 2. 产品真相锁定",
        f"- 产品形状：{product_profile.get('outer_shape') or '以产品真相图为准'}",
        f"- 结构类型：{product_profile.get('structure_type') or '未填写'}",
        f"- 真实状态：{product_profile.get('open_close_states') or '以产品真相图为准'}",
        f"- 必须保留的真实信息：{'; '.join(product_profile.get('must_show_details', [])) or '以产品真相图为准'}",
        "",
        "### 3. 机位锁定",
        f"- 主图意图：{task_brief.get('camera_plan', {}).get('hero_shot_intent') or '未填写'}",
        *bullet_lines([f"镜头优先级：{item}" for item in task_brief.get('camera_plan', {}).get('shot_priority', [])]),
        f"- 机位角度：{task_brief.get('camera_plan', {}).get('camera_angle_lock') or '以机位参考图为准'}",
        f"- 裁切与留白：{task_brief.get('camera_plan', {}).get('crop_and_whitespace_lock') or '以任务说明为准'}",
        f"- 焦点位置：{task_brief.get('camera_plan', {}).get('focus_anchor') or '以任务说明为准'}",
        f"- 主体摆位：{task_brief.get('placement_note') or '以任务说明为准'}",
        "",
        "### 4. 光影锁定",
        f"- 主光方向：{task_brief.get('camera_plan', {}).get('lighting_direction_lock') or '以光影参考图为准'}",
        f"- 场景说明：{task_brief.get('scene_note') or '纯白商业产品图'}",
        "- 只保留大块面的明暗关系，不追求细腻高光。",
        "",
        "### 5. 机位定稿图输出规则",
        "- 统一输出白底、灰度块面的低细节机位确认图。",
        "- 只确认角度、透视、裁切、留白、主体位置、木板方向和主光大关系。",
        "- 可以用简单块面表达产品和道具，不要做写实渲染。",
        "- 不要表现真实食物质感，不要表现芝士细节、榴莲颗粒、微观纹理和风格化修图。",
        "",
        "### 6. 禁止项",
        *bullet_lines(
            list(task_brief.get("must_avoid", []))
            + list(product_profile.get("must_not_fake_details", []))
            + [
                "不要把机位定稿图做成最终成片",
                "不要加入真实材质光泽和复杂食物纹理",
                "不要让风格图接管产品结构和机位",
            ]
        ),
    ]
    prompt_text = "\n".join(prompt_lines).strip() + "\n"
    prompt_path.write_text(prompt_text, encoding="utf-8")

    preview_entry = {
        "preview_id": preview_id,
        "created_at": utc_now(),
        "status": "prompt_ready",
        "prompt_file": str(prompt_path),
        "output": "",
    }
    preview_manifest.setdefault("previews", []).append(preview_entry)
    preview_manifest["updated_at"] = utc_now()
    preview_manifest["latest_preview_id"] = preview_id
    preview_manifest["latest_status"] = "prompt_ready"
    write_json(preview_manifest_path, preview_manifest)

    update_task_state(
        task_dir,
        current_stage="task_camera_preview_prompt_ready",
        stage_status="ready",
        field_updates={
            "selected_camera_preview_id": preview_id,
            "latest_camera_preview_id": preview_id,
        },
    )
    update_task_manifest_entry(
        project_dir,
        task_state["task_id"],
        {
            "status": "camera_preview_prompt_ready",
            "selected_camera_preview_id": preview_id,
            "latest_camera_preview_id": preview_id,
        },
    )
    update_state(
        project_dir,
        current_stage="task_camera_preview_prompt_ready",
        stage_status="ready",
        active_task_id=task_state["task_id"],
    )
    append_audit(
        project_dir,
        "task_camera_preview_prompt_built",
        {
            "task_id": task_state["task_id"],
            "preview_id": preview_id,
            "prompt_file": str(prompt_path),
        },
    )
    print(f"task_id={task_state['task_id']}")
    print(f"preview_id={preview_id}")
    print(f"prompt_file={prompt_path}")


if __name__ == "__main__":
    main()
