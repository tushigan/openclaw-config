#!/usr/bin/env python3
"""Unified gpt-image-2 generator for text/image/distill workflows."""

import os
import sys
import json
import base64
import shutil
import argparse
import subprocess
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Disable proxy to avoid requests going through local proxy
for _p in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(_p, None)


def load_openclaw_env() -> None:
    env_path = Path('/Users/a123/.openclaw/.env')
    if not env_path.exists():
        return
    try:
        lines = env_path.read_text(encoding='utf-8').splitlines()
    except Exception:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_openclaw_env()

# Dual-supplier key mapping (independent keys per endpoint)
ENDPOINT_KEYS = {
    'n.lconai.com': os.getenv('BANANA_API_KEY_N', os.getenv('BANANA_API_KEY', '')),
    'cn.aixor.org': os.getenv('BANANA_API_KEY_AIXOR', os.getenv('BANANA_API_KEY_BACKUP', os.getenv('BANANA_API_KEY', ''))),
}

HOST_MODEL_ALIASES = {
    'cn.aixor.org': {
        'gpt-image-2-pro': os.getenv('BANANA_DEFAULT_MODEL_AIXOR', 'gpt-image-2').strip() or 'gpt-image-2',
    },
}

DELIVERY_DIR = Path('/Users/a123/.openclaw/workspace/feishu-deliver')
PROVIDER_STATE_FILE = Path('/Users/a123/.openclaw/.gpt_image_provider_state.json')
AGENTS_DIR = Path('/Users/a123/.openclaw/agents')


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def load_provider_state() -> dict:
    if not PROVIDER_STATE_FILE.exists():
        return {}
    try:
        return json.loads(PROVIDER_STATE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_provider_state(payload: dict) -> None:
    try:
        PROVIDER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROVIDER_STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


def resolve_result_paths(output_path: Path) -> tuple[Path, Path]:
    return (
        output_path.with_name(f'{output_path.stem}.result.json'),
        output_path.with_name(f'{output_path.stem}.delivery.json'),
    )


def build_result_base(*, output_path: Path, prompt: str, size: str, aspect: str, model: str, count: int, references: list[str]) -> dict:
    result_path, manifest_path = resolve_result_paths(output_path)
    return {
        'status': 'started',
        'phase': 'running',
        'ok': False,
        'started_at': utc_now(),
        'finished_at': None,
        'duration_seconds': None,
        'exit_code': None,
        'prompt': prompt,
        'size': size,
        'aspect': aspect,
        'model': model,
        'count': count,
        'references': references,
        'output': str(output_path),
        'exists': output_path.exists(),
        'size_bytes': output_path.stat().st_size if output_path.exists() else 0,
        'stdout_log': '',
        'stderr_log': '',
        'delivery_manifest': str(manifest_path),
        'generation_status': 'running',
        'delivery_status': 'not_attempted',
        'delivery_attempted': False,
        'delivery_attempted_at': None,
        'delivery_method': 'lark-cli',
        'delivery_target': {},
        'delivery_evidence': {},
        'fallback_required': False,
        'fallback_reason': '',
        'user_report': '',
        'error': '',
        'delivered_paths': [],
        'target_candidates': [],
        'target_conflict_reason': '',
        'result_path': str(result_path),
    }


def update_result(result_path: Path, payload: dict) -> None:
    write_json(result_path, payload)


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


def account_id_from_session_key(session_key: str) -> str:
    match = re.match(r'agent:([^:]+?)(?:-shared)?:', str(session_key or '').strip())
    return match.group(1) if match else ''


def resolve_delivery_target(
    *,
    feishu_target: str = '',
    feishu_user_id: str = '',
    feishu_chat_id: str = '',
    feishu_account_id: str = '',
    source_session_key: str = '',
) -> dict[str, str]:
    explicit_target = normalize_feishu_target(feishu_target)
    chat_id = str(feishu_chat_id or '').strip()
    user_id = str(feishu_user_id or '').strip()
    target_source = ''
    if explicit_target.startswith('chat:'):
        chat_id = explicit_target.split(':', 1)[1]
        user_id = ''
        target_source = 'explicit_target'
    elif explicit_target.startswith('user:'):
        user_id = explicit_target.split(':', 1)[1]
        chat_id = ''
        target_source = 'explicit_target'
    target = explicit_target or normalize_feishu_target(chat_id) or normalize_feishu_target(user_id)
    if target and not target_source:
        target_source = 'explicit_target'
    if not target and source_session_key:
        session_key_context = _extract_peer_from_session_key(source_session_key)
        target = str(session_key_context.get('target') or '').strip()
        if target.startswith('user:'):
            user_id = target.split(':', 1)[1]
            chat_id = ''
        elif target.startswith('chat:'):
            chat_id = target.split(':', 1)[1]
            user_id = ''
        if target:
            target_source = 'source_session_key'
    if target.startswith('chat:') and not chat_id:
        chat_id = target.split(':', 1)[1]
    if target.startswith('user:') and not user_id:
        user_id = target.split(':', 1)[1]
    account_id = str(feishu_account_id or '').strip() or account_id_from_session_key(source_session_key)
    return {
        'target': target,
        'user_id': user_id,
        'chat_id': chat_id,
        'account_id': account_id,
        'source_session_key': str(source_session_key or '').strip(),
        'target_source': target_source,
    }


def parse_runtime_context(content: str) -> dict[str, str]:
    text = str(content or '')
    target_match = re.search(r'"chat_id"\s*:\s*"(chat:[^"]+|user:[^"]+|oc_[^"]+|ou_[^"]+)"', text)
    account_match = re.search(r'Feishu\[([^\]]+)\]', text)
    sender_open_match = re.search(r'"sender_id"\s*:\s*"([^"]+)"', text)
    sender_name_match = re.search(r'"sender"\s*:\s*"([^"]+)"', text)
    target = normalize_feishu_target(target_match.group(1) if target_match else '')
    return {
        'target': target,
        'account_id': account_match.group(1) if account_match else '',
        'source_sender_open_id': sender_open_match.group(1) if sender_open_match else '',
        'source_sender_name': sender_name_match.group(1) if sender_name_match else '',
    }


def _extract_peer_from_session_key(session_key: str) -> dict[str, str]:
    """Extract delivery target from sessionKey like agent:main-shared:feishu:direct:ou_xxx."""
    m = re.match(r'agent:[^:]+:feishu:direct:(ou_[A-Za-z0-9_]+)', session_key)
    if m:
        open_id = m.group(1)
        return {
            'target': f'user:{open_id}',
            'source_sender_open_id': open_id,
        }
    m = re.match(r'agent:[^:]+:feishu:group:(oc_[A-Za-z0-9_]+)', session_key)
    if m:
        chat_id = m.group(1)
        return {
            'target': f'chat:{chat_id}',
        }
    return {}


def _is_cron_session(session_path: Path) -> bool:
    """Skip cron job session files to avoid false target attribution."""
    name = session_path.name
    # Cron sessions are in agents/main/sessions/ and match cron run IDs
    # They also tend to be in the cron runs directory
    return 'cron' in name or str(session_path).endswith('.cron.jsonl')


def _empty_inferred_target(target_source: str = '', reason: str = '', candidates: Optional[list[dict[str, str]]] = None) -> dict[str, Any]:
    return {
        'target': '',
        'user_id': '',
        'chat_id': '',
        'account_id': '',
        'source_session_key': '',
        'target_source': target_source,
        'target_candidates': candidates or [],
        'target_conflict_reason': reason,
    }


def _dedupe_target_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: dict[tuple[str, str, str], dict[str, str]] = {}
    for candidate in candidates:
        target = normalize_feishu_target(candidate.get('target') or '')
        if not target:
            continue
        item = {
            'target': target,
            'account_id': str(candidate.get('account_id') or '').strip(),
            'source_session_key': str(candidate.get('source_session_key') or '').strip(),
            'source_sender_open_id': str(candidate.get('source_sender_open_id') or '').strip(),
            'source_sender_name': str(candidate.get('source_sender_name') or '').strip(),
            'target_source': str(candidate.get('target_source') or '').strip(),
        }
        key = (item['target'], item['account_id'], item['source_session_key'])
        deduped[key] = item
    return list(deduped.values())


def _collect_sibling_manifest_candidates(output_path: Path) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    _result_path, manifest_path = resolve_result_paths(output_path)
    trusted_sources = {'explicit_target', 'source_session_key', 'sibling_manifest', 'manifest_delivery_target'}
    for sibling_manifest in sorted(output_path.parent.glob('*.delivery.json')):
        if sibling_manifest == manifest_path:
            continue
        try:
            manifest = json.loads(sibling_manifest.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue
        delivery_target = manifest.get('delivery_target') or {}
        source_session_key = str(delivery_target.get('source_session_key') or '').strip()
        target = normalize_feishu_target(
            delivery_target.get('target')
            or delivery_target.get('chat_id')
            or delivery_target.get('user_id')
        )
        recorded_source = str(delivery_target.get('target_source') or '').strip()
        if not target and source_session_key:
            target = str(_extract_peer_from_session_key(source_session_key).get('target') or '').strip()
            if not recorded_source:
                recorded_source = 'source_session_key'
        if not target:
            continue
        if recorded_source and recorded_source not in trusted_sources:
            continue
        candidates.append({
            'target': target,
            'account_id': str(delivery_target.get('account_id') or '').strip(),
            'source_session_key': source_session_key,
            'target_source': 'sibling_manifest',
        })
    return _dedupe_target_candidates(candidates)


def _collect_recent_session_candidates(output_path: Path, references: list[str]) -> list[dict[str, str]]:
    if not AGENTS_DIR.exists():
        return []
    needles = {str(output_path.resolve()), output_path.name}
    if output_path.parent.name not in ('.', '/', 'images', 'outputs', 'workspace', 'feishu-deliver'):
        needles.add(output_path.parent.name)
    for ref in references:
        if not ref or is_http_url(ref):
            continue
        ref_path = Path(ref)
        needles.add(str(ref_path))
        needles.add(ref_path.name)
    session_files = list(AGENTS_DIR.glob('*/sessions/*.jsonl'))
    session_files.extend(AGENTS_DIR.glob('*/sessions/*.trajectory.jsonl'))
    unique_files = {str(path): path for path in session_files}
    candidates: list[dict[str, str]] = []

    for session_path in sorted(unique_files.values(), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            lines = session_path.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue

        is_trajectory = session_path.name.endswith('.trajectory.jsonl')
        session_context: dict[str, str] = {}
        session_key = ''
        for line in lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not session_key:
                session_key = str(record.get('sessionKey') or '')
            if ':cron:' in session_key:
                session_context = {}
                break
            if not is_trajectory and record.get('customType') == 'openclaw.runtime-context':
                parsed = parse_runtime_context(record.get('content') or '')
                if parsed.get('target'):
                    session_context = parsed
            if is_trajectory and not session_context and session_key:
                peer_info = _extract_peer_from_session_key(session_key)
                if peer_info.get('target'):
                    session_context = {
                        'target': peer_info['target'],
                        'account_id': account_id_from_session_key(session_key),
                        'source_sender_open_id': peer_info.get('source_sender_open_id', ''),
                        'source_sender_name': '',
                    }
        if not session_context:
            continue
        if any(needle and any(needle in line for line in lines) for needle in needles):
            candidates.append({
                'target': str(session_context.get('target') or '').strip(),
                'account_id': str(session_context.get('account_id') or '').strip(),
                'source_session_key': session_key,
                'source_sender_open_id': str(session_context.get('source_sender_open_id') or '').strip(),
                'source_sender_name': str(session_context.get('source_sender_name') or '').strip(),
                'target_source': 'recent_session_scan',
            })
    return _dedupe_target_candidates(candidates)


def infer_delivery_target_from_recent_sessions(output_path: Path, references: list[str]) -> dict[str, str]:
    sibling_candidates = _collect_sibling_manifest_candidates(output_path)
    if sibling_candidates:
        unique_targets = {item['target'] for item in sibling_candidates}
        if len(unique_targets) == 1:
            winner = sibling_candidates[0]
            return resolve_delivery_target(
                feishu_target=winner['target'],
                feishu_account_id=winner.get('account_id', ''),
                source_session_key=winner.get('source_session_key', ''),
            ) | {
                'target_source': 'sibling_manifest',
                'target_candidates': sibling_candidates,
                'target_conflict_reason': '',
            }
        return _empty_inferred_target(
            target_source='sibling_manifest',
            reason='conflict_across_sibling_manifests',
            candidates=sibling_candidates,
        )

    session_candidates = _collect_recent_session_candidates(output_path, references)
    if session_candidates:
        unique_targets = {item['target'] for item in session_candidates}
        reason = 'recent_session_scan_not_trusted'
        if len(unique_targets) > 1:
            reason = 'conflict_in_recent_session_scan'
        return _empty_inferred_target(
            target_source='recent_session_scan',
            reason=reason,
            candidates=session_candidates,
        )
    return _empty_inferred_target()


def build_delivery_result_payload(
    *,
    output_path: Path,
    deliver_paths: list[Path],
    delivery_target: dict[str, str],
    sent: Optional[dict[str, Any]],
) -> dict[str, Any]:
    target = str(delivery_target.get('target') or '').strip()
    target_candidates = delivery_target.get('target_candidates') or []
    target_conflict_reason = str(delivery_target.get('target_conflict_reason') or '').strip()
    if not target:
        return {
            'project_dir': str(output_path.parent),
            'project_id': output_path.stem,
            'original_image': str(output_path),
            'delivery_mode': 'direct_image',
            'deliverables': {
                'images': [str(p) for p in deliver_paths],
            },
            'delivery_target': delivery_target,
            'delivery_attempted': False,
            'delivery_attempted_at': None,
            'delivery_status': 'pending_target_resolution',
            'delivery_method': 'lark-cli',
            'delivery_evidence': {
                'ok': False,
                'reason': 'missing_delivery_target',
                'sent_paths': [],
                'results': [],
            },
            'fallback_required': True,
            'fallback_reason': 'missing_delivery_target',
            'user_report': 'IMAGE GENERATED BUT TARGET NOT RESOLVED',
            'error': 'missing_delivery_target',
            'generated_paths': [str(p) for p in deliver_paths],
            'target_candidates': target_candidates,
            'target_conflict_reason': target_conflict_reason,
        }

    sent = sent or {
        'ok': False,
        'reason': 'lark-cli send failed',
        'sent_paths': [],
        'results': [],
    }
    return {
        'project_dir': str(output_path.parent),
        'project_id': output_path.stem,
        'original_image': str(output_path),
        'delivery_mode': 'direct_image',
        'deliverables': {
            'images': [str(p) for p in deliver_paths],
        },
        'delivery_target': delivery_target,
        'delivery_attempted': True,
        'delivery_attempted_at': utc_now(),
        'delivery_status': 'sent' if sent['ok'] else 'failed',
        'delivery_method': 'lark-cli',
        'delivery_evidence': sent,
        'fallback_required': not sent['ok'],
        'fallback_reason': '' if sent['ok'] else sent.get('reason', 'send failed'),
        'user_report': 'IMAGE GENERATED AND DELIVERED TO FEISHU' if sent['ok'] else 'IMAGE GENERATED BUT NOT DELIVERED TO USER',
        'error': '' if sent['ok'] else sent.get('reason', 'send failed'),
        'generated_paths': [str(p) for p in deliver_paths],
        'target_candidates': target_candidates,
        'target_conflict_reason': target_conflict_reason,
    }


def resolve_key(base_url: str) -> str:
    """Return the appropriate API key for the endpoint."""
    host = (base_url or '').lower()
    for endpoint_key, key in ENDPOINT_KEYS.items():
        if endpoint_key in host:
            return key
    return os.getenv('BANANA_API_KEY', '')


API_URL = os.getenv('BANANA_API_URL', 'https://n.lconai.com')
DEFAULT_MODEL = 'gpt-image-2-pro'
ENV_MODEL = os.getenv('BANANA_DEFAULT_MODEL', '')
AIXOR_API_URL = os.getenv('BANANA_API_URL_AIXOR', '')
PROVIDER_MODE = (os.getenv('BANANA_PROVIDER_MODE', 'auto') or 'auto').strip().lower()
PRIMARY_COOLDOWN_SECONDS = max(0, int(os.getenv('BANANA_PRIMARY_COOLDOWN_SECONDS', '900') or '900'))
DEFAULT_SIZE = '2880x2880'
WORKSPACE = Path('/Users/a123/.openclaw/workspace')
DISTILL_ROOT = WORKSPACE / 'skills' / 'brand-poster-distiller'
DISTILL_INDEX = DISTILL_ROOT / 'library-index.json'
RENDER_LAYOUT_SCRIPT = DISTILL_ROOT / 'scripts' / 'render_layout.py'
SKELETON_DIR = DISTILL_ROOT / 'site' / 'assets' / 'skeletons'

RATIO_TO_PIXELS = {
    '1:1': (2880, 2880),
    '5:4': (3200, 2560),
    '4:5': (2560, 3200),
    '4:3': (3264, 2448),
    '3:4': (2448, 3264),
    '16:9': (3840, 2160),
    '9:16': (2160, 3840),
    '3:2': (3504, 2336),
    '2:3': (2336, 3504),
}


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def get_mime_type(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
    }
    return mime_types.get(ext, 'image/png')


def normalize_base_url(base_url: str) -> str:
    clean = (base_url or '').rstrip('/')
    return clean or 'https://n.lconai.com'


def preferred_response_format(base_url: str) -> str:
    host = (base_url or '').lower()
    if 'cn.aixor.org' in host:
        return 'b64_json'
    return 'url'


def provider_name(base_url: str) -> str:
    host = (urlparse(base_url).netloc or '').lower()
    if 'cn.aixor.org' in host:
        return 'aixor'
    if 'n.lconai.com' in host:
        return 'n.lconai'
    return host or 'custom'


def normalize_model_for_provider(model: Optional[str], base_url: str) -> str:
    requested = (model or '').strip() or DEFAULT_MODEL
    host = (base_url or '').lower()
    for host_key, aliases in HOST_MODEL_ALIASES.items():
        if host_key in host:
            return aliases.get(requested, requested)
    return requested


def mark_primary_cooldown(reason: str, failed_provider: str) -> None:
    if PRIMARY_COOLDOWN_SECONDS <= 0:
        return
    now = time.time()
    state = load_provider_state()
    state.update({
        'primary_down_until': now + PRIMARY_COOLDOWN_SECONDS,
        'last_failure_at': now,
        'last_failure_reason': reason[:500],
        'last_failed_provider': failed_provider,
    })
    save_provider_state(state)


def clear_primary_cooldown() -> None:
    state = load_provider_state()
    if not state or not state.get('primary_down_until'):
        return
    state['primary_down_until'] = 0
    state['last_primary_recovered_at'] = time.time()
    save_provider_state(state)


def build_provider_candidates() -> list[dict]:
    primary_url = normalize_base_url(API_URL)
    aixor_url = normalize_base_url(AIXOR_API_URL) if AIXOR_API_URL else ''
    candidates: list[dict] = []
    state = load_provider_state()
    primary_down_until = float(state.get('primary_down_until', 0) or 0)
    prefer_backup = PROVIDER_MODE == 'auto' and primary_down_until > time.time()

    def add(name: str, url: str) -> None:
        if not url:
            return
        base_url = normalize_base_url(url)
        if not resolve_key(base_url):
            return
        if any(item['base_url'] == base_url for item in candidates):
            return
        candidates.append({
            'name': name,
            'base_url': base_url,
            'provider': provider_name(base_url),
        })

    if PROVIDER_MODE in {'aixor', 'backup'}:
        add('aixor', aixor_url)
        add('primary', primary_url)
    elif PROVIDER_MODE in {'primary', 'pinned'}:
        add('primary', primary_url)
    elif prefer_backup:
        add('aixor', aixor_url)
        add('primary', primary_url)
    else:
        add('primary', primary_url)
        add('aixor', aixor_url)

    if not candidates:
        add('primary', primary_url)
    return candidates


TIER_TO_PIXELS = {
    '1K': (1024, 1024),
    '2K': (2048, 2048),
    '4K': (4096, 4096),
}


def _round_up_16(v: int) -> int:
    return ((v + 15) // 16) * 16


def normalize_size(raw):
    if not raw:
        return DEFAULT_SIZE
    s = str(raw).strip()
    if s.upper() in TIER_TO_PIXELS:
        w, h = TIER_TO_PIXELS[s.upper()]
        return f'{w}x{h}'
    if s in RATIO_TO_PIXELS:
        w, h = RATIO_TO_PIXELS[s]
        return f'{w}x{h}'
    s_norm = s.replace('X', 'x').replace('*', 'x')
    if 'x' in s_norm:
        try:
            w_str, h_str = s_norm.split('x')
            w, h = int(w_str), int(h_str)
            adjusted = False
            if w % 16 != 0:
                w = _round_up_16(w)
                adjusted = True
            if h % 16 != 0:
                h = _round_up_16(h)
                adjusted = True
            if adjusted:
                print(f'[warn] size {w_str}x{h_str} is not divisible by 16; adjusting to {w}x{h}', file=sys.stderr)
            return f'{w}x{h}'
        except (ValueError, TypeError):
            pass
    return s


def expected_ratio(size: str):
    if not size:
        return None
    s = size.strip()
    if s in RATIO_TO_PIXELS:
        w, h = RATIO_TO_PIXELS[s]
        return w / h
    for sep in ('x', '*'):
        if sep in s:
            try:
                w, h = s.split(sep)
                return int(w) / int(h)
            except Exception:
                return None
    return None


def decode_base64_payload(payload: str) -> bytes:
    missing = 4 - len(payload) % 4
    if missing != 4:
        payload += '=' * missing
    return base64.b64decode(payload)


def save_url_to_file(url: str, output_path: str):
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith('data:'):
        header, sep, payload = url.partition(',')
        if not sep:
            raise ValueError('Malformed data URL: missing comma separator')
        if ';base64' not in header:
            raise ValueError('Unsupported data URL: expected base64 payload')
        target_path.write_bytes(decode_base64_payload(payload))
        return
    resp = requests.get(url, timeout=300, verify=False)
    resp.raise_for_status()
    target_path.write_bytes(resp.content)


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def resolve_distill_card(distill_id: str) -> dict:
    if not DISTILL_INDEX.exists():
        raise FileNotFoundError(f'Distill index missing: {DISTILL_INDEX}')
    index = load_json(DISTILL_INDEX)
    cards = index if isinstance(index, list) else index.get('cards', [])
    match = next((c for c in cards if c.get('id') == distill_id), None)
    if not match:
        raise ValueError(f'Distill ID not found: {distill_id}')
    card_rel = str(match.get('card_path', '')).strip()
    card_path = (DISTILL_ROOT / card_rel) if card_rel else (DISTILL_ROOT / 'cards' / f'{distill_id}.json')
    if not card_path.exists():
        raise FileNotFoundError(f'Card file missing: {card_path}')
    card = load_json(card_path)
    card['__card_path'] = str(card_path)
    return card


def ensure_skeleton_reference(distill_id: str) -> Path:
    skeleton_png = SKELETON_DIR / f'{distill_id}.png'
    if skeleton_png.exists():
        return skeleton_png

    poster_num = distill_id.split('-')[-1].lower()
    alt_png = SKELETON_DIR / f'poster-skeleton-{poster_num}.png'
    if alt_png.exists():
        return alt_png

    try:
        card = resolve_distill_card(distill_id)
        svg_rel = (card.get('layout_analysis') or {}).get('skeleton_image', '')
        if svg_rel:
            svg_path = (DISTILL_ROOT / svg_rel).resolve()
            if svg_path.exists() and svg_path.suffix.lower() == '.svg':
                SKELETON_DIR.mkdir(parents=True, exist_ok=True)
                _svg_to_png(svg_path, alt_png)
                if alt_png.exists():
                    return alt_png
    except Exception as e:
        print(f'[warn] could not resolve SVG skeleton: {e}', file=sys.stderr)

    if RENDER_LAYOUT_SCRIPT.exists():
        try:
            subprocess.run(
                ['python3', str(RENDER_LAYOUT_SCRIPT), '--id', distill_id],
                check=True,
                capture_output=True,
                text=True,
            )
            if skeleton_png.exists():
                return skeleton_png
            if alt_png.exists():
                return alt_png
        except subprocess.CalledProcessError:
            pass

    raise FileNotFoundError(f'skeleton image missing for {distill_id}')


def _svg_to_png(svg_path: Path, png_path: Path):
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1024, output_height=1536)
        print(f'[info] SVG→PNG via cairosvg: {png_path}', file=sys.stderr)
        return
    except ImportError:
        pass

    try:
        from PIL import Image, ImageDraw
        import xml.etree.ElementTree as ET

        tree = ET.parse(svg_path)
        root = tree.getroot()
        ns = ''
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'

        vb = root.get('viewBox', '0 0 800 1200')
        parts = vb.split()
        vw, vh = float(parts[2]), float(parts[3])
        scale = 1024 / vw
        pw, ph = int(vw * scale), int(vh * scale)

        img = Image.new('RGBA', (pw, ph), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        for rect in root.iter(f'{ns}rect'):
            fill = rect.get('fill', 'none')
            stroke = rect.get('stroke', 'none')
            stroke_w = float(rect.get('stroke-width', '1'))
            x = float(rect.get('x', 0)) * scale
            y = float(rect.get('y', 0)) * scale
            w = float(rect.get('width', 0)) * scale
            h = float(rect.get('height', 0)) * scale
            if fill != 'none' and fill != 'white':
                draw.rectangle([x, y, x + w, y + h], fill=_hex_to_rgba(fill))
            if stroke != 'none':
                draw.rectangle([x, y, x + w, y + h], outline=_hex_to_rgba(stroke), width=max(1, int(stroke_w * scale)))

        img.convert('RGB').save(png_path, 'PNG')
        print(f'[info] SVG→PNG via Pillow: {png_path}', file=sys.stderr)
    except Exception as e:
        print(f'[warn] SVG→PNG conversion failed: {e}', file=sys.stderr)
        raise FileNotFoundError(f'Failed to convert SVG to PNG: {e}')


def _hex_to_rgba(hex_color: str):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) == 6:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), 255)
    if len(hex_color) == 8:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), int(hex_color[6:8], 16))
    return (128, 128, 128, 255)


