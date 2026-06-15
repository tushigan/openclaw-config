#!/usr/bin/env python3
"""
品牌档案强制检查和自动创建机制

用途：
1. 在品牌任务开始前，强制检查品牌档案是否存在
2. 如果不存在，从任务描述中提取品牌信息并创建档案
3. 确保所有品牌任务都有完整的品牌记忆

使用方式：
    python3 ensure_brand_profile.py --brand "品牌名" [--client "客户名"] [--extract-from "任务描述文本"]
"""

import sys
import os
import json
import argparse
import re
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agency_project'))

from agency_project import find_brand_profile, create_or_get_brand


def extract_brand_info_from_text(text: str) -> dict:
    """
    从任务描述中提取品牌信息

    Args:
        text: 任务描述文本（可能包含品牌定位、调性、受众等信息）

    Returns:
        提取的品牌信息字典
    """
    brand_info = {
        "industry": "",
        "category": "",
        "positioning": "",
        "target_audience": "",
        "brand_tone": "",
        "core_values": []
    }

    # 提取行业/品类
    industry_patterns = [
        r"(?:行业|品类|产品)[:：]\s*([^\n，。,\.]+)",
        r"([^，。,\.]+)(?:品牌|产品|企业)",
        r"(?:预包装|食品|饮品|烘焙|餐饮|服装|美妆|科技|教育|金融)([^\n，。,\.]*)"
    ]
    for pattern in industry_patterns:
        match = re.search(pattern, text)
        if match:
            brand_info["industry"] = match.group(1).strip()
            break

    # 提取定位
    positioning_patterns = [
        r"(?:定位|品牌定位|市场定位)[:：]\s*([^\n。\.]+)",
        r"(?:面向|针对|定位为)([^\n。\.]+?)(?:的|，|。)",
        r"从(.+?)(?:升级|转向|发展)(?:为|到|成)(.+?)(?:的|，|。)"
    ]
    for pattern in positioning_patterns:
        match = re.search(pattern, text)
        if match:
            brand_info["positioning"] = match.group(0).strip()
            break

    # 提取目标受众
    audience_patterns = [
        r"(?:受众|目标受众|目标人群|用户)[:：]\s*([^\n。\.]+)",
        r"(?:给|为|面向)([^看做的]{2,20}?)(?:看|用|设计|制作)",
        r"(?:渠道客户|经销商|终端|消费者|用户|客户|家庭|妈妈|年轻人|白领)"
    ]
    for pattern in audience_patterns:
        match = re.search(pattern, text)
        if match:
            if match.lastindex:
                brand_info["target_audience"] = match.group(1).strip()
            else:
                brand_info["target_audience"] = match.group(0).strip()
            break

    # 提取品牌调性
    tone_patterns = [
        r"(?:调性|品牌调性|风格|气质)[:：]\s*([^\n。\.]+)",
        r"((?:专业|现代|高级|亲和|温暖|活力|年轻|时尚|简约|优雅)(?:[、,，]?(?:专业|现代|高级|亲和|温暖|活力|年轻|时尚|简约|优雅))*)"
    ]
    for pattern in tone_patterns:
        match = re.search(pattern, text)
        if match:
            brand_info["brand_tone"] = match.group(1).strip()
            break

    # 提取核心价值
    values_text = brand_info.get("brand_tone", "") + " " + brand_info.get("positioning", "")
    common_values = ["专业", "现代", "高级", "亲和", "温暖", "活力", "年轻", "时尚", "简约", "优雅", "创新", "品质", "信任"]
    brand_info["core_values"] = [v for v in common_values if v in values_text]

    return brand_info


def ensure_brand_profile(
    brand_name: str,
    client_name: str = "",
    workspace_root: str = "/Users/a123/.openclaw",
    extract_from: str = "",
    auto_create: bool = False
) -> dict:
    """
    确保品牌档案存在

    Args:
        brand_name: 品牌名
        client_name: 客户名（可选）
        workspace_root: OpenClaw 根目录
        extract_from: 任务描述文本（用于提取品牌信息）
        auto_create: 是否自动创建（不询问用户）

    Returns:
        {"exists": bool, "created": bool, "profile_path": str, "message": str}
    """
    workspace_path = Path(workspace_root)

    # 检查品牌档案是否存在
    profile_path = find_brand_profile(workspace_path, brand_name)

    if profile_path:
        return {
            "exists": True,
            "created": False,
            "profile_path": str(profile_path),
            "message": f"✅ 品牌档案已存在: {brand_name}"
        }

    # 品牌档案不存在
    if not auto_create:
        # 需要用户确认
        return {
            "exists": False,
            "created": False,
            "profile_path": "",
            "message": f"⚠️ 品牌档案不存在: {brand_name}\n\n请确认是否创建新品牌档案？\n\n如需创建，请提供以下信息：\n- 客户名称（如果与品牌名不同）\n- 行业/品类\n- 品牌定位\n- 目标受众\n- 品牌调性"
        }

    # 自动创建品牌档案
    brand_info = {}

    if extract_from:
        # 从文本中提取品牌信息
        brand_info = extract_brand_info_from_text(extract_from)

    # 创建品牌档案
    try:
        brand_dir = create_or_get_brand(
            workspace_root=workspace_path,
            brand_name=brand_name,
            client_name=client_name or brand_name,
            industry=brand_info.get("industry", ""),
            category=brand_info.get("category", ""),
            positioning=brand_info.get("positioning", ""),
            target_audience=brand_info.get("target_audience", ""),
            brand_tone=brand_info.get("brand_tone", ""),
            core_values=brand_info.get("core_values", [])
        )

        profile_path = brand_dir / "_brand-profile.json"

        return {
            "exists": False,
            "created": True,
            "profile_path": str(profile_path),
            "message": f"✅ 品牌档案已创建: {brand_name}\n路径: {profile_path}\n\n提取的信息：\n{json.dumps(brand_info, ensure_ascii=False, indent=2)}"
        }
    except Exception as e:
        return {
            "exists": False,
            "created": False,
            "profile_path": "",
            "message": f"❌ 创建品牌档案失败: {str(e)}"
        }


def main():
    parser = argparse.ArgumentParser(description="品牌档案强制检查和自动创建")
    parser.add_argument("--brand", required=True, help="品牌名称")
    parser.add_argument("--client", default="", help="客户名称（可选）")
    parser.add_argument("--workspace-root", default="/Users/a123/.openclaw", help="OpenClaw 根目录")
    parser.add_argument("--extract-from", default="", help="任务描述文本（用于提取品牌信息）")
    parser.add_argument("--auto-create", action="store_true", help="自动创建（不询问用户）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    result = ensure_brand_profile(
        brand_name=args.brand,
        client_name=args.client,
        workspace_root=args.workspace_root,
        extract_from=args.extract_from,
        auto_create=args.auto_create
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["message"])
        if not result["exists"] and not result["created"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
