# dreamina-reference-video Skill 测试指南

## 优化内容概述

这次优化解决了三个核心问题：

1. **参考图自动归一化**：大图（如 2160x3840 / 9MB）会自动压缩到安全尺寸（1920px / 3MB），避免超时失败
2. **IP 约束字段优化**：新增 `identity_structure`（结构真相）和 `identity_forbidden`（禁止变形）两个字段，替代原来的 `identity_anchor_rules`
3. **故事板画幅强化**：在 prompt 中明确要求"每一格都必须是独立的成片画幅"，避免生成横向长条

## 前置准备

### 1. 安装依赖

参考图归一化功能需要 Pillow 库：

```bash
pip install Pillow
```

### 2. 检查环境

运行 preflight 检查：

```bash
cd /Users/a123/.openclaw/skills/dreamina-reference-video
python3 scripts/run_workflow.py preflight
```

确保：
- `dreamina_bin`: ok
- `dreamina_credit`: ok
- `gpt_image_script`: ok
- `gpt_image_config`: ok

## 测试用例

### 测试 1：参考图自动归一化（核心功能）

**目的**：验证大图会被自动压缩到安全尺寸

**步骤**：

1. 准备一张大图（建议 2160x3840 或更大，文件大小 > 5MB）

2. 创建 `brief.json`：

```json
{
  "subject": "黄小咕",
  "action": "在广场跳舞后定格",
  "scene": "欧洲老城广场",
  "style": "3D 卡通海报感",
  "ratio": "9:16",
  "duration": 5,
  "existing_references": {
    "identity_source": "/path/to/your/large-image.png"
  }
}
```

3. 运行 prepare：

```bash
python3 scripts/run_workflow.py prepare --brief-file /path/to/brief.json
```

4. 检查输出的 `run_dir`，查看归一化结果：

```bash
# 假设输出的 run_dir 是 outputs/dreamina-reference-video/20260527-123456-黄小咕
cd outputs/dreamina-reference-video/20260527-123456-黄小咕

# 查看归一化清单
cat refs/normalized/manifest.json

# 查看 summary.md 中的归一化结果
cat summary.md
```

**验收标准**：

- ✅ `refs/normalized/manifest.json` 存在且包含归一化信息
- ✅ `manifest.json` 中 `normalized_width` 和 `normalized_height` 不超过 1920
- ✅ `manifest.json` 中 `normalized_bytes` 不超过 3MB（约 3145728 字节）
- ✅ `manifest.json` 中 `changed: true`（如果原图超过限制）
- ✅ `summary.md` 中有"参考图归一化结果"章节，显示压缩前后的尺寸和大小
- ✅ `refs/identity-source.png` 存在且是压缩后的版本

**预期输出示例**：

```json
// refs/normalized/manifest.json
[
  {
    "role": "identity_source",
    "source_path": "/path/to/your/large-image.png",
    "source_format": "PNG",
    "source_width": 2160,
    "source_height": 3840,
    "source_bytes": 9437184,
    "normalized_path": ".../refs/normalized/identity-source.png",
    "normalized_format": "JPEG",
    "normalized_width": 1080,
    "normalized_height": 1920,
    "normalized_bytes": 245678,
    "alpha_flattened": false,
    "changed": true
  }
]
```

### 测试 2：IP 约束字段（新功能）

**目的**：验证新的 `identity_structure` 和 `identity_forbidden` 字段在 prompt 中生效

**步骤**：

1. 创建 `brief.json`：

```json
{
  "subject": "黄小咕",
  "action": "在广场跳舞后定格",
  "scene": "欧洲老城广场",
  "style": "3D 卡通海报感",
  "ratio": "9:16",
  "duration": 5,
  "identity_structure": [
    "整体读成点赞大拇指体块",
    "正面也能看到尾巴",
    "只有单侧翅膀（右侧装饰性小翅膀）"
  ],
  "identity_forbidden": [
    "禁止普通圆鸡化",
    "禁止双翅膀",
    "禁止人类手指/手掌",
    "禁止正面尾巴消失"
  ]
}
```

