# Step 11：清理

## 概述

本步骤负责清理项目中间文件，保留核心交付物和状态记录。清理是**可选步骤**，必须经过用户明确确认后才能执行。

---

## 11.1 询问清理

项目交付完成后，询问用户是否清理：

```markdown
🧹 **项目文件清理**

项目已完成交付，是否清理中间文件？

保留的文件：
- ✅ 成品海报图片（`images/final_poster.png`）
- ✅ 需求信息（`brief.json`）
- ✅ 文案策划结果（`copywriting.json`）
- ✅ 生图结果记录（`generation_result.json`）
- ✅ 交付记录（`delivery_manifest.json`）
- ✅ 项目状态（`project_state.json`）
- ✅ 审批记录（`project_grading.json`）
- ✅ 审计日志（`audit_log.jsonl`）
- ✅ 复盘报告（`project_retrospective.md`）

将清理的文件：
- 🗑️ 中间日志文件（`logs/`）
- 🗑️ 中间素材图片（`images/` 下非最终交付图片）
- 🗑️ Prompt 草稿（`prompt_draft.md`）
- 🗑️ 蒸馏卡数据（`distill_card.json`）
- 🗑️ 创意方向草稿（`creative_direction.json`）
- 🗑️ 风格提炼结果（`style_profile.json`）
- 🗑️ 参考图顺序文件（`ref_order.json`）
- 🗑️ 各阶段 manifest 文件

请选择：
- 回复「完成」→ 清理项目中间文件
- 回复「保留」→ 保留所有文件，不清理
```

---

## 11.2 执行清理脚本

如果用户选择「完成」，运行清理脚本：

```bash
python3 {baseDir}/scripts/cleanup_project.py \
  --project-dir "[项目目录绝对路径]" \
  --confirmed
```

### 11.2.1 脚本参数说明

- `--project-dir`: 项目目录绝对路径（必需）
- `--confirmed`: 确认执行清理标志（必需）

**重要**：未传 `--confirmed` 时，脚本必须拒绝执行并记录失败状态。

---

## 11.3 清理规则

### 11.3.1 使用 trash 而非 rm

脚本会使用 `trash` 命令删除中间文件，**不会**直接使用 `rm`。

这样做的好处：
- 文件进入回收站，可以恢复
- 避免误删重要文件
- 更安全的删除操作

### 11.3.2 默认保留的文件

以下文件**必须保留**：

#### 核心配置文件
- `brief.json` - 需求信息
- `copywriting.json` - 文案策划结果
- `copy_strategy.json` - 文案策略

#### 生图相关
- `generation_result.json` - 生图结果记录
- `images/final_poster.png` - 最终海报图片

#### 交付和状态
- `delivery_manifest.json` - 交付记录
- `cleanup_manifest.json` - 清理记录

#### 项目管理
- `project_state.json` - 项目状态
- `project_grading.json` - 审批记录
- `audit_log.jsonl` - 审计日志
- `project_retrospective.md` - 复盘报告

#### 品牌档案缓存
- `brand_profile_cache.json` - 品牌档案缓存（如有）

### 11.3.3 默认清理的文件

以下文件将被清理：

#### 日志文件
- `logs/` 目录下所有日志文件

#### 中间素材图片
- `images/` 下非最终交付图片：
  - `skeleton.png` - 骨架图
  - `style_ref_*.png` - 风格参考图
  - `product.png` - 产品参考图（如已合成到成品中）
  - `logo.png` - Logo 参考图（如已合成到成品中）
  - `ip.png` - IP 参考图（如已合成到成品中）
  - `product_realism_ref.jpg` - 产品参考适配图
  - 其他临时生成的中间图片

#### Prompt 和策划文件
- `prompt_draft.md` - Prompt 草稿
- `creative_direction.json` - 创意方向草稿
- `style_profile.json` - 风格提炼结果
- `ref_order.json` - 参考图顺序文件

#### 蒸馏卡数据
- `distill_card.json` - 蒸馏卡数据（已合成到成品中）

#### 各阶段 manifest 文件
- `distill_manifest.json`
- `gap_check_manifest.json`
- `copywriting_manifest.json`
- `style_profile_manifest.json`
- `creative_direction_manifest.json`
- `prompt_manifest.json`
- `generation_manifest.json`（已合并到 `generation_result.json`）
- `assets_manifest.json`

#### 临时文件和脚本
- `run.sh` - 生图执行脚本
- `copy_brief_for_strategy.json` - 策略临时文件
- `selected_direction.json` - 方向选择记录（多方案拆分时）

---

## 11.4 清理后的项目目录结构

清理完成后，项目目录应保持以下结构：

```
/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/
├── brief.json                    # 需求信息
├── copywriting.json              # 文案策划结果
├── copy_strategy.json            # 文案策略
├── generation_result.json        # 生图结果记录
├── delivery_manifest.json        # 交付记录
├── cleanup_manifest.json         # 清理记录
├── project_state.json            # 项目状态
├── project_grading.json          # 审批记录
├── audit_log.jsonl               # 审计日志
├── project_retrospective.md      # 复盘报告
├── brand_profile_cache.json      # 品牌档案缓存（如有）
└── images/
    └── final_poster.png          # 最终海报图片
```

