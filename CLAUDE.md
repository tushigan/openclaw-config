# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **OpenClaw user configuration directory** (`~/.openclaw`), not source code. OpenClaw is a multi-channel AI gateway/agent framework with multi-agent collaboration capabilities. The actual OpenClaw package is installed via npm at `/opt/homebrew/lib/node_modules/openclaw`.

### Collaboration Role

In this repository, Claude's default role is to act as the user's **programming assistant and engineering expert for maintaining OpenClaw**, not to optimize Claude Code for its own sake.

**Default context**: Treat all tasks as OpenClaw maintenance work unless user explicitly asks about Claude Code itself.

Focus areas include:
- OpenClaw architecture optimization
- skill development, debugging, and refinement
- agent workflow and routing improvements
- configuration cleanup and maintainability upgrades
- stability, observability, and delivery-chain reliability

Key configuration file: [openclaw.json](openclaw.json) contains models, channels, agents, plugins, and all runtime settings.

## Communication Style Principles

### "够用即可" (Sufficient is Enough)
- Provide information at "sufficient" standard, not "comprehensive"
- Answer what the user asks, don't preemptively expand
- Provide technical details on-demand, don't front-load

### Distinguish Technical Delivery vs User Communication
- **Technical delivery** (to upstream agents): Include necessary file paths, status, risks
- **User communication** (to end users): Only conclusions and key evidence, omit process details

### Minimum Necessary Information
- Successful delivery: Result + path
- Failure report: Problem + cause
- Progress update: Current status + estimated completion time
- Other information provided on-demand, not mandated

### Against Over-explanation
- Over-explanation is waste, not professionalism
- Verification process doesn't need step-by-step reporting, only final results
- Evidence and sources provided on-demand, not mandatory citation for every statement

## Common Commands

### OpenClaw CLI (gateway management)
```bash
openclaw gateway --port 18789 --verbose   # Run gateway
openclaw daemon                            # Manage daemon service
openclaw doctor                            # Health check
openclaw config get/set                    # Read/write config
openclaw logs                              # View logs
openclaw sessions                          # View session history
```

### Subagent spawning (multi-agent collaboration)
```bash
# Spawn expert agents for tasks
openclaw subagents spawn strategy "制定产品战略" --timeout 1800
openclaw subagents spawn research "市场调研任务" --timeout 1800
openclaw subagents spawn design "生成产品效果图" --timeout 600
```

**Timeout guidelines:**
- Simple tasks: 60 seconds
- Normal tasks: 10 minutes (600s)
- Deep research: 30 minutes (1800s)
- **Never set timeout to 0** (infinite)

## Agent Architecture

| Agent | Role | Workspace | Primary Model |
|-------|------|-----------|---------------|
| `main` | Coordinator, task orchestration, user delivery | `workspace/` | Claude Opus 4.8 (via cc-vibe) |
| `strategy` | Product strategy, positioning, narrative | `workspace-strategy/` | Claude Opus 4.8 (via cc-vibe) |
| `research` | Market research, competitor analysis | `workspace-research/` | Claude Opus 4.8 (via cc-vibe) |
| `design` | Visual creation (images, video analysis), product renders | `workspace-design/` | Claude Opus 4.8 (via cc-vibe) |
| `meeting-analyst` | Meeting minutes analysis, evidence extraction | `workspace-meeting/` | Claude Opus 4.8 (via cc-vibe) |
| `copywriter` | Copywriting, content creation | `workspace-copywriter/` | Claude Opus 4.8 (via cc-vibe) |

Each agent also has a `*-shared` variant (e.g. `main-shared`, `strategy-shared`) for multi-user access with 虾权 isolation. Shared variants use the same model and workspace as their base agent.

### Available Workspaces

- `workspace/` — Main agent (independent git repo)
- `workspace-strategy/` — Strategy agent
- `workspace-research/` — Research agent
- `workspace-design/` — Design agent (visual creation, PSD extraction, video analysis)
- `workspace-meeting/` — Meeting analyst agent
- `workspace-copywriter/` — Copywriting agent
- `workspace-business/` — Business project intake agent

