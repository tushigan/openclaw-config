#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from project_manager import ProjectManager, now_iso, write_json


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json: {path}: {exc}") from None


def direction_suffix(index: int) -> str:
    if index < 0:
        raise ValueError("index must be >= 0")
    letters = []
    value = index
    while True:
        value, remainder = divmod(value, 26)
        letters.append(chr(ord("A") + remainder))
        if value == 0:
            break
        value -= 1
    return "".join(reversed(letters))


def pick(option: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = option.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def copy_block(text: str, default_style: str = "品牌定制字形，清晰可读") -> dict[str, str]:
    return {
        "文案": text,
        "字体风格": default_style,
    }


def normalize_copywriting(option: dict[str, Any], index: int) -> dict[str, Any]:
    direction_name = pick(option, "direction_name", "name", "title", default=f"方向{direction_suffix(index)}")
    title = pick(option, "main_title", "title_main", "title", "headline")
    subtitle = pick(option, "sub_title", "subtitle", "subtitle_main", "subheadline")
    brand_line = pick(option, "brand_line", "slogan", "tagline")

    copywriting: dict[str, Any] = {
        "title_main": copy_block(title),
        "subtitle_main": copy_block(subtitle),
        "brand_line": copy_block(brand_line),
        "_meta": {
            "direction_name": direction_name,
            "direction_index": index + 1,
            "source": "split_direction_projects.py",
            "split_at": now_iso(),
        },
    }

    for key, value in option.items():
        if key in {
            "direction_name",
            "name",
            "title",
            "headline",
            "main_title",
            "title_main",
            "sub_title",
            "subtitle",
            "subtitle_main",
            "subheadline",
            "brand_line",
            "slogan",
            "tagline",
        }:
            continue
        if key.startswith("_"):
            continue
        copywriting.setdefault("_meta", {})[key] = value
    return copywriting


def split_project(project_dir: Path, source_name: str, force: bool = False) -> list[dict[str, str]]:
    project_dir = project_dir.resolve()
    source_path = project_dir / source_name
    source = load_json(source_path)
    if not isinstance(source, dict) or not isinstance(source.get("options"), list) or not source["options"]:
        raise SystemExit(f"{source_path} must contain a non-empty options array")

    brief_path = project_dir / "brief.json"
    base_brief = load_json(brief_path)
    if not isinstance(base_brief, dict):
        raise SystemExit(f"{brief_path} must contain a json object")

    manifest: list[dict[str, str]] = []
    parent = project_dir.parent
    base_id = project_dir.name

    for index, raw_option in enumerate(source["options"]):
        if not isinstance(raw_option, dict):
            raise SystemExit(f"options[{index}] must be a json object")

        suffix = direction_suffix(index)
        child_id = f"{base_id}-{suffix}"
        child_dir = parent / child_id
        if child_dir.exists():
            if not force:
                raise SystemExit(f"target already exists: {child_dir}; rerun with --force to replace it")
            shutil.rmtree(child_dir)
        shutil.copytree(project_dir, child_dir)

        copywriting = normalize_copywriting(raw_option, index)
        direction_name = copywriting["_meta"]["direction_name"]
        child_brief = dict(base_brief)
        child_brief["task_id"] = child_id
        child_brief["direction_name"] = direction_name
        child_brief["parent_task_id"] = base_brief.get("task_id") or base_id
        child_brief["direction_suffix"] = suffix

        write_json(child_dir / "brief.json", child_brief)
        write_json(child_dir / "copywriting.json", copywriting)
        write_json(
            child_dir / "selected_direction.json",
            {
                "project_id": child_id,
                "parent_project_id": base_id,
                "direction_suffix": suffix,
                "direction_name": direction_name,
                "source_copywriting": str(source_path),
                "created_at": now_iso(),
            },
        )

        manager = ProjectManager(child_dir)
        manager.state["project_id"] = child_id
        manager.state["project_dir"] = str(child_dir)
        manager.state["current_stage"] = "style_profile"
        manager.state["stage_status"]["copywriting"] = "done"
        manager.state["workflow_flags"]["copywriting_ready"] = True
        manager.state["workflow_flags"]["copy_confirmed"] = True
        manager.state["artifacts"]["brief"] = str(child_dir / "brief.json")
        manager.state["artifacts"]["copywriting"] = str(child_dir / "copywriting.json")
        manager.state["resume"]["auto_resume_stage"] = "style_profile"
        manager.state["resume"]["resume_reason"] = "多方向文案已拆分为独立项目，可继续风格提炼或创意表达。"
        manager.state["resume"]["updated_at"] = now_iso()
        manager.save()
        manager.audit(
            "direction_project_split",
            stage="copywriting",
            status="done",
            reason="用户要求多个方向分别出图，已拆分为独立项目。",
            files=["brief.json", "copywriting.json", "selected_direction.json"],
            extra={
                "parent_project_id": base_id,
                "direction_suffix": suffix,
                "direction_name": direction_name,
            },
        )

        manifest.append(
            {
                "project_id": child_id,
                "project_dir": str(child_dir),
                "direction_suffix": suffix,
                "direction_name": direction_name,
                "copywriting_path": str(child_dir / "copywriting.json"),
            }
        )

    write_json(
        project_dir / "direction_split_manifest.json",
        {
            "project_id": base_id,
            "source": str(source_path),
            "created_at": now_iso(),
            "children": manifest,
        },
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Split copywriting options into independent direction projects.")
    parser.add_argument("--project-dir", required=True, help="Base brand poster project directory.")
    parser.add_argument("--source", default="copywriting.json", help="Source JSON file inside project dir. Default: copywriting.json")
    parser.add_argument("--force", action="store_true", help="Replace existing child project directories.")
    args = parser.parse_args(argv)

    manifest = split_project(Path(args.project_dir), args.source, args.force)
    print(json.dumps({"ok": True, "children": manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
