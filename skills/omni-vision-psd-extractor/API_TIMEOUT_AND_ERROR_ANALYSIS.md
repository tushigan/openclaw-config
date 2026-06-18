# API 超时与错误处理分析

## 📊 当前超时配置

### 1. **API 请求超时（OpenAI 格式）**

**位置**: `extract_layers.py` 第 305 行

```python
with urllib.request.urlopen(request, timeout=240) as response:
```

- **超时时间**: **240 秒 (4 分钟)**
- **适用于**: gpt-image-2-pro 的图像生成请求
- **触发条件**: API 服务器 240 秒内没有响应

---

### 2. **图片下载超时（OpenAI 格式）**

**位置**: `extract_layers.py` 第 361 行

```python
with urllib.request.urlopen(image_url, timeout=60) as img_response:
```

- **超时时间**: **60 秒 (1 分钟)**
- **适用于**: 从 API 返回的 URL 下载生成的图片
- **触发条件**: 图片下载 60 秒内未完成

---

### 3. **Gemini API 请求超时**

**位置**: `extract_layers.py` 第 486 行

```python
with urllib.request.urlopen(request, timeout=240) as response:
```

- **超时时间**: **240 秒 (4 分钟)**
- **适用于**: Gemini 格式的图像生成请求

---

### 4. **重试超时（每次尝试）**

**位置**: `extract_layers.py` 第 626 行

```python
attempts = max(1, args.api_retries)  # 默认 3 次重试
for attempt in range(1, attempts + 1):
    res = run_bound_gemini(prompt, source_path, raw_out, env, suggested_size, source_url=source_url)
    if res.returncode == 0 and raw_out.exists():
        generation_success = True
        break  # ✅ 成功后立即退出
```

- **最大重试次数**: **3 次**（通过 `--api-retries` 参数配置）
- **单次超时**: 240 秒
- **总最长等待时间**: **720 秒 (12 分钟)** = 3 次 × 240 秒

---

## 🔍 报错分析

根据你提供的错误信息：

### 错误 1: `401 令牌状态不可用`

```
n.lconai.com 返回 401 令牌状态不可用
```

**原因**:
- HTTP 401 = 未授权（Unauthorized）
- API Key 无效、过期或被禁用

**可能性**:
1. ✅ **API Key 余额充足但已过期/失效**
2. ✅ **API 端点要求的认证格式不匹配**
3. ✅ **API Key 没有访问 `gpt-image-2-pro` 模型的权限**

---

### 错误 2: `429 等待 120 秒`

```
随后触发 429 等待 120 秒
```

**原因**:
- HTTP 429 = 请求过于频繁（Too Many Requests）
- API 触发了速率限制

**可能性**:
1. ✅ **短时间内发送了太多请求**
2. ✅ **API Key 的速率限制配额已用完**
3. ✅ **401 错误后的自动重试触发了 429**

---

### 错误 3: `Remote end closed connection without response`

```
direct.aixor.org / gpt-image-2 连续返回 Remote end closed connection without response
```

**原因**:
- 服务器在完成响应前关闭了连接
- 可能是服务器过载、网络问题或请求格式错误

**可能性**:
1. ✅ **API 服务器不稳定**
2. ✅ **请求体过大（提示词 30K + 31K）**
3. ✅ **multipart/form-data 格式问题**

---

### 错误 4: `SSL EOF`

```
SSL EOF
```

**原因**:
- SSL/TLS 连接在握手或数据传输过程中被意外关闭

**可能性**:
1. ✅ **服务器 SSL 配置问题**
2. ✅ **网络中断**
3. ✅ **防火墙/代理干扰**

---

## 🛠️ 诊断步骤

### 步骤 1: 验证 API Key 有效性

让我检查当前配置的 API Key 和端点：

```bash
cat /Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env | grep OPENCLAW_BOUND
```

**当前配置**:
```
OPENCLAW_BOUND_API_KEY=sk-bSPSorO76pfzfqkbHlWHMK97nkXtXzO5h0bOZpxb3NlF52lw
OPENCLAW_BOUND_BASE_URL=https://n.lconai.com/
OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro
OPENCLAW_BOUND_PROTOCOL=openai
```

**验证方法**:
```bash
curl -X POST https://n.lconai.com/v1/images/edits \
  -H "Authorization: Bearer sk-bSPSorO76pfzfqkbHlWHMK97nkXtXzO5h0bOZpxb3NlF52lw" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2-pro","prompt":"test"}'
```

**预期结果**:
- ✅ 200 OK = API Key 有效
- ❌ 401 Unauthorized = API Key 无效/过期
- ❌ 403 Forbidden = 无权限访问该模型

---

### 步骤 2: 检查请求体大小限制

**当前提示词大小**:
- `万物提取.md`: **30KB**
- `元素整理.md`: **31KB**
- 加上图片数据 (multipart): **总大小可能超过 50MB**

