# 海报项目时间线记录系统集成指南

## 📋 概述

时间线记录系统用于追踪海报项目的每个关键节点，区分 AI 执行时间和人工审批等待时间，便于项目复盘和绩效分析。

---

## 🎯 核心功能

### 1. 时间节点记录
- 自动记录每个工作流步骤的时间点
- 区分执行阶段和等待阶段
- 支持添加备注和元数据

### 2. 问题追踪
- 记录技术问题（AI 错误、系统故障）
- 记录人为延迟（审批拖延、沟通不畅）
- 量化问题影响时长

### 3. 修改追踪
- 记录每次修改请求
- 追踪修改完成时间
- 统计修改次数和原因

### 4. 自动报告生成
- 计算各阶段耗时
- 分析执行效率 vs 审批效率
- 导出飞书文档格式
- 集成到记忆系统任务层级

---

## 🔧 在 brand-poster-creator 中集成

### Step 0: 项目立项后

```bash
# 记录项目立项时间点
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "project_init" \
  --notes "B级项目，客户：某某品牌"
```

### Step 1-2: 需求收集完成后

```bash
# 记录需求收集完成
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "requirement_collected" \
  --notes "品牌档案已查询，蒸馏卡已检查"
```

### Step 4: 文案策划

**开始文案**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "copywriting_start"
```

**文案完成**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "copywriting_done" \
  --notes "文案策略和具体文案已生成"
```

### Step 5: 文案审批

**发送审批请求时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "copywriting_approval_request" \
  --notes "已向客户发送文案审批请求"
```

**收到审批通过时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "copywriting_approved" \
  --notes "客户确认文案"
```

**如果客户要求修改**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-revision \
  --task-id "$TASK_ID" \
  --stage "copywriting" \
  --reason "客户要求调整标题和主文案语气"
```

### Step 6: 创意方向

**开始创意方向**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "creative_direction_start"
```

**创意方向完成**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "creative_direction_done"
```

**发送双审请求时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "creative_approval_request" \
  --notes "已向文案判断者和设计判断者发送审批请求"
```

**双审通过时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "creative_approved" \
  --notes "双审判断者确认创意方向"
```

### Step 7: 生图

**开始生图**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "generation_start"
```

**生图完成**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "generation_done" \
  --notes "海报图片已生成"
```

**如果生图失败**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-issue \
  --task-id "$TASK_ID" \
  --type "technical_error" \
  --description "gpt-image2-gen 生图失败，错误：xxx" \
  --impact 15
```

### Step 8: 设计审批

**发送审批请求时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "design_approval_request" \
  --notes "已向客户发送设计审批请求"
```

**收到审批通过时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "design_approved" \
  --notes "客户确认设计"
```

**如果审批拖延超过2小时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-issue \
  --task-id "$TASK_ID" \
  --type "approval_delay" \
  --description "客户审批响应延迟，等待超过2小时" \
  --impact 120
```

### Step 9: 高级审批（仅A/S级）

**发送高级审批请求时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "advanced_approval_request" \
  --notes "已向创意总监发送审批请求"
```

**高级审批通过时**:
```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "advanced_approved" \
  --notes "创意总监确认"
```

### Step 10: 交付

```bash
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "delivery" \
  --notes "成品图已发送给客户"
```

### Step 11: 项目完结

```bash
# 记录项目完结
python3 /Users/a123/.openclaw/scripts/memory/timeline.py record-node \
  --task-id "$TASK_ID" \
  --node "project_completed" \
  --notes "复盘报告已生成"

# 生成时间线报告并保存到任务目录
python3 /Users/a123/.openclaw/scripts/memory/timeline.py generate-report \
  --task-id "$TASK_ID" \
  --format markdown \
  --output "$TASK_DIR/timeline_report.md"

# 同时生成 JSON 格式供其他工具使用
python3 /Users/a123/.openclaw/scripts/memory/timeline.py generate-report \
  --task-id "$TASK_ID" \
  --format json \
  --output "$TASK_DIR/timeline_report.json"
```

---

## 📊 时间线节点完整列表

| 节点名称 | 说明 | 类型 |
|---------|------|------|
| project_init | 项目立项 | setup |
| requirement_collected | 需求收集完成 | preparation |
| copywriting_start | 文案策划开始 | execution |
| copywriting_done | 文案策划完成 | execution |
| copywriting_approval_request | 文案审批请求 | waiting |
| copywriting_approved | 文案审批通过 | approval |
| creative_direction_start | 创意方向开始 | execution |
| creative_direction_done | 创意方向完成 | execution |
| creative_approval_request | 创意方向审批请求 | waiting |
| creative_approved | 创意方向审批通过 | approval |
| generation_start | 生图开始 | execution |
| generation_done | 生图完成 | execution |
| design_approval_request | 设计审批请求 | waiting |
| design_approved | 设计审批通过 | approval |
| advanced_approval_request | 高级审批请求（A/S级） | waiting |
| advanced_approved | 高级审批通过（A/S级） | approval |
| delivery | 交付完成 | delivery |
| project_completed | 项目完结 | completion |

---

## ⚠️ 问题类型

| 类型 | 说明 | 何时使用 |
|------|------|----------|
| approval_delay | 审批延迟（人为因素） | 审批响应超过合理时间 |
| technical_error | 技术错误（AI/系统问题） | 生图失败、API 错误等 |
| revision_request | 修改请求（客户反馈） | 客户要求修改内容 |
| resource_unavailable | 资源不可用（品牌资产缺失等） | 缺少 Logo、VI 等资源 |
| communication_delay | 沟通延迟 | 需求确认拖延等 |
| other | 其他 | 其他未分类问题 |

