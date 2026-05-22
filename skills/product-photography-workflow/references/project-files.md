# Project Files

## Project root

- `project_state.json`
  Stores the current project stage, gate flags, active task id, and core artifact paths.

- `intake_manifest.json`
  Stores user intent, gap reports, risk confirmations, and collection notes.

- `assets_manifest.json`
  Registers project-level product photos and reusable style references.

- `product_profile.json`
  Locks stable product truth: shape, structure, filling, texture, deformation rules, and must-show details.

- `reference_analysis.json`
  Summarizes what may be borrowed from global style references.

- `creative_direction.json`
  Legacy V1 direction file for single-run still-life flows.

- `generation_manifest.json`
  Legacy V1 generation rounds and review decisions.

- `delivery_manifest.json`
  Delivery bookkeeping for the project-level flow.

- `tasks_manifest.json`
  Registry of all tasks inside the project, including task ids, statuses, active versions, and latest outputs.

- `project_recall.json`
  Natural-language recall aliases and last successful query snapshot.

- `audit_log.jsonl`
  Append-only project event log.

## Project asset folders

- `images/product_sources/`
  Copied or linked project-truth product photos.

- `images/reference_sources/`
  Copied or linked reusable style references.

- `images/generated_drafts/`
  Legacy V1 generated drafts.

- `images/final_delivery/`
  Legacy V1 final delivery area.

- `prompts/`
  Legacy V1 prompt files.

- `reports/`
  Project-level human-readable summaries such as product understanding and style notes.

- `tasks/`
  One subfolder per task.

## Task folder

Path pattern:

- `tasks/[task_id]/`

Core task files:

- `task_state.json`
  Stores the task stage, selected version, workflow flags, and latest output.

- `task_assets.json`
  Registers task-only references such as page drafts, scene references, and product-state references.

- `task_brief.json`
  The confirmed task brief for one requested image direction.

- `generation_manifest.json`
  Versioned generation records for this task.

- `confirmation_log.jsonl`
  Append-only task confirmation history.

Task subfolders:

- `references/page_draft/`
- `references/composition_reference/`
- `references/scene_reference/`
- `references/product_state_reference/`
- `references/other_reference/`
- `prompts/`
- `reports/`
- `versions/`

## Task version outputs

Path pattern:

- `tasks/[task_id]/versions/[version_id]/generated.png`

Version notes live in the task `generation_manifest.json`; old versions are preserved and should not be overwritten.

## Prompt files

Legacy V1:

- `prompts/prompt_v1.md`
- `prompts/negative_prompt.md`
- `prompts/prompt_package.json`

Task V2:

- `tasks/[task_id]/prompts/prompt_V001.md`
- `tasks/[task_id]/prompts/negative_prompt_V001.md`
- `tasks/[task_id]/prompts/prompt_package.json`
