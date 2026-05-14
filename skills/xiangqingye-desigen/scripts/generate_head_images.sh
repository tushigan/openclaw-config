#!/bin/bash
# 5张头图批量生成脚本
#
# 用法：
#   bash scripts/generate_head_images.sh {项目目录} [版本号] [尺寸]
#
# 示例：
#   bash scripts/generate_head_images.sh /path/to/project v1 800x800
#
# 输出：
#   {项目目录}/头图/v1/head_1_main.png
#   {项目目录}/头图/v1/head_2_sellpoint.png
#   ...

set -euo pipefail

# ========== 参数解析 ==========

PROJECT_DIR="${1:-}"
VERSION="${2:-v1}"
SIZE="${3:-800x800}"

if [[ -z "$PROJECT_DIR" ]]; then
    echo "必须指定项目目录" >&2
    exit 1
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "项目目录不存在: $PROJECT_DIR" >&2
    exit 1
fi

# ========== 路径配置 ==========

HEAD_DIR="$PROJECT_DIR/头图/$VERSION"
PLANNING_DIR="$PROJECT_DIR/策划"
PROMPT_PACKAGE_DIR="$PLANNING_DIR/prompt_package"
REF_DIR="$PROJECT_DIR/参考"

GEN_SCRIPT="/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py"
STYLE_GUIDE="$PROJECT_DIR/style_guide.png"
FACTS_FILE="$PROJECT_DIR/facts.json"
PLATFORM_PROFILE="$PROJECT_DIR/platform_profile.json"
CATEGORY_PROFILE="$PROJECT_DIR/category_profile.json"
WIREFRAME_PROMPT_BASE="$PROMPT_PACKAGE_DIR/wireframe_base.txt"
HEAD_PROMPT_BASE="$PROMPT_PACKAGE_DIR/head_image_base.txt"
DATA_LOOKUP_SCRIPT="/Users/a123/.openclaw/skills/xiangqingye-desigen/scripts/project_data_lookup.py"
IMAGE_PROBE_SCRIPT="/Users/a123/.openclaw/skills/xiangqingye-desigen/scripts/probe_image_size.py"

# 参考图（优先读取 asset_registry.json，缺失时按文件名兜底）
REGISTRY="$PROJECT_DIR/asset_registry.json"
KNOWLEDGE_CONFIRMED="$PROJECT_DIR/策划/brand_knowledge_confirmed.json"
REF_LOGO=""
REF_PRODUCT=""
REF_PACKAGING=""

if [[ ! -f "$REGISTRY" ]]; then
    echo "缺少 asset_registry.json，请先确认品牌资产并生成正式素材注册表" >&2
    exit 1
fi

for required_file in "$FACTS_FILE" "$PLATFORM_PROFILE" "$CATEGORY_PROFILE" "$HEAD_PROMPT_BASE"; do
    if [[ ! -f "$required_file" ]]; then
        echo "缺少阶段必需文件: $required_file" >&2
        exit 1
    fi
done

if [[ ! -f "$STYLE_GUIDE" ]]; then
    echo "缺少 style_guide.png，请先完成策略阶段并生成全局风格指南" >&2
    exit 1
fi

if [[ ! -f "$WIREFRAME_PROMPT_BASE" ]]; then
    echo "缺少 wireframe_base.txt，说明项目 prompt package 尚未完整生成" >&2
    exit 1
fi

if [[ ! -f "$KNOWLEDGE_CONFIRMED" ]]; then
    echo "未找到已确认的品牌知识摘要，将继续仅使用基础 prompt package" >&2
fi

if [[ -f "$REGISTRY" ]]; then
    REF_LOGO=$(python3 "$DATA_LOOKUP_SCRIPT" asset --registry "$REGISTRY" --role brand_logo)
    REF_PRODUCT=$(python3 "$DATA_LOOKUP_SCRIPT" asset --registry "$REGISTRY" --role product_main)
    REF_PACKAGING=$(python3 "$DATA_LOOKUP_SCRIPT" asset --registry "$REGISTRY" --role packaging)
fi

if [[ -z "$REF_PRODUCT" ]]; then
    echo "素材注册表中缺少 product_main，头图阶段不能继续" >&2
    exit 1
fi

[[ -z "$REF_LOGO" ]] && REF_LOGO=$(ls "$REF_DIR"/品牌LOGO.* "$REF_DIR"/logo.* 2>/dev/null | head -1 || echo "")
[[ -z "$REF_PRODUCT" ]] && REF_PRODUCT=$(ls "$REF_DIR"/产品图* "$REF_DIR"/product* 2>/dev/null | head -1 || echo "")
[[ -z "$REF_PACKAGING" ]] && REF_PACKAGING=$(ls "$REF_DIR"/包装图* "$REF_DIR"/packaging* 2>/dev/null | head -1 || echo "")

mkdir -p "$HEAD_DIR"

echo "========== 头图批量生成 ========== "
echo "项目目录: $PROJECT_DIR"
echo "版本: $VERSION"
echo "尺寸: $SIZE"
echo "输出目录: $HEAD_DIR"
echo ""

# ========== 检查 prompt 文件 ==========

