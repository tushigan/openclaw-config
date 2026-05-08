#!/usr/bin/env python3
"""把全局平台/品类方法论复制为项目快照。"""

import argparse
import json
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]


def load_profile(profile_file: Path, key: str) -> dict:
    data = json.loads(profile_file.read_text(encoding="utf-8"))
    profiles = data.get("profiles", {})
    if key not in profiles:
        available = ", ".join(sorted(profiles))
        raise SystemExit(f"找不到 profile: {key}。可选: {available}")
    result = profiles[key]
    result = {"key": key, **result}
    return result


def main():
    parser = argparse.ArgumentParser(description="创建项目平台/品类 profile 快照")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--platform", default="tmall_mobile", help="平台 profile key")
    parser.add_argument("--category", default="food_bakery", help="品类 profile key")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        raise SystemExit(f"项目目录不存在: {project_dir}")

    platform = load_profile(SKILL_DIR / "profiles" / "platform_profiles.json", args.platform)
    category = load_profile(SKILL_DIR / "profiles" / "category_profiles.json", args.category)

    (project_dir / "platform_profile.json").write_text(
        json.dumps(platform, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (project_dir / "category_profile.json").write_text(
        json.dumps(category, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"平台规则快照: {project_dir / 'platform_profile.json'}")
    print(f"品类规则快照: {project_dir / 'category_profile.json'}")


if __name__ == "__main__":
    main()