2. 运行 prepare：

```bash
python3 scripts/run_workflow.py prepare --brief-file /path/to/brief.json
```

3. 检查生成的 prompt 文件：

```bash
cd outputs/dreamina-reference-video/20260527-123456-黄小咕

# 检查 identity-board prompt
cat prompts/identity-board.txt

# 检查 storyboard prompt
cat prompts/storyboard.txt

# 检查 video prompt
cat prompts/video.txt

# 检查 summary.md
cat summary.md
```

**验收标准**：

- ✅ `prompts/identity-board.txt` 中包含"结构真相：整体读成点赞大拇指体块；正面也能看到尾巴；只有单侧翅膀"
- ✅ `prompts/identity-board.txt` 中包含"禁止变形：禁止普通圆鸡化；禁止双翅膀；禁止人类手指/手掌；禁止正面尾巴消失"
- ✅ `prompts/storyboard.txt` 中包含相同的结构真相和禁止变形
- ✅ `prompts/video.txt` 中包含相同的结构真相和禁止变形
- ✅ `summary.md` 中有"IP 约束规则"章节，分别列出"结构真相"和"禁止变形"
- ✅ `summary.md` 中有"人工检查清单"，包含对应的检查项

### 测试 3：向后兼容（旧字段自动迁移）

**目的**：验证旧的 `identity_anchor_rules` 会自动迁移到新字段

**步骤**：

1. 创建使用旧字段的 `brief.json`：

```json
{
  "subject": "黄小咕",
  "action": "在广场跳舞后定格",
  "scene": "欧洲老城广场",
  "style": "3D 卡通海报感",
  "ratio": "9:16",
  "duration": 5,
  "identity_anchor_rules": [
    "整体读成点赞大拇指体块",
    "正面也能看到尾巴",
    "禁止普通圆鸡化",
    "禁止双翅膀",
    "不要人类手指"
  ]
}
```

2. 运行 prepare：

```bash
python3 scripts/run_workflow.py prepare --brief-file /path/to/brief.json
```

3. 检查生成的 `brief.json`：

```bash
cd outputs/dreamina-reference-video/20260527-123456-黄小咕
cat brief.json
```

**验收标准**：

- ✅ 生成的 `brief.json` 中有 `identity_structure` 字段，包含"整体读成点赞大拇指体块"和"正面也能看到尾巴"
- ✅ 生成的 `brief.json` 中有 `identity_forbidden` 字段，包含"禁止普通圆鸡化"、"禁止双翅膀"、"不要人类手指"
- ✅ prompt 文件中正确使用了迁移后的字段

### 测试 4：故事板画幅强化

**目的**：验证故事板 prompt 明确要求每格独立画幅

**步骤**：

1. 创建 `brief.json`（使用 9:16 竖版）：

```json
{
  "subject": "黄小咕",
  "action": "在广场跳舞后定格",
  "scene": "欧洲老城广场",
  "style": "3D 卡通海报感",
  "ratio": "9:16",
  "duration": 5
}
```

2. 运行 prepare：

```bash
python3 scripts/run_workflow.py prepare --brief-file /path/to/brief.json
```

3. 检查 storyboard prompt：

```bash
cd outputs/dreamina-reference-video/20260527-123456-黄小咕
cat prompts/storyboard.txt
```

**验收标准**：

- ✅ `prompts/storyboard.txt` 中包含"**每一格都必须是独立的 9:16 成片画幅**"
- ✅ `prompts/storyboard.txt` 中包含"不要做横向长条单格，不要把多格画成电影条带"
- ✅ `prompts/storyboard.txt` 中包含"整张看板怎么排版都可以，但每格内部画幅必须服从 9:16 成片比例"
- ✅ `summary.md` 中的人工检查清单包含"故事板每一格是否都是 **9:16** 画幅？"