### Workflow Rules

Each workspace has an `AGENTS.md` defining execution rules. Key rules from [workspace/AGENTS.md](workspace/AGENTS.md):

1. **Check skills first**: Before any task, scan `available_skills` and read matching `SKILL.md`
2. **Runtime facts must be verified**: Never claim completion without evidence (file paths, return values)
3. **Memory doesn't override current state**: If memory conflicts with actual environment, trust the environment
4. **Main orchestrates by default**: `main` handles understanding, routing, progress tracking, unified delivery
5. **Expert domains require handoff**: Research, strategy, design (visual + video analysis), meeting, copywriting tasks → spawn corresponding expert
6. **Output organization**: `images/` for images, `outputs/` for other files (Markdown/JSON/CSV)
7. **Material staging before handoff**: Before `main` spawns any subagent, copy every source file that subagent needs into that subagent's own workspace or project input directory. Do not ask a subagent to read another workspace's absolute paths

**Meeting-analyst specific**:
- Evidence grading: A (clear decision), B (strong tendency), C (candidate/discussed), D (insufficient)
- Must provide source quotations for key conclusions
- Outputs structured analysis to `outputs/meeting_analysis_*.md`

**Copywriter specific**:
- Collaboration chain: `strategy → copywriter → design`
- Outputs to `outputs/copy_YYYYMMDD_主题.md`
- Provides 2-3 version options with rationale

### Session startup sequence
1. Read `SOUL.md` (personality/temperament)
2. Read `USER.md` (user profile)
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) — daily notes are in each workspace's `memory/` dir
4. In main session, also read `MEMORY.md` (long-term memory)
5. Long-term memory is also stored as SQLite in root `memory/` dir (e.g. `memory/main.sqlite`)

## OpenClaw 顶层记忆系统

⚠️ **重要更新（2026-06-13）**：OpenClaw 现在有统一的顶层记忆系统，所有 agent 和 skill 共享使用。

### 核心概念

**5层架构**：客户 → 品牌 → 项目 → 任务 → 迭代版本

**存储位置**：`/Users/a123/.openclaw/projects/`（根目录，所有 agent 平等访问）

**核心特性**：
- 统一查询接口
- 冲突检测（品牌关键信息变更需用户确认）
- 自动版本管理
- 跨 agent 共享

### 统一查询接口（最常用）

```bash
# 查询品牌档案（获取调性、定位、目标受众、核心价值）
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产（Logo、VI 手册、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json

# 查询活跃项目（获取策略、创意方向、项目上下文）
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json

# 列出所有品牌
python3 /Users/a123/.openclaw/scripts/memory/query.py list-brands

# 列出所有活跃项目
python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects
```

### 使用规范（所有 Agent 必须遵守）

1. **执行品牌相关任务前，先查询品牌档案**
2. **使用品牌调性、定位、目标受众指导产出**
3. **不硬编码项目路径，始终通过查询接口获取**
4. **品牌关键信息变更必须用户确认**

### 典型工作流

**设计任务（design agent）**：
```bash
# 1. 查询品牌档案
brand=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json)

# 2. 查询品牌资产（Logo、参考图）
assets=$(python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json)

# 3. 使用品牌调性和资产生成设计
```

**文案任务（copywriter agent）**：
```bash
# 1. 查询品牌档案
brand=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json)

# 2. 查询项目上下文（策略、创意方向）
project=$(python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json)

# 3. 基于品牌调性和策略撰写文案
```

**策略任务（strategy agent）**：
```bash
# 1. 查询品牌档案（定位、受众、核心价值）
brand=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json)

# 2. 基于品牌基础制定策略
```

### 详细文档

- 完整使用指南：[scripts/memory/README.md](scripts/memory/README.md)
- Skill 集成指南：[scripts/memory/SKILL_INTEGRATION_GUIDE.md](scripts/memory/SKILL_INTEGRATION_GUIDE.md)
- 测试脚本：`python3 scripts/memory/test_system.py`

