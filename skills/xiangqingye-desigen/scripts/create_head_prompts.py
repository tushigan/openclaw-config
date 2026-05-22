#!/usr/bin/env python3
"""根据产品事实和策略生成头图 prompt 文件

用法：
    python3 scripts/create_head_prompts.py --project-dir {项目目录} [--version v1]

输出：
    {项目目录}/策划/head_prompt_1.txt
    {项目目录}/策划/head_prompt_2.txt
    ...
"""

import argparse
import json
import sys
from pathlib import Path


# 头图 Prompt 模板
TEMPLATES = {
    "main": """电商商品主视觉图，作为详情页首屏或主图轮播第一张。
商品：{brand} {product}，{category}。
核心利益：{core_benefit}

画面要求：
- 商品主体清晰，占画面主要区域（60-70%）
- 背景：{background_type}，轻微阴影增加立体感
- 商品形态：{structure}结构，真实产品形态
- 文案克制：品牌名 + 产品名，可加一句短利益点
- 视觉层级：商品 > 标题 > 辅助元素
- 整体传递品牌调性和第一吸引力
- 全中文，禁止英文和占位符

风格参考：延续风格指南的 {style_tone} 调性。
产品参考：使用真实产品图，不臆造新形态。
""",

    "sellpoint": """电商核心卖点图，回答"为什么买它"。
商品：{brand} {product}，{category}。
核心卖点：{sellpoints_text}

画面要求：
- 商品主体居中或左侧，清晰展示
- 卖点标签清晰：将参数转化为用户利益
{sellpoints_list}
- 卖点数量控制在 1-3 个，不超过 4 个
- 视觉形式：标签、图标、局部放大说明
- 整体简洁有力，不堆砌信息
- 全中文，禁止英文和占位符

风格参考：延续风格指南的 {style_tone} 调性。
""",

    "scene": """电商使用场景图，让用户产生代入感。
商品：{brand} {product}，{category}。
目标人群：{target_audience}
使用场景：{usage_scene}

画面要求：
- 商品在真实/理想化场景中使用
- 传递"我在这种场景下使用它"的感觉
- 场景氛围：{scene_atmosphere}
- 商品不能太小，要清晰可识别
- 可展示使用结果或效果感
- 全中文，禁止英文和占位符

风格参考：延续风格指南的 {style_tone} 调性。
""",

    "detail": """电商细节证明图，展示品质/材质/工艺。
商品：{brand} {product}，{category}。
证明重点：{proof_focus}

画面要求：
- 局部放大展示关键细节
- 可展示：{detail_items}
- 传递"品质可信、做工可靠"
- 视觉形式：放大特写 + 说明标注
- 如有认证/检测信息可适度展示
- 全中文，禁止英文和占位符

风格参考：延续风格指南的 {style_tone} 调性。
""",

    "spec": """电商规格确认图，告诉用户"买到什么"。
商品：{brand} {product}，{category}。
规格信息：{spec_info}

画面要求：
- 展示包装、套装内容、配件明细
- 明确规格：{spec_details}
- 可展示多颜色/SKU选择（如有）
- 传递"下单后收到这些"
- 减少售前疑虑
- 全中文，禁止英文和占位符

风格参考：延续风格指南的 {style_tone} 调性。
包装参考：使用真实包装图，不臆造新包装。
""",

    # 高客单复杂品额外图
    "dimension": """电商尺寸适配图，展示规格和空间关系。
商品：{brand} {product}，{category}。
尺寸信息：{dimension_info}

画面要求：
- 清晰展示尺寸/容量/重量
- 可加入空间比例参考图
- 适配信息：适用人群/场景/设备
- 减少用户对尺寸的疑虑
- 全中文，禁止英文和占位符

风格参考：延续风格指南调性。
""",

    "warranty": """电商售后保障图，传递购买信心。
商品：{brand} {product}，{category}。
保障信息：{warranty_info}

画面要求：
- 展示售后政策、质保期限、退换规则
- 可展示认证、检测报告、资质
- 传递"购买有保障，放心下单"
- 全中文，禁止英文和占位符

风格参考：延续风格指南调性。
"""
}


