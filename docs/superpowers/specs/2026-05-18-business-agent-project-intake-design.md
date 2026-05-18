# Business Agent Project Intake Design

## Goal

Add a new `business` agent that can receive business docking requests, collect context across multiple rounds, create and maintain long-lived project records, archive incoming Feishu materials into the project, and hand the project into the existing quote workflow only when the user explicitly starts quoting.

## Why This Is Needed

The current setup has a mature quote workflow, but it starts too late in the real business process.

The user’s actual workflow begins earlier:

- a client need appears before scope is stable
- background information arrives across multiple conversations
- Feishu voice recordings, screenshots, and现场 photos arrive incrementally
- quoting may happen only after several rounds of沟通
- the team still needs one stable place to see project status, key facts, next actions, and materials

Without a dedicated business project layer, these early-stage facts are fragmented across sessions and media folders, and the quote skill becomes the first durable record even though it should only own the quoting phase.

## Scope

### In Scope

- add a new `business` agent and `business-shared` agent
- add a new `workspace-business`
- add a new skill for business intake and project lifecycle management
- create durable project folders under `workspace-business/projects/客户名/项目名/`
- define JSON records for project truth, materials, progress, tasks, and quote handoff
- copy incoming Feishu media into project-local archives
- generate meeting notes and update project records when audio materials arrive
- integrate the existing `quote-skill` through a handoff and embedded `quote/` subproject
- keep quote outputs inside the business project directory

### Out of Scope

- full CRM features such as opportunity pipelines, approval chains, and contact databases
- automatic quote pricing decisions
- automatic outbound delivery or customer messaging without the existing user confirmation rules
- rewriting the quote rendering core

## Approved Decisions

The design reflects these confirmed decisions:

- project records live in the new agent workspace, not inside the skill
- project hierarchy is `客户/项目`
- quote workflow is semi-automatic, not auto-triggered
- formal project creation happens only after minimum fields are present
- incoming materials are copied into the project and also registered in JSON
- business stages use `线索 → 初沟通 → 需求梳理 → 方案中 → 待报价 → 报价中 → 谈判中 → 成交/搁置`
- audio handling defaults to archive + notes + project update + next tasks
- quote outputs live in `quote/` under the business project

## User Interaction Model

### Intake trigger

When the `business` agent receives a docking request, it first checks whether enough structured information exists to create a formal project.

Minimum required fields:

- `client_name`
- `project_name`
- `current_goal`
- at least one `source_material`

If any required field is missing, the agent stays in pre-project collection mode and asks only for the missing minimum fields.

### Project creation

Once the minimum fields are available, the agent creates a formal project directory and initializes the JSON records.

### Ongoing update

After the project exists, every new material or conversation update should map into one or more of:

- material archive update
- progress timeline update
- task update
- project summary refresh

### Quote transition

The agent does not enter quoting only because quoting looks close.

The quote handoff begins only when:

1. the business stage has reached a quote-ready state such as `待报价`
2. the user explicitly asks to start quoting

## Business Stage Model

The project uses this default stage sequence:

`线索 → 初沟通 → 需求梳理 → 方案中 → 待报价 → 报价中 → 谈判中 → 成交/搁置`

This stage model must be treated as durable project state, not just temporary conversation context.

## Architecture

### Agent layer

Add:

- `business`
- `business-shared`

Both use the same workspace:

- `/Users/a123/.openclaw/workspace-business`

`main` and `main-shared` should be allowed to dispatch to the new business agents in the same way they dispatch to the current expert agents.

### Workspace layer

The workspace becomes the long-lived source of truth for business-stage project memory.

It stores:

- project records
- archived materials
- generated notes and summaries
- quote handoff state
- embedded quote versions and outputs

### Skill layer

Add a new skill:

- `/Users/a123/.openclaw/skills/business-project-intake/`

This skill is responsible for the business workflow, not for owning the project storage root.

Its job is to:

- check whether an incoming request maps to a new or existing project
- collect minimum fields
- create project records
- archive materials
- summarize incoming audio and image-based context
- update progress and tasks
- prepare quote handoff records
- invoke `quote-skill` only when the user starts the quote phase

### Quote integration layer

The quote workflow remains a separate skill, but its project storage for business-managed projects moves into the business project:

