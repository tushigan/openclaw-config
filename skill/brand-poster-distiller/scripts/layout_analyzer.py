#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout analyzer: uses multimodal LLM to extract poster layout structure."""

import base64
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Configuration ---
MODEL = "gpt-5.4"
API_KEY = "sk-PbqL08MCu6JNe0AKVhn7wcPbXH1gl0KryGekyvkCu8KvxDN3"
API_BASE = "https://aixor.org/v1"

# --- Colors for skeleton SVG ---
_SKELETON_COLORS = {
    "title": ("#111111", "#f0f0f0", 2), "subtitle": ("#333333", "#e8e8e8", 1.5),
    "body_text": ("#555555", "#e0e0e0", 1), "image": ("#1a5276", "#d4e6f1", 1.5),
    "product_photo": ("#196f3d", "#d5f5e3", 1.5), "logo": ("#7d3c98", "#e8daef", 2),
    "button": ("#b03a2e", "#fadbd8", 2), "divider": ("#2c3e50", "#d5d8dc", 1),
    "background": ("#aab7b8", "#f2f3f4", 1), "decorative": ("#d4ac0d", "#fef9e7", 1),
    "qr_code": ("#1a1a1a", "#e8e8e8", 1.5), "price_tag": ("#c0392b", "#fadbd8", 2),
    "cta_area": ("#b03a2e", "#fadbd8", 2), "info_strip": ("#2c3e50", "#d5d8dc", 1.5),
    "watermark": ("#95a5a6", "#f2f3f4", 1),
}


def load_index():
    index_path = ROOT / 'library-index.json'
    raw = json.loads(index_path.read_text(encoding='utf-8'))
    cards = raw.get('cards', []) if isinstance(raw, dict) else raw
    return {'version': raw.get('version', '1.0'), 'updated_at': raw.get('updated_at', ''), 'cards': cards}


def find_card(distill_id):
    index = load_index()
    for item in index.get('cards', []):
        if item.get('id') == distill_id:
            return item
    return None


def generate_skeleton_svg(elements, title=""):
    W, H = 800, 1200
    rects = []
    labels = []
    for el in sorted(elements, key=lambda e: e.get('z_index', 1)):
        x = el['x'] / 100 * W
        y = el['y'] / 100 * H
        w = el['width'] / 100 * W
        h = el['height'] / 100 * H
        stroke, fill, sw = _SKELETON_COLORS.get(el.get('type', ''), ('#888', '#eee', 1))
        rects.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="2"/>')
        label_y = y + min(16, h / 2)
        name = el.get('name_zh', el.get('type', '?'))
        labels.append(f'<text x="{x + 4:.1f}" y="{label_y:.1f}" font-size="11" font-family="sans-serif" fill="{stroke}">{name}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="white"/>',
        f'<text x="10" y="24" font-size="14" font-family="sans-serif" font-weight="bold" fill="#111">{title}</text>',
    ] + rects + labels + ['</svg>'])


def _svg_to_png_file(svg_path, png_path):
    """Convert SVG to PNG. Try rsvg-convert -> cairosvg -> Pillow. Returns True on success."""
    svg_path = Path(svg_path)
    png_path = Path(png_path)

    # 1. rsvg-convert (system command — best available here, supports text)
    try:
        import subprocess
        result = subprocess.run(
            ['rsvg-convert', '-w', '1024', '-h', '1536', '-o', str(png_path), str(svg_path)],
            capture_output=True, timeout=30
        )
        if result.returncode == 0 and png_path.exists() and png_path.stat().st_size > 0:
            return True
    except Exception:
        pass
    if png_path.exists():
        try:
            png_path.unlink()
        except Exception:
            pass

    # 2. cairosvg
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1024, output_height=1536)
        if png_path.exists() and png_path.stat().st_size > 0:
            return True
    except Exception:
        pass
    if png_path.exists():
        try:
            png_path.unlink()
        except Exception:
            pass

    # 3. Pillow (manual rect rendering fallback, no text support)
    try:
        from PIL import Image, ImageDraw
        import xml.etree.ElementTree as ET
        tree = ET.parse(svg_path)
        root = tree.getroot()
        ns = root.tag.split('}')[0] + '}' if '}' in root.tag else ''
        vb = root.get('viewBox', '0 0 800 1200').split()
        W, H = int(vb[2]), int(vb[3])
        img = Image.new('RGBA', (W, H), 'white')
        draw = ImageDraw.Draw(img)
        for rect in root.findall(f'{ns}rect'):
            attrs = {k: rect.get(k) for k in ('x', 'y', 'width', 'height', 'fill', 'stroke', 'stroke-width')}
            x = float(attrs.get('x', 0))
            y = float(attrs.get('y', 0))
            w = float(attrs.get('width', W))
            h = float(attrs.get('height', H))
            fill = attrs.get('fill')
            if fill and fill != 'none':
                rgba = _hex_to_rgba(fill)
                draw.rectangle([(x, y), (x + w, y + h)], fill=rgba)
            stroke = attrs.get('stroke')
            if stroke and stroke != 'none':
                rgba = _hex_to_rgba(stroke)
                sw = float(attrs.get('stroke-width', 1))
                for _ in range(int(sw)):
                    draw.rectangle([(x, y), (x + w, y + h)], outline=rgba)
        img = img.convert('RGB')
        img = img.resize((1024, 1536), Image.LANCZOS)
        img.save(png_path, 'PNG')
        if png_path.exists() and png_path.stat().st_size > 0:
            return True
    except Exception as e:
        print(f'Pillow fallback failed: {e}')
    if png_path.exists():
        try:
            png_path.unlink()
        except Exception:
            pass

    return False


