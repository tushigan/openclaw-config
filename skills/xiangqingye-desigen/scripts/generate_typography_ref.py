#!/usr/bin/env python3
"""Generate a typography reference image for detail page consistency.

This creates a "typography specimen" showing:
- Headline style (large, bold)
- Subtitle style (medium weight)
- Body text style (regular)
- Label/tag style (small)
- Spacing relationships

The typography ref is generated ONCE after the style guide,
then used as --ref-typography for EVERY segment.

Usage:
  python generate_typography_ref.py --facts facts.json \
    --style-guide style_guide.png \
    --output images/typography_ref.png
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


# Remove proxy env vars
for key in list(os.environ.keys()):
    if key.lower() in ('http_proxy', 'https_proxy', 'all_proxy',
                       'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'):
        os.environ.pop(key, None)


def build_prompt(facts: dict) -> str:
    """Build typography reference generation prompt."""
    brand = facts.get('brand', '')
    product = facts.get('product', '')

    prompt = f"""生成一张电商详情页字体排版参考图，展示中文排版层级体系。

【整体要求】
- 展示不同字号/字重的排版效果
- 使用真实中文文字，不是英文占位
- 干净的白色或浅色背景
- 重点展示字体大小、粗细、间距关系

【字体层级】
从上到下展示以下层级：

1. 大标题样式
   - 最大字号，粗体
   - 用于页面主标题、品牌名
   - 示例："法式可丽饼"、"{brand}"

2. 副标题样式
   - 中等字号，中等粗细
   - 用于模块标题、卖点标题
   - 示例："三层酥脆夹心"、"5种精选口味"

3. 正文样式
   - 常规字号，常规粗细
   - 用于产品描述、配料说明
   - 示例："选用进口黄油制作，层层叠叠的酥脆口感"

4. 标签/标注样式
   - 最小字号
   - 用于口味标签、价格标签、角标
   - 示例："热销口味"、"新品上市"

【排版规则】
- 各层级之间有明显的大小/粗细区分
- 行距适中，保持可读性
- 模块之间有合理的留白
- 整体呈现专业电商详情页的排版感

【禁止事项】
- 禁止英文文字
- 禁止产品图片或包装
- 禁止复杂装饰元素
- 重点是字体层级，不是视觉设计
"""
    return prompt


def generate_typography_ref(facts_path: str, style_guide_path: str,
                            output_path: str, size: str = '768x1024'):
    """Generate typography reference image."""
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
        '--ref-style', style_guide_path,
    ]

    print(f'生成字体排版参考...')
    print(f'输出: {output_path}')

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'错误: {result.stderr}')
        sys.exit(1)

    print(f'字体排版参考已生成: {output_path}')
    return output_path


def main():
    ap = argparse.ArgumentParser(description='Generate typography reference')
    ap.add_argument('--facts', required=True, help='Product facts JSON file')
    ap.add_argument('--style-guide', required=True,
                    help='Style guide image path')
    ap.add_argument('--output', required=True, help='Output image path')
    ap.add_argument('--size', default='768x1024',
                    help='Image size (default 768x1024)')

    args = ap.parse_args()
    generate_typography_ref(args.facts, args.style_guide, args.output, args.size)


if __name__ == '__main__':
    main()
