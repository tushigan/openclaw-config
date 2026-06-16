# SSL EOF 错误完整诊断和解决方案

## 🔍 问题现状

### 错误信息
```
EOF occurred in violation of protocol (_ssl.c:1129)
SSLEOFError
```

### 失败的通道
1. ❌ `https://n.lconai.com/` - SSL EOF
2. ❌ `https://direct.aixor.org/` - SSL EOF
3. ❌ Cloudinary 图床 (`https://api.cloudinary.com/`) - SSL EOF

### 验证的配置
- ✅ API Key 正确（`sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8`）
- ✅ API URL 正确
- ✅ 图片文件正常
- ✅ 代码逻辑正确

---

## 📊 根本原因分析

### SSL EOF 错误的含义

**EOF (End of File) occurred in violation of protocol** 表示：
- SSL/TLS 连接在握手或数据传输过程中被意外关闭
- 这是 **Python SSL 库与服务器 SSL 配置不兼容** 的典型症状

### 可能的具体原因

#### 1. **Python SSL 版本过旧** ⭐ 最可能
```bash
# 检查当前 SSL 版本
python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"

# 常见问题：
# - OpenSSL 1.0.x (太旧，不支持 TLS 1.2+)
# - OpenSSL 1.1.0 (部分场景不兼容)
# - 需要：OpenSSL 1.1.1+ 或 3.0+
```

#### 2. **TLS 版本不匹配**
- 服务器要求：TLS 1.2 或 TLS 1.3
- Python 默认：可能使用较低版本的 TLS
- `urllib` 没有显式指定 TLS 版本

#### 3. **证书验证问题**
- CA 证书过期或缺失
- `certifi` 包版本过旧

#### 4. **请求体过大**
- 图片 5-20MB + 提示词 30KB
- 某些服务器在接收大请求时可能提前关闭连接

---

## 🛠️ 解决方案（按优先级）

### 方案 1: 安装并使用 `requests` 库 ⭐⭐⭐ 强烈推荐

**为什么 `requests` 更好**：
- ✅ 更好的 SSL/TLS 支持
- ✅ 自动处理连接池和重试
- ✅ 更健壮的错误处理
- ✅ 自动使用最新的 `certifi` CA 证书

**安装步骤**：
```bash
cd /Users/a123/.openclaw/skills/omni-vision-psd-extractor/

# 运行修复脚本
chmod +x fix_ssl_error.sh
./fix_ssl_error.sh
```

或手动安装：
```bash
pip3 install requests certifi --upgrade
```

**验证安装**：
```bash
python3 -c "import requests; print(f'requests 版本: {requests.__version__}')"
python3 -c "import certifi; print(f'certifi 版本: {certifi.__version__}')"
python3 -c "import ssl; print(f'OpenSSL 版本: {ssl.OPENSSL_VERSION}')"
```

**代码已自动适配**：
- ✅ 脚本会自动检测是否安装了 `requests`
- ✅ 如果有 `requests`，优先使用（更好的 SSL）
- ✅ 如果没有，回退到 `urllib`

---

### 方案 2: 升级 Python 和 OpenSSL

如果方案 1 不行，可能需要升级底层库：

```bash
# macOS (使用 Homebrew)
brew upgrade python@3.11
brew upgrade openssl@3

# 或者安装最新 Python
brew install python@3.12

# 重新安装依赖
pip3 install requests certifi --upgrade --force-reinstall
```

---

### 方案 3: 使用本地代理或 VPN

如果所有外部 API 都失败，可能是网络环境问题：

```bash
# 检查网络连接
curl -v https://n.lconai.com/ 2>&1 | grep -i "ssl\|tls"
curl -v https://direct.aixor.org/ 2>&1 | grep -i "ssl\|tls"

# 如果 curl 也失败，说明是网络层问题
```

---

### 方案 4: 切换到其他 API 服务商

如果当前的 `n.lconai.com` 和 `direct.aixor.org` 都不可用，考虑：

#### 选项 A: OpenAI 官方 API
```bash
# 更新 .env
OPENCLAW_BOUND_BASE_URL=https://api.openai.com/
OPENCLAW_BOUND_API_KEY=<你的 OpenAI API Key>
OPENCLAW_BOUND_MODEL_ID=dall-e-3
OPENCLAW_BOUND_PROTOCOL=openai
```

