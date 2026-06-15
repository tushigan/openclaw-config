#!/usr/bin/env python3
"""Find active project for a brand."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agency_project import find_active_project


def main() -> None:
    parser = argparse.ArgumentParser(description="Find active project for a brand")
    parser.add_argument(
        "--workspace-root",
        default="/Users/a123/.openclaw",
        help="Workspace root directory (default: /Users/a123/.openclaw)"
    )
    parser.add_argument("--brand-name", required=True, help="Brand name to search")

    args = parser.parse_args()

    project_dir = find_active_project(
        workspace_root=Path(args.workspace_root),
        brand_name=args.brand_name,
    )

    if project_dir:
        project_json = project_dir / "project.json"
        if project_json.exists():
            project_content = json.loads(project_json.read_text(encoding="utf-8"))
            print(
                json.dumps(
                    {
                        "found": True,
                        "project_dir": str(project_dir),
                        "project": project_content,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(
                json.dumps(
                    {"found": True, "project_dir": str(project_dir), "project": None},
                    ensure_ascii=False,
                )
            )
    else:
        print(json.dumps({"found": False, "project_dir": None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
