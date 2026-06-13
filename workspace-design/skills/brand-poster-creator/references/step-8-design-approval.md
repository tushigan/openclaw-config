# Step 8：设计审批

## 概述

本步骤负责将生成的成品图发送给用户，并触发设计判断者审批流程。仅当 `generation_result.json.ok=true` 且成品文件真实存在后，才将成品图发送给用户确认。

⚠️ **重要变更（v3.0）**：新增设计审批流程，根据项目等级（B/A/S）执行不同层级的审批。

---

## 8.1 🔴 CHECKPOINT · STOP：交付前强制检查（必须执行）

在发送前，main 必须先执行交付检查脚本：

```bash
python3 <<'EOF'
import json
import os
import sys

project_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
image_path = f"{project_dir}/images/final_poster.png"

# 检查文件存在
if not os.path.exists(image_path):
    print(json.dumps({"status": "error", "message": "图片文件不存在"}, ensure_ascii=False))
    sys.exit(1)

# 检查文件大小
size = os.path.getsize(image_path)
print(json.dumps({
    "status": "ready",
    "image_path": image_path,
    "size_bytes": size,
    "size_mb": round(size / 1024 / 1024, 2),
    "delivery_instruction": {
        "tool": "message",
        "action": "send",
        "channel": "feishu",
        "media": image_path,
        "mimeType": "image/png"
    },
    "warning": "必须调用 message 工具发送，不得输出 MEDIA: 文本"
}, indent=2, ensure_ascii=False))
EOF
```

**检查脚本输出后，必须按照 `delivery_instruction` 调用 message 工具。**

---

## 8.2 准备交付清单

在发送前，main 必须先执行：

```bash
python3 {baseDir}/scripts/prepare_feishu_delivery.py \
  --project-dir /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]
```

该脚本会产出：
- `/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/delivery_manifest.json`
- 交付目录中的预览图 / 原图副本 / 原图 zip（按大小条件分流）

---

## 8.3 真实发送规则（硬约束）

### 错误示例（用户收不到图片）

```
❌ 错误：MEDIA:/Users/a123/.openclaw/workspace/brand-poster-projects/BP-xxx/images/final_poster.png
❌ 错误：图片路径：/Users/a123/.openclaw/workspace/brand-poster-projects/BP-xxx/images/final_poster.png
❌ 错误：图片已在 images/ 目录里
❌ 错误：发上来了（但没有调用 message 工具）
```

### 正确示例（真实发送）

```
✅ 正确：调用 message 工具
message(action=send, channel=feishu, media=/Users/a123/.openclaw/workspace/brand-poster-projects/BP-xxx/images/final_poster.png, mimeType=image/png)

✅ 正确：等待返回
{"ok": true, "messageId": "om_xxx", "chatId": "oc_xxx"}

✅ 正确：确认交付
已发送图片 (messageId: om_xxx)
```

**记住**：`MEDIA:` 只是文本输出，不是真实发送！用户在飞书中看不到任何图片！

### 发送规则

1. 先读取 `delivery_manifest.json`
2. 必须读取 `agent_delivery_contract`，并按其中的 `send_plan.message_tool_arguments` 调用真实飞书媒体发送工具：
   - 首选 `message(action=send, channel=feishu, accountId=main, media=..., mimeType=...)`
   - 若当前运行环境提供 `feishu-send-image` 等等效图片工具，使用等效图片工具
   - `delivery_target.chat_id/user_id` 为空时，必须使用当前飞书会话绑定继续发送；这不是停止理由
3. **绝对禁止**把 `MEDIA:/absolute/path`、本地绝对路径、`file://...` 或目录说明作为回复文本冒充交付
4. 工具返回 `ok=true` 且有 `messageId/chatId` 后，才允许说"已发送/已发群里/交付完成"
5. **如果没有看到 message 工具的返回值，说明没有真实发送，必须重新调用 message 工具**
6. 发送成功后必须运行：

```bash
python3 {baseDir}/scripts/record_feishu_delivery.py \
  --project-dir /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID] \
  --sent-path [本次真实发送的图片路径] \
  --message-id [飞书发送工具返回的 messageId] \
  --chat-id [飞书发送工具返回的 chatId] \
  --method "message(media)"
```

7. 若 `delivery_mode=direct_image`：
   - 真实发送 `deliverables.original_copy.path`
8. 若 `delivery_mode=preview_and_zip`：
   - 只真实发送 `deliverables.preview_image.path` 供飞书预览
   - 明确告诉用户：当前发送的是压缩预览图，原始高清图已保留，后续修改将继续使用原图，不会基于预览图反复压缩
   - 用户确认定稿后，再发送 `deliverables.original_zip.path` 作为原图交付包
9. 任何"局部修改""继续调整""重新生成"都必须继续引用 `edit_source_image` 指向的原图，不得把 preview 图当作修改输入

---

## 8.4 🔴 CHECKPOINT · STOP：交付验证清单（必须全部通过）

在说"已发送"之前，必须确认：
- ✅ 调用了 `message` 工具（不是输出 `MEDIA:` 文本）
- ✅ `message` 工具返回了 `{"ok": true, "messageId": "...", "chatId": "..."}`
- ✅ 记录了 `messageId` 和 `chatId` 到 `delivery_manifest.json`
- ✅ 向用户回复中包含 `messageId`（证明真实发送）

