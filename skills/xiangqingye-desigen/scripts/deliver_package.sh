#!/bin/bash
# 详情页交付打包脚本
# 功能：压缩设计稿 + 分卷处理（飞书文件上限 30MB）
#
# 用法：
#   bash deliver_package.sh --project-dir /path/to/project [--output-dir /path/to/output]
#
# 输出：
#   - 如果总大小 ≤ 28MB：单个 ZIP 文件
#   - 如果总大小 > 28MB：分卷 ZIP（每卷 28MB）
#   - 输出文件列表到 stdout，供飞书发送

set -euo pipefail

# ========== 参数解析 ==========

PROJECT_DIR=""
OUTPUT_DIR=""
PROJECT_NAME=""
HEAD_IMAGES_REQUIRED="true"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
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

# 自动提取项目名
PROJECT_NAME=$(basename "$PROJECT_DIR" | sed 's/_[0-9]*$//')

# 默认输出目录为项目下的 交付/
if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="$PROJECT_DIR/交付"
fi

PROGRESS_FILE="$PROJECT_DIR/progress.json"
if [[ -f "$PROGRESS_FILE" ]]; then
    HEAD_FLAG=$(python3 - "$PROGRESS_FILE" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding='utf-8'))
flags = data.get('workflow_flags', {})
value = flags.get('head_images_required', True)
print('true' if value else 'false')
PY
)
    if [[ "$HEAD_FLAG" == "false" ]]; then
        HEAD_IMAGES_REQUIRED="false"
    fi
fi

# ========== 交付前门禁检查 ==========

REQUIRED_PROJECT_FILES=(
    "$PROJECT_DIR/facts.json"
    "$PROJECT_DIR/asset_registry.json"
    "$PROJECT_DIR/platform_profile.json"
    "$PROJECT_DIR/category_profile.json"
    "$PROJECT_DIR/策划/strategy_v1.md"
    "$PROJECT_DIR/策划/copywriting_v1.md"
)

for required_file in "${REQUIRED_PROJECT_FILES[@]}"; do
    if [[ ! -f "$required_file" ]]; then
        echo "缺少交付必需文件: $required_file" >&2
        exit 1
    fi
done

# ========== 查找设计稿文件 ==========

DESIGN_DIR="$PROJECT_DIR/设计"

# 找最新版本的目录
LATEST_VERSION=$(ls -d "$DESIGN_DIR"/v* 2>/dev/null | sort -V | tail -1 || true)
if [[ -z "$LATEST_VERSION" ]]; then
    # 尝试直接在 设计/ 下找
    if [[ -d "$DESIGN_DIR" ]]; then
        LATEST_VERSION="$DESIGN_DIR"
    else
        echo "找不到设计稿目录: $DESIGN_DIR" >&2
        exit 1
    fi
fi

echo "设计稿目录: $LATEST_VERSION"

# 收集要打包的文件
FILES_TO_PACK=()

# 添加拼接长图
if [[ -f "$LATEST_VERSION/merged_final.png" ]]; then
    FILES_TO_PACK+=("$LATEST_VERSION/merged_final.png")
fi

# 添加各段设计稿
for seg in segment_A segment_B segment_C segment_D segment_1 segment_2 segment_3 segment_4; do
    for ext in png jpg; do
        if [[ -f "$LATEST_VERSION/${seg}.${ext}" ]]; then
            FILES_TO_PACK+=("$LATEST_VERSION/${seg}.${ext}")
        fi
    done
done

# 添加从切段生成的文件
for f in "$LATEST_VERSION"/segment_*_from_cut.png; do
    if [[ -f "$f" ]]; then
        FILES_TO_PACK+=("$f")
    fi
done

# 添加重建版本
for f in "$LATEST_VERSION"/segment_*_rebuilt.png; do
    if [[ -f "$f" ]]; then
        FILES_TO_PACK+=("$f")
    fi
done

# ========== 查找头图文件 ==========

HEAD_DIR="$PROJECT_DIR/头图"
HEAD_VERSION=$(ls -d "$HEAD_DIR"/v* 2>/dev/null | sort -V | tail -1 || true)

if [[ -n "$HEAD_VERSION" ]]; then
    echo "头图目录: $HEAD_VERSION"
    # 添加头图
    for f in "$HEAD_VERSION"/head_*.png; do
        if [[ -f "$f" ]]; then
            FILES_TO_PACK+=("$f")
        fi
    done
