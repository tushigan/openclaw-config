#!/usr/bin/env python3
"""
OpenClaw 顶层记忆系统 - 品牌管理
提供品牌档案的 CRUD 操作 + 冲突检测
"""

import os
import sys
import argparse
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib import (
    BrandProfile, HistoryEntry,
    get_timestamp, generate_id, ensure_dir, read_json, write_json,
    get_project_root, get_client_dir, get_brand_dir, normalize_name,
    validate_required_fields, generate_diff
)


# 需要冲突检测的字段
CONFLICT_FIELDS = [
    'brand_tone',           # 品牌调性
    'positioning',          # 定位
    'target_audience',      # 目标受众
    'core_values',          # 核心价值观
]


def create_brand(
    client_name: str,
    brand_name: str,
    brand_name_en: str = "",
    industry: str = "",
    category: str = "",
    positioning: str = "",
    brand_tone: str = "",
    target_audience: str = "",
    core_values: list = None,
    brand_story: str = "",
    tags: list = None,
    agent_id: str = "system"
) -> dict:
    """创建品牌档案"""

    client_name = normalize_name(client_name)
    brand_name_normalized = normalize_name(brand_name)

    # 检查客户是否存在
    client_dir = get_client_dir(client_name)
    if not os.path.exists(os.path.join(client_dir, "_client-profile.json")):
        print(f"❌ 客户档案不存在: {client_name}")
        print(f"   请先创建客户档案: python3 client.py create --name \"{client_name}\"")
        return None

    # 检查品牌是否已存在
    brand_dir = get_brand_dir(client_name, brand_name_normalized)
    profile_path = os.path.join(brand_dir, "_brand-profile.json")

    if os.path.exists(profile_path):
        print(f"⚠️ 品牌档案已存在: {brand_name}")
        existing = read_json(profile_path)
        return existing

    # 获取客户 ID
    client_data = read_json(os.path.join(client_dir, "_client-profile.json"))
    client_id = client_data.get('client_id')

    # 生成品牌 ID
    brand_id = generate_id("BRD", brand_name)

    # 创建品牌档案
    profile = BrandProfile(
        brand_id=brand_id,
        client_id=client_id,
        name=brand_name,
        name_en=brand_name_en,
        industry=industry,
        category=category,
        positioning=positioning,
        brand_tone=brand_tone,
        target_audience=target_audience,
        core_values=core_values or [],
        brand_story=brand_story,
        tags=tags or [],
        assets_path=os.path.join(brand_dir, "_brand-assets"),
        created_at=get_timestamp(),
        updated_at=get_timestamp(),
        _last_modified_by=agent_id
    )

    # 创建目录结构
    ensure_dir(brand_dir)
    ensure_dir(os.path.join(brand_dir, "_brand-assets"))
    ensure_dir(os.path.join(brand_dir, "_brand-assets", "logos"))
    ensure_dir(os.path.join(brand_dir, "_brand-assets", "vi-manual"))
    ensure_dir(os.path.join(brand_dir, "_brand-assets", "reference-images"))

    # 保存品牌档案
    data = profile.to_dict()
    if write_json(profile_path, data):
        print(f"✅ 品牌档案创建成功: {brand_name}")
        print(f"   ID: {brand_id}")
        print(f"   客户: {client_name}")
        print(f"   路径: {profile_path}")

        # 更新注册表
        from client import update_registry
        update_registry(brand_id, brand_name, "brand")

        return data
    else:
        print(f"❌ 品牌档案创建失败")
        return None


def get_brand(client_name: str, brand_name: str) -> Optional[dict]:
    """获取品牌档案"""
    client_name = normalize_name(client_name)
    brand_name = normalize_name(brand_name)

    profile_path = os.path.join(get_brand_dir(client_name, brand_name), "_brand-profile.json")

    data = read_json(profile_path)
    if data:
        print(f"✅ 品牌档案: {data.get('name')}")
        print(f"   ID: {data.get('brand_id')}")
        print(f"   客户: {client_name}")
        print(f"   定位: {data.get('positioning', '未设置')}")
        print(f"   调性: {data.get('brand_tone', '未设置')}")
        print(f"   受众: {data.get('target_audience', '未设置')}")
        print(f"   核心价值: {', '.join(data.get('core_values', []))}")
    else:
        print(f"❌ 品牌档案不存在: {brand_name}")

    return data