## File Structure

```
~/.openclaw/
├── openclaw.json         # Main config (models, channels, agents, plugins, skills, cron)
├── CLAUDE.md             # Claude Code guidance (this file)
├── AGENTS.md             # Root-level agent execution rules
├── .env                  # Environment variables (API keys: BANANA, KLING, DIFY, MEMOS)
├── exec-approvals.json   # Per-agent command execution allowlists
├── .mcp.json             # MCP server config (Apifox)
├── .gitignore            # Git tracking rules
│
├── agents/               # Agent runtime dirs (models.json, auth-profiles.json, sessions/)
├── workspace*/           # Per-agent workspaces (AGENTS.md, SOUL.md, IDENTITY.md, etc.)
│
├── projects/             # ⚠️ 顶层记忆系统（新）- 所有 agent 共享
│   ├── _registry.json    # 全局项目注册表
│   ├── 客户名/
│   │   ├── _client-profile.json
│   │   └── 品牌名/
│   │       ├── _brand-profile.json
│   │       ├── _brand-assets/
│   │       └── 项目名/
│   │           ├── project.json
│   │           ├── materials/
│   │           └── outputs/
│
├── memory/               # Agent memory SQLite DBs (main.sqlite, design.sqlite, etc.)
├── scripts/              # Utility scripts
│   └── memory/           # ⚠️ 记忆系统脚本（新）
│       ├── query.py      # 统一查询接口
│       ├── client.py     # 客户管理
│       ├── brand.py      # 品牌管理（带冲突检测）
│       ├── migrate.py    # 数据迁移工具
│       ├── test_system.py # 综合测试
│       └── lib/          # 核心库
│
├── skills/               # Local skills (brand-poster-creator, tvc-director, etc.)
├── skills-store*/        # Inactive/archived skill templates
├── subagents/            # Subagent run registry (runs.json)
├── credentials/          # Feishu/Lark secrets, admin users
├── logs/                 # Gateway logs (gateway.log, gateway.err.log)
├── feishu/               # Feishu channel data
├── identity/             # Device authentication
├── cron/                 # Scheduled tasks (jobs.json, runs/)
├── flows/                # Flow registry (SQLite)
├── tasks/                # Task run history (SQLite)
├── extensions/           # OpenClaw plugins (memos-local, openclaw-lark)
├── delivery-queue/       # Message delivery queue
└── devices/              # Device registration data
```

### Git tracking strategy

Only personality/rule files are tracked in git for sub-workspaces (per `.gitignore`):
- `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md` — tracked
- Everything else in workspace*/ — ignored (images, outputs, scripts, memory)
- Root `memory/` SQLite DBs, `logs/`, `flows/`, `.env`, credentials — ignored

## Utility Scripts

Key scripts in `scripts/` directory:
- `deploy-openclaw.sh`: Deploy OpenClaw config to new machine from GitHub
- `setup-sensitive.sh`: Restore sensitive config from templates
- `cleanup-ghost-group-sessions.sh`: Clean up orphaned group chat sessions
- `delivery-queue-patrol.py`: Monitor and manage delivery queue
- `delivery-queue-patrol-readonly.py`: Read-only delivery queue inspection
- `detect-fake-delivery.sh`: Detect fake/failed delivery events
- `audit-feedback-gaps.py`: Audit feedback coverage gaps
- `feishu-id-registry.py`: Manage Feishu user/group ID registry
- `record_feishu_delivery.py`: Record Feishu message delivery events
- `optimize-shared-agent-permissions.py`: Optimize exec-approvals for shared agents
- `ensure-openclaw-image-deps.sh`: Ensure image processing dependencies are installed
- `test-aixor-anthropic.js`: Test Anthropic API endpoints via Aixor provider
- `test-aixor-endpoints.js`: Test Aixor provider endpoints
- `test-api-endpoints.js`: General API endpoint testing

