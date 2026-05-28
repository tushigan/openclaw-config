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

## 环境要求

### Python 版本
- **最低要求**：Python 3.9+
- **推荐版本**：Python 3.10 或更高

### 依赖安装

```bash
pip install -r requirements.txt
```

**必需依赖**：
- `Pillow>=10.0.0` - 用于参考图归一化（压缩、格式转换）

如果缺少 Pillow，参考图归一化功能将无法使用，可能导致大图上传失败。

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

## 标准执行流程（必须按顺序）

这是固定流程，不要跳步骤，不要省略验证：

```
preflight → prepare → generate-refs → validate-run → complete-manual-checks → review-run → submit-video → fetch-result
```

### 步骤 1：preflight - 环境检查

检查 GPT 图生图配置和即梦额度是否可用。

```bash
python3 scripts/run_workflow.py preflight
```

如果失败，先解决配置问题再继续。

### 步骤 2：prepare - 准备运行目录与提示词

优先把需求写成 `brief.json`，再执行：

```bash
python3 scripts/run_workflow.py prepare --brief-file /path/to/brief.json
```

或直接传最小字段：

```bash
python3 scripts/run_workflow.py prepare \
  --subject “橘猫” \
  --action “在欧洲老城广场跳 breaking” \
  --scene “欧洲老城石板广场，午后阳光” \
  --style “电影感街头纪实”
```

**IP 约束字段**（可选）：

```bash
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

默认值：

- 比例：`16:9`
- 时长：`5`
- 质量档：`draft`（`draft` → `seedance2.0fast`，`final` → `seedance2.0_vip` + 1080p）
- 故事板策略：`auto_beats`
- 身份策略：如果提供准确三视图，默认 `reuse_exact`
- 参考图归一化：默认开启

`prepare` 输出文件：

- `brief.json`
- `prompts/original.txt`
- `prompts/identity-board.txt`
- `prompts/storyboard.txt`
- `prompts/video.txt`
- `summary.md`
- `risk_analysis.json`（如果有风险）

**prepare 完成后必须做的事：**

1. **汇报风险摘要**（如果有高风险）：
   - 总风险数
   - 高风险数
   - 最值得现在就改的前 3 条
   
2. **说明参考图复用策略**（如果提供了 `final_frame_poster`）：
   - 会自动复用为 `original`
   - 不会额外生成冲突原图

### 步骤 3：generate-refs - 生成参考图

先看 dry run：

```bash
python3 scripts/run_workflow.py generate-refs --run-dir /path/to/run --dry-run
```

确认后执行：

```bash
python3 scripts/run_workflow.py generate-refs --run-dir /path/to/run
```

角色分工：

- `原图`：只负责风格与世界
- `身份板 / identity-source`：只负责角色一致性
- `故事板`：只负责关键帧、镜头与动作节奏

现成参考图支持：

- `existing_references.identity_source` - 准确三视图、官方定稿
- `existing_references.final_frame_poster` - 尾帧定版海报

**重要：提供 `final_frame_poster` 时，系统会自动将其复用为 `original`，避免生成与定版不一致的原图。**

身份策略：

- `reuse_exact`：直接用 `identity_source`，不额外生成 AI 身份板
- `extend_from_source`：基于 `identity_source` 延展身份板，但后续仍优先服从 `identity_source`

**generate-refs 完成后必须做的事：**

1. **使用 message 工具发送参考图给用户**：
   - 发送 `original.png`
   - 发送 `identity-board.png` 或 `identity-source.png`
   - 发送 `storyboard.png`
   
2. **汇报关键信息**：
   - 参考图路径
   - 关键帧提纲与规划格数
   - 角色结构最高依据是哪张图
   - 参考图归一化结果（如果有压缩）

3. **明确等待用户确认**：
   - 说明”请先确认这 3 张图”
   - 说明”确认后我会继续验证并提交视频”

### 步骤 4：validate-run - 验证参考图

**这一步是必须的，不能跳过。**

参考图生成后，默认验证 `storyboard` 阶段（不是 `reference_system`）：

```bash
python3 scripts/run_workflow.py validate-run --run-dir /path/to/run --stage storyboard
```

这会检查：
- 故事板画幅是否正确（每格是独立的成片画幅，不是横向长条）
- 角色一致性（是否出现不该有的特征）
- IP 约束验证（`identity_structure` 和 `identity_forbidden`）

验证结果保存在 `validation_reports/storyboard_*.json`。

### 步骤 5：complete-manual-checks - 完成人工检查

**用户确认参考图后，必须回写人工检查结果。**

这一步不能省略，否则 `review-run` 会拒绝放行。

人工检查项（从 `summary.md` 中提取）：
- 故事板每格画幅是否正确
- 角色是否出现漂移或串模板
- IP 约束是否被违反
- 世界观是否一致

回写方式：在最新的验证报告中补充 `manual_checks` 字段，或使用命令：

```bash
python3 scripts/run_workflow.py complete-manual-checks --run-dir /path/to/run --all-passed
```

如果有问题，标记具体检查项为 `failed`，并说明原因。

### 步骤 6：review-run - 决定下一步

**这一步检查验证结果和人工检查是否完成。**

```bash
python3 scripts/run_workflow.py review-run --run-dir /path/to/run
```

`review-run` 会返回三种结果：

- `proceed`：验证通过且人工检查完成，可以提交视频
- `iterate`：发现问题，需要重新生成参考图
- `ask_user`：人工检查未完成，需要用户确认

**只有返回 `proceed` 时，才能进入下一步。**

### 步骤 7：submit-video - 提交即梦视频

先看 dry run：

```bash
python3 scripts/run_workflow.py submit-video --run-dir /path/to/run --dry-run
```

确认后提交：

```bash
python3 scripts/run_workflow.py submit-video --run-dir /path/to/run
```

默认使用 `dreamina multimodal2video`。

其他模式（`frames2video`、`image2video`、`multiframe2video`）只作为扩展，不是默认主通路。

### 步骤 8：fetch-result - 查询并下载结果

如果提交后没有直接拿到完整结果：

```bash
python3 scripts/run_workflow.py fetch-result --run-dir /path/to/run
```

结果下载到 `dreamina/downloads/`。

提交与查询结果记录在：
- `dreamina/submit_id.txt`
- `dreamina/result.json`

## 确认关卡规则（不可跳过）

### 规则 1：参考图生成后必须发图

**generate-refs 完成后，必须使用 message 工具发送参考图给用户。**

- 发送 `original.png`
- 发送 `identity-board.png` 或 `identity-source.png`
- 发送 `storyboard.png`

**没发图，不算进入确认。**

### 规则 2：必须明确等待用户确认

发图后，必须明确告诉用户：

- "请先确认这 3 张图"
- "确认后我会继续验证并提交视频"

**没明确等待，不算确认关卡。**

### 规则 3：用户确认前不得提交视频

只有以下情况可以继续：

- 用户明确说"确认"、"可以"、"继续"
- 用户明确要求"跳过确认，直接生成视频"（需承担风险）

**没确认，不得提交视频。**

### 规则 4：确认后必须回写人工检查

用户确认后，必须执行：

```bash
python3 scripts/run_workflow.py complete-manual-checks --run-dir /path/to/run --all-passed
```

或在验证报告中补充 `manual_checks` 字段。

**没回写，review-run 会拒绝放行。**

### 规则 5：review-run 必须返回 proceed 才能提交

执行 `review-run` 后，只有返回 `proceed` 才能继续。

- `iterate`：需要重新生成参考图
- `ask_user`：需要用户确认

**没有 proceed，不得提交视频。**

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

## 验收标准

### 第一批优化验收标准

连续跑一轮测试时，必须满足：

1. **不催也能走到确认**：
   - 用户不催促，agent 也能自动走到"发图等待确认"
   - agent 主动发送参考图
   - agent 主动汇报关键信息
   - agent 明确等待用户确认

2. **验证不能被跳过**：
   - 没有 `storyboard` 验证报告时，不能进视频提交
   - `validate-run` 默认验证 `storyboard` 阶段
   - 验证报告保存在 `validation_reports/` 目录

3. **人工检查必须回写**：
   - 没有 `manual_checks` 回写时，不能被 review 放行
   - `review-run` 返回 `ask_user` 时，必须完成人工检查
   - 完成后 `review-run` 才能返回 `proceed`

4. **风险必须汇报**：
   - `prepare` 后如果有高风险，必须主动汇报
   - 汇报内容：总风险数、高风险数、前 3 条建议
   - 不能等用户问才说

## 参考资料

- 角色分工与方法边界：`references/methodology.md`
- 四类提示词模板与可改字段：`references/prompt-templates.md`

## 交付时怎么汇报

### 固定汇报模板

**不是文学创作，是工作口令。**

#### prepare 完成后

如果有高风险：

```
准备完成。本次运行目录：[路径]