ROLE_LABELS = {
    'base': 'locked base image — preserve the global scene, framing, props, and all unchanged regions; edit only the explicitly requested targets',
    'skeleton': 'layout skeleton — reproduce this exact spatial composition (block positions & proportions) as faithfully as possible',
    'logo': 'brand LOGO — must be reproduced precisely, do not redraw, do not distort, do not invent new marks',
    'product': 'product reference — keep packaging shape, real materials and color identity faithful',
    'layout': 'layout reference — follow placement, framing, crop, whitespace, and camera arrangement faithfully, without borrowing foreign product identity',
    'ip': 'brand IP character — preserve identity, pose style and recognisable silhouette',
    'mascot': 'brand mascot — preserve identity and signature look',
    'style': 'artistic tone reference — imitate only style, palette and mood, do NOT copy its content/objects',
    'background': 'background/scene reference — use only as environmental cue, do not let it dominate',
    'typography': 'typography reference — imitate type style only, not the literal text',
    'element': 'locked element — this exact element must appear visibly in the final image',
}

REFERENCE_FLAG_ROLES = {
    '-r': 'unlabeled',
    '--reference': 'unlabeled',
    '--ref-base': 'base',
    '--ref-logo': 'logo',
    '--ref-product': 'product',
    '--ref-ip': 'ip',
    '--ref-mascot': 'mascot',
    '--ref-layout': 'layout',
    '--ref-style': 'style',
    '--ref-background': 'background',
    '--ref-typography': 'typography',
    '--ref-element': 'element',
}