**可能的问题**:
- API 可能有请求体大小限制（如 10MB）
- 超大的提示词可能导致连接超时

**解决方案**:
1. **压缩提示词**（移除空行、缩进）
2. **测试小提示词**（如 "提取背景"）验证 API 是否可用

---

### 步骤 3: 测试不同的超时配置

**当前超时**: 240 秒

**建议调整**:
```python
# 对于大文件/复杂提示词，增加超时
with urllib.request.urlopen(request, timeout=600) as response:  # 10 分钟
```

---

## 🎯 解决方案

### 方案 1: 验证并更新 API Key

1. **登录 n.lconai.com 控制台**
2. **检查 API Key 状态**:
   - 是否过期？
   - 余额是否充足？
   - 是否有访问 `gpt-image-2-pro` 的权限？
3. **如果 Key 失效，生成新的 Key**
4. **更新 `.env` 文件**

---

### 方案 2: 简化提示词进行测试

创建一个测试脚本，使用简短的提示词验证 API 是否可用：

```python
import urllib.request
import json

api_key = "sk-bSPSorO76pfzfqkbHlWHMK97nkXtXzO5h0bOZpxb3NlF52lw"
endpoint = "https://n.lconai.com/v1/images/edits"

# 简短的测试提示词
test_prompt = "提取图片中的背景"

# 构建请求（使用小图片测试）
boundary = "----WebKitFormBoundaryTest123"
body = f"""--{boundary}
Content-Disposition: form-data; name="prompt"

{test_prompt}
--{boundary}
Content-Disposition: form-data; name="model"

gpt-image-2-pro
--{boundary}
Content-Disposition: form-data; name="image"; filename="test.png"
Content-Type: image/png

<small test image data>
--{boundary}--
""".encode('utf-8')

request = urllib.request.Request(
    endpoint,
    data=body,
    headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {api_key}"
    }
)

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read())
        print("✅ API 可用:", result)
except urllib.error.HTTPError as e:
    print(f"❌ HTTP 错误 {e.code}:", e.read().decode())
except Exception as e:
    print(f"❌ 连接错误:", e)
```

---

### 方案 3: 增加超时和重试逻辑

修改 `extract_layers.py`，增加超时和添加详细的错误日志：

```python
# 增加超时到 600 秒（10 分钟）
with urllib.request.urlopen(request, timeout=600) as response:

# 添加详细的错误日志
except urllib.error.HTTPError as exc:
    body_text = exc.read().decode("utf-8", errors="replace")
    safe_log(f"❌ HTTP {exc.code} 错误详情:")
    safe_log(f"   请求端点: {config['endpoint']}")
    safe_log(f"   模型: {config['model']}")
    safe_log(f"   响应体: {body_text[:2000]}")
    
    # 如果是 401，提示检查 API Key
    if exc.code == 401:
        safe_log(f"⚠️  API Key 可能无效或已过期，请检查:")
        safe_log(f"   1. 登录 {config['base_url']} 控制台")
        safe_log(f"   2. 验证 API Key 状态和余额")
        safe_log(f"   3. 确认有访问 {config['model']} 的权限")
    
    # 如果是 429，提示速率限制
    if exc.code == 429:
        safe_log(f"⚠️  触发速率限制，建议:")
        safe_log(f"   1. 等待 2-5 分钟后重试")
        safe_log(f"   2. 检查 API 配额是否用完")
```

---

### 方案 4: 切换到备用 API 端点

如果 `n.lconai.com` 不稳定，尝试其他端点：

```bash
# 更新 .env 文件
OPENCLAW_BOUND_BASE_URL=https://api.openai.com/  # OpenAI 官方
# 或
OPENCLAW_BOUND_BASE_URL=https://api.anthropic.com/  # Anthropic 官方（需要切换模型）
```

---

## 📋 当前配置总结

| 配置项 | 当前值 | 建议值 |
|-------|--------|--------|
| **API 超时** | 240 秒 | 600 秒（对于大提示词） |
| **重试次数** | 3 次 | 3-5 次 |
| **提示词大小** | 30KB + 31KB | 考虑压缩到 < 20KB |
| **API Key** | sk-bSPS...F52lw | **需要验证有效性** ⚠️ |
| **端点** | https://n.lconai.com/ | 如果不稳定，考虑切换 |

---

## 🚨 紧急排查清单

1. **[ ] 登录 n.lconai.com 控制台，验证 API Key 状态**
2. **[ ] 检查 API 余额和配额**
3. **[ ] 确认 Key 有访问 gpt-image-2-pro 的权限**
4. **[ ] 使用 curl 命令测试 API 连通性**
5. **[ ] 如果 Key 失效，生成新 Key 并更新 .env**
6. **[ ] 考虑简化提示词进行测试**
7. **[ ] 增加超时到 600 秒**
8. **[ ] 添加详细的错误日志**

---

*文档生成时间: 2026-06-15*