---

## 11.5 清理执行流程

### 11.5.1 前置检查

清理脚本执行前会进行以下检查：

1. **确认标志检查**：必须传入 `--confirmed` 参数
2. **项目目录检查**：项目目录必须存在
3. **核心文件检查**：确认保留文件清单中的文件都存在

### 11.5.2 执行清理

1. 读取项目目录
2. 识别中间文件和保留文件
3. 使用 `trash` 命令将中间文件移到回收站
4. 记录清理结果到 `cleanup_manifest.json`
5. 更新 `project_state.json` 状态为 `cleaned`
6. 追加清理记录到 `audit_log.jsonl`

### 11.5.3 清理验证

清理完成后，脚本会验证：

1. 所有保留文件仍然存在
2. 中间文件已被清理
3. `cleanup_manifest.json` 已生成
4. `project_state.json` 已更新

---

## 11.6 cleanup_manifest.json 结构

```json
{
  "cleanup_status": "success",
  "cleanup_method": "trash",
  "cleaned_at": "2026-06-13T13:10:00Z",
  "files_cleaned": [
    "logs/generation.log",
    "images/skeleton.png",
    "images/style_ref_1.png",
    "images/product.png",
    "images/logo.png",
    "prompt_draft.md",
    "distill_card.json",
    "creative_direction.json",
    "style_profile.json",
    "ref_order.json",
    "run.sh",
    "distill_manifest.json",
    "gap_check_manifest.json",
    "style_profile_manifest.json",
    "creative_direction_manifest.json",
    "prompt_manifest.json"
  ],
  "files_preserved": [
    "brief.json",
    "copywriting.json",
    "copy_strategy.json",
    "generation_result.json",
    "delivery_manifest.json",
    "project_state.json",
    "project_grading.json",
    "audit_log.jsonl",
    "project_retrospective.md",
    "images/final_poster.png"
  ],
  "cleanup_size_mb": 15.8
}
```

---

## 11.7 清理完成确认

清理完成后，向用户确认：

```markdown
✅ **清理完成**

已清理 [N] 个中间文件，释放空间 [X.X] MB。

保留的核心文件：
- 成品海报图片
- 需求和文案记录
- 生图和交付记录
- 项目状态和审批记录
- 复盘报告

项目文件已整理完毕，可随时回溯。
```

---

## 11.8 🔴 CHECKPOINT · STOP：清理安全约束

### 必须遵守

1. **未传 `--confirmed` 时，脚本必须拒绝执行**并记录失败状态
2. **未得到用户"已完成/可清理"明确确认前，不得调用清理脚本**
3. **清理完成后必须生成 `cleanup_manifest.json`**，并同步更新 `project_state.json` 与 `audit_log.jsonl`
4. **使用 `trash` 而非 `rm`**，确保文件可恢复

### 禁止行为

- ❌ **不得在未确认时自动清理**
- ❌ **不得使用 `rm -rf` 直接删除**
- ❌ **不得清理保留文件清单中的文件**
- ❌ **不得在清理失败时隐藏错误**

---

## 11.9 用户选择保留的处理

如果用户选择「保留」，则不执行清理脚本：

```markdown
✅ **文件已保留**

所有项目文件已保留，未执行清理。

你可以随时查看完整的项目文件，包括：
- 中间素材图片
- Prompt 草稿
- 创意方向草稿
- 各阶段日志和 manifest

如果后续需要清理，可以随时告诉我。
```

在 `project_state.json` 中标记状态为 `completed_unclean`。

---

## 11.10 清理失败处理

如果清理脚本执行失败：

1. **记录失败原因**到 `cleanup_manifest.json`
2. **更新 `project_state.json`** 状态为 `cleanup_failed`
3. **追加失败记录到 `audit_log.jsonl`**
4. **向用户报告失败信息**：

```markdown
⚠️ **清理失败**

清理过程中遇到错误：[错误信息]

已保留所有文件，未执行任何删除操作。

你可以：
- 手动检查项目目录
- 重新尝试清理
- 保持现状，不清理
```

---

## 11.11 关键硬规则

### ✅ 必须遵守

1. **清理是可选步骤**：必须经过用户明确确认
2. **使用 trash 而非 rm**：确保文件可恢复
3. **保留核心文件**：不得清理保留清单中的文件
4. **清理必须有记录**：生成 `cleanup_manifest.json`
5. **失败必须报告**：不得隐藏清理错误

### ❌ 禁止行为

1. **不得自动清理**：必须等待用户确认
2. **不得使用 rm -rf**：必须使用 trash
3. **不得清理保留文件**：严格遵守保留清单
4. **不得隐藏失败**：必须向用户报告

---

## 完成

清理步骤完成后，整个品牌海报生成流程结束。