fi

# 添加交付清单和关键项目文件
for f in "$OUTPUT_DIR"/deliver_manifest.json "$PROJECT_DIR"/facts.json "$PROJECT_DIR"/asset_registry.json "$PROJECT_DIR"/platform_profile.json "$PROJECT_DIR"/category_profile.json "$PROJECT_DIR"/策划/strategy_v1.md "$PROJECT_DIR"/策划/copywriting_v1.md; do
    if [[ -f "$f" ]]; then
        FILES_TO_PACK+=("$f")
    fi
done

if [[ ${#FILES_TO_PACK[@]} -eq 0 ]]; then
    echo "没有找到设计稿文件" >&2
    exit 1
fi

if [[ ! -f "$LATEST_VERSION/merged_final.png" ]]; then
    echo "缺少最终拼接长图 merged_final.png，不能打包交付" >&2
    exit 1
fi

if [[ "$HEAD_IMAGES_REQUIRED" == "true" && -z "$HEAD_VERSION" ]]; then
    echo "缺少头图目录，不能按整套详情页交付" >&2
    exit 1
fi

echo "待打包文件:"
for f in "${FILES_TO_PACK[@]}"; do
    echo "  - $f"
done

# ========== 计算总大小 ==========

TOTAL_SIZE=0
for f in "${FILES_TO_PACK[@]}"; do
    SIZE=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
    TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
done

TOTAL_SIZE_MB=$((TOTAL_SIZE / 1024 / 1024))
echo "总大小: ${TOTAL_SIZE_MB}MB"

# ========== 创建输出目录 ==========

mkdir -p "$OUTPUT_DIR"

# ========== 执行压缩 ==========

ZIP_BASENAME="${PROJECT_NAME}_交付"
ZIP_PATH="$OUTPUT_DIR/$ZIP_BASENAME.zip"

# 飞书文件上限 30MB，预留 2MB 余量，使用 28MB 分卷阈值
SPLIT_THRESHOLD=28  # MB

if [[ $TOTAL_SIZE_MB -le $SPLIT_THRESHOLD ]]; then
    # 不需要分卷，直接压缩
    echo "打包为单个 ZIP..."
    zip -j "$ZIP_PATH" "${FILES_TO_PACK[@]}"
    echo "生成: $ZIP_PATH"
    FINAL_FILES=("$ZIP_PATH")
else
    # 需要分卷压缩
    echo "打包为分卷 ZIP（每卷 ${SPLIT_THRESHOLD}MB）..."
    # 先创建临时完整 ZIP
    TEMP_ZIP="$OUTPUT_DIR/.temp_full.zip"
    zip -j "$TEMP_ZIP" "${FILES_TO_PACK[@]}"
    # 分卷
    zip -s ${SPLIT_THRESHOLD}m "$TEMP_ZIP" --out "$ZIP_PATH"
    # 删除临时文件
    rm -f "$TEMP_ZIP"
    # 收集分卷文件
    FINAL_FILES=()
    for f in "$OUTPUT_DIR"/$ZIP_BASENAME.z[0-9][0-9] "$ZIP_PATH"; do
        if [[ -f "$f" ]]; then
            FINAL_FILES+=("$f")
            echo "生成: $f"
        fi
    done
fi

# ========== 输出结果 ==========

echo ""
echo "========== 交付文件列表 ========== "
for f in "${FINAL_FILES[@]}"; do
    SIZE=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
    SIZE_MB=$((SIZE / 1024 / 1024))
    echo "$f (${SIZE_MB}MB)"
done

echo ""
echo "FINAL_DELIVERY_MODE:file_zip"
echo "FINAL_DELIVERY_RULE:禁止直接发送 merged_final.png、segment_*.png、head_*.png；必须发送 ZIP/分卷文件"
echo ""
echo "飞书发送指引："
echo "1. 将以上 ZIP/分卷文件复制到飞书交付目录："
echo "   cp ${FINAL_FILES[*]} /Users/a123/.openclaw/workspace/feishu-deliver/"
echo "2. 使用飞书发文件能力逐个发送"
echo "3. 如有分卷，必须发送所有分卷文件；不要改为图片发送"

# 输出文件路径列表（供其他脚本/agent 使用）
echo ""
echo "DELIVER_FILES:"
for f in "${FINAL_FILES[@]}"; do
    echo "$f"
done
