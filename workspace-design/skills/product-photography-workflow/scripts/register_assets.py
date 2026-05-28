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
    copy_asset_to_project,
    read_json,
    relative_to_project,
    resolve_asset_input,
    resolve_project_dir,
    summarize_assets,
    update_state,
    utc_now,
    write_json,
)

ROLE_ARGS = {
    "product_front": "product_front",
    "product_side": "product_side",
    "product_top": "product_top",
    "product_back": "product_back",
    "product_open": "product_open",
    "product_cross_section": "product_cross_section",
    "product_detail": "product_detail",
    "reference_style": "reference_style",
    "reference_layout": "reference_layout",
    "reference_lighting": "reference_lighting",
    "reference_background": "reference_background",
    "reference_other": "reference_other",
}


def add_entries(
    project_dir: Path,
    manifest: dict,
    role: str,
    values: list[str],
    *,
    bucket_key: str,
    copy_assets: bool,
) -> int:
    if not values:
        return 0
    bucket = manifest.setdefault(bucket_key, [])
    existing = {
        (item.get("role"), item.get("source_original", ""))
        for item in bucket
    }
    if bucket_key == "product_assets":
        dest_dir = project_dir / "images" / "product_sources"
    else:
        dest_dir = project_dir / "images" / "reference_sources"

    added = 0
    next_index = len(bucket) + 1
    for value in values:
        source = resolve_asset_input(value)
        key = (role, str(source))
        if key in existing:
            continue
        if copy_assets:
            copied = copy_asset_to_project(source, dest_dir, role, next_index)
        else:
            copied = source
        bucket.append(
            {
                "id": f"{role}_{next_index:02d}",
                "role": role,
                "path": relative_to_project(project_dir, copied),
                "absolute_path": str(copied),
                "source_original": str(source),
                "copied_into_project": copy_assets,
                "exists": copied.exists(),
                "registered_at": utc_now(),
            }
        )
        next_index += 1
        added += 1
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="登记产品图和参考图到项目")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--copy-assets", action="store_true", help="把素材复制进项目目录")
    parser.add_argument("--no-copy-assets", action="store_true", help="只记录原路径，不复制")
    for arg_name in ROLE_ARGS.values():
        parser.add_argument(f"--{arg_name.replace('_', '-')}", action="append", default=[], help=arg_name)
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    manifest_path = project_dir / "assets_manifest.json"
    manifest = read_json(manifest_path, {})
    copy_assets = True
    if args.no_copy_assets:
        copy_assets = False
    elif args.copy_assets:
        copy_assets = True

    total_added = 0
    for role in ROLE_ARGS:
        values = getattr(args, ROLE_ARGS[role])
        bucket_key = "product_assets" if role.startswith("product_") else "reference_assets"
        total_added += add_entries(
            project_dir,
            manifest,
            role,
            values,
            bucket_key=bucket_key,
            copy_assets=copy_assets,
        )

    manifest["updated_at"] = utc_now()
    manifest["summary"] = summarize_assets(manifest)
    write_json(manifest_path, manifest)

    intake_path = project_dir / "intake_manifest.json"
    intake = read_json(intake_path, {})
    intake["updated_at"] = utc_now()
    intake["asset_summary"] = manifest["summary"]
    write_json(intake_path, intake)

    update_state(
        project_dir,
        current_stage="intake_collecting",
        stage_status="ready",
        workflow_flag_updates={
            "assets_sufficient": False,
        },
    )
    append_audit(
        project_dir,
        "assets_registered",
        {
            "added": total_added,
            "summary": manifest["summary"],
            "copy_assets": copy_assets,
        },
    )
    print(f"added={total_added}")
    print(f"product_assets={manifest['summary']['product_asset_count']}")
    print(f"reference_assets={manifest['summary']['reference_asset_count']}")


if __name__ == "__main__":
    main()
