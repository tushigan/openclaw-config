#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from layer_plan_common import build_initial_state, build_parallel_plan, load_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--mode", choices=["draft", "final", "max"], default="max")
    parser.add_argument("--anchor-key")
    parser.add_argument("--plan-out")
    parser.add_argument("--state-out")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    
    # Semantic analyzer disabled by McKinsey Deep Thinking Engine rule to enforce exact 2 layers.
    # We will ignore any manifest semantic enrichment and strictly output background + foreground.

    plan = build_parallel_plan(manifest, mode=args.mode, preferred_anchor_key=args.anchor_key)
    state = build_initial_state(plan)

    plan_path = Path(args.plan_out) if args.plan_out else manifest_path.with_name("parallel-plan.json")
    state_path = Path(args.state_out) if args.state_out else manifest_path.with_name("parallel-state.json")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps({"plan_path": str(plan_path), "state_path": str(state_path), "anchor_key": plan["anchor_key"]}, ensure_ascii=False, indent=2))
        return

    print(plan_path)
    print(state_path)
    print(f'anchor={plan["anchor_key"]}')
    print(f'parallel={", ".join(plan["parallel_queue"]) if plan["parallel_queue"] else "-"}')


if __name__ == "__main__":
    main()
