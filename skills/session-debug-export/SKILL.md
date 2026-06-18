---
name: session-debug-export
description: 导出聊天记录。将当前 OpenClaw 对话记录、工具调用、工具输出、后台网关日志和 AI 问题定位分析导出为一个可分享的 Markdown 文件。用户说”导出聊天记录””导出当前聊天””导出对话记录””聊天记录导出””生成聊天日志””打包聊天记录”时必须使用本技能。
triggers:
  - “导出聊天记录”
  - “导出当前聊天”
  - “导出当前对话”
  - “导出对话记录”
  - “聊天记录导出”
  - “生成聊天日志”
  - “打包聊天记录”
  - “导出后台日志”
  - “生成调试报告”
---

## ⚠️ AGENT 必读：执行流程（最高优先级）

**当收到”导出聊天记录”等触发词时，按以下步骤执行，不要自行拼接简化的 txt 导出：**

### 第 1 步：复制脚本到 workspace

由于路径保护机制，不能直接执行 `~/.openclaw/skills/` 下的脚本。必须先复制到当前 workspace：

```python
# 使用 read 工具读取脚本内容
read('/Users/a123/.openclaw/skills/session-debug-export/scripts/export_chat_report.py')

# 使用 write 工具写入到当前 workspace 的 outputs 目录
# 例如：<current-workspace>/outputs/_temp_export_chat_report.py
write('<current-workspace>/outputs/_temp_export_chat_report.py', <script-content>)
```

### 第 2 步：执行临时脚本

```bash
python3 <current-workspace>/outputs/_temp_export_chat_report.py \
  --workspace /Users/a123/.openclaw \
  --session-key current \
  --issue “聊天记录导出” \
  --agent-name “<agent-display-name>”
```

**参数说明**：
- `--workspace`：固定为 `/Users/a123/.openclaw`
- `--session-key`：使用 `current` 自动查找当前会话
- `--issue`：问题描述，用于文件命名
- `--agent-name`：当前 agent 的显示名称（如 “research”、”design” 等）

### 第 3 步：检查输出文件

脚本执行成功后，会在以下路径生成导出文件：

```
/Users/a123/Downloads/openclaw 问题汇总/YYYYMMDD-HHMMSS-对话ID-问题短名.md
```

使用 `ls` 或 `find` 命令确认文件已生成，并检查文件大小是否合理（通常 > 10KB）。

### 第 4 步：发送文件给用户

使用 `message` 工具的 `path` 参数发送文件：

```json
{
  “tool”: “message”,
  “path”: “/Users/a123/Downloads/openclaw 问题汇总/<actual-filename>.md”,
  “caption”: “OpenClaw 聊天记录导出”
}
```

**重要**：必须真实发送文件，不能只返回本地路径。

### 常见问题

**Q: 遇到 `exec blocked: python3 cannot target protected path ~/.openclaw/skills/` 怎么办？**  
A: 按第 1 步使用 read+write 复制脚本，不要直接执行 skills 目录下的脚本。

**Q: 遇到 `exec blocked: cp cannot modify protected path ~/.openclaw/skills/` 怎么办？**  
A: 不要用 `cp` 命令，用 read+write 工具复制。

**Q: `sessions_history` 工具超时怎么办？**  
A: 不要降级使用 `sessions_history`，它有截断限制。坚持使用本 skill 的脚本。

**Q: 能不能用 heredoc 手动拼接一个简化版？**  
A: ❌ **禁止**。必须使用本 skill 的完整流程，生成包含 AI 分析和后台日志的完整导出。

---

# Session Debug Export - 会话调试导出

导出当前 OpenClaw agent 会话的完整对话记录和后台网关日志，生成一个自包含的 Markdown 文件，方便用户分享给其他 AI 进行问题分析和定位。它导出的是 OpenClaw agent session，不是飞书平台历史消息接口里的群聊全量记录。

## 何时使用

当用户说以下任意表达时，必须优先使用本 skill：

- **导出聊天记录** - 主触发词，默认导出当前会话聊天记录和后台日志
- **导出当前聊天**
- **导出当前对话**
- **导出对话记录**
- **聊天记录导出**
- **生成聊天日志**
- **打包聊天记录**
- **导出后台日志**
- **生成调试报告**

## 功能特点

