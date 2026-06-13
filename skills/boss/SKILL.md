---
name: boss
description: 广告公司总控岗位。用于协调完整品牌战役和整合营销流程，从 Brief 收集到策略、创意对齐、执行和修订。触发词：品牌全案、整合营销、营销战役、Launch Campaign。
metadata:
  openclaw:
    requires:
      bins:
        - python3
---

# BOSS

## Overview

作为广告公司岗位协作总控，强制维护从客户需求到具体内容执行的岗位顺序。任何品牌全案或整合营销任务都必须先由 Account Executive 基于 brief 模版收集需求并起草问题和目标，再由 AE、Strategy Director、Creative Director 三方确认问题和目标，之后才进入资料收集、策略、创意方向确认、文案与设计执行。

## Project Memory System

每个品牌全案项目都必须建立项目记忆系统，包括品牌档案和项目档案。

### 项目目录结构

```
workspace/projects/
├── _registry.json              # 项目注册表（全局索引）
├── 品牌名/
│   ├── _brand-profile.json     # 品牌档案（跨项目复用）
│   ├── _brand-assets/          # 品牌资产库
│   │   ├── logos/
│   │   ├── vi-manual/
│   │   └── reference-images/
│   ├── Campaign名称/
│   │   ├── project.json        # 项目元信息
│   │   ├── brief.json          # AE Brief
│   │   ├── problem-alignment.json  # 问题与目标对齐
│   │   ├── research-request.json   # 资料收集清单
│   │   ├── strategy.json       # 策略文档
│   │   ├── creative-direction.json # 创意方向
│   │   ├── materials/          # 项目素材
│   │   │   ├── research/
│   │   │   ├── reference/
│   │   │   └── client-assets/
│   │   └── outputs/            # 产出文件
│   │       ├── copy/
│   │       ├── design/
│   │       └── final/
```

### 项目立项流程

1. 收到品牌全案任务时，首先检查是否已有该品牌的档案
2. 如果是新品牌，运行 `scripts/init_agency_project.py` 创建品牌档案和项目
3. 如果是老品牌，从品牌档案中读取品牌信息，创建新项目
4. 项目创建后，按照 7 阶段工作流推进，每个阶段完成后更新对应的 JSON 文件

### 常用脚本

1. `scripts/init_agency_project.py`
   - 初始化新项目，如果品牌不存在则创建品牌档案
   - 参数：`--workspace-root`, `--brand-name`, `--campaign-name`, `--campaign-type`
   - 可选品牌信息：`--brand-name-en`, `--industry`, `--category`, `--positioning`, `--brand-tone`, `--target-audience`, `--core-values`

2. `scripts/find_brand_profile.py`
   - 查找品牌档案（供其他 agent 使用）
   - 参数：`--workspace-root`, `--brand-name`

3. `scripts/find_active_project.py`
   - 查找品牌的活跃项目
   - 参数：`--workspace-root`, `--brand-name`

4. `scripts/archive_material.py`
   - 归档项目材料
   - 参数：`--project-dir`, `--source-path`, `--material-type` (research/reference/client-assets)

5. `scripts/update_stage.py`
   - 更新项目阶段状态
   - 参数：`--project-dir`, `--stage`, `--status`, `--user-confirmed`

### 跨 agent 协作

- **design agent 调用生图 skill 时**，可通过 `find_brand_profile.py` 读取品牌档案
- **归档产出时**，使用 `archive_material.py` 将生成的图片归档到项目的 `outputs/design/` 目录
- **main agent 协调时**，通过 `find_active_project.py` 获取当前活跃项目的上下文

## Role Routing

每个阶段必须按照以下规则执行，包括角色、派发 agent 和调用 skill：

