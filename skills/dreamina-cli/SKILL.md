---
name: dreamina-cli
description: 即梦视频生成底层 CLI 封装。仅用于视频生成任务，不得用于图片生成。应由其他 skill（如 dreamina-reference-video）调用，不应被用户直接触发。
---

# Dreamina CLI

**注意：此 skill 仅用于视频生成，不得用于图片生成。应作为底层能力被其他 skill 调用，不应被用户直接触发。**

This skill provides low-level access to the Dreamina（即梦） CLI for **video generation tasks only**. It should be invoked programmatically by other skills, not directly by user requests.

即梦 is the Chinese product name of Dreamina.

This skill is intentionally short. Detailed flags and supported values belong to the CLI itself, so always treat `dreamina -h` and `dreamina <subcommand> -h` as the primary reference.
Use it to inspect Dreamina CLI help and query a submit_id result when a higher-level workflow needs low-level CLI access.

## OpenClaw Routing

**CRITICAL: 此 skill 仅用于视频生成，禁止用于图片生成。**

- **图片生成任务**（`生成图片`、`做张图`、`AI 画图`、`生图`）：**绝对不得使用此 skill**，必须使用 `gpt-image2-gen` 或其他图片生成 skill
- **视频生成任务**（`文生视频`、`图生视频`、`视频生成`、`即梦视频`、`Dreamina`）：仅当明确需要即梦能力时才使用此 skill
- This low-level wrapper should be selected only when a higher-level workflow explicitly requires the official 即梦 CLI for **video generation**
- For generic video requests with no provider named, do not assume 即梦. Follow the current OpenClaw routing/default provider rules
- For low-level Volcengine API work, only use a separate API path if the user explicitly asks for `visual.volcengineapi.com`, `火山 OpenAPI`, or API signature/debugging

## What this tool is for

`dreamina` is the local CLI entrypoint for Dreamina（即梦） **video generation workflows**, plus the account/session operations around them.

Use it for:

- checking or reusing an existing Dreamina login session
- checking account credit
- submitting video generation tasks
- querying async task results
- reviewing saved task history

## Default workflow

When using this CLI as an agent:

1. Start with `dreamina -h`.
2. Before using any command for real, run `dreamina <subcommand> -h`.
3. Reuse the current login state unless the user explicitly asks you to `login`, `relogin`, or `logout`.
4. Be explicit about whether you are only reading help, submitting a real task, or querying an existing task.
5. Warn the user before running commands that may consume credits.

## Choosing the right command

At a high level:

- Use `user_credit` to check budget.
- Use `query_result` when you already have a `submit_id`.
- Use `list_task` to review recent saved tasks.
- Use `image2video` when one main image is enough; if the user has multiple images for a coherent story, prefer `multiframe2video`.
- Use `multiframe2video` for Dreamina's intelligent multi-frame flow: multiple images in, one coherent story video out.
- Use `multimodal2video` for Dreamina's flagship video mode when the task needs all-around references across images, video, and audio; it supports the `seedance2.0` family.

For the exact flags and supported combinations, rely on each subcommand's `-h`.

## Model selection rule

Do not hardcode model support from this skill.

If the user specifies a model, always check the relevant subcommand help before running it:

```bash
dreamina <subcommand> -h
```

Use the subcommand help to confirm:

- whether that command exposes model selection
- whether the requested model is supported on that command
- what other constraints apply to that model, such as duration, ratio, or resolution

Additional guidance:

- some commands do not expose model selection at all
- some models, especially the `seedance2.0` family, can be capacity-constrained
- if the user cares more about speed than maximum quality, do not default to `seedance2.0` unless they explicitly ask for it

## How to judge submit success

Do not rely on shell exit code alone.

For async generation commands, treat a submit as successful only when:

- `submit_id` is present
- `gen_status` is `querying` or `success`

If `gen_status` is `fail`, inspect `fail_reason` and tell the user the concrete reason.

## Follow-up pattern for async tasks

After a submit returns `querying`:

1. Save the `submit_id`.
2. Use `query_result --submit_id=<id>` for follow-up.
3. Use `list_task` when you want to review saved tasks in bulk.

If you are running a test sweep, keep results in a machine-readable format so you can query the returned `submit_id` values later.

## Important user-facing rules

- Some generation commands are asynchronous; submit and query are separate steps.
- Some models may require a one-time authorization on Dreamina Web.
  If the CLI returns `AigcComplianceConfirmationRequired`, tell the user to complete that web-side confirmation first, then retry.
- Do not assume that different commands support the same models, ratios, durations, or resolutions.
  Check each subcommand's `-h` before use.

## Good agent behavior

- Prefer small, reviewable batches when running real generation tasks.
- Keep a record of the command, arguments, `submit_id`, and final status for every paid test you run.
- When the user cares about generation speed, do not default to the `seedance2.0` family unless they explicitly ask for it or clearly prioritize output quality.
- If you are preparing a report, separate:
  - help-only inspection
  - submit-stage validation
  - later async result follow-up