def load_facts(project_dir: Path) -> dict:
    """读取产品事实文件"""
    facts_path = project_dir / "facts.json"
    if not facts_path.exists():
        raise FileNotFoundError(f"facts.json 不存在: {facts_path}")
    return json.loads(facts_path.read_text(encoding="utf-8"))


def load_strategy(project_dir: Path) -> dict:
    """读取策略文件，提取关键信息"""
    strategy_path = project_dir / "策划" / "strategy_v1.md"
    if not strategy_path.exists():
        return {}

    content = strategy_path.read_text(encoding="utf-8")
    # 简单提取关键信息
    result = {}
    for line in content.split("\n"):
        if "一句话总策略" in line or "总策略" in line:
            result["core_strategy"] = line.split("：")[-1].strip() if "：" in line else ""
        if "目标用户" in line or "目标人群" in line:
            result["target_audience"] = line.split("：")[-1].strip() if "：" in line else ""
    return result


def determine_head_count(facts: dict) -> int:
    """根据商品复杂度判断头图数量"""
    price = facts.get("price", 0)
    if isinstance(price, str):
        # 解析价格字符串
        price = float(price.replace("元", "").replace("¥", "").strip()) if price else 0

    skus = facts.get("skus", [])
    flavors = facts.get("flavors", [])

    # 判断逻辑
    if price < 30 or (len(skus) <= 1 and len(flavors) <= 1):
        return 3  # 低价简单品
    elif price > 200 or len(skus) > 3 or len(flavors) > 5:
        return 7  # 高客单复杂品
    else:
        return 5  # 标准普通品（默认）


def create_prompts(project_dir: Path, facts: dict, strategy: dict, head_count: int) -> list:
    """生成头图 prompt 文件"""
    prompts_dir = project_dir / "策划"
    prompts_dir.mkdir(exist_ok=True)

    # 提取事实信息
    brand = facts.get("brand", "")
    product = facts.get("product", "")
    category = facts.get("category", "")
    structure = facts.get("structure", "")
    flavors = facts.get("flavors", [])
    sellpoints = facts.get("sellpoints", [])
    style_tone = facts.get("style_tone", "法式轻奢")

    # 推断其他信息
    background_type = "干净白底或浅奶油色底" if category in ["食品", "零食", "烘焙"] else "浅灰底或场景氛围"
    target_audience = strategy.get("target_audience", facts.get("target_audience", "年轻白领、品质生活追求者"))
    usage_scene = facts.get("usage_scene", "办公室下午茶、家庭休闲时刻、朋友聚会分享")
    scene_atmosphere = facts.get("scene_atmosphere", "温馨、放松、品质感")
    proof_focus = facts.get("proof_focus", "原料品质、工艺细节")
    detail_items = facts.get("detail_items", "材质纹理、结构拆解、成分说明、工艺特写")
    spec_info = facts.get("spec_info", "包装规格、内容物、数量")
    spec_details = facts.get("spec_details", f"{facts.get('weight', '160g')} / {facts.get('count', '20片')} / 独立包装")

    # 核心利益（取第一个卖点或默认）
    core_benefit = sellpoints[0] if sellpoints else "优质原料，美味享受"

    # 卖点列表格式化
    sellpoints_text = "、".join(sellpoints[:3]) if sellpoints else "优质原料、法式工艺、多层口感"
    sellpoints_list = ""
    for i, sp in enumerate(sellpoints[:3], 1):
        sellpoints_list += f"  - {sp} → 传递用户利益\n"

    # 生成 prompt 文件
    prompt_files = []

    # 标准顺序：main, sellpoint, scene, detail, spec
    order = ["main", "sellpoint", "scene", "detail", "spec"]

    # 高客单复杂品增加 dimension, warranty
    if head_count >= 7:
        order.extend(["dimension", "warranty"])

    # 低价简单品只保留 main, sellpoint, spec
    if head_count == 3:
        order = ["main", "sellpoint", "spec"]

    for i, key in enumerate(order[:head_count], 1):
        template = TEMPLATES.get(key, TEMPLATES["main"])

        # 根据模板填充参数
        prompt_content = template.format(
            brand=brand,
            product=product,
            category=category,
            structure=structure,
            style_tone=style_tone,
            background_type=background_type,
            core_benefit=core_benefit,
            sellpoints_text=sellpoints_text,
            sellpoints_list=sellpoints_list,
            target_audience=target_audience,
            usage_scene=usage_scene,
            scene_atmosphere=scene_atmosphere,
            proof_focus=proof_focus,
            detail_items=detail_items,
            spec_info=spec_info,
            spec_details=spec_details,
            dimension_info=facts.get("dimension", "详见产品参数"),
            warranty_info=facts.get("warranty", "品质保障、售后无忧"),
        )

        prompt_path = prompts_dir / f"head_prompt_{i}.txt"
        prompt_path.write_text(prompt_content, encoding="utf-8")
        prompt_files.append(str(prompt_path))
        print(f"生成: {prompt_path}")

    return prompt_files