| 阶段 | 角色 | 派发给 Agent | 调用 Skill | 说明 |
|------|------|-------------|-----------|------|
| 1. 需求收集 | Account Executive | `main` 自己执行 | `kefu-ae` | 收集客户需求、整理已知信息和未知信息 |
| 2. 问题目标确认 | AE + Strategy Director + Creative Director | `main` 协调三方 | 无 | AE 起草，三方共同确认问题、目标、限制 |
| 3. 资料收集 | Account Executive | `main` 自己执行 | `kefu-ae` | 列出并收集所需资料（行业、竞品、消费者、品牌） |
| 4. 策略制定 | Strategy Director | **`strategy`** | **`celue-zj`** | 基于已确认目标和资料制定策略 |
| 5. 创意方向 | Creative Director | **`strategy`** | **`chuangyi-zj`** | 基于策略制定创意方向 |
| 6. 方向确认 | AE + Strategy Director + Creative Director | `main` 协调三方 | 无 | 三方共同确认创意方向，形成执行依据 |
| 7a. 文案执行 | Copywriter | **`copywriter`** | **`wenan`** | 根据已确认方向产出文案 |
| 7b. 设计执行 | Designer | **`design`** 或 **`design-shared`** | **`sheji`** + 执行 skills | 根据已确认方向产出视觉内容 |
| 7c. TVC 故事版执行 | Storyboard / AI Video Previsualization | **`design`** 或 **`design-shared`（生图高手）** | **`dreamina-reference-video`** + 必要时 `gpt-image2-gen` | TVC / 品牌片 / AI 视频任务在分镜头脚本确认后，必须输出故事版画面 |

**重要说明**：
- **粗体标注的 agent 和 skill** 表示必须派发给专家 agent，不能由 `main` 自己执行
- `main` 负责协调阶段（2、6）和 AE 阶段（1、3）
- 策略、创意、文案、设计阶段必须派发给对应的专家 agent
- 只要任务是 TVC / 品牌片 / AI 视频 / 分镜视频，文字分镜脚本完成后不能停在文字稿；必须进入阶段 7c，派发给生图高手生成故事版画面
- 每次派发时必须在任务描述中明确指定要调用的 skill（见下方"派发任务模板"章节）

## Dispatch Templates

当 `main` agent 执行 boss skill 时，必须按照以下模板派发任务，确保明确指定 agent 和 skill。

**⚠️ 重要：飞书话题群消息投送规则**
- Subagent 完成后**禁止直接投送给最终用户**（会创建新话题，导致消息混乱）
- Subagent 只回传文件路径和核心摘要给 `main`
- 由 `main` 在原话题下读取产出并转发给用户
- 设计类任务（图片）例外：subagent 需要直接发送图片，但文字说明由 main 转发

### 阶段 4：策略制定

```json
{
  "runtime": "subagent",
  "agentId": "strategy",
  "task": "【策略制定任务】\n\n**必须使用 celue-zj skill**\n\n**交付模式：静默回传**\n你是被 main agent 派发的 subagent。完成后：\n- ✅ 将策略文档写入 workspace-strategy/outputs/\n- ✅ 回传文件绝对路径和核心摘要（3-5 句话）\n- ❌ 不要使用 message 工具直接投送给最终用户\n- ❌ 不要发送完整策略内容（会创建新话题）\n由 main 负责在原话题下转发给用户。\n\n**前置信息**：\n- 品牌档案：[品牌档案路径或关键信息]\n- 已确认问题：[问题描述]\n- 已确认目标：[目标描述]\n- 已收集资料：[资料清单]\n\n**任务要求**：\n基于以上信息，使用 celue-zj skill 制定策略，包括问题诊断、洞察、核心主张、传播任务和战役架构。\n\n**输出格式**：\n回传内容必须包含：\n1. 文件绝对路径\n2. 策略核心摘要（问题诊断/洞察/核心主张，各1句话）\n3. 完成状态确认",
  "mode": "run",
  "timeoutSeconds": 1800,
  "lightContext": true
}
```

### 阶段 5：创意方向

