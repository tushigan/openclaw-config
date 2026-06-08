---
name: omni-vision-psd-extractor
version: 3.0.0 (McKinsey Closed-Loop Engine)
description: 【全息万物提取PSD构建器】基于麦肯锡深度思考引擎重构。多模态前置视觉解析 + 动态提示词编排 + 强外挂《万物抠图法典》联合注入。
triggers:
  - "原图提取分层"
  - "物理拆解PSD"
  - "无损提取PSD"
  - "语义抠图PSD"
  - "全息万物提取"
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - node
        - npm
    emoji: "🔪"
---

# 全息万物提取 PSD (Omni-Vision PSD Extractor) V3.0 (麦肯锡闭环重构版)

本技能已经历“麦肯锡深度思考引擎”重构，从原本的“零提示词盲跑黑盒”正式跃迁为**“当前多模态模型前置解析 + 动态提示词编排 + 强外挂《万物抠图法典》 + 底层精准绘图”**的复合引擎。大模型自身将作为视觉前沿哨所，彻底掌控提取语义。

## ⚠️ 绝对红线 1：图片图床 URL 强制前置 (CRITICAL: URL-Based Image Pipeline)
本技能已全面升级为云端 URL 工作流。大模型在执行本技能前，**必须先获取原图的图床 URL**：
1. **强制执行上传探针**：在运行提取主程序前，必须**首先独立运行全局图床探针**，该探针会自动抓取最新用户发送的图片并上传到 Cloudinary 免费图床：
   ```bash
   python "H:\openclaw\.agents\skills\shared\cloudinary_uploader.py"
   ```
2. **捕获 URL**：执行上述脚本后，在标准输出中提取出 `https://...` 开头的图片图床链接。绝对禁止直接使用本地路径传递！

## ⚠️ 绝对红线 2：麦肯锡多模态闭环与动态 Prompt 生成 (The Cognitive Override)
你绝对不能再直接盲调用底层的提取脚本！你必须使用**当前聊天正在使用的多模态模型（即你自己）**预先对图片进行深度解析，并组装极致的提示词。

### 强制执行步骤 (The Executive Workflow)

**Step 1: 视觉语义前置解析 (Visual Autopsy)**
你必须用你自身的视觉能力，对用户的图片进行极端的“背景与前景拆解”，以及**“摄影质感解析”**。明确回答：
- 什么是必须提取的背景？什么是必须被剔除的杂质？
- 什么是必须保留的前景元素（IP角色、特效、文字、特定图标）？
- **[摄影级参数 (Cinematic Parameters)]**：原图的光影质感如何？例如：胶片噪点(Film Grain)、浅景深/焦外虚化(Depth of Field)、光源方向(Lighting Direction)、色温(Color Temperature)。

**Step 2: 组装终极提示词 (Prompt Assembling)**
根据你的解析，浓缩提炼出两个高纯度的字符串：
- **`BgPrompt` (背景指令)**: "【极其重要：绝对禁止凭空生成完全不同的风景！必须严格保持原图中的背景结构、光影和色彩不变，仅仅智能脑补被移除的前景区域。强制锁定以下摄影质感：[填入解析出的噪点、景深、光源等参数]！】将图片中的背景提取出来，背景是[详细描述]，需要将[具体前景/杂质]剔除掉。"
- **`FgPrompt` (前景指令)**: "除了背景之外，看图片中的前景有什么元素（IP角色、文字、图标等），将它们全部提取出来。【极其重要：强制将它们的背景全部填充为纯正的绿幕（纯绿色，Hex: #00FF00）！绝对不要生成那种假透明的像素方格背景！】"

**Step 3: 启动底层绘图引擎 (带万物抠图法典强注入)**
调用 `run_omni_pipeline.py`。为了避免 Windows 命令行超长报错，你不需要手动读取并拼接 32KB 的《万物抠图.md》！底层 Python 引擎已升级原生支持。
你只需通过 `--prompt-append-file` 参数指向它，引擎会自动在后台完成基因融合！

```bash
python "H:\openclaw\.agents\skills\omni-vision-psd-extractor\omni-vision-psd-extractor\scripts\run_omni_pipeline.py" \
  --source "https://res.cloudinary.com/..." \
  --out-dir "H:\openclaw\workspace\omni-out" \
  --auto-2-layer \
  --bg-prompt "你的BgPrompt内容" \
  --fg-prompt "你的FgPrompt内容" \
  --prompt-append-file "H:\openclaw\.agents\skills\omni-vision-psd-extractor\omni-vision-psd-extractor\omni-vision-psd-extractor\references\万物提取.md"
```

执行完毕后，脚本会直接输出最终极高保真的 `layered-output.psd` 路径，请将其提供给用户，并汇报麦肯锡闭环的思考结果！

<!-- openclaw-models-binding:start -->
### 📍 绑定的模型配置 (Bound Model Config)
| 配置项 | 当前设定值 |
| :--- | :--- |
| **模型名称 (Name)** | `gemini-3.1-flash-image-preview` |
| **模型ID (Model ID)** | `gemini-3.1-flash-image-preview` |
| **接口协议 (Protocol)** | `openai` |
| **基础网址 (Base URL)** | `https://s.lconai.com/` |
| **接口密钥 (API Key)** | `sk-l****HBzD` |
<!-- openclaw-models-binding:end -->
