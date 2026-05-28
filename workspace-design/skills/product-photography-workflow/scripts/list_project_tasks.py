#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import load_tasks_manifest, resolve_project_dir  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="列出项目中的所有任务")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    manifest = load_tasks_manifest(project_dir)
    tasks = manifest.get("tasks", [])
    print(f"task_count={len(tasks)}")
    for index, task in enumerate(tasks, start=1):
        prefix = f"task_{index}"
        print(f"{prefix}_id={task.get('task_id', '')}")
        print(f"{prefix}_name={task.get('task_name', '')}")
        print(f"{prefix}_type={task.get('task_type', '')}")
        print(f"{prefix}_status={task.get('status', '')}")
        print(f"{prefix}_latest_version_id={task.get('latest_version_id', '')}")
        print(f"{prefix}_latest_output={task.get('latest_output', '')}")


if __name__ == "__main__":
    main()
