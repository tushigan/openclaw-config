# dreamina-reference-video Skill 优化计划

基于 2026-05-27 14:47 开始的完整测试流程分析

## 测试过程回顾

**测试起点：** 14:47 用户说"dreamina-reference-video 根据这个Skill的流程继续走@生图高手 不要遗漏任何步骤"

**测试流程：**
1. ✅ preflight - 检查通过
2. ✅ prepare - 创建项目和运行目录
3. ✅ generate-refs - 生成参考图（original + storyboard）
4. ❌ **图片发送问题** - agent 多次未能成功发送图片给用户
5. ✅ 用户确认后继续
6. ❌ **final_frame_poster 污染问题** - 用户发现生成了不必要的 original
7. ✅ 重新执行流程
8. ✅ submit-video - 提交视频任务
9. ✅ fetch-result - 获取视频结果

## 发现的问题

### 问题 1：图片发送失败（已修复）
**时间：** 15:03 - 15:09
**现象：** 
- 用户说"图片发上来我看一下，我要确认一下"
- Agent 多次尝试发送，但用户只收到链接地址，没有收到图片
- 用户说"没收到图片"、"还是只收到了链接地址，没有收到图片"

**根本原因：** AGENTS.md 没有明确说明如何使用 message 工具发送图片

**修复状态：** ✅ 已在本次会话中修复（commit 7d12203e）

---

### 问题 2：final_frame_poster 污染问题（已修复）
**时间：** 15:09
**现象：**
- 用户说"我明明已经给了明确的尾帧定版图了，它还是会自己生成一个原图参考出来，这个环节是不是有一定的问题？这会对后续造成污染吧？"

**根本原因：** workflow.py 没有在用户提供 final_frame_poster 时自动复用为 original

**修复状态：** ✅ 已在本次会话中修复（commit e781a77b）

---

### 问题 3：Agent 执行流程不够自主
**时间：** 整个测试过程
**现象：**
- Agent 在 14:48 执行 prepare 后，没有自动继续执行 generate-refs
- Agent 在 14:49 执行 generate-refs 后，没有主动汇报进度
- 用户需要多次催促："检查进度"、"图片发上来我看一下"
- Agent 在 14:55 才主动给出阶段汇报

**问题分析：**
- Skill 流程定义了步骤，但没有明确 agent 应该自主推进还是等待用户确认
- Agent 在长时间任务（生成图片）时，没有主动汇报进度
- 用户体验不好，需要频繁催促

**优化方向：**
1. 明确哪些步骤需要用户确认，哪些可以自动推进
2. 长时间任务应该主动汇报进度
3. 关键节点应该主动展示结果

---

### 问题 4：人工确认关卡不够明确
**时间：** 14:48 - 15:11
**现象：**
- Skill 文档说"参考图生成完成后，必须先把下面这些信息给用户看"
- 但 agent 在参考图生成后，没有主动发送图片给用户确认
- 用户需要主动要求"故事版出来后，直接把图片发上来，我来确认"

**问题分析：**
- SKILL.md 第 3 节"人工确认关卡"写得很清楚，但 agent 没有严格执行
- 可能是因为文档只说"必须先把信息给用户看"，但没有说"必须发送图片"
- Agent 可能理解为"只要生成了就算完成"

**优化方向：**
1. 在 SKILL.md 中明确：参考图生成后，**必须使用 message 工具发送图片**给用户
2. 在 run_workflow.py 的 generate-refs 命令中，添加自动发送图片的逻辑（可选）
3. 或者在 SKILL.md 中明确：generate-refs 完成后，agent 必须调用 message 工具发送图片

---

### 问题 5：风险报告没有被充分利用
**时间：** 14:48
**现象：**
- prepare 阶段生成了风险报告：`"total_risks": 26, "high_severity_risks": 18`
- 但 agent 没有向用户汇报这些风险
- 用户不知道有哪些高风险的 prompt 问题

**问题分析：**
- 风险分析功能已经实现，但没有被纳入标准流程
- Agent 没有意识到应该向用户汇报风险

**优化方向：**
1. 在 SKILL.md 中明确：prepare 完成后，如果有高风险 prompt，必须向用户汇报
2. 在 run_workflow.py 的 prepare 命令输出中，突出显示风险摘要
3. 或者添加一个独立的 `review-risks` 命令

---

