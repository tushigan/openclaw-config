#!/usr/bin/env python3
"""
OpenClaw 顶层记忆系统 - 统一查询接口
供所有 agent 和 skill 调用，快速查询品牌/项目信息
"""

import os
import sys
import argparse
import json
from typing import Optional, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib import (
    get_project_root, get_client_dir, get_brand_dir, get_project_dir,
    normalize_name, read_json, list_subdirs
)


def query_brand(brand_name: str, client_name: str = None) -> Optional[dict]:
    """
    查询品牌档案
    如果不指定 client_name，会在所有客户中搜索
    """
    project_root = get_project_root()

    if client_name:
        # 直接查询指定客户的品牌
        brand_name_normalized = normalize_name(brand_name)
        client_name_normalized = normalize_name(client_name)
        profile_path = os.path.join(
            get_brand_dir(client_name_normalized, brand_name_normalized),
            "_brand-profile.json"
        )
        return read_json(profile_path)

    # 在所有客户中搜索品牌
    brand_name_normalized = normalize_name(brand_name)

    for client_dir_name in list_subdirs(project_root):
        brand_dir = os.path.join(project_root, client_dir_name, brand_name_normalized)
        profile_path = os.path.join(brand_dir, "_brand-profile.json")

        if os.path.exists(profile_path):
            data = read_json(profile_path)
            if data:
                # 补充客户名称
                data['_query_client_name'] = client_dir_name
                return data

    return None


def query_project(
    brand_name: str,
    campaign_name: str = None,
    client_name: str = None,
    active_only: bool = False
) -> Optional[dict]:
    """
    查询项目档案
    - 如果指定 campaign_name，返回单个项目
    - 如果不指定，返回该品牌的所有项目列表
    - active_only=True 只返回活跃项目
    """

    # 先查询品牌
    brand_data = query_brand(brand_name, client_name)
    if not brand_data:
        return None

    client_name_found = brand_data.get('_query_client_name')
    brand_name_normalized = normalize_name(brand_name)
    brand_dir = get_brand_dir(client_name_found, brand_name_normalized)

    # 如果指定了项目名称，直接返回该项目
    if campaign_name:
        campaign_name_normalized = normalize_name(campaign_name)
        project_path = os.path.join(brand_dir, campaign_name_normalized, "project.json")
        return read_json(project_path)

    # 否则返回所有项目
    projects = []
    for item in list_subdirs(brand_dir):
        project_path = os.path.join(brand_dir, item, "project.json")
        if os.path.exists(project_path):
            project_data = read_json(project_path)
            if project_data:
                if active_only and project_data.get('status') != 'active':
                    continue
                projects.append(project_data)

    return {
        "brand_name": brand_name,
        "client_name": client_name_found,
        "projects": projects,
        "total": len(projects)
    }


def query_active_project(brand_name: str, client_name: str = None) -> Optional[dict]:
    """
    查询品牌的活跃项目（只返回第一个活跃项目）
    """
    result = query_project(brand_name, active_only=True, client_name=client_name)
    if result and result.get('projects'):
        return result['projects'][0]
    return None


def query_brand_assets(brand_name: str, client_name: str = None) -> Optional[dict]:
    """
    查询品牌资产库路径
    """
    brand_data = query_brand(brand_name, client_name)
    if not brand_data:
        return None

    assets_path = brand_data.get('assets_path')

    if not os.path.exists(assets_path):
        return None

    # 列出资产文件
    assets = {
        "assets_path": assets_path,
        "logos": [],
        "vi_manual": [],
        "reference_images": []
    }

    logos_dir = os.path.join(assets_path, "logos")
    if os.path.exists(logos_dir):
        assets["logos"] = [
            os.path.join(logos_dir, f)
            for f in os.listdir(logos_dir)
            if os.path.isfile(os.path.join(logos_dir, f))
        ]

    vi_dir = os.path.join(assets_path, "vi-manual")
    if os.path.exists(vi_dir):
        assets["vi_manual"] = [
            os.path.join(vi_dir, f)
            for f in os.listdir(vi_dir)
            if os.path.isfile(os.path.join(vi_dir, f))
        ]

    ref_dir = os.path.join(assets_path, "reference-images")
    if os.path.exists(ref_dir):
        assets["reference_images"] = [
            os.path.join(ref_dir, f)
            for f in os.listdir(ref_dir)
            if os.path.isfile(os.path.join(ref_dir, f))
        ]

    return assets


