---
name: product-photography-workflow
description: Use when users ask for product photography, product still-life images, white-background product shots, clean tabletop product visuals, or product-image generation based on real product photos and style references, especially when the same product may need multiple continued tasks over time.
---

## 🔴 记忆系统集成（执行前必读）

⚠️ **重要**：执行本 skill 前，必须完成项目立项和任务创建。

### Step 0: 项目立项与任务创建

```bash
# 1. 查询或创建项目（自动创建客户和品牌）
PROJECT_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/project.py get-or-create \
  --client "${CLIENT_NAME}" \
  --brand "${BRAND_NAME}" \
  --project "${PROJECT_NAME}" \
  --campaign-type "产品摄影" \
  --json)

PROJECT_ID=$(echo $PROJECT_INFO | jq -r '.project_id')
PROJECT_PATH=$(echo $PROJECT_INFO | jq -r '.project_path')

echo "✅ 项目已就绪: $PROJECT_ID"

# 2. 创建任务
TASK_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/task.py create \
  --project-id "$PROJECT_ID" \
  --name "${TASK_NAME}" \
  --type "photography" \
  --agent "design" \
  --skill "product-photography-workflow" \
  --brief "${TASK_BRIEF}" \
  --json)

TASK_ID=$(echo $TASK_INFO | jq -r '.task_id')

echo "✅ 任务已创建: $TASK_ID"

# 3. 查询品牌档案（用于指导创作）
BRAND_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand \
  --name "${BRAND_NAME}" \
  --json)

# 提取品牌信息
BRAND_TONE=$(echo $BRAND_INFO | jq -r '.brand_tone')
POSITIONING=$(echo $BRAND_INFO | jq -r '.positioning')
TARGET_AUDIENCE=$(echo $BRAND_INFO | jq -r '.target_audience')
CORE_VALUES=$(echo $BRAND_INFO | jq -r '.core_values | join(", ")')

echo "📋 品牌调性: $BRAND_TONE"
echo "📋 品牌定位: $POSITIONING"
echo "📋 目标受众: $TARGET_AUDIENCE"

# 4. 查询品牌资产（Logo、VI、参考图）
BRAND_ASSETS=$(python3 /Users/a123/.openclaw/scripts/memory/query.py assets \
  --brand "${BRAND_NAME}" \
  --json)

LOGO_PATH=$(echo $BRAND_ASSETS | jq -r '.logos[0] // empty')
if [ -n "$LOGO_PATH" ]; then
    echo "🎨 品牌 Logo: $LOGO_PATH"
fi
```

**环境变量说明**：

- `CLIENT_NAME`: 客户名称（从用户输入或上下文获取）
- `BRAND_NAME`: 品牌名称
- `PROJECT_NAME`: 项目名称（如"春节营销活动"）
- `TASK_NAME`: 任务名称（如"春节海报设计"）
- `TASK_BRIEF`: 任务简介

**品牌信息使用**：

在执行创作任务时，必须参考品牌档案中的：
- `BRAND_TONE`: 品牌调性（用于指导视觉风格和文案语气）
- `POSITIONING`: 品牌定位（用于确定传播策略）
- `TARGET_AUDIENCE`: 目标受众（用于内容方向）
- `LOGO_PATH`: 品牌 Logo（用于设计中的 Logo 使用）

---


# Product Photography Workflow

## 记忆系统集成（必读）

⚠️ **执行本 skill 前，必须先查询相关品牌档案**

### 查询品牌信息
```bash
# 查询品牌档案（获取调性、定位、目标受众）
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产（获取 Logo、VI 手册、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json

# 查询项目上下文（获取策略、创意方向）
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json
```

### 关键信息提取
从品牌档案中提取：
- **品牌调性** (`brand_tone`) - 决定整体风格和情绪
- **定位** (`positioning`) - 决定表达层级和差异点
- **目标受众** (`target_audience`) - 决定语境和沟通方式
- **核心价值观** (`core_values`) - 决定价值主张

### 品牌一致性要求
- 所有产出必须符合品牌调性
- 表达方式必须匹配目标受众
- 价值主张必须呼应品牌核心价值观
- 使用品牌资产库中的官方素材（Logo、VI 等）



