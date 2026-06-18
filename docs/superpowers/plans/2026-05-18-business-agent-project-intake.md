# Business Agent Project Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new `business` agent plus a `business-project-intake` skill that can create durable business project records, archive incoming materials, and hand projects into `quote-skill` using an embedded `quote/` subproject.

**Architecture:** The new `workspace-business` directory becomes the source of truth for business-stage project memory. A new Python-backed skill manages project initialization, material archiving, progress/task updates, and quote handoff records, while `quote-skill` is extended only enough to initialize projects directly inside `workspace-business/projects/客户名/项目名/quote/`.

**Tech Stack:** OpenClaw JSON config, markdown workspace role files, Python `unittest`, Python filesystem/JSON helpers, existing `quote-skill` test suite.

---

### Task 1: Track The New Workspace And Agent Config Surface

**Files:**
- Modify: `/Users/a123/.openclaw/.gitignore`
- Modify: `/Users/a123/.openclaw/openclaw.json`
- Modify: `/Users/a123/.openclaw/openclaw.json.template`
- Create: `/Users/a123/.openclaw/agents/business/agent/models.json`
- Create: `/Users/a123/.openclaw/agents/business/agent/models.json.template`
- Create: `/Users/a123/.openclaw/agents/business-shared/agent/models.json`
- Create: `/Users/a123/.openclaw/agents/business-shared/agent/models.json.template`

- [ ] **Step 1: Extend workspace ignore rules before creating files**

```gitignore
workspace-business/*
!workspace-business/AGENTS.md
!workspace-business/SOUL.md
!workspace-business/IDENTITY.md
!workspace-business/USER.md
```

- [ ] **Step 2: Add the business agent and shared agent config blocks**

```json
{
  "id": "business",
  "name": "业务专家",
  "workspace": "/Users/a123/.openclaw/workspace-business",
  "model": {
    "primary": "aixor/claude-opus-4-6",
    "fallbacks": [
      "newapi_channel_conn/gpt-5.5"
    ]
  },
  "thinkingDefault": "adaptive",
  "subagents": {
    "allowAgents": [
      "strategy",
      "design",
      "video",
      "research",
      "meeting-analyst",
      "copywriter"
    ],
    "thinking": "adaptive"
  }
}
```

```json
{
  "id": "business-shared",
  "name": "业务专家（共享版）",
  "workspace": "/Users/a123/.openclaw/workspace-business",
  "model": {
    "primary": "aixor/claude-opus-4-6",
    "fallbacks": [
      "newapi_channel_conn/gpt-5.5"
    ]
  },
  "thinkingDefault": "adaptive",
  "subagents": {
    "allowAgents": [
      "strategy-shared",
      "design-shared",
      "video-shared",
      "research-shared",
      "meeting-analyst-shared",
      "copywriter-shared"
    ],
    "thinking": "adaptive"
  }
}
```

- [ ] **Step 3: Add the new agent IDs to dispatch lists and media roots**

```json
"allowAgents": [
  "strategy",
  "design",
  "video",
  "research",
  "meeting-analyst",
  "copywriter",
  "business"
]
```

```json
"allowAgents": [
  "strategy-shared",
  "design-shared",
  "video-shared",
  "research-shared",
  "meeting-analyst-shared",
  "copywriter-shared",
  "business-shared"
]
```

```json
"mediaLocalRoots": [
  "/Users/a123/.openclaw/workspace",
  "/Users/a123/.openclaw/workspace-design",
  "/Users/a123/.openclaw/workspace-strategy",
  "/Users/a123/.openclaw/workspace-video",
  "/Users/a123/.openclaw/workspace-research",
  "/Users/a123/.openclaw/workspace-meeting",
  "/Users/a123/.openclaw/workspace-copywriter",
  "/Users/a123/.openclaw/workspace-business"
]
```

- [ ] **Step 4: Add the new workspace skills directory to config loading**

