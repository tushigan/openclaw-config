# Boss Skill 话题错位修复测试计划

## 修复内容总结

### 1. Boss Skill 派发模板更新
- ✅ 增加"交付模式"说明（静默回传 / 混合模式）
- ✅ 明确禁止 subagent 直接投送大段文字内容
- ✅ 要求 subagent 只回传路径和简短摘要
- ✅ 增加 Main 接收结果后的标准处理流程

### 2. 各专家 Agent AGENTS.md 更新
- ✅ strategy: 增加 subagent 静默交付规则
- ✅ copywriter: 增加 subagent 静默交付规则
- ✅ design: 增加 subagent 混合模式交付规则（图片可直接发送，文字说明简短）

### 3. 错误排查指南
- ✅ 增加常见派发错误排查步骤
- ✅ 增加调试命令参考

## 测试场景

### 测试 1：策略制定阶段（静默回传）

**前置条件**：
- 在飞书话题群中触发 Boss Skill
- 进入策略制定阶段（阶段 4）

**测试步骤**：
1. Main agent 派发策略任务给 strategy agent
2. Strategy agent 完成后只回传路径和摘要（不直接投送）
3. Main agent 在原话题下读取策略文档并转发给用户

**预期结果**：
- ✅ Strategy agent 的反馈**不创建新话题**
- ✅ Main agent 在原话题下投送策略内容
- ✅ 所有消息在同一个话题下连续展示

### 测试 2：创意方向阶段（静默回传）

**前置条件**：
- 策略已完成并确认
- 进入创意方向阶段（阶段 5）

**测试步骤**：
1. Main agent 派发创意方向任务给 strategy agent
2. Strategy agent 完成后只回传路径和摘要
3. Main agent 在原话题下转发创意方向

**预期结果**：
- ✅ Strategy agent 的反馈**不创建新话题**
- ✅ Main agent 在原话题下投送创意方向内容
- ✅ 所有消息在同一个话题下连续展示

### 测试 3：文案执行阶段（静默回传）

**前置条件**：
- 创意方向已完成并确认
- 进入文案执行阶段（阶段 7a）

**测试步骤**：
1. Main agent 派发文案任务给 copywriter agent
2. Copywriter agent 完成后只回传路径和版本摘要
3. Main agent 在原话题下转发文案内容

**预期结果**：
- ✅ Copywriter agent 的反馈**不创建新话题**
- ✅ Main agent 在原话题下投送文案内容
- ✅ 所有消息在同一个话题下连续展示

### 测试 4：设计执行阶段（混合模式）

**前置条件**：
- 文案已完成并确认
- 进入设计执行阶段（阶段 7b）

**测试步骤**：
1. Main agent 派发设计任务给 design agent
2. Design agent 生成图片后直接发送图片（带简短说明1-2句）
3. Design agent 回传路径给 main
4. Main agent 在原话题下补充详细设计说明

**预期结果**：
- ✅ Design agent 发送的图片**在原话题下显示**（不创建新话题）
- ✅ Main agent 的详细说明也在原话题下
- ✅ 所有消息在同一个话题下连续展示

### 测试 5：并行项目测试

**前置条件**：
- 在同一个飞书话题群中
- 创建两个不同的话题运行两个项目

**测试步骤**：
1. 话题 A：小白心里软 TVC 项目
2. 话题 B：阿嫲秘诀产品卖点项目
3. 两个项目同时进行，各自派发 subagent

**预期结果**：
- ✅ 话题 A 的所有消息（包括 subagent 反馈）都在话题 A 下
- ✅ 话题 B 的所有消息（包括 subagent 反馈）都在话题 B 下
- ✅ 两个话题互不干扰
- ✅ 没有创建新的话题

## 回归测试

### 测试 6：直连会话（非 subagent 模式）

**测试步骤**：
1. 用户直接与 strategy agent 对话（不通过 main 派发）
2. 请求策略制定

**预期结果**：
- ✅ Strategy agent 正常直接投送完整策略内容
- ✅ 交付行为与之前一致（不受 subagent 规则影响）

### 测试 7：非话题群场景

**测试步骤**：
1. 在普通飞书群聊（非话题群）中触发 Boss Skill
2. 派发 subagent 任务

**预期结果**：
- ✅ 消息正常投送到群聊
- ✅ 没有创建话题（因为不是话题群）
- ✅ Main agent 正常接收和转发 subagent 结果

## 错误场景测试

### 测试 8：Subagent 执行失败

**测试步骤**：
1. 派发策略任务但 strategy agent 不可用
2. 或 strategy agent 执行过程中出错

**预期结果**：
- ✅ Main agent 在原话题下报告错误
- ✅ 提供清晰的错误原因和建议
- ✅ 不尝试自己兜底执行策略

### 测试 9：Skill 调用失败

**测试步骤**：
1. 派发任务但指定的 skill 不存在或执行失败
2. 例如：celue-zj skill 路径错误

**预期结果**：
- ✅ Subagent 报告 skill 调用失败
- ✅ Main agent 在原话题下转发错误信息
- ✅ 提供调试建议（检查 skill 路径、权限等）

## 验证检查清单

运行完整测试后，验证以下要点：

- [ ] 所有 subagent 的反馈都通过 main 转发，没有直接投送大段内容
- [ ] 飞书话题群中所有消息都在原话题下，没有创建新话题
- [ ] 图片投送正常（design agent 可以直接发送图片）
- [ ] 文字内容由 main 统一转发
- [ ] 并行项目的消息不会串话题
- [ ] 直连会话不受影响
- [ ] 错误处理清晰，在原话题下报告

## 推荐测试顺序

1. **先做简单场景**：测试 1（策略制定）→ 确认基本修复有效
2. **再做完整流程**：测试 1-4 连续执行 → 验证完整工作流
3. **并行压力测试**：测试 5 → 验证多项目隔离
4. **回归测试**：测试 6-7 → 确保没有破坏现有功能
5. **错误场景**：测试 8-9 → 验证错误处理

## 测试记录模板

```markdown
### 测试日期：2026-06-12

#### 测试 1：策略制定阶段
- 执行时间：__:__
- 话题 ID：omt_xxx
- 结果：✅ / ❌
- 备注：

#### 测试 2：创意方向阶段
- 执行时间：__:__
- 话题 ID：omt_xxx
- 结果：✅ / ❌
- 备注：

[继续记录其他测试...]
```

## 如果测试失败

1. **查看 gateway 日志**：
   ```bash
   openclaw logs | grep -i "topic\|thread\|subagent" | tail -50
   ```

2. **查看 subagent session**：
   ```bash
   ls -lt agents/[agent-name]/sessions/ | head -5
   cat agents/[agent-name]/sessions/[最新session].jsonl | jq 'select(.type=="message")'
   ```

3. **检查 main session**：
   ```bash
   ls -lt agents/main-shared/sessions/*topic-omt_*.jsonl | head -5
   ```

4. **验证修复内容是否生效**：
   - 检查 Boss SKILL.md 的派发模板是否包含"交付模式"说明
   - 检查各 agent 的 AGENTS.md 是否包含 subagent 交付规则
   - 检查 subagent 任务描述中是否包含"静默回传"或"混合模式"标记

---

**修复完成时间**：2026-06-12
**测试负责人**：待定
**测试状态**：待测试
