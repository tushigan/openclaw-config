# Skill 完整配置与 PSD 结构总结

## 📍 Skill 目录地址

```
/Users/a123/.openclaw/skills/omni-vision-psd-extractor/
```

---

## 🔑 API 配置详情

### 当前使用的 API 配置

**配置文件位置**: `/Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env`

```bash
# 图像生成 API 配置
OPENCLAW_BOUND_API_KEY=sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8
OPENCLAW_BOUND_BASE_URL=https://n.lconai.com/
OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro
OPENCLAW_BOUND_PROTOCOL=openai
```

### API 请求详情

| 配置项 | 值 | 说明 |
|-------|-----|------|
| **API URL** | `https://n.lconai.com/v1/images/edits` | OpenAI 格式的图像编辑端点 |
| **API Key** | `sk-ggmpALjA...NWhUFrh8` | 完整 Key 见上方 |
| **模型** | `gpt-image-2-pro` | GPT Image 2 Pro |
| **协议格式** | `openai` | OpenAI /v1/images/edits 格式 |
| **请求格式** | `multipart/form-data` | 表单数据格式 |
| **认证方式** | `Authorization: Bearer <API_KEY>` | Bearer Token |

### 请求参数结构

```http
POST https://n.lconai.com/v1/images/edits
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
Authorization: Bearer sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8

--boundary
Content-Disposition: form-data; name="image"; filename="image.png"
Content-Type: image/png

<原图二进制数据>

--boundary
Content-Disposition: form-data; name="prompt"

<提示词文本>

--boundary
Content-Disposition: form-data; name="model"

gpt-image-2-pro

--boundary
Content-Disposition: form-data; name="size"

4096x2304

--boundary
Content-Disposition: form-data; name="n"

1

--boundary--
```

---

## 🎯 两次 API 请求详情

### 第 1 次 API 请求 - 背景层提取

**请求时机**: 图层提取阶段的第一个任务

**请求参数**:
```json
{
  "model": "gpt-image-2-pro",
  "image": "<原图二进制数据>",
  "prompt": "将图片中的背景提取出来。\n\n<万物提取.md 完整内容>",
  "size": "4096x2304",
  "n": 1
}
```

**提示词来源**:
- 固定前缀: `"将图片中的背景提取出来。"`
- MD 文件: `/Users/a123/.openclaw/skills/omni-vision-psd-extractor/references/万物提取.md` (30KB)

**输出结果**:
- 文件路径: `outputs/job_xxx/raw/background.png`
- 内容: 纯背景图（前景元素已移除）

---

### 第 2 次 API 请求 - 前景层元素整理

**请求时机**: 图层提取阶段的第二个任务

**请求参数**:
```json
{
  "model": "gpt-image-2-pro",
  "image": "<原图二进制数据>",
  "prompt": "<元素整理.md 完整内容>",
  "size": "4096x2304",
  "n": 1
}
```

**提示词来源**:
- MD 文件: `/Users/a123/.openclaw/skills/omni-vision-psd-extractor/references/元素整理.md` (31KB)
- 无额外前缀，直接使用完整 MD 文件内容

