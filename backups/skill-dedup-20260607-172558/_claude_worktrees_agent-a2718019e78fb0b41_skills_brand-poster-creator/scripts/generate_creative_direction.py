#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager


REQUIRED_FIELDS = [
    "summary",
    "scene_concept",
    "hero_focus",
    "composition_plan",
    "text_visual_relationship",
    "style_translation",
]


def load_json(path: str):
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def write_json(path: str, payload: dict) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize_copy(copywriting: dict | None) -> tuple[list[str], list[str]]:
    titles = []
    body_texts = []
    if not copywriting:
        return titles, body_texts
    for _, item in copywriting.items():
        text = str(item.get("文案", "") or "").strip()
        if not text:
            continue
        if len(titles) < 2:
            titles.append(text)
        elif len(body_texts) < 3:
            body_texts.append(text)
    return titles, body_texts


def get_festival_scene(brief: dict) -> str:
    festival = str(brief.get("festival", "") or "").strip()
    poster_type = str(brief.get("type", "") or "").strip()
    style_note = str(brief.get("style_note", "") or "").strip()
    if festival:
        return f"以「{festival}」为主题氛围核心，画面围绕该营销节点建立明确场景与情绪。"
    if poster_type:
        return f"以「{poster_type}」为传播任务核心，画面内容全部服务于该传播目标。"
    if style_note:
        return f"以用户给定的风格要求为基础，围绕“{style_note}”建立统一画面表达。"
    return "以品牌传播主题为核心，建立清晰、集中、可感知的单张海报表达。"


def build_supporting_elements(brief: dict, style_profile: dict | None) -> list[str]:
    hero = brief.get("hero_priority", {}) or {}
    hero2 = str(hero.get("hero_2", "") or "").strip()
    must_include = brief.get("must_include", []) or []
    items = []
    if hero2:
        items.append(f"{hero2}作为氛围陪衬出现，只负责烘托主题，不抢第一视觉。")
    if must_include:
        include_text = "、".join(str(item).strip() for item in must_include if str(item).strip())
        if include_text:
            items.append(f"必须露出的元素包括：{include_text}，但都要服从主视觉层级。")
    if style_profile and style_profile.get("decorative"):
        items.append(str(style_profile.get("decorative", "") or "").strip())
    if not items:
        items.append("使用少量辅助元素烘托气氛，避免陪衬过满导致主体失焦。")
    return items[:3]


def build_style_translation(style_profile: dict | None, brief: dict) -> str:
    if not style_profile:
        return "没有参考图时，以已确认文案、主题与素材关系为准，使用中性但完整的视觉表达，不额外引入陌生风格。"

    inherit_parts = []
    if style_profile.get("overall_mood"):
        inherit_parts.append(f"整体气质继承“{style_profile['overall_mood']}”")
    if style_profile.get("color"):
        inherit_parts.append("色彩继承「" + "、".join(style_profile.get("color", [])) + "」")
    if style_profile.get("material"):
        inherit_parts.append("质感继承「" + "、".join(style_profile.get("material", [])) + "」")

    avoid_parts = []
    for item in style_profile.get("content_do_not_inherit", []) or []:
        value = str(item).strip()
        if value:
            avoid_parts.append(value)
    season_hint = str(style_profile.get("season_override_hint", "") or "").strip()

    base = "；".join(inherit_parts) if inherit_parts else "继承参考图的配色、质感、氛围与笔触语言"
    if avoid_parts:
        base += "；不继承「" + "、".join(avoid_parts[:4]) + "」等具体场景内容"
    if season_hint:
        base += f"；{season_hint}"
    return base


def build_creative_direction(brief: dict, copywriting: dict | None, distill: dict | None, style_profile: dict | None) -> dict:
    brand_name = str(brief.get("brand_name", "") or "").strip() or "品牌"
    product_name = str(brief.get("product_name", "") or "").strip()
    hero = brief.get("hero_priority", {}) or {}
    hero1 = str(hero.get("hero_1", "") or "").strip() or (product_name if product_name else "核心主角")
    ratio = str(brief.get("ratio", "") or "2:3").strip()
    titles, body_texts = summarize_copy(copywriting)
    lead_copy = titles[0] if titles else f"围绕{brand_name}本次传播主题展开"

    layout_mode = "用蒸馏卡锁定的区域关系组织主体、文案和装饰层级" if distill else "在无蒸馏卡情况下，以主体优先、文案清晰、装饰辅助的方式组织画面"
    style_translation = build_style_translation(style_profile, brief)
    supporting = build_supporting_elements(brief, style_profile)

    summary = f"这张海报要把“{lead_copy}”作为核心感受，让用户先被{hero1}吸引，再自然接收品牌信息。"
    scene_concept = get_festival_scene(brief)
    hero_focus = f"第一视觉主体是{hero1}，它必须占据画面主导位置，并成为整张海报情绪和注意力的锚点。"
    composition_plan = f"整体按{ratio}画幅展开，{layout_mode}，让主视觉先抓人，标题与副文案随后建立阅读动线，装饰元素只做氛围补强。"

    if body_texts:
        body_summary = "；".join(body_texts[:2])
        text_visual_relationship = f"文案不是孤立贴字，而是围绕主视觉组织信息层级：主文案先定主题，辅助文案补充“{body_summary}”，与主体形成相互解释关系。"
    else:
        text_visual_relationship = "文案需要围绕主视觉组织信息层级，先定主题，再补充说明，避免文字与主体各说各话。"

    must_hit = [
        f"用户一眼就能感受到{brand_name}这次传播主题，而不是只看到一张泛化好看的图。",
        f"{hero1}必须足够明确、抢眼、可信，不能被背景、装饰或文案抢走主导权。",
    ]
    must_avoid = [
        "不要把参考图里的原始季节、天气、剧情或道具直接照搬进来。",
        "不要让画面变成元素堆砌或文案贴片，导致核心表达失焦。",
    ]

    return {
        "summary": summary,
        "scene_concept": scene_concept,
        "hero_focus": hero_focus,
        "supporting_elements": supporting,
        "composition_plan": composition_plan,
        "text_visual_relationship": text_visual_relationship,
        "style_translation": style_translation,
        "must_hit": must_hit,
        "must_avoid": must_avoid,
    }