def _hex_to_rgba(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) == 6:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), 255)
    if len(hex_color) == 8:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), int(hex_color[6:8], 16))
    return (128, 128, 128, 255)


def _export_skeleton_png(skeleton_svg_rel, distill_id=None):
    """Generate companion PNG from SVG skeleton.

    PNG is named by distill_id (e.g. POSTER-DISTILL-P-002.png) for stable references.
    Falls back to SVG stem if distill_id is not provided.
    """
    svg_path = ROOT / skeleton_svg_rel
    if not svg_path.exists():
        return None
    png_dir = ROOT / 'site' / 'assets' / 'skeletons'
    png_dir.mkdir(parents=True, exist_ok=True)
    if distill_id:
        png_name = f"{distill_id}.png"
    else:
        png_name = f"{svg_path.stem}.png"
    png_path = png_dir / png_name
    if _svg_to_png_file(svg_path, png_path):
        return f"site/assets/skeletons/{png_name}"
    return None


def _compress_image(image_path: str, max_dim: int = 1024, quality: int = 85) -> bytes:
    """Compress image to max_dim on longest side, return JPEG bytes."""
    from PIL import Image
    import io
    img = Image.open(image_path).convert('RGB')
    w, h = img.size
    if w > max_dim or h > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    return buf.getvalue()


def _call_llm(image_path: str, prompt: str) -> str:
    """Call OpenAI-compatible API with image for layout analysis."""
    img_bytes = _compress_image(image_path)
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    mime = 'image/jpeg'

    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}}
            ]
        }],
        "system": "You are a layout analysis expert. Analyze the poster and return ONLY valid JSON."
    }

    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        },
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data['choices'][0]['message']['content']


def _parse_json_from_response(text):
    """Extract JSON from LLM response."""
    # Try direct JSON parse
    text = text.strip()
    if text.startswith('{'):
        return json.loads(text)
    # Extract from code block
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # Find first { to last }
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError(f"No JSON found in response: {text[:200]}")


LAYOUT_ANALYSIS_PROMPT = """Analyze this poster's layout structure. Identify all visual elements and their positions.

Return a JSON object with an "elements" array. Each element has:
- "id": string like "el-1"
- "type": one of: title, subtitle, body_text, image, product_photo, logo, button, divider, background, decorative, qr_code, price_tag, cta_area, info_strip, watermark
- "name_zh": GENERIC slot name in Chinese, describe the TYPE of element, NOT the actual content. Examples:
  - type=title -> name_zh="主标题区" or "顶部大标题" (never include actual text like "RICE DUMPLING")
  - type=subtitle -> name_zh="副标题区" or "英文副标题"
  - type=product_photo -> name_zh="产品主图区"
  - type=decorative -> name_zh="装饰元素" or "品牌图案装饰"
  - type=body_text -> name_zh="正文文字区" or "竖排文案区"
  - type=logo -> name_zh="品牌Logo"
  - type=price_tag -> name_zh="价格标签区"
  - type=qr_code -> name_zh="二维码区"
  - type=background -> name_zh="背景色块"
  - type=cta_area -> name_zh="行动号召区"
  - type=info_strip -> name_zh="信息条"
  The name should describe WHAT KIND OF SLOT this is, so it can be reused for any topic.
- "x", "y", "width", "height": percentage values (0-100) relative to the poster
- "z_index": integer layer order (1 = bottom)
- "confidence": 0-1 float
- "notes": empty string

Sort by visual hierarchy. The background should be z_index=1. Include all visible elements."""