PROMPT_COUNT=$(ls "$PLANNING_DIR"/head_prompt_*.txt 2>/dev/null | wc -l | tr -d ' ')
if [[ "$PROMPT_COUNT" -eq 0 ]]; then
    echo "未找到 prompt 文件，请先执行：" >&2
    echo "  python3 scripts/create_head_prompts.py --project-dir $PROJECT_DIR" >&2
    exit 1
fi

echo "找到 $PROMPT_COUNT 个 prompt 文件"

# ========== 生成函数 ==========

generate_head_image() {
    local PROMPT_FILE="$1"
    local OUTPUT_FILE="$2"
    local EXTRA_ARGS="${3:-}"

    if [[ ! -f "$PROMPT_FILE" ]]; then
        echo "prompt 文件不存在: $PROMPT_FILE" >&2
        return 1
    fi

    echo ">>> 生成: $OUTPUT_FILE"

    # 构建命令（单行，避免复杂命令被网关拒绝）
    local CMD="python3 $GEN_SCRIPT --prompt-file $PROMPT_FILE -s $SIZE -o $OUTPUT_FILE"

    # 添加风格指南（必须）
    if [[ -f "$STYLE_GUIDE" ]]; then
        CMD="$CMD --ref-style $STYLE_GUIDE"
    fi

    # 添加产品参考图
    if [[ -n "$REF_PRODUCT" && -f "$REF_PRODUCT" ]]; then
        CMD="$CMD --ref-product $REF_PRODUCT"
    fi

    # 添加额外参数
    if [[ -n "$EXTRA_ARGS" ]]; then
        CMD="$CMD $EXTRA_ARGS"
    fi

    # 执行
    $CMD

    if [[ -f "$OUTPUT_FILE" ]]; then
        local SIZE_ACTUAL=$(python3 "$IMAGE_PROBE_SCRIPT" "$OUTPUT_FILE")
        echo "完成: $OUTPUT_FILE ($SIZE_ACTUAL)"
    else
        echo "失败: $OUTPUT_FILE 未生成" >&2
        return 1
    fi
}

# ========== 执行生成 ==========

# 第1张：主视觉图
if [[ -f "$PLANNING_DIR/head_prompt_1.txt" ]]; then
    EXTRA_ARGS=""
    [[ -n "$REF_LOGO" && -f "$REF_LOGO" ]] && EXTRA_ARGS="--ref-logo $REF_LOGO"
    generate_head_image "$PLANNING_DIR/head_prompt_1.txt" "$HEAD_DIR/head_1_main.png" "$EXTRA_ARGS"
fi

# 第2张：核心卖点图
if [[ -f "$PLANNING_DIR/head_prompt_2.txt" ]]; then
    generate_head_image "$PLANNING_DIR/head_prompt_2.txt" "$HEAD_DIR/head_2_sellpoint.png"
fi

# 第3张：使用场景图
if [[ -f "$PLANNING_DIR/head_prompt_3.txt" ]]; then
    generate_head_image "$PLANNING_DIR/head_prompt_3.txt" "$HEAD_DIR/head_3_scene.png"
fi

# 第4张：细节证明图
if [[ -f "$PLANNING_DIR/head_prompt_4.txt" ]]; then
    generate_head_image "$PLANNING_DIR/head_prompt_4.txt" "$HEAD_DIR/head_4_detail.png"
fi

# 第5张：规格确认图
if [[ -f "$PLANNING_DIR/head_prompt_5.txt" ]]; then
    EXTRA_ARGS=""
    [[ -n "$REF_PACKAGING" && -f "$REF_PACKAGING" ]] && EXTRA_ARGS="--ref-element $REF_PACKAGING"
    generate_head_image "$PLANNING_DIR/head_prompt_5.txt" "$HEAD_DIR/head_5_spec.png" "$EXTRA_ARGS"
fi

# 第6张：尺寸适配图（高客单复杂品）
if [[ -f "$PLANNING_DIR/head_prompt_6.txt" ]]; then
    generate_head_image "$PLANNING_DIR/head_prompt_6.txt" "$HEAD_DIR/head_6_dimension.png"
fi

# 第7张：售后保障图（高客单复杂品）
if [[ -f "$PLANNING_DIR/head_prompt_7.txt" ]]; then
    generate_head_image "$PLANNING_DIR/head_prompt_7.txt" "$HEAD_DIR/head_7_warranty.png"
fi

# ========== 输出结果 ==========

echo ""
echo "========== 生成完成 ========== "
echo "输出目录: $HEAD_DIR"
echo ""
echo "生成文件:"
ls -la "$HEAD_DIR/*.png" 2>/dev/null || echo "无 PNG 文件"

# ========== 飞书交付指引 ==========

echo ""
echo "飞书交付指引："
echo "1. 头图生成完成后，不要把这批 PNG 当最终交付逐张发送"
echo "2. 统一执行详情页交付检核与 deliver_package.sh 打包"
echo "3. 最终通过 ZIP/分卷文件发送整套交付物"
echo ""
echo "建议命令："
echo "   python scripts/validate_delivery.py --project-dir $PROJECT_DIR"
echo "   bash scripts/deliver_package.sh --project-dir $PROJECT_DIR --output-dir $PROJECT_DIR/交付"