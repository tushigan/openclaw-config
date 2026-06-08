# dreamina-reference-video Skill 优化完成报告

## 优化概述

按照 codex 的优化方案，成功将 `dreamina-reference-video` skill 从"单轮 prompt 生成器"升级为"项目驱动、可验证、可迭代"的视频工作流系统。

## 已完成的功能

### Phase 1: 基础设施（已完成）

#### 1. 项目配置系统（project.json）

**新增文件：** `scripts/state_manager.py`

**核心功能：**
- 项目级配置管理（defaults、constraints、validation_rules、iteration_strategy）
- 自动版本升级（v1 → v2）
- 三层配置继承：skill 默认 → project 默认 → run 级覆盖

**数据结构：**
```json
{
  "schema_version": 2,
  "project_id": "项目标识",
  "project_name": "项目名称",
  "defaults": {
    "ratio": "9:16",
    "duration": 5,
    "quality_tier": "draft"
  },
  "constraints": {
    "must_have": [],
    "must_not_have": [],
    "prefer": []
  },
  "validation_rules": {},
  "iteration_strategy": {
    "max_iterations": 3,
    "max_same_error_repeats": 2,
    "improvement_threshold": 0.15
  },
  "state": {},
  "runs": []
}
```

#### 2. 运行状态系统（run_state.json）

**核心功能：**
- 单轮运行真相源
- 配置快照
- 迭代历史追踪
- 验证报告和风险分析报告存储

**数据结构：**
```json
{
  "schema_version": 1,
  "run_id": "运行标识",
  "project_id": "项目标识",
  "stage": "prepare|generate_refs|submit_video|fetch_result",
  "status": "状态",
  "config_snapshot": {},
  "prompt_files": {},
  "reference_files": {},
  "prompt_risk_report": {},
  "validation_report": {},
  "next_action": {
    "decision": "continue|ask_user|stop",
    "reason": "原因"
  },
  "iterations": []
}
```

#### 3. 配置继承机制

**实现位置：** `workflow.py:normalize_brief()`

**继承顺序：**
1. Skill 默认值（DEFAULTS）
2. 项目级默认值（project.defaults）
3. Run 级覆盖（brief.json）

**示例：**
```python
# 第一次运行：创建项目，设置默认比例为 9:16
brief1 = {"subject": "黄小咕", "ratio": "9:16", ...}

# 第二次运行：自动继承项目默认比例
brief2 = {"subject": "黄小咕", "action": "跳舞"}  # ratio 自动继承为 9:16
```

#### 4. 约束结构化

**实现位置：** `workflow.py:convert_constraints_to_structured()`

**转换规则：**
- `identity_structure` → `must_have` 约束
- `identity_forbidden` → `must_not_have` 约束
- 每个约束包含：id、type、description、strength、applies_to、validation_mode

### Phase 2: 验证和迭代（已完成）

#### 1. 确定性验证器（DeterministicValidator）

**新增文件：** `scripts/validator.py`

**验证规则：**
- **reference_system**: 检查必需文件存在、图片尺寸、prompt 文件完整性
- **storyboard**: 检查故事板文件、比例匹配
- **video**: 检查结果文件、submit_id

**输出：**
- 验证报告（ValidationReport）
- 问题列表（issues）
- 验证分数（score）
- 人工检查清单（manual_checks）

#### 2. 人工检查清单生成器（ManualChecklistGenerator）

**功能：**
- 根据 brief 生成针对性的检查清单
- 分类：style、character、structure、forbidden、format

**示例清单：**
```json
{
  "id": "character_consistency",
  "description": "故事板中的角色是否和 identity-source.png 一致？",
  "category": "character",
  "checked": false
}
```

#### 3. 迭代引擎（IterationEngine）

**新增文件：** `scripts/iteration_engine.py`

**决策逻辑：**
1. 检查人工检查项是否完成 → `ask_user`
2. 检查验证是否通过 → `continue`
3. 检查迭代次数 ≥ max_iterations → `ask_user`
4. 检查相同错误重复次数 ≥ max_same_error_repeats → `ask_user`
5. 检查改进幅度 < improvement_threshold → `ask_user`
6. 检查是否所有错误都可自动重试 → `continue` 或 `ask_user`

**输出：**
```json
{
  "decision": "continue|ask_user|stop",
  "reason": "原因说明",
  "suggested_action": "建议的下一步动作"
}
```

#### 4. 新增 CLI 命令

**validate-run**: 验证运行结果
```bash
python3 scripts/run_workflow.py validate-run \
  --run-dir /path/to/run \
  --stage reference_system
```

**review-run**: 审查运行结果并决定下一步
```bash
python3 scripts/run_workflow.py review-run \
  --run-dir /path/to/run
```

**project-status**: 显示项目状态
```bash
python3 scripts/run_workflow.py project-status \
  --project-dir /path/to/project
```