---

## 📈 报告示例

### 飞书文档格式输出

```markdown
# 海报项目时间线报告

**任务 ID**: TASK-20260617172128-077f15
**生成时间**: 2026-06-17T18:00:00

## 📊 项目总览

- **项目总耗时**: 245.5 分钟 (4.1 小时)
- **AI执行时间**: 45.2 分钟 (18.4%)
- **人工审批等待时间**: 180.3 分钟 (73.4%)
- **问题影响时间**: 20 分钟
- **修改次数**: 1 次

## ⏱️ 详细时间线

### 项目立项
- **时间**: 2026-06-17T14:00:00
- **描述**: 项目分级和基础信息收集
- **备注**: B级项目，客户：wokenday

### 需求收集完成
- **时间**: 2026-06-17T14:05:30
- **描述**: 品牌档案查询、蒸馏卡检查完成

...

## 📈 阶段耗时分析

### 准备阶段（立项→需求收集完成）
- **耗时**: 5.5 分钟 (0.1 小时)
- **类型**: execution

### 文案执行（开始→完成）
- **耗时**: 12.3 分钟 (0.2 小时)
- **类型**: execution

### 文案审批等待（请求→通过）
- **耗时**: 65.0 分钟 (1.1 小时)
- **类型**: waiting

...

## ⚠️ 问题记录

### ISSUE-1: 审批延迟（人为因素）
- **状态**: ✅ 已解决
- **发生时间**: 2026-06-17T15:30:00
- **解决时间**: 2026-06-17T16:30:00
- **影响时长**: 60 分钟
- **描述**: 客户审批响应延迟，等待超过1小时

## 📝 修改记录

### REV-1: copywriting
- **状态**: ✅ 已完成
- **请求时间**: 2026-06-17T15:00:00
- **完成时间**: 2026-06-17T15:15:00
- **原因**: 客户要求调整主文案语气

## 🎯 绩效分析

### AI 执行效率
- AI 执行时间占比：18.4%
- 平均每个执行阶段：15.1 分钟（文案+创意+生图）

### 人工审批效率
- 审批等待时间占比：73.4%
- 平均每个审批节点：60.1 分钟

### 改进建议
- ⚠️ 审批等待时间过长（73.4%），建议：
  - 优化审批流程
  - 设置审批时效提醒
  - 考虑并行审批机制
```

---

## 🔗 数据存储

### 文件位置

```
projects/客户/品牌/项目/tasks/TASK-xxx/
├── task.json                    # 任务基本信息
├── timeline.json                # 时间线原始数据
├── timeline_report.md           # 飞书文档格式报告
├── timeline_report.json         # JSON 格式报告
└── iterations/
    ├── v1/
    ├── v2/
    └── v3/
```

### timeline.json 结构

```json
{
  "task_id": "TASK-xxx",
  "created_at": "2026-06-17T14:00:00",
  "nodes": {
    "project_init": {
      "timestamp": "2026-06-17T14:00:00",
      "notes": "B级项目",
      "metadata": {}
    },
    "copywriting_approval_request": {
      "timestamp": "2026-06-17T14:30:00",
      "notes": "已向客户发送文案审批请求",
      "metadata": {
        "approver": "客户名",
        "approval_type": "copywriting"
      }
    }
  },
  "issues": [
    {
      "issue_id": "ISSUE-1",
      "type": "approval_delay",
      "type_name": "审批延迟（人为因素）",
      "description": "客户审批响应延迟",
      "timestamp": "2026-06-17T15:30:00",
      "resolved_at": "2026-06-17T16:30:00",
      "impact_minutes": 60
    }
  ],
  "revisions": [
    {
      "revision_id": "REV-1",
      "stage": "copywriting",
      "reason": "客户要求调整主文案语气",
      "requested_at": "2026-06-17T15:00:00",
      "completed_at": "2026-06-17T15:15:00"
    }
  ]
}
```

---

## 🎯 核心价值

### 1. 精准绩效评估
- **区分 AI 执行时间 vs 人工等待时间**
- 识别瓶颈环节（审批拖延、技术问题）
- 量化问题影响

### 2. 数据驱动优化
- 基于真实数据改进流程
- 发现重复性问题
- 优化审批机制

### 3. 公平的责任归属
- 明确区分技术问题和人为延迟
- 保护工作人员，避免不公平指责
- 客观评估各环节效率

### 4. 自动化复盘
- 项目完结自动生成报告
- 无需手动整理数据
- 标准化的分析维度

---

## 📝 使用建议

### 1. 及时记录
- **每个节点立即记录**，不要事后补录
- 使用脚本输出确认记录成功

### 2. 准确分类
- 技术问题 vs 人为延迟要明确区分
- 问题影响时长要实事求是

### 3. 定期复盘
- 每周查看时间线报告
- 识别共性问题
- 持续优化流程

### 4. 透明沟通
- 时间线报告可分享给团队
- 基于数据讨论改进方案
- 建立客观的绩效评估体系

---

## 🚀 下一步

1. **集成到 brand-poster-creator skill**
   - 在每个步骤添加时间线记录
   - 测试完整流程

2. **扩展到其他 skill**
   - 详情页设计
   - 视频制作
   - 其他创意项目

3. **建立分析仪表板**
   - 汇总多个项目的时间线数据
   - 生成团队绩效报告
   - 识别系统性问题

---

**文档版本**: 1.0  
**最后更新**: 2026-06-17
