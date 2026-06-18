#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager

KEEP_ROOT_FILES = {
    'brief.json',
    'copywriting.json',
    'generation_result.json',
    'delivery_manifest.json',
    'cleanup_manifest.json',
    'project_state.json',
    'audit_log.jsonl',
}
KEEP_IMAGE_FILES = {'final_poster.png'}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def run_trash(path: Path) -> None:
    subprocess.run(['trash', str(path)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description='清理品牌海报项目中间文件并写入状态')
    parser.add_argument('--project-dir', required=True, help='项目目录绝对路径')
    parser.add_argument('--confirmed', action='store_true', help='确认执行清理')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    manager = ProjectManager(project_dir)
    attempt = manager.start_stage('cleanup', reason='清理项目中间文件', actor='cleanup_project.py')

    if not args.confirmed:
        error = '未传入 --confirmed，拒绝执行清理。'
        manager.fail_stage(
            'cleanup',
            error=error,
            actor='cleanup_project.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'error_summary': error,
                'removed_files': [],
                'kept_files': [],
                'history': [{'event': 'cleanup_failed', 'reason': error}],
            },
            files=['cleanup_manifest.json'],
        )
        print(f'ERROR: {error}')
        return 1

    delivery_manifest_path = project_dir / 'delivery_manifest.json'
    delivery_manifest = load_json(delivery_manifest_path) if delivery_manifest_path.exists() else {}

    removed_files: list[str] = []
    kept_files: list[str] = []

    for path in sorted(project_dir.rglob('*')):
        if path.is_dir():
            continue
        rel = path.relative_to(project_dir).as_posix()
        if rel in KEEP_ROOT_FILES:
            kept_files.append(rel)
            continue
        if path.parent.name == 'images' and path.name in KEEP_IMAGE_FILES:
            kept_files.append(rel)
            continue
        if rel.startswith('logs/'):
            run_trash(path)
            removed_files.append(rel)
            continue
        if path.parent.name == 'images':
            run_trash(path)
            removed_files.append(rel)
            continue
        if path.name in {'prompt_draft.md', 'distill_card.json', 'creative_direction.json', 'style_profile.json', 'ref_order.json', 'creative_direction_manifest.json', 'prompt_manifest.json', 'distill_manifest.json', 'gap_check_manifest.json', 'style_profile_manifest.json'}:
            run_trash(path)
            removed_files.append(rel)
            continue
        kept_files.append(rel)

    manifest = {
        'status': 'completed',
        'attempt': attempt,
        'removed_files': removed_files,
        'kept_files': kept_files,
        'delivery_manifest_path': str(delivery_manifest_path) if delivery_manifest_path.exists() else '',
        'delivery_mode': delivery_manifest.get('delivery_mode', ''),
        'original_copy_path': (((delivery_manifest.get('deliverables') or {}).get('original_copy') or {}).get('path') or ''),
        'original_zip_path': (((delivery_manifest.get('deliverables') or {}).get('original_zip') or {}).get('path') or ''),
        'history': [{'event': 'cleanup_completed', 'removed_count': len(removed_files)}],
    }

    manager.complete_stage(
        'cleanup',
        reason=f'已清理 {len(removed_files)} 个中间文件。',
        actor='cleanup_project.py',
        manifest_payload=manifest,
        flags={'cleanup_ready': True},
        artifacts={'cleanup': str(project_dir / 'cleanup_manifest.json')},
        files=['cleanup_manifest.json'] + removed_files,
        extra={'removed_count': len(removed_files)},
    )

    print(json.dumps({'removed_files': removed_files, 'kept_files': kept_files}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
