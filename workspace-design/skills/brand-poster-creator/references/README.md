# Brand Poster Creator - Reference 文档索引

本目录包含 brand-poster-creator skill 的完整流程参考文档，从原 SKILL.md（2111行）中提取并重构。

---

## 📚 文档列表

### Step 1: 需求收集
**文件**: `step-1-intake.md` (7.4 KB)

**内容**:
- 飞书对话卡片需求收集
- 项目分级与审批者确认（B/A/S 三级）
- brief.json 结构
- 项目目录结构
- 素材文件处理

**关键要点**:
- 触发技能后立即发送需求收集卡片
- 必须先确认项目等级和审批者再继续
- 初始化项目分级和时间记录

---

### Step 2: 品牌档案查询
**文件**: `step-2-brand-query.md` (8.7 KB)

**内容**:
- 品牌档案查询（调性、定位、目标受众）
- 品牌资产查询（Logo、VI 手册、参考图）
- 冲突检测（品牌关键信息变更需用户确认）
- 自动建档流程

**关键要点**:
- 生成品牌海报前必须先查询品牌档案和资产
- 未找到品牌档案时询问用户是否创建
- 高严重性冲突必须暂停任务并让用户选择处理方式

---

### Step 3: 蒸馏卡检查
**文件**: `step-3-distill-card.md` (5.8 KB)

**内容**:
- 蒸馏卡读取与处理
- 版式有效性判断（固定版式 vs 自由构图）
- 骨架图处理（PNG > SVG）
- 降级模式说明

**关键要点**:
- 有版式数据走固定版式坐标模式
- 无版式数据走自由构图与阅读动线模式
- 禁止伪造坐标或混用版式模式

---

### Step 4: 文案策划
**文件**: `step-4-copywriting.md` (7.7 KB)

**内容**:
- 派发 strategy subagent（产出文案策略）
- 派发 copywriter subagent（产出最终文案）
- spawn 参数约束（thinking/model/attachments）
- 文案结果统一落盘

**关键要点**:
- 文案阶段必须分两段执行：先 strategy，后 copywriter
- strategy 不写最终文案，只输出策略框架
- 严格遵守 spawn 参数规则避免报错

---

### Step 5: 文案审批
**文件**: `step-5-copywriting-approval.md` (7.6 KB)

**内容**:
- 展示文案 + 版式确认
- 请求文案审批（艾特文案策划判断者）
- 记录审批响应（approved/revision_needed/rejected）
- 文案审批门禁
- 多方向拆分入口

**关键要点**:
- 未通过文案审批前禁止进入风格提炼或创意表达
- 审批状态必须为 approved 才能继续
- B级项目超时可自动通过

---

### Step 6: 创意方向
**文件**: `step-6-creative-direction.md` (8.3 KB)

**内容**:
- 生成画面创意表达方案
- creative_direction.json 结构
- 创意确认门禁
- 参考图风格转译规则

**关键要点**:
- 这是 prompt 之前的创意对齐步骤
- 方案必须严格基于已确认信息生成
- 若有参考图，只能转译视觉语言，不得继承具体场景

---

### Step 7: 生图
**文件**: `step-7-generation.md` (14 KB)

**内容**:
- 运行 assemble_prompt.py 组装 prompt
- Prompt 版式模式（固定坐标 vs 自由构图）
- main 写好生图脚本
- 派发 design subagent 执行
- 回收结果与视觉核验
- 正式生图失败处理

**关键要点**:
- 必须通过脚本生成 prompt，禁止手写
- main 写完，子 agent 只跑（执行器，不是策划者）
- 绝对禁止 design 在生图失败后自行改用本地拼图

---

### Step 8: 设计审批
**文件**: `step-8-design-approval.md` (9.5 KB)

**内容**:
- 交付前强制检查
- 准备交付清单
- 真实发送规则（硬约束）
- 请求设计审批（艾特设计判断者）
- 记录设计审批响应
- 设计审批门禁

**关键要点**:
- 必须调用 message 工具发送，不得输出 MEDIA: 文本
- MEDIA: 只是文本输出，用户在飞书中看不到任何图片
- B级项目设计审批通过后直接交付，A/S级进入高级审批

