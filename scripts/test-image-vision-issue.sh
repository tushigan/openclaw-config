#!/bin/bash

# 测试 Claude vs GPT 图片识别差异
# 用于诊断"完全看错图片"的问题

echo "=== 图片识别对比测试 ==="
echo ""
echo "请提供测试图片路径（被 Claude 看错的那张 PPT 截图）："
read IMAGE_PATH

if [ ! -f "$IMAGE_PATH" ]; then
    echo "❌ 文件不存在: $IMAGE_PATH"
    exit 1
fi

echo ""
echo "📸 测试图片: $IMAGE_PATH"
echo "文件大小: $(du -h "$IMAGE_PATH" | cut -f1)"
echo "图片尺寸: $(sips -g pixelWidth -g pixelHeight "$IMAGE_PATH" 2>/dev/null | grep -E 'pixelWidth|pixelHeight' | awk '{print $2}' | tr '\n' 'x' | sed 's/x$//')"
echo ""

# 创建临时测试提示
TEST_PROMPT="请详细描述这张图片的内容，包括：1. 主题是什么 2. 有哪些文字 3. 整体是什么类型的文档"

echo "=== 测试 1: GPT-5.4 (调研专家) ==="
echo "提示词: $TEST_PROMPT"
echo ""
echo "正在调用 research agent (GPT-5.4)..."
echo ""

# 使用 OpenClaw CLI 测试
openclaw chat research --image "$IMAGE_PATH" --message "$TEST_PROMPT" --timeout 60

echo ""
echo "=================================="
echo ""
echo "=== 测试 2: Claude Opus 4.6 (文案策划专家) ==="
echo "提示词: $TEST_PROMPT"
echo ""
echo "正在调用 copywriter agent (Claude Opus 4.6)..."
echo ""

openclaw chat copywriter --image "$IMAGE_PATH" --message "$TEST_PROMPT" --timeout 60

echo ""
echo "=================================="
echo ""
echo "✅ 测试完成"
echo ""
echo "请对比两个模型的回答："
echo "  - GPT-5.4 是否正确识别了图片内容？"
echo "  - Claude Opus 4.6 是否出现了'乱回'（识别成完全无关的内容）？"
echo ""
echo "如果 Claude 确实看错了，请执行以下命令查看详细会话："
echo "  openclaw sessions list copywriter"
echo "  openclaw sessions list research"
