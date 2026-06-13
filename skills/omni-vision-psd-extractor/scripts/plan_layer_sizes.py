#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from layer_plan_common import build_size_plan, load_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--mode", choices=["draft", "final", "max"], default="max")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = load_manifest(Path(args.manifest))
    planned = build_size_plan(manifest, args.mode)

    if args.as_json:
        print(json.dumps(planned, ensure_ascii=False, indent=2))
        return

    canvas = manifest["canvas"]
    print(f'mode={args.mode} canvas={canvas["width"]}x{canvas["height"]}')
    for item in planned:
        note_text = "；".join(item["notes"]) if item["notes"] else "-"
        print(
            f'{item["key"]:>14}  {item["group"]:<14}  '
            f'target={item["target_size"]:<12}  gen={item["suggested_size"]:<12}  max={item["max_supported_size"]:<12}  {note_text}'
        )


if __name__ == "__main__":
    main()