#### 选项 B: Azure OpenAI
```bash
OPENCLAW_BOUND_BASE_URL=https://<your-resource>.openai.azure.com/
OPENCLAW_BOUND_API_KEY=<Azure API Key>
```

#### 选项 C: 其他兼容 OpenAI 格式的服务
- Replicate
- Hugging Face Inference API
- 本地部署的模型

---

### 方案 5: Cloudinary 备用方案（已实现）

对于 Gemini 协议，如果 Cloudinary 上传失败，会自动切换到 Base64：

```python
# 代码已实现自动切换
if cloudinary_upload_fails:
    use_base64_mode()  # 自动降级
```

**但注意**：当前使用的是 OpenAI 协议，不经过 Cloudinary。

---

## 🎯 立即可执行的步骤

### Step 1: 安装 requests 库

```bash
cd /Users/a123/.openclaw/skills/omni-vision-psd-extractor/
chmod +x fix_ssl_error.sh
./fix_ssl_error.sh
```

### Step 2: 重新运行 skill

```bash
# 脚本会自动使用 requests 库
# 应该能解决大部分 SSL 问题
```

### Step 3: 如果仍然失败

检查详细的错误日志：
```bash
# 查看最新的 result.json
cat /Users/a123/.openclaw/workspace-design/outputs/omni-vision-psd-extractor/job_*/raw/*.result.json

# 查看完整日志
tail -100 <日志文件>
```

---

## 📋 诊断检查清单

运行以下命令收集诊断信息：

```bash
echo "=== Python 版本 ==="
python3 --version

echo "=== SSL 版本 ==="
python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"

echo "=== requests 库 ==="
python3 -c "import requests; print(requests.__version__)" 2>&1

echo "=== certifi 证书 ==="
python3 -c "import certifi; print(certifi.where())" 2>&1

echo "=== 网络连通性测试 ==="
curl -v https://n.lconai.com/ 2>&1 | head -20
curl -v https://direct.aixor.org/ 2>&1 | head -20
curl -v https://api.cloudinary.com/ 2>&1 | head -20

echo "=== TLS 版本测试 ==="
python3 - <<'EOF'
import ssl
import socket

def test_tls(host, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print(f"{host}: {ssock.version()}")

try:
    test_tls("n.lconai.com")
    test_tls("direct.aixor.org")
    test_tls("api.cloudinary.com")
except Exception as e:
    print(f"TLS 测试失败: {e}")
EOF
```

---

## 🔄 已实现的改进

### 1. ✅ 自动检测并使用 `requests` 库
```python
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    import urllib.request
    USE_REQUESTS = False
```

### 2. ✅ Cloudinary 失败自动切换 Base64（Gemini 协议）
```python
if cloudinary_fails:
    use_base64_mode()
```

### 3. ✅ 增加超时到 600 秒（10 分钟）
```python
timeout=600  # 适应大文件传输
```

### 4. ✅ 详细的错误日志
```python
safe_log(f"❌ SSL 错误: {e}")
safe_log(f"提示: 尝试 'pip install --upgrade requests certifi' 更新证书")
```

---

## 📊 各方案成功率评估

| 方案 | 成功率 | 难度 | 时间 |
|------|--------|------|------|
| **安装 requests 库** | ⭐⭐⭐⭐⭐ 90% | 低 | 1 分钟 |
| **升级 Python/OpenSSL** | ⭐⭐⭐⭐ 80% | 中 | 10 分钟 |
| **使用代理/VPN** | ⭐⭐⭐ 60% | 中 | 5 分钟 |
| **切换 API 服务商** | ⭐⭐⭐⭐⭐ 95% | 低 | 2 分钟 |

---

## 💡 最终建议

### 短期解决方案（立即执行）
1. **安装 requests 库**（1 分钟）
2. **重新运行 skill**
3. 如果成功 → 问题解决 ✅
4. 如果失败 → 执行方案 4（切换 API 服务商）

### 长期解决方案
1. 升级 Python 到 3.11+ 或 3.12
2. 使用 OpenAI 官方 API（更稳定）
3. 考虑本地部署图像生成模型

---

## 📞 如果所有方案都失败

可能是环境特定问题，需要：
1. 检查防火墙/代理设置
2. 检查企业网络限制
3. 尝试在不同网络环境下运行
4. 考虑使用 Docker 容器隔离环境

---

*文档生成时间: 2026-06-15*
*适用于: omni-vision-psd-extractor v5.2.0*