### 问题 6：关键帧规划不够灵活
**时间：** 15:09 - 15:11
**现象：**
- 用户说"最后的定版是要定到我发给你的那张海报上，海报上的文字要出现。所以文字出现的时候，应该是最后2秒开始逐渐通过动效来出现"
- Agent 发现自动生成的关键帧有问题："动作推进：在"（断句异常）
- Agent 建议重新规划 6 格节奏

**问题分析：**
- 自动关键帧规划（`auto_beats`）可能会产生不合理的切分
- 用户需要手动调整关键帧时，流程不够顺畅

**优化方向：**
1. 改进 `auto_beats` 算法，避免断句异常
2. 提供更方便的关键帧调整机制
3. 在 prepare 阶段，向用户展示关键帧规划，允许用户确认或调整

---

### 问题 7：没有使用 validate-run 和 review-run
**时间：** 整个测试过程
**现象：**
- 测试过程中，没有使用 `validate-run` 命令验证参考图
- 没有使用 `review-run` 命令决定下一步动作
- 这些是 Phase 1 实现的核心功能，但在实际测试中没有被使用

**问题分析：**
- SKILL.md 没有明确说明何时使用这些命令
- Agent 不知道应该在什么时候调用这些命令
- 可能是因为这些命令是"可选"的，而不是"必须"的

**优化方向：**
1. 在 SKILL.md 中明确：generate-refs 完成后，必须执行 validate-run
2. 在 SKILL.md 中明确：validate-run 完成后，必须执行 review-run
3. 或者将这些步骤整合到主流程中，减少手动调用

---

### 问题 8：多次重复执行流程
**时间：** 14:47 - 16:15
**现象：**
- 第一次执行：14:47 - 15:11（因为 final_frame_poster 污染问题，用户要求重新执行）
- 第二次执行：15:10 - 15:24（生成新的参考图）
- 第三次执行：15:22 - 16:15（最终提交视频）

**问题分析：**
- 第一次执行因为 final_frame_poster 污染问题失败
- 导致用户需要多次重新执行
- 浪费了时间和额度

**优化方向：**
1. 在 prepare 阶段，检查 existing_references，如果有 final_frame_poster，提示用户会自动复用
2. 在 dry-run 阶段，展示将要使用的参考图列表，让用户确认

---

## 优化计划

### P0：必须修复（影响基本可用性）
- ✅ **问题 1：图片发送失败** - 已修复（commit 7d12203e）
- ✅ **问题 2：final_frame_poster 污染** - 已修复（commit e781a77b）

### P1：重要优化（影响用户体验）
- ✅ **问题 3：Agent 执行流程不够自主**（commit 7d4ed6bd）
  - 在 SKILL.md 中明确哪些步骤需要用户确认，哪些可以自动推进
  - 添加固定汇报模板，减少误解
  - 添加验收标准：不催也能走到"发图等待确认"
  
- ✅ **问题 4：人工确认关卡不够明确**（commit 7d4ed6bd）
  - 在 SKILL.md 中明确：generate-refs 完成后，必须发送图片
  - 添加确认关卡规则（5条规则）
  - 添加人工检查回写步骤到主流程
  - validate-run 默认验证 storyboard（包含人工检查清单）

- ✅ **问题 7：没有使用 validate-run 和 review-run**（commit 7d4ed6bd）
  - 在 SKILL.md 中明确这些命令的使用时机
  - 写入标准执行流程，不可跳过
  - submit-video 强制检查验证和审查结果

### P2：可选优化（改善体验）
- ✅ **问题 5：风险报告没有被充分利用**（commit 9c440e8a）
  - prepare 输出增加 top_risks 字段（前3条高风险详情）
  - summary.md 增加风险摘要区
  - 明确建议是否先修改 prompt
  
- ✅ **问题 6：关键帧规划不够灵活**（commit 1ddb191b）
  - 修复 auto_beats 断句问题（避免"动作推进：在"）
  - 优化语义切分，只在连接词是独立词时才切分
  - 时序约束纳入 beat 规划（final_frame_poster → "收束到定版海报构图"）
  - 添加 adjust-beats 命令（支持 --beats、--beats-file、--panel-count）

- ✅ **问题 8：多次重复执行流程**（commit 9c440e8a）
  - prepare 输出增加 reference_reuse_plan 字段
  - 提前说明 final_frame_poster 会自动复用为 original

---

## 后续发现的问题（2026-05-28）

### 问题 9：字段名不匹配导致 prepare 失败（已修复）

**发现时间**：2026-05-28 10:45（生图高手反馈）

**现象**：
- prepare 阶段提取高风险时报错：`AttributeError: 'PromptRisk' object has no attribute 'rule_id'`
- 风险分析功能无法正常工作

