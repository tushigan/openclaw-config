#!/usr/bin/env python3
"""Archive material into project directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agency_project import archive_material


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive material into project")
    parser.add_argument("--project-dir", required=True, help="Project directory")
    parser.add_argument("--source-path", required=True, help="Source file path")
    parser.add_argument(
        "--material-type",
        required=True,
        choices=["research", "reference", "client-assets"],
        help="Material type",
    )
    parser.add_argument("--notes", default="", help="Notes about the material")

    args = parser.parse_args()

    destination = archive_material(
        project_dir=Path(args.project_dir),
        source_path=Path(args.source_path),
        material_type=args.material_type,
        notes=args.notes,
    )

    print(json.dumps({"destination": str(destination)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