def collect_ordered_typed_references(args, argv: list[str]) -> list[tuple[str, str]]:
    """Preserve the user's CLI reference order across typed reference flags.

    argparse groups repeated flags by option name, which silently reorders
    mixed references like --ref-style A --ref-product B. For image generation,
    that order is semantically important because prompts often refer to image
    indices. Walk argv directly and fall back to argparse groups only when an
    older caller did not expose an ordered argv sequence.
    """
    ordered_typed: list[tuple[str, str]] = []
    if args.distill_id and not args.no_auto_skeleton:
        skeleton = ensure_skeleton_reference(args.distill_id.strip())
        ordered_typed.append(('skeleton', str(skeleton)))

    consumed_from_argv = False
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token in REFERENCE_FLAG_ROLES:
            if idx + 1 >= len(argv):
                break
            ordered_typed.append((REFERENCE_FLAG_ROLES[token], argv[idx + 1]))
            consumed_from_argv = True
            idx += 2
            continue

        matched_equals = False
        for flag, role in REFERENCE_FLAG_ROLES.items():
            prefix = f'{flag}='
            if token.startswith(prefix):
                ordered_typed.append((role, token[len(prefix):]))
                consumed_from_argv = True
                matched_equals = True
                break
        idx += 1 if not matched_equals else 1

    if consumed_from_argv:
        return ordered_typed

    for role_key, items in [
        ('base', args.ref_base),
        ('logo', args.ref_logo),
        ('product', args.ref_product),
        ('layout', args.ref_layout),
        ('ip', args.ref_ip),
        ('mascot', args.ref_mascot),
        ('style', args.ref_style),
        ('background', args.ref_background),
        ('typography', args.ref_typography),
        ('element', args.ref_element),
    ]:
        for p in items or []:
            ordered_typed.append((role_key, p))
    for p in args.reference or []:
        ordered_typed.append(('unlabeled', p))
    return ordered_typed