def query_all_brands() -> List[dict]:
    """列出所有品牌（简要信息）"""
    brands = []
    project_root = get_project_root()

    if not os.path.exists(project_root):
        return []

    for client_dir in list_subdirs(project_root):
        client_path = os.path.join(project_root, client_dir)

        for brand_dir in list_subdirs(client_path):
            profile_path = os.path.join(client_path, brand_dir, "_brand-profile.json")
            if os.path.exists(profile_path):
                data = read_json(profile_path)
                if data:
                    brands.append({
                        "brand_id": data.get("brand_id"),
                        "name": data.get("name"),
                        "client": client_dir,
                        "brand_tone": data.get("brand_tone", ""),
                        "positioning": data.get("positioning", ""),
                        "target_audience": data.get("target_audience", "")
                    })

    return brands


def query_all_active_projects(include_all: bool = False) -> List[dict]:
    """
    列出所有活跃项目

    Args:
        include_all: 如果为 True，返回所有项目；如果为 False（默认），只返回 status='active' 的项目
    """
    projects = []
    project_root = get_project_root()

    if not os.path.exists(project_root):
        return []

    # 递归扫描所有 project.json 文件（不限深度）
    for root, dirs, files in os.walk(project_root):
        # 跳过隐藏目录和特殊目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('_')]

        if 'project.json' in files:
            project_path = os.path.join(root, 'project.json')
            data = read_json(project_path)

            if data:
                # 如果 include_all 为 True，或者项目状态为 active，则包含该项目
                if include_all or data.get('status') == 'active':
                    # 提取相对路径作为项目标识
                    rel_path = os.path.relpath(root, project_root)
                    path_parts = rel_path.split(os.sep)

                    # 尝试解析客户/品牌/项目结构
                    client = path_parts[0] if len(path_parts) > 0 else "未知客户"
                    brand = path_parts[1] if len(path_parts) > 1 else "未知品牌"
                    campaign = path_parts[2] if len(path_parts) > 2 else "未知项目"

                    # 如果路径过深（超过3层），标记为子项目
                    is_subproject = len(path_parts) > 3

                    projects.append({
                        "project_id": data.get("project_id", rel_path),
                        "campaign_name": data.get("campaign_name", campaign),
                        "brand": brand,
                        "client": client,
                        "lifecycle_stage": data.get("lifecycle_stage", ""),
                        "deadline_date": data.get("deadline_date", ""),
                        "status": data.get("status", "unknown"),
                        "path": rel_path,
                        "is_subproject": is_subproject
                    })

    return projects


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw 记忆查询接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 查询品牌档案
  python3 query.py brand --name "优食家族"

  # 查询品牌档案（指定客户）
  python3 query.py brand --name "优食家族" --client "泓一"

  # 查询活跃项目
  python3 query.py project --brand "优食家族" --active

  # 查询品牌资产
  python3 query.py assets --brand "优食家族"

  # 列出所有品牌
  python3 query.py list-brands

  # 列出所有活跃项目
  python3 query.py list-projects
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='查询命令')

    # brand 命令
    brand_parser = subparsers.add_parser('brand', help='查询品牌档案')
    brand_parser.add_argument('--name', required=True, help='品牌名称')
    brand_parser.add_argument('--client', default=None, help='客户名称（可选）')
    brand_parser.add_argument('--json', action='store_true', help='输出 JSON 格式')

    # project 命令
    project_parser = subparsers.add_parser('project', help='查询项目')
    project_parser.add_argument('--brand', required=True, help='品牌名称')
    project_parser.add_argument('--campaign', default=None, help='项目名称（可选）')
    project_parser.add_argument('--client', default=None, help='客户名称（可选）')
    project_parser.add_argument('--active', action='store_true', help='只返回活跃项目')
    project_parser.add_argument('--json', action='store_true', help='输出 JSON 格式')

    # assets 命令
    assets_parser = subparsers.add_parser('assets', help='查询品牌资产')
    assets_parser.add_argument('--brand', required=True, help='品牌名称')
    assets_parser.add_argument('--client', default=None, help='客户名称（可选）')
    assets_parser.add_argument('--json', action='store_true', help='输出 JSON 格式')

    # list-brands 命令
    list_brands_parser = subparsers.add_parser('list-brands', help='列出所有品牌')
    list_brands_parser.add_argument('--json', action='store_true', help='输出 JSON 格式')

    # list-projects 命令
    list_projects_parser = subparsers.add_parser('list-projects', help='列出所有项目')
    list_projects_parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    list_projects_parser.add_argument('--active', action='store_true', help='只显示 status=active 的项目')
    list_projects_parser.add_argument('--all', action='store_true', help='显示所有项目（包括非 active 状态）')

    args = parser.parse_args()

    result = None

    if args.command == 'brand':
        result = query_brand(args.name, args.client)
        if result and not args.json:
            print(f"✅ 品牌档案: {result.get('name')}")
            print(f"   品牌ID: {result.get('brand_id')}")
            print(f"   客户: {result.get('_query_client_name', 'N/A')}")
            print(f"   定位: {result.get('positioning', '未设置')}")
            print(f"   调性: {result.get('brand_tone', '未设置')}")
            print(f"   受众: {result.get('target_audience', '未设置')}")
            print(f"   核心价值: {', '.join(result.get('core_values', []))}")
            print(f"   资产路径: {result.get('assets_path', 'N/A')}")
        elif not result:
            print(f"❌ 品牌档案不存在: {args.name}")

    elif args.command == 'project':
        if args.campaign:
            result = query_project(args.brand, args.campaign, args.client)
            if result and not args.json:
                print(f"✅ 项目档案: {result.get('campaign_name')}")
                print(f"   项目ID: {result.get('project_id')}")
                print(f"   品牌: {args.brand}")
                print(f"   状态: {result.get('status')}")
                print(f"   阶段: {result.get('lifecycle_stage', '未设置')}")
                print(f"   截止日期: {result.get('deadline_date', '未设置')}")
        else:
            result = query_project(args.brand, client_name=args.client, active_only=args.active)
            if result and not args.json:
                print(f"✅ 品牌项目列表: {result.get('brand_name')}")
                print(f"   总数: {result.get('total')}")
                for proj in result.get('projects', []):
                    status_emoji = "🟢" if proj.get('status') == 'active' else "⚪"
                    print(f"   {status_emoji} {proj.get('campaign_name')} - {proj.get('lifecycle_stage', 'N/A')}")

    elif args.command == 'assets':
        result = query_brand_assets(args.brand, args.client)
        if result and not args.json:
            print(f"✅ 品牌资产: {args.brand}")
            print(f"   资产路径: {result.get('assets_path')}")
            print(f"   Logo: {len(result.get('logos', []))} 个")
            print(f"   VI手册: {len(result.get('vi_manual', []))} 个")
            print(f"   参考图: {len(result.get('reference_images', []))} 个")

    elif args.command == 'list-brands':
        result = query_all_brands()
        if not args.json:
            print(f"📋 品牌总数: {len(result)}")
            for brand in result:
                print(f"   • {brand['name']} ({brand['client']}) - {brand['brand_tone']}")

    elif args.command == 'list-projects':
        # 默认显示所有项目，除非明确指定 --active
        include_all = not args.active if hasattr(args, 'active') else True
        if hasattr(args, 'all') and args.all:
            include_all = True

        result = query_all_active_projects(include_all=include_all)
        if not args.json:
            if include_all:
                print(f"📋 项目总数: {len(result)}")
            else:
                print(f"📋 活跃项目总数: {len(result)}")
            for proj in result:
                status_emoji = "🟢" if proj.get('status') == 'active' else "○"
                print(f"   {status_emoji} {proj['campaign_name']} ({proj['brand']}) - {proj['lifecycle_stage']} [{proj.get('status', 'unknown')}]")

    else:
        parser.print_help()
        sys.exit(1)

    # JSON 输出
    if args.json and result:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回码
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
