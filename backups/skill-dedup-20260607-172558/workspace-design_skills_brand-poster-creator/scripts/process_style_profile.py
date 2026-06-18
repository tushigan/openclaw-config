#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager

REQUIRED_TEXT_FIELDS = [
    'overall_mood',
    'background',
    'decorative',
    'main_visual_style',
    'season_override_hint',
]
REQUIRED_LIST_FIELDS = [
    'color',
    'mood',
    'material',
    'avoid',
    'content_do_not_inherit',
]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def existing_files(project_dir: Path, raw_value) -> list[str]:
    values = raw_value if isinstance(raw_value, list) else [raw_value]
    found: list[str] = []
    for item in values:
        path_text = str(item or '').strip()
        if not path_text:
            continue
        path = Path(path_text)
        full = path if path.is_absolute() else project_dir / path
        if full.exists() and full.stat().st_size > 0:
            found.append(str(path if not path.is_absolute() else full))
    return found


def normalize_style_profile(data: dict) -> dict:
    if not isinstance(data, dict):
        return {}
    normalized: dict[str, object] = {}
    for field in REQUIRED_TEXT_FIELDS:
        normalized[field] = str(data.get(field, '') or '').strip()
    for field in REQUIRED_LIST_FIELDS:
        value = data.get(field) or []
        if isinstance(value, str):
            items = [value.strip()] if value.strip() else []
        else:
            items = [str(item).strip() for item in value if str(item).strip()]
        normalized[field] = items
    return normalized


def validate_style_profile(payload: dict) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_TEXT_FIELDS:
        if not str(payload.get(field, '') or '').strip():
            issues.append(f'缺少字段: {field}')
    for field in REQUIRED_LIST_FIELDS:
        value = payload.get(field)
        if not isinstance(value, list) or not any(str(item).strip() for item in value):
            issues.append(f'字段必须为非空数组: {field}')
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description='处理品牌海报风格提炼结果并写入项目状态')
    parser.add_argument('--project-dir', required=True, help='项目目录绝对路径')
    parser.add_argument('--brief', default='', help='brief.json 路径，默认取项目目录下 brief.json')
    parser.add_argument('--source', default='', help='风格提炼来源文件，默认取项目目录下 style_profile.json')
    parser.add_argument('--output', default='', help='风格提炼输出文件，默认取项目目录下 style_profile.json')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    brief_path = Path(args.brief).resolve() if args.brief else project_dir / 'brief.json'
    source_path = Path(args.source).resolve() if args.source else project_dir / 'style_profile.json'
    output_path = Path(args.output).resolve() if args.output else project_dir / 'style_profile.json'

    manager = ProjectManager(project_dir)
    attempt = manager.start_stage('style_profile', reason='处理风格提炼结果', actor='process_style_profile.py')

    brief = load_json(brief_path)
    if not brief:
        error = f'brief.json 不存在或为空: {brief_path}'
        manager.fail_stage(
            'style_profile',
            error=error,
            actor='process_style_profile.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'brief_path': str(brief_path),
                'source_path': str(source_path),
                'output_path': str(output_path),
                'error_summary': error,
                'user_confirmed': False,
                'history': [{'event': 'style_profile_failed', 'reason': error}],
            },
            files=['style_profile_manifest.json'],
        )
        print(f'ERROR: {error}')
        return 1

    assets = brief.get('assets', {}) or {}
    style_refs = existing_files(project_dir, assets.get('style_refs', []))
    if not style_refs:
        manager.skip_stage(
            'style_profile',
            reason='未提供有效风格参考图，跳过风格提炼。',
            actor='process_style_profile.py',
            manifest_payload={
                'status': 'skipped',
                'attempt': attempt,
                'brief_path': str(brief_path),
                'source_path': str(source_path),
                'output_path': str(output_path),
                'style_ref_count': 0,
                'style_refs': [],
                'user_confirmed': False,
                'history': [{'event': 'style_profile_skipped', 'reason': 'missing_style_refs'}],
            },
            flags={'style_profile_ready': False},
            files=['style_profile_manifest.json'],
            extra={'style_ref_count': 0},
        )
        print('OK: 未提供有效风格参考图，已跳过 style_profile 阶段')
        return 0

    source_payload = load_json(source_path)
    if not source_payload:
        error = f'已提供风格参考图，但缺少 style_profile.json: {source_path}'
        manager.fail_stage(
            'style_profile',
            error=error,
            actor='process_style_profile.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'brief_path': str(brief_path),
                'source_path': str(source_path),
                'output_path': str(output_path),
                'style_ref_count': len(style_refs),
                'style_refs': style_refs,
                'error_summary': error,
                'user_confirmed': False,
                'history': [{'event': 'style_profile_failed', 'reason': error}],
            },
            files=['style_profile_manifest.json'],
        )
        print(f'ERROR: {error}')
        return 1

    normalized = normalize_style_profile(source_payload)
    issues = validate_style_profile(normalized)
    if issues:
        error = '；'.join(issues)
        manager.fail_stage(
            'style_profile',
            error=error,
            actor='process_style_profile.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'brief_path': str(brief_path),
                'source_path': str(source_path),
                'output_path': str(output_path),
                'style_ref_count': len(style_refs),
                'style_refs': style_refs,
                'error_summary': error,
                'user_confirmed': False,
                'history': [{'event': 'style_profile_failed', 'reason': error}],
            },
            files=['style_profile_manifest.json'],
            extra={'issues': issues},
        )
        print('ERROR: style_profile 校验失败')
        for issue in issues:
            print(f'  - {issue}')
        return 1

    write_json(output_path, normalized)
    manager.complete_stage(
        'style_profile',
        reason='风格提炼结果已落盘，可继续创意表达。',
        actor='process_style_profile.py',
        manifest_payload={
            'status': 'ready',
            'attempt': attempt,
            'brief_path': str(brief_path),
            'source_path': str(source_path),
            'output_path': str(output_path),
            'style_ref_count': len(style_refs),
            'style_refs': style_refs,
            'required_text_fields': REQUIRED_TEXT_FIELDS,
            'required_list_fields': REQUIRED_LIST_FIELDS,
            'user_confirmed': False,
            'history': [{'event': 'style_profile_ready', 'style_ref_count': len(style_refs)}],
        },
        flags={'style_profile_ready': True},
        artifacts={'style_profile': str(output_path)},
        files=[manager._relative(output_path)],
        extra={'style_ref_count': len(style_refs)},
    )

    print(f'OK: style_profile 已写入 {output_path}')
    print(f'  风格参考图: {len(style_refs)} 张')
    return 0


if __name__ == '__main__':
    sys.exit(main())
