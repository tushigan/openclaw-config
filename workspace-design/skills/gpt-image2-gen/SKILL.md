---
name: gpt-image2-gen
version: 2.3.0
description: 统一 gpt-image-2-pro 生图入口：文生图、图生图、多参考图、按蒸馏卡自动锚定版式。✨ 2.3.0 新增：参考图自动压缩（默认启用）
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - curl
      env:
        - BANANA_API_URL
        - BANANA_API_KEY
        - BANANA_DEFAULT_MODEL
    emoji: "🍌"
---

# 图像生成技能（gpt-image-2 / gpt-image-2-pro，统一入口）

## 记忆系统集成（必读）

⚠️ **执行本 skill 前，必须先查询相关品牌档案**

### 查询品牌信息
```bash
# 查询品牌档案（获取调性、定位、目标受众）
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产（获取 Logo、VI 手册、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json

# 查询项目上下文（获取策略、创意方向）
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json
```

### 关键信息提取
从品牌档案中提取：
- **品牌调性** (`brand_tone`) - 决定整体风格和情绪
- **定位** (`positioning`) - 决定表达层级和差异点
- **目标受众** (`target_audience`) - 决定语境和沟通方式
- **核心价值观** (`core_values`) - 决定价值主张

### 品牌一致性要求
- 所有产出必须符合品牌调性
- 表达方式必须匹配目标受众
- 价值主张必须呼应品牌核心价值观
- 使用品牌资产库中的官方素材（Logo、VI 等）



**✨ v2.3.0 更新：参考图自动压缩功能已启用**
- 所有参考图自动压缩到长边 1920px，JPEG 85% 质量
- 大幅提升上传速度，降低生成失败率
- 典型压缩率：98%+（18MB → 200KB）
- 可通过 `--no-compress-refs` 关闭

通过 OpenAI-compatible Images API 调用 `gpt-image-2` / `gpt-image-2-pro`，统一支持：
- 日常随机文生图
- 图生图 / 多参考图（**参考图自动压缩**）
- 按蒸馏卡 ID 生成（自动拼蒸馏约束 + 自动挂载 skeleton 骨架图）

## Typed References

当多张参考图分别承担不同职责时，优先用 typed refs，不要把所有图都混成普通 `-r`：

- `--ref-product`: 产品真相，锁形态、材质、结构
- `--ref-layout`: 版式、摆位、裁切、机位 authority
- `--ref-style`: 风格、色调、光感、修图气质
- `--ref-background`: 背景或场景环境

如果 layout 和 style 分别来自不同参考图，优先拆成 `--ref-layout` + `--ref-style`。

## 配置

设置以下环境变量：

```bash
export BANANA_API_URL=”https://n.lconai.com”
export BANANA_API_KEY=”你的 n.lconai.com 主通道 key”
export BANANA_DEFAULT_MODEL=”gpt-image-2-pro”
export BANANA_API_URL_AIXOR=”https://direct.aixor.org”
export BANANA_API_KEY_AIXOR=”你的 direct.aixor.org 备用通道 key”
# 可选：primary / auto / aixor。默认 auto，会先走 n.lconai.com（主通道），再在可切换错误时尝试备用通道。
export BANANA_PROVIDER_MODE=”auto”
# 尺寸一律用像素，不要用比例字符串
```

### Provider 说明

- `n.lconai.com` 当前默认模型名：`gpt-image-2-pro`（**主通道**，稳定，智能模型路由）
- `direct.aixor.org` ≤4K 使用 `gpt-image-2`（**备用通道**，稳定100%，平均42秒，原生支持 4K）
- 脚本已内置 provider-aware 映射：
  - 命中 `n.lconai.com` 时，≤2K 自动用 `gpt-image-2`，>2K 自动用 `gpt-image-2-pro`
  - 命中 `direct.aixor.org` 时，`gpt-image-2-pro` 会自动改写为 `gpt-image-2`

这意味着上层 workflow 不需要因为供应商模型别名差异而单独改 prompt 或改任务脚本。

### 自动切换策略

- 默认 `BANANA_PROVIDER_MODE=”auto”`
- `auto` 模式下**主通道（n.lconai.com）优先**
- 但当主通道返回以下可切换错误时，会**直接切到备用通道（direct.aixor.org）**，不再先做多轮无意义等待：
  - `model_not_found`
  - `No available channel for model`
  - `正在加号请稍等`
- 常见 `429 / 500 / 502 / 503 / 504`

这条策略适合你现在这种”主通道偶发封禁 / 排队，但后面可能恢复”的场景。

- 若主通道刚刚触发过上述可切换错误，脚本会在一个短冷却窗口内优先走备用通道，避免批量出图时每一张都先撞一次主通道。

