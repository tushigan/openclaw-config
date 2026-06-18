#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def normalize_copywriting(data: dict) -> dict:
    if not isinstance(data, dict):
        return {}
    normalized: dict[str, dict[str, str]] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        text = str(value.get('文案', '') or value.get('text', '') or '').strip()
        font = str(value.get('字体风格', '') or value.get('font_style', '') or '').strip()
        if not text:
            continue
        normalized[str(key)] = {
            '文案': text,
            '字体风格': font,
        }
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description='处理品牌海报文案并写入项目状态')
    parser.add_argument('--project-dir', required=True, help='项目目录绝对路径')
    parser.add_argument('--source', default='', help='文案来源文件，默认使用项目目录下 copywriting.json')
    parser.add_argument('--output', default='', help='文案输出文件，默认使用项目目录下 copywriting.json')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    source_path = Path(args.source).resolve() if args.source else project_dir / 'copywriting.json'
    output_path = Path(args.output).resolve() if args.output else project_dir / 'copywriting.json'
    manager = ProjectManager(project_dir)
    attempt = manager.start_stage('copywriting', reason='处理文案策划结果', actor='process_copywriting.py')

    payload = load_json(source_path)
    if not payload:
        error = f'文案文件不存在或为空: {source_path}'
        manager.fail_stage(
            'copywriting',
            error=error,
            actor='process_copywriting.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'source_path': str(source_path),
                'output_path': str(output_path),
                'error_summary': error,
                'user_confirmed': False,
                'history': [{'event': 'copywriting_failed', 'reason': error}],
            },
            files=['copywriting_manifest.json'],
        )
        print(f'ERROR: {error}')
        return 1

    normalized = normalize_copywriting(payload)
    if not normalized:
        error = f'文案文件格式无效: {source_path}'
        manager.fail_stage(
            'copywriting',
            error=error,
            actor='process_copywriting.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'source_path': str(source_path),
                'output_path': str(output_path),
                'error_summary': error,
                'user_confirmed': False,
                'history': [{'event': 'copywriting_failed', 'reason': error}],
            },
            files=['copywriting_manifest.json'],
        )
        print(f'ERROR: {error}')
        return 1

    if source_path != output_path:
        write_json(output_path, normalized)
    else:
        write_json(output_path, normalized)

    area_count = len(normalized)
    text_count = sum(1 for item in normalized.values() if str(item.get('文案', '')).strip())

    manager.complete_stage(
        'copywriting',
        reason='文案策划已落盘，可进入风格提炼或创意表达。',
        actor='process_copywriting.py',
        manifest_payload={
            'status': 'ready',
            'attempt': attempt,
            'source_path': str(source_path),
            'output_path': str(output_path),
            'area_count': area_count,
            'text_count': text_count,
            'user_confirmed': False,
            'history': [{'event': 'copywriting_ready', 'area_count': area_count}],
        },
        flags={'copywriting_ready': True, 'copy_confirmed': False},
        artifacts={'copywriting': str(output_path)},
        files=[manager._relative(output_path)],
        extra={'area_count': area_count, 'text_count': text_count},
    )

    print(f'OK: copywriting 已写入 {output_path}')
    print(f'  区域数: {area_count}')
    print(f'  文案条数: {text_count}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