## Overview

Use this skill as a `main`-orchestrated workflow.

Default mode is V2:

- one project = one stable product truth
- one project can accumulate many image tasks over time
- tasks can be recalled later by natural-language project query
- each task has its own brief, references, versions, and confirmation log

Keep V1 only as a legacy shortcut for single-run still-life requests.

## Trigger Phrases

Activate this skill when the user asks for any of the following:

**For `whole_image` mode** (new product photography):
- 产品摄影
- 产品拍摄
- 做产品图
- 生产品图
- 白底产品图
- 静物产品图
- 棚拍产品图
- 台面产品图
- 根据产品图生成摄影图
- 参考这个风格做产品图

**For `local_edit` mode** (refine existing image):
- 只改质感 / 只改表皮 / 只改夹心 / 只改XX
- 其他不变 / 保持构图不变 / 保持机位不变
- 修改现有产品图的XX
- 在这张图的基础上改XX
- 优化/调整现有图片的质感/表面/细节

## Hard Rules

1. **Execution mode selection**: If user says "只改XX，其他不变" or provides an existing product image (not raw product photos) and wants to refine specific aspects, use `local_edit` mode. Otherwise use `whole_image` mode.
2. Run this as a projectized workflow. Every product truth belongs to a project directory.
3. Ask for real product photos first. Prefer 3-8 photos from multiple angles and states.
4. Treat product structure as a first-class constraint. Do not reduce understanding to packaging shape only.
5. For any product whose internal structure affects realism, check cross-section, filling, layering, open/closed state, or internal material evidence before generation.
6. Use soft gating for missing evidence. Ask for more images first; continue only if the user accepts the risk explicitly.
7. Do not call raw image APIs directly. Delegate final generation to the locally installed `gpt-image2-gen` script.
8. Use pixel sizes only when calling `gpt-image2-gen`.
9. If project recall confidence is low, stop and ask for one more clue instead of guessing.
10. Default to the fast sub-2K resolution mapped from the requested ratio; only use higher resolutions when the user explicitly asks for 2K+, 4K, print, or high-res output.

## Workflow

```text
Project bootstrap:
Step 0  init_project or resume_project_context
Step 1  register_assets
Step 2  check_info_gaps
Step 3  build_product_profile
Step 4  analyze_references

Task loop:
Step 5  create_task
Step 6  register_task_assets
Step 7  build_task_brief
Step 8  record_confirmation (task_brief)
Step 9  build_camera_preview_prompt --task-id
Step 10 run_camera_preview --task-id
Step 11 record_confirmation (task_camera_preview)
Step 12 build_generation_prompt --task-id
Step 13 run_generation --task-id
Step 14 record_confirmation (task_generation_review)
Step 15 revise_task if needed

Legacy V1:
Step 5  build_creative_direction
Step 6  record_confirmation (creative_direction)
Step 7  build_generation_prompt
Step 8  run_generation
Step 9  record_confirmation (generation_review)
```

Local command base:

```bash
SKILL_DIR="$HOME/.codex/skills/product-photography-workflow"
```

## Step 0: Start Or Resume A Project

Create a dedicated project folder first:

```bash
python3 "$SKILL_DIR/scripts/init_project.py" \
  "产品名或项目名"
```

Resume an old project by natural-language clue:

```bash
python3 "$SKILL_DIR/scripts/resume_project_context.py" \
  --query "之前我们做的 XX 拍照项目"
```

If the match is ambiguous, ask the user for one more clue before continuing.

## Step 1: Register Project-Level Product Truth

Ask for:

- front view
- side view
- top view
- back view if rear shape matters
- open state if the product opens
- cross-section if internal structure matters
- detail close-ups for texture, seams, crumbs, gloss, pores, coating, fibers, or layers
- 1-2 style references if the user has a target visual language

Register all received product-truth images into the project:

```bash
python3 "$SKILL_DIR/scripts/register_assets.py" \
  --project-dir "[项目目录]" \
  --product-front "/abs/path/front.jpg" \
  --product-side "/abs/path/side.jpg" \
  --product-cross-section "/abs/path/cut.jpg" \
  --reference-style "/abs/path/style.jpg"
```

