---
name: omni-vision-psd-extractor
version: 4.0.0 (McKinsey N-Layer Explosion Engine — 元素原子化并发爆破版)
description: 【全息万物提取PSD构建器】麦肯锡N层爆破引擎。AI视觉前置解析→元素清单JSON→每元素独立API请求并发执行→PS文件夹级多图层PSD组装。支持断点续跑，气球/小图标等小元素全画幅安全模式。
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

# 全息万物提取 PSD (Omni-Vision PSD Extractor) V4.0 (麦肯锡N层爆破引擎)

本技能已经历“麦肯锡深度思考引擎”重构，从原本的“零提示词盲跑黑盒”正式跃迁为**“当前多模态模型前置解析 + 动态提示词编排 + 强外挂《万物抠图法典》 + 底层精准绘图”**的复合引擎。大模型自身将作为视觉前沿哨所，彻底掌控提取语义。

## ⚠️ 绝对红线 1：图片图床 URL 强制前置 (CRITICAL: URL-Based Image Pipeline)
本技能已全面升级为云端 URL 工作流。大模型在执行本技能前，**必须先获取原图的图床 URL**：
1. **强制执行上传探针**：在运行提取主程序前，必须**首先独立运行全局图床探针**，该探针会自动抓取最新用户发送的图片并上传到 Cloudinary 免费图床：
   ```bash
   # 请将 [OPENCLAW_ROOT] 替换为您本地的 OpenClaw 项目根目录的绝对路径（Windows通常为H:\openclaw，Mac通常为/Users/用户名/openclaw 等）
   python "[OPENCLAW_ROOT]/.agents/skills/shared/cloudinary_uploader.py"
   ```
   > **[🚨 关键警告 - 禁止填错 conv_id]**: 只有在 Antigravity（系统消息中含有 `<user_information>` 块且明确提供了 `Conversation ID` 字段）的环境中，才应该加 `--conv-id` 参数。在 **小爪（OpenClaw）** 环境中运行时，**绝对不允许猜测、伪造或复用任何 UUID 作为 conv_id**。小爪没有标准的 conv_id，请直接不加 `--conv-id` 参数，让脚本自动取全局最新图片。
2. **捕获 URL 并交互确认**：执行上述脚本后，在标准输出中提取出 `https://...` 开头的图片图床链接。
   - **交互中断**：拿到 URL 后，大模型必须立刻结束当前回合，向用户汇报“URL已获取，链接为：[URL]”，并告知用户即将开始前景背景提取。
   - **自动唤醒**：在本次回复的同时，大模型必须调用 `schedule` 工具，设置 1 秒后的一次性计时器，通过该定时器在下一轮中被唤醒并自动执行后续的提取及 PSD 组装。

## ⚠️ 绝对红线 2：麦肯锡多模态闭环与动态 Prompt 生成 (The Cognitive Override)
你绝对不能再直接盲调用底层的提取脚本！你必须使用**当前聊天正在使用的多模态模型（即你自己）**预先对图片进行深度解析，并组装极致的提示词。

### 强制执行步骤 (The Executive Workflow)

**Step 1: 视觉语义前置解析 (Visual Autopsy)**
你必须用你自身的视觉能力，对用户的图片进行极端的“背景与前景拆解”，以及**“摄影质感解析”**。明确回答：
- 什么是必须提取的背景？什么是必须被剔除的杂质？
- 什么是必须保留的前景元素（IP角色、特效、文字、特定图标）？
- **[摄影级参数 (Cinematic Parameters)]**：原图的光影质感如何？例如：胶片噪点(Film Grain)、浅景深/焦外虚化(Depth of Field)、光源方向(Lighting Direction)、色温(Color Temperature)。
- **[🆕 强制输出元素清单 JSON]**：解析完毕后，必须以如下格式输出前景元素列表（供Step3直接消费）：
  ```json
  {"fg_elements": "品牌Logo,主标题文字,IP卡通角色,气球,纸飞机,风车,积木"}
  ```
  元素之间用英文逗号分隔，每个元素名称简洁精确（不超过10个汉字）。此 JSON 是下游 pipeline 的唯一元素拆分数据源，**绝对不允许省略**。

**Step 2: 组装终极提示词 (Prompt Assembling)**
根据你的解析，浓缩提炼出两个高纯度的字符串：
- **`BgPrompt` (背景指令)**: "【极其重要：绝对禁止凭空生成完全不同的风景！必须严格保持原图中的背景结构、光影和色彩不变，仅仅智能脑补被移除的前景区域。强制锁定以下摄影质感：[填入解析出的噪点、景深、光源等参数]！】将图片中的背景提取出来，背景是[详细描述]，需要将[具体前景/杂质]全部剔除，只保留背景。"
- **`FgPrompt` (前景总体指令，仅在 Step 1 未产出 fg_elements 时使用)**: "除了背景之外，看图片中的前景有什么元素（IP角色、文字、图标等），将它们全部提取出来。【极其重要：强制将它们的背景全部填充为纯正的绿幕（纯绿色，Hex: #00FF00）！绝对不要生成那种假透明的像素方格背景！】"

