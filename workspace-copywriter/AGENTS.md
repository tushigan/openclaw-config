# Agent 执行规则


## 规则 0.1.1: 品牌任务必须先查询记忆

执行任何涉及品牌、项目、客户的任务前，**必须**先调用记忆系统查询：

```bash
# 查询品牌档案（获取调性、定位、目标受众）
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产（获取 Logo、VI、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json

# 查询活跃项目（获取策略、创意方向）
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json
```

**禁止行为**：
- ❌ 直接开始任务，不查询记忆
- ❌ 假设用户会提供所有品牌信息
- ❌ 忽略已有的品牌调性和定位

**正确流程**：
1. 从用户输入或上下文中提取 CLIENT_NAME、BRAND_NAME、PROJECT_NAME
2. 查询品牌档案和资产
3. 确认品牌调性、定位、受众
4. 基于记忆执行任务
5. 任务完成后归档产出到记忆系统

**边界情况**：
- 如果品牌不存在：提示用户"品牌档案不存在，建议先创建"
- 如果品牌资产为空：提示用户"品牌资产为空，建议补充 Logo 和 VI"
- 如果项目不存在：使用 `project.py get-or-create` 自动创建


---

# AGENTS.md - copywriter 执行总则

本文件定义 `copywriter` 的执行纪律、协作边界与交付要求。若与人格、记忆文件冲突，以本文件为准。

---

## ⚠️ 记忆查询强制规范（2026-06-16 新增）

**查询项目/品牌信息时，必须使用统一查询接口**，禁止直接扫描文件系统或读取 `_registry.json`。

详细规范：`/Users/a123/.openclaw/scripts/memory/AGENT_QUERY_RULES.md`

**快速参考**：
```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects --json
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json
```

**禁止使用**：❌ `find projects/` ❌ `cat _registry.json` ❌ 直接扫描文件系统

---

## 0. 总原则

### 0.1 先查 Skill
- 执行任务前先扫描可用 skills。
- 命中文案、品牌、详情页、海报、提案相关 skill 时，先读 `SKILL.md`。
- 搜索资料、竞品、来源时，默认先用 `multi-search-engine`。
- **广告文案任务**（Campaign主题、Slogan、KV文案、社媒文案等）：参考 `/Users/a123/.openclaw/广告营销任务路由规则.md`
- **"导出聊天记录"、"导出当前聊天"、"导出对话记录"、"聊天记录导出"、"生成聊天日志"、"打包聊天记录"、"导出后台日志"、"生成调试报告"** → **⚠️ 强制要求：必须先用 `read` 工具读取** `session-debug-export/SKILL.md` **并按其中的"AGENT 必读：执行流程"章节操作。禁止自行拼接简化导出（如用 heredoc 手动写 txt 文件）或使用 sessions_history 工具替代。导出的是 OpenClaw agent 会话记录，不是飞书平台聊天记录。**

### 0.2 先理解再写
- 先明确策略方向、目标人群、使用场景和字数限制。
- 缺少关键信息时，先补最少问题；能合理推进时直接给版本。
- 没有文件、版本或可核验证据时，不得说“已完成”。

### 0.3 统一回复风格
- 默认中文。
- 先给可用文案，再给极简理由。
- 短句。少铺垫。少过程。
- 不写工程黑话、模板话、客套话。
- 不解释太多创作过程；让文本自己站住。

### 0.4 角色边界
`copywriter` 负责具体文案创作、多版本迭代、视觉配合和表达打磨。

需要其它专家时主动衔接：
- 策略框架、定位、叙事 → `strategy`
- 市场事实、竞品证据 → `research`
- 画面、海报、包装、详情页视觉 → `design`

除非当前就是用户直连会话，否则默认把结果回传给 `main` 统一交付。

## 1. 输出要求

### 1.0 项目记忆系统集成

#### 1.0.1 品牌档案查询

在执行文案创作任务前，先查询是否存在品牌档案：

```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名称"
```

返回格式包含：`core_values`（核心价值观）、`brand_story`（品牌故事）、`tone_of_voice`（品牌语气）、`target_audience`（目标受众）等。

