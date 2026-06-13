#!/usr/bin/env python3
"""
飞书艾特助手 - 帮助 agent 在流式卡片中生成真实的艾特标签

用法：
  # 按名字查询用户并生成艾特标签
  python3 feishu-mention-helper.py --name "涂是淦"

  # 按 open_id 直接生成艾特标签
  python3 feishu-mention-helper.py --open-id "ou_3669c86e1e9957992630dd1fc0b85577"

  # 列出所有已知用户
  python3 feishu-mention-helper.py --list

  # JSON 输出（适合 agent 调用）
  python3 feishu-mention-helper.py --name "涂是淦" --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path('/Users/a123/.openclaw')
REGISTRY_PATH = ROOT / 'feishu' / 'conversation-ids.json'


def load_registry() -> dict[str, Any]:
    """加载飞书 ID 注册表"""
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def format_mention_tag(open_id: str) -> str:
    """生成飞书卡片格式的艾特标签"""
    return f'<at id={open_id}></at>'


def search_user_by_name(registry: dict[str, Any], name: str) -> list[dict[str, Any]]:
    """按名字搜索用户"""
    users = registry.get('users', {})
    results = []

    name_lower = name.lower().strip()
    for key, user_data in users.items():
        user_name = user_data.get('name', '').lower().strip()
        if name_lower in user_name or user_name in name_lower:
            results.append({
                'openId': user_data.get('openId', ''),
                'name': user_data.get('name', ''),
                'accountId': user_data.get('accountId', ''),
                'target': user_data.get('target', ''),
                'lastSeenAt': user_data.get('lastSeenAt', ''),
                'mentionTag': format_mention_tag(user_data.get('openId', ''))
            })

    return results


def get_user_by_open_id(registry: dict[str, Any], open_id: str) -> dict[str, Any] | None:
    """按 open_id 查询用户"""
    users = registry.get('users', {})

    # 移除可能的 user: 前缀
    clean_id = open_id.split(':', 1)[1] if open_id.startswith('user:') else open_id

    for key, user_data in users.items():
        if user_data.get('openId') == clean_id:
            return {
                'openId': user_data.get('openId', ''),
                'name': user_data.get('name', ''),
                'accountId': user_data.get('accountId', ''),
                'target': user_data.get('target', ''),
                'lastSeenAt': user_data.get('lastSeenAt', ''),
                'mentionTag': format_mention_tag(clean_id)
            }

    return None


def list_all_users(registry: dict[str, Any]) -> list[dict[str, Any]]:
    """列出所有用户"""
    users = registry.get('users', {})
    results = []

    for key, user_data in users.items():
        open_id = user_data.get('openId', '')
        results.append({
            'openId': open_id,
            'name': user_data.get('name', ''),
            'accountId': user_data.get('accountId', ''),
            'lastSeenAt': user_data.get('lastSeenAt', ''),
            'mentionTag': format_mention_tag(open_id)
        })

    # 按最近见到时间排序
    results.sort(key=lambda x: x.get('lastSeenAt', ''), reverse=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description='飞书艾特助手 - 生成真实的艾特标签',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--name', help='按名字搜索用户')
    parser.add_argument('--open-id', help='按 open_id 查询用户')
    parser.add_argument('--list', action='store_true', help='列出所有用户')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('--limit', type=int, default=20, help='列表模式下的最大结果数（默认 20）')

    args = parser.parse_args()

    # 加载注册表
    registry = load_registry()

    if not registry:
        result = {'ok': False, 'error': '注册表为空或无法加载'}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print('❌ 注册表为空或无法加载')
        return 1

    # 执行查询
    if args.list:
        users = list_all_users(registry)[:args.limit]
        result = {'ok': True, 'count': len(users), 'users': users}

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f'📋 找到 {len(users)} 个用户（最近活跃）：\n')
            for i, user in enumerate(users, 1):
                print(f"{i}. {user['name']}")
                print(f"   OpenID: {user['openId']}")
                print(f"   艾特标签: {user['mentionTag']}")
                print(f"   最近活跃: {user['lastSeenAt']}")
                print()
        return 0

    elif args.name:
        users = search_user_by_name(registry, args.name)

        if not users:
            result = {'ok': False, 'error': f'未找到名字包含 "{args.name}" 的用户'}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f'❌ 未找到名字包含 "{args.name}" 的用户')
            return 1

        result = {'ok': True, 'count': len(users), 'users': users}

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if len(users) == 1:
                user = users[0]
                print(f"✅ 找到用户：{user['name']}")
                print(f"OpenID: {user['openId']}")
                print(f"艾特标签: {user['mentionTag']}")
            else:
                print(f"✅ 找到 {len(users)} 个匹配用户：\n")
                for i, user in enumerate(users, 1):
                    print(f"{i}. {user['name']}")
                    print(f"   OpenID: {user['openId']}")
                    print(f"   艾特标签: {user['mentionTag']}")
                    print()
        return 0

    elif args.open_id:
        user = get_user_by_open_id(registry, args.open_id)

        if not user:
            result = {'ok': False, 'error': f'未找到 open_id 为 "{args.open_id}" 的用户'}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f'❌ 未找到 open_id 为 "{args.open_id}" 的用户')
            return 1

        result = {'ok': True, 'user': user}

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"✅ 找到用户：{user['name']}")
            print(f"OpenID: {user['openId']}")
            print(f"艾特标签: {user['mentionTag']}")
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