def update_brand(
    client_name: str,
    brand_name: str,
    field: str,
    value: any,
    agent_id: str = "system",
    require_confirmation: bool = True,
    user_confirmed: bool = False
) -> dict:
    """更新品牌档案（带冲突检测）"""

    client_name = normalize_name(client_name)
    brand_name = normalize_name(brand_name)

    profile_path = os.path.join(get_brand_dir(client_name, brand_name), "_brand-profile.json")

    data = read_json(profile_path)
    if not data:
        print(f"❌ 品牌档案不存在: {brand_name}")
        return {"error": "品牌档案不存在"}

    # 获取旧值
    old_value = data.get(field)

    # 如果值相同，无需更新
    if old_value == value:
        print(f"ℹ️ 字段值未变化: {field}")
        return {"status": "unchanged", "field": field, "value": value}

    # 冲突检测
    if field in CONFLICT_FIELDS and require_confirmation:
        conflict = detect_conflict(data, field, old_value, value)
        if conflict and not user_confirmed:
            print(f"⚠️ 检测到冲突，需要用户确认")
            print(conflict['message'])
            return conflict

    # 记录历史
    if '_history' not in data:
        data['_history'] = []

    history_entry = HistoryEntry(
        timestamp=get_timestamp(),
        field=field,
        old_value=old_value,
        new_value=value,
        changed_by=agent_id,
        user_confirmed=user_confirmed,
        reason=""
    )
    data['_history'].append(history_entry.__dict__)

    # 更新字段
    data[field] = value
    data['updated_at'] = get_timestamp()
    data['_last_modified_by'] = agent_id

    if write_json(profile_path, data):
        print(f"✅ 品牌档案更新成功")
        print(f"   字段: {field}")
        print(f"   原值: {old_value}")
        print(f"   新值: {value}")
        return {"status": "updated", "field": field, "old_value": old_value, "new_value": value}
    else:
        print(f"❌ 品牌档案更新失败")
        return {"error": "写入失败"}


def detect_conflict(data: dict, field: str, old_value: any, new_value: any) -> Optional[dict]:
    """检测冲突"""

    if old_value == new_value:
        return None

    # 生成对比
    diff = generate_diff(old_value, new_value)

    # 分析影响范围
    impact = analyze_impact(data, field)

    # 生成用户确认消息
    message = f"""⚠️ 检测到品牌档案变更

品牌：{data.get('name')}
字段：{field}
原值：{old_value}
新值：{new_value}

变更对比：
{diff}

影响范围：
{impact}

是否确认此变更？
• 若确认，请在命令中添加 --user-confirmed 参数重新执行
• 若取消，请忽略此次更新"""

    return {
        "status": "conflict",
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "diff": diff,
        "impact": impact,
        "message": message,
        "requires_confirmation": True
    }


def analyze_impact(data: dict, field: str) -> str:
    """分析变更影响范围"""

    brand_name = data.get('name')
    client_name = None

    # 查找客户名称
    project_root = get_project_root()
    for client_dir in os.listdir(project_root):
        client_path = os.path.join(project_root, client_dir)
        if os.path.isdir(client_path):
            brand_path = os.path.join(client_path, normalize_name(brand_name))
            if os.path.exists(brand_path):
                client_name = client_dir
                break

    if not client_name:
        return "无法确定影响范围"

    # 统计项目数量
    brand_dir = get_brand_dir(client_name, normalize_name(brand_name))
    project_count = 0
    active_projects = []

    for item in os.listdir(brand_dir):
        item_path = os.path.join(brand_dir, item)
        if os.path.isdir(item_path) and not item.startswith('_'):
            project_json = os.path.join(item_path, "project.json")
            if os.path.exists(project_json):
                project_count += 1
                proj_data = read_json(project_json)
                if proj_data and proj_data.get('status') == 'active':
                    active_projects.append(proj_data.get('campaign_name'))

    impact_lines = []
    impact_lines.append(f"- 关联项目总数：{project_count} 个")
    if active_projects:
        impact_lines.append(f"- 活跃项目：{len(active_projects)} 个")
        if len(active_projects) <= 3:
            for proj in active_projects:
                impact_lines.append(f"  • {proj}")
    else:
        impact_lines.append(f"- 当前无活跃项目")

    # 字段特定影响
    field_impacts = {
        'brand_tone': "品牌调性变更将影响后续所有创意和视觉产出",
        'positioning': "定位变更将影响品牌策略和传播方向",
        'target_audience': "目标受众变更将影响内容策略和渠道选择",
        'core_values': "核心价值观变更将影响品牌叙事和沟通策略"
    }

    if field in field_impacts:
        impact_lines.append(f"- {field_impacts[field]}")

    return "\n".join(impact_lines)