```json
{
  "runtime": "subagent",
  "agentId": "strategy",
  "task": "【创意方向制定任务】\n\n**必须使用 chuangyi-zj skill**\n\n**交付模式：静默回传**\n你是被 main agent 派发的 subagent。完成后：\n- ✅ 将创意方向文档写入 workspace-strategy/outputs/\n- ✅ 回传文件绝对路径和核心摘要（3-5 句话）\n- ❌ 不要使用 message 工具直接投送给最终用户\n- ❌ 不要发送完整创意方向内容（会创建新话题）\n由 main 负责在原话题下转发给用户。\n\n**前置信息**：\n- 品牌档案：[品牌档案路径或关键信息]\n- 已确认策略：[策略文档路径]\n- 策略核心主张：[核心主张摘要]\n\n**任务要求**：\n基于已确认策略，使用 chuangyi-zj skill 制定创意方向，包括方向名称、核心创意、创意机制、可延展触点和风险。\n\n**输出格式**：\n回传内容必须包含：\n1. 文件绝对路径\n2. 创意方向核心摘要（方向名称/核心创意/关键机制，各1句话）\n3. 完成状态确认",
  "mode": "run",
  "timeoutSeconds": 1200,
  "lightContext": true
}
```

### 阶段 7a：文案执行

```json
{
  "runtime": "subagent",
  "agentId": "copywriter",
  "task": "【文案创作任务】\n\n**必须使用 wenan skill**\n\n**交付模式：静默回传**\n你是被 main agent 派发的 subagent。完成后：\n- ✅ 将文案写入 workspace-copywriter/outputs/copy_YYYYMMDD_主题.md\n- ✅ 回传文件绝对路径和版本摘要\n- ❌ 不要使用 message 工具直接投送给最终用户\n- ❌ 不要发送完整文案内容（会创建新话题）\n由 main 负责在原话题下转发给用户。\n\n**前置信息**：\n- 品牌档案：[品牌档案路径或关键信息]\n- 已确认创意方向：[创意方向文档路径]\n- 策略 brief：[策略摘要]\n- 具体需求：[文案类型、渠道、规格等]\n\n**任务要求**：\n基于已确认的创意方向和策略，使用 wenan skill 产出文案（Campaign主题/KV文案/社媒文案/脚本等）。\n\n**输出格式**：\n- 提供 2-3 个版本\n- 回传内容必须包含：\n  1. 文件绝对路径\n  2. 各版本核心差异说明（每版本1句话）\n  3. 完成状态确认",
  "mode": "run",
  "timeoutSeconds": 1200,
  "lightContext": true
}
```

### 阶段 7b：设计执行

```json
{
  "runtime": "subagent",
  "agentId": "design",
  "task": "【视觉设计任务】\n\n**必须使用 sheji skill（若需要视觉方向），然后调用执行 skills**\n\n**交付模式：混合模式**\n你是被 main agent 派发的 subagent。完成后：\n- ✅ 图片文件可以直接通过 message 工具的 path 参数发送给用户（飞书支持图片直接投送）\n- ✅ 将图片写入 workspace-design/images/\n- ✅ 回传文件绝对路径和设计说明摘要\n- ⚠️ 文字说明保持简短（1-2 句话），详细说明由 main 转发\n- ❌ 不要发送大段文字内容（会创建新话题）\n\n**前置信息**：\n- 品牌档案：[品牌档案路径或关键信息]\n- 已确认创意方向：[创意方向文档路径]\n- 文案内容：[文案文档路径]\n- 具体需求：[物料类型、尺寸、渠道等]\n\n**任务要求**：\n1. 如果需要视觉方向，先使用 sheji skill 输出视觉方向\n2. 根据物料类型调用对应执行 skill：\n   - 品牌海报 → brand-poster-creator\n   - 产品摄影 → product-photography-workflow\n   - 详情页 → xiangqingye-desigen\n   - 其他 → gpt-image2-gen 或相应 skill\n\n**输出格式**：\n- 图片通过 message 工具发送（带简短说明）\n- 回传内容必须包含：\n  1. 图片文件绝对路径\n  2. 设计核心说明（1-2 句话）\n  3. 完成状态确认",
  "mode": "run",
  "timeoutSeconds": 1800,
  "lightContext": true
}
```

### 阶段 7c：TVC 故事版执行（强制）

适用条件：只要项目目标包含 TVC、品牌片、广告片、AI 视频、视频分镜、分段生成视频、即梦 / Kling / Seedance 等视频执行，且已经产出文字分镜脚本或 AI 视频分段脚本，就必须进入本阶段。不得只把文字分镜交给用户确认后结束。除非用户明确说“只要文字脚本 / 暂不出图”，否则不需要再额外询问“是否要生成故事版”，应直接派发生图高手开始故事版。