**Step 3: 启动底层绘图引擎 (带万物抠图法典强注入)**
在定时器自动唤醒后，调用 `run_omni_pipeline.py`。为了避免 Windows 命令行超长报错，你不需要手动读取并拼接 32KB 的《万物抠图.md》！底层 Python 引擎已升级原生支持。
你只需通过 `--prompt-append-file` 参数指向它，引擎会自动在后台完成基因融合！

> **[🚨 conv-id 使用规则]**: 在小爪（OpenClaw）环境中，**绝对不要加 `--conv-id` 参数**（小爪无法提供该值，猜测会导致拿到错误图片！）。只有在 Antigravity 环境（系统消息含 `<user_information>` 块）时，才可加 `--conv-id "<实际会话ID>"`。

> **[🆕 N层元素拆分模式 — 麦肯锡闭环核心]**：如果 Step 1 已输出 `fg_elements` 清单，**必须将其作为 `--fg-elements` 参数传入**（此时无需传 `--fg-prompt`），pipeline 会自动为每个元素独立生成一个图层并在 PSD 中放入 `05_FOREGROUND` 文件夹，PS 里可单独拖动每一个元素。

> **[⚡ 并发提取 — 时间降维]**：加入 `--concurrency 4` 可让4个元素同时并行API请求，8元素时间从 ~80分钟 压缩至 ~15分钟。

> **[🔄 断点续跑 — 零重跑成本]**：如果某元素提取失败，**无需重新跑整个pipeline**！直接用相同命令重新执行，`parallel-state.json` 会自动跳过所有已完成的图层，只重试失败的那个。

```bash
# 🎯 N层元素拆分模式（推荐）
# 请将 [OPENCLAW_ROOT] 替换为您本地的实际 OpenClaw 项目绝对路径
python "[OPENCLAW_ROOT]/.agents/skills/omni-vision-psd-extractor/omni-vision-psd-extractor/omni-vision-psd-extractor/scripts/run_omni_pipeline.py" \
  --source "https://res.cloudinary.com/..." \
  --out-dir "[OPENCLAW_ROOT]/workspace/omni-out" \
  --auto-extract \
  --bg-prompt "你的BgPrompt内容" \
  --fg-elements "品牌Logo,主标题文字,IP卡通角色,气球,纸飞机,风车,积木" \
  --prompt-append-file "[OPENCLAW_ROOT]/.agents/skills/omni-vision-psd-extractor/omni-vision-psd-extractor/omni-vision-psd-extractor/references/万物提取.md"
```

```bash
# 🔙 兼容模式（无元素清单时，退回传统2层）
# 请将 [OPENCLAW_ROOT] 替换为您本地的实际 OpenClaw 项目绝对路径
python "[OPENCLAW_ROOT]/.agents/skills/omni-vision-psd-extractor/omni-vision-psd-extractor/omni-vision-psd-extractor/scripts/run_omni_pipeline.py" \
  --source "https://res.cloudinary.com/..." \
  --out-dir "[OPENCLAW_ROOT]/workspace/omni-out" \
  --auto-2-layer \
  --bg-prompt "你的BgPrompt内容" \
  --fg-prompt "你的FgPrompt内容" \
  --prompt-append-file "[OPENCLAW_ROOT]/.agents/skills/omni-vision-psd-extractor/omni-vision-psd-extractor/omni-vision-psd-extractor/references/万物提取.md"
```

执行完毕后，脚本会直接输出最终极高保真、且包含 100% 像素级高保真无损图层的 `layered-output.psd` 路径，请将其提供给用户，并汇报麦肯锡闭环的思考结果！

<!-- openclaw-models-binding:start -->
### 📍 绑定的模型配置 (Bound Model Config)
| 配置项 | 当前设定值 |
| :--- | :--- |
| **模型名称 (Name)** | `gemini-3.1-flash-image-preview` |
| **模型ID (Model ID)** | `gemini-3.1-flash-image-preview` |
| **接口协议 (Protocol)** | `openai` |
| **基础网址 (Base URL)** | `https://s.lconai.com/` |
| **接口密钥 (API Key)** | `sk-ldeV7GIgtTHIvcG4UbKhRo8zN7lFVNgEhOtzgrTHdE1THBzD` |
<!-- openclaw-models-binding:end -->
