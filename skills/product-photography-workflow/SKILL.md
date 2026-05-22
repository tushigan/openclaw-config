---
name: product-photography-workflow
description: Use when users ask for product photography, product still-life images, white-background product shots, clean tabletop product visuals, or product-image generation based on real product photos and style references, especially when the same product may need multiple continued tasks over time.
---

# Product Photography Workflow

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

## Hard Rules

1. Run this as a projectized workflow. Every product truth belongs to a project directory.
2. Ask for real product photos first. Prefer 3-8 photos from multiple angles and states.
3. Treat product structure as a first-class constraint. Do not reduce understanding to packaging shape only.
4. For any product whose internal structure affects realism, check cross-section, filling, layering, open/closed state, or internal material evidence before generation.
5. Use soft gating for missing evidence. Ask for more images first; continue only if the user accepts the risk explicitly.
6. Do not call raw image APIs directly. Delegate final generation to `/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py`.
7. Use pixel sizes only when calling `gpt-image2-gen`.
8. If project recall confidence is low, stop and ask for one more clue instead of guessing.
9. Unless the user explicitly asks for a smaller draft, default to the highest safe resolution allowed by the requested ratio.

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
Step 9  build_generation_prompt --task-id
Step 10 run_generation --task-id
Step 11 record_confirmation (task_generation_review)
Step 12 revise_task if needed

Legacy V1:
Step 5  build_creative_direction
Step 6  record_confirmation (creative_direction)
Step 7  build_generation_prompt
Step 8  run_generation
Step 9  record_confirmation (generation_review)
```

## Step 0: Start Or Resume A Project

Create a dedicated project folder first:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/init_project.py \
  "产品名或项目名"
```

Resume an old project by natural-language clue:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/resume_project_context.py \
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
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/register_assets.py \
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
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/check_info_gaps.py \
  --project-dir "[项目目录]" \
  --product-name "产品名" \
  --selling-points "夹心" \
  --selling-points "切面卖点"
```

If risk remains but the user still wants to continue, record it:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/record_confirmation.py \
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
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/create_task.py \
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

Default resolution policy for task ratios:

- `1:1` → `2880x2880`
- `4:5` → `2560x3200`
- `3:4` → `2448x3264`
- `9:16` → `2160x3840`
- `16:9` → `3840x2160`

If the user only says a ratio and does not specify pixels, use the mapped highest safe resolution above.

## Step 6: Register Task References

Use task references for page-specific needs, not for rewriting product truth.

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/register_task_assets.py \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --page-draft "/abs/path/draft.png" \
  --composition-reference "/abs/path/angle.png" \
  --style-reference "/abs/path/style.png" \
  --lighting-reference "/abs/path/light.png" \
  --scene-reference "/abs/path/scene.png" \
  --product-state-reference "/abs/path/cut.png"
```

Reference intent:

- `page_draft`: long-detail-page draft or layout preview
- `composition_reference`: framing, crop, pose, arrangement. If multiple are registered, the newest one becomes the active layout authority for generation.
- `style_reference`: style language, palette, retouch feel
- `lighting_reference`: light direction, contrast, highlight/shadow behavior
- `scene_reference`: environment, tone, background, props language
- `product_state_reference`: cut-open state, internal exposure, specific angle/state
- `other_reference`: auxiliary hint only

Authority order for multi-reference tasks:

- real product photos always win for anatomy, material, filling, and shape truth
- latest `composition_reference` wins for layout and placement
- `style_reference` and `lighting_reference` may influence tone only, never product geometry
- `scene_reference` may influence environment only
- `product_state_reference` may influence break/open state only

## Step 7: Build Task Brief

Convert the user request into a task-level confirmation document:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_task_brief.py \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --task-goal "做一张详情页摆拍图" \
  --output-ratio "3:4"
```

The brief should clarify:

- what this image is for
- which references are task-only
- whether layout authority and style/lighting authority are split across different references
- which product state must appear
- must-show elements
- must-avoid elements
- placement or whitespace requirements

## Step 8: Record Task Brief Confirmation

Do not generate without this gate.

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/record_confirmation.py \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --kind task_brief \
  --decision approve \
  --note "任务简报确认，可以进入生图"
```

## Step 9: Build Task Prompt Package

Generate the prompt package from project truth plus confirmed task brief:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_generation_prompt.py \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]"
```

This creates task-scoped files such as:

- `prompts/prompt_V001.md`
- `prompts/negative_prompt_V001.md`
- `prompts/prompt_package.json`

## Step 10: Run Task Generation Through gpt-image2-gen

Use the wrapper script instead of constructing raw API calls:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/run_generation.py \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]"
```

This script:

- reads the task prompt
- injects project-level product truth refs as `--ref-product`
- injects the active task layout ref as `--ref-layout`
- injects task style and lighting refs as `--ref-style`
- injects task refs as `--reference` / `--ref-background` / extra `--ref-product`
- maps ratio to pixel size
- calls `gpt-image2-gen`
- writes output into `tasks/[task_id]/versions/[version_id]/generated.png`
- stores metadata in the task `generation_manifest.json`

For dry verification:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/run_generation.py \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --dry-run
```

## Step 11: Record Task Generation Review

After the first round, record whether the user approves or requests revision:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/record_confirmation.py \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --kind task_generation_review \
  --decision revise \
  --note "保留结构理解，改成更干净的白底和更柔的光"
```

## Step 12: Create A New Version Instead Of Overwriting

If the task needs another round, create a new version:

```bash
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/revise_task.py \
  --project-dir "[项目目录]" \
  --task-id "[任务ID]" \
  --note "增加切面展示权重"
```

This keeps old outputs and switches the task to the next version scaffold.

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
