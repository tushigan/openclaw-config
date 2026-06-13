#!/usr/bin/env python3
"""
OpenClaw 顶层记忆系统 - 数据迁移工具
从 workspace-business/projects 和 workspace/projects 迁移到根目录 /Users/a123/.openclaw/projects/
"""

import os
import sys
import json
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib import (
    get_project_root, ensure_dir, read_json, write_json,
    generate_id, get_timestamp, normalize_name
)


def migrate_business_projects():
    """迁移 workspace-business/projects 的数据"""

    source_root = "/Users/a123/.openclaw/workspace-business/projects"
    target_root = get_project_root()

    if not os.path.exists(source_root):
        print("⚠️ workspace-business/projects 不存在，跳过")
        return []

    migrated = []

    print("📦 开始迁移 workspace-business 项目数据...")

    # 遍历客户目录
    for client_name in os.listdir(source_root):
        client_source = os.path.join(source_root, client_name)

        if not os.path.isdir(client_source) or client_name.startswith('.'):
            continue

        print(f"\n处理客户: {client_name}")

        # 创建客户档案（如果不存在）
        client_target = os.path.join(target_root, client_name)
        client_profile_path = os.path.join(client_target, "_client-profile.json")

        if not os.path.exists(client_profile_path):
            # 创建新客户档案
            client_id = generate_id("CLI", client_name)
            client_data = {
                "client_id": client_id,
                "name": client_name,
                "name_en": "",
                "industry": "",
                "company_type": "客户",
                "contacts": [],
                "contracts": [],
                "business_notes": f"从 workspace-business 迁移",
                "tags": ["迁移"],
                "created_at": get_timestamp(),
                "updated_at": get_timestamp(),
                "_last_modified_by": "migration-script",
                "_migration_source": "workspace-business/projects"
            }

            ensure_dir(client_target)
            write_json(client_profile_path, client_data)
            print(f"  ✅ 创建客户档案: {client_name}")

        # 遍历项目目录
        for project_name in os.listdir(client_source):
            project_source = os.path.join(client_source, project_name)

            if not os.path.isdir(project_source) or project_name.startswith('.'):
                continue

            print(f"  处理项目: {project_name}")

            # 读取原项目数据
            project_json_source = os.path.join(project_source, "project.json")

            if not os.path.exists(project_json_source):
                print(f"    ⚠️ 项目缺少 project.json，跳过")
                continue

            old_project_data = read_json(project_json_source)

            # 在新系统中，项目需要归属到品牌下
            # 我们将项目名作为品牌名（业务项目通常是品牌级别的）
            brand_name = project_name
            brand_target = os.path.join(client_target, brand_name)
            brand_profile_path = os.path.join(brand_target, "_brand-profile.json")

            # 创建品牌档案（如果不存在）
            if not os.path.exists(brand_profile_path):
                brand_id = generate_id("BRD", brand_name)
                brand_data = {
                    "brand_id": brand_id,
                    "client_id": client_data.get("client_id"),
                    "name": brand_name,
                    "name_en": "",
                    "industry": "",
                    "category": "",
                    "positioning": "",
                    "brand_tone": "",
                    "target_audience": "",
                    "core_values": [],
                    "brand_story": "",
                    "competitive_advantages": [],
                    "tags": ["迁移"],
                    "assets_path": os.path.join(brand_target, "_brand-assets"),
                    "created_at": get_timestamp(),
                    "updated_at": get_timestamp(),
                    "_history": [],
                    "_last_modified_by": "migration-script",
                    "_migration_source": "workspace-business/projects"
                }

                ensure_dir(brand_target)
                ensure_dir(os.path.join(brand_target, "_brand-assets"))
                ensure_dir(os.path.join(brand_target, "_brand-assets", "logos"))
                ensure_dir(os.path.join(brand_target, "_brand-assets", "vi-manual"))
                ensure_dir(os.path.join(brand_target, "_brand-assets", "reference-images"))

                write_json(brand_profile_path, brand_data)
                print(f"    ✅ 创建品牌档案: {brand_name}")

            # 创建"业务对接"项目（保持原有的业务项目结构）
            campaign_name = "业务对接"
            campaign_target = os.path.join(brand_target, campaign_name)

            # 复制整个项目目录
            if os.path.exists(campaign_target):
                print(f"    ⚠️ 目标项目已存在，备份后覆盖")
                backup_path = f"{campaign_target}.backup.{get_timestamp()}"
                shutil.move(campaign_target, backup_path)

            shutil.copytree(project_source, campaign_target)
            print(f"    ✅ 迁移项目数据")

            # 创建新的 project.json（符合新架构）
            new_project_data = {
                "project_id": old_project_data.get("project_id", generate_id("PRJ", project_name)),
                "brand_id": brand_data.get("brand_id") if 'brand_data' in locals() else "",
                "client_id": client_data.get("client_id"),
                "campaign_name": campaign_name,
                "campaign_type": "业务对接",
                "start_date": old_project_data.get("created_at", ""),
                "deadline_date": "",
                "status": "active" if old_project_data.get("lifecycle_status") == "active" else "completed",
                "lifecycle_stage": old_project_data.get("current_stage", ""),
                "milestones": [],
                "project_summary": old_project_data.get("project_summary", ""),
                "current_goal": old_project_data.get("current_goal", ""),
                "tags": old_project_data.get("tags", []),
                "created_at": old_project_data.get("created_at", get_timestamp()),
                "updated_at": old_project_data.get("updated_at", get_timestamp()),
                "_last_modified_by": "migration-script",
                "brief_path": "",
                "strategy_path": "",
                "creative_direction_path": "",
                "_migration_source": "workspace-business/projects",
                "_original_data": old_project_data
            }

            write_json(os.path.join(campaign_target, "project.json"), new_project_data)

            migrated.append({
                "client": client_name,
                "brand": brand_name,
                "project": campaign_name,
                "source": project_source,
                "target": campaign_target
            })

    return migrated