## Git Version Management

### Remote Repository

GitHub remote: https://github.com/tushigan/openclaw-config.git

### Saving Convention

**IMPORTANT**: When user says "保存 git 版本" or "保存配置" or "保存到 GitHub", execute the following:

```bash
cd ~/.openclaw
git add -A
git commit -m "更新配置: ..."  # describe what changed
git push
```

This saves to BOTH local git AND GitHub.

### What Gets Saved

**Saved** (version controlled):
- ✅ Configuration files: `openclaw.json`, `.gitignore`, `exec-approvals.json`, `cron/jobs.json`
- ✅ Agent templates: `agents/*/agent/*.json.template` (redacted, no API keys)
- ✅ MCP config: `.mcp.json`
- ✅ Workspace personality: `workspace*/{AGENTS.md,IDENTITY.md,SOUL.md,USER.md}`
- ✅ Deployment scripts: `scripts/deploy-openclaw.sh`, `scripts/setup-sensitive.sh`
- ✅ Skills documentation: `skills/*/*.md`

**NOT saved** (excluded by .gitignore):
- ❌ Sensitive data: API keys, OAuth tokens, `credentials/` (except admin-users.json)
- ❌ Runtime data: `memory/*.sqlite`, `logs/`, `flows/`, `tasks/`, `feishu/`
- ❌ Generated files: `workspace/images/`, `workspace/outputs/`
- ❌ Agent sessions: `agents/*/sessions/`
- ❌ Main workspace: `workspace/` (has its own separate git repo)

### Redacted Templates

Sensitive configuration files use **redacted templates**:
- `openclaw.json.template` — uses placeholders like `{{API_KEY_provider}}`, `{{APP_SECRET}}`
- `agents/*/agent/models.json.template` — API keys replaced with `{{API_KEY_xxx}}`
- `agents/*/agent/auth-profiles.json.template` — OAuth tokens replaced with `{{OAUTH_ACCESS}}`, `{{OAUTH_REFRESH}}`

Templates allow sharing config structure without exposing secrets.

### Deployment to New Machine

Use the deployment script:
```bash
~/.openclaw/scripts/deploy-openclaw.sh https://github.com/tushigan/openclaw-config.git /target/dir
```

Or manually:
```bash
git clone https://github.com/tushigan/openclaw-config.git ~/.openclaw
cd ~/.openclaw
./scripts/setup-sensitive.sh  # restore from templates, then fill in API keys
```

### Commit Frequency

Save to git after:
- Changing agent configuration (models, tools, permissions)
- Updating workspace personality files
- Modifying skills or workflow rules
- Updating deployment scripts

Don't need to save after:
- Daily conversation changes (use memory for that)
- Generated output files
- Runtime data

## Model Providers

Configured in `openclaw.json` under `models.providers`:
- `aixor`: Claude Opus 4.7, Claude Opus 4.6 (reasoning, via Anthropic Messages API)
- `cc-vibe`: Claude Opus 4.7, Claude Opus 4.6 (reasoning, via Anthropic Messages API)
- `aixor-g`: GPT-5.4, GPT-5.5 (reasoning, via OpenAI-compatible API)
- `huoshan`: Kimi K2.6 (reasoning), Kimi K2.5, GLM-5.1 (via Volces/火山引擎)

Provider selection is automatic based on model availability and load balancing.

## Key Conventions

### File paths
- **Always use absolute paths**: `/Users/a123/.openclaw/workspace/...`
- **Never use `~/` or relative paths** in subagent tasks

### Image task routing
Image task routing rules are defined in `workspace/AGENTS.md` (section 1.1 - 1.1.2):
- For complex local edits (red box annotations, selective deletion, partial replacement, "keep other parts unchanged"), **must dispatch to `design` or `design-shared` agent**
- `main` agent can only: coordinate/route image tasks, or directly call approved image generation skills
- Never attempt final image composition locally in `main` for complex edit tasks

