#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager

TARGET_SCRIPT = Path('/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py')
ROLE_TO_FLAG = {
    'style_ref': '--ref-style',
    'skeleton': '--ref-layout',
    'product': '--ref-product',
    'product_texture': '--reference',
    'ip': '--ref-ip',
    'logo': '--ref-logo',
}


def looks_like_generated_style_ref(path: str, project_dir: Path | None = None) -> bool:
    raw = str(path or '').strip()
    if not raw:
        return False
    ref_path = Path(raw)
    stem = ref_path.stem.lower()
    name = ref_path.name.lower()

    if stem == 'current_base_ref':
        return True
    if stem.startswith('final_poster') or name.startswith('final_poster'):
        return True
    if stem.startswith('generated_') or stem.endswith('_generated') or '-generated' in stem:
        return True

    if project_dir is not None:
        try:
            resolved = ref_path.resolve()
            images_dir = (project_dir / 'images').resolve()
            if resolved.parent == images_dir and stem.startswith('final_'):
                return True
        except Exception:
            return False
    return False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def next_attempt(log_dir: Path) -> int:
    attempts = []
    for path in log_dir.glob('generate.attempt-*.stdout.log'):
        stem = path.name
        try:
            attempts.append(int(stem.split('attempt-')[1].split('.')[0]))
        except (IndexError, ValueError):
            continue
    return max(attempts, default=0) + 1