def describe_layout_regions(card: dict) -> str:
    la = card.get('layout_analysis') or {}
    elements = la.get('elements') or []
    if not elements:
        spec = card.get('layout_spec') or {}
        regions = spec.get('regions') or []
        if not regions:
            return ''
        lines = ["Layout regions (relative coords, 0–1, top-left origin). Respect each region's role and note:"]
        for r in regions:
            name = r.get('name', '')
            role = r.get('role', '')
            top = r.get('top', 0)
            left = r.get('left', 0)
            w = r.get('width', 0)
            h = r.get('height', 0)
            note = (r.get('note') or '').strip()
            seg = f"- {name} [{role}] at top={top}, left={left}, size {w}x{h}"
            if note:
                seg += f" — {note}"
            lines.append(seg)
        reading = spec.get('reading_order') or []
        if reading:
            lines.append('Reading order: ' + ' -> '.join(reading))
        hint = (spec.get('composition_hint') or '').strip()
        if hint:
            lines.append('Composition hint: ' + hint)
        return '\n'.join(lines)

    guide = la.get('copy_planning_guide', '')
    if guide:
        return guide

    lines = [
        'Layout elements (percentage coords 0-100, top-left origin, relative to poster). Reproduce this exact spatial composition:'
    ]
    for el in sorted(elements, key=lambda e: e.get('z_index', 0)):
        el_type = el.get('type', 'unknown')
        name = el.get('name_zh', '') or el.get('id', '')
        x = el.get('x', 0)
        y = el.get('y', 0)
        w = el.get('width', 0)
        h = el.get('height', 0)
        notes = (el.get('notes') or '').strip()
        seg = f"- [{el_type}] {name}: top-left ({x}%, {y}%), size {w}%×{h}%"
        if notes:
            seg += f" — {notes}"
        lines.append(seg)
    reading = la.get('reading_order') or []
    if reading:
        lines.append('Reading order: ' + ' -> '.join(reading))
    notes = (la.get('notes') or '').strip()
    if notes:
        lines.append('Layout notes: ' + notes)
    return '\n'.join(lines)


