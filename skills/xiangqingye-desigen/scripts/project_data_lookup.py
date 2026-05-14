#!/usr/bin/env python3
"""查询项目固定资产与切段清单。"""

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def asset_path(registry: dict, role: str) -> str:
    for asset in registry.get("assets", []):
        if asset.get("role") == role:
            return (asset.get("absolute_path") or asset.get("path") or "").strip()
    return ""


def manifest_status(manifest: dict) -> str:
    return str(manifest.get("status", "")).strip()


def confirmed_file(manifest: dict, segment_key: str) -> str:
    for item in manifest.get("segments", []):
        if str(item.get("key", "")).strip() == segment_key:
            return str(item.get("confirmed_file", "")).strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="查询项目固定资产与切段清单")
    subparsers = parser.add_subparsers(dest="command", required=True)

    asset_parser = subparsers.add_parser("asset", help="按 role 查询素材路径")
    asset_parser.add_argument("--registry", required=True, type=Path)
    asset_parser.add_argument("--role", required=True)

    status_parser = subparsers.add_parser("manifest-status", help="读取 cut_manifest 状态")
    status_parser.add_argument("--manifest", required=True, type=Path)

    file_parser = subparsers.add_parser("segment-file", help="按 segment key 查询 confirmed_file")
    file_parser.add_argument("--manifest", required=True, type=Path)
    file_parser.add_argument("--segment-key", required=True)

    args = parser.parse_args()

    if args.command == "asset":
        print(asset_path(load_json(args.registry), args.role))
    elif args.command == "manifest-status":
        print(manifest_status(load_json(args.manifest)))
    elif args.command == "segment-file":
        print(confirmed_file(load_json(args.manifest), args.segment_key))


if __name__ == "__main__":
    main()