```json
"extraDirs": [
  "/Users/a123/.openclaw/skills",
  "/Users/a123/.openclaw/workspace/skills",
  "/Users/a123/.openclaw/workspace-strategy/skills",
  "/Users/a123/.openclaw/workspace-design/skills",
  "/Users/a123/.openclaw/workspace-research/skills",
  "/Users/a123/.openclaw/workspace-video/skills",
  "/Users/a123/.openclaw/workspace-copywriter/skills",
  "/Users/a123/.openclaw/workspace-business/skills"
]
```

- [ ] **Step 5: Add the business bot template entry and reserve the live credentials step for runtime config**

```json
"business": {
  "enabled": true,
  "appId": "{{APP_ID_business}}",
  "appSecret": "{{APP_SECRET_business}}",
  "name": "业务专家",
  "domain": "feishu",
  "dmPolicy": "open",
  "allowFrom": ["*"],
  "groupPolicy": "allowlist",
  "groupAllowFrom": ["*"],
  "configWrites": false
}
```

- [ ] **Step 6: Create runtime model files for the new agents**

```json
{
  "providers": {
    "newapi_channel_conn": {
      "baseUrl": "https://aixor.org/v1",
      "apiKey": "{{API_KEY_newapi_channel_conn}}",
      "api": "openai-completions",
      "models": [
        {
          "id": "gpt-5.5",
          "name": "GPT-5.5",
          "reasoning": true,
          "input": ["text", "image"],
          "cost": {
            "input": 0,
            "output": 0,
            "cacheRead": 0,
            "cacheWrite": 0
          },
          "contextWindow": 1000000,
          "maxTokens": 20000,
          "api": "openai-completions"
        }
      ]
    }
  }
}
```

- [ ] **Step 7: Verify the config files still parse**

Run: `jq empty /Users/a123/.openclaw/openclaw.json /Users/a123/.openclaw/openclaw.json.template`
Expected: exit `0`

### Task 2: Create The Business Workspace Role Files

**Files:**
- Create: `/Users/a123/.openclaw/workspace-business/AGENTS.md`
- Create: `/Users/a123/.openclaw/workspace-business/IDENTITY.md`
- Create: `/Users/a123/.openclaw/workspace-business/SOUL.md`
- Create: `/Users/a123/.openclaw/workspace-business/USER.md`
- Create: `/Users/a123/.openclaw/workspace-business/TOOLS.md`
- Create: `/Users/a123/.openclaw/workspace-business/MEMORY.md`

- [ ] **Step 1: Write the workspace execution rules around project truth and quote handoff**

```markdown
## 0. 总原则

### 0.1 先查 Skill，再开工
先扫描 `available_skills`，命中 `business-project-intake` 时先读 `SKILL.md`。

### 0.2 项目主档高于会话记忆
业务事实先回写 `project.json`、`progress.json`、`tasks.json`，不能只停留在聊天上下文。

### 0.3 报价只有显式触发才开始
只有当项目已到 `待报价` 且用户明确说“开始报价”时，才进入 `quote-skill`。
```

- [ ] **Step 2: Write the business role identity**

```markdown
- **名称：** 业务专家
- **身份：** AI 业务对接与项目立项中台
- **角色：** 中台 `business`
- **定位：** 业务资料收口者、项目档案维护者、报价前置整理者
- **领域：** 业务对接、需求梳理、项目推进、报价前交接
```

- [ ] **Step 3: Write the soul and user files around concise business communication**

```markdown
- 不抢结论，先收事实
- 先归档，再判断
- 下一步要明确到人和动作
- 进入报价前，先把边界和材料收齐
```

- [ ] **Step 4: Add local tool notes for audio and media handling**

```markdown
- 录音优先走 `/Users/a123/.openclaw/workspace/scripts/voice2text.py`
- 图片、截图、现场拍照必须复制进项目 `materials/images/`
- 业务项目主目录：`/Users/a123/.openclaw/workspace-business/projects/客户名/项目名/`
```