def describe_reference_roles(typed_refs: list) -> str:
    if not typed_refs:
        return ''
    lines = ['Reference images (by role — obey each role strictly, do not swap them):']
    for idx, role, _path in typed_refs:
        label = ROLE_LABELS.get(role, f'{role} reference — follow its intended purpose')
        lines.append(f'- Image {idx}: {label}')
    return '\n'.join(lines)


def compose_distill_prompt(base_prompt: str, card: dict, typed_refs: list = None) -> str:
    chunks = [base_prompt.strip()]
    chunks.append(f"Distill ID: {card.get('id')}")

    region_block = describe_layout_regions(card)
    if region_block:
        chunks.append(region_block)

    role_block = describe_reference_roles(typed_refs or [])
    if role_block:
        chunks.append(role_block)

    la = card.get('layout_analysis') or {}
    neg_constraints = la.get('negative_constraints', [])
    if neg_constraints:
        constraint_lines = [f'- {c}' for c in neg_constraints]
        chunks.append('## 负面约束\n' + '\n'.join(constraint_lines))

    handoff = card.get('handoff', {})
    prompt_spec = handoff.get('prompt_spec', {})
    art_direction = handoff.get('art_direction', {})
    style_lock = card.get('style_design_lock', {})
    negative_prompt = (card.get('next_stage_prompt_injection') or {}).get('negative_prompt', '')

    if prompt_spec.get('visual_prompt_core'):
        chunks.append(f"Visual core: {prompt_spec['visual_prompt_core']}")
    must_have = prompt_spec.get('must_have', [])
    if must_have:
        chunks.append('Must have: ' + '; '.join(must_have[:10]))
    if art_direction:
        chunks.append(f"Composition direction: {art_direction.get('composition', '')}")
        chunks.append(f"Typography direction: {art_direction.get('typography_direction', '')}")
    if style_lock:
        chunks.append(
            'Style lock: '
            f"art_style={style_lock.get('art_style', '')}; "
            f"design_feel={style_lock.get('design_feel', '')}; "
            f"layout_soul={style_lock.get('layout_soul', '')}"
        )

    avoid = prompt_spec.get('avoid', [])
    if avoid:
        chunks.append('Avoid: ' + '; '.join(avoid[:10]))
    if negative_prompt:
        chunks.append('Negative prompt constraints: ' + negative_prompt)

    la_notes = la.get('notes', '').strip()
    if la_notes and la_notes not in str(chunks):
        chunks.append(f'Layout notes: {la_notes}')

    return '\n\n'.join([c for c in chunks if c]).strip()


def compress_reference_image(input_path: str, max_long_edge: int = 1920, quality: int = 85) -> str:
    """
    压缩参考图以减小文件大小，提升上传速度和成功率。

    Args:
        input_path: 输入图片路径
        max_long_edge: 长边最大像素（默认 1920px）
        quality: JPEG 质量（默认 85%）

    Returns:
        压缩后的临时文件路径
    """
    try:
        from PIL import Image
    except ImportError:
        print('[warn] PIL not available, skipping reference image compression', file=sys.stderr)
        return input_path

    import tempfile

    try:
        img = Image.open(input_path)
        original_size = os.path.getsize(input_path)
        width, height = img.size

        # 计算是否需要缩放
        long_edge = max(width, height)
        if long_edge > max_long_edge:
            scale = max_long_edge / long_edge
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f'[info] resized reference {Path(input_path).name}: {width}x{height} → {new_width}x{new_height}', file=sys.stderr)

        # 转换为 RGB（处理 RGBA/P 模式）
        if img.mode in ('RGBA', 'LA', 'P'):
            # 创建白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])  # 使用 alpha 通道作为 mask
                img = background
            else:
                img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # 保存为压缩的 JPEG
        fd, tmp_path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        img.save(tmp_path, 'JPEG', quality=quality, optimize=True)

        compressed_size = os.path.getsize(tmp_path)
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        print(f'[info] compressed reference {Path(input_path).name}: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB ({ratio:.1f}% reduction)', file=sys.stderr)

        return tmp_path
    except Exception as e:
        print(f'[warn] failed to compress reference image {input_path}: {e}', file=sys.stderr)
        return input_path


def _http_ref_to_local(url: str) -> str:
    import tempfile

    resp = requests.get(url, timeout=300, verify=False)
    resp.raise_for_status()
    ext = '.png'
    u = url.lower()
    for cand in ('.png', '.jpg', '.jpeg', '.webp'):
        if cand in u:
            ext = '.jpg' if cand == '.jpeg' else cand
            break
    fd, tmp = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, 'wb') as f:
        f.write(resp.content)
    return tmp


def _multipart_files_for(reference_images, compress_refs: bool = True):
    files = []
    cleanup_tmp = []
    for ref in reference_images or []:
        if is_http_url(ref):
            local = _http_ref_to_local(ref)
            cleanup_tmp.append(local)
            path = local
        else:
            if not os.path.exists(ref):
                raise ValueError(f'reference image not found: {ref}')
            path = ref

        # 压缩参考图（如果启用）
        if compress_refs:
            compressed_path = compress_reference_image(path)
            if compressed_path != path:
                cleanup_tmp.append(compressed_path)
                path = compressed_path

        fh = open(path, 'rb')
        files.append(('image', (Path(path).name, fh, get_mime_type(path))))
    return files, cleanup_tmp


def call_images_edits_with_curl(prompt, size, references, model, base_url, headers, n=1, compress_refs=True):
    """使用 curl 调用 /v1/images/edits（解决 Python SSL 兼容性问题）"""
    import subprocess

    url = f'{base_url}/v1/images/edits'

    # 准备参考图片路径
    files, tmp_paths = _multipart_files_for(references, compress_refs=compress_refs)
    ref_paths = []
    for _name, (_fn, fh, _mime) in files:
        ref_paths.append(fh.name)
        fh.close()

    # 获取 API key
    api_key = headers.get('Authorization', '').replace('Bearer ', '')

    # 构建 curl 命令
    cmd = [
        'curl',
        '-k',  # 禁用 SSL 验证（解决 SSL 兼容性问题）
        '-X', 'POST',
        url,
        '-H', f'Authorization: Bearer {api_key}',
        '-F', f'model={model}',
        '-F', f'prompt={prompt}',
        '-F', f'n={max(1, int(n))}',
        '-F', f'size={size}',
        '-F', f'response_format={preferred_response_format(base_url)}',
        '--max-time', '600',
        '-s',  # 静默模式
    ]

    # 添加参考图片
    for i, ref_path in enumerate(ref_paths):
        cmd.extend(['-F', f'image=@{ref_path}'])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=610
        )

        if result.returncode != 0:
            raise requests.HTTPError(f'curl failed with return code {result.returncode}: {result.stderr[:500]}')

        response_data = json.loads(result.stdout)

        # 检查错误
        if 'error' in response_data:
            error_msg = response_data['error'].get('message', 'Unknown error')
            raise requests.HTTPError(f'API error: {error_msg}')

        return _normalise_response_items(response_data)

    finally:
        # 清理临时文件
        for tmp in tmp_paths:
            try:
                os.unlink(tmp)
            except Exception:
                pass


def call_images_edits(prompt, size, references, model, base_url, headers, n=1, compress_refs=True):
    """调用 /v1/images/edits，自动选择 curl 或 requests"""
    # 如果是大请求（多个参考图或长提示词），使用 curl
    use_curl = len(references) >= 2 or len(prompt) > 1000

    if use_curl:
        print('[info] using curl for large request (Python SSL compatibility)', file=sys.stderr)
        return call_images_edits_with_curl(prompt, size, references, model, base_url, headers, n, compress_refs)

    # 小请求使用 requests
    url = f'{base_url}/v1/images/edits'
    files, tmp_paths = _multipart_files_for(references, compress_refs=compress_refs)
    data_fields = {
        'model': model,
        'prompt': prompt,
        'n': str(max(1, int(n))),
        'size': size,
        'response_format': preferred_response_format(base_url),
    }
    try:
        response = requests.post(url, headers=headers, data=data_fields, files=files, timeout=600, verify=False)
    finally:
        for _name, (_fn, fh, _mime) in files:
            try:
                fh.close()
            except Exception:
                pass
        for tmp in tmp_paths:
            try:
                os.unlink(tmp)
            except Exception:
                pass
    if response.status_code != 200:
        raise requests.HTTPError(f'{response.status_code} from /v1/images/edits: {response.text[:500]}', response=response)
    return _normalise_response_items(response.json())


