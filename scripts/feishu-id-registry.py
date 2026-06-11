#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import time
from pathlib import Path
from typing import Any


ROOT = Path('/Users/a123/.openclaw')
AGENTS_DIR = ROOT / 'agents'
REGISTRY_PATH = ROOT / 'feishu' / 'conversation-ids.json'


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f'.{int(time.time() * 1000)}.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def cutoff_ms(since_days: int) -> int | None:
    if since_days <= 0:
        return None
    return int((time.time() - since_days * 86400) * 1000)


def path_recent(path: Path, cutoff: int | None) -> bool:
    if cutoff is None:
        return True
    try:
        return int(path.stat().st_mtime * 1000) >= cutoff
    except FileNotFoundError:
        return False


def iso_to_ms(value: Any) -> int | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return int(datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000)
    except ValueError:
        return None


def iter_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except (FileNotFoundError, UnicodeDecodeError):
        return records
    for line_no, line in enumerate(lines, 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            record['_line_no'] = line_no
            records.append(record)
    return records


def json_block(content: str) -> dict[str, Any]:
    match = re.search(r'Conversation info \(untrusted metadata\):\s*```json\s*(\{.*?\})\s*```', content, re.S)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def extract_context(record: dict[str, Any], session_path: Path) -> dict[str, Any] | None:
    if record.get('customType') != 'openclaw.runtime-context':
        return None
    content = str(record.get('content') or '')
    meta = json_block(content)
    chat_id = str(meta.get('chat_id') or '').strip()
    if chat_id.startswith('chat:'):
        chat_id = chat_id.split(':', 1)[1]
    if not chat_id:
        match = re.search(r'\b(?:group|DM)\s+(oc_[a-zA-Z0-9]+)', content)
        chat_id = match.group(1) if match else ''
    account_match = re.search(r'Feishu\[([^\]]+)\]', content)
    account_id = account_match.group(1) if account_match else ''
    sender_id = str(meta.get('sender_id') or '').strip()
    sender = str(meta.get('sender') or '').strip()
    is_group = bool(meta.get('is_group_chat')) or ' group ' in content
    if not account_id or (not chat_id and not sender_id):
        return None
    return {
        'accountId': account_id,
        'chatId': chat_id,
        'senderOpenId': sender_id,
        'senderName': sender,
        'messageId': str(meta.get('message_id') or '').strip(),
        'isGroup': is_group,
        'chatType': 'group' if is_group else 'p2p',
        'timestamp': record.get('timestamp') or '',
        'timestampMs': iso_to_ms(record.get('timestamp')),
        'sessionFile': str(session_path),
        'line': record.get('_line_no'),
    }


def merge_context(registry: dict[str, Any], ctx: dict[str, Any]) -> None:
    now = ctx.get('timestamp') or datetime.now().isoformat()
    registry.setdefault('version', 1)
    registry['updatedAt'] = datetime.now().isoformat()
    conversations = registry.setdefault('conversations', {})
    users = registry.setdefault('users', {})
    sessions = registry.setdefault('sessions', {})
    account_id = ctx['accountId']
    chat_id = ctx.get('chatId') or ''
    sender_id = ctx.get('senderOpenId') or ''
    is_group = bool(ctx.get('isGroup'))
    target = f'chat:{chat_id}' if is_group and chat_id else f'user:{sender_id}' if sender_id else f'chat:{chat_id}'
    message = {
        'at': now,
        'messageId': ctx.get('messageId') or '',
        'senderOpenId': sender_id,
        'sessionFile': ctx.get('sessionFile') or '',
        'line': ctx.get('line'),
    }
    if chat_id:
        key = f'{account_id}:{chat_id}'
        prev = conversations.get(key, {})
        recent = list(prev.get('recentMessages') or [])
        recent.append(message)
        conversations[key] = {
            **prev,
            'accountId': account_id,
            'chatId': chat_id,
            'target': f'chat:{chat_id}' if is_group else target,
            'chatType': ctx.get('chatType') or ('group' if is_group else 'p2p'),
            'isGroup': is_group,
            'lastSeenAt': now,
            'lastMessageId': ctx.get('messageId') or prev.get('lastMessageId') or '',
            'lastSenderOpenId': sender_id or prev.get('lastSenderOpenId') or '',
            'lastSenderName': ctx.get('senderName') or prev.get('lastSenderName') or '',
            'lastSessionFile': ctx.get('sessionFile') or prev.get('lastSessionFile') or '',
            'recentMessages': recent[-20:],
        }
    if sender_id:
        key = f'{account_id}:{sender_id}'
        prev = users.get(key, {})
        recent = list(prev.get('recentMessages') or [])
        recent.append(message)
        users[key] = {
            **prev,
            'accountId': account_id,
            'openId': sender_id,
            'target': f'user:{sender_id}',
            'name': ctx.get('senderName') or prev.get('name') or '',
            'lastSeenAt': now,
            'lastChatId': chat_id or prev.get('lastChatId') or '',
            'dmChatId': chat_id if not is_group and chat_id else prev.get('dmChatId') or '',
            'lastSessionFile': ctx.get('sessionFile') or prev.get('lastSessionFile') or '',
            'recentMessages': recent[-20:],
        }
    session_file = ctx.get('sessionFile')
    if session_file:
        sessions[session_file] = {
            'accountId': account_id,
            'chatId': chat_id,
            'senderOpenId': sender_id,
            'target': target,
            'isGroup': is_group,
            'chatType': ctx.get('chatType') or ('group' if is_group else 'p2p'),
            'lastSeenAt': now,
            'lastMessageId': ctx.get('messageId') or '',
        }


def scan(since_days: int) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH, {})
    cutoff = cutoff_ms(since_days)
    count = 0
    for session_path in sorted(AGENTS_DIR.glob('*/sessions/*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path_recent(session_path, cutoff):
            continue
        for record in iter_records(session_path):
            ctx = extract_context(record, session_path)
            if not ctx:
                continue
            if cutoff is not None and ctx.get('timestampMs') is not None and int(ctx['timestampMs']) < cutoff:
                continue
            merge_context(registry, ctx)
            count += 1
    write_json(REGISTRY_PATH, registry)
    return {
        'ok': True,
        'registry_path': str(REGISTRY_PATH),
        'contexts_seen': count,
        'conversations': len(registry.get('conversations') or {}),
        'users': len(registry.get('users') or {}),
        'sessions': len(registry.get('sessions') or {}),
    }


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH, {})
    account = args.account_id or ''
    if args.session_file:
        item = (registry.get('sessions') or {}).get(args.session_file)
        return {'ok': bool(item), 'kind': 'session', 'item': item or {}}
    if args.chat_id:
        chat_id = args.chat_id.split(':', 1)[1] if args.chat_id.startswith('chat:') else args.chat_id
        key = f'{account}:{chat_id}' if account else next((k for k in (registry.get('conversations') or {}) if k.endswith(f':{chat_id}')), '')
        item = (registry.get('conversations') or {}).get(key)
        return {'ok': bool(item), 'kind': 'conversation', 'item': item or {}}
    if args.open_id:
        user_id = args.open_id.split(':', 1)[1] if args.open_id.startswith('user:') else args.open_id
        key = f'{account}:{user_id}' if account else next((k for k in (registry.get('users') or {}) if k.endswith(f':{user_id}')), '')
        item = (registry.get('users') or {}).get(key)
        return {'ok': bool(item), 'kind': 'user', 'item': item or {}}
    return {'ok': False, 'error': 'provide --session-file, --chat-id, or --open-id'}


def main() -> int:
    parser = argparse.ArgumentParser(description='Maintain and query Feishu conversation ID registry.')
    sub = parser.add_subparsers(dest='cmd')
    scan_p = sub.add_parser('scan')
    scan_p.add_argument('--since-days', type=int, default=14)
    scan_p.add_argument('--json', action='store_true')
    resolve_p = sub.add_parser('resolve')
    resolve_p.add_argument('--session-file')
    resolve_p.add_argument('--chat-id')
    resolve_p.add_argument('--open-id')
    resolve_p.add_argument('--account-id')
    resolve_p.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.cmd == 'resolve':
        payload = resolve(args)
    else:
        payload = scan(getattr(args, 'since_days', 14))
    if getattr(args, 'json', False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"ok={payload.get('ok')} registry={payload.get('registry_path', REGISTRY_PATH)}")
        for key in ('contexts_seen', 'conversations', 'users', 'sessions'):
            if key in payload:
                print(f'{key}={payload[key]}')
        if payload.get('item'):
            print(json.dumps(payload['item'], ensure_ascii=False, indent=2))
    return 0 if payload.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
