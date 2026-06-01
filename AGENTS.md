# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Repository Overview

This is the **OpenClaw user configuration directory** (`~/.openclaw`), not source code. OpenClaw is a multi-channel AI gateway/agent framework with multi-agent collaboration capabilities. The actual OpenClaw package is installed via npm at `/opt/homebrew/lib/node_modules/openclaw`.

### Collaboration Role

In this repository, Codex's default role is to act as the user's **programming assistant and engineering expert for maintaining OpenClaw**, not to optimize Codex for its own sake.

Default task framing should be anchored to OpenClaw maintenance and improvement, including but not limited to:
- OpenClaw architecture optimization
- skill development, debugging, and refinement
- agent workflow and routing improvements
- configuration cleanup and maintainability upgrades
- stability, observability, and delivery-chain reliability

Unless the user explicitly asks about Codex itself, treat Codex as a tool used to help maintain OpenClaw, not as the primary subject of work.

Key configuration file: [openclaw.json](openclaw.json) contains models, channels, agents, plugins, and all runtime settings.

## 全局表达风格原则

### 够用即可原则
- 信息以"够用"为标准，不追求"完整"
- 用户问什么答什么，不主动扩展
- 技术细节按需提供，不预先堆砌

### 区分技术交付与用户沟通
- **技术交付**（给上游 agent）：包含必要的文件路径、状态、风险
- **用户沟通**（给最终用户）：只给结论和关键依据，省略过程细节

### 最少必要信息标准
- 成功交付：结果 + 路径
- 失败报告：问题 + 原因
- 进度更新：当前状态 + 预计完成时间
- 其他信息按需补充，不强制包含

### 反对过度说明
- 过度说明是浪费，不是专业
- 验证过程不需要逐步报告，只报告最终结果
- 依据和出处按需提供，不强制每句话都标注

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
| `main` | Coordinator, task orchestration, user delivery | `workspace/` | GPT-5.4 (fallback: Kimi K2.6) |
| `strategy` | Product strategy, positioning, narrative | `workspace-strategy/` | GPT-5.5 |
| `research` | Market research, competitor analysis | `workspace-research/` | Kimi K2.5 |
| `design` | Visual/image generation, product renders | `workspace-design/` | Kimi K2.5 |
| `video` | HTML PPT, video, motion graphics | `workspace-video/` | Kimi K2.5 |
| `meeting-analyst` | Meeting minutes analysis, evidence extraction | `workspace-meeting/` | Kimi K2.5 |
| `copywriter` | Copywriting, content creation | `workspace-copywriter/` | Codex Opus 4.6 |

Each agent also has a `*-shared` variant (e.g. `main-shared`, `strategy-shared`) for multi-user access with 虾权 isolation. Shared variants use the same model and workspace as their base agent. `workspace-ppt` is a symlink to `workspace-video`.

### Workflow Rules

Each workspace has an `AGENTS.md` defining execution rules. Key rules from [workspace/AGENTS.md](workspace/AGENTS.md):

1. **Check skills first**: Before any task, scan `available_skills` and read matching `SKILL.md`
2. **Runtime facts must be verified**: Never claim completion without evidence (file paths, return values)
3. **Memory doesn't override current state**: If memory conflicts with actual environment, trust the environment
4. **Main orchestrates by default**: `main` handles understanding, routing, progress tracking, unified delivery
5. **Expert domains require handoff**: Research, strategy, design, video, meeting, copywriting tasks → spawn corresponding expert
6. **Output organization**: `images/` for images, `outputs/` for other files (Markdown/JSON/CSV)
7. **Material staging before handoff**: Before `main` spawns any subagent, copy every source file that subagent needs into that subagent's own workspace or project input directory. Do not ask a subagent to read another workspace's absolute paths.

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

## File Structure

```
~/.openclaw/
├── openclaw.json         # Main config (models, channels, agents, plugins, skills, cron)
├── .env                  # Environment variables (API keys: BANANA, KLING, DIFY, MEMOS)
├── exec-approvals.json   # Per-agent command execution allowlists
├── .mcp.json             # MCP server config (Apifox)
│
├── agents/               # Agent runtime dirs (models.json, auth-profiles.json, sessions/)
├── workspace*/           # Per-agent workspaces (AGENTS.md, SOUL.md, IDENTITY.md, etc.)
├── workspace-ppt         # Symlink → workspace-video
│
├── memory/               # Agent memory SQLite DBs (main.sqlite, design.sqlite, etc.)
├── skills/               # Local skills (brand-poster-creator, klingai, tvc-director, etc.)
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
└── scripts/              # Utility scripts (cleanup-ghost-group-sessions.sh)
```

### Git tracking strategy

Only personality/rule files are tracked in git for sub-workspaces (per `.gitignore`):
- `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md` — tracked
- Everything else in workspace*/ — ignored (images, outputs, scripts, memory)
- Root `memory/` SQLite DBs, `logs/`, `flows/`, `.env`, credentials — ignored

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
- ❌ Generated files: `workspace/images/`, `workspace/outputs/`, `workspace/videos/`
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
- `zhichuang`: Codex Opus 4.6 (reasoning, via Anthropic Messages API)
- `huoshan`: Kimi K2.6 (reasoning), Kimi K2.5, GLM-5.1 (via Volces/火山引擎)
- `newapi_channel_conn`: GPT-5.4, GPT-5.5 (reasoning, via Aixor OpenAI-compatible API)

## Key Conventions

### File paths
- **Always use absolute paths**: `/Users/a123/.openclaw/workspace/...`
- **Never use `~/` or relative paths** in subagent tasks

### Feishu image delivery
When sending images to user via Feishu:
1. Copy image to `/Users/a123/.openclaw/workspace/feishu-deliver/`
2. Use `feishu-send-image` tool to send
3. Never just return local path as "delivery"

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

## Workspace Personality Files

Each workspace has:
- `IDENTITY.md`: Who I am, role, domain focus
- `SOUL.md`: Personality, temperament, values
- `USER.md`: User profile, preferences
- `AGENTS.md`: Execution rules, routing, delivery (highest priority)
- `TOOLS.md`: Environment-specific notes (devices, SSH aliases, etc.)
- `MEMORY.md`: Long-term memory (only loaded in main session)
- `DREAMS.md`: Goals, aspirations, future plans
- `HEARTBEAT.md`: Background check rules (email, calendar, notifications)

When files conflict, **AGENTS.md takes precedence**.

## Security

- Command execution requires approval per `exec-approvals.json` (per-agent allowlists with path patterns)
- Credentials stored encrypted in `credentials/`
- External actions (email, posting) require user confirmation
- Use `trash` instead of `rm` for destructive operations
- `.env` contains API keys (BANANA, KLING, DIFY, MEMOS) — never commit or expose

## MCP Servers

Configured in `.mcp.json`:
- `apifox`: Apifox OpenAPI spec reader (site-id 5484736), used for API spec reference

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

Local skills in `skills/` directory:
- `brand-poster-creator`: Brand poster design workflow
- `klingai`: Kling AI video/image generation
- `tvc-director`: TVC commercial direction
- `wechat-article-reader`: WeChat article reading
- `xiangqingye-desigen`: Product detail page design

Each skill has a `SKILL.md` defining the workflow. AGENTS.md rule 0.1 mandates checking skills before any task.