**输出结果**:
- 文件路径: `outputs/job_xxx/raw/foreground.png`
- 内容: 绿幕背景 (#00FF00) + 有序排列的所有前景元素

---

## 📦 最终 PSD 结构

### PSD 文件的 3 层结构

```
layered-output.psd
│
├── 📁 00_SOURCE_REF (原图参考层组)
│   └── 🖼️ 原图参考 (隐藏)
│       - 完整的原始上传图片
│       - 默认隐藏，供参考对比使用
│
├── 📁 01_BG (背景层组)
│   └── 🖼️ 背景层
│       - 第 1 次 API 返回的背景图
│       - 前景元素已移除，仅保留背景
│
└── 📁 05_FOREGROUND_GROUP (前景元素组) ⭐
    ├── 🖼️ 元素_001
    ├── 🖼️ 元素_002
    ├── 🖼️ 元素_003
    ├── 🖼️ 元素_004
    ├── 🖼️ 元素_005
    └── ...
        - 第 2 次 API 返回的前景图 (绿幕) 
        - 经过去绿幕处理得到透明层
        - 再经过 OpenCV 自动切割成多个独立元素
        - 每个元素一个独立图层
        - 所有元素都在 "05_FOREGROUND_GROUP" 文件夹内
```

### 详细说明

#### 1. **00_SOURCE_REF - 原图参考层**
- **数量**: 1 层
- **来源**: 用户上传的原始图片
- **状态**: 默认隐藏
- **作用**: 供设计师参考对比使用

#### 2. **01_BG - 背景层**
- **数量**: 1 层
- **来源**: 第 1 次 API 请求返回的背景图
- **内容**: 纯背景（所有前景元素已被移除）
- **状态**: 可见

#### 3. **05_FOREGROUND_GROUP - 前景元素组** ⭐ 重点
- **数量**: N 层（取决于切割出多少个元素）
- **来源处理流程**:
  1. 第 2 次 API 请求返回前景图（绿幕背景 #00FF00）
  2. 去绿幕处理：绿色 → 透明
  3. OpenCV 自动切割：
     - 连通域检测
     - 按面积排序
     - 每个独立元素保存为一个 PNG 文件
  4. 组装到 PSD：每个 PNG 作为独立图层
- **特点**:
  - ✅ 所有元素都在同一个 **"05_FOREGROUND_GROUP"** 文件夹内
  - ✅ 每个元素是独立的透明 PNG 图层
  - ✅ 元素按面积从大到小排序
  - ✅ 每个元素保留完整的位置信息（bbox, centroid）

---

## 🔄 完整工作流程

```
用户上传原图
    ↓
【Step 1】上传到 Cloudinary（仅 1 次）
    ↓
【Step 2】第 1 次 API 请求
    ├─ 模型: gpt-image-2-pro
    ├─ 提示词: "将图片中的背景提取出来。" + 万物提取.md
    └─ 输出: background.png (纯背景)
    ↓
    📤 实时发送到飞书: 【API 第 1 次请求完成】背景层提取结果
    ↓
【Step 3】第 2 次 API 请求
    ├─ 模型: gpt-image-2-pro
    ├─ 提示词: 元素整理.md 完整内容
    └─ 输出: foreground.png (绿幕 + 有序元素)
    ↓
    📤 实时发送到飞书: 【API 第 2 次请求完成】前景层元素整理结果（绿幕背景）
    ↓
【Step 4】去绿幕处理
    ├─ 输入: foreground.png (绿幕)
    ├─ 处理: 绿色 (#00FF00) → 透明
    └─ 输出: foreground_transparent.png (透明背景)
    ↓
    📤 实时发送到飞书: 【去绿幕完成】前景透明层
    ↓
【Step 5】OpenCV 自动切割前景元素
    ├─ 输入: foreground_transparent.png
    ├─ 处理: 连通域分析 + 按面积排序
    └─ 输出: elements/ 目录
        ├─ element_001.png
        ├─ element_002.png
        ├─ element_003.png
        └─ elements.json (元素清单)
    ↓
【Step 6】组装 PSD 文件
    ├─ 00_SOURCE_REF (原图，隐藏)
    ├─ 01_BG (背景层)
    └─ 05_FOREGROUND_GROUP (前景组)
        ├─ element_001.png
        ├─ element_002.png
        └─ ...
    ↓
【Step 7】上传到飞书云盘
    ├─ 获取 file_token
    └─ 生成下载链接
    ↓
    📤 发送到飞书: 预览图 + 下载链接
```

---

## ✅ 验证你的理解

### 你的理解：
> "我们一共有三层嘛，对不对？我们最终的 PSD 分别是原图、背景层、前景层。前景层那些元素被分割成 PNG 之后再分割成各个元素，各个元素每一个元素都是每一个图层，但是这些元素都属于这个文件夹。"

### 核对结果：✅ 完全正确！

**准确的说**：
- **3 个图层组**（文件夹）：
  1. `00_SOURCE_REF` - 原图参考
  2. `01_BG` - 背景层
  3. `05_FOREGROUND_GROUP` - 前景元素组

- **前景元素处理**：
  - ✅ 第 2 次 API 返回前景图（绿幕背景）
  - ✅ 去绿幕 → 透明背景
  - ✅ OpenCV 切割 → 多个独立 PNG 元素
  - ✅ 每个元素 = 一个独立图层
  - ✅ 所有元素都在 `05_FOREGROUND_GROUP` 文件夹内

---

## 📊 代码实现位置

### API 请求代码
- **文件**: `/Users/a123/.openclaw/skills/omni-vision-psd-extractor/scripts/extract_layers.py`
- **关键函数**: 
  - `_run_openai_image_edits()` (第 233-380 行) - OpenAI 格式
  - `_run_gemini_generate()` (第 383-540 行) - Gemini 格式（备用）

### 提示词组装
- **文件**: `/Users/a123/.openclaw/skills/omni-vision-psd-extractor/scripts/extract_layers.py`
- **位置**: 第 606-620 行
```python
if task["kind"] == "background":
    wanwu_text = wanwu_path.read_text(encoding="utf-8")
    prompt = f"将图片中的背景提取出来。\n\n{wanwu_text}"
else:
    yuansu_text = yuansu_path.read_text(encoding="utf-8")
    prompt = yuansu_text  # 完整内容
```

### 前景切割
- **文件**: `/Users/a123/.openclaw/skills/omni-vision-psd-extractor/scripts/extract_layers.py`
- **位置**: 第 792-846 行
- **调用脚本**: `split_foreground_layers.py`

### PSD 组装
- **文件**: `/Users/a123/.openclaw/skills/omni-vision-psd-extractor/scripts/build_reverse_psd_preview.py`
- **位置**: 第 65-95 行
- **图层结构生成**: 
  - 原图参考层（隐藏）
  - 背景层
  - 前景元素组（每个元素一个图层）

---

## 🎯 总结

你的理解完全正确！当前的 skill 确实是：

1. ✅ **2 次 API 请求**（背景 + 前景）
2. ✅ **3 个图层组**（原图 + 背景 + 前景组）
3. ✅ **前景自动切割**成多个独立元素
4. ✅ **所有元素在同一个文件夹**（05_FOREGROUND_GROUP）
5. ✅ **飞书云盘直接交付**（无分卷压缩）

---

*文档生成时间: 2026-06-15*
*版本: v5.2.0-cloud-drive-only*
