from __future__ import annotations

import argparse
from pathlib import Path

from business_project.project import sync_quote_state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--quote-version", required=True)
    parser.add_argument("--quote-output", action="append", default=[])
    args = parser.parse_args()

    sync_quote_state(
        project_dir=Path(args.project_dir),
        quote_version=args.quote_version,
        output_refs=args.quote_output,
    )


if __name__ == "__main__":
    main()
