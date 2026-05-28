#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    PRODUCT_ROLE_ORDER,
    TASK_CAMERA_PREVIEW_FILE,
    SKILL_DIR,
    append_audit,
    asset_entries_by_role,
    load_task_state,
    read_json,
    resolve_project_dir,
    resolve_task_dir,
    size_for_ratio,
    task_asset_entries_by_role,
    update_state,
    update_task_manifest_entry,
    update_task_state,
    utc_now,
    write_json,
)
from run_generation import build_command, dedupe_entries, latest_unique_entries  # noqa: E402


DEFAULT_GPT_IMAGE2_SCRIPT = (Path.home() / ".codex" / "skills" / "gpt-image2-gen" / "scripts" / "generate.py").resolve()


def resolve_default_gpt_image2_script() -> Path:
    candidates = [
        DEFAULT_GPT_IMAGE2_SCRIPT,
        (SKILL_DIR.parent / "gpt-image2-gen" / "scripts" / "generate.py").resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return DEFAULT_GPT_IMAGE2_SCRIPT


def main() -> None:
    parser = argparse.ArgumentParser(description="生成机位定稿图")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-id", required=True, help="任务 ID 或任务目录")
    parser.add_argument("--gpt-image2-script", default=str(resolve_default_gpt_image2_script()), help="统一生图脚本")
    parser.add_argument("--ratio", default="", help="覆盖比例")
    parser.add_argument("--size", default="", help="覆盖像素尺寸")
    parser.add_argument("--count", type=int, default=1, help="机位定稿图输出数量")
    parser.add_argument("--model", default="gpt-image-2-pro", help="逻辑模型名")
    parser.add_argument("--max-product-refs", type=int, default=4, help="最多产品参考图数量")
    parser.add_argument("--max-style-refs", type=int, default=2, help="最多光影参考图数量")
    parser.add_argument("--dry-run", action="store_true", help="只生成命令和 manifest，不真正调用模型")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    task_dir = resolve_task_dir(project_dir, args.task_id)
    task_state = load_task_state(task_dir)
    task_brief = read_json(task_dir / "task_brief.json", {})
    if not task_state.get("workflow_flags", {}).get("brief_confirmed", False):
        raise SystemExit("任务简报尚未确认，不能进入机位定稿图阶段。")
    if not task_brief.get("camera_preview_required", False):
        raise SystemExit("当前任务不需要机位定稿图。")

    preview_manifest_path = task_dir / TASK_CAMERA_PREVIEW_FILE
    preview_manifest = read_json(preview_manifest_path, {})
    preview_id = task_state.get("selected_camera_preview_id") or preview_manifest.get("latest_preview_id", "")
    if not preview_id:
        raise SystemExit("尚未生成机位定稿图提示词。可先执行 build_camera_preview_prompt.py。")

    prompt_path = task_dir / "prompts" / f"camera_preview_{preview_id}.md"
    if not prompt_path.exists():
        raise SystemExit(f"机位定稿图 Prompt 文件不存在: {prompt_path}")

    assets_manifest = read_json(project_dir / "assets_manifest.json", {})
    task_assets = read_json(task_dir / "task_assets.json", {})
    ratio = args.ratio or task_brief.get("output_ratio") or task_state.get("output_ratio", "") or "1:1"
    size = args.size or size_for_ratio(ratio)

    base_product_refs = asset_entries_by_role(assets_manifest, PRODUCT_ROLE_ORDER)
    product_state_refs = task_asset_entries_by_role(task_assets, ["product_state_reference"])
    product_refs = dedupe_entries(base_product_refs + product_state_refs, args.max_product_refs)

    camera_storyboard_refs = task_asset_entries_by_role(task_assets, ["camera_storyboard_reference"])
    task_layout_refs = task_asset_entries_by_role(task_assets, ["composition_reference"])
    project_layout_refs = asset_entries_by_role(assets_manifest, ["reference_layout"])
    if camera_storyboard_refs:
        layout_source_refs = camera_storyboard_refs
        layout_authority_role = "camera_storyboard_reference"
    else:
        layout_source_refs = task_layout_refs if task_layout_refs else project_layout_refs
        layout_authority_role = "composition_reference" if task_layout_refs else "reference_layout"
    layout_refs = latest_unique_entries(layout_source_refs, 1)

    style_refs = dedupe_entries(
        asset_entries_by_role(assets_manifest, ["reference_lighting"])
        + task_asset_entries_by_role(task_assets, ["lighting_reference"]),
        args.max_style_refs,
    )
    generic_refs = dedupe_entries(
        task_asset_entries_by_role(task_assets, ["page_draft", "other_reference"])
        + (task_layout_refs if camera_storyboard_refs else []),
        8,
    )

    output_path = task_dir / "previews" / preview_id / "preview.png"
    gpt_script = Path(args.gpt_image2_script)
    cmd = build_command(
        gpt_script=gpt_script,
        prompt_path=prompt_path,
        output_path=output_path,
        size=size,
        model=args.model,
        count=args.count,
        base_refs=[],
        product_refs=product_refs,
        layout_refs=layout_refs,
        style_refs=style_refs,
        background_refs=[],
        generic_refs=generic_refs,
    )
    command_summary = " ".join(shlex.quote(part) for part in cmd)

    preview_payload = {
        "preview_id": preview_id,
        "created_at": utc_now(),
        "prompt_file": str(prompt_path),
        "output": str(output_path),
        "size": size,
        "ratio": ratio,
        "count": args.count,
        "model": args.model,
        "product_refs": [item["absolute_path"] for item in product_refs],
        "layout_refs": [item["absolute_path"] for item in layout_refs],
        "layout_authority_role": layout_authority_role,
        "style_refs": [item["absolute_path"] for item in style_refs],
        "generic_refs": [item["absolute_path"] for item in generic_refs],
        "command_summary": command_summary,
        "preview_style": "grayscale_block",
        "status": "dry_run" if args.dry_run else "queued",
    }

    logs_dir = task_dir / "reports"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = logs_dir / f"camera_preview.{preview_id}.stdout.log"
    stderr_log = logs_dir / f"camera_preview.{preview_id}.stderr.log"
    preview_payload["stdout_log"] = str(stdout_log)
    preview_payload["stderr_log"] = str(stderr_log)

    def sync_preview_manifest(status: str, exit_code: int | None = None) -> None:
        preview_manifest["latest_status"] = status
        preview_manifest["latest_output"] = str(output_path)
        preview_manifest["latest_preview_id"] = preview_id
        preview_manifest["updated_at"] = utc_now()
        previews = preview_manifest.setdefault("previews", [])
        matched = False
        for item in previews:
            if item.get("preview_id") != preview_id:
                continue
            item.update(preview_payload)
            item["status"] = status
            if exit_code is not None:
                item["exit_code"] = exit_code
            matched = True
        if not matched:
            entry = dict(preview_payload)
            entry["status"] = status
            if exit_code is not None:
                entry["exit_code"] = exit_code
            previews.append(entry)
        write_json(preview_manifest_path, preview_manifest)

    if args.dry_run:
        sync_preview_manifest("dry_run")
        update_task_state(
            task_dir,
            current_stage="task_camera_preview_queued",
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
                "status": "camera_preview_dry_run",
                "selected_camera_preview_id": preview_id,
                "latest_camera_preview_id": preview_id,
            },
        )
        update_state(
            project_dir,
            current_stage="task_camera_preview_queued",
            stage_status="ready",
            active_task_id=task_state["task_id"],
        )
        append_audit(
            project_dir,
            "task_camera_preview_dry_run_prepared",
            {
                "task_id": task_state["task_id"],
                **preview_payload,
            },
        )
        print(f"task_id={task_state['task_id']}")
        print(f"preview_id={preview_id}")
        print(f"command_summary={command_summary}")
        return

    update_task_state(
        task_dir,
        current_stage="task_camera_preview_running",
        stage_status="running",
        workflow_flag_updates={
            "camera_preview_confirmed": False,
            "generation_allowed": False,
        },
        field_updates={
            "selected_camera_preview_id": preview_id,
            "latest_camera_preview_id": preview_id,
        },
    )
    update_state(
        project_dir,
        current_stage="task_camera_preview_running",
        stage_status="running",
        active_task_id=task_state["task_id"],
    )

    with stdout_log.open("w", encoding="utf-8") as stdout_fh, stderr_log.open("w", encoding="utf-8") as stderr_fh:
        result = subprocess.run(cmd, text=True, stdout=stdout_fh, stderr=stderr_fh)

    status = "succeeded" if result.returncode == 0 else "failed"
    sync_preview_manifest(status, result.returncode)

    update_task_state(
        task_dir,
        current_stage="task_camera_preview_waiting_confirm" if result.returncode == 0 else "task_camera_preview_failed",
        stage_status="waiting_user" if result.returncode == 0 else "error",
        workflow_flag_updates={
            "camera_preview_confirmed": False,
            "generation_allowed": False,
        },
        field_updates={
            "selected_camera_preview_id": preview_id,
            "latest_camera_preview_id": preview_id,
            "latest_camera_preview_output": str(output_path),
        },
    )
    update_task_manifest_entry(
        project_dir,
        task_state["task_id"],
        {
            "status": "camera_preview_waiting_confirm" if result.returncode == 0 else "camera_preview_failed",
            "selected_camera_preview_id": preview_id,
            "latest_camera_preview_id": preview_id,
            "latest_camera_preview_output": str(output_path),
        },
    )
    update_state(
        project_dir,
        current_stage="task_camera_preview_waiting_confirm" if result.returncode == 0 else "task_camera_preview_failed",
        stage_status="waiting_user" if result.returncode == 0 else "error",
        active_task_id=task_state["task_id"],
    )
    append_audit(
        project_dir,
        "task_camera_preview_executed",
        {
            "task_id": task_state["task_id"],
            **preview_payload,
            "exit_code": result.returncode,
            "status": status,
        },
    )
    print(f"task_id={task_state['task_id']}")
    print(f"preview_id={preview_id}")
    print(f"output={output_path}")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
