#!/usr/bin/env python3
"""Generate a global style guide image for detail page consistency.

This creates a "style swatch card" that captures:
- Background treatment (gradient, texture, tone)
- Decorative motif style
- Color accent palette
- Overall mood and atmosphere

The style guide is generated ONCE before any segment generation,
then used as --ref-style for EVERY segment.

Usage:
  python generate_style_guide.py --facts facts.json \
    --ref-style user_style.png \
    --output images/style_guide.png
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


# Remove proxy env vars to avoid Clash TUN issues
for key in list(os.environ.keys()):
    if key.lower() in ('http_proxy', 'https_proxy', 'all_proxy',
                       'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'):
        os.environ.pop(key, None)


def build_prompt(facts: dict) -> str:
    """Build style guide generation prompt."""
    brand = facts.get('brand', '')
    product = facts.get('product', '')
    category = facts.get('category', '')

    prompt = f"""生成一张电商详情页风格指南色卡，仅用于风格参考，不包含具体产品内容或布局。

【整体要求】
- 这是一张风格参考图，不是产品页面
- 展示页面的背景处理方式、装饰元素风格、色彩体系
- 干净的设计手稿感，不是海报强 logo 压场

【背景处理】
- 干净简洁的背景
- 适合食品/烘焙/快消品类电商详情页
- 柔和的渐变或纯色调
- 不要太花哨，保持专业感

【装饰元素风格】
- 有机的柔和曲线或简洁的几何图案
- 适合食品类详情页的氛围
- 作为页面装饰而非主角

【色彩体系】
- 温暖、食欲友好的色调
- 2-3 个主色 + 1-2 个辅助色
- 色彩和谐，对比度适中

【产品背景】
- 品牌：{brand}
- 产品：{product}
- 类目：{category}

【禁止事项】
- 禁止英文文字
- 禁止具体产品图片或包装
- 禁止布局模块或 wireframe
- 禁止文字内容（这是纯风格参考）
"""
    return prompt


def generate_style_guide(facts_path: str, ref_styles: list, output_path: str,
                         size: str = '768x768'):
    """Generate style guide image using gpt-image2-gen."""
    facts = json.loads(Path(facts_path).read_text(encoding='utf-8'))
    prompt = build_prompt(facts)

    # Build command
    script_dir = Path(__file__).parent
    gen_script = script_dir.parent.parent / 'gpt-image2-gen' / 'scripts' / 'generate.py'

    cmd = [
        sys.executable, str(gen_script),
        '--prompt', prompt,
        '--size', size,
        '--output', output_path,
    ]

    for ref in ref_styles:
        cmd.extend(['--ref-style', ref])

    print(f'生成风格指南...')
    print(f'输出: {output_path}')

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'错误: {result.stderr}')
        sys.exit(1)

    print(f'风格指南已生成: {output_path}')
    return output_path


def main():
    ap = argparse.ArgumentParser(description='Generate detail page style guide')
    ap.add_argument('--facts', required=True, help='Product facts JSON file')
    ap.add_argument('--ref-style', action='append', default=[],
                    help='User-provided style reference images (repeatable)')
    ap.add_argument('--output', required=True, help='Output image path')
    ap.add_argument('--size', default='768x768',
                    help='Image size (default 768x768)')

    args = ap.parse_args()
    generate_style_guide(args.facts, args.ref_style, args.output, args.size)


if __name__ == '__main__':
    main()
