#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager, now_iso, write_json

BAKERY_TOKENS = [
    '烘焙', '面包', '吐司', '可可吐司', '糕点', '蛋糕', '饼干', '可颂', '贝果',
    'bread', 'toast', 'bakery', 'pastry', 'cake', 'cookie', 'croissant', 'bagel',
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def resolve_path(project_dir: Path, raw: str) -> Path:
    path = Path(str(raw or '').strip())
    return path if path.is_absolute() else project_dir / path


def relative(project_dir: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_dir))
    except Exception:
        return str(path)


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None


def is_bakery_product(brief: dict) -> bool:
    product_name = str(brief.get('product_name', '') or '')
    industry = str(brief.get('industry', '') or '')
    style_note = str(brief.get('style_note', '') or '')
    haystack = ' '.join([product_name, industry, style_note]).lower()
    return any(token.lower() in haystack for token in BAKERY_TOKENS)


def is_product_poster(brief: dict) -> bool:
    poster_type = str(brief.get('type', '') or '')
    hero = brief.get('hero_priority', {}) or {}
    haystack = ' '.join([
        poster_type,
        str(hero.get('hero_1', '') or ''),
        str(brief.get('product_name', '') or ''),
    ])
    return bool(brief.get('product_name')) and any(token in haystack for token in ['产品', '商品', '推广', '海报'])


def build_normalization_note(brief: dict, source_size: tuple[int, int] | None) -> str:
    product_name = str(brief.get('product_name', '') or '产品').strip()
    size_text = f'{source_size[0]}x{source_size[1]}' if source_size else 'unknown'
    return f"""低清烘焙产品参考软代理说明

产品：{product_name}
原图尺寸：{size_text}

策略：
- 保留产品身份、圆顶吐司轮廓、主体色相和基础烘焙材质。
- 不用 AI 二次重绘切面微观结构，避免把低清孔洞脑补成蜂窝、木屑、鳞片或硬描边。
- 通过确定性图像处理压低局部对比、锐度和压缩纹理，让后续生图模型只读取产品大形和可可色，不把孔洞当成高清微距依据。
- 后续 prompt 仍负责要求真实、新鲜、柔软、含水量充足的面包组织。
"""


def render_soft_product_proxy(source_path: Path, output_png: Path, output_jpg: Path, canvas_size: int = 1024) -> tuple[int, int]:
    from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

    with Image.open(source_path) as img:
        rgb = img.convert('RGB')
        canvas = Image.new('RGB', (canvas_size, canvas_size), 'white')
        fitted = ImageOps.contain(
            rgb,
            (int(canvas_size * 0.9), int(canvas_size * 0.9)),
            method=Image.Resampling.LANCZOS,
        )
        left = (canvas_size - fitted.width) // 2
        top = (canvas_size - fitted.height) // 2
        canvas.paste(fitted, (left, top))

        # Low-pass the crumb texture very aggressively. For low-res bakery
        # references, dark pixels are product identity/color cues, not reliable
        # pore geometry. The proxy intentionally suppresses small holes so the
        # image model does not upscale them into dry honeycomb texture.
        diff = ImageChops.difference(canvas, Image.new('RGB', canvas.size, 'white')).convert('L')
        product_mask = diff.point(lambda p: 255 if p > 18 else 0)
        product_mask = product_mask.filter(ImageFilter.MedianFilter(size=9)).filter(ImageFilter.GaussianBlur(radius=2.0))

        low_freq = canvas.resize(
            (max(1, int(canvas_size * 0.18)), max(1, int(canvas_size * 0.18))),
            resample=Image.Resampling.BICUBIC,
        ).resize((canvas_size, canvas_size), resample=Image.Resampling.BICUBIC)
        median = canvas.filter(ImageFilter.MedianFilter(size=17)).filter(ImageFilter.GaussianBlur(radius=4.5))
        local_average = canvas.filter(ImageFilter.GaussianBlur(radius=18))
        shadow_lifted = ImageChops.lighter(median, local_average)
        softened = Image.blend(shadow_lifted, low_freq, 0.78)
        softened = softened.filter(ImageFilter.GaussianBlur(radius=2.2))
        softened = ImageEnhance.Sharpness(softened).enhance(0.16)
        softened = ImageEnhance.Contrast(softened).enhance(0.55)
        softened = ImageEnhance.Brightness(softened).enhance(1.13)
        softened = ImageEnhance.Color(softened).enhance(0.90)
        softened = Image.blend(softened, Image.new('RGB', softened.size, (214, 171, 134)), 0.10)

        clean_canvas = Image.new('RGB', softened.size, (248, 245, 239))
        softened = Image.composite(softened, clean_canvas, product_mask)

        output_png.parent.mkdir(parents=True, exist_ok=True)
        softened.save(output_png)
        softened.save(output_jpg, quality=94, optimize=True)
        return softened.size