```json
{
  "runtime": "subagent",
  "agentId": "design",
  "task": "【TVC故事版生成任务】\n\n**必须使用 dreamina-reference-video skill**\n**执行 agent：生图高手（design / design-shared）**\n\n**交付模式：混合模式**\n你是被 main agent 派发的生图高手。完成后：\n- ✅ 生成故事版画面文件，并写入 workspace-design/outputs/[项目名]-dreamina-storyboard-[日期]/\n- ✅ 同步归档到 main 项目目录 outputs/design/\n- ✅ 可用 message 工具的 path 参数发送图片给用户；文字说明保持 1-2 句话\n- ✅ 回传故事版图片绝对路径、结果 JSON / manifest 路径、质检结论\n- ❌ 不要提交正式视频生成；本阶段只做故事版 / 参考图确认\n- ❌ 不要只返回 prompt 或本地路径而不生成画面\n\n**前置信息**：\n- 项目目录：[项目目录绝对路径]\n- 已确认策略：[策略文档路径]\n- 已确认创意方向：[创意方向文档路径]\n- 文字分镜脚本 / AI 视频分段脚本：[脚本文档路径]\n- 品牌 / IP / 包装参考素材：[素材路径清单]\n- 输出比例 / 时长：[如 16:9 / 30s]\n\n**执行要求**：\n1. 先读取 /Users/a123/.openclaw/workspace-design/skills/dreamina-reference-video/SKILL.md。\n2. 按 dreamina-reference-video 的故事版标准执行：先锁主体身份和世界观，再生成故事版；不直接跳到视频。\n3. 故事版必须服务后续视频生成：每格是独立成片画幅，镜头顺序清楚，主体一致，场景连续，运镜 / 动作意图明确。\n4. 对 IP / 品牌任务，必须明确 reference image 角色：identity-source 负责角色身份，style/world reference 负责风格与世界，storyboard 负责镜头节奏；不要混用职责。\n5. 中文 Logo、包装文字、结尾文案默认后期合成；故事版里只允许无字占位，避免 AI 生成假字。\n6. 若一次生成完整 8 格故事板内容偏移，必须主动拆成更稳的 4+4 或分段故事版重跑，例如：01-04 现实入口到云路入口，05-08 开心 / 治愈 / 好吃 / 品牌定格。\n7. 若 dreamina-reference-video 的完整 original → identity-board → storyboard 链路卡住，可说明原因后降级为“只生成故事版”的短链路，但仍必须沿用该 skill 的身份锁定、画幅、连续性和人工确认标准。\n8. 质检时必须检查：是否覆盖每个分镜段落、主体是否贴官方 IP、是否有产品/包装轻露出、是否出现干扰性文字、是否适合下一步视频生成。\n\n**输出格式**：\n回传内容必须包含：\n1. 故事版图片绝对路径\n2. 结果 JSON / manifest 绝对路径\n3. 质检结论：可确认 / 需重跑 / 建议拆分重跑\n4. 如果重跑，说明重跑策略和新文件名",
  "mode": "run",
  "timeoutSeconds": 1800,
  "lightContext": true
}
```

**模板使用规则**：
- 模板中的 `[占位符]` 必须替换为实际内容
- `timeoutSeconds` 可根据任务复杂度调整（简单任务 600s，复杂任务 1800s）
- 品牌档案路径可通过 `find_brand_profile.py` 获取
- 派发前必须确认前置条件已满足（如策略已确认、资料已收集等）
- TVC 故事版阶段必须派发给生图高手；`main` 只能做协调、质检、转发和必要的 prompt 压缩，不应自己替代设计 agent 完成故事版执行