**根本原因**：
- `PromptRisk` 类定义的字段是 `risk_type` 和 `reason`
- 但 `run_workflow.py:220` 和 `workflow.py:1180` 访问的是 `rule_id` 和 `message`

**修复状态**：✅ 已修复（commit d3e6ea11）
- 修正字段名：`rule_id` → `risk_type`，`message` → `reason`
- 同时修复了两处访问位置

---

### 问题 10：Pillow 依赖未说明（已修复）

**发现时间**：2026-05-28 10:45（生图高手反馈）

**现象**：
- 生图高手环境中缺少 Pillow 库
- 参考图归一化功能无法使用
- 错误信息：`NameError: name 'Image' is not defined`

**根本原因**：
- `workflow.py` 和 `validator.py` 使用了 `from PIL import Image`
- 但没有在文档中说明这是必需依赖

**修复状态**：✅ 已修复（commit d3e6ea11）
- 新增 `requirements.txt` 说明 `Pillow>=10.0.0` 依赖
- 在 SKILL.md 中添加"环境要求"章节
- 说明 Python 3.9+ 和 Pillow 依赖

---

## 实施完成总结

**完成时间**: 2026-05-28

**三批优化全部完成**：

### 第一批：流程闭环批（commit 7d4ed6bd）
- 重写 SKILL.md 标准执行流程
- 添加确认关卡规则和验收标准
- validate-run 默认验证 storyboard
- 添加 --all-passed 参数

### 第二批：可执行反馈批（commit 9c440e8a）
- prepare 输出增加结构化字段（top_risks、reference_reuse_plan、next_step）
- generate-refs 输出增加结构化字段（preview_candidates、requires_user_confirmation、keyframe_info）
- summary.md 增加风险摘要区

### 第三批：算法优化批（commit 1ddb191b）
- 修复 auto_beats 断句问题
- 时序约束纳入 beat 规划
- 添加 adjust-beats 命令

**预期效果已达成**：
1. ✅ 减少用户催促次数 - agent 能自主走到确认关卡
2. ✅ 提高流程执行的自主性 - 明确每个步骤的输入输出和下一步
3. ✅ 减少重复执行的情况 - 提前说明参考图复用策略
4. ✅ 提升整体用户体验 - 固定汇报模板、风险摘要、可调整关键帧

### 第四批：环境兼容性修复（commit d3e6ea11）
- 修复字段名不匹配：rule_id → risk_type, message → reason
- 添加 requirements.txt 说明 Pillow 依赖
- SKILL.md 添加环境要求章节（Python 3.9+）

---

## 优化优先级建议

### 第一批：流程明确化（1-2小时）
1. **更新 SKILL.md**
   - 明确每个步骤是否需要用户确认
   - 明确 generate-refs 后必须发送图片
   - 明确 validate-run 和 review-run 的使用时机
   
2. **添加流程检查清单**
   - 在 SKILL.md 中添加"标准执行流程"章节
   - 列出每个步骤的输入、输出、确认点

### 第二批：自动化改进（2-3小时）
1. **改进 prepare 输出**
   - 突出显示风险摘要
   - 提示参考图复用策略
   
2. **改进 generate-refs 输出**
   - 自动汇报生成进度
   - 生成完成后提示用户确认

3. **整合 validate-run**
   - 考虑将 validate-run 整合到 generate-refs 中
   - 或者在 SKILL.md 中强制要求执行

### 第三批：算法优化（3-5小时）
1. **改进 auto_beats 算法**
   - 避免断句异常
   - 提供更合理的关键帧切分
   
2. **提供关键帧调整机制**
   - 允许用户在 prepare 阶段调整关键帧
   - 或者提供独立的 adjust-beats 命令

---

## 总结

本次测试暴露了 8 个问题，其中：
- ✅ 2 个已修复（P0 级别）
- ⏳ 6 个待优化（P1 和 P2 级别）

**核心问题：**
1. **流程不够明确** - Agent 不知道何时应该自主推进，何时应该等待用户确认
2. **确认机制不够清晰** - 人工确认关卡的执行不到位
3. **验证功能未被使用** - validate-run 和 review-run 没有被纳入标准流程

**优化重点：**
1. **明确流程** - 在 SKILL.md 中明确每个步骤的执行方式
2. **强化确认** - 确保关键节点的用户确认机制
3. **整合验证** - 将验证功能纳入标准流程

**预期效果：**
- 减少用户催促次数
- 提高流程执行的自主性
- 减少重复执行的情况
- 提升整体用户体验
