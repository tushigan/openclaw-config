#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    PRODUCT_ROLE_ORDER,
    append_audit,
    read_json,
    resolve_project_dir,
    update_state,
    utc_now,
    write_json,
)

STRUCTURE_KEYWORDS = [
    "夹心",
    "流心",
    "切面",
    "层",
    "分层",
    "开袋",
    "剖面",
    "爆浆",
    "馅",
    "酱",
    "coated",
    "filled",
    "layered",
]


def needs_structure_check(hints: list[str], assets_manifest: dict) -> bool:
    blob = " ".join([text for text in hints if text]).lower()
    if any(keyword.lower() in blob for keyword in STRUCTURE_KEYWORDS):
        return True
    roles = {item.get("role", "") for item in assets_manifest.get("product_assets", [])}
    return bool({"product_open", "product_cross_section"} & roles)


def main() -> None:
    parser = argparse.ArgumentParser(description="检查产品摄影信息缺口")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--product-name", default="", help="产品名提示")
    parser.add_argument("--selling-points", action="append", default=[], help="卖点或结构提示")
    parser.add_argument("--user-note", action="append", default=[], help="额外用户描述")
    parser.add_argument("--minimum-product-views", type=int, default=3, help="建议最少产品图数量")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    assets_manifest = read_json(project_dir / "assets_manifest.json", {})
    intake = read_json(project_dir / "intake_manifest.json", {})

    product_assets = assets_manifest.get("product_assets", [])
    roles = {item.get("role", "") for item in product_assets}
    structure_required = needs_structure_check(
        [args.product_name, *args.selling_points, *args.user_note],
        assets_manifest,
    )

    distinct_view_roles = [role for role in PRODUCT_ROLE_ORDER if role in roles]
    hard_missing = []
    soft_missing = []
    recommended = []
    suggested_questions = []

    if len(product_assets) < args.minimum_product_views:
        hard_missing.append("产品图数量不足")
        recommended.append("至少补充到 3 张以上产品图")
    if "product_front" not in roles:
        hard_missing.append("缺正面主视图")
        recommended.append("补 1 张正面主视图")
    if "product_side" not in roles:
        soft_missing.append("缺侧面或厚薄信息")
        recommended.append("补 1 张侧面图，帮助理解体积和厚薄")
    if "product_top" not in roles:
        soft_missing.append("缺顶部结构信息")
        recommended.append("补 1 张顶部图，帮助理解轮廓和表面")
    if "product_detail" not in roles:
        soft_missing.append("缺局部细节图")
        recommended.append("补 1 张近景细节图，帮助理解纹理和材质")

    if structure_required:
        if "product_cross_section" not in roles and "product_open" not in roles:
            hard_missing.append("缺内部结构证据")
            recommended.append("补切面图或打开状态图，帮助锁定夹心/层次/内部结构")
            suggested_questions.append("是否可以补 1 张切面图、开口图或内部结构近景？")
        if "product_detail" not in roles:
            recommended.append("如果内部结构重要，再补 1 张夹心或层次近景")

    if not assets_manifest.get("reference_assets", []):
        soft_missing.append("缺风格参考图")
        recommended.append("如有目标画风，补 1-2 张参考图帮助锁定光线、背景和构图")

    sufficient = not hard_missing and len(product_assets) >= max(2, args.minimum_product_views - 1)
    risk_note = ""
    if not sufficient:
        risk_note = (
            "当前素材继续生成会有形态、结构、材质或切面失真的风险。"
            "如果用户明确接受，可以走带风险继续模式。"
        )

    report = {
        "checked_at": utc_now(),
        "product_asset_count": len(product_assets),
        "reference_asset_count": len(assets_manifest.get("reference_assets", [])),
        "distinct_product_roles": distinct_view_roles,
        "structure_required": structure_required,
        "sufficient_for_generation": sufficient,
        "hard_missing": hard_missing,
        "soft_missing": soft_missing,
        "recommended_additional_shots": recommended,
        "suggested_user_questions": suggested_questions,
        "risk_note": risk_note,
    }

    intake["gap_report"] = report
    intake["updated_at"] = utc_now()
    write_json(project_dir / "intake_manifest.json", intake)
    update_state(
        project_dir,
        current_stage="intake_gap_check",
        stage_status="waiting_user" if not sufficient else "ready",
        workflow_flag_updates={
            "assets_sufficient": sufficient,
            "risk_accepted": False,
        },
    )
    append_audit(project_dir, "gap_check_completed", report)
    print(f"sufficient_for_generation={str(sufficient).lower()}")
    print(f"structure_required={str(structure_required).lower()}")
    if hard_missing:
        print("hard_missing=" + " | ".join(hard_missing))


if __name__ == "__main__":
    main()