---

### Step 9: 高级审批
**文件**: `step-9-advanced-approval.md` (8.3 KB)

**内容**:
- 创意总监审核（仅 A/S 级项目）
- 老板最终决策（仅 S 级项目）
- 审批超时处理（提醒/升级）
- 审批流程可视化

**关键要点**:
- B级项目跳过本步骤
- A级项目只需创意总监审核
- S级项目需要完整审批链：创意总监 → 老板
- A/S级超时不自动通过，需要提醒或升级

---

### Step 10: 交付
**文件**: `step-10-delivery.md` (7.1 KB)

**内容**:
- 生成复盘报告
- 向用户展示项目完成信息
- 发送原图 zip 包（如适用）
- 最终交付验证
- 复盘报告示例

**关键要点**:
- 所有审批通过后才能交付
- 必须生成复盘报告（无论是否清理文件）
- 复盘报告包含时间统计、审批流程统计、资源消耗等

---

### Step 11: 清理
**文件**: `step-11-cleanup.md` (9.1 KB)

**内容**:
- 询问清理
- 执行清理脚本
- 清理规则（使用 trash 而非 rm）
- 保留文件清单
- 清理文件清单
- 清理安全约束

**关键要点**:
- 清理是可选步骤，必须经过用户明确确认
- 使用 trash 而非 rm，确保文件可恢复
- 保留核心交付物和状态记录
- 未传 --confirmed 时脚本必须拒绝执行

---

## 🎯 使用指南

### 文档组织原则

1. **按步骤拆分**: 每个 step 对应一个独立文档
2. **保留关键硬规则**: 所有禁令和门禁都完整保留
3. **保留代码示例**: 所有脚本路径和命令示例都完整保留
4. **使用占位符**: `{baseDir}` 表示 skill 根目录

### 阅读顺序

**快速上手**:
1. Step 1 (需求收集) → Step 4 (文案策划) → Step 7 (生图)

**完整流程**:
1. Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7 → Step 8 → Step 9 → Step 10 → Step 11

**审批流程专题**:
- Step 1.2 (项目分级)
- Step 5 (文案审批)
- Step 8 (设计审批)
- Step 9 (高级审批)

### 与原 SKILL.md 的对应关系

| Reference 文档 | 原 SKILL.md 行号 |
|----------------|------------------|
| step-1-intake.md | 227-456 |
| step-2-brand-query.md | 17-100, 500-760 |
| step-3-distill-card.md | 467-750 |
| step-4-copywriting.md | 970-1120 |
| step-5-copywriting-approval.md | 1120-1270 |
| step-6-creative-direction.md | 1337-1456 |
| step-7-generation.md | 1459-1660 |
| step-8-design-approval.md | 1661-1900 |
| step-9-advanced-approval.md | 1884-2008 |
| step-10-delivery.md | 2009-2097 |
| step-11-cleanup.md | 2054-2097 |

---

## 📊 统计信息

- **总文档数**: 11 个
- **总大小**: 约 90 KB
- **原 SKILL.md 大小**: 2111 行
- **覆盖率**: 100% 核心流程

---

## 🔄 维护建议

### 更新原则

1. **保持同步**: 当 SKILL.md 更新时，同步更新对应的 reference 文档
2. **独立维护**: 每个 step 可以独立更新，不影响其他 step
3. **版本控制**: 重大变更时更新文档头部的版本说明

### 扩展方式

如果需要新增步骤：
1. 创建新的 `step-X-name.md` 文件
2. 按照现有格式编写内容
3. 更新本索引文件

---

## ✅ 重构完成确认

- ✅ 11 个 reference 文档已创建
- ✅ 所有关键硬规则已保留
- ✅ 所有代码示例和脚本路径已保留
- ✅ 使用 `{baseDir}` 占位符表示 skill 根目录
- ✅ 每个文档末尾说明"完成后执行下一步"

---

**重构日期**: 2026-06-13
**重构来源**: `/Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/SKILL.md` (2111 行)
**输出位置**: `/Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/references/`
