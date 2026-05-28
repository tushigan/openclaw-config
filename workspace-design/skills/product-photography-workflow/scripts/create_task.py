#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import initialize_task_files, resolve_project_dir  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="在现有项目下创建一个新任务")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-name", required=True, help="任务名")
    parser.add_argument("--task-type", default="product_display", help="任务类型")
    parser.add_argument("--output-ratio", default="", help="输出比例")
    parser.add_argument("--goal", default="", help="任务目标")
    parser.add_argument("--tag", action="append", default=[], help="任务标签")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    result = initialize_task_files(
        project_dir=project_dir,
        task_name=args.task_name,
        task_type=args.task_type,
        output_ratio=args.output_ratio,
        goal=args.goal,
        tags=args.tag,
    )
    print(f"task_id={result['task_id']}")
    print(f"task_dir={result['task_dir']}")
    print(f"version_id={result['version_id']}")


if __name__ == "__main__":
    main()
