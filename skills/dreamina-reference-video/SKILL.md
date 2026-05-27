---
name: dreamina-reference-video
description: Use when the user wants to reduce 视频抽卡, keep 角色一致性, build 角色板或身份板与故事板, use 即梦 CLI 或 dreamina 或 Seedance 或 全能参考, or turn one idea into a staged 多参考图视频流程 before正式生成视频.
---

# 即梦参考视频 Skill

## Overview

用这套 skill 把”直接抽视频”改成”先锁世界、再锁角色、再锁镜头、最后生视频”。

默认流程固定为：

1. 原图
2. 身份依据整理
3. 故事板
4. 人工确认
5. 即梦视频

不要跳过人工确认关卡，除非用户明确要求承担直接生视频的风险。

## 新增功能（v2 优化）

### 1. 参考图自动归一化

**问题**：用户上传的大图（如 2160x3840 / 9MB）会导致图生图接口超时失败。

**解决**：自动压缩参考图到安全工作尺寸（默认 1920px 最大边长 / 3MB 以内）。

- 默认开启，可通过 `normalize_references: false` 关闭
- 压缩后的图片保存在 `refs/normalized/` 目录
- 归一化信息记录在 `refs/normalized/manifest.json`
- 透明通道自动铺白底
- 小图不会被放大

### 2. IP 约束字段优化

**新增两个字段**，替代原来的 `identity_anchor_rules`：

- `identity_structure`：结构真相（必须成立的特征）
  - 例如：”整体读成点赞大拇指体块”、”正面也能看到尾巴”
- `identity_forbidden`：禁止变形（不能出现的错误）
  - 例如：”禁止普通圆鸡化”、”禁止双翅膀”、”禁止人类手指”

**向后兼容**：旧的 `identity_anchor_rules` 会自动迁移到新字段（带”禁止”关键词的放 `identity_forbidden`，其他放 `identity_structure`）。

### 3. 故事板画幅强化

**问题**：生成的故事板每一格可能是横向长条，而不是目标画幅（如 9:16）。

**解决**：在 prompt 中明确要求”每一格都必须是独立的 {ratio} 成片画幅”。

### 4. 增强的 summary.md

新增内容：
- 参考图归一化结果（原始尺寸 → 工作尺寸）
- IP 约束规则展示（结构真相 + 禁止变形）
- 人工检查清单（故事板画幅、角色一致性、IP 约束验证）

## 先做什么

1. 先用白话确认最小输入：
   - 主体是谁
   - 主体要做什么
   - 场景 / 世界观
   - 风格 / 气质
   - 比例
   - 时长
   - 是否已有现成参考图
   - 当前是打样还是正式出片
2. 如果用户一句话已经给够这些信息，直接整理，不要重复追问。
3. 先运行：

```bash
python3 scripts/run_workflow.py preflight
```

4. 如果 `preflight` 报 `gpt_image_config` 或 `dreamina_credit` 失败，先把问题讲清楚，再继续下一步。

## 固定工作流

### 1. 准备运行目录与提示词

优先把需求写成一个简短 `brief.json`，再执行：

```bash
python3 scripts/run_workflow.py prepare --brief-file /path/to/brief.json
```

或者直接传最小字段：

```bash
python3 scripts/run_workflow.py prepare \
  --subject “橘猫” \
  --action “在欧洲老城广场跳 breaking” \
  --scene “欧洲老城石板广场，午后阳光” \
  --style “电影感街头纪实”
```

**新增字段**（可选）：

```bash
# IP 约束字段
--identity-structure “整体读成点赞大拇指体块” \
--identity-structure “正面也能看到尾巴” \
--identity-forbidden “禁止普通圆鸡化” \
--identity-forbidden “禁止双翅膀”
```

或在 `brief.json` 中：

```json
{
  “subject”: “黄小咕”,
  “action”: “在广场跳舞”,
  “scene”: “欧洲老城广场”,
  “style”: “3D 卡通”,
  “ratio”: “9:16”,
  “duration”: 5,
  “identity_structure”: [
    “整体读成点赞大拇指体块”,
    “正面也能看到尾巴”,
    “只有单侧翅膀（右侧装饰性小翅膀）”
  ],
  “identity_forbidden”: [
    “禁止普通圆鸡化”,
    “禁止双翅膀”,
    “禁止人类手指/手掌”,
    “禁止正面尾巴消失”
  ],
  “existing_references”: {
    “identity_source”: “/path/to/character-sheet.png”
  }
}
```

默认值已经写死：

- 比例：`16:9`
- 时长：`5`
- 质量档：`draft`
- `draft` -> `seedance2.0fast`
- `final` -> `seedance2.0_vip` + 优先 `1080p`
- 故事板策略：`auto_beats`
- 如果用户给了准确三视图但没指定身份策略：默认 `reuse_exact`
- 参考图归一化：默认开启

`prepare` 会自动落这些文件：

- `brief.json`
- `prompts/original.txt`
- `prompts/identity-board.txt`
- `prompts/storyboard.txt`
- `prompts/video.txt`
- `summary.md`

