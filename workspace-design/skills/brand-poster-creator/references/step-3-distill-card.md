# Step 3：蒸馏卡检查

## 概述

本步骤负责读取蒸馏卡数据，提取版式坐标、文案策划指南和负面约束，为后续 prompt 组装提供版式锁定依据。

---

## 3.1 读取蒸馏卡 ID

读取 `brief.json` 中的 `distill_card_id` 字段，判断是否有蒸馏卡。

---

## 3.2 有蒸馏卡 ID 的处理流程

### 3.2.1 运行脚本处理蒸馏卡

```bash
python3 {baseDir}/scripts/process_distill_card.py \
  --project-dir "[项目目录绝对路径]"
```

### 3.2.2 脚本自动完成以下操作

1. 读取对应蒸馏卡 JSON 文件：
   - 路径：`/Users/a123/.openclaw/workspace/skills/brand-poster-distiller/cards/[ID].json`

2. 将完整 JSON 数据写入 `distill_card.json`

3. 提取关键数据：
   - `layout_analysis.elements` → 版式坐标数据
   - `layout_analysis.copy_planning_guide` → 文案策划指南
   - `layout_analysis.negative_constraints` → 负面约束

4. 将骨架图复制到 `images/skeleton.png`：
   - 优先使用 `skeleton_png` 字段（PNG 格式）
   - 若为空则回退 `skeleton_image` 字段（SVG 格式）

5. 写入状态文件：
   - `distill_manifest.json`
   - `project_state.json`
   - `audit_log.jsonl`

---

## 3.3 版式有效性分支判断

脚本执行后，根据 `layout_analysis.elements` 的有效性分三种情况处理：

### 情况 A：有效版式坐标（固定版式模式）

**触发条件**：`layout_analysis.elements` 存在且至少包含 1 个有效区域

**后续影响**：
- prompt 进入**固定版式坐标模式**
- 每个区域输出 `x / y / 宽 / 高 / z`，并绑定区域角色、文案或素材
- 用户确认的文案必须落到对应区域；缺失则阻塞
- 模型只在固定区域内做视觉表达，不得自行重排

### 情况 B：空版式元素（降级为自由构图模式）

**触发条件**：蒸馏卡存在但 `layout_analysis.elements` 为空、缺失或全是无效元素

**必须执行的操作**：
1. 在 `distill_manifest.json` 记录 `layout_status="empty_elements"`
2. 在 `brief.json` 标记 `"distill_mode": "fallback"`

**后续影响**：
- prompt 进入**自由构图与阅读动线模式**
- 不得生成 `x:`、`y:`、坐标框、占位框或"放置在适当位置"
- 使用相对区域约束：顶部信息区、中部主视觉区、底部信息区、前中后景层次
- 锁定第一视觉、辅助视觉、禁忌主角和阅读顺序

**禁止行为**：
- ❌ 不得伪造坐标继续固定版式模式
- ❌ 不得用手写坐标继续生图

### 情况 C：蒸馏卡读取失败

**触发条件**：蒸馏卡 JSON 文件无法读取

**处理方式**：
- 停止当前阶段并展示错误
- 不得用手写坐标继续
- 必须修复蒸馏卡文件或切换到降级模式

---

## 3.4 无蒸馏卡 ID 的处理流程

如果 `brief.json` 中的 `distill_card_id` 为空或不存在：

1. 在 `brief.json` 中标记 `"distill_mode": "fallback"`
2. 后续进入**降级组装流程**（自由构图与阅读动线模式）
3. 不执行 `process_distill_card.py` 脚本

---

## 3.5 骨架图处理规则

### 优先级规则

1. **优先使用 PNG 格式**：`skeleton_png` 字段
2. **回退 SVG 格式**：`skeleton_image` 字段（当 PNG 不可用时）

### 保存位置

骨架图统一保存到：`images/skeleton.png`

### 后续用途

- 作为参考图传入生图 API（role: `skeleton`）
- 在 `ref_order.json` 中记录为 `skeleton` 角色
- 帮助模型理解版式布局和区域关系

---

## 3.6 版式数据结构示例

### distill_card.json 示例

```json
{
  "distill_id": "POSTER-DISTILL-P-012",
  "layout_analysis": {
    "elements": [
      {
        "id": "el-5",
        "type": "title",
        "position": "x:5% y:4% 90%×22%",
        "direction": "横排",
        "role": "主标题区"
      },
      {
        "id": "el-7",
        "type": "subtitle",
        "position": "x:22% y:26% 56%×4%",
        "direction": "横排",
        "role": "副标题区"
      }
    ],
    "copy_planning_guide": "主标题应简洁有力，8-12字；副标题补充细节，12-18字",
    "negative_constraints": ["不要遮挡主视觉", "不要过于密集"]
  },
  "skeleton_png": "/path/to/skeleton.png",
  "skeleton_image": "/path/to/skeleton.svg"
}
```

### distill_manifest.json 示例

```json
{
  "status": "success",
  "distill_id": "POSTER-DISTILL-P-012",
  "layout_status": "valid_elements",
  "elements_count": 6,
  "skeleton_path": "images/skeleton.png",
  "skeleton_format": "png",
  "timestamp": "2026-06-13T10:30:00Z"
}
```

---

## 3.7 关键硬规则

### ✅ 必须遵守

1. **有蒸馏卡时必须运行脚本**：不得手动复制或解析 JSON
2. **版式有效性必须真实判断**：不得假装有坐标或伪造空坐标
3. **骨架图必须按优先级处理**：PNG > SVG，不得跳过
4. **状态必须落盘**：`distill_manifest.json`、`project_state.json`、`audit_log.jsonl`

### ❌ 禁止行为

1. **不得绕过脚本手动处理蒸馏卡**：必须通过 `process_distill_card.py`
2. **不得伪造坐标数据**：空元素时必须标记 fallback
3. **不得跳过版式有效性检查**：必须判断 `elements` 是否真实有效
4. **不得混用版式模式**：固定坐标和自由构图不能混在一起

---

## 3.8 降级模式说明

当蒸馏卡不存在或版式元素无效时，进入**降级模式**：

### 降级模式特征

- `brief.json` 中 `distill_mode="fallback"`
- 不使用固定坐标
- prompt 使用相对区域描述（顶部、中部、底部）
- 依赖创意表达方案和阅读动线引导构图

### 降级模式不是失败

降级模式是**正常工作流程的一部分**，不是错误状态：
- 适用于没有预先设计版式的海报
- 适用于自由创意类海报
- 模型根据创意方向自然构图

---

## 完成后执行下一步

蒸馏卡检查完成后，进入 **Step 3：飞书云盘品牌素材检索**。
