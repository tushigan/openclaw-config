#!/usr/bin/env python3
"""
OpenClaw 顶层记忆系统 - 客户管理
提供客户档案的 CRUD 操作
"""

import os
import sys
import argparse
from typing import Optional

# 添加 lib 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib import (
    ClientProfile, ContactInfo, ContractInfo,
    get_timestamp, generate_id, ensure_dir, read_json, write_json,
    get_project_root, get_client_dir, normalize_name, validate_required_fields
)


def create_client(
    name: str,
    name_en: str = "",
    industry: str = "",
    company_type: str = "",
    business_notes: str = "",
    tags: list = None
) -> dict:
    """创建客户档案"""

    # 规范化客户名称
    client_name = normalize_name(name)

    # 检查是否已存在
    client_dir = get_client_dir(client_name)
    profile_path = os.path.join(client_dir, "_client-profile.json")

    if os.path.exists(profile_path):
        print(f"⚠️ 客户档案已存在: {client_name}")
        existing = read_json(profile_path)
        return existing

    # 生成客户 ID
    client_id = generate_id("CLI", name)

    # 创建客户档案
    profile = ClientProfile(
        client_id=client_id,
        name=name,
        name_en=name_en,
        industry=industry,
        company_type=company_type,
        business_notes=business_notes,
        tags=tags or [],
        created_at=get_timestamp(),
        updated_at=get_timestamp(),
        _last_modified_by="system"
    )

    # 创建目录结构
    ensure_dir(client_dir)

    # 保存客户档案
    data = profile.to_dict()
    if write_json(profile_path, data):
        print(f"✅ 客户档案创建成功: {client_name}")
        print(f"   ID: {client_id}")
        print(f"   路径: {profile_path}")

        # 更新全局注册表
        update_registry(client_id, client_name, "client")

        return data
    else:
        print(f"❌ 客户档案创建失败")
        return None


def get_client(name: str) -> Optional[dict]:
    """获取客户档案"""
    client_name = normalize_name(name)
    profile_path = os.path.join(get_client_dir(client_name), "_client-profile.json")

    data = read_json(profile_path)
    if data:
        print(f"✅ 客户档案: {client_name}")
        print(f"   ID: {data.get('client_id')}")
        print(f"   行业: {data.get('industry', '未设置')}")
        print(f"   类型: {data.get('company_type', '未设置')}")
        print(f"   联系人数量: {len(data.get('contacts', []))}")
        print(f"   合同数量: {len(data.get('contracts', []))}")
    else:
        print(f"❌ 客户档案不存在: {client_name}")

    return data


def update_client(
    name: str,
    field: str,
    value: str,
    agent_id: str = "system"
) -> bool:
    """更新客户档案字段"""
    client_name = normalize_name(name)
    profile_path = os.path.join(get_client_dir(client_name), "_client-profile.json")

    data = read_json(profile_path)
    if not data:
        print(f"❌ 客户档案不存在: {client_name}")
        return False

    # 更新字段
    old_value = data.get(field)
    data[field] = value
    data['updated_at'] = get_timestamp()
    data['_last_modified_by'] = agent_id

    if write_json(profile_path, data):
        print(f"✅ 客户档案更新成功")
        print(f"   字段: {field}")
        print(f"   原值: {old_value}")
        print(f"   新值: {value}")
        return True
    else:
        print(f"❌ 客户档案更新失败")
        return False


def add_contact(
    client_name: str,
    name: str,
    role: str = "",
    phone: str = "",
    email: str = "",
    wechat: str = "",
    feishu_user_id: str = "",
    notes: str = ""
) -> bool:
    """添加联系人"""
    client_name = normalize_name(client_name)
    profile_path = os.path.join(get_client_dir(client_name), "_client-profile.json")

    data = read_json(profile_path)
    if not data:
        print(f"❌ 客户档案不存在: {client_name}")
        return False

    # 创建联系人
    contact = ContactInfo(
        name=name,
        role=role,
        phone=phone,
        email=email,
        wechat=wechat,
        feishu_user_id=feishu_user_id,
        notes=notes
    )

    # 添加到联系人列表
    if 'contacts' not in data:
        data['contacts'] = []

    data['contacts'].append(contact.__dict__)
    data['updated_at'] = get_timestamp()

    if write_json(profile_path, data):
        print(f"✅ 联系人添加成功: {name} ({role})")
        return True
    else:
        print(f"❌ 联系人添加失败")
        return False


def add_contract(
    client_name: str,
    contract_id: str,
    contract_name: str,
    signed_date: str,
    amount: float = 0.0,
    currency: str = "CNY",
    status: str = "active",
    file_path: str = "",
    notes: str = ""
) -> bool:
    """添加合同记录"""
    client_name = normalize_name(client_name)
    profile_path = os.path.join(get_client_dir(client_name), "_client-profile.json")

    data = read_json(profile_path)
    if not data:
        print(f"❌ 客户档案不存在: {client_name}")
        return False

    # 创建合同
    contract = ContractInfo(
        contract_id=contract_id,
        contract_name=contract_name,
        signed_date=signed_date,
        amount=amount,
        currency=currency,
        status=status,
        file_path=file_path,
        notes=notes
    )

    # 添加到合同列表
    if 'contracts' not in data:
        data['contracts'] = []

    data['contracts'].append(contract.__dict__)
    data['updated_at'] = get_timestamp()

    if write_json(profile_path, data):
        print(f"✅ 合同添加成功: {contract_name}")
        print(f"   合同号: {contract_id}")
        print(f"   金额: {amount} {currency}")
        return True
    else:
        print(f"❌ 合同添加失败")
        return False