def call_images_generations(prompt, size, model, base_url, headers, n=1):
    url = f'{base_url}/v1/images/generations'
    body = {
        'model': model,
        'prompt': prompt,
        'n': max(1, int(n)),
        'size': size,
        'response_format': preferred_response_format(base_url),
    }
    response = requests.post(
        url,
        headers={**headers, 'Content-Type': 'application/json'},
        json=body,
        timeout=600,
        verify=False,
    )
    if response.status_code != 200:
        raise requests.HTTPError(f'{response.status_code} from /v1/images/generations: {response.text[:500]}', response=response)
    return _normalise_response_items(response.json())


RETRYABLE_BUSY_MARKERS = (
    '正在加号请稍等',
    'please wait',
    'try again later',
    'server is busy',
    'rate limit',
    'too many requests',
    'temporarily unavailable',
)

PROVIDER_SWITCH_MARKERS = (
    'model_not_found',
    'no available channel for model',
    'invalid model',
    '该令牌状态不可用',
    'token status unavailable',
    'token unavailable',
    'invalid token',
    'api key unavailable',
    '正在加号请稍等',
    'please wait',
    'try again later',
    'server is busy',
    'temporarily unavailable',
)


def is_retryable_busy_error(exc: Exception) -> bool:
    if isinstance(exc, (requests.ReadTimeout, requests.ConnectTimeout, requests.Timeout)):
        return True
    if not isinstance(exc, requests.HTTPError):
        return False
    response = getattr(exc, 'response', None)
    status = getattr(response, 'status_code', None)
    text = ''
    try:
        text = (response.text or '') if response is not None else str(exc)
    except Exception:
        text = str(exc)
    haystack = text.lower()
    if status in {429, 500, 502, 503, 504}:
        return True
    return any(marker.lower() in haystack for marker in RETRYABLE_BUSY_MARKERS)


def is_provider_switchable_error(exc: Exception) -> bool:
    if isinstance(exc, (requests.ReadTimeout, requests.ConnectTimeout, requests.Timeout)):
        return True
    if not isinstance(exc, requests.HTTPError):
        return False
    response = getattr(exc, 'response', None)
    status = getattr(response, 'status_code', None)
    text = ''
    try:
        text = (response.text or '') if response is not None else str(exc)
    except Exception:
        text = str(exc)
    haystack = text.lower()
    if status in {429, 500, 502, 503, 504}:
        return True
    if status in {401, 403} and any(marker.lower() in haystack for marker in PROVIDER_SWITCH_MARKERS):
        return True
    return any(marker.lower() in haystack for marker in PROVIDER_SWITCH_MARKERS)


def _normalise_response_items(payload: dict) -> list:
    if not isinstance(payload, dict):
        raise ValueError(f'Unexpected API response: {payload!r}')
    data = payload.get('data')
    if isinstance(data, list) and data:
        return data
    if isinstance(data, dict):
        content = data.get('content')
        if isinstance(content, list) and content:
            return content
    if payload.get('url') or payload.get('b64_json'):
        return [payload]
    raise ValueError(f'Unexpected API response: {json.dumps(payload, indent=2, ensure_ascii=False)[:800]}')


def call_images_api_on_provider(
    *,
    prompt: str,
    image_size: str,
    reference_images=None,
    model: str = None,
    count: int = 1,
    base_url: str,
    invocation_meta: Optional[dict] = None,
    fast_failover_on_switchable_error: bool = False,
    compress_refs: bool = True,
) -> list:
    if not resolve_key(base_url):
        raise ValueError(f'No API key configured for provider {provider_name(base_url)} ({base_url})')

    requested_model = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    effective_model = normalize_model_for_provider(requested_model, base_url)
    size = normalize_size(image_size)
    if effective_model.startswith('gpt-image') and not any(sep in str(size) for sep in ('x', '*')):
        print(
            f'[warn] gpt-image-2 requires pixel sizes (e.g. 1024x1024, 1536x1152, 2048x1536). Ratio/tier values like "{size}" are rejected by the gateway (HTTP 400 "不合法的size").',
            file=sys.stderr,
        )
    if effective_model != requested_model:
        print(
            f'[note] provider {provider_name(base_url)} remapped requested model {requested_model} -> {effective_model}',
            file=sys.stderr,
        )
    headers = {'Authorization': f'Bearer {resolve_key(base_url)}'}

    refs = [r for r in (reference_images or []) if r]
    count = max(1, int(count))

    if invocation_meta is not None:
        invocation_meta.update({
            'provider_mode': PROVIDER_MODE,
            'api_base_url': base_url,
            'api_provider': provider_name(base_url),
            'requested_model': requested_model,
            'effective_model': effective_model,
            'references_count': len(refs),
        })

    retry_attempts = max(1, int(os.getenv('BANANA_RETRY_ATTEMPTS', '3') or '3'))
    retry_backoffs = [int(part.strip()) for part in os.getenv('BANANA_RETRY_BACKOFFS', '8,20').split(',') if part.strip()]
    if not retry_backoffs:
        retry_backoffs = [8, 20]

    def _single(n_req):
        if refs:
            return call_images_edits(prompt, size, refs, effective_model, base_url, headers, n=n_req, compress_refs=compress_refs)
        return call_images_generations(prompt, size, effective_model, base_url, headers, n=n_req)

    def _single_with_retry(n_req):
        attempt = 1
        while True:
            try:
                return _single(n_req)
            except Exception as exc:
                if fast_failover_on_switchable_error and is_provider_switchable_error(exc):
                    raise
                if attempt >= retry_attempts or not is_retryable_busy_error(exc):
                    raise
                backoff = retry_backoffs[min(attempt - 1, len(retry_backoffs) - 1)]
                print(
                    f'[warn] upstream busy on attempt {attempt}/{retry_attempts}: {exc}. retrying in {backoff}s...',
                    file=sys.stderr,
                )
                time.sleep(backoff)
                attempt += 1

    first_items = _single_with_retry(count)
    if len(first_items) >= count:
        return first_items[:count]

    remaining = count - len(first_items)
    print(
        f'[info] gateway returned {len(first_items)} item(s) for n={count}; fanning out {remaining} parallel request(s) to reach {count}.',
        file=sys.stderr,
    )
    collected = list(first_items)
    with ThreadPoolExecutor(max_workers=min(remaining, 5)) as ex:
        futures = [ex.submit(_single_with_retry, 1) for _ in range(remaining)]
        for fut in as_completed(futures):
            try:
                collected.extend(fut.result())
            except Exception as e:
                print(f'[warn] parallel request failed: {e}', file=sys.stderr)
    return collected[:count]