### 2. 生成三张参考图

先看 dry run：

```bash
python3 scripts/run_workflow.py generate-refs --run-dir /path/to/run --dry-run
```

确认命令没问题后再执行：

```bash
python3 scripts/run_workflow.py generate-refs --run-dir /path/to/run
```

角色分工不要改：

- `原图`：只负责风格与世界
- `身份板 / identity-source`：只负责角色一致性
- `故事板`：只负责关键帧、镜头与动作节奏

如果用户已经有现成参考图，把路径写进 `brief.json` 的 `existing_references`，脚本会自动复制进本次运行目录，并**自动归一化到安全尺寸**。

如果用户给的是准确三视图、官方定稿或最高结构依据，优先放进：

- `existing_references.identity_source`

身份策略固定分两种：

- `reuse_exact`
  - 直接把 `identity_source` 当最高角色依据
  - 不额外生成 AI 身份板
- `extend_from_source`
  - 允许基于 `identity_source` 再延展一张更正式的身份板
  - 但后续故事板和视频仍优先服从 `identity_source`

### 3. 人工确认关卡

参考图生成完成后，必须先把下面这些信息给用户看：

- 参考图路径
- 本次摘要（`summary.md`）
- 本次关键帧提纲与规划格数
- 当前角色结构最高依据是哪一张图
- **参考图归一化结果**（如果有压缩）
- **人工检查清单**（故事板画幅、IP 约束验证）
- 是否存在明显串模板、角色漂移、世界观冲突

只有在用户确认通过后，才进入视频阶段。

### 4. 提交即梦视频

先看 dry run：

```bash
python3 scripts/run_workflow.py submit-video --run-dir /path/to/run --dry-run
```

确认后正式提交：

```bash
python3 scripts/run_workflow.py submit-video --run-dir /path/to/run
```

默认只走：

- `dreamina multimodal2video`

不要把第一版主流程改成：

- `frames2video`
- `image2video`
- `multiframe2video`

这些只作为后续扩展，不作为默认主通路。

### 5. 查询并下载结果

如果提交后没有直接拿到完整结果，执行：

```bash
python3 scripts/run_workflow.py fetch-result --run-dir /path/to/run
```

结果默认下载到：

- `dreamina/downloads/`

提交与查询结果默认写到：

- `dreamina/submit_id.txt`
- `dreamina/result.json`

## 关键约束

1. 不要让 `身份板` 承担背景叙事。
2. 不要让 `故事板` 重新定义角色。
3. 不要让 `视频提示词` 推翻前三张图。
4. 故事板固定强调：
   - `黑白`
   - `导演分镜感`
   - `强连续空间`
   - **每一格都是独立的成片画幅**（不是横向长条）
   - `格数服务于关键帧，不追求平均切段`
5. 默认按关键帧自动规划格数：
   - 简单单动作单转折：优先 `4-6 格`
   - 连续动作推进或明显情绪变化：优先 `6-8 格`
   - 多段剧情 / 多人物 / 多空间：最多到 `8-10 格`
6. 默认先出参考图，再让用户确认，不要直接冲视频。
7. **大参考图会自动压缩**：超过 1920px 或 3MB 的图片会被归一化到安全尺寸。

## 参考资料

- 角色分工与方法边界：`references/methodology.md`
- 四类提示词模板与可改字段：`references/prompt-templates.md`

## 交付时怎么汇报

至少明确告诉用户：

1. 本次运行目录
2. 参考图路径
3. **参考图归一化结果**（如果有压缩）
4. 本次关键帧提纲与规划格数
5. **人工检查清单**（从 `summary.md` 中提取）
6. 视频结果路径
7. 下次复用时最值得改的字段

## 故障排除

### 参考图太大导致超时

**症状**：`Read timed out. (read timeout=600)` 或 `524 timeout`

**原因**：参考图超过 3MB 或分辨率过高（如 2160x3840）

**解决**：
- v2 版本会自动归一化，无需手动处理
- 如果仍然超时，检查 `refs/normalized/manifest.json` 确认压缩是否成功
- 可以手动关闭归一化：`”normalize_references”: false`

### 故事板每格画幅不对

**症状**：生成的故事板是横向长条，而不是 9:16 竖版画幅

**解决**：
- v2 版本已在 prompt 中明确要求每格独立画幅
- 检查 `summary.md` 中的人工检查清单
- 如果仍然不对，可以在 `notes` 中补充：”每格必须是竖版 9:16，不要横向长条”

### IP 角色一致性问题

**症状**：生成的视频中角色出现了不该有的特征（如双翅膀、人类手指）

**解决**：
- 使用新的 `identity_structure` 和 `identity_forbidden` 字段明确约束
- 在 `summary.md` 的人工检查清单中逐项验证
- 如果参考图阶段就已经漂移，不要继续生成视频，先修正参考图

### 向后兼容

旧的 `identity_anchor_rules` 仍然支持，会自动迁移到新字段：
- 带”禁止”、”不要”、”不能”关键词的 → `identity_forbidden`
- 其他 → `identity_structure`
