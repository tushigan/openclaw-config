#!/usr/bin/env python3
"""为单个详情页项目创建固定资产注册表。"""

import argparse
import json
import mimetypes
from datetime import datetime
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
ROLE_PATTERNS = {
    "brand_logo": ["品牌logo", "logo", "标志"],
    "product_main": ["产品图", "product", "主图", "商品图"],
    "product_detail": ["细节", "detail", "局部"],
    "packaging": ["包装", "packaging", "盒", "袋"],
    "style_reference": ["风格", "style", "参考", "reference"],
}


def guess_role(path: Path) -> str:
    name = path.stem.lower()
    for role, patterns in ROLE_PATTERNS.items():
        if any(pattern.lower() in name for pattern in patterns):
            return role
    return "reference_other"


def lock_level_for(role: str) -> str:
    if role in {"brand_logo", "product_main", "packaging"}:
        return "strict"
    if role in {"product_detail", "style_reference"}:
        return "guided"
    return "loose"


def usage_for(role: str) -> str:
    return {
        "brand_logo": "品牌识别，只能作为 LOGO/品牌元素参考，不可改形或重绘成新标志。",
        "product_main": "真实商品形态参考，所有产品主体必须以此为准，不臆造新结构。",
        "product_detail": "材质、结构、工艺、口感等细节证明参考。",
        "packaging": "包装、规格、套装、收到什么等购买确认参考。",
        "style_reference": "风格方向参考，只借鉴色彩、光影、氛围和版式语言，不复制主体。",
        "style_guide": "本项目全局风格指南，后续手稿、成稿、头图必须共用。",
        "reference_other": "辅助参考素材，使用前需明确用途。",
    }.get(role, "辅助参考素材。")


def file_info(path: Path, project_dir: Path) -> dict:
    role = guess_role(path)
    return {
        "role": role,
        "path": str(path.relative_to(project_dir)),
        "absolute_path": str(path),
        "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "lock_level": lock_level_for(role),
        "usage": usage_for(role),
        "exists": path.exists(),
    }


def load_confirmed_assets(project_dir: Path) -> list[dict]:
    confirmed_path = project_dir / "参考" / "brand_asset_confirmed.json"
    if not confirmed_path.exists():
        return []
    data = json.loads(confirmed_path.read_text(encoding="utf-8"))
    assets = []
    for item in data.get("confirmed_assets", []):
        asset_path = Path(item.get("path", ""))
        if not asset_path.is_absolute():
            asset_path = project_dir / item.get("path", "")
        if not asset_path.exists():
            continue
        role = item.get("role") or guess_role(asset_path)
        assets.append({
            "role": role,
            "path": str(asset_path.relative_to(project_dir)) if asset_path.is_relative_to(project_dir) else str(asset_path),
            "absolute_path": str(asset_path),
            "mime": mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream",
            "lock_level": lock_level_for(role),
            "usage": usage_for(role),
            "exists": True,
            "source": item.get("source", "confirmed_candidate"),
            "confirmed": True,
        })
    return assets


def load_candidate_assets(project_dir: Path) -> list[dict]:
    candidate_path = project_dir / "参考" / "brand_asset_candidates.json"
    if not candidate_path.exists():
        return []
    data = json.loads(candidate_path.read_text(encoding="utf-8"))
    return data.get("candidates", [])


def main():
    parser = argparse.ArgumentParser(description="创建项目固定资产注册表")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--platform", default="tmall_mobile", help="平台 profile key")
    parser.add_argument("--category", default="food_bakery", help="品类 profile key")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        raise SystemExit(f"项目目录不存在: {project_dir}")

    ref_dir = project_dir / "参考"
    confirmed_assets = load_confirmed_assets(project_dir)
    candidate_assets = load_candidate_assets(project_dir)
    assets = confirmed_assets
    if not assets and not candidate_assets and ref_dir.exists():
        for path in sorted(ref_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
                assets.append(file_info(path, project_dir))

    style_guide = project_dir / "style_guide.png"
    if style_guide.exists():
        assets.append({
            "role": "style_guide",
            "path": str(style_guide.relative_to(project_dir)),
            "absolute_path": str(style_guide),
            "mime": "image/png",
            "lock_level": "strict",
            "usage": usage_for("style_guide"),
            "exists": True,
        })

    registry = {
        "version": "1.0",
        "project": project_dir.name,
        "created_at": datetime.now().isoformat(),
        "platform_profile": args.platform,
        "category_profile": args.category,
        "assets": assets,
        "pending_candidate_count": len(candidate_assets) if not confirmed_assets else 0,
        "rules": [
            "所有生图/改图脚本必须从本注册表读取素材角色，不得依赖长对话记忆猜测素材用途。",
            "strict 素材只允许作为真实参考，不允许重绘为新形态。",
            "style_guide 必须贯穿手稿、成稿和头图，确保项目风格统一。",
            "自动检索得到的候选素材只有在用户确认后，才允许进入本注册表。",
        ],
    }

    output_path = project_dir / "asset_registry.json" if confirmed_assets else project_dir / "asset_registry_base.json"
    output_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"资产注册表: {output_path}")
    if confirmed_assets:
        print("已生成正式版 asset_registry.json（资产已确认）")
    elif candidate_assets:
        print(f"提示: 候选资产未确认，已生成 asset_registry_base.json 作为占位")
        print(f"提示: 已有 {len(candidate_assets)} 个候选资产，但尚未确认")
    for asset in assets:
        print(f"- {asset['role']}: {asset['path']} ({asset['lock_level']})")


if __name__ == "__main__":
    main()