### 测试 5：完整工作流（端到端）

**目的**：验证从 prepare 到 generate-refs 的完整流程

**步骤**：

1. 准备一张大的角色参考图（建议 > 5MB）

2. 创建完整的 `brief.json`：

```json
{
  "subject": "黄小咕",
  "action": "在广场跳舞后转向镜头定格",
  "scene": "欧洲老城广场，午后阳光",
  "style": "3D 卡通海报感，电影级质感",
  "ratio": "9:16",
  "duration": 5,
  "quality_tier": "draft",
  "identity_structure": [
    "整体读成点赞大拇指体块",
    "正面也能看到尾巴",
    "只有单侧翅膀（右侧装饰性小翅膀）"
  ],
  "identity_forbidden": [
    "禁止普通圆鸡化",
    "禁止双翅膀",
    "禁止人类手指/手掌",
    "禁止正面尾巴消失"
  ],
  "existing_references": {
    "identity_source": "/path/to/your/character-sheet.png"
  }
}
```

3. 运行完整流程：

```bash
# 1. Preflight 检查
python3 scripts/run_workflow.py preflight

# 2. Prepare
python3 scripts/run_workflow.py prepare --brief-file /path/to/brief.json

# 记录输出的 run_dir
RUN_DIR="outputs/dreamina-reference-video/20260527-123456-黄小咕"

# 3. Generate refs (先 dry-run)
python3 scripts/run_workflow.py generate-refs --run-dir "$RUN_DIR" --dry-run

# 4. Generate refs (正式执行)
python3 scripts/run_workflow.py generate-refs --run-dir "$RUN_DIR"
```

4. 检查生成的参考图和 summary：

```bash
cd "$RUN_DIR"

# 查看所有参考图
ls -lh refs/*.png

# 查看归一化结果
cat refs/normalized/manifest.json

# 查看完整摘要
cat summary.md

# 查看所有 prompt
ls -lh prompts/*.txt
```

**验收标准**：

- ✅ `refs/original.png` 存在
- ✅ `refs/identity-source.png` 存在（归一化后的版本）
- ✅ `refs/identity-board.png` 存在（如果 identity_strategy 不是 reuse_exact）
- ✅ `refs/storyboard.png` 存在
- ✅ `refs/normalized/manifest.json` 存在且包含归一化信息
- ✅ `summary.md` 包含完整的归一化结果、IP 约束规则、人工检查清单
- ✅ 所有 prompt 文件都正确生成且包含新的约束字段

5. **人工检查**（这是最重要的验收步骤）：

打开生成的参考图，按照 `summary.md` 中的"人工检查清单"逐项检查：

- [ ] 故事板每一格是否都是 **9:16** 画幅？（不是横向长条，不是电影条带）
- [ ] 角色身份是否和 `refs/identity-source.png` 一致？（脸、服装、比例、姿态）
- [ ] 以下结构真相是否都保持了？
  - [ ] 整体读成点赞大拇指体块
  - [ ] 正面也能看到尾巴
  - [ ] 只有单侧翅膀（右侧装饰性小翅膀）
- [ ] 是否出现了以下禁止变形？（应该全部没有出现）
  - [ ] 禁止普通圆鸡化
  - [ ] 禁止双翅膀
  - [ ] 禁止人类手指/手掌
  - [ ] 禁止正面尾巴消失

**如果人工检查通过**，继续提交视频：

```bash
# 5. Submit video (先 dry-run)
python3 scripts/run_workflow.py submit-video --run-dir "$RUN_DIR" --dry-run

# 6. Submit video (正式提交)
python3 scripts/run_workflow.py submit-video --run-dir "$RUN_DIR"

# 7. Fetch result
python3 scripts/run_workflow.py fetch-result --run-dir "$RUN_DIR"
```

## 单元测试

