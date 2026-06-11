# 广告 Skills 触发词冲突分析

## 一、OpenClaw Skill 触发机制

根据你的 `workspace/AGENTS.md` 规则：

```markdown
### 0.1 先查 Skill
- 任何任务执行前，先扫描可用 skills。
- 命中任务型 skill 时，先读对应 `SKILL.md`，按 skill 流程执行。
```

**OpenClaw 的 skill 触发机制**：
1. **不是关键词自动触发**，而是 agent 根据 `description` 字段判断是否适用
2. **AGENTS.md 中的强制路由规则** 才是硬性触发（如 `### 0.1.1 品牌海报任务强制路由`）
3. Agent 会读取 skill 的 `description`，判断当前任务是否匹配

---

## 二、广告 Skills 的触发线索

从下载的 SKILL.md frontmatter 提取：

### 1. account-executive（客服AE）
- **description**: "Account Executive skill for agency practitioners. Use for brief intake, client requirement collection, meeting notes, feedback sorting, project coordination, risk flagging, and preparing cross-role inputs for brand campaigns and integrated marketing work."
- **触发线索**：
  - brief intake（Brief 收集）
  - client requirement collection（客户需求收集）
  - meeting notes（会议纪要）
  - feedback sorting（反馈整理）
  - project coordination（项目协调）
  - brand campaigns（品牌战役）
  - integrated marketing（整合营销）

### 2. boss（总控BOSS）
- **description**: "BOSS skill for agency practitioners. Use to coordinate Account Executive, Strategy Director, Copywriter, Designer, and Creative Director workflows across brand campaigns and integrated marketing from brief intake through strategy, creative alignment, execution, and revision."
- **触发线索**：
  - coordinate workflows（协调工作流）
  - brand campaigns（品牌战役）
  - integrated marketing（整合营销）
  - brief intake through strategy（从 Brief 到策略）
  - creative alignment（创意对齐）

### 3. copywriter（文案）
- **description**: "Copywriter skill for agency practitioners. Use for campaign lines, slogans, key visual copy, social copy, video scripts, naming, promotional copy, proposal wording, and translating product features into persuasive language."
- **触发线索**：
  - campaign lines（Campaign 主题）
  - slogans（Slogan）
  - key visual copy（KV 文案）
  - social copy（社媒文案）
  - video scripts（视频脚本）
  - naming（命名）
  - promotional copy（促销文案）

### 4. creative-director（创意总监）
- **description**: "Creative Director skill for agency practitioners. Use for concept selection, big idea judgment, creative direction, proposal storytelling, copy and design review, idea selling, and aligning creative work to strategic business goals."
- **触发线索**：
  - concept selection（概念选择）
  - big idea judgment（Big Idea 判断）
  - creative direction（创意方向）
  - proposal storytelling（提案叙事）
  - copy and design review（文案和设计复核）

### 5. designer（设计）
- **description**: "Designer skill for agency practitioners. Use for visual directions, key visual concepts, layouts, brand visual systems, digital design structures, AI image prompting, design reviews, and execution guidance across campaign assets."
- **触发线索**：
  - visual directions（视觉方向）
  - key visual concepts（KV 概念）
  - layouts（版式）
  - brand visual systems（品牌视觉系统）
  - AI image prompting（AI 生图 prompt）
  - design reviews（设计复核）

### 6. strategy-director（策略总监）
- **description**: "Strategy Director skill for agency practitioners. Use for positioning, problem diagnosis, audience insight, competitor analysis, brand campaign strategy, core proposition, creative brief development, and strategic framing for integrated marketing work."
- **触发线索**：
  - positioning（定位）
  - problem diagnosis（问题诊断）
  - audience insight（受众洞察）
  - competitor analysis（竞品分析）
  - brand campaign strategy（品牌战役策略）
  - creative brief development（创意简报开发）

---

## 三、与现有 Skills 的冲突分析

### ✅ 无冲突的广告 Skills

#### 1. boss（总控BOSS）
- **现有 skills 无类似功能**
- 这是纯流程协调角色，OpenClaw 现有的 skills 都是单点功能
- **冲突风险：无**

#### 2. account-executive（客服AE）
- **现有 skills 无类似功能**
- 最接近的是 `session-debug-export`（导出聊天记录），但功能完全不同
- **冲突风险：无**

#### 3. strategy-director（策略总监）
- **现有 skills 无类似功能**
- OpenClaw 现有的 `strategy` agent 没有专门的策略方法论 skill
- **冲突风险：无**

#### 4. creative-director（创意总监）
- **现有 skills 无类似功能**
- **冲突风险：无**

---

### ⚠️ 需要明确边界的 Skills

