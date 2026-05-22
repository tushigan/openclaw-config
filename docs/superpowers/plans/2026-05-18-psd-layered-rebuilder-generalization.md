# PSD Layered Rebuilder Generalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the PSD layered rebuild skill move in a more generalizable direction while improving next-run fidelity for positioning and support-surface reconstruction.

**Architecture:** Externalize poster-family layer definitions into profile files, keep prompt/cleanup behavior keyed by reusable layer kinds, and align final placement to the crop-reference coordinate system instead of squeezing crop-based generations back into tight boxes. Add diagnostic metadata and a structure-guide reference for occluded support-surface layers so future tuning is evidence-based.

**Tech Stack:** Python 3.12, Pillow, numpy, psd-tools, JSON profile files

---

### Task 1: Externalize the default layer profile

**Files:**
- Create: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/profiles/product-poster-v1.json`
- Modify: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/scripts/analyze_layers.py`
- Test: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/tests/test_analyze_layers.py`

- [ ] Add a failing test that expects the default layer definitions to load from a JSON profile rather than a hardcoded Python constant.
- [ ] Run the targeted tests with `/Users/a123/.openclaw/venv-psd/bin/python3.12 -m unittest /Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/tests/test_analyze_layers.py` and confirm the new test fails for the right reason.
- [ ] Implement profile loading with a default profile path and normalize region specs so future poster families can be added without editing the core script.
- [ ] Re-run the targeted tests and confirm they pass.

### Task 2: Align placement to crop semantics and emit diagnostics

**Files:**
- Modify: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/scripts/analyze_layers.py`
- Test: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/tests/test_analyze_layers.py`

- [ ] Add a failing test that expects crop-based layers to place against `crop_bbox` when their placement mode is `reference_crop`.
- [ ] Add a failing test that expects per-layer diagnostics to report alpha coverage and alpha insets so visual drift can be diagnosed from artifacts.
- [ ] Run the targeted tests and confirm both fail before implementation.
- [ ] Implement placement-mode resolution plus diagnostic measurement helpers and write the resulting metadata into the manifest/reference outputs.
- [ ] Re-run the targeted tests and confirm they pass.

### Task 3: Add a reusable support-surface guide strategy

**Files:**
- Modify: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/scripts/analyze_layers.py`
- Modify: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/references/layer-schema.md`
- Modify: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/references/prompt-templates.md`
- Modify: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/references/workflow.md`
- Modify: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/SKILL.md`
- Test: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/tests/test_analyze_layers.py`

- [ ] Add a failing test that expects support-surface layers to produce an extra structure-guide reference and to use the dedicated support-surface prompt path.
- [ ] Run the targeted tests and confirm the new behavior is not present yet.
- [ ] Implement a guide-image generator for support-surface crops, append that guide as an extra reference, and keep the prompt wording focused on geometry continuation behind occluders.
- [ ] Update the skill/reference docs so the new profile system, placement semantics, and support-surface strategy are explicit.
- [ ] Re-run the targeted tests and confirm they pass.

### Task 4: Verify against the real runtime

**Files:**
- Modify: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/scripts/run_pipeline.py`
- Test: `/Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/tests/test_analyze_layers.py`

- [ ] Add a failing test that expects the runtime entrypoint to allow profile selection to flow through to `analyze_layers.py`.
- [ ] Run the targeted tests and confirm they fail first.
- [ ] Implement CLI plumbing for `--profile` in the pipeline entrypoint so profile selection works end-to-end.
- [ ] Re-run the targeted tests and confirm they pass.
- [ ] Run `/Users/a123/.openclaw/venv-psd/bin/python3.12 -m unittest /Users/a123/.openclaw/workspace-design/skills/psd-layered-rebuilder/tests/test_analyze_layers.py` as the final verification pass for this iteration.
