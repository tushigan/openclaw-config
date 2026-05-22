#!/bin/bash
# 详情页分段批量生成脚本
#
# 用法：
#   bash scripts/generate_segment_batch.sh --project-dir /path/to/project [--version v1] [--size 1152x3456]
#
# 输出：
#   {项目目录}/设计/{版本}/segment_A.png
#   {项目目录}/设计/{版本}/segment_B.png
#   ...

set -euo pipefail

PROJECT_DIR=""
VERSION="v1"
SIZE="1152x3456"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --size)
            SIZE="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$PROJECT_DIR" ]]; then
    echo "必须指定 --project-dir" >&2
    exit 1
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "项目目录不存在: $PROJECT_DIR" >&2
    exit 1
fi

DESIGN_DIR="$PROJECT_DIR/设计/$VERSION"
PLANNING_DIR="$PROJECT_DIR/策划"
PROMPT_PACKAGE_DIR="$PLANNING_DIR/prompt_package"
GEN_SCRIPT="${DETAIL_PAGE_GEN_SCRIPT:-/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py}"
STYLE_GUIDE="$PROJECT_DIR/style_guide.png"
FACTS_FILE="$PROJECT_DIR/facts.json"
PLATFORM_PROFILE="$PROJECT_DIR/platform_profile.json"
CATEGORY_PROFILE="$PROJECT_DIR/category_profile.json"
DESIGN_PROMPT_BASE="$PROMPT_PACKAGE_DIR/design_segment_base.txt"
WIREFRAME_PROMPT_BASE="$PROMPT_PACKAGE_DIR/wireframe_base.txt"
DATA_LOOKUP_SCRIPT="/Users/a123/.openclaw/skills/xiangqingye-desigen/scripts/project_data_lookup.py"
IMAGE_PROBE_SCRIPT="/Users/a123/.openclaw/skills/xiangqingye-desigen/scripts/probe_image_size.py"
REGISTRY="$PROJECT_DIR/asset_registry.json"
KNOWLEDGE_CONFIRMED="$PROJECT_DIR/策划/brand_knowledge_confirmed.json"
CUT_PREVIEW_DIR="$PROJECT_DIR/手稿/$VERSION/cut_preview"
LEGACY_CUT_PREVIEW_DIR="$PROJECT_DIR/手稿/cut_preview_$VERSION"

REF_LOGO=""
REF_PRODUCT=""
REF_PACKAGING=""
CUT_SOURCE_DIR=""

if [[ ! -f "$REGISTRY" ]]; then
    echo "缺少 asset_registry.json，请先确认品牌资产并生成正式素材注册表" >&2
    exit 1
fi

for required_file in "$FACTS_FILE" "$PLATFORM_PROFILE" "$CATEGORY_PROFILE" "$DESIGN_PROMPT_BASE" "$WIREFRAME_PROMPT_BASE"; do
    if [[ ! -f "$required_file" ]]; then
        echo "缺少阶段必需文件: $required_file" >&2
        exit 1
    fi
done

if [[ ! -f "$STYLE_GUIDE" ]]; then
    echo "缺少 style_guide.png，请先完成策略阶段并生成全局风格指南" >&2
    exit 1
fi

if [[ ! -f "$KNOWLEDGE_CONFIRMED" ]]; then
    echo "未找到已确认的品牌知识摘要，将继续仅使用基础 prompt package" >&2
fi

REF_LOGO=$(python3 "$DATA_LOOKUP_SCRIPT" asset --registry "$REGISTRY" --role brand_logo)
REF_PRODUCT=$(python3 "$DATA_LOOKUP_SCRIPT" asset --registry "$REGISTRY" --role product_main)
REF_PACKAGING=$(python3 "$DATA_LOOKUP_SCRIPT" asset --registry "$REGISTRY" --role packaging)

if [[ -z "$REF_PRODUCT" ]]; then
    echo "素材注册表中缺少 product_main，成稿阶段不能继续" >&2
    exit 1
fi

if [[ -d "$CUT_PREVIEW_DIR" ]]; then
    CUT_SOURCE_DIR="$CUT_PREVIEW_DIR"
elif [[ -d "$LEGACY_CUT_PREVIEW_DIR" ]]; then
    CUT_SOURCE_DIR="$LEGACY_CUT_PREVIEW_DIR"
else
    echo "缺少手稿切段目录，请先完成手稿 QA 与切段确认: $CUT_PREVIEW_DIR" >&2
    exit 1
fi

CUT_MANIFEST="$CUT_SOURCE_DIR/cut_manifest.json"

if [[ ! -f "$CUT_MANIFEST" ]]; then
    echo "缺少确认切段清单，不能直接消费通用 cut_preview 目录: $CUT_MANIFEST" >&2
    exit 1
fi

CUT_STATUS=$(python3 "$DATA_LOOKUP_SCRIPT" manifest-status --manifest "$CUT_MANIFEST")
if [[ "$CUT_STATUS" != "confirmed" ]]; then
    echo "切段清单未确认，不能进入成稿阶段: $CUT_MANIFEST" >&2
    exit 1
fi

echo "========== 分段成稿批量生成 =========="
echo "项目目录: $PROJECT_DIR"
echo "版本: $VERSION"
echo "尺寸: $SIZE"
echo "输出目录: $DESIGN_DIR"
echo "切段来源: $CUT_SOURCE_DIR"
echo ""
echo "关键输入文件:"
echo "- $FACTS_FILE"
echo "- $REGISTRY"
echo "- $PLATFORM_PROFILE"
echo "- $CATEGORY_PROFILE"
echo "- $STYLE_GUIDE"
echo "- $DESIGN_PROMPT_BASE"
echo "- $WIREFRAME_PROMPT_BASE"
echo ""
echo "参考图角色:"
echo "- brand_logo: ${REF_LOGO:-未提供}"
echo "- product_main: ${REF_PRODUCT:-未提供}"
echo "- packaging: ${REF_PACKAGING:-未提供}"
echo ""

