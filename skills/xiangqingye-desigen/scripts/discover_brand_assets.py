#!/usr/bin/env python3
"""按品牌名生成项目级品牌资产候选清单。"""

import argparse
import json
from datetime import datetime
from pathlib import Path

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
ROLE_PATTERNS = {
    'brand_logo': ['品牌logo', '品牌_logo', 'logo', '标志'],
    'brand_ip': ['ip', '吉祥物', '卡通', '形象'],
    'product_main': ['产品图', 'product', '主图', '商品图'],
    'product_detail': ['细节', 'detail', '局部'],
    'packaging': ['包装', 'packaging', '盒', '袋'],
    'style_reference': ['风格', 'style', '参考', 'reference'],
}


def guess_role(path: Path) -> tuple[str, str]:
    name = path.stem.lower()
    for role, patterns in ROLE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in name:
                return role, f'文件名包含关键词: {pattern}'
    return 'reference_other', '未命中文件名角色规则'


def build_candidates(project_dir: Path, brand: str, source_dir: Path) -> list[dict]:
    candidates = []
    if not source_dir.exists():
        return candidates

    brand_lower = brand.lower()
    for path in sorted(source_dir.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        role, reason = guess_role(path)
        rel = str(path.relative_to(source_dir))
        matched = brand_lower in rel.lower() or brand_lower in path.stem.lower()
        candidates.append({
            'candidate_id': f'asset_{len(candidates) + 1}',
            'brand': brand,
            'source': 'local_brand_asset_library',
            'source_dir': str(source_dir),
            'role': role,
            'path': str(path),
            'relative_path': rel,
            'file_name': path.name,
            'match_reason': reason if matched else f'{reason}；来源目录人工指定为品牌资产库',
            'confirmed': False,
        })
    return candidates


def main():
    parser = argparse.ArgumentParser(description='生成项目级品牌资产候选清单')
    parser.add_argument('--project-dir', required=True, help='项目目录')
    parser.add_argument('--brand', required=True, help='品牌名')
    parser.add_argument('--source-dir', required=True, help='品牌资产来源目录（本地同步目录）')
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    source_dir = Path(args.source_dir)
    if not project_dir.exists():
        raise SystemExit(f'项目目录不存在: {project_dir}')

    candidates = build_candidates(project_dir, args.brand, source_dir)
    output_dir = project_dir / '参考'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'brand_asset_candidates.json'
    payload = {
        'project': project_dir.name,
        'brand': args.brand,
        'generated_at': datetime.now().isoformat(),
        'source_dir': str(source_dir),
        'candidates': candidates,
        'message': '候选资产仅供确认，未确认前不得写入 asset_registry.json。',
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(output_path)
    print(f'candidates={len(candidates)}')


if __name__ == '__main__':
    main()
