# Boss Skill 飞书话题修复 - CLI 测试方案

## 测试目标
验证修复后的 Boss Skill 在飞书话题群中是否正确投送消息（不创建新话题）

## 测试环境
- 群组ID: `oc_deb2956a37fa31823df419ab084a073f`
- 测试话题ID: `omt_194eeb1ac88e9bb4`（小白心里软 TVC 话题，可复用）
- 渠道: `feishu`

## 测试步骤

### 阶段 1: 基础消息投送测试
验证 CLI 能否正确向指定话题发送消息

```bash
openclaw message send \
  --channel feishu \
  --target oc_deb2956a37fa31823df419ab084a073f \
  --thread-id omt_194eeb1ac88e9bb4 \
  --message "【测试消息】Boss Skill 话题修复验证 - 基础投送测试" \
  --json
```

**期望结果**: 消息出现在 `omt_194eeb1ac88e9bb4` 话题下，不创建新话题

### 阶段 2: 模拟 Main Agent 投送测试
模拟 main agent 在原话题下转发 subagent 结果

```bash
openclaw message send \
  --channel feishu \
  --target oc_deb2956a37fa31823df419ab084a073f \
  --thread-id omt_194eeb1ac88e9bb4 \
  --message "【测试】模拟 main agent 转发策略结果

策略文档已生成：workspace-strategy/outputs/strategy_20260612_test.md

核心摘要：
1. 品牌定位：xxx
2. 目标受众：xxx
3. 传播策略：xxx

---
本消息模拟 main agent 在原话题下转发 subagent 静默回传的结果" \
  --json
```

**期望结果**: 消息出现在同一话题下

### 阶段 3: 完整 Boss Skill 流程测试（需要用户触发）
这个阶段需要用户在飞书中实际触发，因为涉及 subagent 派发和完整工作流

**测试指令**（用户在飞书话题中发送）:
```
@虾指挥 用 boss skill 做一个测试项目：某品牌新品发布会策划
```

**观察点**:
1. main agent 的消息是否在原话题下
2. strategy subagent 的结果是否由 main 转发（而不是 subagent 直接发送）
3. copywriter subagent 的结果是否由 main 转发
4. design subagent 的图片是否直接发送（混合模式允许）
5. 整个流程中是否有新话题被创建

## 测试记录

### 测试 1: 基础投送
- 执行时间: 2026-06-12 12:35:42
- 结果: ✅ 成功发送
- 消息ID: `om_x100b6d8c8904b8a0b24feec4f469a78`
- 话题ID确认: 指定 `--thread-id omt_194eeb1ac88e9bb4`，API 返回成功

### 测试 2: 模拟转发
- 执行时间: 2026-06-12 12:35:51
- 结果: ✅ 成功发送
- 消息ID: `om_x100b6d8c8609fcb4b1fee8e93d9e973`
- 话题ID确认: 指定 `--thread-id omt_194eeb1ac88e9bb4`，API 返回成功

### 测试 3: 完整流程（待用户执行）
- 执行时间: 待用户在飞书中触发
- 是否创建新话题: 待验证
- Main 投送正常: 待验证
- Strategy 静默回传: 待验证
- Copywriter 静默回传: 待验证
- Design 混合模式: 待验证 

## 成功标准
- ✅ CLI 消息正确投送到指定话题
- ✅ 模拟转发消息在同一话题下
- ✅ 完整流程无新话题创建
- ✅ Subagent 结果由 main 转发
- ✅ 用户体验连贯（所有消息在同一话题线程下）
