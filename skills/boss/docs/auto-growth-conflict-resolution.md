# Boss Skill 项目记忆系统 - 自动增长与冲突处理机制

## 概述

本文档描述 Boss skill 项目记忆系统的**自动增长**和**冲突处理**两大机制，解决品牌档案在项目执行过程中的自动创建、信息积累和一致性维护问题。

## 核心问题

### 问题 1：品牌档案如何自动增长？

**场景**：用户执行海报任务时输入新品牌信息，这些信息是否会自动记录到项目记忆中？

**解决方案**：
- 检测到新品牌时，从任务输入中提取可用信息
- 显式询问用户是否创建品牌档案
- 用户确认后自动创建档案，后续项目可复用

### 问题 2：品牌信息冲突如何处理？

**场景**：用户输入的品牌信息与档案中的记录不一致（如行业变更、视觉规范变化）

**解决方案**：
- 自动检测高/低严重性冲突
- 高严重性冲突暂停任务，用户选择处理方式
- 低严重性冲突自动合并，任务结束后通知用户

## 自动增长机制

### 触发条件

当执行品牌相关任务时，`find_brand_profile.py` 返回 `found: false`，触发自动建档流程。

### 信息提取规则

从任务输入中提取品牌信息的映射规则：

| 来源 | 字段 | 映射到档案 | 优先级 |
|------|------|-----------|--------|
| brief.json | brand_name | brand_name | 1 |
| brief.json | product_category | industry / category | 1 |
| brief.json | target_audience | target_audience | 1 |
| brief.json | core_message | core_values | 1 |
| brief.json | brand_tone | brand_tone | 1 |
| 用户对话 | "XX品牌是做YY的" | industry | 2 |
| 用户对话 | "定位是ZZ" | positioning | 2 |
| 推断 | 产品类型（如"烘焙"） | industry | 3 |

**提取策略**：
- brief.json 明确字段 > 用户对话 > 推断
- 用户明确表述 > 从产品类型推断
- 不确定时留空，不强行推断

### 用户确认流程

提取信息后，**暂停任务**，使用 `AskUserQuestion` 工具展示确认界面：

```markdown
🆕 检测到新品牌"XX"，是否创建品牌档案？

当前已知信息：
- 品牌名称：XX
- 行业/品类：[提取的信息]
- 目标受众：[提取的信息]
- 核心价值观：[提取的信息]

创建品牌档案的好处：
✅ 后续项目可复用品牌信息（视觉规范、品牌调性、素材路径）
✅ 确保品牌输出物的一致性
✅ 减少重复填写信息的工作量

选项：
1. **创建档案并继续**（推荐：适合长期合作品牌）
2. **仅本次使用，不建档**（适合一次性项目或测试）
```

### 创建档案

用户选择"创建档案并继续"时，调用 `init_agency_project.py`：

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/init_agency_project.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --campaign-name "项目名_$(date +%Y%m%d)" \
  --industry "行业" \
  --target-audience "目标受众" \
  --core-values "价值观1,价值观2"
```

**创建后**：
- 档案位置：`/Users/a123/.openclaw/workspace/projects/品牌名/_brand-profile.json`
- 任务继续执行，使用新创建的档案
- 后续相同品牌任务自动复用档案

## 冲突处理机制

### 冲突类型与严重性

| 冲突类型 | 字段 | 严重性 | 处理方式 |
|---------|------|--------|----------|
| **品牌基础信息** | industry | 高 | 暂停任务，用户选择 |
| **品牌定位** | positioning | 高 | 暂停任务，用户选择 |
| **视觉规范** | vi_guidelines.primary_colors | 高 | 暂停任务，用户选择 |
| **视觉规范** | vi_guidelines.fonts | 高 | 暂停任务，用户选择 |
| **品牌调性** | brand_tone | 高 | 暂停任务，用户选择 |
| **核心价值观扩展** | core_values (append) | 低 | 自动合并，任务后通知 |
| **竞品补充** | competitors (append) | 低 | 自动合并，任务后通知 |
| **目标受众扩展** | target_audience (扩展) | 低 | 自动合并，任务后通知 |

### 冲突检测

执行任务前，调用 `detect_brand_conflicts.py`：

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/detect_brand_conflicts.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --new-info '{"industry":"餐饮","target_audience":"新受众"}'
```

**返回格式**：

```json
{
  "has_conflict": true,
  "conflicts": [
    {
      "field": "industry",
      "archived": "烘焙",
      "new_input": "餐饮",
      "severity": "high"
    }
  ],
  "supplements": [
    {
      "field": "core_values",
      "archived": ["新鲜手作"],
      "new_input": ["新鲜手作", "用心品质"]
    }
  ]
}
```

### 高严重性冲突处理

**暂停任务**，使用 `AskUserQuestion` 展示冲突：

```markdown
⚠️ 品牌信息冲突检测

字段：行业
档案记录：烘焙
当前输入：餐饮

如何处理？
1. **使用档案记录**（烘焙）- 保持品牌一致性
2. **更新档案为新信息**（餐饮）- 档案可能过时
3. **仅本次使用新信息，不更新档案** - 临时偏差
```

**用户选择后**：

**选项 1：使用档案记录**
- 使用档案中的值继续执行
- 不更新档案

**选项 2：更新档案为新信息**
```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --field "industry" \
  --value "餐饮" \
  --operation replace
```

