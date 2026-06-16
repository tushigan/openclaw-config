#!/bin/bash

# SSL EOF 错误修复脚本
# 用于修复 omni-vision-psd-extractor 的 SSL 连接问题

echo "=========================================="
echo "修复 SSL EOF 错误 - 安装 requests 库"
echo "=========================================="
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1)
echo "当前 Python 版本: $PYTHON_VERSION"
echo ""

# 安装 requests 库
echo "正在安装 requests 库（更好的 SSL 支持）..."
pip3 install requests certifi --upgrade

if [ $? -eq 0 ]; then
    echo "✅ requests 库安装成功"
else
    echo "❌ requests 库安装失败"
    exit 1
fi

echo ""
echo "正在验证安装..."
python3 -c "import requests; print(f'requests 版本: {requests.__version__}')"
python3 -c "import certifi; print(f'certifi 版本: {certifi.__version__}')"

echo ""
echo "正在检查 SSL 版本..."
python3 -c "import ssl; print(f'OpenSSL 版本: {ssl.OPENSSL_VERSION}')"

echo ""
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 重新运行 skill"
echo "2. 脚本会自动使用 requests 库（更好的 SSL 支持）"
echo "3. 如果仍然失败，请检查网络连接或尝试其他 API 端点"
echo ""