⚠️ 风险提示：
- 总风险数：X 个
- 高风险数：Y 个
- 最值得现在就改的前 3 条：
  1. [风险描述]
  2. [风险描述]
  3. [风险描述]

是否需要先修改 prompt 再继续？
```

如果提供了 `final_frame_poster`：

```
准备完成。本次运行目录：[路径]

📌 参考图复用策略：
- 检测到 final_frame_poster，会自动复用为 original
- 不会额外生成冲突原图
```

#### generate-refs 完成后

```
参考图已生成。

📊 本次关键帧规划：
- 格数：X 格
- 关键帧提纲：[简要列出]
- 角色结构最高依据：[identity-source 或 identity-board]

📷 参考图归一化结果：
- original.png：[原始尺寸] → [工作尺寸]
- identity-board.png：[原始尺寸] → [工作尺寸]
- storyboard.png：[原始尺寸] → [工作尺寸]

[发送 3 张参考图]

请先确认这 3 张图。确认后我会继续验证并提交视频。
```

#### validate-run 完成后

```
验证完成。

✅ 验证通过项：
- [检查项 1]
- [检查项 2]

⚠️ 需要人工确认项：
- 故事板每格画幅是否正确
- 角色是否出现漂移或串模板
- IP 约束是否被违反

请确认以上检查项。
```

#### submit-video 完成后

```
视频已提交。

📋 提交信息：
- 任务 ID：[submit_id]
- 预计等待时间：[时长]
- 结果保存路径：dreamina/downloads/

我会持续查询结果。
```

#### fetch-result 完成后

```
视频已下载。

📁 结果路径：[完整路径]
📊 视频信息：
- 分辨率：[宽x高]
- 时长：[秒数]
- 文件大小：[MB]

💡 下次复用时最值得改的字段：
- [建议 1]
- [建议 2]
```

### 最少必须告诉用户的信息

1. 本次运行目录
2. 参考图路径
3. **参考图归一化结果**（如果有压缩）
4. 本次关键帧提纲与规划格数
5. **风险摘要**（如果有高风险）
6. **人工检查清单**（从 `summary.md` 中提取）
7. 视频结果路径
8. 下次复用时最值得改的字段

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
