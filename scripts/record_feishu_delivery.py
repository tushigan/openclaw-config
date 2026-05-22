#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path('/Users/a123/.openclaw')
GENERIC_DELIVERY_DIRS = [
    ROOT / 'workspace' / 'images',
    ROOT / 'workspace' / 'outputs',
    ROOT / 'workspace' / 'brand-poster-projects',
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def delivery_paths(manifest: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    deliverables = manifest.get('deliverables') or {}
    for key in ('original_image', 'send_path'):
        if manifest.get(key):
            paths.append(str(manifest[key]))
    image_list = deliverables.get('images')
    if isinstance(image_list, list):
        paths.extend(str(item) for item in image_list if item)
    for value in deliverables.values():
        if isinstance(value, dict) and value.get('path'):
            paths.append(str(value['path']))
    return [str(Path(path).resolve()) for path in dict.fromkeys(paths) if path]


def find_manifest_for_file(sent_file: Path) -> Path | None:
    sent = str(sent_file.resolve())
    candidates: list[Path] = []
    for base in GENERIC_DELIVERY_DIRS:
        if base.exists():
            candidates.extend(base.glob('**/*.delivery.json'))
            candidates.extend(base.glob('**/delivery_manifest.json'))
    candidates = sorted(set(candidates), key=lambda path: path.stat().st_mtime, reverse=True)
    for candidate in candidates:
        try:
            manifest = load_json(candidate)
        except (OSError, json.JSONDecodeError):
            continue
        if sent in delivery_paths(manifest):
            return candidate
    return None


def record_manifest(manifest_path: Path, sent_file: Path, message_id: str, chat_id: str, account: str) -> None:
    manifest = load_json(manifest_path)
    sent_path = str(sent_file.resolve())
    evidence = manifest.setdefault('delivery_evidence', {})
    sent_paths = list(evidence.get('sent_paths') or [])
    if sent_path not in sent_paths:
        sent_paths.append(sent_path)

    manifest.update({
        'delivery_attempted': True,
        'delivery_attempted_at': now_iso(),
        'delivery_status': 'delivered',
        'delivery_method': 'message(media)',
        'fallback_required': False,
        'fallback_reason': '',
        'user_report': '',
        'error': '',
        'message_id': message_id,
        'chat_id': chat_id,
        'account_id': account,
        'delivered_at': now_iso(),
    })
    evidence.update({
        'ok': True,
        'reason': '',
        'message_id': message_id,
        'chat_id': chat_id,
        'account_id': account,
        'sent_paths': sent_paths,
        'method': 'message(media)',
    })
    write_json(manifest_path, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description='Record successful Feishu delivery for OpenClaw artifacts.')
    parser.add_argument('--manifest', help='Delivery manifest path to update')
    parser.add_argument('--file', '--sent-path', dest='sent_file', help='File path sent to Feishu')
    parser.add_argument('--message-id', required=True, help='Feishu message id returned by send')
    parser.add_argument('--chat-id', required=True, help='Feishu chat id returned by send')
    parser.add_argument('--account', default='', help='Feishu account id used for send')
    args = parser.parse_args()

    manifest_path = Path(args.manifest) if args.manifest else None
    sent_file = Path(args.sent_file) if args.sent_file else None
    if sent_file is None:
        if manifest_path is None:
            raise ValueError('either --file/--sent-path or --manifest is required')
        manifest = load_json(manifest_path)
        sent_file = next((Path(path) for path in delivery_paths(manifest) if Path(path).exists()), None)
        if sent_file is None:
            raise FileNotFoundError(f'no existing deliverable found in manifest: {manifest_path}')
    if not sent_file.exists():
        raise FileNotFoundError(f'sent file does not exist: {sent_file}')
    manifest_path = manifest_path if manifest_path is not None else find_manifest_for_file(sent_file)
    if manifest_path is None:
        raise FileNotFoundError(f'no delivery manifest found for: {sent_file}')
    record_manifest(
        manifest_path=manifest_path,
        sent_file=sent_file,
        message_id=args.message_id,
        chat_id=args.chat_id,
        account=args.account,
    )
    print(str(manifest_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