- [ ] **Step 5: Verify the tracked workspace files exist**

Run: `find /Users/a123/.openclaw/workspace-business -maxdepth 1 -type f | sort`
Expected: includes `AGENTS.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`

### Task 3: Build The Business Project Skill With TDD

**Files:**
- Create: `/Users/a123/.openclaw/skills/business-project-intake/SKILL.md`
- Create: `/Users/a123/.openclaw/skills/business-project-intake/scripts/init_business_project.py`
- Create: `/Users/a123/.openclaw/skills/business-project-intake/scripts/archive_project_material.py`
- Create: `/Users/a123/.openclaw/skills/business-project-intake/scripts/prepare_quote_handoff.py`
- Create: `/Users/a123/.openclaw/skills/business-project-intake/scripts/sync_quote_state.py`
- Create: `/Users/a123/.openclaw/skills/business-project-intake/scripts/business_project/__init__.py`
- Create: `/Users/a123/.openclaw/skills/business-project-intake/scripts/business_project/project.py`
- Create: `/Users/a123/.openclaw/skills/business-project-intake/tests/test_business_project.py`

- [ ] **Step 1: Write the failing tests for project initialization**

```python
def test_init_project_creates_full_business_project_tree():
    project_dir = create_business_project(
        workspace_root,
        client_name="丹夫",
        project_name="品牌升级沟通",
        current_goal="梳理需求边界",
        source_materials=[{"path": "input/brief.md", "type": "doc"}],
    )
    assert (project_dir / "project.json").is_file()
    assert (project_dir / "materials.json").is_file()
    assert (project_dir / "progress.json").is_file()
    assert (project_dir / "tasks.json").is_file()
    assert (project_dir / "quote-handoff.json").is_file()
    assert (project_dir / "quote").is_dir()
```

- [ ] **Step 2: Run the new test and watch it fail**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/business-project-intake/tests/test_business_project.py -v`
Expected: FAIL with import or missing function errors

- [ ] **Step 3: Implement the minimal business project helpers**

```python
def create_business_project(
    workspace_root: Path,
    client_name: str,
    project_name: str,
    current_goal: str,
    source_materials: list[dict[str, Any]],
) -> Path:
    project_dir = workspace_root / "projects" / client_name / project_name
    _ensure_project_dirs(project_dir)
    _write_json(project_dir / "project.json", build_project_payload(project_dir, client_name, project_name, current_goal))
    _write_json(project_dir / "materials.json", build_materials_payload(project_dir))
    _write_json(project_dir / "progress.json", build_progress_payload(project_dir, current_goal, source_materials))
    _write_json(project_dir / "tasks.json", build_tasks_payload(project_dir))
    _write_json(project_dir / "quote-handoff.json", build_quote_handoff_payload(project_dir, client_name, project_name))
    return project_dir
```

- [ ] **Step 4: Add tests for material archiving and quote handoff**

```python
def test_archive_material_copies_file_and_registers_metadata():
    material_record = archive_material(
        project_dir,
        source_path=source_file,
        material_type="audio",
        title="首次沟通录音",
        source_channel="feishu",
    )
    assert Path(material_record["stored_path"]).is_file()
    assert material_record["processing_status"] == "copied"
```

```python
def test_prepare_quote_handoff_builds_ready_record_without_starting_quote():
    handoff = prepare_quote_handoff(
        project_dir,
        trigger_reason="用户明确要求开始报价",
        recommended_case_type="项目案",
    )
    assert handoff["handoff_status"] == "ready"
    assert handoff["quote_project_dir"].endswith("/quote")
