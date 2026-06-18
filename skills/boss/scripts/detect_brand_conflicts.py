#!/usr/bin/env python3
"""Detect conflicts between brand profile and new information."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agency_project import detect_conflicts


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect brand profile conflicts")
    parser.add_argument(
        "--workspace-root",
        default="/Users/a123/.openclaw",
        help="Workspace root directory (default: /Users/a123/.openclaw)"
    )
    parser.add_argument("--brand-name", required=True, help="Brand name")
    parser.add_argument("--new-info", required=True, help="New brand information (JSON string)")

    args = parser.parse_args()

    # Parse new info JSON
    try:
        new_info = json.loads(args.new_info)
    except json.JSONDecodeError as e:
        print(
            json.dumps(
                {
                    "error": f"Invalid JSON in --new-info: {e}",
                    "has_conflict": False,
                    "conflicts": [],
                    "supplements": [],
                },
                ensure_ascii=False,
            )
        )
        return

    # Detect conflicts
    result = detect_conflicts(
        workspace_root=Path(args.workspace_root),
        brand_name=args.brand_name,
        new_info=new_info,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