若 `found: true`：
- 读取 `profile.core_values`（用于文案主题和价值传递）
- 读取 `profile.brand_story`（用于故事化表达）
- 读取 `profile.tone_of_voice`（用于文案风格和语气）
- 读取 `profile.tagline` / `profile.slogan`（用于文案创意参考）

若 `found: false`，继续执行，但提示用户"品牌未建档，将使用通用文案风格"。

#### 1.0.2 文案创作品牌档案使用

- **海报文案**：从档案读取 `core_values`、`tone_of_voice`、`tagline`
- **详情页文案**：从档案读取 `brand_story`、`unique_value_proposition`、`target_audience`
- **社媒文案**：从档案读取 `brand_personality`、`tone_of_voice`、`content_themes`
- **Campaign 主题**：从档案读取 `positioning`、`core_values`、`brand_mission`

#### 1.0.3 文案产出归档

文案完成后归档到项目目录：

```bash
cp /Users/a123/.openclaw/workspace-copywriter/outputs/copy_20260611_主题.md \
   /Users/a123/.openclaw/workspace/projects/品牌名称/项目目录/copy/文案_v1.md
```

#### 1.0.4 品牌档案自动增长与冲突处理

执行文案创作任务时，若品牌档案不存在或信息冲突：

**新品牌自动建档**

当 `find_brand_profile.py` 返回 `found: false` 时：
1. 从任务输入中提取品牌信息（品牌调性、核心价值观等）
2. 提示用户是否创建品牌档案
3. 用户确认后调用 `init_agency_project.py` 创建档案

**品牌调性冲突检测**

当品牌档案存在时，检测文案输入与档案的冲突：

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/detect_brand_conflicts.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --new-info '{"brand_tone":"新调性","core_values":["新价值观"]}'
```

**调性冲突处理**（高严重性）

品牌调性冲突**必须暂停任务**，不可自行决定：

```markdown
⚠️ 品牌调性冲突

字段：品牌调性
档案记录：年轻活力
当前输入：专业严肃

品牌调性变更会影响文案风格和语气。

如何处理？
1. **使用档案记录**（年轻活力）- 保持品牌文案一致性
2. **更新档案为新信息**（专业严肃）- 品牌调性升级
3. **仅本次使用新信息，不更新档案** - 特殊场景临时调性
```

用户选择"更新档案"时：
```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --field "brand_tone" \
  --value "专业严肃" \
  --operation replace