**派发后持续轮询协议（强制）**：
- `main` 使用 `sessions_spawn` 派发任何 subagent 后，必须记录：agent、任务标签、sessionId/runId（如工具返回）、开始时间、timeout、预期产物路径。
- 派发后立即在原话题给用户一次可见回执：说明已派发给谁、正在做什么、预计多久、下一次检查时间。
- 只要 subagent 未完成，`main` 必须主动轮询，不得等用户催问。普通策略/文案任务每 2-3 分钟查一次；生图/故事版/视频相关任务每 60-90 秒查一次，或按工具返回的运行状态更短间隔检查。
- 每次轮询后，如果仍在运行，必须在原话题给一句短状态；如果状态没有变化，至少每 3-5 分钟给一次可见心跳。
- `main` 不得在存在 active subagent 时用像“我等它完成”这样的最终语气结束；如果受运行时限制必须结束本轮，必须明确写出当前仍在运行、最近一次检查结果、下一次检查计划。
- subagent 完成后，`main` 必须读取回传文件或 session 结果，验证产物存在，再在原话题交付；不能只依赖 subagent 的完成摘要。
- subagent 失败、超时、无输出、输出路径不存在时，`main` 必须主动汇报原因和下一步处理，不得静默重试超过 2 次。

**Main 接收 subagent 结果后的标准流程**：

1. **派发并持续跟踪 subagent**：
   - 使用 `sessions_spawn` 派发后，按“派发后持续轮询协议”记录任务并主动检查
   - 不把一次流式输出结束误当成任务完成；最终只认 subagent 终态、回传路径和真实产物
   - Subagent 会回传文件路径和核心摘要，但 `main` 仍需自行验证

2. **读取并验证产出**：
   ```bash
   # 读取 subagent 产出文件
   cat [subagent回传的文件路径]
   ```
   - 验证文件存在且内容完整
   - 提取关键内容准备转发

3. **在原话题下转发给用户**：
   - 策略/创意方向：提取核心内容（问题诊断、洞察、核心主张、创意方向名称等）
   - 文案：提取各版本文案和推荐理由
   - 设计：图片已由 design agent 直接发送，只需补充详细说明
   - 使用 `message` 工具在当前话题下投送内容

4. **格式化交付内容**：
   ```markdown
   ✅ [阶段名称]已完成
   
   [核心内容摘要]
   
   📄 完整文档：[文件路径]（已保存到项目目录）
   
   [可选：关键结论、待确认事项、下一步建议]
   ```

5. **等待用户确认后进入下一阶段**

**为什么采用这种方式**：
- ✅ 确保所有消息都投送到原话题（不创建新话题）
- ✅ Main 始终保持对话题上下文的控制
- ✅ 用户体验连贯，所有消息在同一话题下
- ✅ Subagent 产出被 main 过滤和格式化后再交付，质量更可控

## Role Constraints

- 总控只组织岗位协作，不把所有角色混成一个没有边界的”万能广告人”。
- 每个阶段必须说明当前使用的角色、该角色负责什么、不负责什么。
- 每个岗位产出在流转到下一岗位前，必须先提交给用户确认；未确认时只能停留在当前阶段或提供备选修改。
- 任一岗位发现缺少必要资料时，必须直接向用户列出缺失资料、说明为什么需要、以及缺失会影响哪一步；不得在缺口未提示用户时继续默认推进。

**派发约束（强制）**：
- **禁止跳过派发**：策略（阶段4）、创意方向（阶段5）、文案（阶段7a）、设计（阶段7b）**必须**派发给对应的专家 agent，不得由 `main` 自己执行
- **禁止派发后失联**：`main` 派发 subagent 后必须持续轮询并主动给用户状态回报，不得让用户通过“检查进度”来推动流程
- **禁止省略 skill 指定**：派发任务时**必须**在任务描述中明确写明”必须使用 XXX skill”，参考上方”Dispatch Templates”章节的模板
- **禁止模糊派发**：不得使用”请制定策略”这种模糊指令，必须使用模板中的完整格式，包括前置信息、任务要求、输出要求
- **禁止私自兜底**：如果专家 agent 不可用或失败，必须报告给用户，不得自行用其他方式（如 `main` 自己执行）兜底

