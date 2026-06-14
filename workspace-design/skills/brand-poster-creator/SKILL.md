---
name: brand-poster-creator
version: 3.1
description: "品牌海报全流程生成技能（含项目分级与审批流）。从需求收集、版式锁定、文案策划、生图到交付清理的全链路协调器，支持 B/A/S 三级项目管理、自动审批提醒、时间记录与复盘分析。触发词：品牌海报、海报生成、做张海报、节日海报、产品海报、春节海报、营销海报"
metadata:
  openclaw:
    requires:
      bins:
        - python3
    emoji: "🎨"
    streaming: false
---

# Brand Poster Creator - 品牌海报全流程协调器

⚠️ **本 Skill 已结构化拆分，执行时必须按需读取对应的详细文档。**

用于 `main` 子代理统一调度品牌海报从需求到交付的全流程。

---

## 触发词

用户说出以下任意内容时激活本技能：
- 品牌海报 / 海报生成 / 做张海报
- 节日海报 / 春节海报 / 中秋海报等
- 产品海报 / 产品 KV
- 营销海报 / 推广海报

---

## 🚀 执行流程概要

```
Step 0: 项目分级 → Step 1: 需求收集 → Step 2: 品牌档案 → Step 3: 蒸馏卡检查
     ↓                  ↓                  ↓                  ↓
Step 4: 文案策划 → Step 5: 文案审批 → Step 6: 创意方向 → Step 7: 生图
     ↓                  ↓                  ↓                  ↓
Step 8: 设计审批 → Step 9: 高级审批(A/S级) → Step 10: 交付 → Step 11: 清理
```

### Step 0：项目分级（⚠️ 必须先执行）

**详细文档**：`{baseDir}/references/step-0-project-grading.md`

1. 询问项目等级（B/A/S）
2. 根据等级收集审批者信息
3. 使用 `feishu_search_user` 查询 open_id
4. 初始化项目分级配置

**执行前必读**：
```bash
read {baseDir}/references/step-0-project-grading.md
```

---

### Step 1：需求收集

**详细文档**：`{baseDir}/references/step-1-intake.md`

飞书对话卡片收集品牌名称、海报目的、尺寸、必露元素等信息。

---

### Step 2：品牌档案查询

**详细文档**：`{baseDir}/references/step-2-brand-query.md`

查询品牌档案和品牌资产，提取品牌调性、定位、目标受众、Logo、VI 手册。

---

### Step 3：检查蒸馏卡

**详细文档**：`{baseDir}/references/step-3-distill-card.md`

检查是否有蒸馏卡 ID，有则读取版式坐标，无则标记降级模式。

---

### Step 4：文案策划

**详细文档**：`{baseDir}/references/step-4-copywriting.md`

派发 strategy → copywriter subagents，完成文案策略与具体文案。

---

### Step 5：文案审批（⚠️ 审批节点）

**详细文档**：`{baseDir}/references/step-5-copywriting-approval.md`

**执行前必读**：
```bash
read {baseDir}/references/step-5-copywriting-approval.md
```

⚠️ **重要**：审批请求必须使用脚本返回的真实飞书艾特标签，不要手写 `@用户名`。

1. 展示文案给用户
2. 请求文案审批（使用脚本返回的 `.message` 字段中的艾特标签）
3. 记录审批响应和时间
4. 通过后进入 Step 6

---

### Step 6：创意方向确认（⚠️ 审批节点 - 新增 v3.1）

**详细文档**：`{baseDir}/references/step-6-creative-direction.md`

**执行前必读**：
```bash
read {baseDir}/references/step-6-creative-direction.md
```

🔴 **强制格式要求**：使用普通消息（非流式输出）+ Markdown 表格

**实际发送示例**（直接发送，不要放在代码块内）：

<at user_id="ou_xxx">肖宁劼</at> <at user_id="ou_yyy">林育丰</at> 创意方向已生成，请审核确认

| 维度 | 内容 |
|------|------|
| 这张海报想表达 | [summary，一句话] |
| 场景概念 | [scene_concept，简短] |
| 视觉主体 | [hero_focus，简短] |
| 必须打中 | [must_hit，逗号分隔] |
| 必须避免 | [must_avoid，逗号分隔] |

请回复：
- 「通过」→ 进入生图阶段
- 「修改：具体要求」→ 调整创意方向
- 「拒绝：原因」→ 终止项目

⚠️ **关键要点**：
- **直接发送上述格式**（不要使用代码块，不要使用流式输出）
- 使用 Markdown 表格（前端渲染美观）
- 艾特标签使用脚本返回的 message 字段

🔴 **严格禁止**：
- ❌ 使用流式输出（会变成卡片，艾特失效）
- ❌ 在艾特前添加说明文字（如"✅ 文案已确认..."）
- ❌ 使用代码块包裹消息

---

### Step 7：生图

**详细文档**：`{baseDir}/references/step-7-generation.md`

组装 prompt，派发 design subagent 生图。

---

### Step 8：设计审批（⚠️ 审批节点）