def _describe_area(el):
    """Derive size description from element dimensions."""
    w, h = el.get('width', 0), el.get('height', 0)
    area = w * h
    if area >= 3000:
        return '（巨物）'
    elif area >= 1000:
        return '（大）'
    elif area >= 400:
        return '（中）'
    elif area >= 100:
        return ''
    elif area >= 40:
        return '（小）'
    else:
        return '（极小）'


def _derive_copy_guide(elements):
    """Derive a two-phase copy planning template from layout elements.

    Phase 1: AI agent 先按每个区域的要求策划文案（编号列出）
    Phase 2: AI agent 将策划好的文案填入生图 prompt 的具体位置
    """
    _TYPE_GUIDE = {
        'title': ('海报主标题', '横排', '根据主题策划主标题（建议8-15字中文，或2-3行英文）'),
        'subtitle': ('辅助副标题', '横排', '1行副标题（中文5-12字，或英文3-6个单词）'),
        'body_text': ('正文/品牌文案', '', ''),  # dynamic based on aspect
        'product_photo': ('画面主角/产品', '图像', '放置用户提供的产品图，或根据主题自动生成符合版式的主角形象'),
        'logo': ('品牌Logo', '图像', '放置用户提供的Logo图片'),
        'decorative': ('装饰元素', '图形', '不需要文案，根据主题生成相应的装饰图案'),
        'background': ('背景', '', '不需要文案，保持干净的背景'),
        'button': ('行动按钮', '横排', '1-3个中文字'),
        'qr_code': ('二维码', '图像', '放置二维码图片'),
        'price_tag': ('价格标签', '横排', '价格数字（建议1-6字符）'),
        'cta_area': ('行动号召区', '横排', '1行号召性文案（建议5-12字）'),
        'info_strip': ('信息条', '横排', '简短信息（建议10-20字）'),
        'image': ('图片区域', '图像', '放置用户提供的图片'),
        'divider': ('分隔线', '', '不需要文案'),
        'watermark': ('水印', '', '不需要文案'),
    }
    text_slots = []
    image_slots = []
    deco_slots = []
    copy_idx = 0
    for el in sorted(elements, key=lambda e: e.get('z_index', 1)):
        t = el.get('type', '')
        name = el.get('name_zh', t)
        w, h = el.get('width', 0), el.get('height', 0)
        size_desc = f'{w:.0f}%×{h:.0f}%'
        area = w * h
        if area >= 3000:
            size_desc += '（巨物）'
        elif area >= 1000:
            size_desc += '（大）'
        elif area >= 400:
            size_desc += '（中）'
        elif area < 40:
            size_desc += '（极窄）'

        guide = _TYPE_GUIDE.get(t, ('', '', ''))
        purpose = guide[0] if guide[0] else t
        direction = guide[1]
        requirement = guide[2]

        if t == 'body_text':
            if w < 10 and h > 15:
                direction = '竖排'
                requirement = '竖排中文文案（建议20-40字，分多行竖排）'
            else:
                direction = '横排'
                requirement = '横排中文文案（建议20-50字）'

        slot = {'name': name, 'type': t, 'size': size_desc, 'direction': direction, 'requirement': requirement}
        if requirement.startswith('不需要文案'):
            deco_slots.append(slot)
        elif t in ('product_photo', 'logo', 'image', 'qr_code'):
            image_slots.append(slot)
        else:
            copy_idx += 1
            slot['copy_idx'] = copy_idx
            text_slots.append(slot)

    # 构建两阶段模板
    lines = []
    lines.append('## 第一阶段：文案策划（先完成以下编号，再进入第二阶段生图）')
    lines.append('')
    if text_slots:
        for slot in text_slots:
            lines.append(f"{slot['copy_idx']}. 【{slot['name']}】{slot['direction']} {slot['size']} — {slot['requirement']}")
    else:
        lines.append('（本版式无需文案策划，直接跳过）')
    lines.append('')
    lines.append('## 第二阶段：生图 prompt 组装')
    lines.append('将第一阶段策划好的文案填入对应区域，然后按以下结构组装最终 prompt 交给生图模型：')
    lines.append('- 画面主角：放置在产品主图区（90%×60% 中心区域），根据用户主题自动生成或放置产品图')
    lines.append('- 标题文案：放置在主标题区，使用策划好的文案，确保文字有实际含义，不要生成伪文字或乱码')
    lines.append('- 装饰文字：放置在对应装饰区域，使用策划好的文案')
    lines.append('- 参考图：骨架图只约束构图，风格参考图只约束气质，不互相照抄')
    lines.append('- 标题文字必须有实际含义，不要生成伪文字、乱码或无意义的装饰性字符')
    return '\n'.join(lines)


