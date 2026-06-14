# Step 5：文案审批

🔴🔴🔴 **强制规则（必须遵守）** 🔴🔴🔴

**发送审批消息时，必须使用脚本，严禁直接回复：**

```bash
python3 $WORKSPACE_DIR/workspace-design/skills/brand-poster-creator/scripts/send_approval_message.py \
  --content "消息内容"
```

**为什么**：
- 直接回复 → 触发代码块 → 表格错乱 ❌
- 使用脚本 → 飞书 API → 普通消息 → 表格美观 ✅

**禁止**：
- ❌ 直接回复给用户
- ❌ 使用 message 工具
- ❌ 在回复中包含审批内容

---

## 概述

本步骤负责展示文案成果给用户确认，并触发项目分级审批流程。文案策划判断者需要审核文案是否符合品牌调性和策略要求。

⚠️ **重要变更（v3.0）**：新增审批流程，未通过审批前禁止进入后续步骤。

---

## 5.1 展示文案 + 版式确认

回收 copywriter 产出的文案，结合蒸馏卡的版式数据，以飞书对话卡片形式展示给用户确认：

```markdown
📋 **海报文案与版式确认**

### 版式骨架图
[发送骨架图图片]

### 版式坐标与文案对照表

| 区域 | 类型 | 位置坐标 | 排版方向 | 策划文案 |
|------|------|---------|---------|---------|
| 主标题区 | title | x:5% y:4% 90%×22% | 横排 | 把团圆装进礼盒 |
| 副标题区 | subtitle | x:22% y:26% 56%×4% | 横排 | 新年·心意到家 |
| 左侧竖排 | body_text | x:2% y:42% 5%×40% | 竖排 | 五谷为养 匠心烘焙 |
| 右侧竖排 | body_text | x:93% y:42% 5%×40% | 竖排 | 送礼自用 皆是心意 |
| 底部节日 | subtitle | x:20% y:92% 60%×5% | 横排 | 新春佳节 万家团圆 |
| 底部说明 | body_text | x:8% y:97% 84%×3% | 横排 | 小白心里软·手工烘焙 |

### 参考素材
- [ ] 版式骨架图（已锁定）
- [ ] 风格参考图（已上传 N 张）
- [ ] 产品图（已上传）
- [ ] Logo（已上传）

请确认：
- 回复「确认文案」→ 进入生图阶段
- 回复「修改 [区域] → [新文案]」→ 调整对应区域
```

---

## 5.2 请求文案审批（新增 v3.0）

文案展示给用户后，**立即触发审批流程**：

### 5.2.1 记录 AI 文案生成完成时间

```bash
python3 {baseDir}/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "copywriting" \
  --event-type "complete" \
  --actor "ai"
```

### 5.2.2 请求文案审批并获取艾特标签

```bash
# 请求文案审批（JSON 输出）
python3 {baseDir}/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "copywriting" \
  --artifact "copywriting.json"
```

脚本会返回 JSON，包含以下字段：
```json
{
  "milestone": "copywriting",
  "title": "文案策划完成",
  "reviewer": {
    "name": "张三",
    "open_id": "ou_xxxxx"
  },
  "mention_tag": "<at user_id=\"ou_xxxxx\">张三</at>",
  "artifact_path": "copywriting.json",
  "timeout_at": "2026-06-13T13:00:00Z",
  "message": "<at user_id=\"ou_xxxxx\">张三</at> 文案策划完成，请审核确认"
}
```

### 5.2.3 向用户发送审批请求

⚠️ **重要**：使用 send_approval_message.py 脚本直接发送飞书消息，完全绕过代码块和流式输出。

🔴 **强制方法**：使用脚本分两次发送（脚本会自动获取群聊 ID）

**第1次调用脚本**（发送标题和表格）：
```bash
python3 {baseDir}/scripts/send_approval_message.py \
  --content "✅ **文案策划完成**

| 区域 | 上画文案 | 字体建议 |
|---|---|---|
[从 copywriting.json 提取的文案内容]"
```

**第2次调用脚本**（发送艾特和操作指引）：
```bash
python3 {baseDir}/scripts/send_approval_message.py \
  --content "{使用脚本返回的 .message 字段}

请回复：
- 「通过」→ 进入创意方向确认
- 「修改：具体要求」→ 调整文案
- 「拒绝：原因」→ 终止项目"
```

**实际示例**：

第1次：
```bash
CONTENT='✅ **文案策划完成**

| 区域 | 上画文案 | 字体建议 |
|---|---|---|
| 主标题 | 流程验证测试 | 黑体 |
| 副标题 | 文案·审批·设计生成 全链路 | 无衬线体 |'

python3 $WORKSPACE_DIR/workspace-design/skills/brand-poster-creator/scripts/send_approval_message.py \
  --content "$CONTENT"
```

第2次：
```bash
MESSAGE='<at user_id="ou_b5d2c0a6787a3acc8bc889b15280ae11">肖宁劼</at> 文案策划完成，请审核确认

请回复：
- 「通过」→ 进入创意方向确认
- 「修改：具体要求」→ 调整文案
- 「拒绝：原因」→ 终止项目'

python3 $WORKSPACE_DIR/workspace-design/skills/brand-poster-creator/scripts/send_approval_message.py \
  --content "$MESSAGE"
```

🔴 **关键要点**：
1. **必须使用脚本发送**（不是 message 工具，不是直接回复）
2. **分两次调用脚本**（第1次表格，第2次艾特）
3. **脚本会自动获取群聊 ID**（不需要传 --chat-id 参数）
4. **使用 exec 工具执行**（确保脚本真正执行）