def validate_creative_direction(payload: dict) -> list[str]:
    issues = []
    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if not str(value or "").strip():
            issues.append(f"缺少字段: {field}")
    for field in ("supporting_elements", "must_hit", "must_avoid"):
        value = payload.get(field)
        if not isinstance(value, list) or not any(str(item).strip() for item in value):
            issues.append(f"字段必须为非空数组: {field}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="生成品牌海报画面创意表达方案")
    parser.add_argument("--brief", required=True, help="brief.json 路径")
    parser.add_argument("--copywriting", default="", help="copywriting.json 路径（可选）")
    parser.add_argument("--distill", default="", help="distill_card.json 路径（可选）")
    parser.add_argument("--style-profile", default="", help="style_profile.json 路径（可选）")
    parser.add_argument("--output", required=True, help="creative_direction.json 输出路径")
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    project_dir = output_path.parent
    manager = ProjectManager(project_dir)
    attempt = manager.start_stage('creative_direction', reason='生成画面创意表达方案', actor='generate_creative_direction.py')

    brief = load_json(args.brief)
    if not brief:
        error = f"无法读取 brief.json: {args.brief}"
        manager.fail_stage(
            'creative_direction',
            error=error,
            actor='generate_creative_direction.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'error_summary': error,
                'brief_path': str(Path(args.brief).resolve()),
                'copywriting_path': str(Path(args.copywriting).resolve()) if args.copywriting else '',
                'distill_path': str(Path(args.distill).resolve()) if args.distill else '',
                'style_profile_path': str(Path(args.style_profile).resolve()) if args.style_profile else '',
                'output_path': str(output_path),
                'user_confirmed': False,
                'history': [{
                    'ts': manager.state['updated_at'],
                    'event': 'creative_direction_failed',
                    'reason': error,
                }],
            },
            files=['creative_direction_manifest.json'],
        )
        print(f"ERROR: {error}")
        return 1

    copywriting = load_json(args.copywriting) if args.copywriting else None
    distill = load_json(args.distill) if args.distill else None
    style_profile = load_json(args.style_profile) if args.style_profile else None

    payload = build_creative_direction(brief, copywriting, distill, style_profile)
    issues = validate_creative_direction(payload)
    if issues:
        error = '；'.join(issues)
        manager.fail_stage(
            'creative_direction',
            error=error,
            actor='generate_creative_direction.py',
            manifest_payload={
                'status': 'failed',
                'attempt': attempt,
                'error_summary': error,
                'brief_path': str(Path(args.brief).resolve()),
                'copywriting_path': str(Path(args.copywriting).resolve()) if args.copywriting else '',
                'distill_path': str(Path(args.distill).resolve()) if args.distill else '',
                'style_profile_path': str(Path(args.style_profile).resolve()) if args.style_profile else '',
                'output_path': str(output_path),
                'user_confirmed': False,
                'history': [{
                    'ts': manager.state['updated_at'],
                    'event': 'creative_direction_failed',
                    'reason': error,
                }],
            },
            files=['creative_direction_manifest.json'],
            extra={'issues': issues},
        )
        print("ERROR: 创意表达方案校验失败:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    write_json(str(output_path), payload)
    manager.complete_stage(
        'creative_direction',
        reason='创意表达方案已生成，等待用户确认。',
        actor='generate_creative_direction.py',
        manifest_payload={
            'status': 'generated',
            'attempt': attempt,
            'brief_path': str(Path(args.brief).resolve()),
            'copywriting_path': str(Path(args.copywriting).resolve()) if args.copywriting else '',
            'distill_path': str(Path(args.distill).resolve()) if args.distill else '',
            'style_profile_path': str(Path(args.style_profile).resolve()) if args.style_profile else '',
            'output_path': str(output_path),
            'required_fields': REQUIRED_FIELDS,
            'user_confirmed': False,
            'history': [{
                'ts': manager.state['updated_at'],
                'event': 'creative_direction_generated',
                'summary': payload['summary'],
            }],
        },
        flags={
            'creative_direction_ready': True,
            'creative_direction_confirmed': False,
        },
        artifacts={'creative_direction': str(output_path)},
        files=[manager._relative(output_path)],
        extra={'summary': payload['summary']},
    )

    print(f"OK: creative_direction 已写入 {output_path}")
    print(f"  核心表达: {payload['summary']}")
    print(f"  主视觉焦点: {payload['hero_focus']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