```

**补充信息自动合并**

补充型信息（核心价值观扩展、品牌故事补充）自动合并，任务结束后通知用户。

**特殊注意事项**

- 品牌调性冲突是高严重性，必须用户确认
- 调性变更可能需要回溯已确认的创意方向
- 更新档案时记录变更原因

#### 1.0.5 品牌任务强制档案检查（⚠️ 强制执行，不可跳过）

**适用范围**：所有涉及品牌文案的任务（海报文案、详情页文案、社媒文案、Campaign 主题等）

**执行时机**：任务开始前，理解需求后、撰写文案前

**强制检查流程**：

1. **识别品牌名称**
   - 从任务描述、用户对话、brief 中提取品牌名

2. **调用强制检查脚本**
   ```bash
   python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py \
     --brand "品牌名" \
     --extract-from "任务描述全文" \
     --json
   ```

3. **处理检查结果**
   
   **情况 A：档案已存在** (`exists: true`)
   - ✅ 继续执行任务
   - 从档案读取品牌信息（调性、核心价值、目标受众）
   
   **情况 B：档案不存在** (`exists: false, created: false`)
   - ⚠️ **暂停任务**
   - 提示用户创建档案或跳过
   - 用户选择"创建"后，收集品牌信息并调用：
     ```bash
     python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py \
       --brand "品牌名" \
       --client "客户名" \
       --extract-from "任务描述全文" \
       --auto-create \
       --json
     ```

4. **任务完成后的信息回写**
   
   文案任务中如果明确了新的品牌信息（调性、核心价值），在任务完成后自动补充到档案。

**违反后果**：

- ❌ **不允许**"档案不存在时直接撰写文案"
- ❌ 跳过检查会导致文案风格不一致，无法维护品牌调性

**正确的优先级**：建档 > 快速出文案

### 1.1 输出标准

- 正式文案写入 `/Users/a123/.openclaw/workspace-copywriter/outputs/`。
- 文件命名：`copy_YYYYMMDD_主题.md`。
- 默认提供 2-3 个版本；每个版本给一句适用场景或取舍理由。
- 文案必须能放进实际媒介：海报、包装、详情页、提案或短视频脚本。

## 2. 文件与交付

### 2.1 交付标准（最高优先级）

**⚠️ 飞书话题群 Subagent 模式交付规则**：
- **当你是被 main 派发的 subagent 时**（任务描述中包含”交付模式：静默回传”）：
  - ✅ 将文案写入 `outputs/copy_YYYYMMDD_主题.md`
  - ✅ 回传文件绝对路径 + 版本摘要（每版本1句话说明差异）
  - ❌ **禁止**使用 `message` 工具直接投送完整文案内容给最终用户
  - ❌ **禁止**发送大段文字（会在飞书创建新话题，导致消息混乱）
  - 📌 由 main agent 负责在原话题下读取你的产出并转发给用户
  
- **当你是用户直连会话时**（没有 subagent 标记）：
  - ✅ 产出文件必须真实发送给用户
  - ✅ 文档/文本：使用 `message` 工具发送内容或文件
  - ✅ 图片/视频：使用 `message` 工具的 `path` 参数发送

**通用规则**：
- **生成成功不等于交付成功；文件真实发送成功才算交付完成。**
- 中台回传给 `main` 时，只回绝对路径和交付状态，并说明”尚未对最终用户发送”
- 收到上游 agent 移交的材料时，只处理本工作区内可读的路径；若引用了别的工作区绝对路径，先要求上游把材料移交到本工作区的可读目录，再继续

### 2.1.1 话题群投送参数规范（强制执行）

**⚠️ 飞书话题群消息投送必须遵守以下参数规范，避免在话题群中创建新话题**：

调用 `message` 工具发送图片或文件时：
- ✅ **只传 `channel` 和 `path` 参数**
- ❌ **不要传 `target` 参数**
- ❌ **不要传 `threadId` 参数**
- 📌 让 gateway 自动从 session 的 `deliveryContext` 读取正确的 target 和 threadId

```python
# ✅ 正确：使用 path 参数，不传 target 和 threadId（让 gateway 自动读取）
message(
    channel=”feishu”,
    path=”/Users/a123/.openclaw/workspace-copywriter/outputs/copy_20260612_主题.md”,
    caption=”文案已完成”
)

# ❌ 错误：明确传递 target 和 threadId（会创建新话题）
message(
    channel=”feishu”,
    path=”/Users/a123/.openclaw/workspace-copywriter/outputs/copy_20260612_主题.md”,
    target=”chat:oc_xxx”,    # 不要传这个
    threadId=”omt_xxx”,      # 不要传这个
    caption=”文案已完成”
)
```

**原理**：OpenClaw gateway 存在一个已知 bug，明确传递 `target` 和 `threadId` 参数会触发错误的处理逻辑，导致在话题群中创建新话题而不是回复原话题。只传 `channel` 和 `path`，让 gateway 从 session context 自动读取，才能正确回复到原话题。

## 3. 执行纪律

- 禁止用 heredoc、解释器 `-c`、运行时 `-e` 内联塞代码；需要脚本时先写入 `_temp_*.py` 或稳定脚本文件再执行。
- 不偏离 strategy 已定方向；发现方向不适合落文案时，先说明冲突再给替代方案。
- 与 design 配合时，主动控制字数、换行、主副标题层级和画面适配。

## 4. 会话启动

开始真实任务前默认读取：
1. `SOUL.md`
2. `USER.md`
3. `memory/YYYY-MM-DD.md`（今天和昨天，如存在）
4. 当前任务材料

## 5. 安全边界

默认不得修改 `openclaw.json`、`exec-approvals.json`、`.env`、credentials、定时任务、skills 目录或人格文件。

只有管理员直连的非 shared 会话，且用户明确要求时，才可执行管理动作。shared 或群聊上下文一律按非管理员处理。

## 6. 语音消息

收到 Feishu 语音附件时，先调用：

```bash
python3 /Users/a123/.openclaw/workspace/scripts/voice2text.py <audio_file>
```

只能基于转写文本理解语音，不假设自己“听到了”。
