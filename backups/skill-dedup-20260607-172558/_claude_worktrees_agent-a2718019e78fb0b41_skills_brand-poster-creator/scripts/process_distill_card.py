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

DISTILLER_CARDS_DIR = Path('/Users/a123/.openclaw/workspace/skills/brand-poster-distiller/cards')
DISTILLER_ROOT = Path('/Users/a123/.openclaw/workspace/skills/brand-poster-distiller')


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def resolve_card_path(distill_id: str) -> Path:
    return DISTILLER_CARDS_DIR / f'{distill_id}.json'


def resolve_asset(raw_path: str, card_path: Path) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    card_relative = (card_path.parent / raw_path).resolve()
    if card_relative.exists():
        return card_relative
    distiller_relative = (DISTILLER_ROOT / raw_path).resolve()
    if distiller_relative.exists():
        return distiller_relative
    return None


def copy_skeleton(distill_data: dict, card_path: Path, project_dir: Path) -> tuple[str, str]:
    layout = distill_data.get('layout_analysis', {}) or {}
    skeleton_png = str(layout.get('skeleton_png', '') or '').strip()
    skeleton_svg = str(layout.get('skeleton_image', '') or '').strip()
    source_path = resolve_asset(skeleton_png, card_path) if skeleton_png else None
    used_field = 'skeleton_png'
    if source_path is None and skeleton_svg:
        source_path = resolve_asset(skeleton_svg, card_path)
        used_field = 'skeleton_image'
    if source_path is None:
        return '', used_field

    ext = source_path.suffix.lower() or '.png'
    target_name = 'skeleton.png' if ext == '.png' else f'skeleton{ext}'
    target_path = project_dir / 'images' / target_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    return str(target_path), used_field


def main() -> int:
    parser = argparse.ArgumentParser(description='处理品牌海报蒸馏卡并写入项目状态')
    parser.add_argument('--project-dir', required=True, help='项目目录绝对路径')
    parser.add_argument('--brief', default='', help='brief.json 路径，默认取项目目录下 brief.json')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    brief_path = Path(args.brief).resolve() if args.brief else project_dir / 'brief.json'
    manager = ProjectManager(project_dir)
    attempt = manager.start_stage('distill', reason='检查蒸馏卡并同步版式约束', actor='process_distill_card.py')

    if not brief_path.exists():
        error = f'brief.json 不存在: {brief_path}'
        manager.fail_stage(
            'distill',
            error=error,
            actor='process_distill_card.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'brief_path': str(brief_path),
                'error_summary': error,
                'user_confirmed': False,
                'history': [{'event': 'distill_failed', 'reason': error}],
            },
            files=['distill_manifest.json'],
        )
        print(f'ERROR: {error}')
        return 1

    brief = load_json(brief_path)
    distill_id = str(brief.get('distill_card_id', '') or '').strip()
    distill_output_path = project_dir / 'distill_card.json'

    if not distill_id:
        brief['distill_mode'] = 'fallback'
        write_json(brief_path, brief)
        manager.skip_stage(
            'distill',
            reason='未提供蒸馏卡 ID，已切换到 fallback 模式。',
            actor='process_distill_card.py',
            manifest_payload={
                'status': 'skipped',
                'attempt': attempt,
                'brief_path': str(brief_path),
                'distill_mode': 'fallback',
                'distill_card_id': '',
                'user_confirmed': False,
                'history': [{'event': 'distill_fallback', 'reason': 'missing_distill_id'}],
            },
            flags={'distill_fallback': True, 'distill_available': False},
            artifacts={'brief': str(brief_path)},
            files=[manager._relative(brief_path)],
        )
        print('OK: 未提供蒸馏卡 ID，已标记 fallback 模式')
        return 0

    card_path = resolve_card_path(distill_id)
    if not card_path.exists():
        error = f'蒸馏卡不存在: {card_path}'
        manager.fail_stage(
            'distill',
            error=error,
            actor='process_distill_card.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'brief_path': str(brief_path),
                'distill_card_id': distill_id,
                'card_path': str(card_path),
                'error_summary': error,
                'user_confirmed': False,
                'history': [{'event': 'distill_failed', 'reason': error}],
            },
            files=['distill_manifest.json'],
        )
        print(f'ERROR: {error}')
        return 1

    distill_data = load_json(card_path)
    write_json(distill_output_path, distill_data)
    skeleton_path, skeleton_source_field = copy_skeleton(distill_data, card_path, project_dir)
    layout = distill_data.get('layout_analysis', {}) or {}
    element_count = len(layout.get('elements', []) or [])
    negative_count = len(layout.get('negative_constraints', []) or [])
    copy_guide = str(layout.get('copy_planning_guide', '') or '').strip()

    manager.complete_stage(
        'distill',
        reason='蒸馏卡已同步到项目目录。',
        actor='process_distill_card.py',
        manifest_payload={
            'status': 'ready',
            'attempt': attempt,
            'brief_path': str(brief_path),
            'distill_card_id': distill_id,
            'card_path': str(card_path),
            'distill_output_path': str(distill_output_path),
            'skeleton_path': skeleton_path,
            'skeleton_source_field': skeleton_source_field,
            'element_count': element_count,
            'negative_constraints_count': negative_count,
            'copy_planning_guide_present': bool(copy_guide),
            'user_confirmed': False,
            'history': [{'event': 'distill_ready', 'distill_card_id': distill_id}],
        },
        flags={'distill_available': True, 'distill_fallback': False},
        artifacts={'distill': str(distill_output_path), 'brief': str(brief_path)},
        files=[manager._relative(distill_output_path)] + ([manager._relative(skeleton_path)] if skeleton_path else []),
        extra={'distill_card_id': distill_id, 'element_count': element_count},
    )

    print(f'OK: distill_card 已写入 {distill_output_path}')
    print(f'  distill_id: {distill_id}')
    print(f'  elements: {element_count}')
    print(f'  negative_constraints: {negative_count}')
    if skeleton_path:
        print(f'  skeleton: {skeleton_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
