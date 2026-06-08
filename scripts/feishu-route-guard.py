#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROUTE_SIDECAR_SUFFIX = '.route.json'


def normalize_feishu_target(value: Any) -> str:
    raw = str(value or '').strip()
    if not raw:
        return ''
    if raw.startswith(('chat:', 'user:')):
        return raw
    if raw.startswith('oc_'):
        return 'chat:' + raw
    if raw.startswith('ou_'):
        return 'user:' + raw
    return raw


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def route_sidecar_path(media_path: Path) -> Path:
    return media_path.with_name(f'{media_path.name}{ROUTE_SIDECAR_SUFFIX}')


def write_route_sidecar(
    media_path: Path,
    *,
    target: str,
    account_id: str = '',
    source: str = '',
    source_manifest: str = '',
) -> Path:
    sidecar = route_sidecar_path(media_path)
    write_json(
        sidecar,
        {
            'schema': 'openclaw.feishu.media-route.v1',
            'media': str(media_path),
            'delivery_target': {
                'target': normalize_feishu_target(target),
                'account_id': str(account_id or '').strip(),
                'target_source': str(source or '').strip() or 'route_sidecar',
            },
            'source_manifest': str(source_manifest or '').strip(),
        },
    )
    return sidecar


def _target_from_payload(payload: dict[str, Any]) -> str:
    delivery_target = payload.get('delivery_target') or {}
    if not isinstance(delivery_target, dict):
        delivery_target = {}
    return normalize_feishu_target(
        delivery_target.get('target')
        or delivery_target.get('chat_id')
        or delivery_target.get('user_id')
        or payload.get('target')
        or payload.get('chat_id')
        or payload.get('user_id')
    )


def _record_paths_for_media(media_path: Path) -> list[Path]:
    paths = [
        route_sidecar_path(media_path),
        media_path.parent / 'task_manifest.json',
        media_path.with_name(f'{media_path.stem}.delivery.json'),
        media_path.with_name(f'{media_path.stem}.result.json'),
    ]
    for parent in media_path.parents:
        manifest = parent / 'delivery_manifest.json'
        if manifest not in paths:
            paths.append(manifest)
        if parent.name in ('workspace', '.openclaw'):
            break
    unique: dict[str, Path] = {}
    for path in paths:
        unique[str(path)] = path
    return list(unique.values())


def route_records_for_media(media_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in _record_paths_for_media(media_path):
        payload = load_json(path)
        if not payload:
            continue
        records.append(
            {
                'path': str(path),
                'target': _target_from_payload(payload),
                'schema': str(payload.get('schema') or ''),
            }
        )
    return records


def check_media_route(media_path: Path, requested_target: str, *, strict: bool = False) -> dict[str, Any]:
    normalized_target = normalize_feishu_target(requested_target)
    if not normalized_target:
        return {
            'ok': False,
            'status': 'missing_requested_target',
            'media': str(media_path),
            'requested_target': '',
            'recorded_targets': [],
            'route_records': [],
        }

    records = route_records_for_media(media_path)
    if not records:
        return {
            'ok': not strict,
            'status': 'no_route_record' if not strict else 'missing_route_record',
            'media': str(media_path),
            'requested_target': normalized_target,
            'recorded_targets': [],
            'route_records': [],
        }

    targets = sorted({record['target'] for record in records if record.get('target')})
    if not targets:
        return {
            'ok': False,
            'status': 'route_record_without_target',
            'media': str(media_path),
            'requested_target': normalized_target,
            'recorded_targets': [],
            'route_records': records,
        }

    if len(targets) > 1:
        return {
            'ok': False,
            'status': 'route_record_target_conflict',
            'media': str(media_path),
            'requested_target': normalized_target,
            'recorded_targets': targets,
            'route_records': records,
        }

    if normalized_target not in targets:
        return {
            'ok': False,
            'status': 'target_conflict',
            'media': str(media_path),
            'requested_target': normalized_target,
            'recorded_targets': targets,
            'route_records': records,
        }

    return {
        'ok': True,
        'status': 'matched',
        'media': str(media_path),
        'requested_target': normalized_target,
        'recorded_targets': targets,
        'route_records': records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate Feishu media route before sending.')
    sub = parser.add_subparsers(dest='command', required=True)

    check = sub.add_parser('check')
    check.add_argument('--media', required=True)
    check.add_argument('--target', required=True)
    check.add_argument('--strict', action='store_true')
    check.add_argument('--json', action='store_true')

    stamp = sub.add_parser('stamp')
    stamp.add_argument('--media', required=True)
    stamp.add_argument('--target', required=True)
    stamp.add_argument('--account-id', default='')
    stamp.add_argument('--source', default='')
    stamp.add_argument('--source-manifest', default='')
    stamp.add_argument('--json', action='store_true')

    args = parser.parse_args(argv)

    if args.command == 'check':
        result = check_media_route(Path(args.media), args.target, strict=args.strict)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif not result['ok']:
            print(f'Feishu route blocked: {result["status"]}', file=sys.stderr)
        return 0 if result['ok'] else 2

    sidecar = write_route_sidecar(
        Path(args.media),
        target=args.target,
        account_id=args.account_id,
        source=args.source,
        source_manifest=args.source_manifest,
    )
    result = {'ok': True, 'status': 'stamped', 'sidecar': str(sidecar)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(str(sidecar))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
