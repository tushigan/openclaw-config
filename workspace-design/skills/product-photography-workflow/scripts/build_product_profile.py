#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    append_audit,
    read_json,
    resolve_project_dir,
    update_state,
    utc_now,
    write_json,
)


def md_list(title: str, values: list[str]) -> str:
    if not values:
        return f"## {title}\n\n- 无\n"
    return "## " + title + "\n\n" + "\n".join(f"- {value}" for value in values) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="构建产品事实画像")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--product-name", required=True, help="产品名")
    parser.add_argument("--brand-name", default="", help="品牌名")
    parser.add_argument("--category", default="", help="品类")
    parser.add_argument("--outer-shape", default="", help="外轮廓")
    parser.add_argument("--structure-type", default="unknown", help="结构类型")
    parser.add_argument("--open-close-states", default="closed", help="开合状态")
    parser.add_argument("--cross-section-required", choices=["yes", "no"], default="no")
    parser.add_argument("--cross-section-state", default="not_shown", help="切面状态")
    parser.add_argument("--layer-count", type=int, default=0, help="层数")
    parser.add_argument("--filling-type", default="", help="夹心/内馅类型")
    parser.add_argument("--filling-texture", default="", help="夹心/内馅质地")
    parser.add_argument("--filling-flow-level", default="none", help="流动程度")
    parser.add_argument("--shell-texture", default="", help="外壳/外皮质地")
    parser.add_argument("--surface-finish", default="", help="表面状态")
    parser.add_argument("--breakage-pattern", default="", help="破损或断裂规律")
    parser.add_argument("--material-note", action="append", default=[], help="材质说明")
    parser.add_argument("--color-note", action="append", default=[], help="颜色说明")
    parser.add_argument("--key-identifier", action="append", default=[], help="关键识别点")
    parser.add_argument("--must-show-detail", action="append", default=[], help="必须体现的细节")
    parser.add_argument("--must-not-fake-detail", action="append", default=[], help="不能乱造的细节")
    parser.add_argument("--deformation-rule", action="append", default=[], help="禁止变形规则")
    parser.add_argument("--structure-note", action="append", default=[], help="结构说明")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    assets_manifest = read_json(project_dir / "assets_manifest.json", {})
    gap_report = read_json(project_dir / "intake_manifest.json", {}).get("gap_report", {})
    product_roles = [item.get("role", "") for item in assets_manifest.get("product_assets", [])]

    profile = {
        "version": "1.0",
        "project_id": read_json(project_dir / "project_state.json", {}).get("project_id", ""),
        "created_at": utc_now(),
        "product_name": args.product_name,
        "brand_name": args.brand_name,
        "category": args.category,
        "outer_shape": args.outer_shape,
        "structure_type": args.structure_type,
        "open_close_states": args.open_close_states,
        "cross_section_required": args.cross_section_required == "yes",
        "cross_section_state": args.cross_section_state,
        "layer_count": args.layer_count,
        "filling_type": args.filling_type,
        "filling_texture": args.filling_texture,
        "filling_flow_level": args.filling_flow_level,
        "shell_texture": args.shell_texture,
        "surface_finish": args.surface_finish,
        "breakage_pattern": args.breakage_pattern,
        "material_notes": args.material_note,
        "color_notes": args.color_note,
        "key_identifiers": args.key_identifier,
        "must_show_details": args.must_show_detail,
        "must_not_fake_details": args.must_not_fake_detail,
        "deformation_rules": args.deformation_rule,
        "structure_notes": args.structure_note,
        "evidence": {
            "registered_product_roles": product_roles,
            "gap_report_snapshot": gap_report,
        },
    }
    write_json(project_dir / "product_profile.json", profile)

    report = [
        f"# 产品理解卡：{args.product_name}",
        "",
        f"- 品牌：{args.brand_name or '未填'}",
        f"- 品类：{args.category or '未填'}",
        f"- 外轮廓：{args.outer_shape or '未填'}",
        f"- 结构类型：{args.structure_type}",
        f"- 开合状态：{args.open_close_states}",
        f"- 是否必须体现切面：{'是' if args.cross_section_required == 'yes' else '否'}",
        f"- 切面状态：{args.cross_section_state}",
        f"- 层数：{args.layer_count or '未填'}",
        f"- 内馅类型：{args.filling_type or '未填'}",
        f"- 内馅质地：{args.filling_texture or '未填'}",
        f"- 内馅流动程度：{args.filling_flow_level}",
        f"- 外壳质地：{args.shell_texture or '未填'}",
        f"- 表面状态：{args.surface_finish or '未填'}",
        f"- 破损规律：{args.breakage_pattern or '未填'}",
        "",
        md_list("材质说明", args.material_note),
        md_list("颜色说明", args.color_note),
        md_list("关键识别点", args.key_identifier),
        md_list("必须体现的细节", args.must_show_detail),
        md_list("不能乱造的细节", args.must_not_fake_detail),
        md_list("禁止变形规则", args.deformation_rule),
        md_list("结构说明", args.structure_note),
    ]
    (project_dir / "reports" / "product_understanding.md").write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    update_state(
        project_dir,
        current_stage="product_profile_ready",
        stage_status="ready",
    )
    append_audit(
        project_dir,
        "product_profile_built",
        {
            "product_name": args.product_name,
            "structure_type": args.structure_type,
            "cross_section_required": args.cross_section_required == "yes",
        },
    )
    print(f"profile={project_dir / 'product_profile.json'}")


if __name__ == "__main__":
    main()
