#!/bin/bash

# 模型托底机制配置和安装脚本

echo "=========================================="
echo "模型托底机制配置"
echo "=========================================="
echo ""

cd /Users/a123/.openclaw/skills/omni-vision-psd-extractor/

# Step 1: 验证当前配置
echo "Step 1: 验证当前 .env 配置"
echo "----------------------------------------"
echo ""

CURRENT_MODEL=$(grep "OPENCLAW_BOUND_MODEL_ID" .env | cut -d'=' -f2)
CURRENT_PROTOCOL=$(grep "OPENCLAW_BOUND_PROTOCOL" .env | cut -d'=' -f2)

echo "当前主模型: $CURRENT_MODEL"
echo "当前协议: $CURRENT_PROTOCOL"
echo ""

if [ "$CURRENT_MODEL" = "gpt-image-2-pro" ] && [ "$CURRENT_PROTOCOL" = "openai" ]; then
    echo "✅ 主模型配置正确"
else
    echo "⚠️  主模型配置需要调整"
    echo ""
    echo "请确保 .env 包含:"
    echo "  OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro"
    echo "  OPENCLAW_BOUND_PROTOCOL=openai"
    echo ""
    echo "是否自动修正? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        sed -i.bak 's/OPENCLAW_BOUND_MODEL_ID=.*/OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro/' .env
        sed -i.bak 's/OPENCLAW_BOUND_PROTOCOL=.*/OPENCLAW_BOUND_PROTOCOL=openai/' .env
        echo "✅ 配置已修正"
    else
        echo "❌ 请手动修改 .env 文件"
        exit 1
    fi
fi

echo ""

# Step 2: 应用托底机制补丁
echo "Step 2: 应用托底机制补丁"
echo "----------------------------------------"
echo ""

if [ ! -f "scripts/apply_fallback_patch.py" ]; then
    echo "❌ 补丁脚本不存在"
    exit 1
fi

python3 scripts/apply_fallback_patch.py

if [ $? -eq 0 ]; then
    echo "✅ 托底机制已添加"
else
    echo "❌ 补丁应用失败"
    exit 1
fi

echo ""

# Step 3: 验证安装
echo "Step 3: 验证托底机制"
echo "----------------------------------------"
echo ""

if grep -q "托底模型" scripts/extract_layers.py; then
    echo "✅ 托底机制代码已存在"
else
    echo "❌ 托底机制未正确添加"
    exit 1
fi

echo ""

# Step 4: 总结
echo "=========================================="
echo "✅ 配置完成！"
echo "=========================================="
echo ""
echo "当前配置:"
echo "  主模型: gpt-image-2-pro (OpenAI 协议)"
echo "  托底模型: gemini-3.1-flash-image-preview (Gemini 协议)"
echo ""
echo "重试逻辑:"
echo "  1. 主模型尝试 3 次"
echo "  2. 主模型失败 → 托底模型尝试 3 次"
echo "  3. 托底模型失败 → 任务失败"
echo ""
echo "每个图层最多 API 请求:"
echo "  正常: 1 次（主模型成功）"
echo "  重试: 3 次（主模型重试）"
echo "  托底: 6 次（3 次主模型 + 3 次托底模型）"
echo ""
echo "两个图层总计最多: 12 次 API 请求"
echo ""
echo "下一步:"
echo "  1. 运行 skill 测试"
echo "  2. 查看日志验证模型使用情况"
echo "  3. 确认托底机制在主模型失败时正确触发"
echo ""