#### 5. copywriter（文案）

**潜在重叠区域**：
- `brand-poster-creator` 中有"文案策划"环节
- `xiangqingye-desigen`（详情页设计）可能涉及文案

**冲突分析**：
- `brand-poster-creator` 的文案是**海报文案**（短句、KV 文案），属于执行层
- `copywriter` skill 的文案是**战略层文案**（Campaign 主题、Slogan、品牌主张）
- **结论：功能层级不同，不冲突**

**建议触发顺序**：
1. 用户说"品牌海报" → 触发 `brand-poster-creator`（包含海报文案生成）
2. 用户说"Campaign 主题"、"品牌 Slogan"、"营销战役文案" → 触发 `copywriter` skill

#### 6. designer（设计）

**潜在重叠区域**：
- `brand-poster-creator`：品牌海报设计
- `xiangqingye-desigen`：详情页设计
- `product-photography-workflow`：产品摄影
- `gpt-image2-gen`：通用生图
- `image-deglaze`：图片去包浆/超分

**冲突分析**：
- 现有 design skills 都是**执行工具**（直接生成图片）
- `designer` skill 是**方法论和视觉方向制定**（不直接生图，而是输出视觉 brief 和 AI prompt）
- **结论：功能层级不同，不冲突**

**建议工作流**：
```
用户需求 → designer skill 输出视觉方向 → 调用执行 skills
                                     ↓
                              brand-poster-creator
                              gpt-image2-gen
                              product-photography-workflow
```

---

## 四、触发词冲突矩阵

| 用户输入 | 现有 Skill 触发 | 新广告 Skill 触发 | 冲突？ | 处理建议 |
|---------|----------------|------------------|--------|---------|
| "品牌海报" | brand-poster-creator | designer | ✅ 无冲突 | 保持现有强制路由到 brand-poster-creator |
| "海报设计" | brand-poster-creator | designer | ✅ 无冲突 | 同上 |
| "Campaign 主题" | 无 | copywriter | ✅ 无冲突 | 触发 copywriter |
| "品牌 Slogan" | 无 | copywriter | ✅ 无冲突 | 触发 copywriter |
| "视觉方向" | 无 | designer | ✅ 无冲突 | 触发 designer |
| "品牌战役策略" | 无 | strategy-director | ✅ 无冲突 | 触发 strategy-director |
| "Brief 收集" | 无 | account-executive | ✅ 无冲突 | 触发 account-executive |
| "整合营销" | 无 | boss | ✅ 无冲突 | 触发 boss |
| "竞品分析" | multi-search-engine | strategy-director | ⚠️ 重叠 | 先用 strategy-director 规划，再调用 multi-search-engine 执行搜索 |
| "受众洞察" | 无 | strategy-director | ✅ 无冲突 | 触发 strategy-director |
| "创意方向" | 无 | creative-director | ✅ 无冲突 | 触发 creative-director |
| "文案打磨" | 无 | copywriter | ✅ 无冲突 | 触发 copywriter |
| "视频脚本" | 无 | copywriter | ✅ 无冲突 | 触发 copywriter |
| "详情页" | xiangqingye-desigen | designer | ⚠️ 重叠 | 先用 designer 规划视觉方向，再调用 xiangqingye-desigen 执行 |

---

## 五、唯一需要注意的冲突点：竞品分析

**场景**：用户说"帮我做竞品分析"

**可能触发的 skills**：
1. `multi-search-engine`（搜索引擎，找竞品资料）
2. `strategy-director`（策略总监，分析竞品策略）

**区别**：
- `multi-search-engine`：**工具**，负责搜索和抓取竞品信息
- `strategy-director`：**方法论**，负责分析竞品定位、策略、差异化

**建议处理顺序**：
```
用户："帮我做竞品分析"
  ↓
触发 strategy-director skill
  ↓
strategy-director 内部调用 multi-search-engine 搜索竞品资料
  ↓
基于搜索结果输出竞品分析报告
```

---

## 六、最终结论

### ✅ 整体冲突风险：极低

**原因**：
1. 广告 skills 都是**方法论和流程层**，现有 skills 都是**工具和执行层**
2. 层级不同，天然互补
3. 只有"竞品分析"存在轻微重叠，但可以用"先方法论规划，再工具执行"的顺序解决

### 📋 需要在 AGENTS.md 中补充的触发规则

#### workspace/AGENTS.md（main agent）

