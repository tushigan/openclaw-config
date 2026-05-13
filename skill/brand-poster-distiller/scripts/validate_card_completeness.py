#!/usr/bin/env python3
"""Validate v3 card completeness."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_TOP = ['id', 'title', 'subtitle', 'summary', 'tags', 'distill_version', 'source_images', 'layout_analysis']
REQUIRED_LAYOUT = ['status', 'skeleton_image', 'elements']


def main():
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    files = [target] if target else sorted((ROOT / 'cards').glob('POSTER-DISTILL-P-*.json'))
    failed = False
    for path in files:
        card = json.loads(path.read_text(encoding="utf-8"))
        missing = []
        for key in REQUIRED_TOP:
            if key not in card or card.get(key) in ({}, [], '', None):
                missing.append(key)
        la = card.get('layout_analysis', {}) or {}
        for key in REQUIRED_LAYOUT:
            if key not in la or la.get(key) in ({}, [], None):
                missing.append(f'layout_analysis.{key}')
        if missing:
            failed = True
            print(json.dumps({'ok': False, 'card': str(path), 'missing': missing}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({'ok': True, 'card': str(path), 'elements': len(la.get('elements', []))}, ensure_ascii=False))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