Default copy targets:

- `images/product_sources/`
- `images/reference_sources/`

## Step 2: Check Gaps

Run gap checking before any style imitation or task generation:

```bash
python3 "$SKILL_DIR/scripts/check_info_gaps.py" \
  --project-dir "[项目目录]" \
  --product-name "产品名" \
  --selling-points "夹心" \
  --selling-points "切面卖点"
```

If risk remains but the user still wants to continue, record it:

```bash
python3 "$SKILL_DIR/scripts/record_confirmation.py" \
  --project-dir "[项目目录]" \
  --kind risk_continue \
  --decision continue_with_risk \
  --note "用户接受当前素材不足带来的结构风险"
```

## Step 3: Build Product Profile

Lock product facts before style borrowing.

Use `build_product_profile.py` to capture at least:

- outer shape
- structure type
- open/close state
- cross-section requirement
- filling type and texture
- shell texture
- surface finish
- breakage pattern
- key identifiers
- must-show details
- must-not-fake details
- deformation rules

## Step 4: Analyze Style References

Summarize what the workflow may borrow from references:

- composition
- lighting
- background
- camera angle
- retouch level
- mood
- what to borrow only
- what to avoid

## Step 5: Create A New Task

Each task is one concrete requested image or one tightly coupled batch under the same project truth.

```bash
python3 "$SKILL_DIR/scripts/create_task.py" \
  --project-dir "[项目目录]" \
  --task-name "详情页主图摆拍" \
  --task-type "product_display" \
  --output-ratio "3:4"
```

Typical task types:

- `product_display`
- `detail_page_hero`
- `scene_insert`
- `cutaway_focus`
- `texture_refine` (use with `local_edit` execution mode)

## Execution Modes

This workflow supports two execution modes:

### Mode 1: `whole_image` (default)

**Use when**: Creating a new product photography image from scratch.

**Characteristics**:
- Rebuilds the entire image (composition, lighting, background, product placement)
- Requires camera preview confirmation before final generation
- Full 10-step workflow from project init to final output

**Trigger phrases**:
- "做产品图"
- "生成产品摄影图"
- "白底产品图"
- "根据产品真相照片生成摄影图"

### Mode 2: `local_edit`

**Use when**: Refining specific aspects of an existing product image while keeping everything else unchanged.

**Characteristics**:
- Takes an existing image as base (`--base-image`)
- Only modifies explicitly specified targets (`--editable-target`)
- Preserves composition, camera angle, lighting, and background
- **Skips camera preview** (Step 9-11) since layout is locked
- Much faster than `whole_image` mode

**Trigger phrases**:
- "只改质感" / "只改表皮" / "只改夹心"
- "其他不变" / "保持构图不变" / "保持机位不变"
- "修改现有图片的XX"
- "在这张图的基础上改XX"

**When to use `local_edit`**:
- User provides an existing product image (not raw product photos)
- User explicitly says "只改XX，其他不变"
- User wants to refine texture, surface finish, or filling appearance
- User wants to keep the current composition/lighting/background

**When NOT to use `local_edit`**:
- User provides raw product photos (white background, multiple angles) → use `whole_image`
- User wants to change composition, camera angle, or background → use `whole_image`
- User wants to add/remove props or change scene → use `whole_image`

**Example `local_edit` workflow**:

