#!/bin/bash

# RH抠图王集成 - 安装依赖和测试脚本

echo "=========================================="
echo "RH抠图王集成 - 安装依赖"
echo "=========================================="
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1)
echo "当前 Python 版本: $PYTHON_VERSION"
echo ""

# 安装 httpx 库（推荐，更好的异步支持）
echo "正在安装 httpx 库（推荐用于 RH抠图王）..."
pip3 install httpx --upgrade

if [ $? -eq 0 ]; then
    echo "✅ httpx 库安装成功"
else
    echo "⚠️  httpx 库安装失败，将使用 urllib 作为备用（功能正常，但性能较低）"
fi

echo ""
echo "正在验证安装..."
python3 -c "import httpx; print(f'httpx 版本: {httpx.__version__}')" 2>&1 || echo "httpx 未安装，将使用 urllib"

echo ""
echo "=========================================="
echo "✅ 依赖安装完成！"
echo "=========================================="
echo ""
echo "RH抠图王配置信息："
echo "  API Key: 442de49dcb5247a285b678a4c70e7499"
echo "  API URL: https://n8n.lconai.com/webhook/c662eebb-0a0b-4c4d-8df4-7b5b01d2b27a"
echo ""
echo "替换说明："
echo "  ❌ 旧方案: 本地 Python 去绿幕（remove_chroma_key.py）"
echo "  ✅ 新方案: RH抠图王云端高精度抠图（rh_matting.py）"
echo ""
echo "优势："
echo "  ✅ 云端高精度抠图算法"
echo "  ✅ 自动处理各种背景（绿幕/纯色/复杂背景）"
echo "  ✅ 无需本地 OpenCV 依赖"
echo "  ✅ 结果质量更稳定"
echo ""
echo "下一步："
echo "  1. 运行 skill 测试"
echo "  2. 查看日志中的 [RH抠图王] 标记"
echo "  3. 验证透明 PNG 质量"
echo ""

# 可选：测试 RH抠图王脚本
if [ -f "scripts/rh_matting.py" ]; then
    echo "=========================================="
    echo "测试 RH抠图王脚本"
    echo "=========================================="
    echo ""
    echo "脚本位置: scripts/rh_matting.py"
    echo "使用方法:"
    echo "  python3 scripts/rh_matting.py --input <绿幕图.png> --output <透明图.png>"
    echo ""

    # 检查是否有测试图片
    if [ -f "test-image.png" ]; then
        echo "发现测试图片: test-image.png"
        echo "是否运行测试？(y/n)"
        read -r response
        if [ "$response" = "y" ]; then
            python3 scripts/rh_matting.py --input test-image.png --output test-output-transparent.png
            if [ $? -eq 0 ]; then
                echo "✅ 测试成功！查看输出: test-output-transparent.png"
            else
                echo "❌ 测试失败，请检查错误日志"
            fi
        fi
    fi
fi

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