### 1. 完整对话记录
- 用户消息和 AI 回复
- 工具调用详情（工具名称、输入参数）
- 工具输出结果
- 时间戳信息

### 2. 后台日志
- 网关连接日志
- 工具执行错误
- 性能警告（长时间运行会话、事件循环延迟等）
- 系统诊断信息

### 3. 输出格式
- 单一 Markdown 文件，易于分享
- 自动命名：`YYYYMMDD-HHMMSS-对话ID-问题短名.md`
- 问题短名优先取 `--issue` 中的中文，最多 8 个汉字
- 默认保存到 `/Users/a123/Downloads/openclaw 问题汇总`

## 使用方法

### 基本用法 - 导出当前会话

优先使用 `--session-key current`。脚本会按以下顺序解析当前会话：

1. 运行环境里的当前 session（如 `OPENCLAW_MCP_SESSION_KEY` / `OPENCLAW_SOURCE_SESSION_KEY`）
2. `--agent`、`--chat-type`、`--peer-id` 过滤到的最近 session
3. 当前工作目录对应的 agent / shared-agent 最近 session
4. 全 agent 最近 session 兜底

不要自己用 `openclaw sessions --limit 1` 代替 `current`，管理员私聊、共享 agent、群聊并发时会拿错会话。

```bash
python3 "<skill-dir>/scripts/export_chat_report.py" \
  --workspace "/Users/a123/.openclaw" \
  --session-key current \
  --issue "问题简短描述" \
  --agent-name "小爪"
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--workspace` | 否 | 当前目录 | OpenClaw 工作区路径 |
| `--session-key` | 否 | `current` | 会话标识，`current` 会自动查找活跃会话 |
| `--agent` / `--agent-id` | 否 | 环境或工作目录推断 | 解析 `current` 时限定 agent，如 `design-shared` |
| `--chat-type` | 否 | 不限定 | 解析 `current` 时限定 `direct` / `group` / `channel` |
| `--peer-id` | 否 | 不限定 | 解析 `current` 时限定 `ou_xxx` 或 `oc_xxx` |
| `--issue` | 是 | 无 | 问题简短描述，用于文件命名 |
| `--agent-name` | 否 | `小爪` | AI 助手显示名称 |
| `--output-dir` | 否 | `/Users/a123/Downloads/openclaw 问题汇总` | 输出目录 |
| `--log-lines` | 否 | `300` | 捕获日志行数 |
| `--max-bytes` | 否 | `400000` | 日志最大字节数 |
| `--no-logs` | 否 | `false` | 跳过日志捕获 |

### 示例

#### 1. 导出当前会话（自动检测）

```bash
python3 "<skill-dir>/scripts/export_chat_report.py" \
  --workspace "/Users/a123/.openclaw" \
  --session-key current \
  --issue "工具超时问题"
```

#### 2. 导出指定会话并自定义代理名称

```bash
python3 "<skill-dir>/scripts/export_chat_report.py" \
  --workspace "/Users/a123/.openclaw" \
  --session-key "agent:main:dashboard:abc123..." \
  --issue "飞书消息发送失败" \
  --agent-name "Kiro"
```

#### 3. 在群聊/共享 agent 中强制限定目标

```bash
python3 "<skill-dir>/scripts/export_chat_report.py" \
  --workspace "/Users/a123/.openclaw" \
  --session-key current \
  --agent design-shared \
  --chat-type group \
  --peer-id "oc_xxx" \
  --issue "群聊导出"
```

#### 4. 只导出对话，不包含日志

```bash
python3 "<skill-dir>/scripts/export_chat_report.py" \
  --workspace "/Users/a123/.openclaw" \
  --session-key current \
  --issue "正常对话导出" \
  --no-logs
```

#### 5. 增加日志捕获量

```bash
python3 "<skill-dir>/scripts/export_chat_report.py" \
  --workspace "/Users/a123/.openclaw" \
  --session-key current \
  --issue "复杂问题排查" \
  --log-lines 500 \
  --max-bytes 500000
```

## 查找会话 Key

如果不确定当前会话的 key，可以使用以下命令：

```bash
# 查看最近的活跃会话
openclaw sessions --all-agents --active 60 --limit 10 --json

# 查看某个 agent 的会话
openclaw sessions --agent design-shared --active 60 --limit 20 --json
```

从输出的 JSON 中找到 `"key"` 字段的值。

## 输出示例

