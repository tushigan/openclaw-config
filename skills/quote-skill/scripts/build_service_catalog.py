from __future__ import annotations

import argparse
from pathlib import Path

from quote_skill.catalog import build_catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Build data/service-catalog.json from the workbook.")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sheet", default="汇总表")
    args = parser.parse_args()
    build_catalog(Path(args.workbook), Path(args.output), sheet_name=args.sheet)


if __name__ == "__main__":
    main()