### 已验证尺寸

**n.lconai.com（主通道）已验证尺寸：**
- 文生图（gpt-image-2-pro）：`1024x1024`, `1536x2048`, `1728x2304`, `2048x2048`, `2448x3264`, `2560x1440`, `1440x2560`, `2880x2880`, `3840x2160`, `2160x3840`
- 图生图（gpt-image-2-pro）：`1024x1024`, `1536x2048`

**direct.aixor.org（备用通道）已验证尺寸：**
- 文生图（gpt-image-2）：`1024x1024`, `1536x2048`, `1728x2304`, `2048x2048`, `2448x3264`, `2560x1440`, `1440x2560`, `2880x2880`, `3840x2160`, `2160x3840`, `1280x3840`
- 图生图（gpt-image-2）：`1024x1024`, `1536x2048`

已确认拒绝：

- `3840x3840` → `Requested resolution exceeds the current pixel budget.`

对产品摄影工作流来说，这至少已经覆盖了：

- `1:1`
- `1:3`
- `3:4`
- `16:9`
- `9:16`

## 接口说明

### 端点
- Base URL: `${BANANA_API_URL}`
- Path: `/v1/images/generations`
- Method: `POST`
- Auth: `Authorization: Bearer <API_KEY>`

### 请求格式

**文生图：**
```json
{
  "model": "gpt-image-2-pro",
  "prompt": "一只可爱的小海獭",
  "n": 1,
  "size": "1024x1024",
  "response_format": "b64_json"
}
```

**图生图：**
```json
{
  "model": "gpt-image-2-pro",
  "prompt": "画个类似的图",
  "image": ["https://public-image-url.example.com/a.png"],
  "n": 1,
  "size": "1024x1024",
  "response_format": "b64_json"
}
```

## 尺寸规则（重要）

### 硬性约束（2026-05-08 实测确认）

上游 `gpt-image-2-pro` 有三个硬性限制：

1. **长边 ≤ 3840px** — 超过返回 `The longest edge must be less than or equal to 3840.`
2. **总像素 ≤ 8,294,400**（即 3840×2160）— 超过返回 `Requested resolution exceeds the current pixel budget.`
3. **长宽比 ≤ 3:1** — 超过返回 `The maximum supported aspect ratio is 3:1.`

只要 W×H > 8,294,400，即使长边 ≤ 3840 也会被拒绝。长宽比超出 3:1 同样会被拒绝，与像素预算无关（如 `1104x3840` 仅 4.2M 像素但仍被拒）。

### 格式规则
- **只用像素值**（`WxH`），如 `1024x1024`、`1536x1152`、`2048x1536`
- **不要用比例字符串**（`1:1` / `4:3` / `16:9` / `9:16` 等）—— 上游返回 `HTTP 400 “不合法的size”`
- 不要用 `1K` / `2K` / `4K` 这类 tier 值 —— 同样不稳定
- **宽高必须都能被 16 整除**，否则返回 `HTTP 400 “Width and height must both be divisible by 16.”`
  - 脚本已自动处理：不能被 16 整除的尺寸会自动向上取整并打印 `[warn]`

### 默认快速尺寸（低于 2K）

| 比例 | 默认像素 |
|------|----------|
| 1:1  | `1920x1920` |
| 16:9 | `1920x1080` |
| 9:16 | `1080x1920` |
| 4:3  | `1920x1440` |
| 3:4  | `1440x1920` |
| 4:5  | `1536x1920` |

默认优先效率。只有用户明确要求高清、4K、打印或大图时，才手动传更高像素。

### 常用像素推荐

#### 常规出图（稳定、快速）
- 方图：`1024x1024` / `1536x1536` / `1920x1920`
- 竖版海报（2:3 / 3:4）：`1280x1920` / `1440x1920`
- 横版 KV（3:2 / 4:3 / 16:9）：`1920x1080` / `1920x1280` / `1920x1440`
- 短视频封面 / 手机屏（9:16）：`1080x1920`

#### 高分出图（用户明确要求时）
- 方图：`2880x2880`
- 竖版（16:9→9:16）：`2160x3840`
- 竖版（3:2→2:3）：`2336x3504`
- 竖版（4:3→3:4）：`2448x3264`
- 横版（16:9）：`3840x2160`（标准 4K UHD）
- 横版（3:2）：`3504x2336`
- 横版（4:3）：`3264x2448`

### 超长图（详情页等）

- **不要用单张超长图直接出详情页** — 长图极易比例被改写、分辨率缩水、结构失真
- 正确做法：**分段生成，再拼接成长页**