```

- [ ] **Step 5: Implement the material and handoff helpers**

```python
def archive_material(
    project_dir: Path,
    source_path: Path,
    material_type: str,
    title: str,
    source_channel: str,
    captured_at: str | None = None,
):
    destination = project_dir / "materials" / folder_name / source_path.name
    shutil.copy2(source_path, destination)
    material = build_material_record(
        project_dir=project_dir,
        destination=destination,
        material_type=material_type,
        title=title,
        source_channel=source_channel,
        captured_at=captured_at,
    )
    payload["items"].append(material)
    _write_json(materials_path, payload)
    return material
```

```python
def prepare_quote_handoff(
    project_dir: Path,
    trigger_reason: str,
    recommended_case_type: str,
    confirmed_scope: list[str] | None = None,
    excluded_scope: list[str] | None = None,
):
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    payload["handoff_status"] = "ready"
    payload["trigger_reason"] = trigger_reason
    payload["recommended_case_type"] = recommended_case_type
    payload["confirmed_scope"] = confirmed_scope or []
    payload["excluded_scope"] = excluded_scope or []
    payload["quote_project_dir"] = str(project_dir / "quote")
    _write_json(handoff_path, payload)
    return payload
```

- [ ] **Step 6: Implement quote state sync back into the business project**

```python
def sync_quote_state(project_dir: Path, quote_version: str, output_refs: list[str]) -> None:
    project_payload["quote_status"] = "quoted"
    project_payload["current_quote_version"] = quote_version
    handoff_payload["handoff_status"] = "quoted"
    handoff_payload["current_quote_version"] = quote_version
    handoff_payload["quote_output_refs"] = output_refs
    progress_payload["entries"].append(
        build_quote_progress_entry(
            project_payload=project_payload,
            quote_version=quote_version,
            output_refs=output_refs,
        )
    )
    tasks_payload["tasks"].append(
        build_quote_followup_task(
            quote_version=quote_version,
            title="跟进本轮报价反馈",
        )
    )
```

- [ ] **Step 7: Write the skill instructions**

```markdown
---
name: business-project-intake
description: Use when business docking requests need project background collection, durable project setup, material archiving, progress tracking, or quote handoff preparation.
---
```

```markdown
1. 先判断是新项目还是旧项目
2. 未满足最少字段时，只补 `客户名 / 项目名 / 当前目标 / 来源材料`
3. 满足后，初始化 `workspace-business/projects/客户名/项目名/`
4. 新材料必须复制进项目目录并登记到 `materials.json`
5. 录音默认要归档、纪要、回写进展、更新待办
6. 只有用户明确说开始报价时，才准备 `quote-handoff.json` 并切到 `quote-skill`
```

- [ ] **Step 8: Run the business project tests and make them pass**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/business-project-intake/tests/test_business_project.py -v`
Expected: all tests PASS

### Task 4: Extend Quote Skill For Embedded Quote Projects

**Files:**
- Modify: `/Users/a123/.openclaw/skills/quote-skill/SKILL.md`
- Modify: `/Users/a123/.openclaw/skills/quote-skill/scripts/init_quote_project.py`
- Modify: `/Users/a123/.openclaw/skills/quote-skill/scripts/quote_skill/project.py`
- Modify: `/Users/a123/.openclaw/skills/quote-skill/tests/test_project.py`
- Modify: `/Users/a123/.openclaw/skills/quote-skill/tests/test_smoke_flow.py`

- [ ] **Step 1: Write the failing test for direct quote directory initialization**

```python
def test_create_project_supports_direct_project_dir():
    quote_dir = Path(tmp) / "workspace-business" / "projects" / "丹夫" / "品牌升级沟通" / "quote"
    project_dir = create_project(
        None,
        client_name="丹夫",
        project_name="品牌升级沟通",
        output_mode="html_pdf",
        project_dir=quote_dir,
    )
    self.assertEqual(project_dir, quote_dir)
    self.assertTrue((quote_dir / "project.json").is_file())
```

