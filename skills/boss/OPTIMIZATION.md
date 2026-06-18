# Boss Skill 优化说明

## 优化日期
2026-06-12

## 优化目标
增强 boss skill 的确定性，确保：
1. **派发规则明确**：每个阶段明确写死要派发给哪个 agent ID
2. **Skill 调用强制**：派发任务时明确指定要调用的 skill

## 优化内容

### 1. 新增 Role Routing 表格（第 85-104 行）

明确定义了 7 个阶段的派发规则：

| 阶段 | 角色 | 派发给 Agent | 调用 Skill |
|------|------|-------------|-----------|
| 1. 需求收集 | Account Executive | `main` 自己执行 | `kefu-ae` |
| 2. 问题目标确认 | AE + Strategy + Creative | `main` 协调 | 无 |
| 3. 资料收集 | Account Executive | `main` 自己执行 | `kefu-ae` |
| 4. 策略制定 | Strategy Director | **`strategy`** | **`celue-zj`** |
| 5. 创意方向 | Creative Director | **`strategy`** | **`chuangyi-zj`** |
| 6. 方向确认 | AE + Strategy + Creative | `main` 协调 | 无 |
| 7a. 文案执行 | Copywriter | **`copywriter`** | **`wenan`** |
| 7b. 设计执行 | Designer | **`design`** 或 **`design-shared`** | **`sheji`** + 执行 skills |

**关键改进**：
- ✅ 明确了每个阶段要派发给哪个 agent ID（不再是模糊的"角色"）
- ✅ 明确了每个阶段要调用哪个 skill
- ✅ 粗体标注必须派发的阶段，防止 `main` 自己兜底执行

### 2. 新增 Dispatch Templates 章节（第 106-166 行）

为每个需要派发的阶段提供了标准模板：

**阶段 4：策略制定**
```json
{
  "runtime": "subagent",
  "agentId": "strategy",
  "task": "【策略制定任务】\n\n**必须使用 celue-zj skill**\n\n**前置信息**：...",
  "mode": "run",
  "timeoutSeconds": 1800,
  "lightContext": true
}
```

**模板特点**：
- ✅ 明确指定 `agentId`（如 `strategy`、`copywriter`、`design`）
- ✅ 在任务描述开头强制写明"**必须使用 XXX skill**"
- ✅ 包含完整的前置信息、任务要求、输出要求
- ✅ 提供了所有必须替换的 `[占位符]`

**涵盖的阶段**：
- 阶段 4：策略制定 → `strategy` agent + `celue-zj` skill
- 阶段 5：创意方向 → `strategy` agent + `chuangyi-zj` skill
- 阶段 7a：文案执行 → `copywriter` agent + `wenan` skill
- 阶段 7b：设计执行 → `design` agent + `sheji` skill + 执行 skills

### 3. 强化 Role Constraints（第 168-189 行）

新增了"**派发约束（强制）**"章节：

**四大禁止**：
- ❌ **禁止跳过派发**：策略、创意、文案、设计阶段必须派发，不得由 `main` 自己执行
- ❌ **禁止省略 skill 指定**：派发时必须明确写明"必须使用 XXX skill"
- ❌ **禁止模糊派发**：不得使用"请制定策略"这种模糊指令，必须使用完整模板
- ❌ **禁止私自兜底**：专家 agent 失败时必须报告用户，不得自行兜底

### 4. 新增派发验证检查点（第 221-250 行）

在 Collaboration Rules 中新增了"**派发验证检查点**"：

**五大验证**：
1. **派发对象验证**：确认要派发给哪个 agent，确认该 agent 可用
2. **Skill 指定验证**：确认该阶段需要调用哪个 skill，在任务描述中明确写明
3. **前置条件验证**：确认前置阶段已完成、产出已确认、资料已收集
4. **上下文传递验证**：确认品牌档案、前置产出路径、具体需求已包含
5. **模板使用验证**：确认使用了标准模板，占位符已替换，超时时间已设置

**派发失败处理**：
- 专家 agent 不可用 → 必须报告用户，建议使用 shared variant
- 专家 agent 返回错误 → 必须报告用户并说明原因，不得重试超过 2 次
- 禁止在专家 agent 失败后由 `main` 自己兜底执行

## 优化前后对比

### 优化前
- ❌ 只定义了"角色"（Strategy Director），没有明确 agent ID
- ❌ 没有派发模板，依赖 `main` 自己决定如何派发
- ❌ 没有强制要求在派发时指定 skill
- ❌ 依赖于 agent 的"自律执行"（通过 AGENTS.md 的 0.1 规则）
- ⚠️ 存在风险：`main` 可能不派发而是自己执行；专家 agent 可能不调用 skill

### 优化后
- ✅ 明确了每个阶段要派发给哪个 agent ID（`strategy`、`copywriter`、`design`）
- ✅ 提供了标准派发模板，包含完整的任务描述结构
- ✅ 强制要求在任务描述开头写明"**必须使用 XXX skill**"
- ✅ 新增了派发验证检查点，确保每次派发都遵循规则
- ✅ 新增了派发约束，明确禁止跳过派发、省略 skill、模糊派发、私自兜底
- ✅ 提供了派发失败处理规则，确保问题能及时暴露给用户

## 机制对比

### 之前的机制（三层自律）
```
boss skill 定义角色
    ↓
main 根据 AGENTS.md 判断是否派发
    ↓
专家 agent 根据 AGENTS.md 0.1 规则查找并调用 skill
```
**风险**：依赖于每个环节的自律执行