def main():
    parser = argparse.ArgumentParser(description="生成头图 prompt 文件")
    parser.add_argument("--project-dir", required=True, help="项目目录路径")
    parser.add_argument("--version", default="v1", help="版本号")
    parser.add_argument("--count", type=int, default=None, help="手动指定头图数量（3/5/7）")

    args = parser.parse_args()
    project_dir = Path(args.project_dir)

    if not project_dir.exists():
        raise SystemExit(f"项目目录不存在: {project_dir}")

    # 加载事实和策略
    facts = load_facts(project_dir)
    strategy = load_strategy(project_dir)

    # 判断头图数量
    head_count = args.count or determine_head_count(facts)
    print(f"商品类型判断: {facts.get('product', '')} → 头图数量 {head_count} 张")

    # 生成 prompt 文件
    prompt_files = create_prompts(project_dir, facts, strategy, head_count)

    # 输出策略摘要
    strategy_path = project_dir / "策划" / "head_image_strategy_v1.md"
    strategy_content = f"""# 头图策略 v1

## 商品信息
- 品牌：{facts.get('brand', '')}
- 产品：{facts.get('product', '')}
- 品类：{facts.get('category', '')}

## 头图数量
- 判断依据：{facts.get('price', 0)}元，{len(facts.get('skus', []))}SKU，{len(facts.get('flavors', []))}口味
- 头图数量：{head_count} 张

## 头图分工

"""
    order_desc = {
        "main": "主视觉图 - 商品识别 + 第一吸引",
        "sellpoint": "核心卖点图 - 为什么买（参数转利益）",
        "scene": "使用场景图 - 代入感",
        "detail": "细节证明图 - 品质信任",
        "spec": "规格确认图 - 下单确认",
        "dimension": "尺寸适配图 - 规格疑虑",
        "warranty": "售后保障图 - 购买信心",
    }

    order = ["main", "sellpoint", "scene", "detail", "spec"]
    if head_count >= 7:
        order.extend(["dimension", "warranty"])
    if head_count == 3:
        order = ["main", "sellpoint", "spec"]

    for i, key in enumerate(order[:head_count], 1):
        strategy_content += f"| 第{i}张 | {order_desc.get(key, key)} | head_prompt_{i}.txt |\n"

    strategy_content += f"""
## 执行命令

```bash
bash scripts/generate_head_images.sh {project_dir} {args.version} 1440x1440
```

## 风格统一

所有头图共用：
- style_guide.png
- 产品参考图
- 品牌 LOGO
"""

    strategy_path.write_text(strategy_content, encoding="utf-8")
    print(f"策略文件: {strategy_path}")

    print(f"\n完成：生成 {len(prompt_files)} 个 prompt 文件")


if __name__ == "__main__":
    main()
