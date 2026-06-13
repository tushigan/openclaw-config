# 飞书真实艾特助手

## 功能说明

在飞书流式卡片输出中生成**真实的艾特标签**，触发飞书的艾特通知功能。

## 核心能力

1. **按名字查询用户**：支持模糊匹配，返回用户的 open_id 和艾特标签
2. **列出最近活跃用户**：快速查看可艾特的用户列表
3. **生成正确的艾特格式**：自动生成 `<at id=ou_xxx></at>` 格式

## 使用场景

当你需要在飞书群里艾特某人时：

### ❌ 错误做法（假艾特）
```
@张三 请帮忙处理一下这个问题
```
这样输出的只是纯文本，不会触发飞书的艾特通知。

### ✅ 正确做法（真艾特）
```bash
# 1. 先查询用户的艾特标签
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "张三" --json
```

返回示例：
```json
{
  "ok": true,
  "count": 1,
  "users": [
    {
      "openId": "ou_xxx",
      "name": "张三",
      "mentionTag": "<at id=ou_xxx></at>"
    }
  ]
}
```

```markdown
# 2. 在输出中使用返回的 mentionTag
<at id=ou_xxx></at> 请帮忙处理一下这个问题
```

这样输出的艾特会触发飞书通知，用户会收到真正的艾特提醒。

## 工作流程

### 场景 1: 艾特特定用户

```bash
# 查询用户
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "张三" --json

# 解析返回的 JSON，提取 mentionTag
# 在回复中使用：
<at id=ou_xxx></at> 你好，请查看这个任务
```

### 场景 2: 查看可艾特的用户列表

```bash
# 列出最近活跃的 10 个用户
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --list --limit 10 --json
```

### 场景 3: 艾特多个用户

```bash
# 查询第一个用户
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "张三" --json

# 查询第二个用户
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "李四" --json

# 在回复中同时艾特多人：
<at id=ou_xxx></at> <at id=ou_yyy></at> 请两位一起讨论一下
```

## 命令参考

### 按名字查询
```bash
python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "用户名" --json
```

### 按 open_id 查询
```bash
python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --open-id "ou_xxx" --json
```

### 列出用户
```bash
python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --list --limit 20 --json
```

## 返回格式

所有查询都返回 JSON 格式：

```json
{
  "ok": true,
  "count": 1,
  "users": [
    {
      "openId": "ou_xxx",
      "name": "张三",
      "accountId": "main",
      "target": "user:ou_xxx",
      "lastSeenAt": "2026-06-13T08:50:57.713Z",
      "mentionTag": "<at id=ou_xxx></at>"
    }
  ]
}
```

**关键字段**：
- `mentionTag`: 直接使用这个字段的值，就是正确的艾特格式
- `openId`: 用户的飞书 open_id
- `name`: 用户名
- `lastSeenAt`: 最近活跃时间

## 注意事项

1. **必须使用 mentionTag 字段**：不要自己拼接，直接用返回的 `mentionTag` 值
2. **艾特标签必须在流式卡片内容中**：不能只在思考或工具调用中提及
3. **支持模糊匹配**：名字不需要完全匹配，比如搜 "张" 可以找到 "张三"
4. **同名用户处理**：如果返回多个结果，根据 `accountId` 和 `lastSeenAt` 选择最合适的
5. **保持流式输出格式**：艾特标签会在卡片中正常渲染，不影响流式输出效果

## 典型错误示例

### ❌ 错误 1: 自己拼接格式
```markdown
@张三 或 @ou_xxx
```
这些都不会触发艾特。

### ❌ 错误 2: 没有查询直接艾特
```markdown
<at id=ou_假设的id></at> 
```
ID 错误不会触发艾特。

### ✅ 正确做法
```bash
# 先查询
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "张三" --json

# 使用返回的 mentionTag
<at id=ou_cd6cc762e35c0640414d33335a183a67></at> 你好
```

## 数据来源

用户数据来自飞书 ID 注册表：`/Users/a123/.openclaw/feishu/conversation-ids.json`

该注册表通过扫描历史会话自动维护，包含所有与 OpenClaw 互动过的飞书用户。

## 快速测试

```bash
# 测试查询功能（非 JSON 输出，方便阅读）
python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "涂是淦"

# 测试列出用户
python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --list --limit 5
```
