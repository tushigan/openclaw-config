from __future__ import annotations

import argparse
import json
from pathlib import Path

from business_project.project import archive_material


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--material-type", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--source-channel", default="")
    parser.add_argument("--captured-at")
    args = parser.parse_args()

    record = archive_material(
        project_dir=Path(args.project_dir),
        source_path=Path(args.source_path),
        material_type=args.material_type,
        title=args.title,
        source_channel=args.source_channel,
        captured_at=args.captured_at,
    )
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