- `/Users/a123/.openclaw/workspace-business/projects/客户名/项目名/quote/`

This keeps business history and quote history in the same project universe.

## File Layout

```text
/Users/a123/.openclaw/workspace-business/
├── AGENTS.md
├── IDENTITY.md
├── SOUL.md
├── USER.md
├── TOOLS.md
├── MEMORY.md
├── outputs/
└── projects/
    └── 客户名/
        └── 项目名/
            ├── project.json
            ├── materials.json
            ├── progress.json
            ├── tasks.json
            ├── quote-handoff.json
            ├── materials/
            │   ├── audio/
            │   ├── images/
            │   ├── docs/
            │   └── chat/
            ├── notes/
            │   ├── meeting-notes/
            │   ├── briefs/
            │   └── summaries/
            ├── outputs/
            │   ├── handoff/
            │   └── reports/
            └── quote/
                ├── project.json
                ├── source-materials/
                ├── working-notes/
                └── versions/
                    ├── v1/
                    └── v2/
```

## JSON Responsibilities

### `project.json`

This is the main project truth. It answers:

- who the client is
- what the project is
- what stage it is in
- what the current goal is
- what the next action is
- whether quote work has started

Required fields:

- `schema_version`
- `project_id`
- `client_name`
- `project_name`
- `project_slug`
- `current_stage`
- `lifecycle_status`
- `current_goal`
- `project_summary`
- `background_summary`
- `requirement_summary`
- `recommended_case_type`
- `quote_status`
- `created_at`
- `updated_at`
- `last_activity_at`
- `next_action_summary`
- `primary_contact`
- `source_channels`
- `tags`
- `material_count`
- `latest_material_id`
- `latest_progress_id`
- `current_quote_version`
- `quote_project_dir`

### `materials.json`

This is the authoritative registry of archived materials.

Root fields:

- `schema_version`
- `project_id`
- `items`

Each item includes:

- `material_id`
- `type`
- `title`
- `source_channel`
- `original_name`
- `stored_path`
- `copied_at`
- `captured_at`
- `mime_type`
- `tags`
- `summary`
- `transcript_path`
- `note_path`
- `processing_status`
- `related_progress_ids`
- `related_task_ids`

### `progress.json`

This is the project timeline and stage-change log.

Root fields:

- `schema_version`
- `project_id`
- `entries`

Each entry includes:

- `progress_id`
- `recorded_at`
- `event_type`
- `stage_before`
- `stage_after`
- `summary`
- `details`
- `key_decisions`
- `open_questions`
- `blockers`
- `next_actions`
- `source_material_ids`
- `note_path`
- `recorded_by`

### `tasks.json`

This is the follow-up execution list for the project.

Root fields:

- `schema_version`
- `project_id`
- `tasks`

Each task includes:

- `task_id`
- `title`
- `description`
- `status`
- `priority`
- `owner`
- `due_at`
- `created_at`
- `updated_at`
- `source_progress_id`
- `related_material_ids`
- `related_quote_version`
- `completion_note`

### `quote-handoff.json`

This is the transition record from business coordination into quoting.

Root fields:

- `schema_version`
- `project_id`
- `handoff_status`
- `prepared_at`
- `prepared_by`
- `trigger_reason`
- `client_name`
- `project_name`
- `current_stage`
- `business_goal`
- `recommended_case_type`
- `confirmed_scope`
- `excluded_scope`
- `key_requirements`
- `key_decisions`
- `open_questions`
- `material_refs`
- `meeting_note_refs`
- `quote_project_dir`
- `current_quote_version`
- `quote_output_refs`
- `last_quote_generated_at`
- `quote_followup_summary`

## Default Material Handling

### Audio

When a Feishu recording arrives for an existing project, the agent should:

1. copy the original file into `materials/audio/`
2. add a material registry entry
3. produce a meeting note under `notes/meeting-notes/`
4. summarize key decisions, requirements, blockers, and next actions
5. append a `progress.json` entry
6. update `project.json` summary fields
7. create or update follow-up tasks in `tasks.json`

### Images

When screenshots,现场 photos, or reference images arrive, the agent should:

1. copy the original file into `materials/images/`
2. add a material registry entry
3. summarize why the image matters if the use is clear
4. link the material to project progress or quote handoff when relevant

