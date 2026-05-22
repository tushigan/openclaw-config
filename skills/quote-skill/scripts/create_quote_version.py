from __future__ import annotations

import argparse
from pathlib import Path

from quote_skill.project import create_version


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--change-reason", required=True)
    args = parser.parse_args()

    create_version(Path(args.project_dir), change_reason=args.change_reason)


if __name__ == "__main__":
    main()
