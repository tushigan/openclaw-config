# Main RunningHub Skill Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the downloaded RunningHub skill into `main`'s local skill directory, wire it into `openclaw.json`, and make its basic script flows usable in this environment.

**Architecture:** Treat the downloaded package as the source artifact, install it under `workspace/skills/runninghub`, keep its existing workflow docs and scripts intact, and only patch portability issues needed for `main` to load and execute it safely. Add one focused regression test for the known `--list` crash so the migrated copy does not regress immediately.

**Tech Stack:** OpenClaw skill loading via `openclaw.json`, Python 3 stdlib scripts, `pytest` for regression coverage, shell verification commands.

---

### Task 1: Install the skill into `main`

**Files:**
- Create: `/Users/a123/.openclaw/workspace/skills/runninghub/**`
- Modify: `/Users/a123/.openclaw/openclaw.json`

- [ ] Copy the downloaded `runninghub` package into `/Users/a123/.openclaw/workspace/skills/runninghub`.
- [ ] Register `skills.entries.runninghub` in `/Users/a123/.openclaw/openclaw.json` with `enabled=true` and the configured API key field expected by the script.
- [ ] Confirm the skill directory contains `SKILL.md`, `scripts/`, `references/`, and `data/`.

### Task 2: Lock in the `--list` regression test first

**Files:**
- Create: `/Users/a123/.openclaw/workspace/skills/runninghub/tests/test_runninghub.py`
- Test: `/Users/a123/.openclaw/workspace/skills/runninghub/tests/test_runninghub.py`

- [ ] Write a failing test that loads the migrated `runninghub.py`, swaps in a temporary capabilities file without `tags`, runs `cmd_list(None, None)`, and asserts it prints endpoint rows instead of crashing.
- [ ] Run `pytest /Users/a123/.openclaw/workspace/skills/runninghub/tests/test_runninghub.py -q` and verify the new test fails with a `KeyError` before the fix.

### Task 3: Patch the migrated scripts minimally

**Files:**
- Modify: `/Users/a123/.openclaw/workspace/skills/runninghub/scripts/runninghub.py`

- [ ] Change `cmd_list` so missing optional fields like `tags` and `name_en` do not crash older or trimmed `capabilities.json` snapshots.
- [ ] Re-run `pytest /Users/a123/.openclaw/workspace/skills/runninghub/tests/test_runninghub.py -q` and verify it passes.

### Task 4: Verify the integrated skill end-to-end

**Files:**
- Verify: `/Users/a123/.openclaw/workspace/skills/runninghub/scripts/runninghub.py`
- Verify: `/Users/a123/.openclaw/workspace/skills/runninghub/data/capabilities.json`
- Verify: `/Users/a123/.openclaw/openclaw.json`

- [ ] Run `python3 /Users/a123/.openclaw/workspace/skills/runninghub/scripts/runninghub.py --check` and verify the script can read the configured key from `openclaw.json`.
- [ ] Run `python3 /Users/a123/.openclaw/workspace/skills/runninghub/scripts/runninghub.py --list` and verify the migrated copy prints endpoint rows instead of raising.
- [ ] Verify `runninghub` now appears in `openclaw.json` skill entries and that the skill lives under `main`'s workspace.