- [ ] **Step 2: Run the quote project tests and watch the new case fail**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/quote-skill/tests/test_project.py -v`
Expected: FAIL because `create_project` does not accept `project_dir`

- [ ] **Step 3: Implement direct directory mode with backward compatibility**

```python
def create_project(
    projects_root: Path | None,
    client_name: str,
    project_name: str,
    output_mode: str,
    project_dir: Path | None = None,
) -> Path:
    if project_dir is None:
        if projects_root is None:
            raise ValueError("projects_root or project_dir is required")
        project_dir = projects_root / client_name / project_name
```

- [ ] **Step 4: Update the CLI entrypoint to accept either `--projects-root` or `--project-dir`**

```python
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--projects-root")
group.add_argument("--project-dir")
```

- [ ] **Step 5: Update the skill doc to describe business-project integration**

```markdown
- 旧模式：`quote-skill/projects/客户名/项目名/`
- 业务专家联动模式：`workspace-business/projects/客户名/项目名/quote/`
- 进入报价前先读 `quote-handoff.json`
```

- [ ] **Step 6: Re-run the quote tests**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/quote-skill/tests/test_project.py /Users/a123/.openclaw/skills/quote-skill/tests/test_smoke_flow.py -v`
Expected: all tests PASS

### Task 5: Enable The Runtime Config And Verify The Full Flow

**Files:**
- Modify: `/Users/a123/.openclaw/openclaw.json`
- Modify: `/Users/a123/.openclaw/openclaw.json.template`

- [ ] **Step 1: Collect the live Feishu business bot values, then write the runtime binding**

Run: ask the user for `appId`, `appSecret`, and the business bot direct-chat `open_id`, then insert those exact values into:
- `openclaw.json > channels.internal.entries.business`
- `openclaw.json > bindings[]` for `business`
- `openclaw.json > bindings[]` for `business-shared`

Expected: the new business bot can route direct Feishu chats to `business`, and all other account traffic falls back to `business-shared`

- [ ] **Step 2: Create a sample business project through the new helper**

Run: `python3 /Users/a123/.openclaw/skills/business-project-intake/scripts/init_business_project.py --workspace-root /Users/a123/.openclaw/workspace-business --client-name 示例客户 --project-name 示例项目 --current-goal 梳理报价范围 --source-material /tmp/example-brief.txt:doc`
Expected: project tree created under `/Users/a123/.openclaw/workspace-business/projects/示例客户/示例项目/`

- [ ] **Step 3: Initialize the embedded quote project in direct-dir mode**

Run: `python3 /Users/a123/.openclaw/skills/quote-skill/scripts/init_quote_project.py --project-dir /Users/a123/.openclaw/workspace-business/projects/示例客户/示例项目/quote --client-name 示例客户 --project-name 示例项目 --output-mode html_pdf`
Expected: quote subproject created directly under `/Users/a123/.openclaw/workspace-business/projects/示例客户/示例项目/quote/`

- [ ] **Step 4: Sync a sample quote result back into the business project**

Run: `python3 /Users/a123/.openclaw/skills/business-project-intake/scripts/sync_quote_state.py --project-dir /Users/a123/.openclaw/workspace-business/projects/示例客户/示例项目 --quote-version v1 --quote-output versions/v1/quote.html --quote-output versions/v1/quote.xlsx`
Expected: parent `project.json`, `progress.json`, `tasks.json`, and `quote-handoff.json` updated

- [ ] **Step 5: Run the focused verification suite**

Run: `python3 -m unittest /Users/a123/.openclaw/skills/business-project-intake/tests/test_business_project.py /Users/a123/.openclaw/skills/quote-skill/tests/test_project.py /Users/a123/.openclaw/skills/quote-skill/tests/test_smoke_flow.py -v`
Expected: all targeted tests PASS

- [ ] **Step 6: Inspect the generated sample files for evidence**

Run: `find /Users/a123/.openclaw/workspace-business/projects/示例客户/示例项目 -maxdepth 3 | sort`
Expected: shows business JSON files plus `quote/versions/v1`
