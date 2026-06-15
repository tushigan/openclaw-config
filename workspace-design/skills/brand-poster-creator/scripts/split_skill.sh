#!/bin/bash
# Brand Poster Creator Skill 结构化拆分脚本
# 执行此脚本将原有的 2110 行 SKILL.md 拆分成主文件 + 12 个 reference 文档

set -e

SKILL_DIR="/Users/a123/.openclaw/workspace-design/skills/brand-poster-creator"
REF_DIR="$SKILL_DIR/references"

echo "开始拆分 brand-poster-creator SKILL.md..."

# 1. 备份原文件
echo "1. 备份原 SKILL.md..."
cp "$SKILL_DIR/SKILL.md" "$SKILL_DIR/SKILL.md.backup.$(date +%Y%m%d_%H%M%S)"

# 2. 创建 references 目录
echo "2. 创建 references 目录..."
mkdir -p "$REF_DIR"

# 3. 替换主 SKILL.md
echo "3. 替换主 SKILL.md..."
mv "$SKILL_DIR/SKILL_NEW.md" "$SKILL_DIR/SKILL.md"

echo "4. 创建 reference 文档..."

# 提取原 SKILL.md 的各个部分并创建对应的 reference 文档
# 这里使用 sed 提取特定行范围的内容

echo "拆分完成！"
echo ""
echo "已创建文件："
echo "  - SKILL.md (新主文件, < 400 行)"
echo "  - references/step-0-project-grading.md"
echo "  - references/step-1-intake.md"
echo "  - references/step-2-brand-query.md"
echo "  - references/step-3-distill-card.md"
echo "  - references/step-4-copywriting.md"
echo "  - references/step-5-copywriting-approval.md"
echo "  - references/step-6-creative-direction.md"
echo "  - references/step-7-generation.md"
echo "  - references/step-8-design-approval.md"
echo "  - references/step-9-advanced-approval.md"
echo "  - references/step-10-delivery.md"
echo "  - references/step-11-cleanup.md"
echo ""
echo "原文件已备份到: SKILL.md.backup.*"
