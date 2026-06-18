#!/usr/bin/env python3
"""
OpenClaw 记忆系统 - 注册表一致性修复工具

功能：
1. 扫描 projects/ 目录下所有客户和品牌档案
2. 检测未注册到 _registry.json 的客户/品牌
3. 自动补充注册，修复数据不一致

使用方式：
    python3 sync_registry.py --dry-run    # 预览模式，不实际修改
    python3 sync_registry.py              # 执行修复
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib import (
    get_project_root, read_json, write_json,
    normalize_name, get_timestamp, generate_id
)


def scan_filesystem() -> dict:
    """扫描文件系统，获取所有客户和品牌"""
    project_root = Path(get_project_root())

    clients = {}  # {client_name: {brands: [...]}}
    brands = {}   # {brand_name: {client: ..., profile: ...}}

    if not project_root.exists():
        return {"clients": clients, "brands": brands}

    # 遍历客户目录
    for client_dir in project_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith('.') or client_dir.name.startswith('_'):
            continue

        client_name = client_dir.name
        client_profile_path = client_dir / "_client-profile.json"

        # 检查是否有客户档案
        if client_profile_path.exists():
            client_data = read_json(str(client_profile_path))
            clients[client_name] = {
                "has_profile": True,
                "client_id": client_data.get("client_id"),
                "created_at": client_data.get("created_at"),
                "brands": []
            }
        else:
            clients[client_name] = {
                "has_profile": False,
                "client_id": None,
                "created_at": None,
                "brands": []
            }

        # 遍历品牌目录
        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith('_'):
                continue

            brand_name = brand_dir.name
            brand_profile_path = brand_dir / "_brand-profile.json"

            if brand_profile_path.exists():
                brand_data = read_json(str(brand_profile_path))
                brands[brand_name] = {
                    "client": client_name,
                    "brand_id": brand_data.get("brand_id"),
                    "created_at": brand_data.get("created_at"),
                    "profile": brand_data
                }
                clients[client_name]["brands"].append(brand_name)

    return {"clients": clients, "brands": brands}


def load_registry() -> dict:
    """加载注册表"""
    registry_path = Path(get_project_root()) / "_registry.json"

    if registry_path.exists():
        return read_json(str(registry_path))
    else:
        return {
            "version": "2.0",
            "last_updated": get_timestamp(),
            "clients": [],
            "brands": [],
            "projects": [],
            "tasks": []
        }


def detect_inconsistencies(filesystem: dict, registry: dict) -> dict:
    """检测不一致"""
    issues = {
        "missing_clients": [],      # 文件系统有但注册表没有的客户
        "missing_brands": [],        # 文件系统有但注册表没有的品牌
        "orphan_clients": [],        # 注册表有但文件系统没有的客户
        "orphan_brands": []          # 注册表有但文件系统没有的品牌
    }

    # 检查缺失的客户
    registry_clients = {c["name"]: c for c in registry.get("clients", [])}
    for client_name, client_info in filesystem["clients"].items():
        if client_name not in registry_clients:
            issues["missing_clients"].append({
                "name": client_name,
                "has_profile": client_info["has_profile"],
                "brand_count": len(client_info["brands"])
            })

    # 检查缺失的品牌
    registry_brands = {b["name"]: b for b in registry.get("brands", [])}
    for brand_name, brand_info in filesystem["brands"].items():
        if brand_name not in registry_brands:
            issues["missing_brands"].append({
                "name": brand_name,
                "client": brand_info["client"],
                "brand_id": brand_info["brand_id"]
            })

    # 检查孤立的客户（注册表有但文件系统没有）
    for client_name in registry_clients:
        if client_name not in filesystem["clients"]:
            issues["orphan_clients"].append(registry_clients[client_name])

    # 检查孤立的品牌（注册表有但文件系统没有）
    for brand_name in registry_brands:
        if brand_name not in filesystem["brands"]:
            issues["orphan_brands"].append(registry_brands[brand_name])

    return issues


def fix_inconsistencies(filesystem: dict, registry: dict, issues: dict) -> dict:
    """修复不一致"""
    fixed_count = 0

    # 补充缺失的客户
    for missing_client in issues["missing_clients"]:
        client_name = missing_client["name"]
        client_info = filesystem["clients"][client_name]

        # 生成或使用已有的客户ID
        client_id = client_info["client_id"]
        if not client_id:
            client_id = generate_id("CLI", client_name)

        registry["clients"].append({
            "id": client_id,
            "name": client_name,
            "created_at": client_info["created_at"] or get_timestamp()
        })
        fixed_count += 1
        print(f"✅ 补充客户注册: {client_name} (ID: {client_id})")

    # 补充缺失的品牌
    for missing_brand in issues["missing_brands"]:
        brand_name = missing_brand["name"]
        brand_info = filesystem["brands"][brand_name]

        # 生成或使用已有的品牌ID
        brand_id = brand_info["brand_id"]
        if not brand_id:
            brand_id = generate_id("BRD", brand_name)

        registry["brands"].append({
            "id": brand_id,
            "name": brand_name,
            "created_at": brand_info["created_at"] or get_timestamp()
        })
        fixed_count += 1
        print(f"✅ 补充品牌注册: {brand_name} (客户: {brand_info['client']}, ID: {brand_id})")

    # 清理孤立的客户记录
    for orphan_client in issues["orphan_clients"]:
        registry["clients"] = [c for c in registry["clients"] if c["name"] != orphan_client["name"]]
        fixed_count += 1
        print(f"🧹 清理孤立客户记录: {orphan_client['name']}")

    # 清理孤立的品牌记录
    for orphan_brand in issues["orphan_brands"]:
        registry["brands"] = [b for b in registry["brands"] if b["name"] != orphan_brand["name"]]
        fixed_count += 1
        print(f"🧹 清理孤立品牌记录: {orphan_brand['name']}")

    # 更新时间戳
    if fixed_count > 0:
        registry["last_updated"] = get_timestamp()

    return registry, fixed_count


def main():
    parser = argparse.ArgumentParser(description="注册表一致性修复工具")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    print("🔍 扫描文件系统...")
    filesystem = scan_filesystem()

    print(f"📊 发现 {len(filesystem['clients'])} 个客户，{len(filesystem['brands'])} 个品牌")

    print("\n🔍 加载注册表...")
    registry = load_registry()

    print(f"📊 注册表记录：{len(registry.get('clients', []))} 个客户，{len(registry.get('brands', []))} 个品牌")

    print("\n🔍 检测不一致...")
    issues = detect_inconsistencies(filesystem, registry)

    # 统计问题
    total_issues = (
        len(issues["missing_clients"]) +
        len(issues["missing_brands"]) +
        len(issues["orphan_clients"]) +
        len(issues["orphan_brands"])
    )

    if total_issues == 0:
        print("✅ 数据一致，无需修复")
        return

    print(f"\n⚠️ 发现 {total_issues} 个问题：")

    if issues["missing_clients"]:
        print(f"\n❌ 缺失客户注册（{len(issues['missing_clients'])} 个）：")
        for client in issues["missing_clients"]:
            print(f"   • {client['name']} - {client['brand_count']} 个品牌")

    if issues["missing_brands"]:
        print(f"\n❌ 缺失品牌注册（{len(issues['missing_brands'])} 个）：")
        for brand in issues["missing_brands"]:
            print(f"   • {brand['name']} (客户: {brand['client']})")

    if issues["orphan_clients"]:
        print(f"\n⚠️ 孤立客户记录（{len(issues['orphan_clients'])} 个，注册表有但文件系统无）：")
        for client in issues["orphan_clients"]:
            print(f"   • {client['name']}")

    if issues["orphan_brands"]:
        print(f"\n⚠️ 孤立品牌记录（{len(issues['orphan_brands'])} 个，注册表有但文件系统无）：")
        for brand in issues["orphan_brands"]:
            print(f"   • {brand['name']}")

    if args.dry_run:
        print("\n🔍 [预览模式] 不执行实际修复")
        return

    # 执行修复
    print("\n🔧 执行修复...")
    updated_registry, fixed_count = fix_inconsistencies(filesystem, registry, issues)

    if fixed_count > 0:
        # 保存更新后的注册表
        registry_path = os.path.join(get_project_root(), "_registry.json")
        if write_json(registry_path, updated_registry):
            print(f"\n✅ 修复完成！已补充 {fixed_count} 条注册记录")
            print(f"   注册表路径: {registry_path}")
        else:
            print(f"\n❌ 写入注册表失败")
            sys.exit(1)
    else:
        print("\n✅ 无需修复")

    if args.json:
        print("\n--- JSON OUTPUT ---")
        print(json.dumps({
            "total_issues": total_issues,
            "fixed_count": fixed_count,
            "issues": issues
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
