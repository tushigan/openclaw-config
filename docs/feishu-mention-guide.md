# 飞书真实艾特功能 - 使用指南

## 问题背景

在飞书流式卡片输出模式下，agent 直接输出 `@张三` 这样的文本**不会触发真实的艾特通知**，用户不会收到提醒。

## 解决方案

使用 `feishu-mention-helper` skill，让 agent 能够查询用户的 open_id 并生成正确的艾特标签。

## 快速开始

### 示例 1：艾特单个用户

当你需要在群里艾特某人时：

```markdown
我需要先查询一下张三的艾特标签。

[调用工具]
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "张三" --json

[根据返回结果，使用 mentionTag]
<at id=ou_cd6cc762e35c0640414d33335a183a67></at> 你好，请帮忙处理一下这个任务。
```

### 示例 2：查看可艾特的用户

```markdown
让我先看看最近活跃的用户有哪些。

[调用工具]
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --list --limit 10 --json

[根据返回的用户列表，选择需要艾特的人]
```

### 示例 3：艾特多个用户

```markdown
我需要艾特张三和李四。

[先查询张三]
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "张三" --json

[再查询李四]
exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "李四" --json

[同时艾特两人]
<at id=ou_xxx></at> <at id=ou_yyy></at> 请两位一起讨论一下这个方案。
```

## 核心原理

### 艾特标签格式

飞书流式卡片中的真实艾特格式：
```
<at id=ou_用户的open_id></at>
```

### 错误示例 ❌

以下方式都**不会触发真实艾特**：
- `@张三`
- `@ou_xxx`
- `<at>张三</at>`
- `[@张三](user:ou_xxx)`

### 正确示例 ✅

```
<at id=ou_cd6cc762e35c0640414d33335a183a67></at>
```

## 工具返回格式

```json
{
  "ok": true,
  "count": 1,
  "users": [
    {
      "openId": "ou_cd6cc762e35c0640414d33335a183a67",
      "name": "张三",
      "accountId": "main",
      "mentionTag": "<at id=ou_cd6cc762e35c0640414d33335a183a67></at>"
    }
  ]
}
```

**关键字段**：
- `mentionTag`: 直接使用此字段，无需修改
- `openId`: 用户的飞书 open_id
- `name`: 用户名

## Agent 工作流程

1. **用户请求艾特某人**
2. **Agent 调用查询工具**：`exec python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "用户名" --json`
3. **解析返回的 JSON**：提取 `mentionTag` 字段
4. **在回复中使用艾特标签**：直接插入 `mentionTag` 的值
5. **保持流式输出**：艾特标签会在流式卡片中正常渲染

## 注意事项

1. ✅ **艾特标签必须在最终输出的文本中**，不能只在工具调用日志里
2. ✅ **直接使用 mentionTag 字段**，不要自己拼接
3. ✅ **支持模糊匹配**：搜 "张" 可以找到 "张三"
4. ✅ **处理同名用户**：如果返回多个结果，选择 `lastSeenAt` 最近的，或根据 `accountId` 匹配当前会话
5. ✅ **流式输出不受影响**：艾特标签会随文本流式渲染

## 测试验证

### 手动测试

```bash
# 测试查询功能
python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "涂是淦"

# 测试 JSON 输出
python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --name "涂是淦" --json

# 列出最近用户
python3 /Users/a123/.openclaw/scripts/feishu-mention-helper.py --list --limit 5
```

### Agent 测试

在飞书中向 agent 发送：

```
在群里艾特一下张三，提醒他查看最新的项目进展。
```

**预期行为**：
1. Agent 先调用查询工具
2. Agent 在回复中使用正确的艾特标签
3. 张三收到飞书艾特通知

## 配置位置

- **Skill 文档**：`/Users/a123/.openclaw/skills/feishu-mention-helper/SKILL.md`
- **查询脚本**：`/Users/a123/.openclaw/scripts/feishu-mention-helper.py`
- **数据来源**：`/Users/a123/.openclaw/feishu/conversation-ids.json`
- **已添加到**：`agents.defaults.skills` 和 `main` agent

## 更新数据

用户注册表会自动维护，也可以手动更新：

```bash
# 扫描最近 14 天的会话
python3 /Users/a123/.openclaw/scripts/feishu-id-registry.py scan --json
```

## 相关文档

- Skill 详细文档：`skills/feishu-mention-helper/SKILL.md`
- 飞书扩展源码：`extensions/openclaw-lark/src/messaging/inbound/mention.js`
- ID 注册表脚本：`scripts/feishu-id-registry.py`
