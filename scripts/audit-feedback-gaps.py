#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import re
import time
from pathlib import Path
from typing import Any


ROOT = Path('/Users/a123/.openclaw')
RUNS_PATH = ROOT / 'subagents' / 'runs.json'
AGENTS_DIR = ROOT / 'agents'
PROJECTS_DIR = ROOT / 'workspace' / 'brand-poster-projects'
DELIVER_DIR = ROOT / 'workspace' / 'feishu-deliver'
FEISHU_ID_REGISTRY = ROOT / 'feishu' / 'conversation-ids.json'
GENERIC_DELIVERY_DIRS = [
    ROOT / 'workspace' / 'images',
    ROOT / 'workspace' / 'outputs',
]

SUCCESS_DELIVERY_STATUSES = {
    'sent',
    'sent_to_feishu',
    'delivered',
    'done',
    'success',
}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        return {'_error': f'json_decode_error: {exc}'}


def short(text: Any, limit: int = 180) -> str:
    value = str(text or '').replace('\n', ' ').strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + '...'


def cutoff_ms(since_minutes: int) -> int | None:
    if since_minutes <= 0:
        return None
    return int((time.time() - since_minutes * 60) * 1000)


def is_recent_ms(value: Any, cutoff: int | None) -> bool:
    if cutoff is None:
        return True
    if not isinstance(value, (int, float)):
        return False
    return int(value) >= cutoff


def is_recent_path(path: Path, cutoff: int | None) -> bool:
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


