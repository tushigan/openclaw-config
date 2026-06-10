#!/usr/bin/env python3
"""
大型 HTML PPT 生成辅助工具
用法: python3 gen_large_deck.py --script ppt_script.md --output deck/ [--style modern-minimal]

功能：
- 解析 Markdown 格式的 PPT 逐页脚本
- 逐页生成独立 HTML 文件（1920×1080）
- 自动生成 index.html（基于 deck_index.html 模板）
- 支持自定义样式主题

依赖：无外部依赖，纯标准库实现
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any


def parse_markdown_script(md_file: Path) -> List[Dict[str, Any]]:
    """
    解析 Markdown 格式的 PPT 逐页脚本

    期望格式：
    # 第1页：标题
    内容...

    ## 第2页：副标题
    内容...

    返回：[{"index": 1, "title": "标题", "content": "内容..."}, ...]
    """
    if not md_file.exists():
        raise FileNotFoundError(f"脚本文件不存在: {md_file}")

    content = md_file.read_text(encoding='utf-8')
    slides = []

    # 匹配页面标题：# 第N页：标题 或 ## 第N页：标题
    pattern = r'^#{1,2}\s*第?\s*(\d+)\s*页[：:]\s*(.+?)$'

    lines = content.split('\n')
    current_slide = None
    current_content = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            # 保存上一页
            if current_slide:
                current_slide['content'] = '\n'.join(current_content).strip()
                slides.append(current_slide)

            # 开始新页
            page_num = int(match.group(1))
            title = match.group(2).strip()
            current_slide = {
                'index': page_num,
                'title': title,
                'content': ''
            }
            current_content = []
        elif current_slide:
            current_content.append(line)

    # 保存最后一页
    if current_slide:
        current_slide['content'] = '\n'.join(current_content).strip()
        slides.append(current_slide)

    return slides


def generate_slide_html(slide: Dict[str, Any], style: str) -> str:
    """
    根据页面数据生成单页 HTML（1920×1080）

    Args:
        slide: 页面数据 {"index": 1, "title": "标题", "content": "内容"}
        style: 样式主题名称

    Returns:
        完整的 HTML 字符串
    """

    # 样式配置
    styles = {
        'modern-minimal': {
            'bg': '#ffffff',
            'title_color': '#1a1a1a',
            'content_color': '#4a4a4a',
            'accent': '#0066cc',
            'font': '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
        },
        'dark-elegant': {
            'bg': '#1a1a1a',
            'title_color': '#ffffff',
            'content_color': '#cccccc',
            'accent': '#00aaff',
            'font': 'Georgia, serif'
        },
        'warm-creative': {
            'bg': '#faf8f5',
            'title_color': '#2c1810',
            'content_color': '#5a4a3a',
            'accent': '#d4713f',
            'font': '"Newsreader", "Source Serif Pro", Georgia, serif'
        }
    }

    theme = styles.get(style, styles['modern-minimal'])

    # 处理内容：简单的 Markdown 解析
    content = slide['content']
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)  # **粗体**
    content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)  # *斜体*
    content = re.sub(r'^- (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)  # 列表
    content = content.replace('\n\n', '</p><p>')  # 段落

    # 如果有列表项，包裹在 <ul> 中
    if '<li>' in content:
        content = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', content, flags=re.DOTALL)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1920, initial-scale=1">
    <title>{slide['title']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            width: 1920px;
            height: 1080px;
            background: {theme['bg']};
            font-family: {theme['font']};
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 120px 160px;
            overflow: hidden;
        }}

        .slide {{
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        h1 {{
            font-size: 72px;
            font-weight: 700;
            color: {theme['title_color']};
            margin-bottom: 60px;
            line-height: 1.2;
        }}

        .content {{
            font-size: 36px;
            color: {theme['content_color']};
            line-height: 1.6;
        }}

        .content p {{
            margin-bottom: 30px;
        }}

        .content strong {{
            color: {theme['accent']};
            font-weight: 600;
        }}

        .content em {{
            font-style: italic;
            color: {theme['accent']};
        }}

        .content ul {{
            list-style: none;
            margin: 30px 0;
        }}

        .content li {{
            margin-bottom: 20px;
            padding-left: 40px;
            position: relative;
        }}

        .content li::before {{
            content: "•";
            position: absolute;
            left: 0;
            color: {theme['accent']};
            font-size: 48px;
            line-height: 1;
        }}
    </style>
</head>
<body>
    <div class="slide">
        <h1>{slide['title']}</h1>
        <div class="content">
            <p>{content}</p>
        </div>
    </div>
</body>
</html>"""

    return html