resolve_confirmed_segment_file() {
    local SEGMENT_KEY="$1"
    python3 "$DATA_LOOKUP_SCRIPT" segment-file --manifest "$CUT_MANIFEST" --segment-key "$SEGMENT_KEY"
}

generate_segment() {
    local SEGMENT_KEY="$1"
    local PROMPT_FILE="$DESIGN_DIR/prompt_${SEGMENT_KEY}.txt"
    local CONFIRMED_FILE
    CONFIRMED_FILE=$(resolve_confirmed_segment_file "$SEGMENT_KEY")
    local WIREFRAME_FILE="$CUT_SOURCE_DIR/$CONFIRMED_FILE"
    local OUTPUT_FILE="$DESIGN_DIR/segment_${SEGMENT_KEY}.png"
    local EXTRA_ARGS=""

    if [[ -z "$CONFIRMED_FILE" ]]; then
        echo "切段清单中未找到 segment_${SEGMENT_KEY} 的 confirmed_file: $CUT_MANIFEST" >&2
        return 1
    fi

    if [[ ! -f "$PROMPT_FILE" ]]; then
        echo "缺少分段 prompt 文件: $PROMPT_FILE" >&2
        return 1
    fi

    if [[ ! -f "$WIREFRAME_FILE" ]]; then
        echo "缺少手稿切段图: $WIREFRAME_FILE" >&2
        return 1
    fi

    echo ">>> 生成分段: $OUTPUT_FILE"

    local -a CMD=("python3" "$GEN_SCRIPT" "--prompt-file" "$PROMPT_FILE" "-r" "$WIREFRAME_FILE" "-s" "$SIZE" "-o" "$OUTPUT_FILE")

    if [[ -f "$STYLE_GUIDE" ]]; then
        CMD+=("--ref-style" "$STYLE_GUIDE")
    fi

    if [[ -n "$REF_PRODUCT" && -f "$REF_PRODUCT" ]]; then
        CMD+=("--ref-product" "$REF_PRODUCT")
    fi

    if [[ -n "$REF_LOGO" && -f "$REF_LOGO" ]]; then
        CMD+=("--ref-logo" "$REF_LOGO")
    fi

    if [[ "$SEGMENT_KEY" == "D" && -n "$REF_PACKAGING" && -f "$REF_PACKAGING" ]]; then
        EXTRA_ARGS="--ref-element $REF_PACKAGING"
    fi

    if [[ -n "$EXTRA_ARGS" ]]; then
        # shellcheck disable=SC2206
        local EXTRA_PARTS=($EXTRA_ARGS)
        CMD+=("${EXTRA_PARTS[@]}")
    fi

    "${CMD[@]}"

    if [[ -f "$OUTPUT_FILE" ]]; then
        local SIZE_ACTUAL
        SIZE_ACTUAL=$(python3 "$IMAGE_PROBE_SCRIPT" "$OUTPUT_FILE")
        echo "完成: $OUTPUT_FILE ($SIZE_ACTUAL)"
    else
        echo "失败: $OUTPUT_FILE 未生成" >&2
        return 1
    fi
}

PROMPT_COUNT=$(ls "$DESIGN_DIR"/prompt_*.txt 2>/dev/null | wc -l | tr -d ' ')
if [[ "$PROMPT_COUNT" -eq 0 ]]; then
    echo "未找到分段 prompt 文件，请先执行：" >&2
    echo "  python3 scripts/create_design_segment_prompts.py --project-dir $PROJECT_DIR --version $VERSION" >&2
    exit 1
fi

echo "找到 $PROMPT_COUNT 个分段 prompt 文件"

GENERATED_COUNT=0
for prompt_path in "$DESIGN_DIR"/prompt_*.txt; do
    if [[ ! -f "$prompt_path" ]]; then
        continue
    fi
    prompt_name=$(basename "$prompt_path")
    segment_key=${prompt_name#prompt_}
    segment_key=${segment_key%.txt}
    generate_segment "$segment_key"
    GENERATED_COUNT=$((GENERATED_COUNT + 1))
done

if [[ "$GENERATED_COUNT" -eq 0 ]]; then
    echo "没有生成任何分段，请检查 prompt 文件命名是否为 prompt_A.txt / prompt_B.txt 等格式" >&2
    exit 1
fi

echo ""
echo "========== 生成完成 =========="
echo "输出目录: $DESIGN_DIR"
echo ""
echo "生成文件:"
find "$DESIGN_DIR" -maxdepth 1 -name 'segment_*.png' -print | sort

echo ""
echo "建议下一步："
echo "   python scripts/validate_segment_boundaries.py $DESIGN_DIR/segment_A.png $DESIGN_DIR/segment_B.png $DESIGN_DIR/segment_C.png $DESIGN_DIR/segment_D.png --report $DESIGN_DIR/boundary_check_report.json"
echo "   python scripts/hard_concat.py $DESIGN_DIR/merged_final.png $DESIGN_DIR/segment_A.png $DESIGN_DIR/segment_B.png $DESIGN_DIR/segment_C.png $DESIGN_DIR/segment_D.png"
echo "   python scripts/validate_delivery.py --project-dir $PROJECT_DIR"
echo "   bash scripts/deliver_package.sh --project-dir $PROJECT_DIR --output-dir $PROJECT_DIR/交付"
