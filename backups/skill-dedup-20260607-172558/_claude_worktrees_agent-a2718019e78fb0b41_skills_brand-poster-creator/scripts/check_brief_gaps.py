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

REQUIRED_BASE_FIELDS = ['brand_name', 'festival', 'ratio']
REQUIRED_PRODUCT_FIELDS = ['product_name']


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def file_exists(project_dir: Path, relative_path: str) -> bool:
    if not relative_path:
        return False
    path = Path(relative_path)
    if path.is_absolute():
        return path.exists() and path.stat().st_size > 0
    full = project_dir / relative_path
    return full.exists() and full.stat().st_size > 0


def collect_gaps(brief: dict, project_dir: Path) -> list[str]:
    gaps: list[str] = []
    assets = brief.get('assets', {}) or {}
    poster_type = str(brief.get('type', '') or '').strip()
    style_note = str(brief.get('style_note', '') or '').strip()

    for field in REQUIRED_BASE_FIELDS:
        if not str(brief.get(field, '') or '').strip():
            label = {
                'brand_name': '品牌名称',
                'festival': '营销节点',
                'ratio': '尺寸比例',
            }[field]
            gaps.append(label)

    if not file_exists(project_dir, str(assets.get('logo', '') or '')):
        gaps.append('Logo')

    style_refs = assets.get('style_refs', []) or []
    has_style_ref = any(file_exists(project_dir, str(item or '')) for item in style_refs) if isinstance(style_refs, list) else file_exists(project_dir, str(style_refs or ''))
    if not has_style_ref and not style_note:
        gaps.append('风格参考')

    is_product_promo = '产品' in poster_type or '推广' in poster_type
    if is_product_promo:
        for field in REQUIRED_PRODUCT_FIELDS:
            if not str(brief.get(field, '') or '').strip():
                label = {'product_name': '产品名称'}[field]
                gaps.append(label)
        product_sell_points = brief.get('product_sell_points') or brief.get('selling_points') or brief.get('product_points') or []
        if isinstance(product_sell_points, str):
            has_sell_points = bool(product_sell_points.strip())
        else:
            has_sell_points = any(str(item).strip() for item in product_sell_points)
        if not has_sell_points:
            gaps.append('产品卖点')
        if not file_exists(project_dir, str(assets.get('product', '') or '')):
            gaps.append('产品图')

    deduped = []
    for item in gaps:
        if item not in deduped:
            deduped.append(item)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(description='检查品牌海报需求缺口并写入项目状态')
    parser.add_argument('--project-dir', required=True, help='项目目录绝对路径')
    parser.add_argument('--brief', default='', help='brief.json 路径，默认取项目目录下 brief.json')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    brief_path = Path(args.brief).resolve() if args.brief else project_dir / 'brief.json'
    manager = ProjectManager(project_dir)
    attempt = manager.start_stage('gap_check', reason='检查当前需求与素材缺口', actor='check_brief_gaps.py')

    if not brief_path.exists():
        error = f'brief.json 不存在: {brief_path}'
        manager.fail_stage(
            'gap_check',
            error=error,
            actor='check_brief_gaps.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'brief_path': str(brief_path),
                'error_summary': error,
                'user_confirmed': False,
                'history': [{'event': 'gap_check_failed', 'reason': error}],
            },
            files=['gap_check_manifest.json'],
        )
        print(f'ERROR: {error}')
        return 1

    brief = load_json(brief_path)
    gaps = collect_gaps(brief, project_dir)

    manifest = {
        'status': 'complete' if not gaps else 'gaps_found',
        'attempt': attempt,
        'brief_path': str(brief_path),
        'gaps': gaps,
        'gap_count': len(gaps),
        'poster_type': str(brief.get('type', '') or ''),
        'brand_name': str(brief.get('brand_name', '') or ''),
        'festival': str(brief.get('festival', '') or ''),
        'user_confirmed': False,
        'history': [{'event': 'gap_check_completed', 'gap_count': len(gaps)}],
    }

    manager.complete_stage(
        'gap_check',
        reason='信息缺口检查已完成。' if not gaps else f'发现 {len(gaps)} 项信息缺口。',
        actor='check_brief_gaps.py',
        manifest_payload=manifest,
        flags={'gap_check_completed': True},
        artifacts={'brief': str(brief_path)},
        files=['gap_check_manifest.json'],
        extra={'gaps': gaps},
    )

    print(json.dumps({'gap_count': len(gaps), 'gaps': gaps}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
