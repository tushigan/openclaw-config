---
name: omni-vision-psd-extractor
version: 4.0.0-mac-openclaw (111omni original logic)
description: 【全息万物提取PSD构建器】基于 111omni Windows 原版逻辑的 Mac/OpenClaw 适配版。保留 N 层元素拆分、4K 画布、全画幅小元素安全提取和万物提取法典；禁止离线兜底层冒充分层成功。
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
        - zip
    emoji: "🔪"
---

# 全息万物提取 PSD (Omni-Vision PSD Extractor)

这是基于 `111omni` 原始 Windows 版本的 Mac/OpenClaw 适配版。核心分层效果逻辑保持原版：视觉前置解析、`fg_elements` N 层拆分、原图 4K 尺寸策略、小元素全画幅安全提取、`万物提取.md` 注入、PSD 文件夹级组装。

## OpenClaw 执行规则

1. 默认使用用户上传图片的本地绝对路径或 HTTPS URL 作为 `--source`，不要强制 Cloudinary 前置上传。
2. 如果用户没有提供明确路径，才使用 `--source auto` 兜底。
3. 必须实际运行命令行脚本，不能只分析或复用历史产物。
4. 默认走轻包装入口 `scripts/run_omni_delivery.py`，它会调用原始 pipeline，生成摘要、18MB 分卷包，并校验分卷可恢复。
5. 绝对不能跳过视觉语义前置解析：必须先根据图片列出 `fg_elements`，再把英文逗号分隔的元素清单传给 `--fg-elements`。这是精细 N 层拆分的核心逻辑。
6. 默认禁止粗糙 2 层输出。只有用户明确说“只要背景/前景两层”时，才允许加 `--allow-2-layer` 并使用 `--fg-prompt`。
7. 本 skill 是模型线路例外：图层生成只允许使用本 skill 绑定的 `gemini-3.1-flash-image-preview @ https://s.lconai.com/`。不要把 `gpt-image2-gen`、`gpt-image-2`、`gpt-image-2-pro`、Aixor 主线路作为 omni 的默认分层引擎。
8. 不要修改其他生图 skill 或 OpenClaw 全局模型配置；此限制只属于 `omni-vision-psd-extractor`。
9. 不要使用 `schedule` 中断式二阶段流程；在当前回合里直接执行并交付结果。
10. Feishu 会话里运行时，必须把当前会话目标传给入口：私聊传 `--feishu-user-id ou_xxx`，群聊传 `--feishu-chat-id oc_xxx`；如果有 `agent:...:feishu:...` 会话 key，也可以传 `--source-session-key`。
11. 成功后必须读取 `result-summary.json`。如果 `delivery.sendResult.status=sent`，才算已真实发送；如果不是 `sent`，必须按 `deliveryPackage.deliveryFiles` 里的完整文件清单逐个发送，不能只发 `.zip`。
12. 中间图层的 `raw/*.result.json` 里出现 `missing_delivery_target` 不等于 PSD 失败；最终交付以 `result-summary.json` 为准。
13. 分层必须是真 API 成功：任意图层 API 重试后仍失败，整单失败。禁止用原图切片、离线恢复、简化 prompt、NanoBanana 或 `_lossless` 还原层冒充分层成功。
14. PSD 不再生成 `[无损还原]` 层；压缩只在交付阶段进行，不改变 PSD 图层内容。

## 必须先做的视觉解析

运行命令前，先用当前会话里的视觉能力把图片拆成元素清单。元素要独立、可移动、适合在 Photoshop 单独成层；不要只写“前景”。

输出并使用这种格式：

```json
{"fg_elements": "品牌Logo,主标题文字,副标题文字,产品主体,人物角色,装饰图标,背景光效"}
```

元素命名要求：每个元素不超过 12 个汉字，使用英文逗号分隔；文字块、产品主体、角色、贴纸、按钮、气球、图标、装饰物要尽量拆开。

## 推荐命令

```bash
python3 {baseDir}/scripts/run_omni_delivery.py \
  --source "/absolute/path/to/source.png" \
  --feishu-user-id "ou_xxx" \
  --bg-prompt "背景提取说明" \
  --fg-elements "品牌Logo,主标题文字,IP角色,气球,纸飞机,风车,积木"
```

只有用户明确接受粗分层时，才允许这样运行：

```bash
python3 {baseDir}/scripts/run_omni_delivery.py \
  --source "/absolute/path/to/source.png" \
  --allow-2-layer \
  --bg-prompt "背景提取说明" \
  --fg-prompt "前景总体提取说明"
```

## 底层兼容入口

如需直接运行原始 pipeline：

```bash
python3 {baseDir}/omni-vision-psd-extractor/omni-vision-psd-extractor/scripts/run_omni_pipeline.py \
  --source "/absolute/path/to/source.png" \
  --out-dir "/Users/a123/.openclaw/workspace-design/outputs/omni-vision-psd-extractor/job_xxx" \
  --auto-extract \
  --bg-prompt "背景提取说明" \
  --fg-elements "品牌Logo,主标题文字,IP角色,气球,纸飞机,风车,积木" \
  --prompt-append-file "{baseDir}/omni-vision-psd-extractor/omni-vision-psd-extractor/references/万物提取.md"
```

## 交付说明

- 输出目录包含 `layered-output.psd`、`reverse-preview.png`、`manifest.json`、`scene.json`、`result-summary.json`。
- 默认会生成 `layered-output-delivery.zip` 和可能的 `.z01`、`.z02` 分卷。
- 单个分卷默认限制为 18MB；任一分卷超过限制时必须视为交付失败并重新处理。
- 分卷压缩只影响传输，不改变 PSD 内容和图层。
- 解压时把 `.zip` 和所有 `.z*` 分卷放在同一目录，从 `.zip` 主文件解压。
- 绝对不要只发送 `layered-output-delivery.zip`。必须发送 `result-summary.json` 中 `deliveryPackage.deliveryFiles` 列出的每一个文件；缺任意一个 `.z*` 分卷，用户都无法解压。
- 如果入口拿到了明确 Feishu 目标，脚本会发送预览图和所有分卷文件，并把每个文件的发送结果写入 `delivery.sendResult`。
- 如果入口没有拿到明确 Feishu 目标，脚本只生成文件并写 `pending_target_resolution`；此时当前会话 agent 必须使用真实飞书发送工具补发完整 `deliveryFiles`，不能只回复本地路径。
- 只有 `delivery.sendResult.status=sent` 且 `delivery.sendResult.allPartsSent=true`，才算压缩包完整送达。