**选项 3：仅本次使用新信息**
- 使用新值继续执行
- 不更新档案

### 低严重性冲突处理

**自动合并**，不暂停任务：

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --field "core_values" \
  --value '["用心品质"]' \
  --operation append
```

**任务结束后**，向用户通知补充信息：

```markdown
✅ 已补充品牌档案：
- 核心价值观：新增"用心品质"、"匠心传承"
- 竞品：新增"品牌A"、"品牌B"
```

### 特殊情况处理

#### 视觉规范冲突

**严重性**：高

**原因**：影响所有设计输出物，可能是品牌升级

**处理**：
- 必须用户确认
- 在 audit_log 中记录决策原因
- 如选择"更新档案"，记录为品牌视觉升级

**示例**：

```markdown
⚠️ 品牌视觉规范冲突

字段：主色
档案记录：#FF6B6B（红色系）
当前输入：#0000FF（蓝色系）

视觉规范变更会影响所有品牌输出物，建议确认是否为品牌升级。

如何处理？
1. 使用档案记录（红色系）
2. 更新档案为新信息（蓝色系）- 确认品牌视觉升级
3. 仅本次使用新信息，不更新档案
```

#### 品牌调性冲突

**严重性**：高

**原因**：影响文案风格和创意方向

**处理**：
- 必须用户确认
- 可能需要回溯已确认的创意方向

#### 目标受众扩展

**严重性**：低

**原因**：扩展而非替换（如从"25-35岁"扩展到"25-45岁"）

**处理**：
- 自动合并
- 不需要用户确认

## CLI 脚本使用

### 检测冲突

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/detect_brand_conflicts.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --new-info '{"industry":"新行业","core_values":["新价值观"]}'
```

### 更新档案（replace 操作）

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --field "industry" \
  --value "新行业" \
  --operation replace
```

### 更新档案（append 操作）

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --field "core_values" \
  --value '["新价值观"]' \
  --operation append
```

### 更新嵌套字段

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --field "vi_guidelines.primary_colors" \
  --value '["#FF0000"]' \
  --operation replace
```

## 集成点

### brand-poster-creator skill

**位置**：Step 2.4 品牌档案查询

**流程**：
1. 查询品牌档案
2. 若未找到，提取信息并询问是否建档
3. 若找到，检测冲突
4. 高严重性冲突：暂停任务，用户选择
5. 低严重性冲突：自动合并
6. 继续执行 Step 2.5

### Agent AGENTS.md

所有 5 个 agent（main、design、strategy、copywriter、research）都已集成：

- **main**：1.0.6 品牌档案自动增长与冲突处理
- **design**：1.2.5 品牌档案自动增长与冲突处理
- **strategy**：0.05.4 品牌档案自动增长与冲突处理
- **copywriter**：1.0.4 品牌档案自动增长与冲突处理
- **research**：1.0.3 品牌档案自动增长与冲突处理

### Agent 特定注意事项

- **main agent**：负责协调建档决策，传递品牌上下文给下游 agent
- **design agent**：视觉规范冲突必须暂停，不可自行决定使用哪个色彩方案
- **copywriter agent**：品牌调性冲突必须暂停，不可自行决定使用哪种语气
- **strategy agent**：品牌定位冲突必须暂停，不可自行调整定位方向
- **research agent**：竞品信息补充可自动合并，无需暂停

## 故障排查

### 问题：冲突检测未触发

**可能原因**：
- 新信息字段为空或 null
- 新信息与档案完全一致
- 脚本未正确调用

**排查步骤**：
1. 检查 `detect_brand_conflicts.py` 输入参数
2. 验证 `--new-info` 参数是有效 JSON
3. 检查档案是否存在：`find_brand_profile.py`

### 问题：自动合并未生效

**可能原因**：
- `operation` 参数错误（应为 `append`）
- `value` 参数格式错误（list 字段需 JSON 数组）
- 档案文件权限问题

**排查步骤**：
1. 检查 `update_brand_profile.py` 返回的 JSON
2. 验证档案文件 `updated_at` 字段是否更新
3. 直接读取档案文件确认字段值

### 问题：用户确认界面未显示

**可能原因**：
- 未使用 `AskUserQuestion` 工具
- 工具参数格式错误

**排查步骤**：
1. 检查代码中是否调用 `AskUserQuestion`
2. 验证 `questions` 参数格式
3. 查看 agent 执行日志

## 向后兼容性

- 所有新功能都是**可选**的
- 用户可选择"仅本次使用，不建档"
- 档案未建档时系统仍能正常工作
- 不影响现有的查询流程

## 版本历史

- **v1.0**（2026-06-11）：初始版本，实现自动增长和冲突处理机制
- 新增脚本：`detect_brand_conflicts.py`、`update_brand_profile.py`
- 更新模块：`agency_project/project.py` 新增 `detect_conflicts()` 和 `update_brand_profile_field()` 函数
- 集成 agent：5 个 agent 的 AGENTS.md 全部更新
- 集成 skill：brand-poster-creator Step 2.4 增强

## 相关文档

- Boss Skill 总览：`/Users/a123/.openclaw/skills/boss/SKILL.md`
- 品牌档案 Schema：`agency_project/schemas.py` 中的 `build_brand_profile()`
- Agent 执行规则：各 workspace 的 `AGENTS.md`
- Brand Poster Creator Skill：`/Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/SKILL.md`
