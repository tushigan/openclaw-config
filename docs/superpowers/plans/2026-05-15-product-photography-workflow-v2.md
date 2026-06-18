# Product Photography Workflow V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `product-photography-workflow` into a resumable project/task system that supports project recall, many tasks per project, task-specific references, and revision history.

**Architecture:** Keep project-level product truth in the existing root manifests, then add a task registry plus per-task folders under `tasks/`. Extend current helper scripts for compatibility and add a small set of task-management CLIs that the skill instructions can orchestrate.

**Tech Stack:** Python 3 CLI scripts, JSON/JSONL state files, Markdown reports, OpenClaw skill instructions, `unittest` smoke tests.

---

### Task 1: Upgrade Shared Helpers And Project Schema

**Files:**
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/init_project.py`
- Test: `/Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_init_project_creates_v2_registry_files(self) -> None:
    ...
    self.assertTrue((project_dir / "tasks_manifest.json").exists())
    self.assertTrue((project_dir / "tasks").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: fail because `tasks_manifest.json` and task directories do not exist yet.

- [ ] **Step 3: Implement minimal schema changes**

```python
state["schema_version"] = "2.0"
state["project_mode"] = "multi_task_v2"
state["artifacts"]["tasks_manifest"] = "tasks_manifest.json"
```

- [ ] **Step 4: Re-run the test**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: the new init test passes.

- [ ] **Step 5: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/init_project.py /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py
git commit -m "feat: add v2 project schema scaffolding"
```

### Task 2: Add Project Recall CLIs

**Files:**
- Create: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/find_project.py`
- Create: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/resume_project_context.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py`
- Test: `/Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_find_project_matches_project_name_alias(self) -> None:
    ...
    self.assertIn("project_dir=", result.stdout)
    self.assertIn("confidence=", result.stdout)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: fail because `find_project.py` and `resume_project_context.py` do not exist.

- [ ] **Step 3: Implement recall and summary output**

```python
score = project_name_score + alias_score + product_name_score
if score < threshold:
    print("status=ambiguous")
```

- [ ] **Step 4: Re-run tests**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: recall tests pass and summary output includes tasks, project name, and product truth.

- [ ] **Step 5: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/scripts/find_project.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/resume_project_context.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py
git commit -m "feat: add project recall commands"
```

### Task 3: Add Task Creation And Task Asset Registration

**Files:**
- Create: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/create_task.py`
- Create: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/register_task_assets.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py`
- Test: `/Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_create_task_and_register_task_assets(self) -> None:
    ...
    self.assertTrue((task_dir / "task_state.json").exists())
    self.assertEqual(task_assets["summary"]["page_draft_count"], 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: fail because task directories and task asset manifests are missing.

- [ ] **Step 3: Implement task folder generation and task roles**

```python
task_id = f"TASK-{index:03d}-{slug}"
task_dir = project_dir / "tasks" / task_id
```

- [ ] **Step 4: Re-run tests**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: task creation and asset registration tests pass.

- [ ] **Step 5: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/scripts/create_task.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/register_task_assets.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py
git commit -m "feat: add task creation and task asset registration"
```

### Task 4: Add Task Briefing, Task Listing, And Revisioning

**Files:**
- Create: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_task_brief.py`
- Create: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/list_project_tasks.py`
- Create: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/revise_task.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/record_confirmation.py`
- Test: `/Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_build_task_brief_and_revise_task(self) -> None:
    ...
    self.assertEqual(task_state["selected_version_id"], "V002")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: fail because task brief and revision scripts do not exist yet.

- [ ] **Step 3: Implement task brief JSON plus versioned revision folders**

```python
version_id = f"V{next_version:03d}"
(task_dir / "versions" / version_id).mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Re-run tests**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: task brief, task listing, and revision tests pass.

- [ ] **Step 5: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_task_brief.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/list_project_tasks.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/revise_task.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/record_confirmation.py /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py
git commit -m "feat: add task brief and revision flow"
```

### Task 5: Make Prompt Assembly And Generation Task-Aware

**Files:**
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_generation_prompt.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/run_generation.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py`
- Test: `/Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_task_prompt_and_generation_manifest_use_task_context(self) -> None:
    ...
    self.assertIn("task_brief", prompt_text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: fail because prompt and generation still only look at project-level direction files.

- [ ] **Step 3: Implement task-aware prompt resolution**

```python
task_dir = resolve_task_dir(project_dir, task_id)
prompt_path = task_dir / "prompts" / f"prompt_{version_id}.md"
```

- [ ] **Step 4: Re-run tests**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: the task-aware prompt and generation tests pass.

- [ ] **Step 5: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_generation_prompt.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/run_generation.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py
git commit -m "feat: add task-aware generation flow"
```

### Task 6: Update Skill Docs And References

**Files:**
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/SKILL.md`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/references/project-files.md`
- Modify: `/Users/a123/.openclaw/docs/superpowers/specs/2026-05-15-product-photography-workflow-design.md`

- [ ] **Step 1: Rewrite the workflow sections**

```markdown
Step 0 find_project / init_project
Step 1 resume_project_context
Step 2 create_task
...
```

- [ ] **Step 2: Verify references and paths**

Run: `rg -n "create_task|find_project|register_task_assets|build_task_brief|revise_task" /Users/a123/.openclaw/skills/product-photography-workflow`
Expected: all new scripts are referenced from `SKILL.md`.

- [ ] **Step 3: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/SKILL.md /Users/a123/.openclaw/skills/product-photography-workflow/references/project-files.md /Users/a123/.openclaw/docs/superpowers/specs/2026-05-15-product-photography-workflow-design.md
git commit -m "docs: document v2 project task workflow"
```

### Task 7: Final Verification

**Files:**
- Test: `/Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py`

- [ ] **Step 1: Run targeted unit/smoke coverage**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: all tests pass.

- [ ] **Step 2: Run a manual CLI smoke flow**

Run:

```bash
tmpdir="$(mktemp -d)" && \
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/init_project.py "Smoke Product" --output-root "$tmpdir" && \
project_dir="$(find "$tmpdir" -maxdepth 1 -type d -name 'Smoke Product_*' | head -n 1)" && \
python3 /Users/a123/.openclaw/skills/product-photography-workflow/scripts/create_task.py --project-dir "$project_dir" --task-name "场景图A" --task-type scene
```

Expected: project and task paths print successfully, with no traceback.

- [ ] **Step 3: Review for regressions**

Run: `git diff --check`
Expected: no whitespace or patch formatting issues.
