#!/usr/bin/env python3
"""生成项目级 prompt package，供嵌套生图 skill 使用 --prompt-file 调用。"""

import argparse
import json
from pathlib import Path
from typing import Optional


def read_json(path: Path, default: Optional[dict] = None) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default or {}


def require_project_inputs(project_dir: Path) -> None:
    required_files = [
        project_dir / "facts.json",
        project_dir / "platform_profile.json",
        project_dir / "category_profile.json",
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        missing_text = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"缺少必需项目文件，不能生成 prompt package:\n{missing_text}")

    # 资产注册表：优先正式版，fallback 基础版
    registry_path = project_dir / "asset_registry.json"
    base_registry_path = project_dir / "asset_registry_base.json"
    if not registry_path.exists() and not base_registry_path.exists():
        raise FileNotFoundError(
            f"缺少资产注册表（asset_registry.json 或 asset_registry_base.json），"
            f"不能生成 prompt package"
        )


def resolve_registry_path(project_dir: Path) -> Path:
    """正式注册表优先；仅当正式版不存在时，回退到基础版。"""
    registry_path = project_dir / "asset_registry.json"
    if registry_path.exists():
        return registry_path
    return project_dir / "asset_registry_base.json"


def asset_block(registry: dict) -> str:
    assets = registry.get("assets", [])
    if not assets:
        return "【项目素材】\n- 未登记素材；执行前应先创建 asset_registry.json。\n"
    lines = ["【项目素材】"]
    for asset in assets:
        lines.append(
            f"- {asset.get('role')}: {asset.get('path')}｜锁定级别：{asset.get('lock_level')}｜用途：{asset.get('usage')}"
        )
    return "\n".join(lines) + "\n"


def profile_block(platform: dict, category: dict) -> str:
    lines = ["【平台与品类规则】"]
    if platform:
        lines.append(f"平台：{platform.get('name', platform.get('key', ''))}")
        for rule in platform.get("detail_page_rules", []):
            lines.append(f"- 平台规则：{rule}")
    if category:
        lines.append(f"品类：{category.get('name', category.get('key', ''))}")
        for rule in category.get("detail_page_logic", []):
            lines.append(f"- 品类逻辑：{rule}")
        for rule in category.get("visual_rules", []):
            lines.append(f"- 视觉规则：{rule}")
    return "\n".join(lines) + "\n"


def global_constraints() -> str:
    return """【全局硬规则】
- 全中文，禁止英文占位符和无意义文字。
- 禁止手机外框、刘海、状态栏、底部横条。
- 禁止屏数标注、Column 标注、1/11 等页码标识。
- 禁止使用“标题占位”“卖点条”“XXX”“Lorem”等占位内容。
- 产品结构必须遵守 facts.json 和 asset_registry.json，不臆造新商品形态。
- 风格必须延续 style_guide.png；手稿、成稿、头图不能各自另起风格。
- 手稿阶段默认直接输出高精度正式版本，禁止先出低精度预览再升级为正式版。
- 每次进入新阶段前必须重新读取本项目的 facts、素材注册表、平台/品类 profile、已确认品牌知识和对应 prompt package，不得依赖聊天上下文记忆。
"""


def boundary_block() -> str:
    return """【成稿分段封闭边界规则】
IMPORTANT: This segment must be a COMPLETE INDEPENDENT DESIGN BLOCK with FULL TOP AND BOTTOM BOUNDARY DESIGN.
【Top boundary】Complete finished design with 40-60px visual closing band or equivalent complete transition.
【Bottom boundary】Complete finished design with 40-60px visual closing band or equivalent complete transition.
This segment should look like a complete standalone module, ready for hard vertical stacking.
禁止开放式裁切、半截元素、未收口背景和需要 blend/crop 才能拼接的边界。
"""


def knowledge_block(project_dir: Path) -> str:
    confirmed = read_json(project_dir / "策划" / "brand_knowledge_confirmed.json")
    items = confirmed.get("confirmed_items") or confirmed.get("confirmed_knowledge") or []
    if not items:
        return "【品牌知识摘要】\n- 未确认品牌知识；当前仅使用 facts、素材注册表和平台/品类规则。\n"
    lines = ["【品牌知识摘要】"]
    dataset_name = confirmed.get("matched_dataset_name")
    if dataset_name:
        lines.append(f"- 来源知识库：{dataset_name}")
    for item in items:
        title = item.get("title") or item.get("query") or "未命名条目"
        summary = item.get("summary") or item.get("content") or ""
        lines.append(f"- {title}：{summary}")
    return "\n".join(lines) + "\n"


def build(project_dir: Path):
    require_project_inputs(project_dir)
    facts = read_json(project_dir / "facts.json")
    registry_path = resolve_registry_path(project_dir)
    registry = read_json(registry_path)
    platform = read_json(project_dir / "platform_profile.json")
    category = read_json(project_dir / "category_profile.json")

    out_dir = project_dir / "策划" / "prompt_package"
    out_dir.mkdir(parents=True, exist_ok=True)

    base = "\n".join([
        global_constraints(),
        f"【产品事实】\n{json.dumps(facts, ensure_ascii=False, indent=2)}\n",
        asset_block(registry),
        knowledge_block(project_dir),
        profile_block(platform, category),
    ])

    packages = {
        "wireframe_base.txt": base + "\n【阶段任务】默认生成黑白详情页手稿：单张 1920x1920 方形画板，4 列纵向排列全部屏，专业 UI/UX wireframe 质感；用户明确要求高分辨率时才升高画板尺寸。\n",
        "design_segment_base.txt": base + "\n" + boundary_block() + "\n【阶段任务】生成最终详情页分段设计稿，必须高清、完整收边、可硬拼接。\n",
        "head_image_base.txt": base + "\n【阶段任务】生成电商头图/KV，遵循平台和品类的头图数量、角色和信息密度要求。\n",
        "delivery_checklist.txt": """【最终交付检核】
- 只交付用户确认过的最终稿。
- 必须包含高清无损 PNG 原图，不为发送便利降低图片质量。
- 检查完整拼接长图、分段图、头图、策略/文案、交付清单是否齐全。
- 图片超过 10MB 不直接发图，文件超过 30MB 不直接发送。
- ZIP 超过 30MB 必须分卷压缩，每卷建议 28MB，并发送全部分卷。
- 用户确认项目结束后，才能整理或清理过程稿。
""",
    }

    for name, content in packages.items():
        path = out_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"生成: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成项目 prompt package")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    args = parser.parse_args()
    build(Path(args.project_dir))
