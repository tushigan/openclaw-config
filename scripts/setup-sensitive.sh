#!/bin/bash
# setup-sensitive.sh - 从脱敏模板恢复敏感配置文件
#
# 用法:
#   ./scripts/setup-sensitive.sh [openclaw-dir]
#
# 功能:
#   1. 扫描所有 .json.template 文件
#   2. 如果对应 .json 不存在，从模板复制
#   3. 列出需要手动填写的占位符

set -e

OPENCLAW_DIR="${1:-$HOME/.openclaw}"

if [ ! -d "$OPENCLAW_DIR" ]; then
    echo "错误: 目录不存在: $OPENCLAW_DIR"
    exit 1
fi

cd "$OPENCLAW_DIR"

echo "扫描脱敏模板..."
echo ""

created=0
existing=0

for template in $(find . -name "*.json.template" -not -path "./.git/*" 2>/dev/null); do
    target="${template%.template}"
    rel_template="${template#./}"
    rel_target="${target#./}"

    if [ ! -f "$target" ]; then
        cp "$template" "$target"
        echo "  ✅ 创建: $rel_target (来自 $rel_template)"
        created=$((created + 1))
    else
        echo "  ⏭️  已存在: $rel_target"
        existing=$((existing + 1))
    fi
done

echo ""
echo "统计: 新建 $created 个, 已存在 $existing 个"

if [ $created -gt 0 ]; then
    echo ""
    echo "=========================================="
    echo "  需要手动配置以下占位符"
    echo "=========================================="
    echo ""

    # 搜索所有占位符
    placeholders=$(grep -rn '{{' agents/*/agent/models.json agents/*/agent/auth-profiles.json openclaw.json 2>/dev/null | grep -v '.template' || true)

    if [ -n "$placeholders" ]; then
        echo "$placeholders" | sed 's/^/  /'
        echo ""
        echo "请编辑上述文件，将 {{...}} 占位符替换为真实值。"
    fi
fi