**如果以上任一条不满足，说明交付失败，必须重新发送。**

---

## 8.5 给用户的话术

```markdown
🎉 **海报已生成**

- 若当前收到的是原图：可直接按原清晰度确认
- 若当前收到的是预览图：这是为适配飞书大小限制自动生成的压缩预览，原始高清图已保留；若你确认定稿，我再把原图 zip 包发给你
- 后续如需局部修改，我会继续基于原图处理，不会使用压缩预览图反复修改

请确认：
- 文案位置是否正确
- 产品外观是否保真
- 整体视觉效果是否满意

请选择：
- 「确认定稿」→ 进入设计审批流程
- 「局部修改 [具体描述]」→ 调整后重新生图
```

---

## 8.6 请求设计审批（新增 v3.0）

用户确认设计成品后，**触发设计审批流程**：

### 8.6.1 记录 AI 设计完成时间

```bash
python3 {baseDir}/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "design" \
  --event-type "complete" \
  --actor "ai"
```

### 8.6.2 请求设计审批并获取艾特标签

```bash
# 请求设计审批（JSON 输出）
python3 {baseDir}/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "design" \
  --artifact "images/final_poster.png"
```

脚本会返回 JSON，包含真实飞书艾特标签。

### 8.6.3 向用户发送审批请求

⚠️ **重要**：必须使用脚本返回的 `message` 字段中的艾特标签，不要手写 `@用户名`。

从返回的 JSON 中提取 `message` 字段，直接用于回复：

```markdown
✅ **设计初稿完成**

[已发送设计成品图]

{从 JSON 提取的 .message 字段内容，包含真实飞书艾特标签}

请审核确认：
- 回复「通过」→ 设计审批通过
  - B级项目：直接进入交付流程
  - A/S级项目：进入创意总监审核
- 回复「修改：[具体要求]」→ 需要调整设计
- 回复「拒绝：[原因]」→ 终止项目
```

**示例回复**：
```markdown
✅ **设计初稿完成**

[已发送成品图]

<at user_id="ou_2253f3cfcdb6e0ae8707cee2ea10a57c">林育丰</at> 设计初稿完成，请审核确认

请回复：
- 「通过」→ 设计审批通过
- 「修改：具体要求」→ 调整设计
- 「拒绝：原因」→ 终止项目
```
- 回复「拒绝：[原因]」→ 终止项目
```

---

## 8.7 记录设计审批响应

**等待设计判断者回复**。收到回复后，记录审批结果：

```bash
# 记录审批响应
python3 {baseDir}/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "design" \
  --decision "approved" \
  --feedback "设计效果符合预期"

# 记录人工审核完成时间
python3 {baseDir}/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "design" \
  --event-type "complete" \
  --actor "human"
```

### 处理不同的审批结果

#### 1. approved（通过）

- **B级项目**：设计审批通过后，直接进入 Step 10 最终交付
- **A级项目**：需要继续创意总监审核（Step 9.1）
- **S级项目**：需要继续创意总监审核（Step 9.1）

#### 2. revision_needed（需要修改）

- 记录反馈意见
- 根据反馈调整设计或重新生成
- 再次请求审批（回到 Step 8.6）

#### 3. rejected（拒绝）

- 记录拒绝原因
- 终止项目
- 生成复盘报告

---

## 8.8 补偿入口（强制）

用户追问"进度 / 好了没 / 图片呢 / 发图 / 没收到 / 继续"时，如果当前项目已经有 `generation_result.json.ok=true` 或 `delivery_manifest.json`，必须先恢复到 Step 8 检查交付状态。

若 `delivery_manifest.json.delivery_status` 不是成功状态，或缺少 `delivery_evidence.message_id/chat_id`，说明还没有真实发送成功。此时禁止回复本地路径、`MEDIA:/...`、"图片已在目录里"或"交付副本已生成"；必须继续执行真实飞书发送。

若子 agent 只返回了 `feishu-deliver` 路径，也只能视为"发送副本已准备"，不能视为"已发给用户"。

---

## 8.9 设计审批门禁

**未通过设计审批前，B级项目禁止进入 Step 10（最终交付），A/S级项目禁止进入 Step 9（高级审批）。**

### 确认条件

- `project_grading.json` 中 `design` 节点的 `status` 必须为 `approved`
- 或用户在超时后选择继续（仅B级项目）

### 禁止行为

- ❌ 自动假设用户已确认
- ❌ 沉默视为同意
- ❌ 绕过审批流程直接进入下一步
- ❌ 在审批状态为 `waiting` 或 `pending` 时继续执行后续步骤

---

## 8.10 艾特设计判断者的实现

在发送审批请求时，`project_grading.py request` 脚本会自动生成艾特消息：

```bash
# 脚本返回示例
{
  "status": "success",
  "milestone": "design",
  "reviewer_role": "designer",
  "reviewer_name": "李四",
  "message": "@李四 请审核设计初稿"
}
```

main agent 必须将 `message` 字段的内容插入到发送给用户的消息中，确保设计判断者能收到飞书通知。

---

## 完成后执行下一步

- **B级项目**：设计审批通过后，进入 **Step 10：最终交付**
- **A/S级项目**：设计审批通过后，进入 **Step 9：高级审批**（创意总监审核）