```bash
# Step 5: Create task with local_edit mode
python3 "$SKILL_DIR/scripts/create_task.py" \
  --project-dir "[项目目录]" \
  --task-name "曲奇质感优化" \
  --task-type "texture_refine" \
  --output-ratio "3:4"

# Step 6: Register the base image and texture reference
python3 "$SKILL_DIR/scripts/register_task_assets.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --texture-identity-reference "/abs/path/texture_reference.jpg"

# Step 7: Build task brief with local_edit mode
python3 "$SKILL_DIR/scripts/build_task_brief.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --execution-mode "local_edit" \
  --base-image "/abs/path/current_product_image.jpg" \
  --editable-target "曲奇表皮质感" \
  --editable-target "夹心流质状态" \
  --immutable-element "产品形态和堆叠方式" \
  --immutable-element "摄影机位和构图" \
  --immutable-element "光线方向和背景" \
  --anchor-object "盘子位置" \
  --spatial-relation "曲奇与盘子的相对位置不变" \
  --texture-priority "表皮光滑细腻" \
  --texture-priority "夹心呈流质状态" \
  --must-show "曲奇的完整形态" \
  --must-avoid "改变产品的整体构图"

# Step 8: Confirm task brief
python3 "$SKILL_DIR/scripts/record_confirmation.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --kind task_brief \
  --decision approve \
  --note "local_edit 模式确认，跳过机位预览"

# Step 9-11: SKIP (local_edit mode does not require camera preview)

# Step 12: Build generation prompt
python3 "$SKILL_DIR/scripts/build_generation_prompt.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]"

# Step 13: Run generation
python3 "$SKILL_DIR/scripts/run_generation.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]"
```

**Key parameters for `local_edit` mode**:
- `--execution-mode local_edit`: Activates local edit mode
- `--base-image`: The existing image to refine (required for local_edit)
- `--editable-target`: What can be changed (e.g., "表皮质感", "夹心流质")
- `--immutable-element`: What must stay unchanged (e.g., "构图", "机位", "背景")
- `--anchor-object`: Spatial anchors (e.g., "盘子位置")
- `--spatial-relation`: Spatial relationships to preserve (e.g., "曲奇与盘子的相对位置")

**Hard rule for `local_edit`**:
- If user says "只改XX，其他不变", you MUST use `local_edit` mode, not `whole_image`
- If you use `whole_image` when user wants `local_edit`, the entire composition will change

Default resolution policy for task ratios:

- `1:1` → `1920x1920`
- `4:5` → `1536x1920`
- `3:4` → `1440x1920`
- `9:16` → `1080x1920`
- `16:9` → `1920x1080`

If the user only says a ratio and does not specify pixels, use the mapped resolution above.
For higher resolution needs (2K+), user should explicitly request it.

## Step 6: Register Task References

Use task references for page-specific needs, not for rewriting product truth.

```bash
python3 "$SKILL_DIR/scripts/register_task_assets.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --page-draft "/abs/path/draft.png" \
  --camera-storyboard-reference "/abs/path/storyboard.png" \
  --composition-reference "/abs/path/angle.png" \
  --style-reference "/abs/path/style.png" \
  --lighting-reference "/abs/path/light.png" \
  --scene-reference "/abs/path/scene.png" \
  --product-state-reference "/abs/path/cut.png" \
  --package-material-reference "/abs/path/package-material.png" \
  --texture-identity-reference "/abs/path/texture.png"
```

Reference intent:

- `page_draft`: long-detail-page draft or layout preview
- `camera_storyboard_reference`: shot intent only. Use it to tell the workflow how you want to shoot. It no longer directly owns the final layout once a camera preview has been confirmed.
- `composition_reference`: generic framing inspiration. When no storyboard exists, it can help build the camera preview. Once a camera preview is confirmed, it drops to a secondary hint.
- `style_reference`: style language, palette, retouch feel
- `lighting_reference`: light direction, contrast, highlight/shadow behavior
- `scene_reference`: environment, tone, background, props language
- `product_state_reference`: cut-open state, internal exposure, specific angle/state
- `package_material_reference`: packaging material truth only. Use for matte/gloss type, film or paper feel, seal edges, thickness, stiffness, folds, and reflection character.
- `texture_identity_reference`: material truth only. Use for cross-section, pores, shell detail, crumbs, broken edge, filling thickness, and surface finish.
- `other_reference`: auxiliary hint only

Authority order for multi-reference tasks:

- real product photos always win for anatomy, material, filling, and shape truth
- `package_material_reference` is the highest supplemental authority for packaging material truth, but must not take over composition or food texture
- `texture_identity_reference` is the highest supplemental authority for food/content texture truth, but must not take over scene composition
- confirmed camera preview wins for final layout, camera angle, crop, whitespace, focus, and key light direction
- latest `camera_storyboard_reference` and latest `composition_reference` are used to build the camera preview, not to bypass it
- `style_reference` and `lighting_reference` may influence tone only, never product geometry
- `scene_reference` may influence environment only
- `product_state_reference` may influence break/open state only

