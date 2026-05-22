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
    build_project_id,
    initialize_project_files,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化产品摄影项目目录")
    parser.add_argument("project_name", help="项目名或产品名")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="项目输出根目录")
    parser.add_argument("--project-id", default="", help="可选项目 ID")
    parser.add_argument("--scene-mode", default="studio_white", help="默认场景模式")
    parser.add_argument("--scope-level", default="still_life_v1", help="默认能力范围")
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    project_id = args.project_id or build_project_id(args.project_name)
    project_suffix = project_id.removeprefix("PP-")
    project_dir = output_root / f"{args.project_name}_{project_suffix}"

    initialize_project_files(
        project_dir=project_dir,
        project_name=args.project_name,
        project_id=project_id,
        scene_mode=args.scene_mode,
        scope_level=args.scope_level,
    )
    append_audit(
        project_dir,
        "project_initialized",
        {
            "project_id": project_id,
            "project_name": args.project_name,
            "scene_mode": args.scene_mode,
            "scope_level": args.scope_level,
        },
    )
    print(f"project_dir={project_dir}")
    print(f"project_id={project_id}")


if __name__ == "__main__":
    main()