> 现在凡是走 ratio-to-size 映射的 workflow，默认会使用上面的快速尺寸。不要默认拉满像素预算；只有用户明确要求高分辨率时才使用“高分出图”尺寸。

## 输出路径规范（强制）

- 生成图片一律写入当前 agent workspace 下的 `images/`
- 不要把产物直接堆在 workspace 根目录

## 参考图自动压缩（默认启用）

**为什么需要压缩？**
- 参考图文件过大会导致上传慢、生成失败率高
- 多张参考图时问题更明显
- 使用上一轮生成的高分辨率图作为参考时尤其需要

**压缩策略：**
- **长边限制**：1920px（足够清晰用于参考，又不会太大）
- **质量参数**：JPEG 85%（平衡质量和文件大小）
- **格式转换**：PNG → JPEG（大幅减小文件体积）
- **保持宽高比**：等比缩放，不变形
- **自动清理**：压缩后的临时文件自动删除

**压缩效果示例：**
```
[info] resized reference product.png: 3840x2160 → 1920x1080
[info] compressed reference product.png: 8234.5KB → 456.2KB (94.5% reduction)
```

**关闭压缩：**
如果需要使用原始高分辨率参考图（不推荐），可以添加 `--no-compress-refs` 参数：
```bash
python skills/gpt-image2-gen/scripts/generate.py \
  "保留主体，做成更强的广告感" \
  -r /path/high-res-ref.png \
  --no-compress-refs \
  -s 2048x1536 -o images/output.png
```

**注意：**
- 压缩只影响上传到 API 的参考图，不影响生成图的分辨率
- 生成图的分辨率由 `-s/--size` 参数控制
- 压缩需要 PIL/Pillow 库，如果未安装会自动跳过压缩并打印警告

## 一次生成多张（`-n/--count`）

默认生成 1 张；当用户说“同一个提示词一次生 N 张 / 给我 5 个备选 / 多来几张”之类意图时，直接传 `-n N`（范围 1~10）：

```bash
python skills/gpt-image2-gen/scripts/generate.py \
  "高端零食包装，干净白底，商业摄影" \
  -s 1024x1024 -n 4 -o images/product.png
# → images/product.png, images/product_2.png, images/product_3.png, images/product_4.png
```

实现细节（不影响使用）：
- 当 `count > 1` 时，脚本会把同一个端点上的多图请求拆成 `N` 个并行的单图请求，避免一张一张串行生成。
- 如果主端点这一批没有拿满 `N` 张，脚本会把该端点视为失败并切到备用端点重试同样的并行策略。
- 多张文件名规则：第 1 张落在 `-o` 指定路径；第 2 张起追加 `_2/_3/...`。

## 使用示例

```bash
python skills/gpt-image2-gen/scripts/generate.py \
  "高端零食包装，干净白底，商业摄影" \
  -s 1024x1024 -o images/product.png
```

```bash
python skills/gpt-image2-gen/scripts/generate.py \
  "保留主体，做成更强的广告感" \
  -r https://public-image-url.example.com/base.png \
  -r /path/local-logo.png \
  -s 2048x1536 -o images/product-edit.png
```

```bash
python skills/gpt-image2-gen/scripts/generate.py \
  --prompt "做一张新品上市主视觉，强调高级感与食欲" \
  --distill-id POSTER-DISTILL-P-009 \
  -r /path/style-ref.jpg \
  -s 1536x2048 -o images/p009-run.png
```

蒸馏卡模式说明：
- 传 `--distill-id` 后，会自动读取 `brand-poster-distiller` 卡片
- 自动挂载 skeleton 骨架图作为第一参考图，标注"版式骨架，请严格按此构图"
- 自动注入版式空间指导表（每个区域的用途、排版方向、字数限制），让 AI 做文案策划后填空
- 自动注入负面约束列表（基于版式特征推导的禁止项）
- 自动标注参考图角色（logo/product/style 等）
- **不注入**：summary / tags / 风格描述 / 原海报文案（这些由用户输入和参考图决定）
- 若 skeleton 缺失，自动调用 `render_layout.py --id <ID>` 先生成
- 可用 `--no-auto-skeleton` 关闭自动挂载

## 参考图角色标注（强烈建议使用）

gpt-image-2 本身不知道"哪张图是 LOGO、哪张是产品"。用下面这些带角色的 flag 替代 `-r`，脚本会自动在 prompt 里明确告诉模型每张图的用途：

```bash
python skills/gpt-image2-gen/scripts/generate.py \
  --prompt "做一张新品菠萝饼干海报" \
  --distill-id POSTER-DISTILL-P-011 \
  --ref-style    /path/art-style.jpg \
  --ref-logo     /path/logo.png \
  --ref-product  /path/product.png \
  --ref-ip       /path/ip.png \
  -s 1536x2048 -o images/x.png
```