How to prepare a `camera_storyboard_reference`:

- recommend 4-9 panels
- mark the hero shot camera angle
- mark the cutaway close-up angle if needed
- mark subject direction
- mark whitespace positions
- mark key light direction
- mark the main focus anchor

How to prepare a `texture_identity_reference`:

- include one full product view for context
- include a cross-section close-up
- include a shell close-up
- include a filling close-up when relevant
- include broken-edge or crumb detail
- include powder, sugar frost, gloss, matte, or surface reflection state when relevant

How to prepare a `package_material_reference`:

- include one full package view for context
- include a close-up of the package surface
- include seal edges, center seal, zipper, tear notch, or fold details when relevant
- include one photo that clearly shows matte vs glossy vs metallic reflection behavior
- include thickness, puff, stiffness, dent, wrinkle, or crease evidence when relevant

Hard rule for food products:

- cross-section truth and texture truth are more important than style completeness
- if cross-section evidence is weak, ask for more material first before generation

## Step 7: Build Task Brief

Convert the user request into a task-level confirmation document:

```bash
python3 "$SKILL_DIR/scripts/build_task_brief.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --task-goal "做一张详情页摆拍图" \
  --output-ratio "3:4" \
  --hero-shot-intent "主图机位锁定在三分之二侧前方" \
  --camera-angle-lock "以角度故事板为主机位 authority" \
  --texture-priority "先保住切面孔洞和夹心厚度"
```

The brief should clarify:

- what this image is for
- which references are task-only
- whether layout authority and style/lighting authority are split across different references
- which product state must appear
- whether `camera_plan` is filled for hero / main image tasks
- whether `texture_plan` is filled for food texture / cross-section tasks
- must-show elements
- must-avoid elements
- placement or whitespace requirements

The brief now carries two explicit planning blocks:

- `camera_plan`
  - `hero_shot_intent`
  - `shot_priority`
  - `camera_angle_lock`
  - `crop_and_whitespace_lock`
  - `lighting_direction_lock`
  - `focus_anchor`
- `texture_plan`
  - `texture_priority`
  - `must_match_texture_points`
  - `cross_section_truth_lock`
  - `surface_finish_lock`
  - `fake_texture_risks`
- `package_material_plan`
  - `package_material_priority`
  - `material_type_lock`
  - `finish_lock`
  - `structure_detail_lock`
  - `reflection_lock`
  - `fake_package_material_risks`

Soft-gate behavior:

- if a main-image / hero task has no `camera_plan`, the workflow continues but writes a planning warning
- if a food / cross-section task has no `texture_plan`, the workflow continues but writes a planning warning
- the warning must be reviewed with the user before generation

## Step 8: Record Task Brief Confirmation

Do not generate without this gate.

```bash
python3 "$SKILL_DIR/scripts/record_confirmation.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --kind task_brief \
  --decision approve \
  --note "任务简报确认，可以进入生图"
```

For normal whole-image tasks, this confirmation unlocks the camera preview stage, not the final image stage.

## Step 9: Build Camera Preview Prompt

Create a fixed grayscale camera-preview prompt first:

```bash
python3 "$SKILL_DIR/scripts/build_camera_preview_prompt.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]"
```

This prompt always aims for:

- white background
- grayscale block shapes
- low detail
- no food texture rendering
- only camera angle, perspective, crop, whitespace, placement, and key light direction

## Step 10: Run Camera Preview

```bash
python3 "$SKILL_DIR/scripts/run_camera_preview.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]"
```

The result is stored under:

- `tasks/[task_id]/previews/[preview_id]/preview.png`
- `tasks/[task_id]/camera_preview_manifest.json`

## Step 11: Record Camera Preview Confirmation

The final image is blocked until this gate is approved.

```bash
python3 "$SKILL_DIR/scripts/record_confirmation.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --kind task_camera_preview \
  --decision approve \
  --note "机位确认通过" \
  --selected-output "[preview.png 绝对路径]"
```

## Step 12: Build Task Prompt Package

