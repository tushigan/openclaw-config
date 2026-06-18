#!/usr/bin/env python3
"""Update project stage checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agency_project import update_stage_checkpoint


def main() -> None:
    parser = argparse.ArgumentParser(description="Update project stage checkpoint")
    parser.add_argument("--project-dir", required=True, help="Project directory")
    parser.add_argument(
        "--stage",
        required=True,
        choices=[
            "brief_intake",
            "problem_alignment",
            "research",
            "strategy",
            "creative_direction",
            "direction_confirmation",
            "execution",
        ],
        help="Stage name",
    )
    parser.add_argument(
        "--status",
        required=True,
        choices=["pending", "in_progress", "completed"],
        help="Stage status",
    )
    parser.add_argument(
        "--user-confirmed",
        action="store_true",
        help="Mark as user confirmed",
    )

    args = parser.parse_args()

    update_stage_checkpoint(
        project_dir=Path(args.project_dir),
        stage=args.stage,
        status=args.status,
        user_confirmed=args.user_confirmed,
    )

    print(json.dumps({"success": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