支持的角色：`--ref-logo / --ref-product / --ref-ip / --ref-mascot / --ref-style / --ref-background / --ref-typography / --ref-element`。  
未标注的通用参考图仍可用 `-r`（脚本不会给它拼角色说明）。

最终参考图顺序：`skeleton（如启用） → --ref-logo → --ref-product → --ref-ip → --ref-mascot → --ref-style → --ref-background → --ref-typography → --ref-element → -r`。  
每个带角色的参考图都会在 prompt 里出现一条对应指令，例如：
> Image 3: brand LOGO — must be reproduced precisely, do not redraw, do not distort, do not invent new marks.

## 注意

- 文生图时不要传 `image`
- 图生图可传多个 `-r/--reference`，支持 URL 与本地文件混用
- 本地图片会自动转成 data URL 后发给 API
- 若接口返回 `url`，脚本会自动下载；若返回 `b64_json`，脚本会自动解码保存
- **做高分测试时注意**：
  - n.lconai.com 可能会出现尺寸缩水
  - 建议使用长边 ≤ 3840 的尺寸以获得稳定输出

## 命令构造规则（强制执行）

网关 exec preflight 安全检查会拒绝复杂命令，必须遵守以下规则：

### 允许的命令格式
- 直接执行：`python3 /path/to/generate.py --prompt "text" -s 1024x1024 -o output.png`
- 单行命令：不带 `\` 换行、不带 `&&`、不带 `$(...)`、不带 `set -e`
- 脚本执行：`bash /path/to/script.sh`（脚本内容可以复杂）

### 禁止的命令格式

| 模式 | 示例 | 被拒绝原因 |
|------|------|-----------|
| 多行换行 `\` | `python3 generate.py \`<br>`--prompt "text" \` | 网关认为是"复杂命令" |
| Shell 变量替换 | `$(cat prompt.txt)` | 需要子shell执行 |
| 链式命令 `&&` | `mkdir -p dir && python3 generate.py` | 多命令组合 |
| 前置 `set -e` | `set -e\npython3...` | shell内置命令 |
| `cd` 前置 | `cd /path && python3...` | 目录切换 |

### 推荐做法

当需要多步操作时：

1. **写 shell 脚本封装**
   ```bash
   #!/bin/bash
   set -euo pipefail
   python3 /path/to/generate.py --prompt "段A prompt" -r ref.jpg -s 1440x2560 -o segment_A.png
   python3 /path/to/generate.py --prompt "段B prompt" -r ref.jpg -s 1440x2560 -o segment_B.png
   ```

2. **执行脚本**
   ```bash
   bash /path/to/script.sh
   ```

3. **禁止先尝试复杂命令失败后再切脚本**，应该直接用脚本方式

### Prompt 过长时的处理

当 prompt 很长（超过 1000 字符）时：

1. 使用 `--prompt-file /path/to/prompt.txt` 参数（推荐）
2. 或写脚本，在脚本内读取 prompt 文件

### 错误信息识别

如果看到以下错误，说明命令被网关拒绝：
```
exec preflight: complex interpreter invocation detected; refusing to run without script preflight validation.
```

解决方案：把命令封装到 shell 脚本中，然后执行脚本。

## 飞书交付硬规则

生成完成后，如需由主会话发送图片给用户，请把文件复制到：

`/Users/a123/.openclaw/workspace/feishu-deliver/`

再由主会话引用该路径发图。

如果任务来自 Feishu 群聊或私聊，不能只生成图片和复制文件就结束。必须二选一：

1. 已知原始会话目标时，在命令里显式传入 `--feishu-chat-id oc_xxx` 或 `--feishu-user-id ou_xxx`，让 `generate.py` 直接发送。
2. 不在生图脚本里直发时，主会话必须读取同名 `*.result.json` 和 `*.delivery.json`，确认 `delivery_status`；若是 `failed/not_attempted`、`fallback_required=true`、`error=missing_delivery_target`，必须继续用真实飞书发送接口发送 `workspace/feishu-deliver/` 里的副本。

原始会话目标优先从 runtime context 读取；跨轮或补偿时可查 `/Users/a123/.openclaw/feishu/conversation-ids.json`，或执行 `python3 /Users/a123/.openclaw/scripts/feishu-id-registry.py resolve ... --json`。

本地路径、`MEDIA:/...` 文本、`feishu-deliver` 副本、或 `IMAGE GENERATED BUT NOT DELIVERED` 提示，都不算交付。只有飞书发送工具返回成功，才算完成。