Generate the prompt package from project truth plus confirmed task brief:

```bash
python3 "$SKILL_DIR/scripts/build_generation_prompt.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]"
```

This creates task-scoped files such as:

- `prompts/prompt_V001.md`
- `prompts/negative_prompt_V001.md`
- `prompts/prompt_package.json`

The final prompt now follows a fixed skeleton:

- 出图目标
- 产品真相锁定
- 机位锁定
- 质感锁定
- 光影锁定
- 禁止项

## Step 13: Run Task Generation Through gpt-image2-gen

Use the wrapper script instead of constructing raw API calls:

```bash
python3 "$SKILL_DIR/scripts/run_generation.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]"
```

This script:

- reads the task prompt
- injects project-level product truth refs as `--ref-product`
- injects the confirmed camera preview as `--ref-layout` for normal whole-image tasks
- keeps `camera_storyboard_reference` as upstream shot-planning input instead of direct final layout authority
- injects task style and lighting refs as `--ref-style`
- injects `package_material_reference` into `--ref-product` as packaging material truth supplement
- injects `texture_identity_reference` into `--ref-product` as texture truth supplement
- keeps `product_state_reference` in `--ref-product` for cut-open state only
- downgrades `composition_reference` to generic `--reference` hints once a camera preview is confirmed
- injects task refs as `--reference` / `--ref-background` / extra `--ref-product`
- maps ratio to pixel size
- calls `gpt-image2-gen`
- writes output into `tasks/[task_id]/versions/[version_id]/generated.png`
- stores metadata in the task `generation_manifest.json`, including confirmed camera preview id and mounted package-material / texture refs for later review

For dry verification:

```bash
python3 "$SKILL_DIR/scripts/run_generation.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --dry-run
```

## Step 14: Record Task Generation Review

After the first round, record whether the user approves or requests revision:

```bash
python3 "$SKILL_DIR/scripts/record_confirmation.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --kind task_generation_review \
  --decision revise \
  --note "保留结构理解，改成更干净的白底和更柔的光"
```

## Step 15: Create A New Version Instead Of Overwriting

If the task needs another round, create a new version:

```bash
python3 "$SKILL_DIR/scripts/revise_task.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --note "增加切面展示权重"
```

This keeps old outputs and switches the task to the next version scaffold.

Default behavior:

- if you only change texture or lighting, the workflow keeps the confirmed camera preview
- if you also need to change camera angle, reset the preview gate:

```bash
python3 "$SKILL_DIR/scripts/revise_task.py" \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --note "机位也要一起改" \
  --reset-camera-preview
```

## Legacy V1 Path

Keep this only for simple one-shot still-life requests with no ongoing task tree.

Use:

- `build_creative_direction.py`
- `record_confirmation.py --kind creative_direction`
- `build_generation_prompt.py` without `--task-id`
- `run_generation.py` without `--task-id`
- `record_confirmation.py --kind generation_review`

## Structure-Sensitive Products

Treat these as structure-critical by default:

- filled bakery
- layered snacks
- molten products
- coated products
- products whose opened state differs from closed state
- products whose cut section is a selling point

If internal structure matters, do not continue as if exterior photos are enough.

## References

- [project-files.md](references/project-files.md)
- [pressure-scenarios.md](references/pressure-scenarios.md)


---


## 📁 执行目录索引设置

在任务执行过程中，需要维护执行目录与记忆系统的关联：

### 1. 设置执行工作目录

```bash
# 定义实际执行工作目录（根据 skill 类型调整）
EXECUTION_WORKSPACE="/Users/a123/.openclaw/workspace-design/outputs/${PROJECT_NAME}_$(date +%Y%m%d)"

# 或者
EXECUTION_WORKSPACE="/Users/a123/.openclaw/workspace-strategy/outputs/${PROJECT_NAME}_$(date +%Y%m%d)"

# 创建执行目录
mkdir -p "$EXECUTION_WORKSPACE"
```

### 2. 更新项目的执行目录索引

```bash
# 更新 project.json
python3 /Users/a123/.openclaw/scripts/memory/project.py update-execution   --project-id "$PROJECT_ID"   --execution-workspace "$EXECUTION_WORKSPACE"   --work-stage "策略制定"
```