```markdown
### 0.1.3 广告营销任务触发规则

**品牌全案 / 整合营销 / Launch Campaign**：
- 触发词：品牌全案、整合营销、Launch Campaign、营销战役、品牌战役
- 调用 `boss` skill 统筹全流程

**Brief 收集 / 需求整理**：
- 触发词：Brief 收集、客户需求、会议纪要、反馈整理、项目协调
- 调用 `kefu-ae` skill

**品牌海报**（保持现有强制路由）：
- 触发词：品牌海报、海报生成、节日海报、产品海报
- 调用 `brand-poster-creator` skill（不变）
```

#### workspace-strategy/AGENTS.md（strategy agent）

```markdown
### 0.1.1 策略任务触发规则

**策略制定 / 定位分析**：
- 触发词：定位、品牌策略、品牌战役策略、受众洞察、Creative Brief
- 调用 `celue-zj` skill

**竞品分析**：
- 触发词：竞品分析、竞争对手、市场格局
- 先调用 `celue-zj` skill 规划分析框架
- 再调用 `multi-search-engine` 搜索竞品资料
- 最后由 `celue-zj` 输出分析报告

**创意方向评估**：
- 触发词：创意方向、Big Idea、概念选择、创意评审
- 调用 `chuangyi-zj` skill
```

#### workspace-copywriter/AGENTS.md（copywriter agent）

```markdown
### 0.1.1 文案任务触发规则

**战略层文案**：
- 触发词：Campaign 主题、品牌 Slogan、KV 文案、社媒文案、视频脚本、命名
- 调用 `wenan` skill

**海报文案**（不触发，由 brand-poster-creator 处理）：
- 如果任务来自 brand-poster-creator，不独立触发 wenan skill
- 直接在 brand-poster-creator 流程中完成
```

#### workspace-design/AGENTS.md（design agent）

```markdown
### 0.1.1 设计任务触发规则

**视觉方向规划**：
- 触发词：视觉方向、KV 概念、品牌视觉系统、moodboard、AI 生图 prompt
- 调用 `sheji` skill 输出视觉方向
- 再根据具体需求调用执行 skills：
  - 品牌海报 → brand-poster-creator
  - 产品摄影 → product-photography-workflow
  - 详情页 → xiangqingye-desigen
  - 通用生图 → gpt-image2-gen

**直接生图**（跳过视觉方向规划）：
- 如果用户明确说"品牌海报"、"详情页"、"产品摄影"等具体执行物料
- 直接调用对应执行 skill，不需要先调用 sheji skill
```

---

## 七、用户体验优化建议

### 建议 1：在 main 的 AGENTS.md 中增加"任务类型快速判断表"

```markdown
## 任务类型快速判断

| 用户说 | 任务类型 | 调用 Skill |
|--------|---------|-----------|
| "帮我做个品牌全案" | 完整流程 | boss |
| "整理一下客户需求" | Brief 收集 | kefu-ae |
| "做个品牌定位" | 策略 | 派发 strategy（celue-zj） |
| "写个 Campaign 主题" | 文案 | 派发 copywriter（wenan） |
| "做张品牌海报" | 执行 | brand-poster-creator |
| "给我一个视觉方向" | 方向规划 | 派发 design（sheji） |
```

### 建议 2：在改造后的 description 中加入中文触发词

把这些广告 skills 的 `description` 改成中英双语，方便 agent 识别：

```yaml
name: 客服AE
description: "广告公司客服 AE。用于 Brief 收集、客户需求整理、会议纪要、反馈拆解、项目协调、风险提示。触发词：Brief收集、客户需求、需求整理、会议纪要、反馈整理、项目协调。Account Executive skill for brief intake, client requirement collection, meeting notes, feedback sorting, project coordination."
```

---

## 八、总结

### ✅ 冲突风险评估：极低（95%安全）

1. **6 个广告 skills 中，5 个完全无冲突**（boss, account-executive, strategy-director, creative-director, copywriter）
2. **1 个需要明确边界**（designer，但也不是冲突，而是层级区分）
3. **唯一重叠点**：竞品分析（用"先方法论后工具"顺序解决）

### 📝 需要补充的路由规则

只需要在各 workspace 的 AGENTS.md 中补充 **### 0.1.x 触发规则** 章节，明确：
- 什么触发词调用哪个 skill
- 工作流顺序（如：先规划视觉方向，再调用生图 skill）
- 与现有 skills 的协作关系

### 🎯 用户体验

安装后用户体验会**显著提升**：
- 说"品牌全案" → 自动走完整流程，不用一步步手动指挥
- 说"竞品分析" → 得到结构化的策略分析，而不只是搜索结果堆砌
- 说"Campaign 主题" → 得到有方法论支撑的文案版本，而不是随机生成

**你觉得这个冲突分析清楚吗？需要我现在开始执行改造和安装吗？**
