#!/usr/bin/env python3
"""Initialize a new agency project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agency_project import create_agency_project


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a new agency project")
    parser.add_argument("--workspace-root", required=True, help="Workspace root directory")
    parser.add_argument("--brand-name", required=True, help="Brand name")
    parser.add_argument("--campaign-name", required=True, help="Campaign name")
    parser.add_argument("--campaign-type", default="integrated_marketing", help="Campaign type")
    parser.add_argument("--brand-name-en", default="", help="Brand name in English")
    parser.add_argument("--industry", default="", help="Industry")
    parser.add_argument("--category", default="", help="Category")
    parser.add_argument("--positioning", default="", help="Brand positioning")
    parser.add_argument("--brand-tone", default="", help="Brand tone")
    parser.add_argument("--target-audience", default="", help="Target audience")
    parser.add_argument("--core-values", default="", help="Core values (comma-separated)")

    args = parser.parse_args()

    brand_info = {
        "brand_name_en": args.brand_name_en,
        "industry": args.industry,
        "category": args.category,
        "positioning": args.positioning,
        "brand_tone": args.brand_tone,
        "target_audience": args.target_audience,
    }

    if args.core_values:
        brand_info["core_values"] = [v.strip() for v in args.core_values.split(",") if v.strip()]

    project_dir = create_agency_project(
        workspace_root=Path(args.workspace_root),
        brand_name=args.brand_name,
        campaign_name=args.campaign_name,
        campaign_type=args.campaign_type,
        brand_info=brand_info,
    )

    print(json.dumps({"project_dir": str(project_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