def migrate_workspace_projects():
    """迁移 workspace/projects 的数据"""

    source_root = "/Users/a123/.openclaw/workspace/projects"
    target_root = get_project_root()

    if not os.path.exists(source_root):
        print("⚠️ workspace/projects 不存在，跳过")
        return []

    migrated = []

    print("\n📦 开始迁移 workspace 项目数据...")

    # workspace/projects 的结构是品牌直接在根目录下
    for brand_name in os.listdir(source_root):
        brand_source = os.path.join(source_root, brand_name)

        if not os.path.isdir(brand_source) or brand_name.startswith('.') or brand_name.startswith('_'):
            continue

        print(f"\n处理品牌: {brand_name}")

        # 检查是否有品牌档案
        brand_profile_source = os.path.join(brand_source, "_brand-profile.json")

        if not os.path.exists(brand_profile_source):
            print(f"  ⚠️ 缺少品牌档案，跳过")
            continue

        brand_data = read_json(brand_profile_source)

        # 获取客户信息（从品牌档案中提取或创建默认客户）
        client_name = brand_data.get("_client_name", "未分类客户")
        client_target = os.path.join(target_root, client_name)
        client_profile_path = os.path.join(client_target, "_client-profile.json")

        # 创建客户档案（如果不存在）
        if not os.path.exists(client_profile_path):
            client_id = generate_id("CLI", client_name)
            client_data = {
                "client_id": client_id,
                "name": client_name,
                "name_en": "",
                "industry": "",
                "company_type": "客户",
                "contacts": [],
                "contracts": [],
                "business_notes": f"从 workspace 迁移",
                "tags": ["迁移"],
                "created_at": get_timestamp(),
                "updated_at": get_timestamp(),
                "_last_modified_by": "migration-script",
                "_migration_source": "workspace/projects"
            }

            ensure_dir(client_target)
            write_json(client_profile_path, client_data)
            print(f"  ✅ 创建客户档案: {client_name}")
        else:
            client_data = read_json(client_profile_path)

        # 复制品牌目录
        brand_target = os.path.join(client_target, brand_name)

        if os.path.exists(brand_target):
            print(f"  ⚠️ 目标品牌已存在，备份后覆盖")
            backup_path = f"{brand_target}.backup.{get_timestamp()}"
            shutil.move(brand_target, backup_path)

        shutil.copytree(brand_source, brand_target)
        print(f"  ✅ 迁移品牌数据: {brand_name}")

        # 更新品牌档案中的 client_id
        brand_profile_target = os.path.join(brand_target, "_brand-profile.json")
        brand_data_new = read_json(brand_profile_target)
        brand_data_new["client_id"] = client_data.get("client_id")
        brand_data_new["_migration_source"] = "workspace/projects"
        write_json(brand_profile_target, brand_data_new)

        migrated.append({
            "client": client_name,
            "brand": brand_name,
            "source": brand_source,
            "target": brand_target
        })

    return migrated


def create_migration_report(business_migrated, workspace_migrated):
    """生成迁移报告"""

    report_path = os.path.join(get_project_root(), "_migration_report.json")

    report = {
        "migration_time": get_timestamp(),
        "business_projects": {
            "count": len(business_migrated),
            "items": business_migrated
        },
        "workspace_projects": {
            "count": len(workspace_migrated),
            "items": workspace_migrated
        },
        "total": len(business_migrated) + len(workspace_migrated)
    }

    write_json(report_path, report)

    print("\n" + "="*60)
    print("📊 迁移报告")
    print("="*60)
    print(f"workspace-business 迁移: {len(business_migrated)} 个项目")
    print(f"workspace 迁移: {len(workspace_migrated)} 个品牌")
    print(f"总计: {report['total']} 项")
    print(f"\n报告保存至: {report_path}")
    print("="*60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OpenClaw 记忆系统数据迁移")
    parser.add_argument('--dry-run', action='store_true', help='仅检查，不实际迁移')
    parser.add_argument('--skip-business', action='store_true', help='跳过 workspace-business 迁移')
    parser.add_argument('--skip-workspace', action='store_true', help='跳过 workspace 迁移')

    args = parser.parse_args()

    if args.dry_run:
        print("⚠️ DRY RUN 模式 - 仅检查，不实际迁移")

    business_migrated = []
    workspace_migrated = []

    if not args.skip_business:
        if not args.dry_run:
            business_migrated = migrate_business_projects()
        else:
            print("📋 检查 workspace-business/projects...")

    if not args.skip_workspace:
        if not args.dry_run:
            workspace_migrated = migrate_workspace_projects()
        else:
            print("📋 检查 workspace/projects...")

    if not args.dry_run:
        create_migration_report(business_migrated, workspace_migrated)
        print("\n✅ 迁移完成！")
        print("\n⚠️ 重要提示:")
        print("1. 原数据仍保留在原位置，建议验证后再删除")
        print("2. 请更新所有 skill 中的路径引用")
        print("3. 请测试所有依赖项目数据的功能")


if __name__ == '__main__':
    main()