def write_manifest(project_dir: Path, payload: dict) -> Path:
    manifest_path = project_dir / 'product_reference_manifest.json'
    current = {}
    if manifest_path.exists():
        try:
            current = load_json(manifest_path)
        except Exception:
            current = {}
    current.update(payload)
    current['updated_at'] = now_iso()
    write_json(manifest_path, current)
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description='Normalize low-resolution bakery product reference before poster generation')
    parser.add_argument('--project-dir', required=True, help='品牌海报项目目录')
    parser.add_argument('--threshold', type=int, default=900, help='短边低于该尺寸时触发')
    parser.add_argument('--size', default='1024x1024', help='产品参考代理图尺寸')
    parser.add_argument('--model', default='gpt-image-2', help='产品参考代理图生成模型')
    parser.add_argument('--force', action='store_true', help='即使非低清也强制生成')
    parser.add_argument('--strict', action='store_true', help='生成失败时返回非 0')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    manager = ProjectManager(project_dir)
    brief_path = project_dir / 'brief.json'
    if not brief_path.exists():
        print(json.dumps({'status': 'skipped', 'reason': 'brief.json 不存在'}, ensure_ascii=False, indent=2))
        return 0

    brief = load_json(brief_path)
    assets = brief.setdefault('assets', {})
    product_raw = str(assets.get('product', '') or '').strip()
    if not product_raw:
        payload = {'status': 'skipped', 'reason': '未提供产品图'}
        write_manifest(project_dir, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    realization = brief.get('product_reference_realization', {}) or {}
    original_raw = str(
        assets.get('product_original')
        or realization.get('original_product')
        or product_raw
    ).strip()
    product_path = resolve_path(project_dir, original_raw)
    size = image_size(product_path)
    should_run = bool(args.force)
    reason = ''
    if not should_run:
        if not size:
            reason = '产品图无法读取尺寸'
        elif min(size) >= args.threshold:
            reason = f'产品图尺寸足够（{size[0]}x{size[1]}）'
        elif not is_product_poster(brief):
            reason = '非产品推广/产品海报场景'
        elif not is_bakery_product(brief):
            reason = '非烘焙/吐司类产品'
        else:
            should_run = True

    if not should_run:
        payload = {'status': 'skipped', 'reason': reason, 'source': original_raw, 'source_size': size or []}
        manifest_path = write_manifest(project_dir, payload)
        manager.audit(
            'product_reference_normalization_skipped',
            stage='assets',
            status='skipped',
            actor='normalize_product_reference.py',
            reason=reason,
            files=[manager._relative(manifest_path)],
            extra=payload,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    note_path = project_dir / 'product_reference_prompt.txt'
    output_png = project_dir / 'images' / 'product_realism_ref.png'
    output_jpg = project_dir / 'images' / 'product_realism_ref.jpg'
    note_path.write_text(build_normalization_note(brief, size), encoding='utf-8')

    try:
        output_size = render_soft_product_proxy(product_path, output_png, output_jpg)
    except Exception as e:
        payload = {
            'status': 'failed_nonblocking',
            'method': 'deterministic_soft_proxy',
            'reason': '产品软代理参考生成失败，后续将回退到小尺寸产品参考图适配策略。',
            'source': original_raw,
            'source_size': size or [],
            'error': str(e),
        }
        manifest_path = write_manifest(project_dir, payload)
        manager.audit(
            'product_reference_normalization_failed',
            stage='assets',
            status='failed_nonblocking',
            actor='normalize_product_reference.py',
            reason=payload['reason'],
            files=[manager._relative(manifest_path)],
            extra=payload,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if args.strict else 0

    original_product = original_raw
    assets['product_original'] = original_product
    assets['product'] = relative(project_dir, output_jpg)
    assets['product_normalization'] = {
        'status': 'generated',
        'method': 'deterministic_soft_proxy',
        'source': original_product,
        'output': relative(project_dir, output_jpg),
        'output_png': relative(project_dir, output_png),
        'note_file': relative(project_dir, note_path),
        'generated_at': now_iso(),
        'source_size': size or [],
        'output_size': list(output_size),
        'reason': '低清烘焙产品图自动生成低频软代理，避免把压缩像素和锐化孔洞当作产品组织。',
    }
    write_json(brief_path, brief)

    payload = {
        'status': 'generated',
        'method': 'deterministic_soft_proxy',
        'source': original_product,
        'source_size': size or [],
        'output': relative(project_dir, output_jpg),
        'output_png': relative(project_dir, output_png),
        'output_size': list(output_size),
        'note_file': relative(project_dir, note_path),
    }
    manifest_path = write_manifest(project_dir, payload)
    manager.set_artifacts(product_reference=relative(project_dir, output_jpg))
    manager.audit(
        'product_reference_normalized',
        stage='assets',
        status='generated',
        actor='normalize_product_reference.py',
        reason='低清烘焙产品图已生成低频软代理参考。',
        files=[manager._relative(manifest_path), relative(project_dir, output_jpg), relative(project_dir, note_path)],
        extra=payload,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
