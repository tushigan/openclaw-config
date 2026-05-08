#!/usr/bin/env python3
"""根据项目事实、策略文案和手稿切段生成正式的成稿分段 prompt 文件。"""

import argparse
import json
import re
from pathlib import Path


REQUIRED_FILES = (
    "facts.json",
    "asset_registry.json",
    "platform_profile.json",
    "category_profile.json",
    "style_guide.png",
    "策划/strategy_v1.md",
    "策划/copywriting_v1.md",
    "策划/prompt_package/design_segment_base.txt",
)

SEGMENT_PATTERNS = [
    "segment_{key}",
    "segment {key}",
    "段{key}",
    "第{key}段",
    "连续段{key}",
    "连续段 {key}",
    "所属连续段：{key}",
    "所属连续段: {key}",
]


def require_project_inputs(project_dir: Path) -> None:
    missing = []
    for rel_path in REQUIRED_FILES:
        path = project_dir / rel_path
        if not path.exists():
            missing.append(str(path))
    if missing:
        missing_text = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"缺少成稿阶段必需文件，不能生成分段 prompt:\n{missing_text}")



def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))



def resolve_cut_preview_dir(project_dir: Path, version: str) -> Path:
    preferred = project_dir / "手稿" / version / "cut_preview"
    legacy = project_dir / "手稿" / f"cut_preview_{version}"
    if preferred.exists() and preferred.is_dir():
        return preferred
    if legacy.exists() and legacy.is_dir():
        return legacy
    raise FileNotFoundError(f"缺少已确认的手稿切段目录，请先完成手稿 QA 与切段确认: {preferred}")



def load_cut_manifest(cut_preview_dir: Path) -> dict:
    manifest_path = cut_preview_dir / "cut_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"缺少 cut_manifest.json，不能把临时切图当正式输入，请先完成确认切点: {manifest_path}"
        )
    manifest = read_json(manifest_path)
    if manifest.get("status") != "confirmed":
        raise ValueError(
            f"切段 manifest 未标记为 confirmed，不能进入成稿阶段: {manifest_path}"
        )
    segments = manifest.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError(f"切段 manifest 缺少 segments 清单: {manifest_path}")
    return manifest



def collect_segment_files(cut_preview_dir: Path) -> list[tuple[str, Path]]:
    manifest = load_cut_manifest(cut_preview_dir)
    segment_files = []
    for item in manifest.get("segments", []):
        key = str(item.get("key") or "").strip()
        filename = str(item.get("confirmed_file") or "").strip()
        source = str(item.get("source") or "").strip()
        if not key or not filename:
            raise ValueError(f"切段 manifest 中存在缺少 key/confirmed_file 的项: {item}")
        if source and source not in {"annotation", "whitespace_analysis", "manual", "confirmed_preview"}:
            raise ValueError(f"切段 manifest 中存在未知切点来源 {source}: {item}")
        path = cut_preview_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"切段 manifest 引用的确认段图不存在: {path}")
        if not path.name.startswith("segment_") or "_confirmed" not in path.stem:
            raise ValueError(f"正式确认段图必须命名为 segment_*_confirmed.png: {path}")
        segment_files.append((key, path))
    if not segment_files:
        raise FileNotFoundError(f"切段 manifest 中未找到确认段图: {cut_preview_dir / 'cut_manifest.json'}")
    return segment_files



def load_asset_summary(project_dir: Path) -> str:
    registry = read_json(project_dir / "asset_registry.json")
    lines = ["【素材角色摘要】"]
    assets = registry.get("assets", [])
    if not assets:
        lines.append("- 未登记素材")
        return "\n".join(lines)

    for asset in assets:
        role = asset.get("role") or "unknown"
        path = asset.get("path") or asset.get("absolute_path") or ""
        usage = asset.get("usage") or ""
        lines.append(f"- {role}: {path} {usage}".rstrip())
    return "\n".join(lines)



def extract_summary_lines(text: str, keywords: tuple[str, ...], limit: int = 8) -> list[str]:
    matches = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(keyword in line for keyword in keywords):
            matches.append(line)
    return matches[:limit]



def normalize_block(text: str, max_length: int = 2200) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[:max_length].rstrip() + "\n……（以下内容省略，原文见项目文件）"



def extract_segment_context(text: str, segment_key: str) -> str:
    paragraphs = re.split(r"\n\s*\n", text)
    lowered_key = segment_key.lower()
    matched = []
    patterns = [pattern.format(key=segment_key) for pattern in SEGMENT_PATTERNS]
    patterns += [pattern.format(key=lowered_key) for pattern in SEGMENT_PATTERNS]

    for paragraph in paragraphs:
        para = paragraph.strip()
        if not para:
            continue
        para_lower = para.lower()
        if any(pattern.lower() in para_lower for pattern in patterns):
            matched.append(para)

    if matched:
        return normalize_block("\n\n".join(matched), max_length=2600)
    return ""



