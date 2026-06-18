#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    append_audit,
    find_project_candidates,
    load_tasks_manifest,
    project_summary,
    read_json,
    resolve_project_dir,
    update_project_recall,
)


def resolve_project_from_query(query: str, output_root: Path) -> Path:
    candidates = find_project_candidates(query, output_root, limit=3)
    if not candidates:
        raise SystemExit("未找到匹配项目，请补充更多线索。")
    if len(candidates) > 1 and int(candidates[1].get("score", 0)) >= int(candidates[0].get("score", 0)) - 5:
        raise SystemExit("项目命中不够确定，请补一条线索再继续。")
    return Path(candidates[0]["project_dir"]).resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="恢复旧项目上下文摘要")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project-dir", help="已知项目目录")
    group.add_argument("--query", help="自然语言召回线索")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="项目输出根目录")
    args = parser.parse_args()

    if args.project_dir:
        project_dir = resolve_project_dir(args.project_dir)
        query = project_dir.name
    else:
        query = args.query or ""
        project_dir = resolve_project_from_query(query, Path(args.output_root).resolve())

    summary = project_summary(project_dir)
    tasks_manifest = load_tasks_manifest(project_dir)
    product_profile = read_json(project_dir / "product_profile.json", {})
    update_project_recall(project_dir, query, summary)
    append_audit(project_dir, "project_resumed", {"query": query, "summary": summary})

    tasks = tasks_manifest.get("tasks", [])
    latest_task = tasks[-1] if tasks else {}

    print("status=matched")
    print(f"project_dir={project_dir}")
    print(f"project_id={summary['project_id']}")
    print(f"project_name={summary['project_name']}")
    print(f"product_name={summary['product_name']}")
    print(f"brand_name={summary['brand_name']}")
    print(f"task_count={summary['task_count']}")
    print(f"active_task_id={summary['active_task_id']}")
    print(f"latest_task_id={latest_task.get('task_id', '')}")
    print(f"latest_task_name={latest_task.get('task_name', '')}")
    print("aliases=" + " | ".join(summary["aliases"]))
    print("must_show_details=" + " | ".join(product_profile.get("must_show_details", [])))
    print("deformation_rules=" + " | ".join(product_profile.get("deformation_rules", [])))


if __name__ == "__main__":
    main()