🔴 **严格禁止**：
- ❌ 直接回复给用户（可能触发代码块或流式输出）
- ❌ 使用 message 工具（可能仍有系统行为）
- ❌ 不调用脚本就发送审批消息

🔍 **技术原理**：
- Python 脚本 → 直接调用飞书 API
- 完全绕过 Claude Code 的输出机制
- 飞书 API 发送普通消息 → Markdown 正确渲染
- 脚本自动获取群聊 ID → 简化使用

---

## 5.3 记录审批响应

**等待文案判断者回复**。收到回复后，记录审批结果。

### 5.3.1 判断决策类型

根据用户回复，判断决策类型：
- "通过" → `approved`
- "修改：xxx" → `revision_needed`
- "拒绝：xxx" → `rejected`

### 5.3.2 记录审批响应

```bash
# 记录审批响应
python3 {baseDir}/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "copywriting" \
  --decision "approved" \
  --feedback "文案符合品牌调性"

# 记录人工审核完成时间
python3 {baseDir}/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "copywriting" \
  --event-type "complete" \
  --actor "human"
```

---

## 5.4 处理不同的审批结果

### 情况 A：approved（通过）

文案审批通过，继续进入 Step 6 风格提炼。

向用户确认：
```markdown
✅ 文案审批通过，进入风格提炼阶段
```

### 情况 B：revision_needed（需要修改）

1. **记录反馈意见**到 `project_grading.json`
2. **根据反馈修改 `copywriting.json`**
3. **重新运行 `process_copywriting.py`**：
   ```bash
   python3 {baseDir}/scripts/process_copywriting.py \
     --project-dir "[项目目录绝对路径]"
   ```
4. **再次请求审批**（回到 Step 5.2）

### 情况 C：rejected（拒绝）

1. **记录拒绝原因**
2. **终止项目**
3. **生成复盘报告**：
   ```bash
   python3 {baseDir}/scripts/time_tracking.py \
     retrospective \
     --project-dir "[项目目录绝对路径]" \
     --output "[项目目录绝对路径]/project_retrospective.md"
   ```

---

## 5.5 🔴 CHECKPOINT · STOP：文案审批门禁

**未通过文案审批前，禁止进入 Step 6（风格提炼）或 Step 6（创意表达）。**

### 确认条件

- `project_grading.json` 中 `copywriting` 节点的 `status` 必须为 `approved`
- 或用户在超时后选择继续（仅B级项目）

### 禁止行为

- ❌ **自动假设用户已确认**
- ❌ **沉默视为同意**
- ❌ **绕过审批流程直接进入下一步**
- ❌ **在审批状态为 `waiting` 或 `pending` 时继续执行后续步骤**

---

## 5.6 用户确认后的文件处理

### 情况 A：用户回复「确认文案」

- `copywriting.json` 保留并进入后续风格提炼 / 创意表达
- 审批状态设为 `approved`

### 情况 B：用户回复「修改文案：[具体要求]」

- 更新文案后重新运行 `process_copywriting.py`
- 重新请求审批

### 文案阶段结束后的操作

- 必须先落盘（更新 `project_state.json`、`audit_log.jsonl`）
- 再进入下一步

---

## 5.7 多方向都要出图时的拆分入口

如果 `copywriting.json` 是多方案结构（包含 `options` 数组），且用户明确回复「三个都要」「每个方向各出」「A/B/C 都生成」「每个方案各 N 张」：

### 禁止行为

- ❌ **不得在同一个项目里手写多份 prompt**
- ❌ **不得手动复制目录**

### 正确做法

必须先运行拆分脚本：

```bash
python3 {baseDir}/scripts/split_direction_projects.py \
  --project-dir "[项目目录绝对路径]"
```

### 脚本自动产出

- `[任务ID]-A`、`[任务ID]-B`、`[任务ID]-C` 等独立项目目录
- 每个子项目自己的 `brief.json`、`copywriting.json`、`selected_direction.json`
- 父项目的 `direction_split_manifest.json`
- 子项目已修复/规范化的 `project_state.json`

### 后续处理

拆分后，每个子项目从 Step 6 / Step 6 继续：
- 如果用户要求每个方向各出 `N` 张，则每个子项目的 `run.sh` 都写入同一个 `--count N`
- 这些子项目可以并行派发给 design agent 执行
- 每个子项目内部仍必须通过 `assemble_prompt.py` 和 `execute_generation.py`

---

## 5.8 审批超时处理（B级项目）

B级项目的文案审批如果超时，可以自动通过：

```bash
# 检查超时
timeout_check=$(python3 {baseDir}/scripts/project_grading.py \
  check_timeout \
  --project-dir "[项目目录绝对路径]")

timeout_count=$(echo "$timeout_check" | jq '.timeout_steps | length')

# 如果超时且是 B 级项目，自动通过
if [ "$timeout_count" -gt 0 ]; then
  python3 {baseDir}/scripts/project_grading.py \
    handle_timeout \
    --project-dir "[项目目录绝对路径]" \
    --milestone "copywriting" \
    --timeout-action "auto_approve"
fi
```

**注意**：A/S 级项目超时不自动通过，需要提醒或升级。

---

## 5.9 project_grading.json 结构示例

```json
{
  "project_grade": "B",
  "reviewers": {
    "copywriter": {
      "name": "张三",
      "open_id": "ou_xxxxx"
    },
    "designer": {
      "name": "李四",
      "open_id": "ou_yyyyy"
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
    }
  ]
}
```

---

## 完成后执行下一步

文案审批通过后，进入 **Step 6：参考图风格提炼**（如有参考图）或 **Step 6：画面创意表达方案确认**。