def build_prompt(
    project_dir: Path,
    version: str,
    segment_key: str,
    segment_path: Path,
    facts: dict,
    strategy_text: str,
    copywriting_text: str,
    base_prompt: str,
    asset_summary: str,
) -> str:
    brand = facts.get("brand", "")
    product = facts.get("product", "")
    category = facts.get("category", "")
    structure = facts.get("structure", "")
    style_tone = facts.get("style_tone", "")
    sellpoints = facts.get("sellpoints", [])
    flavors = facts.get("flavors", [])

    strategy_focus = extract_summary_lines(strategy_text, ("总策略", "一句话总策略", "叙事", "模块", "风格", "风险", "卖点"))
    copy_focus = extract_summary_lines(copywriting_text, ("主标题", "副标题", "关键信息", "建议视觉", "信息层级", "过渡", "任务", "所属连续段"), limit=14)
    strategy_segment = extract_segment_context(strategy_text, segment_key)
    copy_segment = extract_segment_context(copywriting_text, segment_key)

    if not strategy_segment:
        strategy_segment = normalize_block(strategy_text, max_length=1600)
    if not copy_segment:
        copy_segment = normalize_block(copywriting_text, max_length=2600)

    sections = [
        base_prompt.strip(),
        "【本次生成目标】",
        f"- 当前成稿段：segment_{segment_key}",
        f"- 对应手稿切段：{segment_path}",
        f"- 输出版本目录：{project_dir / '设计' / version}",
        "- 必须延续 style_guide.png 的统一风格，不得脱离项目既定品牌调性。",
        "- 必须严格参考手稿切段的结构层级，但允许在正式设计中提升质感与完成度。",
        "- 必须保持产品真实结构、包装关系和品牌资产正确，不得替换错误品牌或自由改造产品形态。",
        "- 必须遵守封闭边界规则，使该段可以直接参与硬拼接。",
        "",
        "【产品事实快照】",
        f"- 品牌：{brand}",
        f"- 产品：{product}",
        f"- 品类：{category}",
        f"- 结构：{structure}",
        f"- 风格调性：{style_tone}",
        f"- 核心卖点：{'、'.join(sellpoints) if sellpoints else '未提供'}",
        f"- 口味/SKU：{'、'.join(flavors) if flavors else '未提供'}",
        "",
        asset_summary,
        "",
        "【策略摘要】",
        *(strategy_focus or ["- 未从 strategy_v1.md 中提取到结构化摘要，请以原文为准。"]),
        "",
        f"【与 segment_{segment_key} 直接相关的策略内容】",
        strategy_segment,
        "",
        "【文案摘要】",
        *(copy_focus or ["- 未从 copywriting_v1.md 中提取到结构化摘要，请以原文为准。"]),
        "",
        f"【与 segment_{segment_key} 直接相关的文案内容】",
        copy_segment,
        "",
        "【执行要求】",
        f"- 仅生成 segment_{segment_key} 对应的一段最终设计稿。",
        "- 所有文字必须为中文成稿文案，不得出现英文占位符、屏号、列号、手机外框或 Lorem/XXX。",
        "- 画面必须体现电商详情页正式设计完成度，而不是线框图、低精度预览图或临时草图。",
        "- 若本段包含包装、规格、认证、配件等信息，应以项目事实和已确认素材为准，不得自行编造。",
        "- 若本段是最后一段，应补足完整页尾结束设计。",
    ]

    return "\n".join(sections).strip() + "\n"



def create_prompts(project_dir: Path, version: str) -> list[Path]:
    require_project_inputs(project_dir)

    facts = read_json(project_dir / "facts.json")
    strategy_path = project_dir / "策划" / "strategy_v1.md"
    copywriting_path = project_dir / "策划" / "copywriting_v1.md"
    base_prompt_path = project_dir / "策划" / "prompt_package" / "design_segment_base.txt"
    strategy_text = strategy_path.read_text(encoding="utf-8")
    copywriting_text = copywriting_path.read_text(encoding="utf-8")
    base_prompt = base_prompt_path.read_text(encoding="utf-8")
    asset_summary = load_asset_summary(project_dir)
    cut_preview_dir = resolve_cut_preview_dir(project_dir, version)
    segment_files = collect_segment_files(cut_preview_dir)

    design_dir = project_dir / "设计" / version
    design_dir.mkdir(parents=True, exist_ok=True)

    print("========== 成稿分段 prompt 生成 ==========")
    print(f"项目目录: {project_dir}")
    print(f"版本: {version}")
    print(f"输出目录: {design_dir}")
    print(f"切段目录: {cut_preview_dir}")
    print("")
    print("关键输入文件:")
    for rel_path in REQUIRED_FILES:
        print(f"- {project_dir / rel_path}")
    print("")
    print("识别到的切段图:")
    for segment_key, segment_path in segment_files:
        print(f"- segment_{segment_key}: {segment_path}")

    created_paths = []
    for segment_key, segment_path in segment_files:
        prompt_content = build_prompt(
            project_dir=project_dir,
            version=version,
            segment_key=segment_key,
            segment_path=segment_path,
            facts=facts,
            strategy_text=strategy_text,
            copywriting_text=copywriting_text,
            base_prompt=base_prompt,
            asset_summary=asset_summary,
        )
        prompt_path = design_dir / f"prompt_{segment_key}.txt"
        prompt_path.write_text(prompt_content, encoding="utf-8")
        created_paths.append(prompt_path)
        print(f"生成: {prompt_path}")

    return created_paths



def main() -> None:
    parser = argparse.ArgumentParser(description="生成详情页成稿分段 prompt 文件")
    parser.add_argument("--project-dir", required=True, help="项目目录路径")
    parser.add_argument("--version", default="v1", help="版本号")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        raise SystemExit(f"项目目录不存在: {project_dir}")

    created_paths = create_prompts(project_dir, args.version)
    print("")
    print(f"完成：生成 {len(created_paths)} 个成稿分段 prompt 文件")


if __name__ == "__main__":
    main()
