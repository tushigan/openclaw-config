#!/usr/bin/env python3
"""Find brand profile by brand name."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agency_project import find_brand_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Find brand profile")
    parser.add_argument("--workspace-root", required=True, help="Workspace root directory")
    parser.add_argument("--brand-name", required=True, help="Brand name to search")

    args = parser.parse_args()

    profile_path = find_brand_profile(
        workspace_root=Path(args.workspace_root),
        brand_name=args.brand_name,
    )

    if profile_path:
        profile_content = json.loads(profile_path.read_text(encoding="utf-8"))
        print(
            json.dumps(
                {
                    "found": True,
                    "profile_path": str(profile_path),
                    "profile": profile_content,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(json.dumps({"found": False, "profile_path": None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