**详细文档**：`{baseDir}/references/step-8-design-approval.md`

**执行前必读**：
```bash
read {baseDir}/references/step-8-design-approval.md
```

⚠️ **重要**：审批请求必须使用脚本返回的真实飞书艾特标签，不要手写 `@用户名`。

1. 发送成品图给用户
2. 请求设计审批（使用脚本返回的 `.message` 字段中的艾特标签）
3. 记录审批响应和时间
4. 根据项目等级决定下一步：
   - B级：通过后直接进入 Step 10 交付
   - A/S级：进入 Step 9 高级审批

---

### Step 9：高级审批（仅 A/S 级项目）

**详细文档**：`{baseDir}/references/step-9-advanced-approval.md`

**执行前必读**：
```bash
read {baseDir}/references/step-9-advanced-approval.md
```

⚠️ **重要**：审批请求必须使用脚本返回的真实飞书艾特标签，不要手写 `@用户名`。

- A级项目：创意总监审批
- S级项目：创意总监审批 + 老板最终决策

---

### Step 10：交付

**详细文档**：`{baseDir}/references/step-10-delivery.md`

发送成品图，生成复盘报告。

---

### Step 11：清理

**详细文档**：`{baseDir}/references/step-11-cleanup.md`

询问用户是否清理项目中间文件。

---

## ⚠️ 执行规则（严格遵守）

### 1. 流程顺序

**必须按顺序执行：Step 0 → 1 → 2 → ... → 11**

- ❌ **不要跳过 Step 0 项目分级**
- ❌ **不要直接进入文案或设计阶段**
- ❌ **不要假设"测试项目可以跳过审批"**
- ✅ 每个步骤执行前，先读取对应的详细文档

### 2. 审批节点

**审批节点必须等待，不要自动假设通过。**

- ❌ **不要说"假设审批通过，我们继续"**
- ❌ **不要跳过艾特审批者的步骤**
- ❌ **不要发送图片后只说"请看图确认"而不触发审批流程**
- ❌ **不要把艾特标签单独放在第一行，前面必须有标题**
- ✅ 必须等待审批者明确回复"通过"
- ✅ 记录审批响应时间
- ✅ **发送成品图后立即触发设计审批（Step 8.6），不要等用户说"确认定稿"**

**特别提醒 - 艾特标签格式**：
- ❌ 错误：`<at user_id="...">xxx</at> 创意方向确认`（光秃秃的艾特，飞书无法解析）
- ✅ 正确：`🎬 **标题**\n\n<at user_id="...">xxx</at> 创意方向确认`（有标题）
- Step 6 创意方向：必须按照 step-6 文档的强制格式，标题 → 艾特 → 说明 → 内容
- Step 8 设计审批：发送图片后立即调用 `project_grading.py request --milestone design`
- 使用脚本返回的真实艾特标签，不要手写 `@用户名`

**Step 6 创意方向强制格式（必须遵守）**：
```markdown
🎬 **创意方向双审**

<at user_id="ou_xxx">肖宁劼</at> <at user_id="ou_yyy">林育丰</at> <at user_id="ou_zzz">涂是淦</at> 创意方向已生成，请审核确认

**审核说明**：需要文案策划判断者和设计判断者双方都确认，或AI驱动者确认。

---

**这张海报想表达**：[summary]
**画面呈现**：[详细展示]
**必须打中**：[must_hit]
**必须避免**：[must_avoid]

---

请回复：
- 「通过」→ 创意方向审批通过，进入生图阶段
- 「修改：具体要求」→ 调整创意方向
- 「拒绝：原因」→ 终止项目
```

### 3. 生图入口

**不要绕过 `execute_generation.py` 直接调用 `gpt-image2-gen`。**

- ❌ **不要手写、追加、拼接或临场改 `prompt_draft.md`**
- ❌ **不要用 Python/PIL/ImageMagick/本地贴图顶替正式海报**
- ✅ 先固化 `prompt_draft.md`、`ref_order.json`、`run.sh`
- ✅ 再执行 `execute_generation.py`

### 4. 交付规则

**不要回复本地路径或 `MEDIA:` 文本冒充发送。**

- ❌ **不要回复 `MEDIA:`、本地路径或"图片在目录里"**
- ❌ **不要只返回文件路径就说"已发送"**
- ✅ 调用真实飞书图片发送工具（`message` 工具的 `path` 参数）
- ✅ 等待返回 `messageId` 和 `chatId`
- ✅ 记录交付证据到 `delivery_manifest.json`

### 5. 清理规则

**不要未确认就清理项目。**

- ❌ **不要未确认就清理项目**
- ❌ **不要直接用 `rm` 命令删除**
- ✅ 用户确认后运行 `cleanup_project.py --confirmed`
- ✅ 使用 `trash` 命令代替 `rm`

---

## 🔴 反例黑名单速查

以下动作一律不要做；命中任一项时停下，回到对应步骤修正。