运行单元测试验证代码逻辑：

```bash
cd /Users/a123/.openclaw/skills/dreamina-reference-video
python3 -m unittest tests.test_workflow -v
```

**预期结果**：

- 所有测试通过（除了 3 个需要 Pillow 的测试可能会跳过）
- 新增的测试包括：
  - `test_normalize_brief_migrates_identity_anchor_rules_to_new_fields`
  - `test_build_prompts_uses_new_identity_fields`
  - `test_build_prompts_enforces_storyboard_panel_aspect_ratio`
  - `test_normalize_reference_image_compresses_large_image`
  - `test_normalize_reference_image_keeps_small_image`
  - `test_normalize_reference_image_handles_transparency`

## 常见问题排查

### 问题 1：Pillow 未安装

**症状**：运行时报错 `需要安装 Pillow: pip install Pillow`

**解决**：

```bash
pip install Pillow
```

### 问题 2：参考图没有被归一化

**症状**：`refs/normalized/` 目录不存在或为空

**可能原因**：
- `normalize_references` 被设置为 `false`
- 参考图本身就很小，不需要归一化

**检查**：

```bash
# 查看 brief.json
cat brief.json | grep normalize_references

# 查看原始参考图大小
ls -lh /path/to/original/image.png
```

### 问题 3：旧字段没有迁移

**症状**：使用了 `identity_anchor_rules` 但 prompt 中没有生效

**可能原因**：同时提供了新字段和旧字段，新字段优先级更高

**解决**：只使用新字段 `identity_structure` 和 `identity_forbidden`，或者只使用旧字段 `identity_anchor_rules`（会自动迁移）

### 问题 4：故事板画幅仍然不对

**症状**：生成的故事板每格仍然是横向长条

**说明**：
- 这次优化只是在 prompt 中强化了要求，不是 100% 保证
- 如果仍然出现问题，可以在 `notes` 中补充："每格必须是竖版 9:16，不要横向长条"
- 或者在人工确认关卡拒绝，重新生成

## 验收标准总结

### 必须通过的验收项

1. ✅ **参考图归一化**：大图（> 1920px 或 > 3MB）会被自动压缩
2. ✅ **归一化清单**：`refs/normalized/manifest.json` 存在且包含完整信息
3. ✅ **新字段生效**：`identity_structure` 和 `identity_forbidden` 在所有 prompt 中正确使用
4. ✅ **向后兼容**：旧的 `identity_anchor_rules` 自动迁移到新字段
5. ✅ **故事板画幅**：prompt 中明确要求"每一格都必须是独立的成片画幅"
6. ✅ **summary.md 增强**：包含归一化结果、IP 约束规则、人工检查清单
7. ✅ **单元测试**：所有测试通过

### 建议验收的项（需要实际生成视频）

1. ⭐ **故事板画幅实际效果**：生成的故事板每格是否真的是目标画幅
2. ⭐ **IP 一致性实际效果**：生成的视频中角色是否保持了结构真相，是否避免了禁止变形
3. ⭐ **归一化对质量的影响**：压缩后的参考图是否仍然能保持足够的细节

## 下一步建议

如果基础功能测试通过，建议：

1. **用黄小咕案例跑 5-10 轮**，记录：
   - 故事板画幅合格率
   - IP 一致性保持率
   - 归一化是否影响最终质量

2. **根据实际效果决定是否需要第二阶段优化**：
   - 如果故事板画幅问题仍然频繁出现 → 考虑添加自动画幅校验
   - 如果 IP 约束效果不明显 → 考虑更细的字段分类或更强的 prompt
   - 如果归一化影响质量 → 调整压缩参数或策略

3. **收集用户反馈**，优先解决最影响体验的问题

## 联系方式

如果测试过程中遇到问题，请提供：
- 完整的错误信息
- `brief.json` 内容
- `summary.md` 内容
- 生成的参考图（如果有）
