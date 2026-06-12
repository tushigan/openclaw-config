# Boss Skill 飞书话题群消息错位修复总结

## 📋 问题回顾

### 用户报告的问题
1. **话题错位问题**：在飞书话题群中使用 Boss Skill 时，Main agent 的消息正确投送到原话题下，但 Subagent 派发任务的反馈会自动新建话题，导致消息混乱
2. **Subagent 派发错误**：执行 subagent 任务派发时经常出现错误

### 实际测试案例
- **小白心里软 TVC 项目**：Topic ID `omt_194eeb1ac88e9bb4`
- **阿嫲秘诀产品卖点项目**：Topic ID `omt_194efcd8430f5be3`

## 🔍 根本原因分析

### 话题错位根源
1. **Subagent 会话确实继承了 topic ID**（从 session 文件名可以看出）
2. **但 subagent 使用 `message` 工具直接投送大段内容时**，OpenClaw gateway 会创建新话题而非回复到原话题
3. **Main agent 的消息正常**是因为它始终在原话题的会话上下文中

### 为什么会创建新话题
根据 AGENTS.md 的规则：
- `runtime="subagent"` **不能传 `streamTo`**
- Subagent 完成后的消息投送没有明确的话题上下文
- 飞书 gateway 默认行为是创建新话题

## ✅ 解决方案

### 采用方案：Main 转发模式（方案 C）

**核心思路**：
- Subagent **不直接投送**大段内容给最终用户
- Subagent 只回传**文件路径 + 简短摘要**给 Main
- Main 在原话题下**读取产出并转发**给用户

### 为什么选择这个方案
- ✅ Main 始终在正确的话题上下文中
- ✅ 用户体验连贯（所有消息在同一话题下）
- ✅ Main 可以过滤和格式化 subagent 的产出
- ✅ 不依赖 OpenClaw 底层修改（稳定可靠）

## 🛠️ 具体修改内容

### 1. Boss Skill 派发模板更新

**文件**：`skills/boss/SKILL.md`

**修改点**：
- 在每个派发模板中增加「**交付模式：静默回传**」说明
- 明确指示 subagent：
  - ✅ 将产出写入文件
  - ✅ 回传文件路径 + 核心摘要（3-5 句话）
  - ❌ **禁止**使用 `message` 工具直接投送大段内容
  - ❌ **禁止**发送完整文档（会创建新话题）

**示例（策略制定阶段）**：
```json
{
  "runtime": "subagent",
  "agentId": "strategy",
  "task": "【策略制定任务】\n\n**必须使用 celue-zj skill**\n\n**交付模式：静默回传**\n你是被 main agent 派发的 subagent。完成后：\n- ✅ 将策略文档写入 workspace-strategy/outputs/\n- ✅ 回传文件绝对路径和核心摘要（3-5 句话）\n- ❌ 不要使用 message 工具直接投送给最终用户\n- ❌ 不要发送完整策略内容（会创建新话题）\n由 main 负责在原话题下转发给用户。\n\n...",
  "mode": "run",
  "timeoutSeconds": 1800,
  "lightContext": true
}
```

**设计阶段例外**：
- 设计阶段使用「**交付模式：混合模式**」
- 图片可以直接发送（飞书支持图片直接投送）
- 但文字说明保持简短（1-2 句话），详细说明由 Main 转发

### 2. Main 接收结果后的标准流程

新增章节「Main 接收 subagent 结果后的标准流程」：

1. **等待 subagent 完成**：接收路径和摘要
2. **读取并验证产出**：确认文件存在且内容完整
3. **在原话题下转发给用户**：提取关键内容投送
4. **格式化交付内容**：使用统一格式
5. **等待用户确认后进入下一阶段**

### 3. 各专家 Agent AGENTS.md 更新

#### Strategy Agent (`workspace-strategy/AGENTS.md`)
在「2.1 交付标准」章节增加：

```markdown
**⚠️ 飞书话题群 Subagent 模式交付规则**：
- **当你是被 main 派发的 subagent 时**（任务描述中包含"交付模式：静默回传"）：
  - ✅ 将产出写入 `outputs/` 或 `images/`
  - ✅ 回传文件绝对路径 + 核心摘要（3-5 句话）
  - ❌ **禁止**使用 `message` 工具直接投送大段文字内容给最终用户
  - ❌ **禁止**发送完整策略/创意方向文档（会在飞书创建新话题，导致消息混乱）
  - 📌 由 main agent 负责在原话题下读取你的产出并转发给用户
```

#### Copywriter Agent (`workspace-copywriter/AGENTS.md`)
同样增加 Subagent 静默交付规则

#### Design Agent (`workspace-design/AGENTS.md`)
增加 Subagent 混合模式交付规则：
- 图片可以直接发送（使用 `message` 工具的 `path` 参数）
- 文字说明保持简短（1-2 句话）
- 详细设计说明由 Main 转发

### 4. 错误排查指南

新增「常见派发错误排查」章节，包括：
1. **Subagent 启动失败**：检查 agent ID、权限配置、gateway 日志
2. **Subagent 执行超时**：检查 timeout 设置、查看 session 日志
3. **Skill 调用失败**：确认 skill 路径、权限、SKILL.md 完整性
4. **文件路径访问权限问题**：使用绝对路径、确认目录权限
5. **消息投送到错误话题**：确认 subagent 没有直接投送大段内容

提供调试命令：
```bash
# 查看错误日志
openclaw logs | grep -i "error\|fail" | tail -20

# 查看 agent session
ls -lt agents/[agent-name]/sessions/ | head -5

# 检查 skill 可用性
available_skills | grep [skill-name]
```