### 现在的机制（明确约束 + 自律）
```
boss skill 明确定义 agent ID + skill
    ↓
main 必须使用标准模板派发（包含 "必须使用 XXX skill"）
    ↓
专家 agent 看到明确指令 + 自己的 AGENTS.md 0.1 规则 → 双重保障
```
**优势**：明确约束 + 自律执行的双重保障

## 使用指南

### 1. Main Agent 执行 Boss Skill 时

**步骤**：
1. 读取 boss skill 的 SKILL.md
2. 查看 "Role Routing" 表格，确认当前阶段要派发给哪个 agent
3. 如果需要派发（粗体标注的阶段）：
   - 打开 "Dispatch Templates" 章节
   - 复制对应阶段的模板
   - 替换所有 `[占位符]` 为实际内容
   - 使用 "派发验证检查点" 进行自检
   - 执行派发
4. 如果 `main` 自己执行（阶段 1、2、3、6）：
   - 使用对应的 skill（如 `kefu-ae`）
   - 或协调三方确认（阶段 2、6）

### 2. 专家 Agent 接收任务时

当收到任务描述中包含"**必须使用 XXX skill**"时：
1. 优先读取指定的 skill（如 `celue-zj`、`chuangyi-zj`、`wenan`）
2. 按照 skill 的流程执行
3. 输出结果到指定路径
4. 回传文件绝对路径给 `main`

**双重保障**：
- ✅ 任务描述中的明确指令："必须使用 XXX skill"
- ✅ 自己的 AGENTS.md 0.1 规则："先查 Skill"

### 3. 派发失败时

如果遇到以下情况：
- 专家 agent 不可用（如 `strategy` agent 未启动）
- 专家 agent 返回错误
- 专家 agent 超时

**正确处理**：
- ❌ 不要自己兜底执行
- ❌ 不要重试超过 2 次
- ✅ 报告给用户："[agent] 当前不可用，无法执行 [阶段]，建议稍后重试或使用 [agent]-shared variant"
- ✅ 说明错误原因，让用户决定下一步

## 验证方法

### 验证派发规则是否生效

1. **检查 main agent 是否使用了模板**：
   - 查看派发的任务描述
   - 确认开头有"**必须使用 XXX skill**"
   - 确认包含完整的前置信息、任务要求、输出要求

2. **检查专家 agent 是否调用了 skill**：
   - 查看专家 agent 的执行日志
   - 确认读取了指定的 SKILL.md
   - 确认按照 skill 的流程执行

3. **检查是否有私自兜底**：
   - 如果专家 agent 失败，main 是否报告给用户？
   - 还是 main 自己继续执行了？

### 测试案例

**测试 1：策略制定阶段**
- 输入：品牌全案任务，进入策略制定阶段
- 期望：main 派发给 `strategy` agent，任务描述包含"必须使用 celue-zj skill"
- 验证：strategy agent 读取并执行了 `celue-zj` skill

**测试 2：专家 agent 不可用**
- 输入：品牌全案任务，但 `strategy` agent 未启动
- 期望：main 报告"strategy 当前不可用，无法执行策略制定阶段"
- 验证：main 没有自己执行策略制定

**测试 3：文案执行阶段**
- 输入：创意方向已确认，进入文案执行阶段
- 期望：main 派发给 `copywriter` agent，任务描述包含"必须使用 wenan skill"
- 验证：copywriter agent 读取并执行了 `wenan` skill

## 相关文件

- `/Users/a123/.openclaw/skills/boss/SKILL.md` - Boss skill 主文件（已优化）
- `/Users/a123/.openclaw/workspace/AGENTS.md` - Main agent 执行规则
- `/Users/a123/.openclaw/workspace-strategy/AGENTS.md` - Strategy agent 执行规则
- `/Users/a123/.openclaw/workspace-copywriter/AGENTS.md` - Copywriter agent 执行规则
- `/Users/a123/.openclaw/workspace-design/AGENTS.md` - Design agent 执行规则
- `/Users/a123/.openclaw/广告营销任务路由规则.md` - 广告营销任务路由规则

## 后续改进建议

### 短期（可选）
1. **增加派发日志**：在 main agent 派发时记录派发决策和使用的模板
2. **增加 skill 调用验证**：在专家 agent 完成任务后，验证是否确实调用了指定的 skill

### 长期（可选）
1. **自动化验证**：开发脚本自动检查派发是否符合 boss skill 的规则
2. **派发监控**：统计派发成功率、失败原因、兜底次数
3. **模板生成器**：提供工具自动生成符合标准的派发任务描述

## 总结

这次优化通过"明确约束 + 自律执行"的双重保障机制，大幅增强了 boss skill 的确定性：

**核心改进**：
- ✅ 派发规则从"角色"升级为"agent ID"，消除了 main 的判断空间
- ✅ 提供了标准派发模板，确保每次派发都包含 skill 指定
- ✅ 新增了派发约束和验证检查点，防止跳过派发或私自兜底
- ✅ 明确了派发失败处理规则，确保问题能及时暴露

**预期效果**：
- 🎯 每个阶段的执行路径清晰可预测
- 🎯 专家 agent 一定会调用对应的 skill
- 🎯 派发失败能及时暴露，不会被掩盖
- 🎯 用户对整个流程有更强的掌控感
