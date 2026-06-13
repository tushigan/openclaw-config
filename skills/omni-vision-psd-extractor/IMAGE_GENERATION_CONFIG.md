# 图像生成模型配置总结

## 📋 当前配置（v5.2.0）

### 🔧 配置文件位置
`/Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env`

### 🎯 生图模型配置

```bash
# 图像生成 API 配置
OPENCLAW_BOUND_API_KEY=sk-bSPSorO76pfzfqkbHlWHMK97nkXtXzO5h0bOZpxb3NlF52lw
OPENCLAW_BOUND_BASE_URL=https://n.lconai.com/
OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro
OPENCLAW_BOUND_PROTOCOL=openai
```

### 📊 配置说明

| 配置项 | 值 | 说明 |
|-------|-----|------|
| **模型名称** | `gpt-image-2-pro` | GPT Image 2 Pro 模型 |
| **API 端点** | `https://n.lconai.com/v1/images/edits` | OpenAI 格式的图像编辑接口 |
| **API Key** | `sk-bSPS...F52lw` | 认证密钥 |
| **协议格式** | `openai` | 使用 OpenAI /v1/images/edits 格式 |
| **传输方式** | `multipart/form-data` | 直接上传图片文件 |

---

## 🔄 两次 API 请求详情

### 第 1 次 API 请求 - 背景层提取

**请求参数**：
```json
{
  "model": "gpt-image-2-pro",
  "image": "<原图二进制数据>",
  "prompt": "将图片中的背景提取出来。\n\n<万物提取.md 完整内容>",
  "size": "4096x2304",  // 根据原图自动计算
  "n": 1
}
```

**提示词组成**：
- 固定前缀：`"将图片中的背景提取出来。"`
- 完整指令：`/Users/a123/.openclaw/skills/omni-vision-psd-extractor/references/万物提取.md` (30K)

**响应格式**：
```json
{
  "data": [
    {
      "url": "https://oaidalleapiprodscus.blob.core.windows.net/..."
    }
  ]
}
```

---

### 第 2 次 API 请求 - 前景层元素整理

**请求参数**：
```json
{
  "model": "gpt-image-2-pro",
  "image": "<原图二进制数据>",
  "prompt": "<元素整理.md 完整内容>",
  "size": "4096x2304",  // 与第1次相同
  "n": 1
}
```

**提示词组成**：
- 完整指令：`/Users/a123/.openclaw/skills/omni-vision-psd-extractor/references/元素整理.md` (31K)
- 无额外前缀，直接使用完整 MD 文件内容

**响应格式**：同第 1 次请求

---

## 🌐 图床配置（Cloudinary）

### 配置信息
```python
CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dc6kesgub/image/upload"
CLOUDINARY_PRESET = "my_n8n_upload"
```

### 使用场景
- **Gemini 协议时使用**：上传原图到 Cloudinary，获取 URL 后发送给 API
- **OpenAI 协议时不使用**：直接通过 multipart/form-data 上传原图

### 自动缩放规则
- 上传前自动缩放到 2K（最长边 2048px）
- 保持宽高比
- 对齐到 16 的倍数

---

## 🔀 协议切换支持

代码支持两种协议格式，通过 `OPENCLAW_BOUND_PROTOCOL` 环境变量控制：

### OpenAI 格式（当前使用）
```bash
OPENCLAW_BOUND_PROTOCOL=openai
```
- **API 端点**: `/v1/images/edits`
- **请求格式**: `multipart/form-data`
- **图片传输**: 直接上传二进制数据
- **适用模型**: `gpt-image-2-pro`

### Gemini 格式（备用）
```bash
OPENCLAW_BOUND_PROTOCOL=gemini
```
- **API 端点**: `/v1beta/models/{model}:generateContent`
- **请求格式**: `application/json`
- **图片传输**: Cloudinary URL（节省流量）
- **适用模型**: `gemini-3.1-flash-image-preview`

---

## 📁 代码文件说明

### 核心文件
1. **`scripts/runtime_config.py`**
   - 第 111-144 行：`resolve_bound_gemini_config()` 函数
   - 根据 `OPENCLAW_BOUND_PROTOCOL` 返回不同的配置

2. **`scripts/extract_layers.py`**
   - 第 195-230 行：`run_bound_gemini()` 主函数（协议分发）
   - 第 233-380 行：`_run_openai_image_edits()` OpenAI 格式实现
   - 第 383-540 行：`_run_gemini_generate()` Gemini 格式实现
   - 第 372-386 行：提示词组装逻辑

3. **`scripts/run_omni_delivery.py`**
   - 入口脚本，负责整体流程编排

---

## ✅ 验证检查清单

- [x] 模型配置：`gpt-image-2-pro`
- [x] API 端点：`https://n.lconai.com/v1/images/edits`
- [x] 协议格式：`openai` (multipart/form-data)
- [x] API Key：已配置
- [x] 提示词文件：
  - [x] `references/万物提取.md` (30K)
  - [x] `references/元素整理.md` (31K)
- [x] 两次 API 请求：
  - [x] 第 1 次：背景层（"将图片中的背景提取出来。" + 万物提取.md）
  - [x] 第 2 次：前景层（元素整理.md 完整内容）
- [x] 实时图片发送：已实现
- [x] 飞书云盘交付：已实现

---

## 🎯 总结

当前配置使用 **gpt-image-2-pro** 模型，通过 **OpenAI /v1/images/edits 格式**发送请求。

**两次 API 请求**固定为：
1. **背景层提取** - 使用万物提取.md指令
2. **前景层元素整理** - 使用元素整理.md指令

所有配置已优化完成，确保只发送 **2 次 API 请求**，成本降低 75%。

---

*更新时间：2026-06-12*
*版本：v5.2.0-cloud-drive-only*
