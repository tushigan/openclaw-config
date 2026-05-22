from __future__ import annotations

import argparse
import json
from pathlib import Path

from business_project.project import create_business_project


def _parse_source_material(value: str) -> dict[str, str]:
    parts = value.split(":", 3)
    if len(parts) < 2:
        raise ValueError("source material must be path:type[:title[:source_channel]]")
    path, material_type = parts[0], parts[1]
    title = parts[2] if len(parts) >= 3 and parts[2] else Path(path).name
    source_channel = parts[3] if len(parts) >= 4 and parts[3] else ""
    return {
        "path": path,
        "type": material_type,
        "title": title,
        "source_channel": source_channel,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--client-name", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--current-goal", required=True)
    parser.add_argument("--source-material", action="append", required=True)
    args = parser.parse_args()

    project_dir = create_business_project(
        workspace_root=Path(args.workspace_root),
        client_name=args.client_name,
        project_name=args.project_name,
        current_goal=args.current_goal,
        source_materials=[_parse_source_material(item) for item in args.source_material],
    )

    print(json.dumps({"project_dir": str(project_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
