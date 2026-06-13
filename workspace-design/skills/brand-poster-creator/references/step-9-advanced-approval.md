# Step 9：高级审批

## 概述

本步骤仅适用于 **A 级和 S 级项目**。设计判断者审批通过后，需要进一步的高层决策审批：
- **A 级项目**：需要创意总监审核
- **S 级项目**：需要创意总监审核 + 老板最终决策

⚠️ **B 级项目跳过本步骤**，设计审批通过后直接进入 Step 10（最终交付）。

---

## 9.1 创意总监审核（仅 A/S 级项目）

### 9.1.1 前置条件

- 项目等级为 A 或 S
- 设计判断者已审批通过（`project_grading.json` 中 `design` 节点的 `status` 为 `approved`）

### 9.1.2 触发创意总监审批

设计判断者通过后，触发创意总监审核：

```bash
# 请求创意总监审批
approval_request=$(python3 {baseDir}/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "creative_direction" \
  --artifact "images/final_poster.png")

mention_message=$(echo "$approval_request" | jq -r '.message')
```

### 9.1.3 向用户发送审批请求

```markdown
✅ **设计判断者已通过，进入创意总监审核**

$mention_message

请审核确认：
- 回复「通过」→ 创意总监审批通过
  - A级项目：进入交付流程
  - S级项目：进入老板最终决策
- 回复「修改：[具体要求]」→ 需要调整创意方向
- 回复「拒绝：[原因]」→ 终止项目
```

### 9.1.4 记录创意总监审批响应

**等待创意总监回复**。收到回复后，记录审批结果：

```bash
# 记录审批响应
python3 {baseDir}/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "creative_direction" \
  --decision "approved" \
  --feedback "创意方向符合战略定位"
```

### 9.1.5 处理不同的审批结果

#### approved（通过）

- **A级项目**：创意总监通过后，进入 Step 10（最终交付）
- **S级项目**：创意总监通过后，继续进入 Step 9.2（老板最终决策）

#### revision_needed（需要修改）

- 记录反馈意见
- 根据反馈调整创意方向或重新生成设计
- 重新走设计审批流程（回到 Step 8.6）

#### rejected（拒绝）

- 记录拒绝原因
- 终止项目
- 生成复盘报告

---

## 9.2 老板最终决策（仅 S 级项目）

### 9.2.1 前置条件

- 项目等级为 S
- 创意总监已审批通过（`project_grading.json` 中 `creative_direction` 节点的 `status` 为 `approved`）

### 9.2.2 触发老板最终审批

创意总监通过后，触发老板最终审批：

```bash
# 请求老板最终审批
approval_request=$(python3 {baseDir}/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "final_approval" \
  --artifact "images/final_poster.png")

mention_message=$(echo "$approval_request" | jq -r '.message')
```

### 9.2.3 向用户发送审批请求

```markdown
✅ **创意总监已通过，进入老板最终决策**

$mention_message

请审核确认：
- 回复「通过」→ 项目最终批准，进入交付流程
- 回复「修改：[具体要求]」→ 需要调整
- 回复「拒绝：[原因]」→ 终止项目
```

### 9.2.4 记录老板审批响应

**等待老板回复**。收到回复后，记录审批结果：

```bash
# 记录审批响应
python3 {baseDir}/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "final_approval" \
  --decision "approved" \
  --feedback "符合战略目标，批准上线"
```

### 9.2.5 处理不同的审批结果

#### approved（通过）

- S级项目：老板通过后，进入 Step 10（最终交付）

#### revision_needed（需要修改）

- 记录反馈意见
- 根据反馈调整设计或创意方向
- 重新走审批流程（回到对应审批节点）

#### rejected（拒绝）

- 记录拒绝原因
- 终止项目
- 生成复盘报告

---

## 9.3 审批超时处理

在等待审批过程中，定期检查超时：

### 9.3.1 检查超时

```bash
# 检查超时
timeout_check=$(python3 {baseDir}/scripts/project_grading.py \
  check_timeout \
  --project-dir "[项目目录绝对路径]")

timeout_count=$(echo "$timeout_check" | jq '.timeout_steps | length')
```

### 9.3.2 根据项目等级处理超时

#### B级项目：自动通过

```bash
python3 {baseDir}/scripts/project_grading.py \
  handle_timeout \
  --project-dir "[项目目录绝对路径]" \
  --milestone "[超时的节点]" \
  --timeout-action "auto_approve"
```