def _derive_negative_constraints(elements):
    """Derive negative constraints from layout features."""
    constraints = [
        '不要破坏画面构图的比例关系',
        '标题文字必须有实际含义，不要生成伪文字、乱码或无意义的装饰性字符',
        '不要在留白区域添加构图之外的额外元素',
    ]
    has_giant = any(e.get('width', 0) * e.get('height', 0) >= 3000 for e in elements)
    if has_giant:
        constraints.append('产品主图区必须占画面主导地位，不能被其他元素抢镜')
    has_title = any(e.get('type') == 'title' and e.get('width', 0) * e.get('height', 0) >= 500 for e in elements)
    if has_title:
        constraints.append('顶部标题区必须强，不能被削弱或缩小')
    has_vertical = any(e.get('type') == 'body_text' and e.get('width', 0) < 10 and e.get('height', 0) > 15 for e in elements)
    if has_vertical:
        constraints.append('竖排文案区必须保持竖排方向，不得改为横排')
    high_whitespace = any(e.get('type') == 'background' and e.get('width', 0) >= 100 and e.get('height', 0) >= 100 for e in elements)
    if high_whitespace:
        constraints.append('不要在背景区域添加额外元素')
    return constraints


def analyze_card(distill_id: str):
    """Analyze a poster card and generate layout data."""
    card_info = find_card(distill_id)
    if not card_info:
        return {'ok': False, 'error': 'CARD_NOT_FOUND', 'id': distill_id}

    # 从卡片 JSON 文件读取完整数据（索引中可能缺少 source_images 等字段）
    card_path = ROOT / (card_info.get('card_path') or f"cards/{distill_id}.json")
    if not card_path.exists():
        return {'ok': False, 'error': 'CARD_FILE_NOT_FOUND', 'id': distill_id}
    card = json.loads(card_path.read_text(encoding='utf-8'))

    source_images = card.get('source_images', []) or []
    if not source_images:
        return {'ok': False, 'error': 'NO_SOURCE_IMAGES', 'id': distill_id}

    # Use first source image for analysis
    image_path = ROOT / source_images[0]
    if not image_path.exists():
        return {'ok': False, 'error': 'IMAGE_NOT_FOUND', 'path': str(image_path)}

    try:
        response = _call_llm(str(image_path), LAYOUT_ANALYSIS_PROMPT)
        result = _parse_json_from_response(response)
        elements = result.get('elements', [])

        # Generate skeleton SVG
        title = card.get('title', distill_id)
        skeleton_rel = f"site/assets/posters/poster-skeleton-{distill_id[-3:]}.svg"
        svg_path = ROOT / skeleton_rel

        svg = generate_skeleton_svg(elements, title)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(svg, encoding='utf-8')

        # Auto-export companion PNG (named by distill_id for stable references)
        png_rel = _export_skeleton_png(skeleton_rel, distill_id=distill_id)

        # Save layout data to card
        card = json.loads(card_path.read_text(encoding='utf-8'))
        analyzed_at = time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())
        notes = ''
        if not png_rel:
            notes = 'PNG export failed: all converters (cairosvg, Pillow, rsvg-convert) unavailable. SVG skeleton is ready.'
        card['layout_analysis'] = {
            'status': 'ready',
            'analyzed_at': analyzed_at,
            'analyzer_model': MODEL,
            'skeleton_image': skeleton_rel,
            'skeleton_png': png_rel or '',
            'elements': elements,
            'copy_planning_guide': _derive_copy_guide(elements),
            'negative_constraints': _derive_negative_constraints(elements),
            'notes': notes,
        }
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding='utf-8')

        return {
            'ok': True,
            'id': distill_id,
            'elements': elements,
            'skeleton_image': skeleton_rel,
            'skeleton_png': png_rel,
            'analyzer_model': MODEL,
            'analyzed_at': analyzed_at,
        }

    except Exception as e:
        # Set to failed status
        if card_path.exists():
            card = json.loads(card_path.read_text(encoding='utf-8'))
            card['layout_analysis'] = {
                'status': 'failed',
                'analyzed_at': time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime()),
                'analyzer_model': MODEL,
                'skeleton_image': '',
                'elements': [],
                'copy_planning_guide': '',
                'negative_constraints': [],
                'notes': f'Analysis failed: {str(e)}',
            }
            card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'ok': False, 'error': 'ANALYSIS_FAILED', 'detail': str(e), 'id': distill_id}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <DISTILL_ID>")
        sys.exit(1)

    distill_id = sys.argv[1]
    result = analyze_card(distill_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get('ok') else 1)
