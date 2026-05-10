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


def assemble_ref_image_refs(refs, style_profile=None):
    """
    组装参考图说明区块。
    排序：风格参考 → 骨架图 → 产品图 → IP 图 → Logo
    每个说明 ≤ 30 字，一句话角色声明。
    返回 (说明文本列表, 按生图命令顺序的图片路径列表, 参考图角色信息列表)
    """
    lines = []
    image_paths = []
    ref_roles = []  # [{"index": N, "role": "style_ref|skeleton|product|ip|logo", "path": "..."}]

    # 1. 风格参考图（最优先 — 决定画面气质）
    style_refs = refs.get("风格参考图", [])
    for i, sr in enumerate(style_refs):
        idx = len(image_paths)
        path = sr.get("路径", "")
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "style_ref", "path": path})
        lines.append(
            f"参考图[{idx}] 风格参考：只参考这张图的配色关系、材质质感、笔触语言与氛围表达，不继承其中具体季节、天气、场景、道具或叙事内容。"
        )

    # 2. 骨架图（只约束构图结构）
    skeleton = refs.get("版式骨架图")
    if skeleton and skeleton.get("路径"):
        idx = len(image_paths)
        path = skeleton["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "skeleton", "path": path})
        lines.append(f"参考图[{idx}] 骨架图：严格按此构图和各区域比例布局。")

    # 3. 产品图
    product = refs.get("产品图")
    if product and product.get("路径"):
        idx = len(image_paths)
        path = product["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "product", "path": path})
        name = product.get("产品名", product.get("角色说明", "产品"))
        lines.append(f"参考图[{idx}] 产品图：产品外观保真，形体、颜色、质感与包装关系以该参考为准。")

    # 4. IP 图
    ip_ref = refs.get("IP")
    if ip_ref and ip_ref.get("路径"):
        idx = len(image_paths)
        path = ip_ref["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "ip", "path": path})
        lines.append(f"参考图[{idx}] IP 角色：角色外观保真（配色、面部特征、身体比例），姿态可自由发挥。")

    # 5. Logo
    logo = refs.get("Logo")
    if logo and logo.get("路径"):
        idx = len(image_paths)
        path = logo["路径"]
        image_paths.append(path)
        ref_roles.append({"index": idx, "role": "logo", "path": path})
        lines.append(f"参考图[{idx}] 品牌 Logo：官方 Logo 文件，必须原样使用，不得自行绘制。")

    return lines, image_paths, ref_roles


def get_ref_image_number(image_paths, image_path):
    """根据图片路径在 image_paths 列表中的位置，返回参考图编号。"""
    for i, p in enumerate(image_paths):
        if p == image_path:
            return i
    target_stem = Path(image_path).stem
    for i, p in enumerate(image_paths):
        if Path(p).stem == target_stem:
            return i
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


def assemble_hero_priority(brief):
    """组装视觉权力结构 — 只保留纯视觉指令，无工作流术语。"""
    hero = brief.get("hero_priority", {})
    if not hero:
        return ""
    lines = []
    hero1 = hero.get("hero_1", "")
    hero2 = hero.get("hero_2", "")
    forbidden = hero.get("forbidden_hero", "")
    if hero1:
        lines.append(f"- 画面绝对主角：{hero1}，占据画面主导地位")
    if hero2:
        lines.append(f"- 陪衬元素：{hero2}，不喧宾夺主，不占主位")
    if forbidden:
        lines.append(f"- 禁止作为主视觉：{forbidden}，不得在画面中作为突出元素出现")
    if not lines:
        return ""
    return "== 视觉权力结构 ==\n" + "\n".join(lines)


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

        return (
            f"{header}\n"
            f"将{img_ref}（{product_name}）作为画面第一视觉主体，"
            f"放置在此区域中心。外观保真，不照抄参考图原始场景。{action_hint}"
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
        return f"{header}\n不需要生成二维码，此区域留白或放置轻量装饰。"

    else:
        if style_profile and style_profile.get("main_visual_style"):
            desc = normalize_style_text(style_profile["main_visual_style"], f"以整体风格呈现的{el_name}元素")
            return f"{header}\n{desc}。内容语义仍需服从当前主题。"
        return f"{header}\n{el_name}元素，按主题风格自然放置。"


def validate_prompt(prompt, distill, copywriting):
    """校验 assembled prompt 质量。"""
    issues = []

    for word in _FORBIDDEN_WORDS:
        if word in prompt:
            issues.append(f"发现工作流术语: 「{word}」")

    if distill:
        elements = distill.get("layout_analysis", {}).get("elements", [])
        if elements and "x:" not in prompt:
            issues.append("有蒸馏卡但 prompt 中未出现坐标数据")
        for el in elements:
            el_id = el.get("id", "")
            if el_id and el_id not in prompt:
                issues.append(f"元素 {el_id} 未在 prompt 中出现")

    if copywriting:
        for el_id, cw in copywriting.items():
            text = cw.get("文案", "")
            if text and text not in prompt:
                issues.append(f"元素 {el_id} 的文案「{text}」未在 prompt 中出现")

    if len(prompt) < 200:
        issues.append(f"prompt 过短（{len(prompt)} 字符），可能缺失关键信息")
    if len(prompt) > 7000:
        issues.append(f"prompt 过长（{len(prompt)} 字符），建议精简")

    return issues


def assemble_prompt(brief, distill, copywriting, refs, style_profile=None):
    """主组装逻辑。"""
    blocks = []
    style_profile = sanitize_style_profile(style_profile, brief)

    ratio = brief.get("ratio", "2:3")
    blocks.append(f"这是一张{get_ratio_label(ratio)}的满版品牌海报。画面采用 100% 宽高画布。")

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

    ref_lines, image_paths, ref_roles = assemble_ref_image_refs(refs, style_profile=style_profile)
    if ref_lines:
        blocks.append("== 参考图说明 ==")
        blocks.extend(ref_lines)

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
    lines = ["== 画面布局（无版式锁定，以风格参考和文案描述为主） =="]
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
    parser.add_argument("--output", required=True, help="输出 prompt_draft.md 路径")
    args = parser.parse_args()

    brief = load_json(args.brief)
    if not brief:
        print(f"ERROR: 无法读取 brief.json: {args.brief}")
        sys.exit(1)

    distill = load_json(args.distill) if args.distill else None
    copywriting = load_json(args.copywriting) if args.copywriting else None
    style_profile = load_json(args.style_profile) if args.style_profile else None

    refs = {}
    project_dir = Path(args.output).resolve().parent
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

        if assets.get("product"):
            refs["产品图"] = {
                "路径": assets["product"],
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

    prompt, image_paths, ref_roles = assemble_prompt(brief, distill, copywriting, refs, style_profile=style_profile)

    role_issues = validate_ref_roles(brief, refs, ref_roles)
    if role_issues:
        print("ERROR: 参考图角色校验失败:")
        for issue in role_issues:
            print(f"  - {issue}")
        sys.exit(1)

    issues = validate_prompt(prompt, distill, copywriting)
    if issues:
        print("WARNING: 校验发现问题:")
        for issue in issues:
            print(f"  - {issue}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt, encoding="utf-8")
    print(f"OK: prompt 已写入 {output_path}")
    print(f"  字符数: {len(prompt)}")
    print(f"  参考图数量: {len(image_paths)}")
    for i, p in enumerate(image_paths):
        print(f"  参考图[{i}]: {p}")

    ref_order_path = output_path.parent / "ref_order.json"
    ref_order_data = {"ref_order": ref_roles}
    ref_order_path.write_text(json.dumps(ref_order_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ref_order.json 已写入 {ref_order_path}")

    if issues:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
