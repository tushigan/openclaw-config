---
name: poster-2k-psd-splitter
version: 1.2.0
description: 【海报2K分层PSD构建器】双提取引擎。原图→2K缩放→自动VLM解析→Gemini双提取（背景+前景）→RH抠图王精准去底→连通域元素分割→PSD多图层组装→分卷压缩。
triggers:
  - "海报拆图"
  - "海报导出PSD"
  - "双提取分层"
  - "2K海报PSD"
  - "快拆PSD"
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - node
        - npm
    emoji: "📐"
---

# 海报2K分层PSD构建器 (Poster 2K PSD Splitter) V1.2

将任意海报图片通过「VLM自动分析 + 双提取 + RH抠图王 + 连通域切割」管线，输出为多图层分层 PSD + 分卷压缩包。

## ⚠️ 绝对红线 1：图片图床 URL 强制前置 (CRITICAL: URL-Based Image Pipeline)

本技能已全面升级为云端 URL 工作流。大模型在执行本技能前，**必须先获取原图的图床 URL**：

1. **强制执行上传探针**：在运行提取主程序前，必须**首先独立运行全局图床探针**，该探针会自动抓取最新用户发送的图片并上传到 Cloudinary 免费图床：
   ```bash
   python "H:\openclaw\.agents\skills\shared\cloudinary_uploader.py"
   ```
   > **[🚨 关键警告 - 禁止填错 conv_id]**: 只有在 Antigravity 的环境中才加 `--conv-id`。在 **小爪（OpenClaw）** 环境中运行时，**绝对不允许加 `--conv-id` 参数**，让脚本自动取全局最新图片。

2. **捕获 URL 并交互确认**：执行上述脚本后，在标准输出中提取出 `https://...` 开头的图片图床链接。
   - **交互中断**：拿到 URL 后，大模型必须立刻结束当前回合，向用户汇报“URL已获取，链接为：[URL]”，并告知用户即将开始后台处理。
   - **自动唤醒**：在本次回复的同时，大模型必须调用 `schedule` 工具，设置 1 秒后的一次性计时器，通过该定时器在下一轮中被唤醒并自动执行后续的管线。

## ⚠️ 绝对红线 2：一键执行底层管线 (The Executive Workflow)

由于 Python 管线已内置了 VLM (GPT-5.4) 自动视觉分析机制，你**不再需要**手动分析图片或提供提示词！在定时器自动唤醒后，直接传入 URL 运行：

```bash
python "H:\openclaw\.agents\skills\poster-2k-psd-splitter\scripts\run_pipeline.py" --source "https://res.cloudinary.com/..."
```

**就这样！** 脚本内部会自动完成：
1. 图片下载并缩放至2K
2. 上传到 Cloudinary 获取 URL
3. **VLM自动分析**（调用GPT-5.4分析海报的前景/背景）
4. Gemini 3.1 Flash 双提取（背景 + 前景）
5. RH抠图王前景去底
6. OpenCV连通域切割元素
7. PSD组装 + 分卷压缩

### 可选参数 (仅在需要手动覆盖时使用)
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--out-dir <path>` | 输出目录 | `~/.openclaw/workspace/poster-psd-out` |
| `--max-edge <int>` | 最长边像素数 | `2048` |
| `--volume-size <int>` | 分卷大小MB | `30` |
| `--bg-prompt <str>` | 手动覆盖背景提示词 | 自动生成 |
| `--fg-prompt <str>` | 手动覆盖前景提示词 | 自动生成 |

执行完毕后，脚本会输出最终极高保真的 `layered-output.psd.zip.001` 等分卷压缩包路径，请将其提供给用户！

## PSD 图层结构
```
PSD Root
├── 📁 00_ORIGINAL (hidden) — 原图参考
│   └── Original Poster (Reference)
├── 📁 01_BG — 干净背景
│   └── Clean Background
└── 📁 05_FOREGROUND — 前景元素
    ├── Element 1
    ├── Element 2
    ├── Element 3
    └── ...
```

<!-- openclaw-models-binding:start -->
### 📍 绑定的模型配置 (Bound Model Config)
| 配置项 | 当前设定值 |
| :--- | :--- |
| **模型名称 (Name)** | `gemini-3.1-flash-image-preview` |
| **模型ID (Model ID)** | `gemini-3.1-flash-image-preview` |
| **接口协议 (Protocol)** | `gemini-native` |
| **基础网址 (Base URL)** | `https://s.lconai.com/` |
| **接口密钥 (API Key)** | `sk-ldeV7GIgtTHIvcG4UbKhRo8zN7lFVNgEhOtzgrTHdE1THBzD` |
<!-- openclaw-models-binding:end -->