def pid_alive(pid: Any) -> bool:
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    try:
        os.kill(value, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def has_tool_call(message: dict[str, Any]) -> bool:
    content = message.get('content') or []
    if not isinstance(content, list):
        return False
    return any(isinstance(item, dict) and item.get('type') == 'toolCall' for item in content)


def message_text(message: dict[str, Any]) -> str:
    parts: list[str] = []
    content = message.get('content') or []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                parts.append(str(item.get('text') or ''))
    return '\n'.join(parts).strip()


def looks_like_commitment_without_start(text: str) -> bool:
    normalized = text.replace(' ', '').replace('\n', '')
    if not normalized:
        return False
    direct_phrases = [
        '我先生成',
        '我会生成',
        '我来生成',
        '我去生成',
        '我先出图',
        '我会出图',
        '我先跑',
        '我会跑',
        '我已经补启动',
        '现在开始跑',
        '开始生成',
        '开始跑高清图',
        '出来后我直接发',
        '下一步直接发',
        '我下一步直接发',
        '我现在检查',
    ]
    return any(phrase in normalized for phrase in direct_phrases)


def later_successful_visible_message(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    for record in records:
        message = record.get('message') or {}
        if message.get('toolName') != 'message':
            continue
        details = message.get('details') or {}
        if details.get('ok') is True:
            return {
                'line': record.get('_line_no'),
                'message_id': details.get('messageId') or details.get('message_id') or '',
                'chat_id': details.get('chatId') or details.get('chat_id') or '',
            }
    return None


def iter_session_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except (FileNotFoundError, UnicodeDecodeError):
        return records
    for line_no, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            record['_line_no'] = line_no
            records.append(record)
    return records


def registry_session_context(session_path: Path) -> dict[str, str]:
    registry = load_json(FEISHU_ID_REGISTRY, {})
    sessions = registry.get('sessions') if isinstance(registry, dict) else {}
    if not isinstance(sessions, dict):
        return {}
    item = sessions.get(str(session_path))
    if not isinstance(item, dict):
        return {}
    chat_id = str(item.get('chatId') or '').strip()
    target = str(item.get('target') or '').strip()
    account_id = str(item.get('accountId') or '').strip()
    if chat_id and not chat_id.startswith('chat:'):
        chat_id = 'chat:' + chat_id
    if not chat_id and target.startswith('chat:'):
        chat_id = target
    return {
        **({'chat_id': chat_id} if chat_id else {}),
        **({'account_id': account_id} if account_id else {}),
        'source': 'feishu_id_registry',
    } if chat_id or account_id else {}


def session_chat_context(records: list[dict[str, Any]], session_path: Path | None = None) -> dict[str, str]:
    candidate: dict[str, str] = {}
    for record in records:
        if record.get('customType') != 'openclaw.runtime-context':
            continue
        content = str(record.get('content') or '')
        chat_match = re.search(r'"chat_id"\s*:\s*"(chat:[^"]+|oc_[^"]+)"', content)
        account_match = re.search(r'Feishu\[([^\]]+)\]', content)
        if chat_match:
            chat_id = chat_match.group(1)
            if chat_id.startswith('oc_'):
                chat_id = 'chat:' + chat_id
            candidate = {
                'chat_id': chat_id,
                'account_id': account_match.group(1) if account_match else '',
            }
            if candidate.get('account_id'):
                return candidate
    if candidate:
        return candidate
    if session_path is not None:
        return registry_session_context(session_path)
    return {}


MEDIA_PATH_RE = re.compile(r'(/Users/a123/[^\s"\'<>]+?\.(?:png|jpg|jpeg|webp|gif|mp4|mov|pdf|zip))')
SCRIPT_PATH_RE = re.compile(r'(/Users/a123/[^\s"\'<>]+?\.sh)')


def extract_delivery_paths_from_text(text: str) -> list[str]:
    paths: list[str] = []
    text = str(text or '')
    paths.extend(MEDIA_PATH_RE.findall(text))
    for script_path in SCRIPT_PATH_RE.findall(text):
        script = Path(script_path)
        try:
            paths.extend(MEDIA_PATH_RE.findall(script.read_text(encoding='utf-8')))
        except (FileNotFoundError, UnicodeDecodeError, OSError):
            continue
    return [path for path in dict.fromkeys(paths) if path]


def extract_delivery_paths_from_command(command: str) -> list[str]:
    return extract_delivery_paths_from_text(command)


def infer_chat_for_paths(paths: list[str], cutoff: int | None = None) -> dict[str, str]:
    needles = {path for path in paths if path}
    needles.update(Path(path).name for path in paths if path)
    needles = {needle for needle in needles if needle}
    if not needles or not AGENTS_DIR.exists():
        return {}
    for session_path in sorted(AGENTS_DIR.glob('*/sessions/*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True):
        if cutoff is not None and not is_recent_path(session_path, cutoff):
            continue
        records = iter_session_records(session_path)
        context = session_chat_context(records, session_path)
        if not context:
            continue
        for record in records:
            serialized = json.dumps(record, ensure_ascii=False)
            if any(needle in serialized for needle in needles):
                return {
                    **context,
                    'source_session_file': str(session_path),
                }
    return {}


def audit_stalled_commitments(
    cutoff: int | None,
    grace_minutes: int,
    include_resolved_chases: bool = False,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not AGENTS_DIR.exists():
        return findings

    grace_ms = max(grace_minutes, 0) * 60 * 1000
    now_ms = int(time.time() * 1000)
    for session_path in sorted(AGENTS_DIR.glob('*/sessions/*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True):
        if not is_recent_path(session_path, cutoff):
            continue
        records = iter_session_records(session_path)
        chat_context = session_chat_context(records, session_path)
        for index, record in enumerate(records):
            message = record.get('message') or {}
            if message.get('role') != 'assistant' or has_tool_call(message):
                continue
            text = message_text(message)
            if not looks_like_commitment_without_start(text):
                continue
            ts_ms = iso_to_ms(record.get('timestamp'))
            if cutoff is not None and not is_recent_ms(ts_ms, cutoff):
                continue
            if ts_ms is not None and now_ms - ts_ms < grace_ms:
                continue

            previous_user_index = next(
                (
                    prior_index
                    for prior_index in range(index - 1, -1, -1)
                    if (records[prior_index].get('message') or {}).get('role') == 'user'
                ),
                -1,
            )
            previous_tool_started = any(
                has_tool_call(records[prior_index].get('message') or {})
                for prior_index in range(previous_user_index + 1, index)
            )
            if previous_tool_started:
                continue

            later_records = records[index + 1 :]
            next_tool_record = next(
                (item for item in later_records if has_tool_call((item.get('message') or {}))),
                None,
            )
            next_user_record = next(
                (
                    item for item in later_records
                    if (item.get('message') or {}).get('role') == 'user'
                ),
                None,
            )
            required_user_chase = (
                next_user_record is not None
                and (
                    next_tool_record is None
                    or int(next_user_record.get('_line_no') or 0) < int(next_tool_record.get('_line_no') or 0)
                )
            )
            if next_tool_record is not None and not required_user_chase:
                continue
            resolved_delivery = later_successful_visible_message(later_records)
            if required_user_chase and resolved_delivery and not include_resolved_chases:
                continue
            later_serialized = '\n'.join(json.dumps(item, ensure_ascii=False) for item in later_records)
            delivery_paths = extract_delivery_paths_from_text(later_serialized)
            if any(find_message_delivery_evidence(path, ts_ms) for path in delivery_paths):
                continue

            finding = {
                'kind': 'stalled_commitment',
                'session_file': str(session_path),
                'line': record.get('_line_no'),
                'timestamp': record.get('timestamp') or '',
                'text': short(text, 260),
                'required_user_chase': required_user_chase,
                **chat_context,
            }
            if resolved_delivery:
                finding['resolved_by_later_message'] = resolved_delivery
            if next_user_record is not None:
                finding.update({
                    'next_user_line': next_user_record.get('_line_no'),
                    'next_user_text': short(message_text(next_user_record.get('message') or {}), 260),
                })
            if next_tool_record is not None:
                finding['next_tool_line'] = next_tool_record.get('_line_no')
            findings.append(finding)
    return findings


def audit_background_execs(cutoff: int | None, grace_minutes: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not AGENTS_DIR.exists():
        return findings

    grace_ms = max(grace_minutes, 0) * 60 * 1000
    now_ms = int(time.time() * 1000)
    session_paths = sorted(AGENTS_DIR.glob('*/sessions/*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
    for session_path in session_paths:
        if not is_recent_path(session_path, cutoff):
            continue
        records = iter_session_records(session_path)
        calls: dict[str, dict[str, Any]] = {}
        for index, record in enumerate(records):
            message = record.get('message') or {}
            content = message.get('content') or []
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict) or item.get('type') != 'toolCall':
                        continue
                    call_id = item.get('id')
                    if call_id:
                        calls[str(call_id)] = {
                            'name': item.get('name') or '',
                            'arguments': item.get('arguments') or {},
                            'timestamp': record.get('timestamp') or '',
                            'line_no': record.get('_line_no'),
                        }

            if message.get('toolName') != 'exec':
                continue
            details = message.get('details') or {}
            if details.get('status') != 'running':
                continue
            started_at = details.get('startedAt')
            if cutoff is not None and not is_recent_ms(started_at, cutoff):
                continue
            if isinstance(started_at, (int, float)) and now_ms - int(started_at) < grace_ms:
                continue

            call = calls.get(str(message.get('toolCallId'))) or {}
            args = call.get('arguments') or {}
            session_id = str(details.get('sessionId') or '').strip()
            later_text = '\n'.join(json.dumps(item, ensure_ascii=False) for item in records[index + 1 :])
            followed_up = bool(session_id and session_id in later_text)
            if followed_up:
                continue

            pid = details.get('pid')
            started_at_ms = int(started_at) if isinstance(started_at, (int, float)) else None
            delivery_paths = extract_delivery_paths_from_command(str(args.get('command') or ''))
            if any(find_message_delivery_evidence(path, started_at_ms) for path in delivery_paths):
                continue

            findings.append({
                'kind': 'background_exec',
                'session_file': str(session_path),
                'line': record.get('_line_no'),
                'exec_session_id': session_id,
                'pid': pid,
                'pid_running': pid_alive(pid),
                'started_at': started_at,
                'workdir': details.get('cwd') or args.get('workdir') or '',
                'command': short(args.get('command'), 260),
                    **session_chat_context(records, session_path),
            })
    return findings


def same_path(left: str, right: str) -> bool:
    if not left or not right:
        return False
    try:
        return str(Path(left).resolve()) == str(Path(right).resolve())
    except OSError:
        return left == right


def find_message_delivery_evidence(media_path: str, after_ms: int | None) -> dict[str, Any] | None:
    if not media_path or not AGENTS_DIR.exists():
        return None
    session_paths = sorted(AGENTS_DIR.glob('*/sessions/*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
    for session_path in session_paths:
        try:
            if after_ms is not None and int(session_path.stat().st_mtime * 1000) < after_ms:
                continue
        except FileNotFoundError:
            continue
        calls: dict[str, dict[str, Any]] = {}
        for record in iter_session_records(session_path):
            message = record.get('message') or {}
            content = message.get('content') or []
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict) or item.get('type') != 'toolCall' or item.get('name') != 'message':
                        continue
                    args = item.get('arguments') or {}
                    sent_path = args.get('media') or args.get('path') or args.get('filePath')
                    if sent_path and same_path(str(sent_path), media_path):
                        calls[str(item.get('id'))] = {
                            'session_file': str(session_path),
                            'line': record.get('_line_no'),
                            'media': str(sent_path),
                        }
            if message.get('toolName') != 'message':
                continue
            call_id = str(message.get('toolCallId') or '')
            if call_id not in calls:
                continue
            details = message.get('details') or {}
            if details.get('ok') is True:
                return {
                    'ok': True,
                    'message_id': details.get('messageId') or details.get('message_id') or '',
                    'chat_id': details.get('chatId') or details.get('chat_id') or '',
                    **calls[call_id],
                }
    return None


def audit_subagents(cutoff: int | None) -> list[dict[str, Any]]:
    data = load_json(RUNS_PATH, {})
    runs = data.get('runs') if isinstance(data, dict) else {}
    if not isinstance(runs, dict):
        return []

    findings: list[dict[str, Any]] = []
    for run_id, run in runs.items():
        if not isinstance(run, dict):
            continue
        status = (run.get('outcome') or {}).get('status')
        pending = run.get('pendingFinalDelivery') is True
        announce_error = run.get('lastAnnounceDeliveryError') or run.get('pendingFinalDeliveryLastError')
        subagent_error = status == 'error' or run.get('endedReason') == 'subagent-error'
        if not (pending or announce_error or subagent_error):
            continue
        recency_markers = [
            run.get('endedAt'),
            run.get('pendingFinalDeliveryCreatedAt'),
            run.get('pendingFinalDeliveryLastAttemptAt'),
            run.get('lastAnnounceRetryAt'),
            run.get('createdAt'),
        ]
        if cutoff is not None and not any(is_recent_ms(value, cutoff) for value in recency_markers):
            continue
        findings.append({
            'kind': 'subagent',
            'run_id': run_id,
            'label': run.get('label') or '',
            'status': status or '',
            'ended_reason': run.get('endedReason') or '',
            'pending_final_delivery': pending,
            'requester': run.get('requesterSessionKey') or '',
            'child': run.get('childSessionKey') or '',
            'error': short(announce_error or (run.get('outcome') or {}).get('error')),
            'result': short(run.get('frozenResultText')),
        })
    return findings


def delivery_send_paths(manifest: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    contract = manifest.get('agent_delivery_contract') or {}
    send_plan = contract.get('send_plan') or {}
    if send_plan.get('path'):
        paths.append(str(send_plan.get('path')))

    deliverables = manifest.get('deliverables') or {}
    if manifest.get('delivery_mode') == 'preview_and_zip':
        paths.append(str(((deliverables.get('preview_image') or {}).get('path') or '')).strip())
    paths.append(str(((deliverables.get('original_copy') or {}).get('path') or '')).strip())
    paths.append(str(manifest.get('original_image') or '').strip())
    image_list = deliverables.get('images')
    if isinstance(image_list, list):
        paths.extend(str(item).strip() for item in image_list)
    return [path for path in dict.fromkeys(paths) if path]


def iter_delivery_manifest_paths() -> list[Path]:
    paths: list[Path] = []
    if PROJECTS_DIR.exists():
        paths.extend(PROJECTS_DIR.glob('**/delivery_manifest.json'))
    for base in GENERIC_DELIVERY_DIRS:
        if base.exists():
            paths.extend(base.glob('**/*.delivery.json'))
    unique = {str(path): path for path in paths}
    return sorted(unique.values(), key=lambda p: p.stat().st_mtime, reverse=True)


def audit_delivery_manifests(limit: int, cutoff: int | None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for manifest_path in iter_delivery_manifest_paths():
        if not is_recent_path(manifest_path, cutoff):
            continue
        manifest = load_json(manifest_path, {})
        if not isinstance(manifest, dict) or manifest.get('_error'):
            findings.append({
                'kind': 'delivery_manifest',
                'path': str(manifest_path),
                'project_id': manifest_path.parent.name,
                'delivery_status': 'invalid_json',
                'error': manifest.get('_error') if isinstance(manifest, dict) else '',
            })
            continue

        status = str(manifest.get('delivery_status') or '').strip().lower()
        evidence = manifest.get('delivery_evidence') or {}
        message_id = str(
            evidence.get('message_id')
            or evidence.get('messageId')
            or manifest.get('message_id')
            or manifest.get('messageId')
            or ''
        ).strip()
        attempted = manifest.get('delivery_attempted') is True
        if status in SUCCESS_DELIVERY_STATUSES and (message_id or evidence.get('ok') is True):
            continue

        send_paths = delivery_send_paths(manifest)
        manifest_mtime_ms = int(manifest_path.stat().st_mtime * 1000)
        inferred_evidence = next(
            (found for found in (find_message_delivery_evidence(path, manifest_mtime_ms) for path in send_paths) if found),
            None,
        )
        if inferred_evidence:
            continue

        send_path = next((path for path in send_paths if Path(path).exists()), send_paths[0] if send_paths else '')
        send_path_exists = bool(send_path and Path(send_path).exists())
        chat_context = infer_chat_for_paths([str(manifest_path), *send_paths, str(manifest.get('original_image') or '')], cutoff)
        findings.append({
            'kind': 'delivery_manifest',
            'path': str(manifest_path),
            'project_id': manifest.get('project_id') or manifest_path.parent.name,
            'delivery_status': status or 'missing',
            'delivery_attempted': attempted,
            'message_id': message_id,
            'delivery_mode': manifest.get('delivery_mode') or '',
            'send_path': send_path,
            'send_paths': send_paths,
            'send_path_exists': send_path_exists,
            'original_image': manifest.get('original_image') or '',
            'fallback_required': manifest.get('fallback_required') is True,
            'error': short(manifest.get('error') or manifest.get('fallback_reason')),
            **chat_context,
        })
        if limit > 0 and len(findings) >= limit:
            break
    return findings


def audit_loose_deliverables(limit: int, cutoff: int | None) -> list[dict[str, Any]]:
    if not DELIVER_DIR.exists():
        return []
    files = [p for p in DELIVER_DIR.iterdir() if p.is_file() and is_recent_path(p, cutoff)]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            'kind': 'feishu_deliver_file',
            'path': str(path),
            'size_bytes': path.stat().st_size,
        }
        for path in files[:limit]
    ]


def print_human(payload: dict[str, Any]) -> None:
    stalled_commitments = payload['stalled_commitments']
    background_execs = payload['background_execs']
    subagents = payload['subagents']
    deliveries = payload['undelivered_manifests']
    deliver_files = payload['recent_feishu_deliver_files']

    print('OpenClaw feedback gap audit')
    print(f'- stalled commitments without tool start: {len(stalled_commitments)}')
    print(f'- background execs without follow-up: {len(background_execs)}')
    print(f'- pending/error subagents: {len(subagents)}')
    print(f'- undelivered manifests: {len(deliveries)}')
    print(f'- recent feishu-deliver files listed: {len(deliver_files)}')

    if background_execs:
        print('\nBackground execs without follow-up:')
        for item in background_execs:
            state = 'running' if item.get('pid_running') else 'not running'
            print(f"- {item['exec_session_id'] or 'unknown-session'} pid={item.get('pid')} ({state})")
            if item.get('command'):
                print(f"  command: {item['command']}")
            print(f"  session: {item['session_file']}:{item['line']}")

    if stalled_commitments:
        print('\nStalled commitments without proactive tool start:')
        for item in stalled_commitments:
            suffix = ' (user chased before next tool)' if item.get('required_user_chase') else ''
            print(f"- {item['session_file']}:{item['line']}{suffix}")
            print(f"  text: {item['text']}")
            if item.get('next_user_text'):
                print(f"  next user: {item['next_user_text']}")

    if subagents:
        print('\nSubagent issues:')
        for item in subagents:
            print(f"- {item['run_id']} [{item['status'] or item['ended_reason']}] {item['label']}")
            if item.get('pending_final_delivery'):
                print('  pending_final_delivery=true')
            if item.get('error'):
                print(f"  error: {item['error']}")
            if item.get('result'):
                print(f"  result: {item['result']}")

    if deliveries:
        print('\nUndelivered project artifacts:')
        for item in deliveries:
            marker = 'exists' if item.get('send_path_exists') else 'missing'
            print(f"- {item['project_id']} status={item['delivery_status']} send_path={marker}")
            if item.get('send_path'):
                print(f"  {item['send_path']}")
            print(f"  manifest: {item['path']}")

    if deliver_files:
        print('\nRecent files in feishu-deliver:')
        for item in deliver_files:
            print(f"- {item['path']} ({item['size_bytes']} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser(description='Audit OpenClaw tasks that may have completed without user-visible feedback.')
    parser.add_argument('--json', action='store_true', help='Print machine-readable JSON')
    parser.add_argument('--max-manifests', type=int, default=25, help='Maximum undelivered manifests to list, newest first. Use 0 for no limit')
    parser.add_argument('--recent-files', type=int, default=20, help='How many recent feishu-deliver files to list')
    parser.add_argument('--since-minutes', type=int, default=0, help='Only include records touched within this many minutes. Use 0 for no time filter')
    parser.add_argument('--background-grace-minutes', type=int, default=10, help='Ignore newly-started background execs for this many minutes')
    parser.add_argument('--commitment-grace-minutes', type=int, default=5, help='Ignore newly-made assistant commitments for this many minutes')
    parser.add_argument('--include-resolved-chases', action='store_true', help='Include historical commitments that required a user chase but were later visibly resolved')
    args = parser.parse_args()
    cutoff = cutoff_ms(args.since_minutes)

    payload = {
        'stalled_commitments': audit_stalled_commitments(
            cutoff,
            args.commitment_grace_minutes,
            args.include_resolved_chases,
        ),
        'background_execs': audit_background_execs(cutoff, args.background_grace_minutes),
        'subagents': audit_subagents(cutoff),
        'undelivered_manifests': audit_delivery_manifests(args.max_manifests, cutoff),
        'recent_feishu_deliver_files': audit_loose_deliverables(args.recent_files, cutoff),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human(payload)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
