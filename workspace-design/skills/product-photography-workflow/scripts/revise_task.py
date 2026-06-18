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
    build_version_id,
    load_task_state,
    next_task_version_id,
    read_json,
    resolve_project_dir,
    resolve_task_dir,
    update_state,
    update_task_manifest_entry,
    update_task_state,
    utc_now,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="为任务创建一个新版本，不覆盖旧版本")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-id", required=True, help="任务 ID 或任务目录")
    parser.add_argument("--note", default="", help="修改说明")
    parser.add_argument("--reset-camera-preview", action="store_true", help="如果这次连机位也要改，则重置机位定稿状态")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    task_dir = resolve_task_dir(project_dir, args.task_id)
    task_state = load_task_state(task_dir)
    generation_path = task_dir / "generation_manifest.json"
    generation = read_json(generation_path, {})

    version_id = next_task_version_id(task_dir)
    version_dir = task_dir / "versions" / version_id
    version_dir.mkdir(parents=True, exist_ok=True)

    generation.setdefault("versions", []).append(
        {
            "version_id": version_id,
            "created_at": utc_now(),
            "status": "draft",
            "note": args.note,
        }
    )
    generation["updated_at"] = utc_now()
    generation["latest_version_id"] = version_id
    generation["latest_status"] = "revision_requested"
    write_json(generation_path, generation)

    revision_round = int(task_state.get("history", {}).get("revision_round", 0)) + 1
    preserve_camera_preview = (
        not args.reset_camera_preview
        and task_state.get("workflow_flags", {}).get("camera_preview_confirmed", False)
    )
    next_stage = "task_camera_preview_ready" if args.reset_camera_preview else "task_revision_requested"
    update_task_state(
        task_dir,
        current_stage=next_stage,
        stage_status="ready",
        workflow_flag_updates={
            "brief_confirmed": True,
            "camera_preview_confirmed": preserve_camera_preview,
            "generation_allowed": preserve_camera_preview,
            "result_approved": False,
        },
        field_updates={
            "selected_version_id": version_id,
            "latest_version_id": version_id,
            "selected_camera_preview_id": task_state.get("selected_camera_preview_id", "") if preserve_camera_preview else "",
            "latest_camera_preview_id": task_state.get("latest_camera_preview_id", "") if preserve_camera_preview else "",
            "latest_camera_preview_output": task_state.get("latest_camera_preview_output", "") if preserve_camera_preview else "",
            "history": {
                **task_state.get("history", {}),
                "revision_round": revision_round,
            },
        },
    )
    update_task_manifest_entry(
        project_dir,
        task_state["task_id"],
        {
            "status": "camera_preview_required" if args.reset_camera_preview else "revision_requested",
            "selected_version_id": version_id,
            "latest_version_id": version_id,
            "version_count": len(generation.get("versions", [])),
            "selected_camera_preview_id": task_state.get("selected_camera_preview_id", "") if preserve_camera_preview else "",
            "latest_camera_preview_id": task_state.get("latest_camera_preview_id", "") if preserve_camera_preview else "",
            "latest_camera_preview_output": task_state.get("latest_camera_preview_output", "") if preserve_camera_preview else "",
        },
    )
    project_state = read_json(project_dir / "project_state.json", {})
    attempts = project_state.get("attempts", {})
    update_state(
        project_dir,
        current_stage=next_stage,
        stage_status="ready",
        active_task_id=task_state["task_id"],
        attempts_update={
            **attempts,
            "revision_round": int(attempts.get("revision_round", 0)) + 1,
        },
    )
    append_audit(
        project_dir,
        "task_revised",
        {
            "task_id": task_state["task_id"],
            "version_id": version_id,
            "note": args.note,
            "reset_camera_preview": args.reset_camera_preview,
        },
    )
    print(f"task_id={task_state['task_id']}")
    print(f"version_id={version_id}")
    print(f"version_dir={version_dir}")


if __name__ == "__main__":
    main()