#### A/S级项目：提醒或升级

**第一次超时：提醒**

```bash
python3 {baseDir}/scripts/project_grading.py \
  handle_timeout \
  --project-dir "[项目目录绝对路径]" \
  --milestone "[超时的节点]" \
  --timeout-action "remind"
```

向审批者发送提醒消息：

```markdown
⏰ **审批提醒**

@[审批者姓名] 项目审批已超时 [X] 分钟，请尽快审核。

项目：[任务ID]
审批节点：[创意总监审核 / 老板最终决策]
等待时长：[X] 分钟
```

**第二次超时：升级给项目经理**

```bash
python3 {baseDir}/scripts/project_grading.py \
  handle_timeout \
  --project-dir "[项目目录绝对路径]" \
  --milestone "[超时的节点]" \
  --timeout-action "escalate"
```

向项目经理发送升级通知：

```markdown
🚨 **审批超时升级**

项目审批已超时 [X] 分钟，需要协调处理。

项目：[任务ID]
项目等级：[A/S]
审批节点：[创意总监审核 / 老板最终决策]
审批者：@[审批者姓名]
等待时长：[X] 分钟

请协调推进审批流程。
```

---

## 9.4 审批流程可视化

### A级项目审批流程

```
Step 5: 文案审批（文案策划判断者）
  ↓ 通过
Step 8: 设计审批（设计判断者）
  ↓ 通过
Step 9.1: 创意总监审核
  ↓ 通过
Step 10: 最终交付
```

### S级项目审批流程

```
Step 5: 文案审批（文案策划判断者）
  ↓ 通过
Step 8: 设计审批（设计判断者）
  ↓ 通过
Step 9.1: 创意总监审核
  ↓ 通过
Step 9.2: 老板最终决策
  ↓ 通过
Step 10: 最终交付
```

---

## 9.5 审批状态数据结构

### project_grading.json 示例（S级项目）

```json
{
  "project_grade": "S",
  "reviewers": {
    "copywriter": {
      "name": "张三",
      "open_id": "ou_xxxxx"
    },
    "designer": {
      "name": "李四",
      "open_id": "ou_yyyyy"
    },
    "creative_director": {
      "name": "王五",
      "open_id": "ou_zzzzz"
    },
    "boss": {
      "name": "赵六",
      "open_id": "ou_wwwww"
    }
  },
  "approval_flow": [
    {
      "milestone": "copywriting",
      "reviewer_role": "copywriter",
      "status": "approved",
      "decision": "approved",
      "feedback": "文案符合品牌调性",
      "requested_at": "2026-06-13T11:00:00Z",
      "responded_at": "2026-06-13T11:15:00Z"
    },
    {
      "milestone": "design",
      "reviewer_role": "designer",
      "status": "approved",
      "decision": "approved",
      "feedback": "设计效果符合预期",
      "requested_at": "2026-06-13T12:00:00Z",
      "responded_at": "2026-06-13T12:20:00Z"
    },
    {
      "milestone": "creative_direction",
      "reviewer_role": "creative_director",
      "status": "approved",
      "decision": "approved",
      "feedback": "创意方向符合战略定位",
      "requested_at": "2026-06-13T12:25:00Z",
      "responded_at": "2026-06-13T12:40:00Z"
    },
    {
      "milestone": "final_approval",
      "reviewer_role": "boss",
      "status": "approved",
      "decision": "approved",
      "feedback": "符合战略目标，批准上线",
      "requested_at": "2026-06-13T12:45:00Z",
      "responded_at": "2026-06-13T13:00:00Z"
    }
  ]
}
```

---

## 9.6 关键硬规则

### ✅ 必须遵守

1. **B级项目跳过本步骤**：设计审批通过后直接进入 Step 10
2. **A级项目只需创意总监审核**：不需要老板审批
3. **S级项目需要完整审批链**：创意总监 → 老板
4. **审批顺序不可跳过**：必须按流程逐级审批
5. **超时处理必须区分项目等级**：B级自动通过，A/S级提醒或升级

### ❌ 禁止行为

1. **不得跳过审批节点**：A/S级项目必须完成对应审批
2. **不得自动假设通过**：必须等待审批者明确回复
3. **不得混淆审批层级**：A级不需要老板审批，S级必须有老板审批
4. **不得在超时后自动通过 A/S 级审批**：只有 B 级可以自动通过

---

## 完成后执行下一步

所有必需的审批节点通过后，进入 **Step 10：最终交付**。
