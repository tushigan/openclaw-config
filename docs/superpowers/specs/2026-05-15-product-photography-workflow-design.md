# Product Photography Workflow Design

## Goal

Upgrade `product-photography-workflow` from a single-run still-life flow into a resumable project system for real production work:

1. One project represents one stable product truth
2. The same project can accumulate many image tasks over time
3. Each task can carry its own page draft, composition references, scene references, and product-state references
4. The skill can resume old projects from natural-language recall in Feishu
5. Task revisions keep history instead of overwriting prior outputs
6. Final image generation still delegates to the existing `gpt-image2-gen` backend

## Why V1 Is Not Enough

V1 assumes:

- one intake
- one direction confirmation
- one generation package

That works for a simple “give me a product photo” request, but not for the actual workflow described by the user:

- the client sends a real product after the detail-page draft already exists
- the product truth remains stable across the project
- multiple future images are requested under the same project
- each requested image may need different references and constraints
- the team needs to revisit the same project days later by memory, not by rigid command syntax

## Scope

### V2 in scope

- project recall from natural-language mention of a prior shoot project
- project-level product truth shared across all tasks
- multiple tasks under one project
- task-specific references and confirmations
- versioned revisions for task updates
- one approved final image per task by default
- resumable JSON state and audit trail

### Still out of scope

- automatic shot extraction from a long detail-page draft
- automatic semantic image understanding inside the scripts
- human subjects and complex hero ads
- layout-to-PNG compositing inside this skill
- full production scheduling or delivery approval workflows

## User Interaction Model

### Project recall

The user will not usually say “open project X” in a rigid way. The expected natural entry is:

- “还记得之前我们做的 XX 拍照项目吗”

The skill must:

1. search for the most likely project by project name, product name, and aliases
2. refuse to continue if confidence is low
3. restore the project context before asking for the next action

### Project continuation

After recall succeeds, the user may:

- add a new task
- revise an existing task
- resend references
- regenerate a task version

### Task entry

The user should be able to attach all task references together without manually classifying each one first.

The skill will classify the task references into:

- `page_draft`
- `composition_reference`
- `scene_reference`
- `product_state_reference`

Then it presents a confirmation summary before generation.

## Core Model

### Project

One project is the long-lived container for a single product truth.

Project-level data includes:

- stable product identity
- project-level product assets
- product structure and deformation rules
- recall aliases and summary
- task registry

### Task

One task is one requested image under the project.

Task-level data includes:

- task brief
- task-specific references
- task-specific constraints
- confirmation gates
- generation history
- selected or latest version

### Version

If the user says “这张图改一下”, the skill must create a new version instead of overwriting the original task output.

## Workflow

```text
Project recall
→ resume project context
→ create task or choose task to revise
→ classify task references
→ check task gaps
→ build task brief
→ confirm task understanding
→ build task prompt
→ run generation
→ review result
→ approve or create next version
```

## Confirmation Gates

### Gate 1: project recall confidence

If the skill cannot confidently map the user’s natural-language memory cue to a single project, it must stop and ask for one more clue.

### Gate 2: task reference classification

Before generation, the skill must show how it interpreted the new task references:

- which image is the page draft
- which image drives composition
- which image drives scene
- which image clarifies product state

### Gate 3: task brief approval

The skill must confirm:

- product truth is inherited from the project
- the new task goal is understood
- the right product state is being used
- the right visual references are attached

### Gate 4: generation review

The user either:

- approves the task result
- requests a revised version

## File Layout

```text
workspace/outputs/{project_name}_{project_suffix}/
├── project_state.json
├── intake_manifest.json
├── assets_manifest.json
├── product_profile.json
├── reference_analysis.json
├── project_recall.json
├── tasks_manifest.json
├── generation_manifest.json                 # legacy-compatible summary only
├── delivery_manifest.json
├── audit_log.jsonl
├── images/
│   ├── product_sources/
│   ├── reference_sources/
│   ├── generated_drafts/
│   └── final_delivery/
├── prompts/
├── reports/
└── tasks/
    ├── TASK-001-hero-flatlay/
    │   ├── task_state.json
    │   ├── task_assets.json
    │   ├── task_brief.json
    │   ├── confirmation_log.jsonl
    │   ├── generation_manifest.json
    │   ├── prompts/
    │   │   ├── prompt_v1.md
    │   │   └── negative_prompt_v1.md
    │   ├── reports/
    │   │   ├── task_summary.md
    │   │   └── task_reference_summary.md
    │   └── versions/
    │       ├── V001/
    │       └── V002/
    └── TASK-002-scene-shot/
```

## JSON Responsibilities

### `project_state.json`

Tracks:

- schema version
- project mode (`multi_task_v2`)
- recall aliases
- current active task
- artifact paths
- workflow flags

### `tasks_manifest.json`

Registry of all tasks:

- task id
- task slug
- task name
- task status
- created/updated timestamps
- latest version id
- latest output path
- tags

### `tasks/*/task_state.json`

Tracks:

- task lifecycle stage
- task goal
- task type (`product_display`, `scene`, `cross_section`, etc.)
- inherited product truth snapshot metadata
- current selected version
- gate flags

### `tasks/*/task_assets.json`

Tracks task-specific references by role:

- `page_draft`
- `composition_reference`
- `scene_reference`
- `product_state_reference`
- `other_reference`

### `tasks/*/task_brief.json`

Stores the confirmed task understanding:

- purpose
- output ratio
- must-show elements
- must-avoid elements
- scene rules
- placement rules
- product-state rules

### `tasks/*/generation_manifest.json`

Tracks all generations for that task:

- version id
- prompt path
- reference bundle used
- command summary
- output path
- review decision

## Script Changes

### Existing scripts to keep and adapt

- `init_project.py`
- `register_assets.py`
- `record_confirmation.py`
- `build_generation_prompt.py`
- `run_generation.py`
- `common.py`

### New scripts to add

- `find_project.py`
- `resume_project_context.py`
- `create_task.py`
- `register_task_assets.py`
- `build_task_brief.py`
- `list_project_tasks.py`
- `revise_task.py`

## Backward Compatibility

The upgrade must not break V1 project folders or the current still-life path.

Rules:

1. old project folders remain readable
2. V2 files are additive
3. existing scripts keep their current arguments where possible
4. task-aware generation is an extension, not a rewrite that strands the old flow

## Testing Strategy

The skill lives in a configuration repo with Python scripts and no global package harness. V2 should therefore rely on focused CLI regression tests:

- initialize a project
- register project assets
- create a task
- register task assets
- build a task brief
- create a revision
- verify JSON state transitions and task manifests

## Success Criteria

V2 is successful when the user can:

1. recall a prior project by natural language
2. continue that project without rebuilding product truth
3. add a new task with its own references
4. revise a task without overwriting history
5. keep using the existing generation backend after the new task brief is confirmed
