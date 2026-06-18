# Brand Poster Role Contacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `brand-poster-creator` ask for project role assignments naturally, resolve those people from the current Feishu group member list, and persist the resolved IDs for later confirmations.

**Architecture:** Keep contact routing inside the existing `brief.json.contacts` and `project_state.json.role_contacts` surfaces. Update the skill contract first, then extend `project_manager.py` normalization so richer contact objects survive initialization and stage confirmation routing.

**Tech Stack:** Markdown skill documentation, Python 3 standard library, JSON project manifests.

---

### Task 1: Document Role Assignment Intake

**Files:**
- Modify: `/Users/a123/.openclaw/skills/brand-poster-creator/SKILL.md`

- [x] **Step 1: Replace manual Feishu ID fields**

Change Step 1 demand collection text so it asks for names, nicknames, or @ mentions for:
- design lead
- planning lead
- project manager

- [x] **Step 2: Add group-member resolution rules**

Document that the agent must resolve names/@ mentions against the current Feishu group member list, write IDs into `brief.json.contacts`, and ask a follow-up question when no match or multiple matches exist.

- [x] **Step 3: Update contact schema**

Expand the example schema to include `initiator`, `source`, `match_status`, and `raw_input`.

### Task 2: Preserve Rich Contact Objects

**Files:**
- Modify: `/Users/a123/.openclaw/skills/brand-poster-creator/scripts/project_manager.py`

- [x] **Step 1: Write a failing contact normalization check**

Use a temporary Python command that imports `ProjectManager`, initializes a temp project with rich `contacts`, and asserts that `source`, `match_status`, and `raw_input` are preserved.

- [x] **Step 2: Extend role keys and default shape**

Set `ROLE_KEYS` to include `initiator`, `design_lead`, `planning_lead`, and `project_manager`. Default each contact to include `feishu_user_id`, `name`, `source`, `match_status`, and `raw_input`.

- [x] **Step 3: Update normalization**

When a contact is an object, preserve the known fields as strings. When it is a legacy string, keep treating it as `feishu_user_id`.

- [x] **Step 4: Verify state and manifests**

Run the temporary Python check again and inspect the generated `project_state.json` / `intake_manifest.json`.

### Task 3: Validate Skill Text

**Files:**
- Inspect: `/Users/a123/.openclaw/skills/brand-poster-creator/SKILL.md`
- Inspect: `/Users/a123/.openclaw/skills/brand-poster-creator/scripts/project_manager.py`

- [x] **Step 1: Search for stale manual-ID wording**

Run `rg "设计负责人飞书 ID|策划负责人飞书 ID|项目经理飞书 ID|手填"`.

- [x] **Step 2: Run Python syntax check**

Run `python3 -m py_compile /Users/a123/.openclaw/skills/brand-poster-creator/scripts/project_manager.py`.

- [x] **Step 3: Review git diff**

Confirm only the intended skill docs, contact normalization code, and plan file changed.