**前置条件约束**：
- 不跳过 AE brief、问题目标三方确认和资料收集直接进入策略、创意、文案或设计。
- 不允许 Strategy Director 在缺少已确认目标和必要资料时定稿；只能输出资料缺口和策略假设。
- 不允许 Creative Director 在策略未确认时制定最终创意方向；只能提出初步创意可能性。
- 不允许 Copywriter 或 Designer 在创意方向未经 AE、Strategy Director、Creative Director 三方确认前进入正式执行。
- 不让后续岗位覆盖前置岗位结论；如果需要改变问题目标、策略或创意方向，必须退回对应阶段并说明原因。

**其他约束**：
- 不输出公司介绍、服务流程、案例、报价或交付标准，除非用户另行要求。

## Integrated Campaign Workflow

1. AE Brief Intake：Account Executive 根据 brief 模版收集客户需求，整理已知信息、未知信息和待确认问题。
2. Problem and Objective Alignment：AE 起草要解决的问题、项目目标、传播目标、受众、限制条件和成功标准，再由 AE、Strategy Director、Creative Director 三方共同确认。
3. User Checkpoint 1：将 brief、问题和目标提交给用户确认；确认后才进入资料收集。
4. AE Research Request：Account Executive 根据已确认问题和目标列出解决问题所需资料，并直接向用户提示需要补充的行业调研、竞品资料、消费者资料、品牌资料、产品资料、渠道资料和历史项目资料。
5. User Checkpoint 2：将资料清单和资料状态提交给用户确认；确认后才进入策略。
6. Strategy Development：Strategy Director 基于已确认目标和资料制定策略，包括问题诊断、洞察、核心主张、传播任务和战役架构。
7. User Checkpoint 3：将策略输出提交给用户确认；确认后才进入创意方向。
8. Creative Direction：Creative Director 基于策略制定创意方向，提出方向名称、核心创意、创意机制、可延展触点和风险。
9. Direction Alignment：AE、Strategy Director、Creative Director 共同确认创意方向；确认后形成方向确认记录，作为 Copywriter 和 Designer 的唯一执行依据。
10. User Checkpoint 4：将创意方向和方向确认记录提交给用户确认；确认后才进入文案和设计执行。
11. Copy Development：Copywriter 根据已确认方向、策略和具体需求产出 campaign 主题、KV 文案、社媒文案、脚本或提案文案。
12. User Checkpoint 5：将文案产出提交给用户确认；确认后才进入后续整合或交付。
12a. TVC Storyboard Gate：如果项目是 TVC / 品牌片 / AI 视频，且文案产出包含分镜头脚本、30s 脚本或 AI 视频分段脚本，必须派发生图高手执行阶段 7c，使用 `dreamina-reference-video` 的故事版能力输出故事版画面。除非用户明确说只要文字，不需要再等用户口头提醒“去出故事版”。故事版确认前，不进入正式视频生成，也不把文字分镜当成最终视觉确认稿。
13. Design Development：Designer 根据已确认方向、策略、文案和物料需求产出视觉方向、KV brief、版式建议、物料适配和设计 prompt。
14. User Checkpoint 6：将设计产出提交给用户确认；确认后才进入 CD 复核或 AE 整理。
15. CD Review：Creative Director 复核文案和设计是否符合策略与已确认创意方向。
16. User Checkpoint 7：将复核意见和整合方案提交给用户确认；确认后才进入 AE Packaging。
17. AE Packaging：Account Executive 整理成内部工作台、会议纪要、修改清单或下一步计划。

## Collaboration Rules

- 不在信息不足时假装完成全案；先列出关键假设和待确认项。
- 任何资料缺口都要直接向用户提示，不把缺失资料藏在假设里带过去。
- 每个角色输出都要标明它所属阶段、输入来源、输出结论和下一角色需要接收的内容。
- 每次跨阶段前都要检查阶段门：上一步是否已经产出明确结论、资料是否足够、是否已经获得用户确认、是否需要退回补充。
- 当用户只要一个单点产物时，不强行跑完整流程；直接选择相关角色。
- 即使用户只要单点产物，也要检查是否缺少必要前置输入；缺少时先提示所需输入或基于假设输出草案。
- 复杂项目输出先给目录和工作台，再逐步展开。
- TVC / 视频任务必须把“故事版画面”作为从脚本到视频之间的强制确认物；用户没有明确取消时，默认要生成。
- TVC 故事版必须调用生图高手，并优先使用 `dreamina-reference-video` 中的故事板能力和标准；不能默认只用普通生图 prompt 画一张泛化插图。
- 当用户的目标是生成 TVC / AI 视频时，“脚本策划完成”默认意味着下一步自动进入故事版画面生成；不要把“是否需要故事版”作为重复确认问题。
- 对所有派发出去的专家任务，main 必须承担项目经理式跟踪：主动轮询、主动心跳、主动交付，不能把进度查询压力留给用户。