### Feishu image delivery
When sending images to user via Feishu:
1. Copy image to `/Users/a123/.openclaw/workspace/feishu-deliver/`
2. Use `message` tool with `path` parameter (not `image` parameter) to send
3. Never just return local path as "delivery"

**Important**: The `feishu-send-image` tool does not exist. Always use `message` tool's `path` parameter for image delivery.

### Subagent spawn format
```json
{
  "runtime": "subagent",
  "agentId": "strategy",
  "task": "Task description",
  "mode": "run",
  "timeoutSeconds": 1200,
  "runTimeoutSeconds": 1200,
  "lightContext": true
}
```

**Rules:**
- `runtime="subagent"`: Never pass `streamTo`
- `runtime="acp"`: Can pass `streamTo`, never pass `lightContext`
- `lightContext` only valid for `runtime="subagent"`

### Long-running task execution
For tasks that take significant time (>30 seconds):
1. **Prefer subagent execution**: Use `openclaw subagents spawn` instead of direct `exec`
2. **Write completion markers**: Scripts should write a `.done` file when finished
3. **Track completion status**: After starting, monitor for the `.done` file or check process status
4. Never assume completion without verification

## Workspace Personality Files

### Root vs Workspace AGENTS.md
- `/Users/a123/.openclaw/AGENTS.md`: Root-level execution rules (applies to all agents)
- `workspace*/AGENTS.md`: Per-agent specific rules (overrides root rules for that agent)

Each workspace has:
- `IDENTITY.md`: Who I am, role, domain focus
- `SOUL.md`: Personality, temperament, values
- `USER.md`: User profile, preferences
- `AGENTS.md`: Execution rules, routing, delivery (highest priority)
- `TOOLS.md`: Environment-specific notes (devices, SSH aliases, etc.)
- `MEMORY.md`: Long-term memory (only loaded in main session)
- `DREAMS.md`: Goals, aspirations, future plans
- `HEARTBEAT.md`: Background check rules (email, calendar, notifications)

When files conflict, **AGENTS.md takes precedence over all other personality files** (SOUL.md, IDENTITY.md, USER.md, MEMORY.md).

Key principles from AGENTS.md:
- **Rule 0.1**: Check skills first before any task execution
- **Rule 0.2**: Verify runtime facts before claiming completion (never say "done" without evidence)
- **Rule 0.3**: Unified response style (Chinese, conclusion-first, short sentences)
- **Rule 0.4**: Main agent's role is coordination, routing, progress tracking, and unified delivery

## Security

- Command execution requires approval per `exec-approvals.json` (per-agent allowlists with path patterns)
- Credentials stored encrypted in `credentials/`
- External actions (email, posting) require user confirmation
- Use `trash` instead of `rm` for destructive operations
- `.env` contains API keys (BANANA, KLING, DIFY, MEMOS) — never commit or expose

## MCP Servers

Configured in `.mcp.json`:
- `apifox`: Apifox OpenAPI spec reader (site-id 5484736), used for API spec reference

## Troubleshooting

### Gateway issues
If gateway fails to start:
1. Check if port 18789 is already in use: `lsof -i :18789`
2. Review logs: `openclaw logs` or check `logs/gateway.log`
3. Run health check: `openclaw doctor`
4. Verify `.env` has required API keys (BANANA, KLING, DIFY, MEMOS)

### Subagent timeout
If subagent tasks timeout:
1. Check if timeout is appropriate for task complexity (see timeout guidelines)
2. Review subagent logs in `agents/*/sessions/`
3. Consider splitting complex tasks into smaller subtasks
4. Verify model provider is responding (check `openclaw.json` provider config)

### Model call failures
1. Verify API keys in `.env` and `agents/*/agent/models.json`
2. Check provider status in `openclaw.json` under `models.providers`
3. Review error messages in gateway logs
4. Test with `openclaw doctor` to verify connectivity

