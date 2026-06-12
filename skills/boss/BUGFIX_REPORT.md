# Boss Skill 话题错位问题诊断报告

## 问题描述

用户在飞书话题群中使用 Boss Skill 时，发现：
1. **Main agent 的消息**正确投送到原话题下
2. **Subagent 派发的任务反馈**会自动新建话题，导致消息混乱

## 问题定位

### 实际案例

**测试项目**：
- 小白心里软 TVC：Topic ID `omt_194eeb1ac88e9bb4`
- 阿嫲秘诀产品卖点：Topic ID `omt_194efcd8430f5be3`

**Session 文件证据**：
- Main agent session: `b6619f35-4b63-4d57-9677-1816add3395a-topic-omt_194eeb1ac88e9bb4.jsonl`
- Strategy subagent session: `0c24f23f-8292-4aa3-8a83-57600dd328a2-topic-omt_194eeb1ac88e9bb4.jsonl`

从 session 文件名可以看出，**subagent 已经继承了 topic ID**，但消息投送时创建了新话题。

### 根本原因

查看实际的 `sessions_spawn` 调用（来自 main-shared session 日志）：

```json
{
  "runtime": "subagent",
  "agentId": "strategy-shared",
  "task": "【策略制定任务】...",
  "mode": "run",
  "timeoutSeconds": 1800,
  "lightContext": true
}
```

**关键缺失**：派发时没有传递任何话题/消息投送目标信息。

OpenClaw 虽然会自动在 subagent 的 session key 中包含 topic ID（从文件名可以看出），但 subagent 完成后的消息投送**没有明确指定回到原话题**。

## 解决方案

### 方案 A：在 sessions_spawn 中传递投送目标

OpenClaw 的 subagent 机制可能支持以下参数（需要验证）：
- `deliveryTarget`: 指定消息投送目标
- `parentThreadId`: 继承父会话的 thread ID
- `replyContext`: 保持回复上下文

### 方案 B：使用 runtime="acp" 替代 runtime="subagent"

根据 AGENTS.md：
- `runtime="subagent"`: **不能传 `streamTo`**
- `runtime="acp"`: **可以传 `streamTo`**，不能传 `lightContext`

如果 ACP runtime 支持明确的消息投送目标，可以切换到 ACP 模式。

### 方案 C：Subagent 完成后由 main 转发

让 subagent 的结果不直接投送给用户，而是：
1. Subagent 完成后只回传给 main（已有机制）
2. Main 接收到结果后，在原话题下转发给用户

**这是最稳妥的方案**，因为 main 已经在正确的话题上下文中。

## 推荐方案：方案 C（Main 转发模式）

### 修改点

1. **Boss Skill 派发模板**增加"静默模式"说明：
   - Subagent 产出后**不要直接投送给最终用户**
   - 只回传文件路径和核心摘要给 main
   - 由 main 在原话题下汇总交付

2. **Subagent AGENTS.md 明确交付规则**：
   - 当前是 subagent 上下文时，产出写入文件，回传路径
   - 不使用 `message` 工具直接投送（会创建新话题）

3. **Main 接收 subagent 结果后的标准流程**：
   - 读取 subagent 产出文件
   - 提取关键内容
   - 在原话题下用 `message` 工具投送给用户
   - 可选：附加产出文件

## 实施步骤

1. ✅ 诊断问题（已完成）
2. ⬜ 修改 Boss Skill 派发模板，增加"静默交付"指令
3. ⬜ 更新 strategy/copywriter/design AGENTS.md，明确 subagent 交付规则
4. ⬜ 测试验证：重跑小白 TVC 或阿嫲秘诀项目
5. ⬜ 确认消息全部投送到原话题

## 次要问题：Subagent 派发错误

用户还提到"执行 subagent 任务派发的时候经常会出现一些错误"。

**需要排查的错误类型**：
1. Subagent 启动失败
2. Subagent 执行超时
3. Skill 调用失败
4. 文件路径访问权限问题

**排查方法**：
1. 查看 gateway 日志：`openclaw logs | grep -i error`
2. 查看 subagent session 的错误消息
3. 检查 exec-approvals.json 中对应 agent 的权限配置
4. 验证 skill 路径是否正确

---

**生成时间**：2026-06-12
**作者**：Claude (Kiro)
**状态**：待实施修复