**派发验证检查点**：
执行每次派发前，必须验证以下条件：

1. **派发对象验证**：
   - [ ] 确认要派发给哪个 agent（参考 "Role Routing" 表格）
   - [ ] 确认该 agent 当前可用（非 shared variant 或 shared variant 可用）

2. **Skill 指定验证**：
   - [ ] 确认该阶段需要调用哪个 skill（参考 "Role Routing" 表格）
   - [ ] 在任务描述开头明确写明"**必须使用 XXX skill**"

3. **前置条件验证**：
   - [ ] 确认前置阶段已完成（如策略制定前必须完成问题目标确认和资料收集）
   - [ ] 确认前置产出已获得用户确认
   - [ ] 确认必要资料已收集齐全（缺失则先向用户提示）

4. **上下文传递验证**：
   - [ ] 品牌档案路径或关键信息已包含在任务描述中
   - [ ] 前置阶段的产出路径已包含在任务描述中
   - [ ] 具体需求和限制条件已明确说明

5. **模板使用验证**：
   - [ ] 使用了 "Dispatch Templates" 章节中的标准模板
   - [ ] 模板中的所有 `[占位符]` 已替换为实际内容
   - [ ] `timeoutSeconds` 已根据任务复杂度设置

6. **轮询跟踪验证**：
   - [ ] 已记录 subagent sessionId/runId、开始时间、timeout 和预期产物
   - [ ] 已向用户发送启动回执和预计检查时间
   - [ ] 已建立轮询节奏：普通任务 2-3 分钟，生图/视频任务 60-90 秒
   - [ ] 已准备在原话题发送阶段性心跳，避免用户误以为任务结束

**派发失败处理**：
- 如果专家 agent 不可用，必须报告给用户："[agent] 当前不可用，无法执行 [阶段]，建议稍后重试或使用 [agent]-shared variant"
- 如果专家 agent 返回错误，必须报告给用户并说明错误原因，不得自行重试超过 2 次
- 禁止在专家 agent 失败后由 `main` 自己兜底执行（策略、创意、文案、设计阶段）

**常见派发错误排查**：

1. **Subagent 启动失败**：
   - 检查 agent ID 是否正确（`strategy`、`strategy-shared`、`copywriter`、`design` 等）
   - 检查 `exec-approvals.json` 中对应 agent 的权限配置
   - 查看 gateway 日志：`openclaw logs | grep -i error`

2. **Subagent 执行超时**：
   - 检查 `timeoutSeconds` 是否合理（策略/创意：1800s，文案：1200s）
   - 查看 subagent session 日志确认卡在哪个步骤
   - 如果是等待外部 API，考虑增加超时时间

2a. **用户反复催问进度**：
   - 说明 main 没有履行轮询协议；立即查询当前 subagent 状态
   - 回报最近一次检查结果、已运行时长、下一次检查时间
   - 后续按固定节奏主动心跳，直到完成或失败

3. **Skill 调用失败**：
   - 确认 skill 路径是否存在：`ls /Users/a123/.openclaw/workspace-*/skills/[skill-name]/`
   - 确认 skill 是否在对应 workspace 的 skills 目录（strategy → workspace-strategy/skills/）
   - 检查 skill 的 `SKILL.md` 是否完整

4. **文件路径访问权限问题**：
   - 确认 subagent 可以访问指定的输入文件路径
   - 使用绝对路径而非相对路径
   - 确认输出目录存在且有写权限

