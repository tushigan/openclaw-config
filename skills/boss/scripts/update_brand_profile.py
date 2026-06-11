#!/usr/bin/env python3
"""Update brand profile field."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agency_project import update_brand_profile_field


def main() -> None:
    parser = argparse.ArgumentParser(description="Update brand profile field")
    parser.add_argument("--workspace-root", required=True, help="Workspace root directory")
    parser.add_argument("--brand-name", required=True, help="Brand name")
    parser.add_argument("--field", required=True, help="Field name (supports nested like 'vi_guidelines.primary_colors')")
    parser.add_argument("--value", required=True, help="New value (JSON string for lists/objects)")
    parser.add_argument(
        "--operation",
        choices=["replace", "append"],
        default="replace",
        help="Operation: 'replace' to replace value, 'append' to append to list",
    )

    args = parser.parse_args()

    # Parse value JSON
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        # If not valid JSON, treat as string
        value = args.value

    # Update field
    result = update_brand_profile_field(
        workspace_root=Path(args.workspace_root),
        brand_name=args.brand_name,
        field=args.field,
        value=value,
        operation=args.operation,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
