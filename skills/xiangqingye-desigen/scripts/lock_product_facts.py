#!/usr/bin/env python3
"""Lock product facts into a structured JSON for downstream generation.

Usage:
  python lock_product_facts.py --output facts.json \
    --brand "卡宾熊" \
    --product "法式可丽饼" \
    --structure "clamped" \
    --layers 3 \
    --flavors "浓郁巧克力味,玫瑰盐芝士味,蓝莓酸奶味,焦糖咖啡味,抹茶芝士味" \
    --emboss "bear_face" \
    --packaging-required true

The output JSON is designed to be injected into every image generation prompt
as a preamble, ensuring consistent product representation across all segments.
"""
import json
import argparse
from pathlib import Path


# Valid values for structured fields
STRUCTURE_OPTIONS = {
    'solid': '实心（无夹心）',
    'clamped': '夹心（上下层+中间夹酱）',
    'hollow': '空心（如口袋面包）',
    'coated': '涂层（表面有巧克力/糖衣等）',
    'filled': '注心（如注心饼干）',
    'molten': '流心（切面有流心效果）',
}

EMBOSS_OPTIONS = {
    'none': '无压纹',
    'bear_face': '熊脸压纹',
    'brand_logo': '品牌 LOGO 压纹',
    'pattern': '花纹/几何压纹',
}


def parse_flavors(raw: str) -> list:
    """Parse comma-separated flavor names, strip whitespace."""
    return [f.strip() for f in raw.split(',') if f.strip()]


def main():
    ap = argparse.ArgumentParser(description='Lock product facts into JSON')
    ap.add_argument('--output', required=True, help='Output JSON file path')

    # Basic product info
    ap.add_argument('--brand', default='', help='Brand name')
    ap.add_argument('--product', default='', help='Product name')
    ap.add_argument('--category', default='', help='Product category (e.g. 饼干/烘焙/零食)')

    # Structure facts (Step 3.5 hard lock)
    ap.add_argument('--structure', choices=list(STRUCTURE_OPTIONS.keys()),
                    help='Product structure type')
    ap.add_argument('--layers', type=int, default=0,
                    help='Number of visible layers (e.g. 3 for 上饼+夹酱+下饼)')
    ap.add_argument('--is-coated', action='store_true', help='Has surface coating')
    ap.add_argument('--is-molten', action='store_true', help='Has molten/flowing center')
    ap.add_argument('--cross-section-needed', action='store_true',
                    help='Whether cross-section view is required')

    # Flavor & exposure
    ap.add_argument('--flavors', default='',
                    help='Comma-separated flavor names')
    ap.add_argument('--main-flavor', default='',
                    help='The hero flavor being promoted')
    ap.add_argument('--flavors-separate', action='store_true',
                    help='Whether each flavor needs its own screen')

    # Brand assets
    ap.add_argument('--emboss', choices=list(EMBOSS_OPTIONS.keys()), default='none',
                    help='Product embossing pattern')
    ap.add_argument('--packaging-required', action='store_true',
                    help='Whether packaging must appear in the detail page')
    ap.add_argument('--logo-locked', action='store_true',
                    help='Whether the logo must be reproduced precisely (not redrawn)')

    # Additional constraints
    ap.add_argument('--avoid', default='',
                    help='Comma-separated things to avoid (e.g. 英文,占位框,注释线)')
    ap.add_argument('--style-note', default='',
                    help='Free-text style note for generation')

    args = ap.parse_args()

    facts = {
        'brand': args.brand,
        'product': args.product,
        'category': args.category,
        'structure': {
            'type': args.structure,
            'description': STRUCTURE_OPTIONS.get(args.structure, ''),
            'layers': args.layers,
            'is_coated': args.is_coated,
            'is_molten': args.is_molten,
            'cross_section_needed': args.cross_section_needed,
        },
        'flavors': parse_flavors(args.flavors),
        'main_flavor': args.main_flavor,
        'flavors_separate': args.flavors_separate,
        'emboss': {
            'type': args.emboss,
            'description': EMBOSS_OPTIONS.get(args.emboss, ''),
        },
        'packaging_required': args.packaging_required,
        'logo_locked': args.logo_locked,
        'avoid': [a.strip() for a in args.avoid.split(',') if a.strip()],
        'style_note': args.style_note,
        'typography_scale': {
            'headline': 'large, bold, primary page title style',
            'subtitle': 'medium weight, secondary section title',
            'body': 'regular weight, descriptive text',
            'label': 'small, tags and callouts',
            'rule': 'all segments must use the same relative size hierarchy',
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'Product facts locked to: {out}')
    print(json.dumps(facts, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