生成的 Markdown 文件包含：

```markdown
# Chat with 小爪

## AI Analysis

### 定位摘要

- **问题标题**：工具超时问题
- **Session Key**：`agent:main:dashboard:...`
- **事件数**：139；用户消息 2；AI 消息 9；工具调用 44；工具结果 44；疑似工具错误 2

### 初步判断

- 工具或上游服务存在错误 / 超时，需要优先查看 Tool Output 和 Backend Logs 中的 error/timeout 行。

## Export Metadata

- Issue: `工具超时问题`
- Session: `agent:main:dashboard:...`
- Raw trajectory bundle: `/Users/carl/.openclaw/workspace/.openclaw/trajectory-exports/...`

## You (2026-06-03T12:00:00.000Z)

用户的消息内容...

## 小爪 (2026-06-03T12:00:05.000Z)

AI 的回复内容...

## 小爪 (2026-06-03T12:00:06.000Z)

🔧 **Tool Call**: `read` (read)
**Input**:
```json
{
  "path": "/some/file.md"
}
```

## Tool (2026-06-03T12:00:07.000Z)

📦 **Tool Output**: `read` (read)
**Output**:
```text
文件内容...
```

## Backend Logs

```log
2026-06-03T12:00:00.000+08:00 info gateway/ws ...
2026-06-03T12:00:01.000+08:00 warn diagnostic ...
```
```

## 使用场景

### 1. 问题报告
当遇到工具执行失败、超时、或其他异常时，导出完整对话和日志，发送给技术支持或其他 AI 进行分析。

### 2. 工作流记录
保存重要的工作流程和对话，用于后续参考或分享给团队成员。

### 3. 性能分析
通过后台日志中的性能警告（如 `long-running session`、`event_loop_delay` 等），定位性能瓶颈。

### 4. 错误定位
结合对话记录和后台日志，快速定位错误发生的时间点和上下文。

## AI 分析建议

生成的导出文件可以直接提供给 AI 进行分析。AI 可以：

1. **识别错误模式** - 从日志中找到工具失败、超时、网络错误等
2. **关联时间线** - 将用户操作和后台日志事件关联起来
3. **性能诊断** - 识别长时间运行、高延迟等性能问题
4. **根因分析** - 根据错误堆栈和上下文推断根本原因

常见的问题特征：
- `tool failed:` - 工具执行失败
- `timed out after` - 超时错误
- `long-running session` - 会话运行时间过长
- `event_loop_delay` - 事件循环延迟
- `queued_behind_active_work` - 请求排队等待

## 技术实现

### 解析流程
1. 使用 `openclaw sessions export-trajectory` 导出会话轨迹
2. 解析 `events.jsonl` 文件，提取用户消息、AI 回复、工具调用等事件
3. 使用 `openclaw logs` 捕获后台网关日志
4. 将所有信息格式化为 Markdown 文件

### 事件类型
脚本会解析以下事件类型：
- `user.message` - 用户消息
- `assistant.message` - AI 回复
- `tool.call` - 工具调用
- `tool.result` - 工具执行结果

## 注意事项

1. **隐私保护** - 导出的文件可能包含敏感信息（路径、API key 等），分享前请检查
2. **文件大小** - 对于长会话，导出文件可能很大，默认限制日志为 250KB
3. **临时文件** - 导出过程会在 `.openclaw/trajectory-exports/` 创建临时目录
4. **权限要求** - 需要读取会话文件和日志文件的权限

## 故障排除

### 无法找到会话
```
Failed to auto-resolve current session key.
```
解决方法：使用 `openclaw sessions --all-agents --limit 20 --json` 查找会话 key，然后明确指定 `--session-key`。如果知道当前通道，优先加 `--agent`、`--chat-type`、`--peer-id`。

### 日志为空
如果后台日志部分为空，可能是：
- 使用了 `--no-logs` 参数
- OpenClaw 日志文件位置不在默认路径
- 没有权限读取日志文件

### 消息数量为 0
可能是会话还没有任何对话，或者会话 key 不正确。

## 相关命令

```bash
# 列出所有会话
openclaw sessions --all-agents --limit 20

# 查看活跃会话
openclaw sessions --all-agents --active 60

# 查看日志
openclaw logs --limit 100

# 导出会话轨迹
openclaw sessions export-trajectory --session-key "..." --workspace "."
```
