#!/usr/bin/env python3
"""
创建完稿提示词确认文档
将提示词和参考图片整合到飞书文档中，方便用户一站式确认

用法:
    python3 skills/brand-poster-creator/scripts/create_prompt_doc.py \
        --title "完稿提示词确认 - 青团海报" \
        --mood-image images/mood_upscaled.png \
        --logo assets/logo.png \
        --product assets/product.png \
        --brand "青团品牌" \
        --copy-file .prompt_copy.md \
        --output-doc-url doc_url.txt
"""

import argparse
import os
import sys
import base64
import json
from datetime import datetime
from pathlib import Path


def read_copy_file(copy_file_path):
    """读取文案配置文件"""
    if not os.path.exists(copy_file_path):
        return None
    
    with open(copy_file_path, 'r', encoding='utf-8') as f:
        return f.read()


def build_markdown_content(args, copy_content=None):
    """构建飞书文档的 Markdown 内容"""
    
    # 图片 URL 占位符（实际需要上传到图床或使用 base64）
    mood_image_tag = f'<image url="file://{args.mood_image}" width="600" align="center" caption="图一：垫图/调性图"/>' if args.mood_image and os.path.exists(args.mood_image) else "*未提供垫图*"
    logo_image_tag = f'<image url="file://{args.logo}" width="200" align="center" caption="图二：品牌 Logo"/>' if args.logo and os.path.exists(args.logo) else "*未提供 Logo*"
    product_image_tag = f'<image url="file://{args.product}" width="300" align="center" caption="图三：产品图"/>' if args.product and os.path.exists(args.product) else "*未提供产品图*"
    
    # 如果提供了文案文件，解析内容
    prompt_text = copy_content if copy_content else ""
    
    markdown = f"""#### 📋 完稿生成提示词确认

<callout emoji="🎨" background-color="light-blue">
请确认以下内容后，回复「确认生成」开始生成最终海报
</callout>

---

#### 📎 参考图片

<grid cols="3">
<column>

{mood_image_tag}

**图一：垫图/调性图**
- 来源：MJ 升频后的高清图
- 用途：作为画面风格参考

</column>
<column>

{logo_image_tag}

**图二：品牌 Logo**
- 位置：按提示词指定位置放置

</column>
<column>

{product_image_tag}

**图三：产品图**
- 位置：按提示词指定位置放置

</column>
</grid>

---

#### 📝 完稿提示词（中文）

<callout emoji="⚠️" background-color="light-yellow">
以下提示词将直接用于 Nano Banana 2 生图（支持中文）
</callout>

{prompt_text if prompt_text else '''
**画面主体**：
- 主体元素：
- 构图方式：
- 视角/景深：
- 光影氛围：

**品牌元素位置**：
- Logo 位置：
- 产品位置：
- 产品呈现方式：

**文案内容与排版**：
| 层级 | 内容 | 字体风格 | 位置 | 大小 |
|-----|------|---------|------|-----|
| 主标题 | | | | |
| 副标题 | | | | |
| 卖点文案 | | | | |
| CTA | | | | |

**色调与质感**：
- 主色调：
- 辅助色：
- 整体质感：
'''}

---

#### ✅ 确认选项

请确认以上描述是否准确：

1. **回复「确认生成」** → 使用上述提示词直接生成最终海报（一次性带完整文案）
2. **回复「修改 [具体项]」** → 调整对应描述（如「修改主标题位置」）
3. **回复「返回 Step 2」** → 重新选择调性图

<callout emoji="💡" background-color="light-green">
**提示**：Nano Banana 2 支持中文提示词，将直接使用上述中文描述生图
</callout>

---

生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
品牌：{args.brand or "未指定"}
"""
    return markdown


def main():
    parser = argparse.ArgumentParser(description='创建完稿提示词确认文档')
    parser.add_argument('--title', required=True, help='文档标题')
    parser.add_argument('--mood-image', help='垫图/调性图路径')
    parser.add_argument('--logo', help='Logo 图片路径')
    parser.add_argument('--product', help='产品图路径')
    parser.add_argument('--brand', help='品牌名称')
    parser.add_argument('--copy-file', help='文案配置文件路径（包含完整提示词）')
    parser.add_argument('--output-doc-url', default='doc_url.txt', help='输出文档 URL 的文件路径')
    parser.add_argument('--folder-token', help='飞书文件夹 token（可选）')
    
    args = parser.parse_args()
    
    # 读取文案配置
    copy_content = None
    if args.copy_file and os.path.exists(args.copy_file):
        copy_content = read_copy_file(args.copy_file)
        print(f"✓ 已读取文案配置: {args.copy_file}")
    
    # 构建 Markdown 内容
    markdown_content = build_markdown_content(args, copy_content)
    
    # 输出 Markdown 内容（供外部工具使用）
    output_file = f".prompt_doc_{args.brand or 'temp'}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\n✓ Markdown 文档已生成: {output_file}")
    print(f"\n接下来请使用 feishu_mcp_create_doc 工具创建飞书文档：")
    print(f"  - title: {args.title}")
    print(f"  - markdown: [读取 {output_file} 文件内容]")
    if args.folder_token:
        print(f"  - folder_token: {args.folder_token}")
    
    # 提示图片上传方式
    print("\n📎 图片处理说明：")
    if args.mood_image:
        print(f"  - 垫图: {args.mood_image}")
        print(f"    使用 feishu_doc_media 工具追加到文档，或使用公开 URL")
    if args.logo:
        print(f"  - Logo: {args.logo}")
    if args.product:
        print(f"  - 产品图: {args.product}")
    
    print("\n⚠️  注意：飞书文档中的 <image> 标签需要公开可访问的 URL")
    print("   本地图片需要：")
    print("   1. 上传到图床获取 URL，或")
    print("   2. 先用 feishu_doc_media 工具追加到文档")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