### Image generation wrapper errors
When debugging image generation failures:
1. **Check output files first** before interpreting return codes
2. Distinguish between generation failure (no output file) and delivery failure (file exists but delivery failed)
3. Never report generation failure if output file exists

## Debugging and Development

### Viewing agent execution logs
```bash
# View gateway logs
tail -f ~/.openclaw/logs/gateway.log

# View specific agent session logs
ls ~/.openclaw/agents/main/sessions/
cat ~/.openclaw/agents/main/sessions/<session-id>.json
```

### Testing configuration changes
```bash
# Dry-run config validation
openclaw config validate

# Test specific agent spawn
openclaw subagents spawn <agent> "test task" --timeout 60

# Run endpoint tests
node ~/.openclaw/scripts/test-api-endpoints.js
node ~/.openclaw/scripts/test-aixor-anthropic.js
```

### Monitoring delivery queue
```bash
# Check delivery queue status (read-only)
python ~/.openclaw/scripts/delivery-queue-patrol-readonly.py

# Detect delivery issues
bash ~/.openclaw/scripts/detect-fake-delivery.sh
```

## Scheduled Tasks (Cron Jobs)

Jobs are defined in `cron/jobs.json`. Examples:
- **Memory Dreaming Promotion**: Promotes weighted short-term recalls into MEMORY.md (runs daily at 3am)
- **AI圈24h晨报**: Generates 24h AI industry news briefing and delivers to Feishu user (runs daily at 7am)

Job properties:
- `schedule.kind`: "cron" with `expr` (cron expression) and optional `tz` timezone
- `sessionTarget`: "main" or "isolated"
- `delivery.mode`: "announce" with channel and target
- `payload`: Agent turn message or system event

## Skills

Skills are organized in three layers with specific lookup priority (see skill lookup hierarchy below).

### Global skills (in `~/.openclaw/skills/`)
Available to all agents via `agents.defaults.skills`:
- `multi-search-engine`: Multi-engine search aggregation
- `wechat-article-reader`: WeChat article reading
- `feishu-create-doc`: Feishu document creation automation
- `memos-memory-guide`: Memory management with Memos integration
- `tvc-director`: TVC commercial direction (disabled)
- Plus 39 other global skills

### Workspace-specific skills

**workspace-design/skills/** (design agent exclusive):
- `brand-poster-creator`: Brand poster design workflow
- `brand-poster-distiller`: Brand poster requirement extraction
- `xiangqingye-desigen`: Product detail page design
- `dreamina-cli`: Dreamina AI video generation CLI wrapper
- `dreamina-reference-video`: Reference video processing for Dreamina
- `image-deglaze`: Image deglaze and style transfer
- `psd-layered-rebuilder`: PSD layered file rebuilding
- `product-photography-workflow`: Product photography generation workflow
- `video-expert-analyzer`: Video analysis and scoring tool
- Plus other design tools

**workspace-business/skills/** (business agent exclusive):
- `quote-skill`: Quote generation and formatting
- `business-project-intake`: Business project intake and requirements gathering

**workspace-research/skills/** (research agent exclusive):
- `research-analyst`: Research analysis methodology tool

Each skill has a `SKILL.md` defining the workflow. AGENTS.md rule 0.1 mandates checking skills before any task.

### Skill lookup hierarchy
Skills are searched in three layers:
1. **Workspace-local skills**: `workspace-*/skills/` (highest priority)
2. **Global skills**: `~/.openclaw/skills/`
3. **Built-in skills**: Bundled with OpenClaw package

### Skill development
- Each skill must have a `SKILL.md` with workflow definition
- Test skills before deployment to avoid breaking production workflows
- When optimizing skills, prepare changes but don't auto-execute project generation tasks
- Archive inactive skills to `skills-store*/` directories

### Storyboard generation rules
For video storyboard generation:
- **Must use standard grid layouts**: Refer to the standard layout table (GRID_LAYOUT)
- **Non-standard shot counts** (5, 7, 11, etc.) must be merged/split/expanded to standard counts first
- Never invent custom layouts