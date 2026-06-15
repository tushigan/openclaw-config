#!/usr/bin/env python3
"""
OpenClaw 记忆系统 - 健康检查工具

功能：
1. 检查注册表与文件系统的一致性
2. 检查品牌档案完整性（必填字段）
3. 检查项目档案完整性
4. 生成健康报告

使用方式：
    python3 healthcheck.py              # 完整健康检查
    python3 healthcheck.py --quick      # 快速检查（仅一致性）
    python3 healthcheck.py --json       # JSON 格式输出
"""

import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib import get_project_root, read_json


def check_registry_consistency() -> dict:
    """检查注册表一致性"""
    from sync_registry import scan_filesystem, load_registry, detect_inconsistencies

    filesystem = scan_filesystem()
    registry = load_registry()
    issues = detect_inconsistencies(filesystem, registry)

    total_issues = (
        len(issues["missing_clients"]) +
        len(issues["missing_brands"]) +
        len(issues["orphan_clients"]) +
        len(issues["orphan_brands"])
    )

    return {
        "status": "healthy" if total_issues == 0 else "unhealthy",
        "total_issues": total_issues,
        "issues": issues
    }


def check_brand_profiles() -> dict:
    """检查品牌档案完整性"""
    project_root = Path(get_project_root())
    issues = []

    required_fields = ["brand_id", "brand_name", "brand_tone", "positioning", "target_audience"]

    for client_dir in project_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith('.') or client_dir.name.startswith('_'):
            continue

        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith('_'):
                continue

            profile_path = brand_dir / "_brand-profile.json"
            if profile_path.exists():
                profile = read_json(str(profile_path))
                missing_fields = []

                for field in required_fields:
                    if not profile.get(field):
                        missing_fields.append(field)

                if missing_fields:
                    issues.append({
                        "brand": profile.get("brand_name", brand_dir.name),
                        "client": client_dir.name,
                        "missing_fields": missing_fields,
                        "path": str(profile_path)
                    })

    return {
        "status": "healthy" if len(issues) == 0 else "warning",
        "total_issues": len(issues),
        "issues": issues
    }


def check_project_files() -> dict:
    """检查项目文件完整性"""
    project_root = Path(get_project_root())
    issues = []

    required_files = ["project.json", "brief.json", "strategy.json"]

    for client_dir in project_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith('.') or client_dir.name.startswith('_'):
            continue

        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith('_'):
                continue

            for project_dir in brand_dir.iterdir():
                if not project_dir.is_dir() or project_dir.name.startswith('_'):
                    continue

                # 检查是否是项目目录（至少有 project.json）
                project_json = project_dir / "project.json"
                if not project_json.exists():
                    continue

                missing_files = []
                for required_file in required_files:
                    if not (project_dir / required_file).exists():
                        missing_files.append(required_file)

                if missing_files:
                    project_data = read_json(str(project_json))
                    issues.append({
                        "project": project_data.get("campaign_name", project_dir.name),
                        "brand": brand_dir.name,
                        "client": client_dir.name,
                        "missing_files": missing_files,
                        "path": str(project_dir)
                    })

    return {
        "status": "healthy" if len(issues) == 0 else "warning",
        "total_issues": len(issues),
        "issues": issues
    }


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 记忆系统健康检查")
    parser.add_argument("--quick", action="store_true", help="快速检查（仅一致性）")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    report = {
        "timestamp": None,
        "overall_status": "healthy",
        "checks": {}
    }

    # 导入时间戳函数
    from lib import get_timestamp
    report["timestamp"] = get_timestamp()

    # 1. 注册表一致性检查
    print("🔍 检查注册表一致性...")
    registry_check = check_registry_consistency()
    report["checks"]["registry_consistency"] = registry_check

    if registry_check["status"] != "healthy":
        report["overall_status"] = "unhealthy"
        print(f"   ❌ 发现 {registry_check['total_issues']} 个不一致问题")
    else:
        print("   ✅ 注册表一致")

    if not args.quick:
        # 2. 品牌档案完整性检查
        print("\n🔍 检查品牌档案完整性...")
        brand_check = check_brand_profiles()
        report["checks"]["brand_profiles"] = brand_check

        if brand_check["total_issues"] > 0:
            if report["overall_status"] == "healthy":
                report["overall_status"] = "warning"
            print(f"   ⚠️ 发现 {brand_check['total_issues']} 个品牌档案缺少必填字段")
        else:
            print("   ✅ 品牌档案完整")

        # 3. 项目文件完整性检查
        print("\n🔍 检查项目文件完整性...")
        project_check = check_project_files()
        report["checks"]["project_files"] = project_check

        if project_check["total_issues"] > 0:
            if report["overall_status"] == "healthy":
                report["overall_status"] = "warning"
            print(f"   ⚠️ 发现 {project_check['total_issues']} 个项目缺少必需文件")
        else:
            print("   ✅ 项目文件完整")

    # 输出报告
    print("\n" + "="*60)
    if report["overall_status"] == "healthy":
        print("✅ 整体健康状态：正常")
    elif report["overall_status"] == "warning":
        print("⚠️ 整体健康状态：警告（有轻微问题）")
    else:
        print("❌ 整体健康状态：不健康（需要修复）")
    print("="*60)

    # 修复建议
    if registry_check["status"] != "healthy":
        print("\n💡 修复建议：")
        print("   运行 `python3 scripts/memory/sync_registry.py` 修复注册表不一致")

    if args.json:
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(report, ensure_ascii=False, indent=2))

    # 返回状态码
    if report["overall_status"] == "unhealthy":
        sys.exit(1)
    elif report["overall_status"] == "warning":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
