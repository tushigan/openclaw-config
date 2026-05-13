#!/usr/bin/env python3
"""Migrate all cards from v2 to v3 layout-only format."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

KEEP_TOP = {'id', 'slug', 'title', 'subtitle', 'status', 'thumb', 'tags', 'summary',
            'source_images', 'distill_version', 'layout_analysis'}
V2_CLEANUP = {
    'source_asset_register', 'poster_object', 'one_line_judgment',
    'most_valuable_takeaway', 'can_take_directly', 'should_not_copy_directly',
    'can_take_after_adaptation', 'evidence_still_insufficient', 'scores',
    'distillation_target', 'anti_drift_constraints', 'generation_strategy',
    'handoff', 'how_to_use', 'distill_version', 'style_design_lock',
    'element_lock_strategy', 'next_stage_prompt_injection', 'layout_analysis',
}


def migrate_card(card_path: Path):
    card = json.loads(card_path.read_text(encoding='utf-8'))
    clean = {k: v for k, v in card.items() if k in KEEP_TOP}
    if 'source_images' not in clean:
        sar = card.get('source_asset_register', {})
        clean['source_images'] = sar.get('original_reference_images', []) if sar else []
    clean['distill_version'] = 'v3'
    la = card.get('layout_analysis', {})
    if la and la.get('status') == 'ready':
        clean['layout_analysis'] = la
    else:
        clean['layout_analysis'] = {
            'status': 'pending',
            'analyzed_at': '',
            'analyzer_model': '',
            'skeleton_image': '',
            'elements': [],
            'notes': '',
        }
    card_path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding='utf-8')
    el_count = len(clean['layout_analysis'].get('elements', []))
    status = clean['layout_analysis'].get('status', 'pending')
    print(f'  OK   {clean["id"]}: status={status}, elements={el_count}')


def main():
    cards_dir = ROOT / 'cards'
    if not cards_dir.exists():
        print(f'Cards directory not found: {cards_dir}')
        sys.exit(1)
    files = sorted(cards_dir.glob('POSTER-DISTILL-P-*.json'))
    if not files:
        print('No cards to migrate')
        sys.exit(0)
    print(f'Migrating {len(files)} cards to v3...')
    failed = []
    for f in files:
        try:
            migrate_card(f)
        except Exception as e:
            print(f'  FAIL {f.name}: {e}')
            failed.append(str(f))
    if failed:
        print(f'\n{len(failed)} failed')
        sys.exit(1)
    print('Done')


if __name__ == '__main__':
    main()
