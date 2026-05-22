from __future__ import annotations

import argparse
from pathlib import Path

from quote_skill.project import create_project


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--projects-root")
    group.add_argument("--project-dir")
    parser.add_argument("--client-name", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--output-mode", required=True, choices=["html_pdf", "xlsx"])
    args = parser.parse_args()

    create_project(
        Path(args.projects_root) if args.projects_root else None,
        args.client_name,
        args.project_name,
        output_mode=args.output_mode,
        project_dir=Path(args.project_dir) if args.project_dir else None,
    )


if __name__ == "__main__":
    main()
