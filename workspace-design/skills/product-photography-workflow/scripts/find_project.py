#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import DEFAULT_OUTPUT_ROOT, find_project_candidates  # noqa: E402


def confidence_label(candidates: list[dict]) -> str:
    if not candidates:
        return "none"
    top = int(candidates[0].get("score", 0))
    second = int(candidates[1].get("score", 0)) if len(candidates) > 1 else 0
    if top >= 100 or top - second >= 20:
        return "high"
    if top >= 70:
        return "medium"
    return "low"


def status_label(candidates: list[dict]) -> str:
    if not candidates:
        return "not_found"
    if len(candidates) == 1:
        return "matched"
    top = int(candidates[0].get("score", 0))
    second = int(candidates[1].get("score", 0))
    return "ambiguous" if second >= top - 5 else "matched"


def main() -> None:
    parser = argparse.ArgumentParser(description="按自然语言线索查找产品摄影项目")
    parser.add_argument("--query", required=True, help="项目名、产品名或记忆线索")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="项目输出根目录")
    parser.add_argument("--limit", type=int, default=3, help="最多返回候选数量")
    args = parser.parse_args()

    candidates = find_project_candidates(args.query, Path(args.output_root).resolve(), limit=args.limit)
    print(f"status={status_label(candidates)}")
    print(f"confidence={confidence_label(candidates)}")
    print(f"candidate_count={len(candidates)}")
    if candidates:
        top = candidates[0]
        print(f"project_dir={top['project_dir']}")
        print(f"project_id={top['project_id']}")
        print(f"project_name={top['project_name']}")
        print(f"product_name={top['product_name']}")
        print(f"task_count={top['task_count']}")
    for index, candidate in enumerate(candidates, start=1):
        prefix = f"candidate_{index}"
        print(f"{prefix}_project_dir={candidate['project_dir']}")
        print(f"{prefix}_project_name={candidate['project_name']}")
        print(f"{prefix}_product_name={candidate['product_name']}")
        print(f"{prefix}_score={candidate['score']}")


if __name__ == "__main__":
    main()
