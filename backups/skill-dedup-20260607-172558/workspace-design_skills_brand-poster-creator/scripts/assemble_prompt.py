#!/usr/bin/env python3
"""
Prompt 精确装配器 — 脚本化版本
读取 brief.json + distill_card.json + copywriting.json，程序化组装生图 prompt。
agent 只需执行此脚本，不需要手写 prompt。

用法:
    python3 assemble_prompt.py \
        --brief /path/to/brief.json \
        --distill /path/to/distill_card.json \
        --copywriting /path/to/copywriting.json \
        --output /path/to/prompt_draft.md
"""

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager

DISTILLER_ROOT = Path('/Users/a123/.openclaw/workspace/skills/brand-poster-distiller')
DISTILLER_SCRIPTS_DIR = DISTILLER_ROOT / 'scripts'
if str(DISTILLER_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(DISTILLER_SCRIPTS_DIR))

from layout_analyzer import _export_skeleton_png


# ─── 禁止混入 prompt 的工作流术语 ───
_FORBIDDEN_WORDS = [
    "蒸馏卡", "主题语义", "品类语义", "原海报", "版式锁定",
    "hero_1", "hero_2", "forbidden_hero", "brief.json",
    "版式使用说明", "蒸馏", "distill", "distill_card",
    "copy_planning", "layout_analysis",
    "Distill ID", "copy_planning_guide",
    "第一阶段：文案策划", "第二阶段：生图",
    "Layout notes", "PNG export skipped",
    "Reference images (by role",
]

# ─── 未知元素类型 → 已知类型映射 ───
_TYPE_ALIAS = {
    'cta_area': 'body_text',
    'info_strip': 'body_text',
    'channel_logo_group': 'logo',
    'image': 'decorative',
    'price_tag': 'body_text',
    'watermark': 'decorative',
    'button': 'body_text',
    'divider': 'decorative',
}

_FESTIVAL_SCENE_HINTS = {
    "六一": {
        "season": "初夏",
        "mood": "轻松欢乐、童趣互动、治愈有活力",
        "scene": "画面应体现儿童节氛围，可出现气球、糖果、彩旗、礼物、甜点分享等轻量节日元素",
        "action": "主角应处于庆祝、玩耍、分享甜点或与儿童节小道具互动的瞬间",
        "avoid": ["冬季雪地", "冰雪", "圣诞装饰", "厚重冬装", "寒冷天气意象"],
    },
    "儿童节": {
        "season": "初夏",
        "mood": "轻松欢乐、童趣互动、治愈有活力",
        "scene": "画面应体现儿童节氛围，可出现气球、糖果、彩旗、礼物、甜点分享等轻量节日元素",
        "action": "主角应处于庆祝、玩耍、分享甜点或与儿童节小道具互动的瞬间",
        "avoid": ["冬季雪地", "冰雪", "圣诞装饰", "厚重冬装", "寒冷天气意象"],
    },
    "春节": {
        "season": "冬末春初",
        "mood": "热闹喜庆、团圆祥和、年味鲜明",
        "scene": "画面应体现迎新、团圆、年俗氛围，可出现灯笼、福字、烟花、年货等节庆元素",
        "action": "主角应处于迎新、送福、团圆互动或年俗庆祝的瞬间",
        "avoid": ["冷清空旷", "性冷淡留白", "非节庆化冬日雪景"],
    },
    "中秋": {
        "season": "初秋",
        "mood": "温柔明亮、团圆有仪式感",
        "scene": "画面应体现赏月、团圆、月饼礼赠氛围，可出现月亮、云纹、灯笼、玉兔等节庆元素",
        "action": "主角应处于赏月、团圆分享、礼盒互动的瞬间",
        "avoid": ["圣诞装饰", "冰雪", "寒冬雪地"],
    },
}

_SCENE_CONFLICT_HINTS = {
    "冬季雪地": ["冬", "雪"],
    "冰雪": ["冰", "雪"],
    "圣诞装饰": ["圣诞"],
    "厚重冬装": ["冬装", "围巾", "羽绒", "厚靴", "棉服"],
    "寒冷天气意象": ["寒冷", "冷风", "霜", "冰", "雪"],
    "寒冬雪地": ["寒冬", "冬", "雪"],
    "非节庆化冬日雪景": ["冬", "雪"],
}