def generate_deck_index(slides: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    生成 index.html（基于 deck_index.html 模板）

    Args:
        slides: 所有页面数据
        output_dir: 输出目录
    """

    # 构建 MANIFEST
    manifest = [
        {
            "file": f"slides/slide-{slide['index']:02d}.html",
            "label": slide['title']
        }
        for slide in slides
    ]

    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2)

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PPT 演示</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #0a0a0a;
            color: #fff;
            overflow: hidden;
        }}

        #container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        iframe {{
            border: none;
            width: 1920px;
            height: 1080px;
            transform-origin: center;
        }}

        .controls {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            gap: 15px;
            z-index: 1000;
        }}

        .controls button {{
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }}

        .controls button:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}

        .counter {{
            position: fixed;
            bottom: 30px;
            left: 30px;
            font-size: 18px;
            color: rgba(255, 255, 255, 0.6);
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div id="container">
        <iframe id="slide-frame"></iframe>
    </div>

    <div class="controls">
        <button id="prev">← 上一页</button>
        <button id="next">下一页 →</button>
    </div>

    <div class="counter">
        <span id="current">1</span> / <span id="total">{len(slides)}</span>
    </div>

    <script>
        const MANIFEST = {manifest_json};

        let currentIndex = 0;
        const frame = document.getElementById('slide-frame');
        const currentEl = document.getElementById('current');
        const totalEl = document.getElementById('total');

        function loadSlide(index) {{
            if (index < 0 || index >= MANIFEST.length) return;
            currentIndex = index;
            frame.src = MANIFEST[index].file;
            currentEl.textContent = index + 1;

            // 自适应缩放
            fitSlide();
        }}

        function fitSlide() {{
            const containerWidth = window.innerWidth;
            const containerHeight = window.innerHeight;
            const slideWidth = 1920;
            const slideHeight = 1080;

            const scale = Math.min(
                containerWidth / slideWidth,
                containerHeight / slideHeight
            ) * 0.9;

            frame.style.transform = `scale(${{scale}})`;
        }}

        // 键盘导航
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === ' ') {{
                loadSlide(currentIndex + 1);
            }} else if (e.key === 'ArrowLeft') {{
                loadSlide(currentIndex - 1);
            }}
        }});

        // 按钮导航
        document.getElementById('prev').addEventListener('click', () => {{
            loadSlide(currentIndex - 1);
        }});

        document.getElementById('next').addEventListener('click', () => {{
            loadSlide(currentIndex + 1);
        }});

        // 窗口调整
        window.addEventListener('resize', fitSlide);

        // 初始加载
        totalEl.textContent = MANIFEST.length;
        loadSlide(0);
    </script>
</body>
</html>"""

    (output_dir / 'index.html').write_text(index_html, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='大型 HTML PPT 生成辅助工具')
    parser.add_argument('--script', required=True, help='PPT 逐页脚本文件（Markdown 格式）')
    parser.add_argument('--output', required=True, help='输出目录')
    parser.add_argument('--style', default='modern-minimal',
                       choices=['modern-minimal', 'dark-elegant', 'warm-creative'],
                       help='样式主题（默认：modern-minimal）')

    args = parser.parse_args()

    script_file = Path(args.script)
    output_dir = Path(args.output)

    # 创建输出目录
    slides_dir = output_dir / 'slides'
    slides_dir.mkdir(parents=True, exist_ok=True)

    print(f"📖 解析脚本文件: {script_file}")
    slides = parse_markdown_script(script_file)
    print(f"✓ 解析到 {len(slides)} 页")

    # 逐页生成
    print(f"\n🎨 开始生成页面（样式：{args.style}）")
    for slide in slides:
        html = generate_slide_html(slide, args.style)
        output_file = slides_dir / f"slide-{slide['index']:02d}.html"
        output_file.write_text(html, encoding='utf-8')
        print(f"  ✓ 第 {slide['index']} 页: {slide['title']}")

    # 生成 index.html
    print(f"\n📦 生成 index.html")
    generate_deck_index(slides, output_dir)

    print(f"\n✅ PPT 生成完成！")
    print(f"   输出目录: {output_dir.absolute()}")
    print(f"   打开方式: file://{output_dir.absolute()}/index.html")
    print(f"\n💡 提示：")
    print(f"   - 使用左右箭头键或空格键翻页")
    print(f"   - 按 F11 进入全屏演示模式")


if __name__ == '__main__':
    main()