def list_clients() -> list:
    """列出所有客户"""
    root = get_project_root()
    if not os.path.exists(root):
        print("📂 项目根目录不存在，尚未创建任何客户")
        return []

    clients = []
    for item in os.listdir(root):
        client_dir = os.path.join(root, item)
        if os.path.isdir(client_dir) and not item.startswith('.'):
            profile_path = os.path.join(client_dir, "_client-profile.json")
            if os.path.exists(profile_path):
                data = read_json(profile_path)
                if data:
                    clients.append({
                        'name': data.get('name'),
                        'client_id': data.get('client_id'),
                        'industry': data.get('industry', ''),
                        'company_type': data.get('company_type', ''),
                        'brand_count': len([d for d in os.listdir(client_dir)
                                          if os.path.isdir(os.path.join(client_dir, d))
                                          and not d.startswith('_')])
                    })

    if clients:
        print(f"📋 客户列表（共 {len(clients)} 个）：")
        for c in clients:
            print(f"   • {c['name']} ({c['company_type']}) - {c['brand_count']} 个品牌")
    else:
        print("📂 暂无客户档案")

    return clients


def update_registry(entity_id: str, entity_name: str, entity_type: str):
    """更新全局注册表"""
    registry_path = os.path.join(get_project_root(), "_registry.json")

    registry = read_json(registry_path) or {
        "version": "2.0",
        "last_updated": get_timestamp(),
        "clients": [],
        "brands": [],
        "projects": [],
        "tasks": []
    }

    # 添加到对应列表
    key = f"{entity_type}s"
    if key in registry:
        # 检查是否已存在
        existing = next((item for item in registry[key] if item.get('id') == entity_id), None)
        if not existing:
            registry[key].append({
                "id": entity_id,
                "name": entity_name,
                "created_at": get_timestamp()
            })
            registry["last_updated"] = get_timestamp()
            write_json(registry_path, registry)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 客户管理")
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # create 命令
    create_parser = subparsers.add_parser('create', help='创建客户档案')
    create_parser.add_argument('--name', required=True, help='客户名称')
    create_parser.add_argument('--name-en', default="", help='英文名称')
    create_parser.add_argument('--industry', default="", help='行业')
    create_parser.add_argument('--company-type', default="", help='公司类型')
    create_parser.add_argument('--notes', default="", help='商务备注')
    create_parser.add_argument('--tags', nargs='*', default=[], help='标签')

    # get 命令
    get_parser = subparsers.add_parser('get', help='获取客户档案')
    get_parser.add_argument('--name', required=True, help='客户名称')

    # update 命令
    update_parser = subparsers.add_parser('update', help='更新客户档案')
    update_parser.add_argument('--name', required=True, help='客户名称')
    update_parser.add_argument('--field', required=True, help='字段名')
    update_parser.add_argument('--value', required=True, help='新值')
    update_parser.add_argument('--agent', default='system', help='操作者 agent ID')

    # add-contact 命令
    contact_parser = subparsers.add_parser('add-contact', help='添加联系人')
    contact_parser.add_argument('--client', required=True, help='客户名称')
    contact_parser.add_argument('--name', required=True, help='联系人姓名')
    contact_parser.add_argument('--role', default="", help='职位')
    contact_parser.add_argument('--phone', default="", help='电话')
    contact_parser.add_argument('--email', default="", help='邮箱')
    contact_parser.add_argument('--wechat', default="", help='微信')
    contact_parser.add_argument('--feishu-user-id', default="", help='飞书用户ID')
    contact_parser.add_argument('--notes', default="", help='备注')

    # add-contract 命令
    contract_parser = subparsers.add_parser('add-contract', help='添加合同')
    contract_parser.add_argument('--client', required=True, help='客户名称')
    contract_parser.add_argument('--contract-id', required=True, help='合同号')
    contract_parser.add_argument('--contract-name', required=True, help='合同名称')
    contract_parser.add_argument('--signed-date', required=True, help='签订日期 (YYYY-MM-DD)')
    contract_parser.add_argument('--amount', type=float, default=0.0, help='金额')
    contract_parser.add_argument('--currency', default="CNY", help='币种')
    contract_parser.add_argument('--status', default="active", help='状态')
    contract_parser.add_argument('--file-path', default="", help='合同文件路径')
    contract_parser.add_argument('--notes', default="", help='备注')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有客户')

    args = parser.parse_args()

    if args.command == 'create':
        create_client(
            name=args.name,
            name_en=args.name_en,
            industry=args.industry,
            company_type=args.company_type,
            business_notes=args.notes,
            tags=args.tags
        )
    elif args.command == 'get':
        get_client(args.name)
    elif args.command == 'update':
        update_client(args.name, args.field, args.value, args.agent)
    elif args.command == 'add-contact':
        add_contact(
            client_name=args.client,
            name=args.name,
            role=args.role,
            phone=args.phone,
            email=args.email,
            wechat=args.wechat,
            feishu_user_id=args.feishu_user_id,
            notes=args.notes
        )
    elif args.command == 'add-contract':
        add_contract(
            client_name=args.client,
            contract_id=args.contract_id,
            contract_name=args.contract_name,
            signed_date=args.signed_date,
            amount=args.amount,
            currency=args.currency,
            status=args.status,
            file_path=args.file_path,
            notes=args.notes
        )
    elif args.command == 'list':
        list_clients()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
