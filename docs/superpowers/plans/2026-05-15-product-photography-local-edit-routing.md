# Product Photography Local-Edit Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a scoped `local_edit` path for product-photography tasks that only activates when the task explicitly says to preserve the base scene and change a specific sub-area.

**Architecture:** Keep the existing whole-image workflow as the default. Add explicit task-brief metadata for local-edit constraints, teach prompt building and generation command assembly to honor those constraints, and expose an additive `--ref-base` image role in `gpt-image2-gen` so the base image becomes the primary scene lock when the task opts into local edit.

**Tech Stack:** Python CLI scripts, unittest, JSON manifests, Markdown skill docs

---

### Task 1: Add Regression Tests For Local-Edit Task Metadata

**Files:**
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_local_edit_task_brief_routes_generation_through_base_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(project_dir, root / "task-assets")

            base_image = task_dir / "versions" / "V001" / "approved-base.png"
            write_png(base_image)

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "保持母版场景，只改木盘上的顶部剖面产品",
                "--output-ratio",
                "3:4",
                "--execution-mode",
                "local_edit",
                "--base-image",
                str(base_image),
                "--editable-target",
                "木盘上的顶部剖面产品",
                "--immutable-element",
                "木桌、葡萄、饮品、底部两个完整面包全部不变",
                "--anchor-object",
                "木盘",
                "--spatial-relation",
                "顶部剖面产品仍叠在底部两个完整面包上",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            confirm = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "局部替换约束确认",
            )
            self.assertEqual(confirm.returncode, 0, confirm.stderr)

            prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            generate = run_cmd(
                str(SCRIPTS_DIR / "run_generation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            task_brief = read_json(task_dir / "task_brief.json")
            self.assertEqual(task_brief["execution_mode"], "local_edit")
            self.assertEqual(task_brief["base_image"]["absolute_path"], str(base_image))
            self.assertIn("木盘上的顶部剖面产品", task_brief["edit_scope"]["editable_targets"])

            prompt_path = task_dir / "prompts" / "prompt_V001.md"
            prompt_text = prompt_path.read_text(encoding="utf-8")
            self.assertIn("Scene-locked local edit mode", prompt_text)
            self.assertIn("Immutable elements", prompt_text)
            self.assertIn("Editable targets", prompt_text)

            generation = read_json(task_dir / "generation_manifest.json")
            command_summary = generation["versions"][-1]["command_summary"]
            self.assertIn("--ref-base", command_summary)
            self.assertIn(str(base_image), command_summary)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: FAIL because `build_task_brief.py` does not accept `--execution-mode` / `--base-image`, and `run_generation.py` never emits `--ref-base`.

- [ ] **Step 3: Write minimal implementation**

```python
# Add task-brief fields:
# - execution_mode
# - base_image
# - edit_scope = {editable_targets, immutable_elements, anchor_objects, spatial_relations}
#
# Then branch run_generation command building:
# if task_brief["execution_mode"] == "local_edit":
#     cmd.extend(["--ref-base", task_brief["base_image"]["absolute_path"]])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: PASS for the new local-edit regression test and existing workflow tests.

- [ ] **Step 5: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py
git commit -m "test: cover local-edit routing for product photography"
```

### Task 2: Add Local-Edit Metadata To Workflow Scripts

**Files:**
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_task_brief.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_generation_prompt.py`
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/scripts/run_generation.py`

- [ ] **Step 1: Extend the default task brief schema**

```python
    return {
        "version": "1.1",
        ...
        "execution_mode": "whole_image",
        "base_image": {},
        "edit_scope": {
            "editable_targets": [],
            "immutable_elements": [],
            "anchor_objects": [],
            "spatial_relations": [],
        },
        ...
    }
```

- [ ] **Step 2: Parse and persist local-edit CLI inputs**

```python
    parser.add_argument("--execution-mode", default="whole_image", choices=["whole_image", "local_edit"])
    parser.add_argument("--base-image", default="", help="局部编辑母版图")
    parser.add_argument("--editable-target", action="append", default=[], help="允许改动的目标")
    parser.add_argument("--immutable-element", action="append", default=[], help="必须保持不变的元素")
    parser.add_argument("--anchor-object", action="append", default=[], help="空间锚点")
    parser.add_argument("--spatial-relation", action="append", default=[], help="空间关系锁定")
```

- [ ] **Step 3: Add a local-edit block to prompt assembly**

```python
    if task_brief.get("execution_mode") == "local_edit":
        prompt_lines.extend(
            [
                "",
                "Scene-locked local edit mode:",
                f"- Base image authority: {task_brief['base_image'].get('absolute_path', 'missing')}",
                "Immutable elements:",
                *bullet_lines(task_brief.get("edit_scope", {}).get("immutable_elements", [])),
                "Editable targets:",
                *bullet_lines(task_brief.get("edit_scope", {}).get("editable_targets", [])),
                "Anchor objects:",
                *bullet_lines(task_brief.get("edit_scope", {}).get("anchor_objects", [])),
                "Spatial relation locks:",
                *bullet_lines(task_brief.get("edit_scope", {}).get("spatial_relations", [])),
            ]
        )
```

- [ ] **Step 4: Branch generation command building for local edit**

```python
def build_command(..., base_refs: list[dict], ...):
    ...
    for entry in base_refs:
        cmd.extend(["--ref-base", entry["absolute_path"]])
```

```python
    local_mode = task_brief.get("execution_mode") == "local_edit"
    base_refs = []
    if local_mode:
        base_info = task_brief.get("base_image", {})
        base_path = Path(base_info.get("absolute_path", ""))
        if not base_path.exists():
            raise SystemExit("local_edit 模式缺少可用母版图。")
        base_refs = [{"absolute_path": str(base_path)}]
```

- [ ] **Step 5: Run targeted tests**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: PASS with local-edit and existing whole-image workflow coverage.

- [ ] **Step 6: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/scripts/common.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_task_brief.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/build_generation_prompt.py /Users/a123/.openclaw/skills/product-photography-workflow/scripts/run_generation.py
git commit -m "feat: add scoped local-edit routing to product photography workflow"
```

### Task 3: Expose A Base-Image Typed Reference In gpt-image2-gen

**Files:**
- Modify: `/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/SKILL.md`
- Modify: `/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py`

- [ ] **Step 1: Add parser support for `--ref-base`**

```python
parser.add_argument('--ref-base', action='append', default=[], help='Locked base image for local edits')
```

- [ ] **Step 2: Give the new role stable ordering and prompt labeling**

```python
ROLE_LABELS = {
    'base': 'locked base image — preserve the global scene, framing, props, and all unchanged regions; edit only the explicitly requested targets',
    ...
}
```

```python
for role_key, items in [
    ('base', args.ref_base),
    ('logo', args.ref_logo),
    ('product', args.ref_product),
    ...
]:
```

- [ ] **Step 3: Run focused workflow tests so fake generation still accepts the new flag**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: PASS, proving `run_generation.py` and the fake generator tolerate `--ref-base`.

- [ ] **Step 4: Commit**

```bash
git add /Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/SKILL.md /Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py
git commit -m "feat: add base-image reference role for image edits"
```

### Task 4: Update Product Photography Skill Documentation

**Files:**
- Modify: `/Users/a123/.openclaw/skills/product-photography-workflow/SKILL.md`

- [ ] **Step 1: Document the routing rule**

```md
- Default remains `whole_image`.
- Switch to `local_edit` only when the user explicitly says the base scene should remain unchanged and only a named sub-area should change.
```

- [ ] **Step 2: Document the required local-edit inputs**

```md
For `local_edit` tasks, capture:
- base image path
- editable targets
- immutable elements
- anchor objects
- spatial relation locks
```

- [ ] **Step 3: Run tests again after doc-adjacent workflow changes**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_common_sizes.py /Users/a123/.openclaw/skills/product-photography-workflow/tests/test_workflow_cli.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add /Users/a123/.openclaw/skills/product-photography-workflow/SKILL.md
git commit -m "docs: describe scoped local-edit routing for product photography"
```