## 📊 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `skills/boss/SKILL.md` | 修改 | 更新派发模板、增加 Main 转发流程、错误排查指南 |
| `workspace-strategy/AGENTS.md` | 修改 | 增加 Subagent 静默交付规则 |
| `workspace-copywriter/AGENTS.md` | 修改 | 增加 Subagent 静默交付规则 |
| `workspace-design/AGENTS.md` | 修改 | 增加 Subagent 混合模式交付规则 |
| `skills/boss/BUGFIX_REPORT.md` | 新增 | 完整问题诊断报告 |
| `skills/boss/TEST_TOPIC_FIX.md` | 新增 | 测试计划（9 个测试场景）|
| `skills/boss/FIX_SUMMARY.md` | 新增 | 修复总结（本文件）|

## 🧪 测试计划

已创建完整测试计划（`TEST_TOPIC_FIX.md`），包括：

### 核心功能测试
1. **测试 1**：策略制定阶段（静默回传）
2. **测试 2**：创意方向阶段（静默回传）
3. **测试 3**：文案执行阶段（静默回传）
4. **测试 4**：设计执行阶段（混合模式）
5. **测试 5**：并行项目测试（话题隔离）

### 回归测试
6. **测试 6**：直连会话（非 subagent 模式）
7. **测试 7**：非话题群场景

### 错误场景测试
8. **测试 8**：Subagent 执行失败
9. **测试 9**：Skill 调用失败

## ✨ 预期效果

修复后的体验：

### ✅ 话题连贯性
```
飞书话题群 > 话题 A：小白心里软 TVC
├── 用户：开始 Boss Skill
├── Main：收到，建立项目
├── 用户：确认进入策略阶段
├── Main：派发策略任务...
├── Main：✅ 策略制定已完成（从 strategy 接收并转发）
│   ├── 核心内容摘要
│   └── 📄 完整文档路径
├── 用户：确认策略
├── Main：派发创意方向任务...
├── Main：✅ 创意方向已完成（从 strategy 接收并转发）
└── ...（所有消息都在话题 A 下）
```

### ❌ 修复前的问题
```
飞书话题群 > 话题 A：小白心里软 TVC
├── 用户：开始 Boss Skill
├── Main：收到，建立项目
├── 用户：确认进入策略阶段
├── Main：派发策略任务...

飞书话题群 > 话题 B：【自动创建】❌
└── Strategy Agent：策略制定完成（错误投送到新话题）

飞书话题群 > 话题 A：小白心里软 TVC
└── Main：等待 strategy 反馈...（用户困惑：消息去哪了？）
```

## 🚀 下一步行动

### 立即执行
1. ✅ **已完成**：修改代码并提交到 Git
2. ⬜ **待执行**：在飞书话题群中重新测试 Boss Skill
   - 选择之前的测试项目（小白 TVC 或阿嫲秘诀）
   - 完整运行一个流程，确认消息不再错位

### 验证要点
- [ ] Main agent 的消息在原话题下 ✓
- [ ] Subagent 的反馈通过 Main 转发，在原话题下 ✓
- [ ] 没有自动创建新话题 ✓
- [ ] 并行项目的消息不串话题 ✓
- [ ] 图片投送正常（design agent）✓
- [ ] 错误处理清晰（如果发生错误）✓

### 如果测试成功
- 记录测试结果到 `TEST_TOPIC_FIX.md`
- 标记修复为「已验证」
- 更新 MEMORY.md 记录修复经验

### 如果测试失败
1. 查看 gateway 日志：`openclaw logs | grep -i "topic\|thread\|subagent"`
2. 查看 subagent session 日志
3. 检查任务描述中是否包含「交付模式」标记
4. 验证 subagent 是否仍然直接投送大段内容
5. 根据实际情况调整修复方案

## 📝 关键设计决策

### 为什么不修改 OpenClaw 底层？
- ✅ **稳定性**：不依赖 OpenClaw 版本更新
- ✅ **可维护性**：问题在应用层解决，容易理解和调试
- ✅ **快速部署**：只需更新配置文件，无需重启 gateway

### 为什么设计阶段使用混合模式？
- 图片文件可以直接投送（飞书支持）
- 图片投送不会创建新话题（已验证）
- 保持用户体验流畅（图片即时可见）
- 文字说明简短，避免触发新话题创建

### 为什么要求 Main 转发而不是 Subagent 直接发送？
- **话题上下文控制**：Main 始终在正确的话题中
- **内容质量控制**：Main 可以格式化和过滤内容
- **统一交付体验**：所有阶段的交付格式一致
- **错误处理统一**：Main 统一处理所有错误情况

## 🎯 修复目标达成情况

| 目标 | 状态 | 说明 |
|------|------|------|
| 修复话题错位问题 | ✅ 已完成 | 所有消息通过 Main 转发到原话题 |
| 增加错误排查指南 | ✅ 已完成 | 提供调试命令和常见错误处理 |
| 更新派发模板 | ✅ 已完成 | 所有阶段增加交付模式说明 |
| 更新专家 Agent 规则 | ✅ 已完成 | Strategy/Copywriter/Design 都已更新 |
| 创建测试计划 | ✅ 已完成 | 9 个测试场景覆盖核心功能和边界情况 |
| 实际测试验证 | ⬜ 待执行 | 需要在飞书话题群中实际运行 |

---

**修复完成时间**：2026-06-12  
**Git 提交**：5de0f5de  
**修复状态**：已实施，待测试验证  
**作者**：Claude (Kiro)