def call_images_api(prompt: str, image_size: str, reference_images=None, model: Optional[str] = None, count: int = 1, invocation_meta: Optional[dict] = None, compress_refs: bool = True) -> list:
    candidates = build_provider_candidates()
    if not candidates:
        raise ValueError('No usable image providers configured')

    last_exc = None
    for idx, candidate in enumerate(candidates, start=1):
        base_url = candidate['base_url']
        has_next = idx < len(candidates)
        try:
            items = call_images_api_on_provider(
                prompt=prompt,
                image_size=image_size,
                reference_images=reference_images,
                model=model,
                count=count,
                base_url=base_url,
                invocation_meta=invocation_meta,
                fast_failover_on_switchable_error=has_next,
                compress_refs=compress_refs,
            )
            if candidate['name'] == 'primary':
                clear_primary_cooldown()
            return items
        except Exception as exc:
            last_exc = exc
            if invocation_meta is not None:
                invocation_meta.update({
                    'api_base_url': base_url,
                    'api_provider': provider_name(base_url),
                    'requested_model': (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL,
                    'effective_model': normalize_model_for_provider(model, base_url),
                })
            if not has_next or not is_provider_switchable_error(exc):
                raise
            if candidate['name'] == 'primary':
                mark_primary_cooldown(str(exc), provider_name(base_url))
            next_candidate = candidates[idx]
            print(
                f'[warn] provider {provider_name(base_url)} failed with switchable error: {exc}. '
                f'trying {provider_name(next_candidate["base_url"])} next...',
                file=sys.stderr,
            )
    if last_exc is not None:
        raise last_exc
    raise RuntimeError('Image API returned without a result')


def validate_image_signature(path: str):
    try:
        with open(path, 'rb') as f:
            sig = f.read(12)
    except Exception as e:
        print(f'[warn] could not open output for signature check: {e}', file=sys.stderr)
        return
    ok = sig.startswith(b'\x89PNG\r\n\x1a\n') or sig[:3] == b'\xff\xd8\xff' or sig[:4] == b'RIFF'
    if not ok:
        print(f'[warn] output file does not look like PNG/JPG/WEBP. signature={sig!r}', file=sys.stderr)


def assert_returned_size(output_path: str, requested_size: str):
    try:
        from PIL import Image

        w, h = Image.open(output_path).size
    except Exception as e:
        print(f'[warn] could not read output dimensions: {e}', file=sys.stderr)
        return
    exp = expected_ratio(requested_size)
    print(f'Returned image size: {w}x{h}')
    if exp is None:
        return
    got = w / h if h else 0
    if abs(got - exp) / exp > 0.05:
        print(
            f'[warn] requested size={requested_size} (expected AR≈{exp:.3f}) but server returned {w}x{h} (AR={got:.3f}). The upstream may be ignoring the size parameter for this model.',
            file=sys.stderr,
        )


def send_feishu_images(deliver_paths: list[Path], *, target: str = '', user_id: str = '', chat_id: str = '') -> dict:
    normalized_target = normalize_feishu_target(target)
    target_args = []
    target_label = ''
    if normalized_target.startswith('chat:'):
        actual_chat_id = normalized_target.split(':', 1)[1]
        target_args = ['--chat-id', actual_chat_id]
        target_label = f'target={normalized_target}'
    elif normalized_target.startswith('user:'):
        actual_user_id = normalized_target.split(':', 1)[1]
        target_args = ['--user-id', actual_user_id]
        target_label = f'target={normalized_target}'
    elif chat_id:
        target_args = ['--chat-id', chat_id]
        target_label = f'chat_id={chat_id}'
    elif user_id:
        target_args = ['--user-id', user_id]
        target_label = f'user_id={user_id}'
    else:
        return {
            'ok': False,
            'reason': 'missing_delivery_target',
            'sent_paths': [],
            'results': [],
        }

    ok = True
    results = []
    for path in deliver_paths:
        cmd = ['npx', 'lark-cli', 'im', '+messages-send', '--as', 'bot', *target_args, '--image', str(path)]
        print(f'[deliver] sending {path} to Feishu {target_label}')
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=180)
        if result.stdout.strip():
            print(result.stdout.strip())
        item = {
            'path': str(path),
            'returncode': result.returncode,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'sent': result.returncode == 0,
        }
        results.append(item)
        if result.returncode != 0:
            ok = False
            print(f'[deliver:error] lark-cli failed for {path}: {result.stderr.strip()}', file=sys.stderr)
        else:
            print(f'[deliver] sent successfully: {path}')
    return {
        'ok': ok,
        'reason': '' if ok else 'lark-cli send failed',
        'sent_paths': [item['path'] for item in results if item['sent']],
        'results': results,
    }