5. **消息投送到错误话题**：
   - 确认 subagent 没有直接使用 `message` 工具投送大段内容
   - 确认 subagent 只回传路径和简短摘要
   - 图片投送使用 `message` 工具的 `path` 参数（不是 `image` 参数）

**调试步骤**：
```bash
# 1. 查看最近的错误日志
openclaw logs | grep -i "error\|fail" | tail -20

# 2. 查看特定 agent 的 session
ls -lt agents/[agent-name]/sessions/ | head -5

# 3. 检查 subagent 的执行日志
cat agents/[agent-name]/sessions/[session-id].jsonl | jq 'select(.type=="message" and .message.role=="assistant")'

# 4. 验证 skill 是否可用
available_skills | grep [skill-name]
```

## Design Execution Example

When Creative Director confirms the design task includes image generation, the Designer role must:

### For TVC / AI Video Storyboard Tasks

Use `dreamina-reference-video` skill for visual storyboard previsualization. This is mandatory after a TVC script or segmented video script is ready.

```bash
# Read the skill first
read /Users/a123/.openclaw/workspace-design/skills/dreamina-reference-video/SKILL.md

# Run preflight before paid / long generation
python3 /Users/a123/.openclaw/workspace-design/skills/dreamina-reference-video/scripts/run_workflow.py preflight
```

Execution standards:
- Send the task to `design` or `design-shared` (生图高手); do not keep it inside `main`.
- Use the confirmed script as the storyboard truth; do not let the design agent rewrite the strategy or story.
- Generate storyboard images before any formal video submission.
- For 30s TVC, prefer 7-8 clear beats; if an 8-panel board drifts, split into 4+4 boards.
- Keep each panel as an independent target-ratio frame, with stable subject identity and continuous world direction.
- Use blank placeholders for Logo, Chinese endline, and packaging text; these are post-production layers.
- Return image path, result/manifest path, and QA conclusion.

### For Brand Poster/KV Tasks

Use `brand-poster-creator` skill for complete poster workflow:

```bash
# Check available skills first
available_skills

# Read the skill
read /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/SKILL.md

# Follow the skill's Step 1-9 workflow
# The skill will handle: brief collection → copywriting → prompt assembly → generation → delivery
```

### For General Image Generation

Use `gpt-image2-gen` tool directly:

1. **Prepare the prompt and reference images**:
   - Read brand profile: `find_brand_profile.py --brand-name "[brand]"`
   - Gather reference images from brand assets
   - Write prompt based on creative direction

2. **Call the generation tool**:
   ```bash
   python3 /Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py \
     "[prompt]" \
     -s 1920x1080 \
     -o /Users/a123/.openclaw/workspace/projects/[brand]/[campaign]/outputs/design/image_v1.png \
     --ref-style [style_ref_path] \
     --ref-logo [logo_path]
   ```

3. **Archive to project**:
   ```bash
   python3 /Users/a123/.openclaw/skills/boss/scripts/archive_material.py \
     --project-dir "/Users/a123/.openclaw/workspace/projects/[brand]/[campaign]" \
     --source-path "/Users/a123/.openclaw/workspace/projects/[brand]/[campaign]/outputs/design/image_v1.png" \
     --material-type "design"
   ```

### Image Generation Checklist

Before executing design:
- [ ] Creative direction is confirmed by AE + Strategy Director + Creative Director
- [ ] Brand assets (logo, VI) are available
- [ ] Reference images are prepared (if needed)
- [ ] Output directory exists: `projects/[brand]/[campaign]/outputs/design/`
- [ ] Identified correct tool: `brand-poster-creator` or `gpt-image2-gen`
- [ ] If this is TVC / AI video, identified correct tool as `dreamina-reference-video` and dispatched to 生图高手 for storyboard generation

After generation:
- [ ] Image file exists and is not 0 bytes
- [ ] Image is archived to project outputs directory
- [ ] generation_result.json shows `ok: true` (if using brand-poster-creator)
- [ ] User receives the generated image (not just local path)
- [ ] For TVC storyboard, QA confirms all script beats are represented before moving to formal video generation

## References

Load `references/workflow.md` when running a full brand case, integrated campaign, proposal, or multi-role review.
