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
    copy_asset_to_task,
    load_task_state,
    read_json,
    relative_to_project,
    resolve_asset_input,
    resolve_project_dir,
    resolve_task_dir,
    summarize_task_assets,
    update_task_manifest_entry,
    update_task_state,
    utc_now,
    write_json,
)

ROLE_ARGS = {
    "page_draft": "page_draft",
    "composition_reference": "composition_reference",
    "scene_reference": "scene_reference",
    "style_reference": "style_reference",
    "lighting_reference": "lighting_reference",
    "product_state_reference": "product_state_reference",
    "other_reference": "other_reference",
}


def add_entries(
    project_dir: Path,
    task_dir: Path,
    manifest: dict,
    role: str,
    values: list[str],
    *,
    copy_assets: bool,
) -> int:
    if not values:
        return 0
    asset_bucket = manifest.setdefault("assets", {}).setdefault(role, [])
    existing = {(entry.get("role"), entry.get("source_original", "")) for entry in asset_bucket}
    added = 0
    next_index = len(asset_bucket) + 1
    for value in values:
        source = resolve_asset_input(value)
        key = (role, str(source))
        if key in existing:
            continue
        copied = copy_asset_to_task(source, task_dir, role, next_index) if copy_assets else source
        asset_bucket.append(
            {
                "id": f"{role}_{next_index:02d}",
                "role": role,
                "path": relative_to_project(project_dir, copied),
                "absolute_path": str(copied),
                "source_original": str(source),
                "copied_into_task": copy_assets,
                "exists": copied.exists(),
                "registered_at": utc_now(),
            }
        )
        next_index += 1
        added += 1
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="登记任务级参考素材")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-id", required=True, help="任务 ID 或任务目录")
    parser.add_argument("--copy-assets", action="store_true", help="把素材复制进任务目录")
    parser.add_argument("--no-copy-assets", action="store_true", help="只记录原路径")
    for arg_name in ROLE_ARGS.values():
        parser.add_argument(f"--{arg_name.replace('_', '-')}", action="append", default=[], help=arg_name)
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    task_dir = resolve_task_dir(project_dir, args.task_id)
    task_state = load_task_state(task_dir)
    manifest_path = task_dir / "task_assets.json"
    manifest = read_json(manifest_path, {})
    copy_assets = not args.no_copy_assets
    if args.copy_assets:
        copy_assets = True

    total_added = 0
    for role in TASK_ROLE_ORDER:
        values = getattr(args, ROLE_ARGS[role], [])
        total_added += add_entries(project_dir, task_dir, manifest, role, values, copy_assets=copy_assets)

    manifest["updated_at"] = utc_now()
    manifest["summary"] = summarize_task_assets(manifest)
    write_json(manifest_path, manifest)
    update_task_state(
        task_dir,
        current_stage="task_reference_review",
        stage_status="ready",
        workflow_flag_updates={
            "references_classified": any(manifest["summary"].get(f"{role}_count", 0) for role in TASK_ROLE_ORDER),
        },
    )
    update_task_manifest_entry(
        project_dir,
        task_state["task_id"],
        {
            "status": "reference_ready",
        },
    )
    append_audit(
        project_dir,
        "task_assets_registered",
        {
            "task_id": task_state["task_id"],
            "added": total_added,
            "summary": manifest["summary"],
            "copy_assets": copy_assets,
        },
    )
    print(f"task_id={task_state['task_id']}")
    print(f"added={total_added}")
    print("roles=" + " | ".join(manifest["summary"].get("distinct_roles", [])))


if __name__ == "__main__":
    main()