def load_json(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_ref_path(raw_path, base_dir):
    if not raw_path:
        return ""
    path = Path(raw_path)
    if path.is_absolute():
        return str(path)
    return str((base_dir / path).resolve())


def normalize_refs(refs, project_dir):
    normalized = {}
    for key, value in refs.items():
        if isinstance(value, list):
            items = []
            for item in value:
                item_copy = dict(item)
                if item_copy.get("路径"):
                    item_copy["路径"] = normalize_ref_path(item_copy["路径"], project_dir)
                items.append(item_copy)
            normalized[key] = items
        elif isinstance(value, dict):
            item_copy = dict(value)
            if item_copy.get("路径"):
                item_copy["路径"] = normalize_ref_path(item_copy["路径"], project_dir)
            normalized[key] = item_copy
        else:
            normalized[key] = value
    return normalized


def looks_like_generated_style_ref(path, project_dir=None):
    raw = str(path or '').strip()
    if not raw:
        return False
    ref_path = Path(raw)
    stem = ref_path.stem.lower()
    name = ref_path.name.lower()

    if stem == 'current_base_ref':
        return True
    if stem.startswith('final_poster') or name.startswith('final_poster'):
        return True
    if stem.startswith('generated_') or stem.endswith('_generated') or '-generated' in stem:
        return True

    if project_dir is not None:
        try:
            resolved = ref_path.resolve()
            images_dir = (project_dir / 'images').resolve()
            if resolved.parent == images_dir and stem.startswith('final_'):
                return True
        except Exception:
            return False
    return False


def validate_style_refs(brief, refs, project_dir):
    workflow_options = brief.get('workflow_options', {}) or {}
    if brief.get('allow_generated_style_refs') or workflow_options.get('allow_generated_style_refs'):
        return []

    issues = []
    for item in refs.get("风格参考图", []) or []:
        path = str((item or {}).get("路径", "") or "").strip()
        if path and looks_like_generated_style_ref(path, project_dir):
            issues.append(
                f"风格参考图不能直接使用上一版 AI 成图或项目输出图：{path}。"
                "请改用真实风格参考图；如果只是想延续构图或氛围，请保留骨架图并在创意表达中描述，不要继续把生成图当 style_ref。"
            )
    return issues


def is_bakery_product(brief):
    product = brief.get("product", {}) or {}
    product_name = str(brief.get("product_name", "") or product.get("name", "") or "")
    industry = str(brief.get("industry", "") or "")
    festival = str(brief.get("festival", "") or "")
    style_note = str(brief.get("style_note", "") or "")
    haystack = " ".join([product_name, industry, festival, style_note]).lower()
    tokens = [
        "烘焙", "面包", "吐司", "可可吐司", "糕点", "蛋糕", "饼干", "可颂", "贝果",
        "bread", "toast", "bakery", "pastry", "cake", "cookie", "croissant", "bagel",
    ]
    return any(token.lower() in haystack for token in tokens)


def build_bakery_texture_guard(brief):
    if not is_bakery_product(brief):
        return ""
    return "\n".join([
        "== 烘焙产品质感约束 ==",
        "面包/吐司切面必须呈现真实商业软吐司组织，而不是酸面包/欧包/夏巴塔的大开孔结构：整体应是细密闭合、柔软湿润、低局部对比的面包芯。",
        "孔隙只能少量、细小、疏密不一、边缘柔和，不能成为画面主要纹理；不要满屏蜂窝孔、开放式大洞、干海绵、木屑纤维、网状雕刻、鳞片状或金属蚀刻纹理。",
        "如果产品是可可吐司或深色吐司，切面暗斑应被理解为可可色泽变化，不要把每个暗斑都画成洞；不要每个孔洞都有强高光/强暗边；不要为了“高清晰”堆很重的微观纹理。",
        "外皮应是自然烘烤形成的细微褶皱和轻微粗糙，带柔和油润感和自然明暗，不要塑料高光、干裂外壳或过度锐化。",
        "如果缺少足够清晰的真实切面参考，应使用真实商业烘焙摄影的常识补全自然、低频、柔软的组织；宁可让切面细节稍软，也不要脑补出规则、干硬、超锐化的假切面。",
        "如果产品参考图与目标主视觉姿态差异很大，优先保真产品身份、形体、颜色和真实组织感；不要为了做成完美正面立姿，重新捏造一块假的切面。"
    ])


def build_lowres_bakery_visual_strategy(brief, refs):
    if not is_bakery_product(brief) or not is_low_resolution_product_ref(brief, refs):
        return ""
    return "\n".join([
        "== 低清烘焙产品主视觉策略（最高优先级） ==",
        "本项目产品参考图为低清烘焙图，不能把切面放大成主视觉微距。若其它段落要求“站立吐司”“切面可见”或“产品大主视觉”，必须按本段重解释。",
        "主视觉应采用完整中景产品肖像：看见圆顶、外皮、侧面和整体轮廓，产品完整入画，不做超近景裁切，不让切面铺满画面。",
        "切面只能是柔和、低细节的辅助识别区域；如果无法保证真实湿润组织，就让切面转向侧面或减少可见面积，优先表现圆顶外皮与整体可可吐司身份。",
        "禁止把产品切面画成欧包/酸面包/夏巴塔的大孔、蜂窝、木屑、干海绵或锐化网格；不要在每个暗点上加高光和硬暗边。",
        "画面判断标准：远看是一片新鲜柔软的可可吐司，近看也不应该看到密集孔洞、焦脆木屑感或过度锐化纹理。"
    ])


def read_image_size(path):
    raw = str(path or "").strip()
    if not raw:
        return None
    try:
        from PIL import Image
        with Image.open(raw) as img:
            return img.size
    except Exception:
        return None


def product_reference_size(refs):
    product = refs.get("产品图") or {}
    return read_image_size(str(product.get("路径", "") or "").strip())


def product_texture_refs(refs):
    raw = refs.get("产品质地参考图", []) or []
    if isinstance(raw, dict):
        return [raw]
    return raw


def has_product_texture_refs(refs):
    return any(str((item or {}).get("路径", "") or "").strip() for item in product_texture_refs(refs))


def normalized_source_size(brief):
    assets = brief.get("assets", {}) or {}
    normalization = assets.get("product_normalization", {}) or {}
    raw_size = normalization.get("source_size") or []
    if isinstance(raw_size, (list, tuple)) and len(raw_size) >= 2:
        try:
            return int(raw_size[0]), int(raw_size[1])
        except Exception:
            return None
    return None


def is_low_resolution_product_ref(brief, refs, threshold=900):
    source_size = normalized_source_size(brief)
    if source_size and min(source_size) < threshold:
        return True
    size = product_reference_size(refs)
    return bool(size and min(size) < threshold)


def build_product_reference_guard(brief, refs):
    product = refs.get("产品图") or {}
    product_path = str(product.get("路径", "") or "").strip()
    if not product_path:
        return ""

    lines = [
        "== 产品保真与参考边界 ==",
        "产品参考图是产品身份、真实材质、颜色和形体的最高优先级依据；风格参考和骨架图不得覆盖产品真实质感。",
        "如果目标画面要求的姿态、角度、裁切或放大倍率在产品参考图中没有明确出现，不要重新发明产品微观结构；宁可保留参考图的真实角度、轻微不完美和自然质感。",
        "产品被放大为主视觉时，不要把参考图的压缩像素或噪点脑补成规则纹理、硬边纹理或高锐度微距纹理；整体观感应先真实、自然、可食用，再考虑清晰度。",
    ]

    source_size = normalized_source_size(brief)
    size = read_image_size(product_path)
    effective_size = source_size or size
    if effective_size:
        width, height = effective_size
        size_is_original = source_size is not None
        size_label = "原始产品参考图尺寸" if size_is_original else "产品参考图尺寸"
        if min(width, height) < 900:
            if size_is_original:
                current_size = f"；当前传入的软代理图尺寸为 {size[0]}x{size[1]}" if size else ""
            else:
                current_size = ""
            lines.extend([
                "",
                "== 小尺寸产品参考图适配策略 ==",
                f"{size_label}为 {width}x{height}{current_size}，这不是阻塞条件；它只用于锁定产品身份、轮廓、配色、基础材质和包装/形体关系。",
                "不要把小图像素直接放大、锐化或复制成产品表面细节；不要从压缩纹理里推断均匀孔洞、木屑感、鳞片感或硬描边。",
                "需要把产品作为主视觉时，可以保持清晰的产品轮廓和可读外形，但微观组织必须用真实产品摄影常识补全：自然低频、软边、低局部对比、非均匀分布。",
                "如果小图没有提供足够切面信息，切面细节应克制、柔和、可信，不做超微距肌理炫技；不要因为参考图小而生成干硬、塑料或过度锐化的假产品。",
            ])

    normalization = brief.get("assets", {}).get("product_normalization", {}) or {}
    if normalization.get("status") == "generated" and normalization.get("method") == "deterministic_soft_proxy":
        lines.extend([
            "",
            "== 低频软代理说明 ==",
            "产品参考图已经经过低频软代理处理，后续生图只读取产品身份、轮廓、色相和整体质感，不要再把孔洞、压缩噪点或边缘锐化成新的微观纹理。",
            "软代理里的暗点、暗斑、模糊纹路都不是孔洞依据，只能当作可可吐司的宽泛色块变化；不要逐点复刻。",
            "切面组织只需轻微可见、柔软可信即可；不要把孔洞进一步画密、画硬、画成蜂窝或木屑感。",
            "如果模型想强化微距纹理，宁可降低孔洞可见度，也不要制造规则网格、鳞片或硬描边。"
        ])

    if has_product_texture_refs(refs):
        lines.extend([
            "",
            "== 产品身份与质地参考分离 ==",
            "产品图只决定产品身份、圆顶吐司轮廓、可可色相和整体比例；产品质地参考图只决定切面组织的柔软度、孔隙尺度、低对比和湿润感。",
            "不得让质地参考图替换产品身份、颜色或造型；也不得把原始产品图中的低清暗斑逐点放大成孔洞。",
            "如果两类参考冲突，身份/颜色/轮廓听产品图，切面组织听产品质地参考图。",
            "已有质地参考时，不需要再生成中间 AI 产品 hero 参考；最终生图应直接综合“原始产品身份图 + 质地组织参考”。"
        ])

    return "\n".join(lines)


def validate_product_normalization_gate(brief, project_dir):
    assets = brief.get("assets", {}) or {}
    product_raw = str(assets.get("product", "") or "").strip()
    if not product_raw or not brief.get("product_name") or not is_bakery_product(brief):
        return ""

    if assets.get("product_texture_refs"):
        return ""

    realization = brief.get("product_reference_realization", {}) or {}
    source_raw = str(
        assets.get("product_original")
        or realization.get("original_product")
        or product_raw
    ).strip()
    source_path = normalize_ref_path(source_raw, project_dir)
    source_size = read_image_size(source_path)
    if not source_size or min(source_size) >= 900:
        return ""

    normalization = assets.get("product_normalization", {}) or {}
    normalization_status = str(normalization.get("status", "") or "").strip()

    manifest_status = ""
    manifest_path = project_dir / "product_reference_manifest.json"
    if manifest_path.exists():
        try:
            manifest = load_json(str(manifest_path)) or {}
            manifest_status = str(manifest.get("status", "") or "").strip()
        except Exception:
            manifest_status = ""

    product_name = Path(product_raw).name.lower()
    looks_manual_realized = "product_realized" in product_name or "realized_product" in product_name
    ran_standard_script = normalization_status == "generated" or manifest_status in {"generated", "failed_nonblocking"}

    if looks_manual_realized and normalization_status != "generated":
        return (
            f"低清烘焙产品图原始尺寸为 {source_size[0]}x{source_size[1]}，"
            "当前产品参考疑似手写/临时生成的 product_realized 文件。"
            "禁止绕过 Step 3.5 手动生成产品代理图；请先运行 normalize_product_reference.py，"
            "生成 product_reference_manifest.json 与 assets.product_normalization 后再组装 prompt。"
        )

    if not ran_standard_script:
        return (
            f"低清烘焙产品图原始尺寸为 {source_size[0]}x{source_size[1]}，"
            "必须先运行 Step 3.5 的 normalize_product_reference.py。"
            "该步骤会生成低频软代理，避免把低清孔洞/压缩纹理放大成木屑、蜂窝或鳞片感。"
        )

    return ""


def build_product_reference_proxy(product_path, project_dir, force=False):
    raw = str(product_path or '').strip()
    if not raw:
        return ''
    source = Path(raw)
    if not source.exists():
        return raw
    proxy_path = (project_dir / 'images' / f'{source.stem}_prompt_proxy.jpg').resolve()
    if proxy_path.exists() and not force:
        try:
            if proxy_path.stat().st_mtime >= source.stat().st_mtime:
                return str(proxy_path)
        except Exception:
            pass
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        with Image.open(source) as img:
            img = img.convert('RGB')
            # Suppress compression texture while keeping identity, shape, and broad material cues.
            softened = img.resize(
                (max(1, int(img.width * 0.72)), max(1, int(img.height * 0.72))),
                resample=Image.Resampling.LANCZOS,
            ).resize(img.size, resample=Image.Resampling.LANCZOS)
            softened = softened.filter(ImageFilter.GaussianBlur(radius=0.85))
            softened = ImageEnhance.Sharpness(softened).enhance(0.72)
            softened = ImageEnhance.Contrast(softened).enhance(0.94)
            softened = ImageEnhance.Color(softened).enhance(0.97)
            proxy_path.parent.mkdir(parents=True, exist_ok=True)
            softened.save(proxy_path, quality=96, subsampling=0)
        return str(proxy_path)
    except Exception:
        return raw


def product_hero_requested(brief):
    hero = brief.get("hero_priority", {}) or {}
    haystack = " ".join([
        str(hero.get("hero_1", "") or ""),
        str(brief.get("type", "") or ""),
        str(brief.get("product_name", "") or ""),
    ])
    return "产品" in haystack or "商品" in haystack


def distill_has_product_region(distill):
    if not distill:
        return False
    elements = (distill.get("layout_analysis", {}) or {}).get("elements", []) or []
    product_terms = ("product", "商品", "产品", "主视觉", "主体")
    for el in elements:
        raw_type = str(el.get("type", "") or "")
        resolved_type = _TYPE_ALIAS.get(raw_type, raw_type)
        name = str(el.get("name_zh", "") or el.get("id", "") or "")
        area = float(el.get("width", 0) or 0) * float(el.get("height", 0) or 0)
        label = f"{raw_type} {resolved_type} {name}".lower()
        if resolved_type == "product_photo" and area >= 250:
            return True
        if area >= 250 and any(term.lower() in label for term in product_terms):
            return True
    return False


def build_product_hero_layout_guard(brief, distill, refs, image_paths):
    product = refs.get("产品图") or {}
    product_path = str(product.get("路径", "") or "").strip()
    if not product_path or not product_hero_requested(brief) or distill_has_product_region(distill):
        return ""

    ref_num = get_ref_image_number(image_paths, product_path)
    img_ref = f"参考图[{ref_num}]" if ref_num >= 0 else "产品参考图"
    product_name = product.get("产品名", brief.get("product_name", "产品"))
    low_res = is_low_resolution_product_ref(brief, refs)

    if low_res:
        region = "x:24% y:38% 宽:52% 高:32% z:3"
        framing = (
            "采用完整产品中景肖像：产品仍是主视觉，但必须完整入画，能看见整体圆顶、外皮、侧面和底部，"
            "不允许从底部截断、只露出半个产品或裁成超近景切面；切面可见面积要克制，不能成为画面主纹理。"
            "轮廓、色彩和整体质感清楚，微观组织只保持轻微、柔和、可信。"
        )
    else:
        region = "x:14% y:31% 宽:72% 高:46% z:3"
        framing = "产品可以作为大主视觉，但仍需避免切面微距化和过度锐化。"

    return "\n".join([
        "== 产品主视觉区域 ==",
        "当前版式骨架没有单独标出产品主图区，因此必须显式建立产品主视觉锚点，不能让模型自行猜测产品位置。",
        f"将{img_ref}（{product_name}）作为第一视觉产品，放在标题/副标题下方、底部信息区上方的中部区域：{region}。",
        framing,
        "产品可以与满版背景自然融合并有柔和落影，但不要压住顶部文字、不要侵入底部说明文字，不要生成额外透明框、占位框或二维码框。",
        "如果产品参考、风格参考或创意描述与本区域冲突，以本产品主视觉区域为准；不要把产品挪到画面底部当作被裁切的巨大近景。",
    ])


def resolve_skeleton_reference(distill, distill_path):
    if not distill:
        return ""

    layout = distill.get("layout_analysis", {}) or {}
    skeleton_png = layout.get("skeleton_png") or ""
    skeleton_svg = layout.get("skeleton_image") or ""
    if not skeleton_png and not skeleton_svg:
        return ""

    distill_root = Path(distill_path).parent

    def resolve_path(raw_path):
        if not raw_path:
            return None
        path = Path(raw_path)
        if path.is_absolute():
            return path
        card_relative = distill_root / raw_path
        if card_relative.exists():
            return card_relative
        distiller_relative = DISTILLER_ROOT / raw_path
        if distiller_relative.exists():
            return distiller_relative
        return card_relative

    png_path = resolve_path(skeleton_png)
    svg_path = resolve_path(skeleton_svg)

    png_exists = bool(png_path and png_path.exists())
    svg_exists = bool(svg_path and svg_path.exists())

    if svg_exists:
        png_stale = (not png_exists) or (png_path.stat().st_mtime < svg_path.stat().st_mtime)
        if png_stale:
            distill_id = distill.get("id") or distill.get("distill_id") or Path(distill_path).stem
            svg_rel = skeleton_svg
            if not svg_rel and svg_path:
                try:
                    svg_rel = str(svg_path.relative_to(distill_root))
                except ValueError:
                    svg_rel = str(svg_path)
            regenerated = _export_skeleton_png(svg_rel, distill_id=distill_id)
            if regenerated:
                regenerated_path = resolve_path(regenerated)
                if regenerated_path and regenerated_path.exists():
                    return str(regenerated_path)
            return str(svg_path)

    if png_exists:
        return str(png_path)
    if svg_exists:
        return str(svg_path)
    return ""


def get_ratio_label(ratio):
    labels = {
        "2:3": "竖版 2:3 比例",
        "9:16": "竖版 9:16 比例",
        "1:1": "方形 1:1 比例",
        "16:9": "横版 16:9 比例",
        "3:4": "竖版 3:4 比例",
        "4:3": "横版 4:3 比例",
    }
    return labels.get(ratio, f"比例 {ratio}")


def get_festival_profile(brief):
    festival = brief.get("festival", "") or ""
    for key, profile in _FESTIVAL_SCENE_HINTS.items():
        if key in festival:
            return festival, profile
    return festival, None


def build_theme_anchor(brief, style_profile=None):
    festival, festival_profile = get_festival_profile(brief)
    poster_type = brief.get("type", "") or ""
    style_note = brief.get("style_note", "") or ""
    brand_name = brief.get("brand_name", "") or ""

    lines = ["== 主题场景锚点 =="]
    if festival:
        lines.append(f"本海报营销节点为「{festival}」，主题场景必须优先于参考图中的原始环境内容。")
    elif poster_type:
        lines.append(f"本海报目的为「{poster_type}」，画面内容必须服务于该主题，不得被参考图原场景带偏。")
    else:
        lines.append("本海报的主题场景必须优先于参考图中的原始环境内容。")

    if brand_name:
        lines.append(f"画面内容应服务于「{brand_name}」本次传播主题，先确定讲什么，再确定怎么画。")

    if festival_profile:
        lines.append(f"画面季节建议：{festival_profile['season']}；整体氛围：{festival_profile['mood']}。")
        lines.append(festival_profile["scene"] + "。")
        lines.append(festival_profile["action"] + "。")

    if style_note:
        lines.append(f"用户补充的风格/主题要求：{style_note}。")

    season_override_hint = (style_profile or {}).get("season_override_hint", "")
    if season_override_hint:
        lines.append(season_override_hint)
    else:
        lines.append("如参考图包含与本次营销节点不一致的季节、天气、场景或节庆道具，只继承其配色、质感、笔触和构图气质，不继承其具体内容设定。")

    return "\n".join(lines)


def build_main_visual_action_hint(brief):
    style_note = brief.get("style_note", "") or ""
    festival, festival_profile = get_festival_profile(brief)
    hero = brief.get("hero_priority", {})
    hero_name = hero.get("hero_1", "") or brief.get("hero_name", "") or "主角"

    if style_note and any(word in style_note for word in ["动作", "互动", "场景", "姿态", "庆祝", "玩耍"]):
        return f"主角动作和场景互动优先遵循用户要求：{style_note}"

    if festival_profile:
        return f"{hero_name}应围绕「{festival or '当前主题'}」展开明确互动，{festival_profile['action']}。"

    return "主体需要有明确动作和场景互动，不要只给静态站姿或空泛摆拍。"


def normalize_style_text(text, fallback):
    if not text:
        return fallback
    cleaned = str(text).strip()
    if cleaned.endswith("。"):
        cleaned = cleaned[:-1]
    return cleaned or fallback


def _contains_conflict_keyword(text, keywords):
    if not text:
        return False
    source = str(text)
    return any(keyword and keyword in source for keyword in keywords)


def sanitize_style_profile(style_profile, brief):
    if not style_profile:
        return style_profile

    sanitized = dict(style_profile)
    festival, festival_profile = get_festival_profile(brief)
    if not festival_profile:
        return sanitized

    conflict_terms = []
    for avoid_item in festival_profile.get("avoid", []):
        conflict_terms.extend(_SCENE_CONFLICT_HINTS.get(avoid_item, [avoid_item]))

    content_do_not_inherit = list(sanitized.get("content_do_not_inherit", []))
    seen_conflicts = set(content_do_not_inherit)

    def replace_conflicted_text(value, fallback):
        if _contains_conflict_keyword(value, conflict_terms):
            return fallback
        return value

    sanitized["background"] = replace_conflicted_text(
        sanitized.get("background", ""),
        f"以{festival_profile['season']}氛围为准的明亮背景，保留参考图的配色关系、空气感和留白节奏，不继承冲突季节场景",
    )
    sanitized["decorative"] = replace_conflicted_text(
        sanitized.get("decorative", ""),
        "装饰元素少而准，以轻量节日小道具和漂浮元素增强气氛，但不喧宾夺主",
    )
    sanitized["main_visual_style"] = replace_conflicted_text(
        sanitized.get("main_visual_style", ""),
        "主视觉保持参考图的笔触、配色和轮廓语言，但角色互动与场景动作必须服从当前营销节点",
    )

    color_values = []
    for color in sanitized.get("color", []) or []:
        if _contains_conflict_keyword(color, conflict_terms):
            conflict_label = next((item for item in festival_profile.get("avoid", []) if _contains_conflict_keyword(color, _SCENE_CONFLICT_HINTS.get(item, [item]))), color)
            if conflict_label not in seen_conflicts:
                content_do_not_inherit.append(conflict_label)
                seen_conflicts.add(conflict_label)
            continue
        color_values.append(color)
    sanitized["color"] = color_values

    mood_values = []
    for mood in sanitized.get("mood", []) or []:
        if _contains_conflict_keyword(mood, conflict_terms):
            continue
        mood_values.append(mood)
    sanitized["mood"] = mood_values

    sanitized["content_do_not_inherit"] = content_do_not_inherit
    sanitized.setdefault(
        "season_override_hint",
        f"若参考图风格描述与「{festival or '当前主题'}」的季节或场景冲突，以 brief 为准，只保留风格不保留场景。",
    )
    return sanitized


def assemble_hero_priority(brief):
    hero = brief.get("hero_priority", {}) or {}
    lines = []
    hero_1 = hero.get("hero_1", "")
    hero_2 = hero.get("hero_2", "")
    forbidden = hero.get("forbidden_hero", "")
    if hero_1 or hero_2 or forbidden:
        lines.append("== 主视觉层级 ==")
        if hero_1:
            lines.append(f"第一视觉主角：{hero_1}。")
        if hero_2:
            lines.append(f"辅助陪衬元素：{hero_2}。")
        if forbidden:
            lines.append(f"禁止作为主视觉：{forbidden}。")
    return "\n".join(lines)


def assemble_ref_image_refs(refs, style_profile=None):
    """
    组装参考图说明区块。
    排序：风格参考 → 骨架图 → 产品图 → 产品质地参考 → IP 图 → Logo
    每个说明 ≤ 30 字，一句话角色声明。
    返回 (说明文本列表, 按生图命令顺序的图片路径列表, 参考图角色信息列表)
    """
    lines = []
    image_paths = []
    ref_roles = []  # [{"index": N, "role": "style_ref|skeleton|product|product_texture|ip|logo", "path": "..."}]

    # 1. 风格参考图（最优先 — 决定画面气质）
    style_refs = refs.get("风格参考图", [])
    for i, sr in enumerate(style_refs):
        idx = len(image_paths)
        display_idx = idx + 1
        path = sr.get("路径", "")
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "style_ref", "path": path})
        lines.append(
            f"参考图[{display_idx}] 风格参考：只参考这张图的配色关系、材质质感、笔触语言与氛围表达，不继承其中具体季节、天气、场景、道具或叙事内容。"
        )

    # 2. 骨架图（只约束构图结构）
    skeleton = refs.get("版式骨架图")
    if skeleton and skeleton.get("路径"):
        idx = len(image_paths)
        display_idx = idx + 1
        path = skeleton["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "skeleton", "path": path})
        lines.append(f"参考图[{display_idx}] 骨架图：严格按此构图和各区域比例布局。")

    # 3. 产品图
    product = refs.get("产品图")
    if product and product.get("路径"):
        idx = len(image_paths)
        display_idx = idx + 1
        path = product["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "product", "path": path})
        name = product.get("产品名", product.get("角色说明", "产品"))
        lines.append(f"参考图[{display_idx}] 产品图：产品外观保真，形体、颜色、质感与包装关系以该参考为准。")

    # 4. 产品质地参考图
    texture_refs = product_texture_refs(refs)
    for texture_ref in texture_refs:
        if not texture_ref or not texture_ref.get("路径"):
            continue
        idx = len(image_paths)
        display_idx = idx + 1
        path = texture_ref["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "product_texture", "path": path})
        lines.append(
            f"参考图[{display_idx}] 产品质地参考：只参考面包切面组织、孔隙尺度、湿润感和柔软边缘，不继承产品身份、颜色、造型、背景或摆拍。"
        )

    # 5. IP 图
    ip_ref = refs.get("IP")
    if ip_ref and ip_ref.get("路径"):
        idx = len(image_paths)
        display_idx = idx + 1
        path = ip_ref["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "ip", "path": path})
        lines.append(f"参考图[{display_idx}] IP 角色：角色外观保真（配色、面部特征、身体比例），姿态可自由发挥。")

    # 6. Logo
    logo = refs.get("Logo")
    if logo and logo.get("路径"):
        idx = len(image_paths)
        display_idx = idx + 1
        path = logo["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "logo", "path": path})
        lines.append(f"参考图[{display_idx}] 品牌 Logo：官方 Logo 文件，必须原样使用，不得自行绘制。")

    return lines, image_paths, ref_roles


def get_ref_image_number(image_paths, image_path):
    """根据图片路径在 image_paths 列表中的位置，返回 prompt 展示编号（1-based）。"""
    for i, p in enumerate(image_paths):
        if p == image_path:
            return i + 1
    target_stem = Path(image_path).stem
    for i, p in enumerate(image_paths):
        if Path(p).stem == target_stem:
            return i + 1
    return -1


def validate_ref_roles(brief, refs, ref_roles):
    """校验参考图角色挂载，阻断 product/IP 错挂。"""
    issues = []
    assets = brief.get("assets", {}) or {}
    hero = brief.get("hero_priority", {}) or {}
    hero1 = str(hero.get("hero_1", "") or "")

    product = refs.get("产品图", {}) or {}
    ip_ref = refs.get("IP", {}) or {}
    product_path = str(product.get("路径", "") or "").strip()
    ip_path = str(ip_ref.get("路径", "") or "").strip()
    product_name = str(product.get("产品名", "") or "").strip()
    product_asset = str(assets.get("product", "") or "").strip()
    ip_asset = str(assets.get("ip", "") or "").strip()

    def _looks_like_ip(value):
        text = str(value or "").lower()
        return any(token in text for token in ("ip", "角色", "吉祥物", "mascot", "character"))

    if "产品" in hero1 and not product_asset:
        issues.append("hero_1 已指定为产品，但 brief.assets.product 为空，不能继续生成 prompt。")

    if product_path and ip_path and product_path == ip_path:
        issues.append("产品图与 IP 图引用了同一路径，说明角色挂载冲突。")

    if product_name and _looks_like_ip(product_name):
        issues.append(f"产品图名称疑似写成了 IP 角色：{product_name}")

    if product_asset and ip_asset and product_asset == ip_asset:
        issues.append("brief.assets.product 与 brief.assets.ip 指向同一路径，素材角色未分离。")

    for item in ref_roles:
        role = item.get("role", "")
        path = str(item.get("path", "") or "")
        if role == "product" and _looks_like_ip(Path(path).name):
            issues.append(f"ref_order 中的 product 路径疑似 IP 文件：{path}")
        if role == "ip" and ("product" in Path(path).name.lower() or "产品" in Path(path).name):
            issues.append(f"ref_order 中的 ip 路径疑似产品文件：{path}")

    return issues


def build_creative_direction_block(creative_direction):
    if not creative_direction:
        return ""

    lines = ["== 画面创意表达锚点 =="]

    summary = str(creative_direction.get("summary", "") or "").strip()
    scene_concept = str(creative_direction.get("scene_concept", "") or "").strip()
    hero_focus = str(creative_direction.get("hero_focus", "") or "").strip()
    supporting_elements = creative_direction.get("supporting_elements", []) or []
    composition_plan = str(creative_direction.get("composition_plan", "") or "").strip()
    text_visual_relationship = str(creative_direction.get("text_visual_relationship", "") or "").strip()
    style_translation = str(creative_direction.get("style_translation", "") or "").strip()
    must_hit = creative_direction.get("must_hit", []) or []
    must_avoid = creative_direction.get("must_avoid", []) or []

    if summary:
        lines.append(f"核心表达：{summary}")
    if scene_concept:
        lines.append(f"场景概念：{scene_concept}")
    if hero_focus:
        lines.append(f"主视觉焦点：{hero_focus}")
    if supporting_elements:
        lines.append("氛围陪衬：" + "；".join(str(item).strip() for item in supporting_elements if str(item).strip()))
    if composition_plan:
        lines.append(f"构图关系：{composition_plan}")
    if text_visual_relationship:
        lines.append(f"文案与画面关系：{text_visual_relationship}")
    if style_translation:
        lines.append(f"风格转译：{style_translation}")
    if must_hit:
        lines.append("必须打中的表达要点：" + "；".join(str(item).strip() for item in must_hit if str(item).strip()))
    if must_avoid:
        lines.append("必须避免的表达偏差：" + "；".join(str(item).strip() for item in must_avoid if str(item).strip()))

    if len(lines) == 1:
        return ""
    return "\n".join(lines)


def describe_element(el, copywriting, refs, image_paths, brief=None, style_profile=None):
    """为单个蒸馏卡元素生成精确视觉描述。"""
    el_type = el.get("type", "")
    el_name = el.get("name_zh", el_type)
    x = el.get("x", 0)
    y = el.get("y", 0)
    w = el.get("width", 0)
    h = el.get("height", 0)
    z = el.get("z_index", 1)
    direction = el.get("排版方向", "")
    el_id = el.get("id", "")

    resolved_type = _TYPE_ALIAS.get(el_type, el_type)

    cw = copywriting.get(el_id, {}) if copywriting else {}
    text = cw.get("文案", "")
    font_style = cw.get("字体风格", "")

    header = f"【区域 {el_id} - {el_name}】x:{x:.0f}% y:{y:.0f}% 宽:{w:.0f}% 高:{h:.0f}% z:{z}"

    if resolved_type == "background":
        if style_profile and style_profile.get("background"):
            desc = normalize_style_text(style_profile["background"], "与风格参考图保持一致的背景")
            return f"{header}\n{desc}。背景内容仍需服从本次营销节点，不得直接沿用参考图中的原季节场景。"
        return f"{header}\n与风格参考图保持一致的背景，但背景内容必须服从当前主题场景。"

    elif resolved_type == "product_photo":
        area = w * h
        if area < 400:
            if style_profile and style_profile.get("decorative"):
                desc = normalize_style_text(style_profile["decorative"], "与整体风格协调的装饰元素，不喧宾夺主")
                return f"{header}\n{desc}。"
            return f"{header}\n与整体风格协调的装饰元素，不喧宾夺主。"

        product = refs.get("产品图", {})
        product_name = product.get("产品名", product.get("产品名", "主体"))
        product_path = product.get("路径", "")
        ref_num = get_ref_image_number(image_paths, product_path) if product_path else -1
        action_hint = build_main_visual_action_hint(brief or {})

        if ref_num >= 0:
            img_ref = f"参考图[{ref_num}]"
        else:
            img_ref = "参考图中的主体图"

        low_res_note = ""
        if product_path and is_low_resolution_product_ref(brief or {}, refs):
            low_res_note = (
                "该产品参考图只锁定身份、轮廓、颜色和基础材质，不把压缩像素当作微观纹理；"
                "产品可以是主视觉，但必须完整中景入画，不要裁成切面微距；"
                "切面和表面细节必须自然柔和、低局部对比、非均匀分布，不要木屑感、鳞片感或过度锐化。"
            )

        return (
            f"{header}\n"
            f"将{img_ref}（{product_name}）作为画面第一视觉主体，"
            f"放置在此区域中心。外观保真，不照抄参考图原始场景。{action_hint}{low_res_note}"
        )

    elif resolved_type == "title":
        direction_text = "横排" if "横" in (direction or "横") else "竖排"
        if font_style:
            if len(font_style) > 20 or font_style.endswith('。') or font_style.endswith('.'):
                font_desc = f"使用{font_style}"
            else:
                font_desc = f"使用{font_style}的中文字体"
        else:
            font_desc = "使用大气端庄的中文字体"
        return (
            f"{header}\n"
            f"在此区域{direction_text}生成主标题文字：「{text}」。"
            f"字号大，占据此区域主要空间，{font_desc}，"
            f"文字必须有实际含义，不可生成伪文字或乱码。"
        )

    elif resolved_type == "subtitle":
        direction_text = "横排" if "横" in (direction or "横") else "竖排"
        return (
            f"{header}\n"
            f"在此区域{direction_text}生成副标题文字：「{text}」。"
            f"字号小于主标题。"
        )

    elif resolved_type == "body_text":
        if direction and ("竖" in direction):
            dir_text = "从上到下竖排"
        elif w < 10 and h > 15:
            dir_text = "从上到下竖排"
        else:
            dir_text = "从左到右横排"
        return (
            f"{header}\n"
            f"在此区域生成文案：「{text}」。文字{dir_text}。"
        )

    elif resolved_type == "decorative":
        if style_profile and style_profile.get("decorative"):
            desc = normalize_style_text(style_profile["decorative"], "与整体风格协调的装饰元素，不喧宾夺主")
            return f"{header}\n{desc}。装饰内容仍需服从当前主题场景，不得直接复制参考图原始季节元素。"
        return (
            f"{header}\n"
            f"与整体风格协调的装饰元素，不喧宾夺主。"
        )

    elif resolved_type == "logo":
        logo = refs.get("Logo", {})
        logo_path = logo.get("路径", "")
        ref_num = get_ref_image_number(image_paths, logo_path) if logo_path else -1
        if ref_num >= 0:
            return (
                f"{header}\n"
                f"使用参考图[{ref_num}]的官方 Logo 文件，"
                f"放置在此区域，不得自行生成或改写。"
            )
        return f"{header}\n使用官方 Logo 文件，放置在此区域，不得自行生成。"

    elif resolved_type == "qr_code":
        return f"{header}\n不需要生成二维码；此区域完全留白或只保留自然背景纹理。不要画二维码、边框、占位框、半透明矩形或按钮框。"

    else:
        if style_profile and style_profile.get("main_visual_style"):
            desc = normalize_style_text(style_profile["main_visual_style"], f"以整体风格呈现的{el_name}元素")
            return f"{header}\n{desc}。内容语义仍需服从当前主题。"
        return f"{header}\n{el_name}元素，按主题风格自然放置。"


def validate_prompt(prompt, distill, copywriting, creative_direction=None):
    """
    校验 assembled prompt 质量。
    返回 (blocking_errors, warnings) 两个列表。
    blocking_errors: 必须修复才能继续的致命错误
    warnings: 质量提醒，不阻塞流程
    """
    blocking_errors = []
    warnings = []

    # 工作流术语检查 → blocking（这些术语不应该出现在 prompt 中）
    for word in _FORBIDDEN_WORDS:
        if word in prompt:
            blocking_errors.append(f"发现工作流术语: 「{word}」")

    # 蒸馏卡坐标覆盖率检查 → blocking
    if distill:
        elements = distill.get("layout_analysis", {}).get("elements", [])
        if elements and "x:" not in prompt:
            blocking_errors.append("有蒸馏卡但 prompt 中未出现坐标数据")
        for el in elements:
            el_id = el.get("id", "")
            if el_id and el_id not in prompt:
                warnings.append(f"元素 {el_id} 未在 prompt 中出现")

    # 文案覆盖率检查 → blocking（用户确认的文案必须出现）
    if copywriting:
        for el_id, cw in copywriting.items():
            text = cw.get("文案", "")
            if text and text not in prompt:
                blocking_errors.append(f"元素 {el_id} 的文案「{text}」未在 prompt 中出现")

    # creative_direction 字段检查 → warning（这些是质量增强字段，不是必需的）
    if creative_direction:
        summary = str(creative_direction.get("summary", "") or "").strip()
        hero_focus = str(creative_direction.get("hero_focus", "") or "").strip()
        composition_plan = str(creative_direction.get("composition_plan", "") or "").strip()
        if not summary:
            warnings.append("creative_direction 缺少 summary，建议补充核心表达")
        if not hero_focus:
            warnings.append("creative_direction 缺少 hero_focus，建议补充主视觉焦点")
        if not composition_plan:
            warnings.append("creative_direction 缺少 composition_plan，建议补充构图关系")

    # prompt 长度检查 → warning（长度问题不应该阻塞流程）
    if len(prompt) < 200:
        warnings.append(f"prompt 过短（{len(prompt)} 字符），可能缺失关键信息")
    if len(prompt) > 7000:
        warnings.append(f"prompt 过长（{len(prompt)} 字符），建议精简")

    return blocking_errors, warnings


def assemble_prompt(brief, distill, copywriting, refs, style_profile=None, creative_direction=None):
    """主组装逻辑。"""
    blocks = []
    style_profile = sanitize_style_profile(style_profile, brief)

    ratio = brief.get("ratio", "2:3")
    blocks.append(f"这是一张{get_ratio_label(ratio)}的满版品牌海报。画面采用 100% 宽高画布。")

    creative_block = build_creative_direction_block(creative_direction)
    if creative_block:
        blocks.append(creative_block)

    if style_profile:
        style_lines = ["== 画面风格调性 =="]
        if style_profile.get("overall_mood"):
            style_lines.append(f"整体气质：{style_profile['overall_mood']}")
        if style_profile.get("color"):
            style_lines.append(f"色彩关系：{', '.join(style_profile['color'])}")
        if style_profile.get("material"):
            style_lines.append(f"画面质感：{', '.join(style_profile['material'])}")
        if style_profile.get("avoid"):
            style_lines.append(f"避免风格：{', '.join(style_profile['avoid'])}")
        if len(style_lines) > 1:
            blocks.append("\n".join(style_lines))

    theme_anchor = build_theme_anchor(brief, style_profile=style_profile)
    if theme_anchor:
        blocks.append(theme_anchor)

    bakery_guard = build_bakery_texture_guard(brief)
    if bakery_guard:
        blocks.append(bakery_guard)

    product_guard = build_product_reference_guard(brief, refs)
    if product_guard:
        blocks.append(product_guard)

    lowres_bakery_strategy = build_lowres_bakery_visual_strategy(brief, refs)
    if lowres_bakery_strategy:
        blocks.append(lowres_bakery_strategy)

    ref_lines, image_paths, ref_roles = assemble_ref_image_refs(refs, style_profile=style_profile)
    if ref_lines:
        blocks.append("== 参考图说明 ==")
        blocks.extend(ref_lines)

    product_layout_guard = build_product_hero_layout_guard(brief, distill, refs, image_paths)
    if product_layout_guard:
        blocks.append(product_layout_guard)

    hero_block = assemble_hero_priority(brief)
    if hero_block:
        blocks.append(hero_block)

    if distill:
        elements = distill.get("layout_analysis", {}).get("elements", [])
        if elements:
            blocks.append("== 画面布局（严格按以下坐标）==")
            blocks.append("")
            for el in elements:
                desc = describe_element(el, copywriting, refs, image_paths, brief=brief, style_profile=style_profile)
                blocks.append(desc)
                blocks.append("")
        else:
            blocks.append(assemble_fallback_layout(brief, copywriting))
    else:
        blocks.append(assemble_fallback_layout(brief, copywriting))

    constraints = []
    if distill:
        nc = distill.get("layout_analysis", {}).get("negative_constraints", [])
        constraints.extend(nc)

    taboos = brief.get("taboos", "")
    if taboos:
        if isinstance(taboos, list):
            constraints.extend(taboos)
        else:
            constraints.append(taboos)

    festival, festival_profile = get_festival_profile(brief)

    if style_profile:
        constraints.extend(style_profile.get("avoid", []))
        festival_avoid = set((festival_profile or {}).get("avoid", []))
        for item in style_profile.get("content_do_not_inherit", []):
            if item in festival_avoid:
                continue
            constraints.append(f"不要出现{item}相关的场景或意象")

    if festival_profile:
        constraints.extend([f"不要出现{item}" for item in festival_profile.get("avoid", [])])
        if festival:
            constraints.append(f"不要让参考图中的原始环境覆盖「{festival}」主题场景")

    constraints.append("满版效果，不要出现外边框或白色卡片感")

    product = refs.get("产品图", {})
    if product and product.get("路径"):
        product_name = product.get("产品名", "")
        if "IP" in product_name or "角色" in product_name:
            constraints.append("IP 角色的配色和身体比例保持与参考图一致，但场景内容以本次主题为准")
        else:
            constraints.append("产品外观必须保真，不得变形或改变配色")

    logo = refs.get("Logo", {})
    if logo and logo.get("路径"):
        constraints.append("Logo 必须使用官方原文件，不得自行绘制")

    constraints = [c for c in constraints if c and str(c).strip() and str(c).strip() not in ('无', 'none', 'None', 'N/A')]

    seen = set()
    unique_constraints = []
    for c in constraints:
        normalized = str(c).strip()
        if normalized not in seen:
            seen.add(normalized)
            unique_constraints.append(normalized)

    if unique_constraints:
        blocks.append("== 负面约束 ==")
        for c in unique_constraints:
            blocks.append(f"- {c}")

    return "\n\n".join(
        block.strip() for block in blocks if block.strip()
    ), image_paths, ref_roles


def assemble_fallback_layout(brief, copywriting):
    """无蒸馏卡时的降级布局描述。"""
    lines = ["== 画面布局（无固定版式，以风格参考和文案描述为主） =="]
    lines.append("")
    lines.append("画面主体居中放置，占画面主导地位。")
    lines.append(build_main_visual_action_hint(brief))

    if copywriting:
        for el_id, cw in copywriting.items():
            text = cw.get("文案", "")
            if text:
                lines.append(f"文案：「{text}」，放置在画面适当位置。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Prompt 精确装配器")
    parser.add_argument("--brief", required=True, help="brief.json 路径")
    parser.add_argument("--distill", default="", help="distill_card.json 路径（可选）")
    parser.add_argument("--copywriting", default="", help="copywriting.json 路径（可选）")
    parser.add_argument("--refs", default="", help="references.json 路径（可选，如不提供则从 brief.json 的 assets 字段读取）")
    parser.add_argument("--style-profile", default="", help="style_profile.json 路径（可选，参考图风格提炼结果）")
    parser.add_argument("--creative-direction", default="", help="creative_direction.json 路径（可选，画面创意表达方案）")
    parser.add_argument("--output", required=True, help="输出 prompt_draft.md 路径")
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    project_dir = output_path.parent
    manager = ProjectManager(project_dir)
    attempt = manager.start_stage('prompt', reason='组装生图 prompt', actor='assemble_prompt.py')

    brief = load_json(args.brief)
    if not brief:
        error = f"无法读取 brief.json: {args.brief}"
        manager.fail_stage(
            'prompt',
            error=error,
            actor='assemble_prompt.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'error_summary': error,
                'brief_path': str(Path(args.brief).resolve()),
                'distill_path': str(Path(args.distill).resolve()) if args.distill else '',
                'copywriting_path': str(Path(args.copywriting).resolve()) if args.copywriting else '',
                'style_profile_path': str(Path(args.style_profile).resolve()) if args.style_profile else '',
                'creative_direction_path': str(Path(args.creative_direction).resolve()) if args.creative_direction else '',
                'output_path': str(output_path),
                'ref_order_path': str(project_dir / 'ref_order.json'),
                'user_confirmed': False,
                'history': [{
                    'ts': manager.state['updated_at'],
                    'event': 'prompt_assembly_failed',
                    'reason': error,
                }],
            },
            files=['prompt_manifest.json'],
        )
        print(f"ERROR: {error}")
        sys.exit(1)

    distill = load_json(args.distill) if args.distill else None
    copywriting = load_json(args.copywriting) if args.copywriting else None
    style_profile = load_json(args.style_profile) if args.style_profile else None
    creative_direction = load_json(args.creative_direction) if args.creative_direction else None

    product_normalization_issue = validate_product_normalization_gate(brief, project_dir)
    if product_normalization_issue:
        error = product_normalization_issue
        manager.fail_stage(
            'prompt',
            error=error,
            actor='assemble_prompt.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'error_summary': error,
                'brief_path': str(Path(args.brief).resolve()),
                'output_path': str(output_path),
                'ref_order_path': str(project_dir / 'ref_order.json'),
                'user_confirmed': False,
                'history': [{
                    'ts': manager.state['updated_at'],
                    'event': 'prompt_assembly_failed',
                    'reason': error,
                }],
            },
            files=['prompt_manifest.json'],
        )
        print(f"ERROR: {error}")
        sys.exit(1)

    refs = {}
    if args.refs and os.path.exists(args.refs):
        with open(args.refs, "r", encoding="utf-8") as f:
            refs = json.load(f)
    else:
        assets = brief.get("assets", {})
        style_refs = assets.get("style_refs", [])
        if style_refs:
            if isinstance(style_refs, list):
                refs["风格参考图"] = [{"来源": "用户上传", "路径": p} for p in style_refs]
            else:
                refs["风格参考图"] = [{"来源": "用户上传", "路径": style_refs}]

        if assets.get("logo"):
            refs["Logo"] = {"路径": assets["logo"], "角色说明": "品牌官方 Logo"}

        texture_assets = assets.get("product_texture_refs", [])
        if texture_assets:
            if isinstance(texture_assets, list):
                refs["产品质地参考图"] = [{"来源": "用户上传", "路径": p} for p in texture_assets]
            else:
                refs["产品质地参考图"] = [{"来源": "用户上传", "路径": texture_assets}]

        if assets.get("product"):
            product_ref_path = normalize_ref_path(assets["product"], project_dir)
            product_size = read_image_size(product_ref_path)
            if product_size and min(product_size) < 900 and is_bakery_product(brief) and not texture_assets:
                product_ref_path = build_product_reference_proxy(product_ref_path, project_dir)
            refs["产品图"] = {
                "路径": product_ref_path,
                "产品名": brief.get("product_name", "产品"),
                "角色说明": "画面主体产品",
            }

        if assets.get("ip"):
            refs["IP"] = {
                "路径": assets["ip"],
                "产品名": brief.get("hero_name", "IP 角色"),
                "角色说明": "画面辅助 IP",
            }

    if distill:
        skeleton_path = resolve_skeleton_reference(distill, args.distill)
        if skeleton_path:
            refs["版式骨架图"] = {"路径": skeleton_path, "角色说明": "版式骨架图"}

    refs = normalize_refs(refs, project_dir)

    style_ref_issues = validate_style_refs(brief, refs, project_dir)
    if style_ref_issues:
        error = '；'.join(style_ref_issues)
        manager.fail_stage(
            'prompt',
            error=error,
            actor='assemble_prompt.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'error_summary': error,
                'brief_path': str(Path(args.brief).resolve()),
                'distill_path': str(Path(args.distill).resolve()) if args.distill else '',
                'copywriting_path': str(Path(args.copywriting).resolve()) if args.copywriting else '',
                'style_profile_path': str(Path(args.style_profile).resolve()) if args.style_profile else '',
                'creative_direction_path': str(Path(args.creative_direction).resolve()) if args.creative_direction else '',
                'output_path': str(output_path),
                'ref_order_path': str(project_dir / 'ref_order.json'),
                'user_confirmed': False,
                'history': [{
                    'ts': manager.state['updated_at'],
                    'event': 'prompt_assembly_failed',
                    'reason': error,
                }],
            },
            files=['prompt_manifest.json'],
        )
        print(f"ERROR: {error}")
        sys.exit(1)

    prompt, image_paths, ref_roles = assemble_prompt(
        brief,
        distill,
        copywriting,
        refs,
        style_profile=style_profile,
        creative_direction=creative_direction,
    )

    role_issues = validate_ref_roles(brief, refs, ref_roles)
    if role_issues:
        error = '；'.join(role_issues)
        manager.fail_stage(
            'prompt',
            error=error,
            actor='assemble_prompt.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'error_summary': error,
                'brief_path': str(Path(args.brief).resolve()),
                'distill_path': str(Path(args.distill).resolve()) if args.distill else '',
                'copywriting_path': str(Path(args.copywriting).resolve()) if args.copywriting else '',
                'style_profile_path': str(Path(args.style_profile).resolve()) if args.style_profile else '',
                'creative_direction_path': str(Path(args.creative_direction).resolve()) if args.creative_direction else '',
                'output_path': str(output_path),
                'ref_order_path': str(project_dir / 'ref_order.json'),
                'user_confirmed': False,
                'history': [{
                    'ts': manager.state['updated_at'],
                    'event': 'prompt_assembly_failed',
                    'reason': error,
                }],
            },
            files=['prompt_manifest.json'],
            extra={'role_issues': role_issues},
        )
        print("ERROR: 参考图角色校验失败:")
        for issue in role_issues:
            print(f"  - {issue}")
        sys.exit(1)

    blocking_errors, warnings = validate_prompt(prompt, distill, copywriting, creative_direction=creative_direction)

    # 只有 blocking_errors 才阻塞流程
    if blocking_errors:
        error = '；'.join(blocking_errors)
        manager.fail_stage(
            'prompt',
            error=error,
            actor='assemble_prompt.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'error_summary': error,
                'brief_path': str(Path(args.brief).resolve()),
                'distill_path': str(Path(args.distill).resolve()) if args.distill else '',
                'copywriting_path': str(Path(args.copywriting).resolve()) if args.copywriting else '',
                'style_profile_path': str(Path(args.style_profile).resolve()) if args.style_profile else '',
                'creative_direction_path': str(Path(args.creative_direction).resolve()) if args.creative_direction else '',
                'output_path': str(output_path),
                'ref_order_path': str(project_dir / 'ref_order.json'),
                'user_confirmed': False,
                'history': [{
                    'ts': manager.state['updated_at'],
                    'event': 'prompt_assembly_failed',
                    'reason': error,
                }],
            },
            files=['prompt_manifest.json'],
            extra={'blocking_errors': blocking_errors, 'warnings': warnings},
        )
        print("ERROR: 校验失败（阻塞性错误）:")
        for issue in blocking_errors:
            print(f"  - {issue}")
        sys.exit(1)

    # warnings 只打印，不阻塞流程
    if warnings:
        print("WARNING: 校验发现质量提醒（不影响生成）:")
        for warning in warnings:
            print(f"  - {warning}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt, encoding="utf-8")
    print(f"OK: prompt 已写入 {output_path}")
    print(f"  字符数: {len(prompt)}")
    print(f"  参考图数量: {len(image_paths)}")
    for i, p in enumerate(image_paths):
        print(f"  参考图[{i + 1}]: {p}")

    ref_order_path = output_path.parent / "ref_order.json"
    ref_order_data = {"ref_order": ref_roles}
    ref_order_path.write_text(json.dumps(ref_order_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ref_order.json 已写入 {ref_order_path}")

    manager.complete_stage(
        'prompt',
        reason='Prompt 与参考图顺序已生成，等待用户确认生图。',
        actor='assemble_prompt.py',
        manifest_payload={
            'status': 'generated',
            'attempt': attempt,
            'brief_path': str(Path(args.brief).resolve()),
            'distill_path': str(Path(args.distill).resolve()) if args.distill else '',
            'copywriting_path': str(Path(args.copywriting).resolve()) if args.copywriting else '',
            'style_profile_path': str(Path(args.style_profile).resolve()) if args.style_profile else '',
            'creative_direction_path': str(Path(args.creative_direction).resolve()) if args.creative_direction else '',
            'output_path': str(output_path),
            'ref_order_path': str(ref_order_path),
            'reference_count': len(image_paths),
            'reference_roles': ref_roles,
            'blocking_errors': [],
            'warnings': warnings,
            'user_confirmed': False,
            'history': [{
                'ts': manager.state['updated_at'],
                'event': 'prompt_assembled',
                'reference_count': len(image_paths),
            }],
        },
        flags={'prompt_ready': True},
        artifacts={
            'prompt': str(output_path),
            'ref_order': str(ref_order_path),
        },
        files=[manager._relative(output_path), manager._relative(ref_order_path)],
        extra={'reference_count': len(image_paths)},
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