### Documents and chat extracts

Documents and structured chat extracts should be archived in the same way, using `materials/docs/` and `materials/chat/`.

## Quote Workflow Adaptation

The quote rendering core is already reusable. The required changes are around pathing and handoff, not quote composition logic.

### Keep unchanged

Keep the existing `quote-skill` capabilities for:

- quote project initialization
- quote version creation
- quote content validation
- HTML, PDF, and XLSX generation
- quote version record updates

### Add business-project-compatible project creation

The quote project initializer must support a direct target directory mode in addition to the current `projects-root + client-name + project-name` mode.

Current legacy pattern:

- build under `quote-skill/projects/客户名/项目名/`

New business-integrated pattern:

- build directly under `/Users/a123/.openclaw/workspace-business/projects/客户名/项目名/quote/`

### Handoff contract

Before quoting starts, the business skill prepares `quote-handoff.json`.

Then the quote skill consumes:

- quote-ready project facts
- scope and exclusions
- key requirements
- open questions
- linked material paths
- linked meeting-note paths

### Quote result write-back

After a quote version is generated, the business project must also update:

- `project.json`
- `progress.json`
- `tasks.json`
- `quote-handoff.json`

This prevents quote history from becoming detached from the business project record.

## Required Config Changes

### `openclaw.json`

Add:

- `business` agent entry
- `business-shared` agent entry
- `workspace-business` paths where needed
- dispatch permissions from `main` and `main-shared`
- any shared-agent allowlists that must include the new business agent

### Workspace files

Create:

- `/Users/a123/.openclaw/workspace-business/AGENTS.md`
- `/Users/a123/.openclaw/workspace-business/IDENTITY.md`
- `/Users/a123/.openclaw/workspace-business/SOUL.md`
- `/Users/a123/.openclaw/workspace-business/USER.md`
- `/Users/a123/.openclaw/workspace-business/TOOLS.md`
- `/Users/a123/.openclaw/workspace-business/MEMORY.md`

These should mirror the current workspace pattern while specializing the role around business intake, project continuity, and quote readiness management.

### Skill files

Create:

- `/Users/a123/.openclaw/skills/business-project-intake/SKILL.md`

Add supporting scripts for:

- project initialization
- material archiving
- JSON record updates
- quote handoff preparation

### `quote-skill`

Update:

- `SKILL.md`
- quote project creation entrypoint
- project utility helpers if they currently assume only the legacy path mode

## Validation Expectations

The final implementation should be verifiable with concrete evidence:

- the new agents appear in `openclaw.json`
- the new workspace exists with the expected role files
- the new skill is loadable from the configured skills path
- a sample business project can be created under `workspace-business/projects/客户名/项目名/`
- a sample material can be copied into the correct archive folder and registered in `materials.json`
- a sample quote project can be initialized under `quote/`
- a sample quote output can update both quote-local records and the parent business project records

## Non-Goals and Simplicity Constraints

To keep v1 workable, do not add:

- contact master tables
- approval workflows
- CRM-wide analytics
- automatic customer-facing follow-up delivery
- mandatory deep cross-agent orchestration for each small update

The system should first succeed at durable memory, clean archive structure, stage tracking, and smooth quote handoff.

## Risks

### Duplicate truths

If business project state and quote project state diverge, the system becomes hard to trust.

Mitigation:

- treat the business project as the main truth for business-stage facts
- treat `quote/` as the quote-production subdomain
- define explicit write-back after quote generation

### Over-eager project creation

If the agent creates projects too early, the workspace fills with noise.

Mitigation:

- enforce minimum creation fields before formal initialization

### Material sprawl

If copied materials are not registered, the project folder becomes a dead archive.

Mitigation:

- every copied material must create or update a `materials.json` entry

### Premature quoting

If quote flow starts only because the agent infers quote intent, the project can jump stages incorrectly.

Mitigation:

- require explicit user instruction to start quoting

## Success Criteria

The design is successful when:

1. the user can return later and immediately see the current status of any business project
2. recordings, screenshots, and other materials are archived inside the project and traceable in JSON
3. each major conversation creates durable project memory instead of staying trapped in session history
4. quote work happens inside the same project context rather than in a disconnected skill-owned project tree
5. the existing quote skill is reused with targeted adaptation rather than replaced