| 场景 | 不要做 | 正确动作 |
|------|--------|----------|
| 素材角色 | 不要把风格参考图、Logo、IP、产品图混成普通参考图 | 写入 `brief.json.assets`，由 `assemble_prompt.py` 生成 `ref_order.json` |
| 风格参考 | 不要继承参考图中的非品牌人物、服装、脸型、身份或原剧情 | 只提炼画风、色彩、光感、动势，并写入 `content_do_not_inherit` |
| Logo/IP | 不要只在 prompt 里写"保留 Logo/IP"就直接生图 | `ref_order.json` 必须包含匹配路径的 `logo` / `ip` 角色 |
| Prompt | 不要手写、追加、拼接或临场改 `prompt_draft.md` | 只运行 `assemble_prompt.py`，失败就修脚本或素材数据 |
| 生图入口 | 不要绕过 `execute_generation.py` 直接调用 `gpt-image2-gen` | 先固化 `prompt_draft.md`、`ref_order.json`、`run.sh`，再执行正式入口 |
| 正式失败 | 不要用 Python/PIL/ImageMagick/本地贴图顶替正式海报 | 记录失败事实，修复 provider/权限/路径后重试 |
| 交付 | 不要回复 `MEDIA:`、本地路径或"图片在目录里"冒充发送 | 调用真实飞书图片发送工具，并记录 `messageId/chatId` |
| 创意方向审批 | 不要展示创意方向后不触发审批流程 | 立即调用 `project_grading.py request --milestone creative_direction_dual` |
| 设计审批 | 不要发送图片后只说"请看图确认"而不@审批者 | 发送图片后立即调用 `project_grading.py request --milestone design` |
| 审批艾特 | 不要手写 `@用户名` 当作艾特标签 | 使用脚本返回的 `<at user_id="...">` 真实艾特标签 |
| 艾特格式 | 不要把艾特标签单独放第一行（无标题） | 必须：`🎬 **标题**\n\n<at>艾特</at> 说明` 格式 |
| Logo 验收 | 不要把 `ref_order.json` 含 `logo` 当成成品 Logo 正确 | `ref_order.json` 只证明已挂载；交付前必须视觉核验成品中的 Logo 是否接近官方文件 |
| 清理 | 不要未确认就清理项目，也不要直接 `rm` | 用户确认后运行 `cleanup_project.py --confirmed` |

---

## 📖 文档索引

执行某个步骤时，必须先读取对应的详细文档：

| 步骤 | 文档路径 | 何时读取 |
|------|---------|----------|
| Step 0: 项目分级 | `{baseDir}/references/step-0-project-grading.md` | ⚠️ 立项时立即读取 |
| Step 1: 需求收集 | `{baseDir}/references/step-1-intake.md` | 完成分级后读取 |
| Step 2: 品牌档案 | `{baseDir}/references/step-2-brand-query.md` | 收集需求后读取 |
| Step 3: 蒸馏卡检查 | `{baseDir}/references/step-3-distill-card.md` | 查询品牌档案后读取 |
| Step 4: 文案策划 | `{baseDir}/references/step-4-copywriting.md` | 开始文案阶段时读取 |
| Step 5: 文案审批 | `{baseDir}/references/step-5-copywriting-approval.md` | 文案完成后读取 |
| Step 6: 创意方向 | `{baseDir}/references/step-6-creative-direction.md` | 文案审批通过后读取 |
| Step 7: 生图 | `{baseDir}/references/step-7-generation.md` | 创意方向确认后读取 |
| Step 8: 设计审批 | `{baseDir}/references/step-8-design-approval.md` | 生图完成后读取 |
| Step 9: 高级审批 | `{baseDir}/references/step-9-advanced-approval.md` | 设计审批通过后读取（仅 A/S 级） |
| Step 10: 交付 | `{baseDir}/references/step-10-delivery.md` | 所有审批通过后读取 |
| Step 11: 清理 | `{baseDir}/references/step-11-cleanup.md` | 交付完成后读取 |

---

## 🔧 核心脚本

| 功能 | 脚本路径 |
|------|---------|
| 项目分级 | `{baseDir}/scripts/project_grading.py` |
| 时间记录 | `{baseDir}/scripts/time_tracking.py` |
| 审批流程测试 | `{baseDir}/scripts/test_approval_flow.py` |
| Prompt 组装 | `{baseDir}/scripts/assemble_prompt.py` |
| 生图执行 | `{baseDir}/scripts/execute_generation.py` |
| 交付准备 | `{baseDir}/scripts/prepare_feishu_delivery.py` |
| 清理项目 | `{baseDir}/scripts/cleanup_project.py` |

---

## 🗂️ 参考文档

- **数据结构定义**：`{baseDir}/references/data-structures.md`
- **故障排查指南**：`{baseDir}/references/troubleshooting.md`
- **Prompt 组装规范**：`{baseDir}/references/prompt-assembler.md`

---

## 版本历史

- **v3.1**：结构化拆分，主文件精简到 < 400 行，详细流程移至 references/
- **v3.0**：新增项目分级与审批流系统
- **v2.4**：集成品牌记忆系统