def main():
    parser = argparse.ArgumentParser(description='Unified gpt-image-2 generator')
    parser.add_argument('prompt_positional', nargs='?', help='Prompt text (backward compatible positional arg)')
    parser.add_argument('-p', '--prompt', help='Prompt text')
    parser.add_argument('--prompt-file', help='Read prompt from file (useful for long prompts that trigger gateway preflight rejection)')
    parser.add_argument('-r', '--reference', action='append', default=[], help='Reference image path or URL (repeatable, unlabeled)')
    parser.add_argument('--ref-base', action='append', default=[], help='Reference image as locked base image for local edits')
    parser.add_argument('--ref-logo', action='append', default=[], help='Reference image as brand LOGO (repeatable)')
    parser.add_argument('--ref-product', action='append', default=[], help='Reference image as product')
    parser.add_argument('--ref-ip', action='append', default=[], help='Reference image as brand IP character')
    parser.add_argument('--ref-mascot', action='append', default=[], help='Reference image as brand mascot')
    parser.add_argument('--ref-layout', action='append', default=[], help='Reference image as layout/composition authority')
    parser.add_argument('--ref-style', action='append', default=[], help='Reference image as artistic tone / palette')
    parser.add_argument('--ref-background', action='append', default=[], help='Reference image as background/scene')
    parser.add_argument('--ref-typography', action='append', default=[], help='Reference image as typography sample')
    parser.add_argument('--ref-element', action='append', default=[], help='Reference image as a locked element that must appear')
    parser.add_argument('-a', '--aspect', default='1:1', help='Compatibility arg only; not sent to API')
    parser.add_argument('-s', '--size', default=DEFAULT_SIZE, help='Image size (pixel form like 1024x1024, 1536x1152, 2048x1536). Ratio values like 4:3 are rejected by the gateway.')
    parser.add_argument('-o', '--output', default='output.png', help='Output file path. When --count>1 extra images are saved as <stem>_2.png, <stem>_3.png, ...')
    parser.add_argument('-n', '--count', type=int, default=1, help='How many images to generate for the same prompt (1-10). Default 1. Values >1 fan out in parallel if the upstream ignores n.')
    parser.add_argument('-m', '--model', default=DEFAULT_MODEL, help='Model name')
    parser.add_argument('--distill-id', help='Attach constraints and skeleton from brand-poster-distiller')
    parser.add_argument('--no-auto-skeleton', action='store_true', help='Disable auto attach of distill skeleton PNG')
    parser.add_argument('--feishu-target', default=os.getenv('OPENCLAW_FEISHU_TARGET', ''), help='Optional explicit Feishu target (`user:ou_xxx` or `chat:oc_xxx`) to auto-send generated images')
    parser.add_argument('--feishu-user-id', default=os.getenv('OPENCLAW_FEISHU_USER_ID', os.getenv('FEISHU_USER_ID', '')), help='Optional Feishu open_id (ou_xxx) to auto-send generated images')
    parser.add_argument('--feishu-chat-id', default=os.getenv('OPENCLAW_FEISHU_CHAT_ID', os.getenv('FEISHU_CHAT_ID', '')), help='Optional Feishu chat_id (oc_xxx) to auto-send generated images')
    parser.add_argument('--feishu-account-id', default=os.getenv('OPENCLAW_FEISHU_ACCOUNT_ID', ''), help='Optional Feishu account id associated with the current conversation')
    parser.add_argument('--source-session-key', default=os.getenv('OPENCLAW_SOURCE_SESSION_KEY', ''), help='Optional OpenClaw session key that owns the current delivery target')
    parser.add_argument('--no-compress-refs', action='store_true', help='Disable automatic reference image compression (default: compress to max 1920px long edge, JPEG 85%%)')

    args = parser.parse_args()

    if args.prompt_file:
        prompt_path = Path(args.prompt_file)
        if not prompt_path.exists():
            raise SystemExit(f'Prompt file not found: {args.prompt_file}')
        prompt = prompt_path.read_text(encoding='utf-8').strip()
    else:
        prompt = (args.prompt or args.prompt_positional or '').strip()

    if not prompt:
        raise SystemExit('Need prompt: pass positional prompt, --prompt, or --prompt-file')

    count = max(1, min(10, int(args.count or 1)))
    output_path = Path(args.output)
    result_path, manifest_path = resolve_result_paths(output_path)
    start_dt = datetime.now(timezone.utc)

    ordered_typed = collect_ordered_typed_references(args, sys.argv[1:])

    references = [p for _role, p in ordered_typed]
    typed_for_prompt = [(idx, role, path) for idx, (role, path) in enumerate(ordered_typed, 1) if role != 'unlabeled']

    if args.distill_id:
        card = resolve_distill_card(args.distill_id.strip())
        prompt = compose_distill_prompt(prompt, card, typed_refs=typed_for_prompt)
    elif typed_for_prompt:
        prompt = '\n\n'.join([prompt, describe_reference_roles(typed_for_prompt)]).strip()

    endpoint = '/v1/images/edits' if references else '/v1/images/generations'
    print('Generating image...')
    print(f'Endpoint: {endpoint}')
    print(f'Model: {args.model}')
    print(f'Provider mode: {PROVIDER_MODE}')
    print(f'Primary base URL: {normalize_base_url(API_URL)}')
    if ENV_MODEL and ENV_MODEL != DEFAULT_MODEL:
        print(f'[note] ignoring BANANA_DEFAULT_MODEL={ENV_MODEL}; this skill is locked to default model {DEFAULT_MODEL} unless --model is explicitly passed.')
    print(f'Requested size: {args.size}  (normalised: {normalize_size(args.size)})')
    print(f'References: {len(references)}')
    if references:
        print('Reference list:')
        for ref in references:
            print(f'- {ref}')
    print(f'Count: {count}')
    print(f'Prompt:\n{prompt}')

    result_payload = build_result_base(
        output_path=output_path,
        prompt=prompt,
        size=args.size,
        aspect=args.aspect,
        model=args.model,
        count=count,
        references=references,
    )
    update_result(result_path, result_payload)
    api_meta: dict = {}

    try:
        items = call_images_api(
            prompt=prompt,
            image_size=args.size,
            reference_images=references,
            model=args.model,
            count=count,
            invocation_meta=api_meta,
            compress_refs=not args.no_compress_refs,
        )
        result_payload.update(api_meta)
        if not items:
            raise ValueError('API returned no image items')

        out_paths = []
        for idx, item in enumerate(items, start=1):
            target = output_path if idx == 1 else output_path.with_name(f'{output_path.stem}_{idx}{output_path.suffix}')
            out_paths.append(target)

            if item.get('url'):
                print(f"[{idx}/{len(items)}] Image URL: {item['url']}")
                save_url_to_file(item['url'], str(target))
            elif item.get('b64_json'):
                image_bytes = decode_base64_payload(item['b64_json'])
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, 'wb') as f:
                    f.write(image_bytes)
            else:
                raise ValueError(f"Unexpected image response item: {json.dumps(item, indent=2, ensure_ascii=False)}")

            validate_image_signature(str(target))
            assert_returned_size(str(target), args.size)
            print(f'[{idx}/{len(items)}] Image saved to: {target}')
            if item.get('revised_prompt'):
                print(f"[{idx}/{len(items)}] Revised prompt: {item['revised_prompt']}")

        if len(out_paths) > 1:
            print('All images:')
            for p in out_paths:
                print(f'- {p}')

        DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
        deliver_paths = []
        for p in out_paths:
            dest = DELIVERY_DIR / p.name
            shutil.copy2(str(p), str(dest))
            deliver_paths.append(dest)
            print(f'[deliver] copied to {dest}')

        delivery_target = resolve_delivery_target(
            feishu_target=args.feishu_target.strip(),
            feishu_user_id=args.feishu_user_id.strip(),
            feishu_chat_id=args.feishu_chat_id.strip(),
            feishu_account_id=args.feishu_account_id.strip(),
            source_session_key=args.source_session_key.strip(),
        )
        if not delivery_target.get('target'):
            inferred_target = infer_delivery_target_from_recent_sessions(output_path, references)
            if inferred_target:
                delivery_target = {
                    **delivery_target,
                    **{k: v for k, v in inferred_target.items() if v},
                }
        delivery_target['channel'] = 'feishu'
        result_payload.update({
            'status': 'succeeded',
            'phase': 'generated',
            'ok': True,
            'finished_at': utc_now(),
            'duration_seconds': round((datetime.now(timezone.utc) - start_dt).total_seconds(), 3),
            'exit_code': 0,
            'exists': all(p.exists() for p in out_paths),
            'size_bytes': sum(p.stat().st_size for p in out_paths if p.exists()),
            'generation_status': 'generated',
            'delivery_status': 'verified',
            'delivery_target': delivery_target,
            'delivered_paths': [str(p) for p in deliver_paths],
        })
        update_result(result_path, result_payload)

        sent = None
        if delivery_target.get('target'):
            sent = send_feishu_images(deliver_paths, target=delivery_target['target'])
        manifest = build_delivery_result_payload(
            output_path=output_path,
            deliver_paths=deliver_paths,
            delivery_target=delivery_target,
            sent=sent,
        )
        write_json(manifest_path, manifest)

        result_payload.update({
            'delivery_manifest': str(manifest_path),
            'delivery_status': manifest['delivery_status'],
            'delivery_attempted': manifest['delivery_attempted'],
            'delivery_attempted_at': manifest['delivery_attempted_at'],
            'delivery_evidence': manifest['delivery_evidence'],
            'fallback_required': manifest['fallback_required'],
            'fallback_reason': manifest['fallback_reason'],
            'user_report': manifest['user_report'],
            'error': manifest['error'],
            'delivered_paths': manifest['delivery_evidence'].get('sent_paths', []),
            'delivery_target': delivery_target,
            'target_candidates': manifest.get('target_candidates', []),
            'target_conflict_reason': manifest.get('target_conflict_reason', ''),
        })
        if manifest['delivery_status'] == 'pending_target_resolution':
            result_payload.update({
                'delivery_error': 'missing_delivery_target',
            })
        elif not sent['ok']:
            result_payload.update({
                'status': 'succeeded',
                'phase': 'generated',
                'ok': True,
                'exit_code': 0,
                'delivery_error': sent.get('reason', 'send failed'),
            })
        update_result(result_path, result_payload)

        if sent and sent['ok']:
            print()
            print('=' * 60)
            print('✅ IMAGE GENERATED AND DELIVERED TO FEISHU')
            print('=' * 60)
            for p in deliver_paths:
                print(f'[delivered] {p}')
            print('=' * 60)
            return 0

        if manifest['delivery_status'] == 'pending_target_resolution':
            print()
            print('=' * 60)
            print('⚠️ IMAGE GENERATED BUT TARGET NOT RESOLVED')
            print('=' * 60)
            for p in deliver_paths:
                print(f'[ready] {p}')
            print('=' * 60)
            return 0

        print()
        print('=' * 60)
        print('⚠️  IMAGE GENERATED BUT NOT DELIVERED TO USER')
        print('=' * 60)
        print('You MUST now deliver the image to the user:')
        for p in deliver_paths:
            print(f'  1. Image ready at: {p}')
            print(f'  2. Send the real media in Feishu, e.g. message(action=send, channel=feishu, media="{p}")')
            print(f'  3. If this came from a Feishu group/DM, use the original chat_id/account_id from runtime context.')
        print('DO NOT reply "Done." or "NO_REPLY" without sending the image.')
        print('DO NOT just return the local file path as delivery.')
        print('DO NOT send MEDIA:/path as text; that is not a real Feishu media message.')
        print('The user MUST receive the image in their Feishu chat.')
        print('=' * 60)
        return 0

    except Exception as e:
        output_exists = any(p.exists() for p in out_paths) if 'out_paths' in locals() else output_path.exists()
        output_size = sum(p.stat().st_size for p in out_paths if p.exists()) if 'out_paths' in locals() else (output_path.stat().st_size if output_path.exists() else 0)
        result_payload.update({
            **api_meta,
            'status': 'failed',
            'phase': 'generate_failed',
            'ok': False,
            'finished_at': utc_now(),
            'duration_seconds': round((datetime.now(timezone.utc) - start_dt).total_seconds(), 3),
            'exit_code': 1,
            'exists': output_exists,
            'size_bytes': output_size,
            'generation_status': 'failed',
            'delivery_status': 'not_attempted',
            'error': str(e),
        })
        update_result(result_path, result_payload)
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