### Phase 3: 风险分析和优化（已完成）

#### 1. Prompt 风险分析器（PromptRiskAnalyzer）

**新增文件：** `scripts/prompt_risk_analyzer.py`

**检测的风险类型：**

1. **action_body_confusion**: 动作词 + 身体部位混淆
   - 检测模式：`点赞 + 大拇指`、`竖起 + 手指`、`挥手 + 手臂` 等
   - 严重程度：high
   - 建议：将动作词改为形状描述（如"点赞造型"）

2. **conceptual_description**: 概念型描述
   - 检测关键词：`读成`、`看起来像`、`像`、`类似` 等
   - 严重程度：medium
   - 建议：改用具体视觉特征描述

3. **excessive_negation**: 否定句堆叠
   - 检测：否定词超过 3 个
   - 严重程度：medium
   - 建议：将部分否定描述改为正面描述

**输出：**
- 风险报告（PromptRiskReport）
- 自动改写建议（rewrite_suggestions）
- 保存到 `prompts/risk_report.json`

#### 2. 集成到工作流

**prepare 阶段自动执行：**
1. 生成 prompts
2. 执行风险分析
3. 保存风险报告
4. 在输出中显示风险统计

**示例输出：**
```json
{
  "risk_report_file": "/path/to/prompts/risk_report.json",
  "risk_summary": {
    "total_risks": 10,
    "high_severity_risks": 7
  }
}
```

## 向后兼容性

### 1. 旧版 project.json 自动升级

**升级逻辑：**
- 检测 `schema_version`，如果是 1 或不存在，自动升级到 v2
- 提取 `defaults` 字段
- 转换 `identity_structure` 和 `identity_forbidden` 为结构化约束
- 提取 `state` 字段

### 2. 旧版 brief.json 继续支持

**兼容策略：**
- `identity_anchor_rules` 自动迁移到 `identity_structure` 和 `identity_forbidden`
- 所有现有字段保持不变
- 新字段为可选，不影响旧工作流

### 3. CLI 命令保持兼容

**现有命令不变：**
- `preflight`
- `prepare`
- `generate-refs`
- `submit-video`
- `fetch-result`

**新增命令：**
- `validate-run`
- `review-run`
- `project-status`

## 测试结果

### 基本功能测试

✅ **StateManager 测试**
- 项目创建和加载
- 运行状态创建和加载
- 配置继承

✅ **PromptRiskAnalyzer 测试**
- 检测到 10 个风险（7 个 high，3 个 medium）
- 正确识别动作词 + 身体部位混淆
- 正确识别概念型描述
- 正确识别否定句堆叠

✅ **DeterministicValidator 测试**
- 正确检测缺失文件
- 生成验证报告

## 文件结构

```
skills/dreamina-reference-video/
├── scripts/
│   ├── __init__.py
│   ├── workflow.py                 # 核心工作流（已更新）
│   ├── run_workflow.py             # CLI 入口（已更新）
│   ├── state_manager.py            # 状态管理（新增）
│   ├── validator.py                # 验证引擎（新增）
│   ├── iteration_engine.py         # 迭代引擎（新增）
│   └── prompt_risk_analyzer.py     # 风险分析器（新增）
├── SKILL.md                        # Skill 文档（待更新）
└── references/
    ├── methodology.md
    └── prompt-templates.md
```

## 下一步建议

### 1. 文档更新（未完成）

需要更新以下文档：
- `SKILL.md`: 添加新命令说明、配置继承机制、验证和迭代流程
- `references/`: 添加风险分析和验证规则说明

### 2. 实际项目测试

建议用真实项目测试：
1. 创建新项目，验证配置继承
2. 运行 `validate-run` 和 `review-run`
3. 检查风险分析报告的准确性
4. 验证迭代决策逻辑

### 3. 可选的后续优化（P2 优先级）

根据 codex 的建议，以下功能暂不实现，等基础稳定后再考虑：
- 目标检测验证器（ObjectDetectionValidator）
- VLM 自动判图
- 自动 prompt 改写（目前只提供建议）
- 复杂的回滚/对比工具

## 总结

本次优化成功实现了 codex 方案中的所有 P0 和 P1 功能：

✅ **P0（马上做）：**
- 项目级配置文件
- run 状态持续更新
- 关键约束结构化保存
- 人工检查清单标准化

✅ **P1（下一步）：**
- 简单提示词风险提示器（只报警不改写）
- 简单验证规则（格数、比例、关键文件）
- 迭代上限和人工介入条件

⏸️ **P2（后面再说）：**
- 目标检测验证
- 自动质量评分
- 自动改写 prompt
- 复杂回滚/对比工具

整个优化过程遵循了"先做基础设施，再做智能化"的原则，避免了过度设计，为后续扩展预留了接口。