def tail_text(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8', errors='ignore')[-limit:]


def classify_generation_error(error_text: str) -> str:
    text = (error_text or '').lower()
    if not text:
        return 'unknown'
    if 'quota' in text or 'pre-consumed quota failed' in text or 'insufficient_quota' in text:
        return 'quota_insufficient'
    if 'permission' in text or 'forbidden' in text or 'access denied' in text:
        return 'permission_denied'
    if '401' in text or '403' in text or '429' in text or '/v1/images/' in text:
        return 'provider_error'
    return 'command_failed'


def recommended_action_for_error(category: str) -> str:
    if category == 'quota_insufficient':
        return '补充生图额度或切换到可用 provider 后重试正式生图。'
    if category == 'permission_denied':
        return '修复脚本路径或执行权限后，重新运行正式生图。'
    if category == 'provider_error':
        return '检查上游生图接口状态、鉴权和 provider 配置后重试。'
    if category == 'command_failed':
        return '查看 stdout/stderr 日志，修复命令或输入后重试正式生图。'
    return '查看日志并修复正式生图链路后重试。'


def _text_values(value) -> str:
    if isinstance(value, list):
        return ' '.join(str(item or '') for item in value)
    if isinstance(value, dict):
        return ' '.join(_text_values(item) for item in value.values())
    return str(value or '')


def _asset_path(project_dir: Path, raw_path: str) -> str:
    raw = str(raw_path or '').strip()
    if not raw:
        return ''
    path = Path(raw)
    if not path.is_absolute():
        path = project_dir / path
    return str(path.resolve())


def _has_required_ref(resolved_refs: list[dict], role: str, expected_path: str) -> bool:
    for ref in resolved_refs:
        if ref.get('role') != role:
            continue
        if not expected_path:
            return True
        if str(Path(ref.get('path', '')).resolve()) == expected_path:
            return True
    return False


def validate_preflight(project_dir: Path, brief: dict, ref_order_data: dict) -> tuple[list[str], list[dict], list[str], list[str]]:
    errors: list[str] = []
    resolved_refs: list[dict] = []
    missing_refs: list[str] = []
    required_files = [
        project_dir / 'brief.json',
        project_dir / 'copywriting.json',
        project_dir / 'prompt_draft.md',
        project_dir / 'ref_order.json',
    ]
    if brief.get('distill_card_id'):
        required_files.append(project_dir / 'distill_card.json')

    for file_path in required_files:
        if not file_path.exists():
            errors.append(f'缺少必需文件: {file_path}')

    prompt_path = project_dir / 'prompt_draft.md'
    if prompt_path.exists() and not prompt_path.read_text(encoding='utf-8').strip():
        errors.append(f'prompt 文件为空: {prompt_path}')

    assets = brief.get('assets', {}) or {}
    hero = brief.get('hero_priority', {}) or {}
    hero1 = str(hero.get('hero_1', '') or '')
    product_asset = str(assets.get('product', '') or '').strip()
    ip_asset = str(assets.get('ip', '') or '').strip()

    if '产品' in hero1 and not product_asset:
        errors.append('hero_1 已指定为产品，但 brief.assets.product 为空。')

    if product_asset and ip_asset and product_asset == ip_asset:
        errors.append('brief.assets.product 与 brief.assets.ip 指向同一路径。')

    order = ref_order_data.get('ref_order', []) or []
    if not order:
        errors.append('ref_order.json 为空，缺少参考图顺序。')

    for item in order:
        role = str(item.get('role', '') or '').strip()
        raw_path = str(item.get('path', '') or '').strip()
        if role not in ROLE_TO_FLAG:
            errors.append(f'未知参考图角色: {role}')
            continue
        if not raw_path:
            errors.append(f'{role} 缺少 path')
            continue
        ref_path = Path(raw_path)
        if not ref_path.is_absolute():
            errors.append(f'{role} 路径不是绝对路径: {raw_path}')
            missing_refs.append(raw_path)
            continue
        resolved_refs.append({
            'index': item.get('index'),
            'role': role,
            'path': str(ref_path),
        })
        if not ref_path.exists():
            errors.append(f'{role} 参考图不存在: {ref_path}')
            missing_refs.append(str(ref_path))

    product_ref = next((r for r in resolved_refs if r['role'] == 'product'), None)
    ip_ref = next((r for r in resolved_refs if r['role'] == 'ip'), None)
    if product_ref and ip_ref and product_ref['path'] == ip_ref['path']:
        errors.append('ref_order.json 中的 product 与 ip 指向同一路径。')

    must_include_text = _text_values(brief.get('must_include', '')).lower()
    hero_text = _text_values(hero).lower()
    logo_required = any(token in must_include_text for token in ('logo', '品牌logo', '标志', '商标'))
    ip_required = (
        'ip' in must_include_text
        or '品牌ip' in must_include_text
        or '角色' in must_include_text
        or 'ip' in hero_text
        or '品牌ip' in hero_text
    )

    logo_expected = _asset_path(project_dir, assets.get('logo', ''))
    ip_expected = _asset_path(project_dir, assets.get('ip', ''))
    if logo_required:
        if not logo_expected:
            errors.append('brief.must_include 要求 Logo，但 brief.assets.logo 为空。')
        elif not _has_required_ref(resolved_refs, 'logo', logo_expected):
            errors.append('brief.must_include 要求 Logo，但 ref_order.json 中缺少匹配的 logo 参考图。')
    if ip_required:
        if not ip_expected:
            errors.append('brief.must_include/hero_priority 要求 IP，但 brief.assets.ip 为空。')
        elif not _has_required_ref(resolved_refs, 'ip', ip_expected):
            errors.append('brief.must_include/hero_priority 要求 IP，但 ref_order.json 中缺少匹配的 ip 参考图。')

    workflow_options = brief.get('workflow_options', {}) or {}
    allow_generated_style_refs = bool(brief.get('allow_generated_style_refs')) or bool(workflow_options.get('allow_generated_style_refs'))
    if not allow_generated_style_refs:
        for item in resolved_refs:
            if item['role'] != 'style_ref':
                continue
            if looks_like_generated_style_ref(item['path'], project_dir):
                errors.append(
                    '正式生图禁止把上一版 AI 成图或项目输出图继续作为 style_ref：'
                    f"{item['path']}。请改用真实风格参考图，或只保留骨架图/产品图/Logo。"
                )

    return errors, resolved_refs, missing_refs, [str(p) for p in required_files]


def build_command(prompt_path: Path, output_path: Path, refs: list[dict], size: str, aspect: str, model: str, count: int = 1) -> list[str]:
    cmd = [
        'python3',
        str(TARGET_SCRIPT),
        '--prompt-file',
        str(prompt_path),
    ]
    for item in refs:
        cmd.extend([ROLE_TO_FLAG[item['role']], item['path']])
    cmd.extend([
        '--output',
        str(output_path),
        '--size',
        size,
        '--aspect',
        aspect,
        '--model',
        model,
        '--count',
        str(max(1, min(int(count or 1), 10))),
    ])
    return cmd


def build_generation_env(brief: dict) -> dict:
    env = dict(os.environ)
    workflow_options = brief.get('workflow_options', {}) or {}
    provider_mode = str(
        workflow_options.get('image_provider_mode')
        or brief.get('image_provider_mode')
        or 'auto'
    ).strip().lower() or 'auto'
    env['BANANA_PROVIDER_MODE'] = provider_mode
    return env


def summarize_command(cmd: list[str]) -> str:
    return ' '.join(shlex.quote(part) for part in cmd)


def make_base_result(project_dir: Path, attempt: int, prompt_path: Path, output_path: Path, stdout_log: Path, stderr_log: Path, refs: list[dict], missing_refs: list[str], command_summary: str) -> dict:
    return {
        'attempt': attempt,
        'project_dir': str(project_dir),
        'project_id': project_dir.name,
        'cwd': str(project_dir),
        'prompt_file': str(prompt_path),
        'output': str(output_path),
        'stdout_log': str(stdout_log),
        'stderr_log': str(stderr_log),
        'delivery_manifest': str(project_dir / 'delivery_manifest.json'),
        'resolved_references': refs,
        'missing_references': missing_refs,
        'command_summary': command_summary,
        'fallback_allowed': False,
        'error_category': '',
        'recommended_action': '',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Execute brand poster generation with preflight and structured result logging')
    parser.add_argument('--project-dir', required=True, help='Brand poster project directory')
    parser.add_argument('--size', required=True, help='Output size')
    parser.add_argument('--aspect', required=True, help='Output aspect ratio')
    parser.add_argument('--model', default='gpt-image-2', help='Image model')
    parser.add_argument('--count', type=int, default=1, help='Number of poster variants to generate in parallel via gpt-image2-gen (1-10)')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    log_dir = project_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    manager = ProjectManager(project_dir)

    result_path = project_dir / 'generation_result.json'
    prompt_path = project_dir / 'prompt_draft.md'
    output_path = project_dir / 'images' / 'final_poster.png'
    brief_path = project_dir / 'brief.json'
    ref_order_path = project_dir / 'ref_order.json'

    attempt = next_attempt(log_dir)
    manager.start_stage('generation', reason='执行海报生图脚本', actor='execute_generation.py', attempt=attempt)
    stdout_log = log_dir / f'generate.attempt-{attempt:02d}.stdout.log'
    stderr_log = log_dir / f'generate.attempt-{attempt:02d}.stderr.log'
    started_at = utc_now()

    if not TARGET_SCRIPT.exists():
        base = make_base_result(project_dir, attempt, prompt_path, output_path, stdout_log, stderr_log, [], [], '')
        base.update({
            'status': 'failed',
            'phase': 'preflight_failed',
            'ok': False,
            'exit_code': 1,
            'exists': False,
            'size': 0,
            'started_at': started_at,
            'finished_at': utc_now(),
            'duration_seconds': 0,
            'error': f'generator not found: {TARGET_SCRIPT}',
            'error_category': 'generator_missing',
            'recommended_action': '修复正式生图脚本路径后重试，不要改走本地拼图。',
        })
        write_json(result_path, base)
        manager.fail_stage(
            'generation',
            error=base['error'],
            actor='execute_generation.py',
            manifest_payload=base,
            files=[manager._relative(result_path)],
        )
        print(base['error'], file=sys.stderr)
        return 1

    brief = load_json(brief_path)
    ref_order_data = load_json(ref_order_path)
    errors, resolved_refs, missing_refs, required_files = validate_preflight(project_dir, brief, ref_order_data)
    count = max(1, min(int(args.count or 1), 10))
    cmd = build_command(prompt_path, output_path, resolved_refs, args.size, args.aspect, args.model, count=count) if not errors else []
    command_summary = summarize_command(cmd) if cmd else ''
    generation_env = build_generation_env(brief)

    started_payload = make_base_result(project_dir, attempt, prompt_path, output_path, stdout_log, stderr_log, resolved_refs, missing_refs, command_summary)
    started_payload.update({
        'status': 'started',
        'phase': 'running',
        'ok': False,
        'exit_code': None,
        'exists': output_path.exists(),
        'size': output_path.stat().st_size if output_path.exists() else 0,
        'started_at': started_at,
        'finished_at': None,
        'duration_seconds': None,
        'required_files': required_files,
        'error': '',
        'provider_mode_requested': generation_env.get('BANANA_PROVIDER_MODE', ''),
        'count': count,
    })
    write_json(result_path, started_payload)

    if errors:
        finished_at = utc_now()
        payload = dict(started_payload)
        payload.update({
            'status': 'failed',
            'phase': 'preflight_failed',
            'finished_at': finished_at,
            'duration_seconds': round(time.time() - datetime.fromisoformat(started_at.replace('Z', '+00:00')).timestamp(), 3),
            'exit_code': 1,
            'exists': output_path.exists(),
            'size': output_path.stat().st_size if output_path.exists() else 0,
            'error': '\n'.join(errors),
            'error_category': 'preflight_failed',
            'recommended_action': '补齐缺失文件或修复参考图冲突后，重新运行正式生图。',
        })
        write_json(result_path, payload)
        manager.fail_stage(
            'generation',
            error=payload['error'],
            actor='execute_generation.py',
            manifest_payload=payload,
            files=[manager._relative(result_path)],
            extra={'required_files': required_files},
        )
        print(payload['error'], file=sys.stderr)
        return 1

    start_ts = time.time()
    with stdout_log.open('w', encoding='utf-8') as stdout_f, stderr_log.open('w', encoding='utf-8') as stderr_f:
        proc = subprocess.run(cmd, cwd=str(project_dir), stdout=stdout_f, stderr=stderr_f, env=generation_env)

    exists = output_path.exists()
    size = output_path.stat().st_size if exists else 0
    output_paths = [output_path] + [
        output_path.with_name(f'{output_path.stem}_{idx}{output_path.suffix}')
        for idx in range(2, count + 1)
    ]
    existing_output_paths = [str(path) for path in output_paths if path.exists() and path.stat().st_size > 0]
    stderr_tail = tail_text(stderr_log)
    finished_at = utc_now()
    payload = dict(started_payload)
    payload.update({
        'finished_at': finished_at,
        'duration_seconds': round(time.time() - start_ts, 3),
        'exit_code': proc.returncode,
        'exists': exists,
        'size': size,
        'output_paths': existing_output_paths,
        'error': stderr_tail,
    })

    if proc.returncode != 0:
        error_category = classify_generation_error(stderr_tail)
        payload.update({
            'status': 'failed',
            'phase': 'generate_failed',
            'ok': False,
            'error_category': error_category,
            'recommended_action': recommended_action_for_error(error_category),
        })
        write_json(result_path, payload)
        manager.fail_stage(
            'generation',
            error=stderr_tail or f'生图命令执行失败，退出码 {proc.returncode}',
            actor='execute_generation.py',
            manifest_payload=payload,
            files=[manager._relative(result_path), manager._relative(stdout_log), manager._relative(stderr_log)],
            extra={'exit_code': proc.returncode},
        )
        return proc.returncode or 1

    if not exists or size <= 0 or len(existing_output_paths) < count:
        missing_outputs = [str(path) for path in output_paths if not path.exists() or path.stat().st_size <= 0]
        payload.update({
            'status': 'failed',
            'phase': 'postcheck_failed',
            'ok': False,
            'error': stderr_tail or f'输出文件缺失或为空: {", ".join(missing_outputs)}',
            'error_category': 'postcheck_failed',
            'recommended_action': '确认正式生图输出文件已生成且非空后再继续交付，不要改走本地拼图。',
        })
        write_json(result_path, payload)
        manager.fail_stage(
            'generation',
            error=payload['error'],
            actor='execute_generation.py',
            manifest_payload=payload,
            files=[manager._relative(result_path), manager._relative(stdout_log), manager._relative(stderr_log)],
        )
        return 1

    payload.update({
        'status': 'succeeded',
        'phase': 'generated',
        'generation_status': 'generated',
        'delivery_status': 'not_attempted',
        'ok': True,
        'output_paths': existing_output_paths,
    })
    write_json(result_path, payload)
    manager.complete_stage(
        'generation',
        reason='海报已生成成功，下一步可进入交付准备。',
        actor='execute_generation.py',
        manifest_payload=payload,
        flags={'generation_ready': True},
        artifacts={'generation': str(result_path)},
        files=[manager._relative(result_path), manager._relative(stdout_log), manager._relative(stderr_log), manager._relative(output_path)],
        extra={'output_size': size, 'exit_code': proc.returncode},
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