def list_brands(client_name: str = None) -> list:
    """列出品牌"""

    brands = []
    project_root = get_project_root()

    if not os.path.exists(project_root):
        print("📂 项目根目录不存在")
        return []

    # 如果指定客户，只列出该客户的品牌
    if client_name:
        client_name = normalize_name(client_name)
        client_dir = get_client_dir(client_name)
        if not os.path.exists(client_dir):
            print(f"❌ 客户不存在: {client_name}")
            return []

        for item in os.listdir(client_dir):
            if item.startswith('_'):
                continue
            brand_dir = os.path.join(client_dir, item)
            if os.path.isdir(brand_dir):
                profile_path = os.path.join(brand_dir, "_brand-profile.json")
                if os.path.exists(profile_path):
                    data = read_json(profile_path)
                    if data:
                        brands.append({
                            'name': data.get('name'),
                            'brand_id': data.get('brand_id'),
                            'client': client_name,
                            'positioning': data.get('positioning', ''),
                            'brand_tone': data.get('brand_tone', '')
                        })
    else:
        # 列出所有客户的所有品牌
        for client_item in os.listdir(project_root):
            if client_item.startswith('.'):
                continue
            client_path = os.path.join(project_root, client_item)
            if os.path.isdir(client_path):
                for brand_item in os.listdir(client_path):
                    if brand_item.startswith('_'):
                        continue
                    brand_dir = os.path.join(client_path, brand_item)
                    if os.path.isdir(brand_dir):
                        profile_path = os.path.join(brand_dir, "_brand-profile.json")
                        if os.path.exists(profile_path):
                            data = read_json(profile_path)
                            if data:
                                brands.append({
                                    'name': data.get('name'),
                                    'brand_id': data.get('brand_id'),
                                    'client': client_item,
                                    'positioning': data.get('positioning', ''),
                                    'brand_tone': data.get('brand_tone', '')
                                })

    if brands:
        print(f"📋 品牌列表（共 {len(brands)} 个）：")
        for b in brands:
            print(f"   • {b['name']} ({b['client']}) - {b['brand_tone']}")
    else:
        print("📂 暂无品牌档案")

    return brands


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 品牌管理")
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # create 命令
    create_parser = subparsers.add_parser('create', help='创建品牌档案')
    create_parser.add_argument('--client', required=True, help='客户名称')
    create_parser.add_argument('--name', required=True, help='品牌名称')
    create_parser.add_argument('--name-en', default="", help='英文名称')
    create_parser.add_argument('--industry', default="", help='行业')
    create_parser.add_argument('--category', default="", help='品类')
    create_parser.add_argument('--positioning', default="", help='定位')
    create_parser.add_argument('--brand-tone', default="", help='品牌调性')
    create_parser.add_argument('--target-audience', default="", help='目标受众')
    create_parser.add_argument('--core-values', nargs='*', default=[], help='核心价值观')
    create_parser.add_argument('--brand-story', default="", help='品牌故事')
    create_parser.add_argument('--tags', nargs='*', default=[], help='标签')
    create_parser.add_argument('--agent', default='system', help='操作者 agent ID')

    # get 命令
    get_parser = subparsers.add_parser('get', help='获取品牌档案')
    get_parser.add_argument('--client', required=True, help='客户名称')
    get_parser.add_argument('--name', required=True, help='品牌名称')

    # update 命令
    update_parser = subparsers.add_parser('update', help='更新品牌档案')
    update_parser.add_argument('--client', required=True, help='客户名称')
    update_parser.add_argument('--name', required=True, help='品牌名称')
    update_parser.add_argument('--field', required=True, help='字段名')
    update_parser.add_argument('--value', required=True, help='新值')
    update_parser.add_argument('--agent', default='system', help='操作者 agent ID')
    update_parser.add_argument('--user-confirmed', action='store_true', help='用户已确认变更')
    update_parser.add_argument('--no-conflict-check', action='store_true', help='跳过冲突检测')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出品牌')
    list_parser.add_argument('--client', default=None, help='客户名称（可选）')

    args = parser.parse_args()

    if args.command == 'create':
        create_brand(
            client_name=args.client,
            brand_name=args.name,
            brand_name_en=args.name_en,
            industry=args.industry,
            category=args.category,
            positioning=args.positioning,
            brand_tone=args.brand_tone,
            target_audience=args.target_audience,
            core_values=args.core_values,
            brand_story=args.brand_story,
            tags=args.tags,
            agent_id=args.agent
        )
    elif args.command == 'get':
        get_brand(args.client, args.name)
    elif args.command == 'update':
        result = update_brand(
            client_name=args.client,
            brand_name=args.name,
            field=args.field,
            value=args.value,
            agent_id=args.agent,
            require_confirmation=not args.no_conflict_check,
            user_confirmed=args.user_confirmed
        )
        # 输出 JSON 格式结果供其他脚本使用
        import json
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(result, ensure_ascii=False))
    elif args.command == 'list':
        list_brands(args.client)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