### 3. 更新任务的执行目录索引

```bash
# 更新 task.json
python3 /Users/a123/.openclaw/scripts/memory/task.py update-execution   --task-id "$TASK_ID"   --execution-workspace "$EXECUTION_WORKSPACE"   --work-stage "初稿完成"   --key-file "strategy" "$EXECUTION_WORKSPACE/strategy_v1.md"   --key-file "wireframe" "$EXECUTION_WORKSPACE/wireframe_v1.png"
```

### 4. 创建执行索引文件（可选但推荐）

```bash
# 在项目目录创建索引文件
cat > "$PROJECT_PATH/execution_index.json" << 'EOF'
{
  "execution_workspace": "$EXECUTION_WORKSPACE",
  "key_files": {
    "strategy": "$EXECUTION_WORKSPACE/strategy_v1.md",
    "wireframe": "$EXECUTION_WORKSPACE/wireframe_v1.png",
    "final_output": "$EXECUTION_WORKSPACE/final_v1.png"
  },
  "work_stages": [
    {"stage": "策略制定", "completed_at": "2026-06-17T10:00:00"},
    {"stage": "初稿设计", "completed_at": "2026-06-17T15:00:00"}
  ],
  "last_updated": "$(date -Iseconds)"
}
EOF

# 创建可读的 README
cat > "$PROJECT_PATH/README_执行索引.md" << 'EOF'
# 执行目录索引

## 实际执行工作目录
$EXECUTION_WORKSPACE

## 关键文件
- 策略文档: strategy_v1.md
- 线框图: wireframe_v1.png
- 最终产出: final_v1.png

## 工作阶段
- [x] 策略制定
- [x] 初稿设计
- [ ] 最终成稿
EOF
```

### 5. 在执行工作目录创建回链（推荐）

```bash
# 在执行工作目录创建指向记忆系统的链接
cat > "$EXECUTION_WORKSPACE/memory_link.json" << EOF
{
  "project_id": "$PROJECT_ID",
  "task_id": "$TASK_ID",
  "project_path": "$PROJECT_PATH",
  "task_path": "$TASK_PATH",
  "memory_system_root": "/Users/a123/.openclaw/projects"
}
EOF
```

**为什么需要执行目录索引？**

1. **回溯能力**：未来回忆项目时，能准确找到所有执行文件
2. **关键文件定位**：知道策略文档、设计稿、最终产出的具体位置
3. **工作连续性**：不同 agent 接手时能快速了解工作状态和文件位置
4. **审计追溯**：完整记录从立项到交付的所有关键节点和文件

---

## 📦 产出归档（执行后必须）

任务完成后，必须将产出归档到记忆系统：

```bash
# 1. 保存产出到任务系统
python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
  --task-id "$TASK_ID" \
  --file "${OUTPUT_FILE_PATH}" \
  --note "${VERSION_NOTE}" \
  --expire-days 30 \
  --prompt "${GENERATION_PROMPT}" \
  --model "${MODEL_USED}" \
  --json

echo "✅ 产出已归档（30天后自动清理）"

# 2. 更新任务状态
python3 /Users/a123/.openclaw/scripts/memory/task.py update-status \
  --task-id "$TASK_ID" \
  --status "completed"

echo "✅ 任务状态已更新为完成"

# 3. 查看任务的所有版本
python3 /Users/a123/.openclaw/scripts/memory/task.py list-iterations \
  --task-id "$TASK_ID"
```

**变量说明**：

- `OUTPUT_FILE_PATH`: 产出文件的绝对路径
- `VERSION_NOTE`: 版本说明（如"初稿"、"客户反馈后修改"）
- `GENERATION_PROMPT`: 生成时使用的 prompt（可选）
- `MODEL_USED`: 使用的模型名称（可选）

**归档后的效果**：

- ✅ 自动版本化（v1, v2, v3...）
- ✅ 记录生成参数和 prompt
- ✅ 设置过期时间（30天后自动清理）
- ✅ 可通过任务 ID 追溯所有历史版本
- ✅ 产出文件自动复制到项目 tasks 目录下

---
