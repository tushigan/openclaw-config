---
name: internal-interview-research
description: Use when 需要做内部员工访谈调研、培训前访谈、发起人立项访谈、问题清单设计、飞书 1 对 1 访谈执行、找某位员工做访谈测试、或按截止时间自动催访与收口。
metadata:
  openclaw:
    emoji: "🗂️"
    requires:
      bins:
        - python3
---

# 内部访谈调研 Skill

这个 skill 用来跑“内部员工访谈调研项目”。

它不是泛化搜索 skill，也不是单次资料整理 skill。它适合从发起人访谈开始，连续推进一个带截止时间、带受访对象清单、带飞书 1 对 1 对话、带最终收口报告的完整调研项目。

## 适用场景

- 用户要做内部员工访谈调研
- 需要先访谈发起人，确认调研目的与范围
- 需要设计访谈问题清单
- 需要规划受访对象名单，或先按范围生成建议名单
- 需要在飞书上主动发起 1 对 1 调研对话
- 需要按截止时间自动催访、自动收口
- 需要把全过程沉淀为项目文件，而不是只留在聊天上下文里

## 不适用场景

- 外部市场资料搜索
- 行业报告、竞品、新闻、公开来源检索
- 一次性问卷整理但没有持续访谈项目

这些场景优先使用 `multi-search-engine` 或 `research-analyst`。

## 核心原则

1. 先立项，再访谈。
2. 没有截止时间，不进入自动访谈。
3. 所有推进依据都落在项目文件里，不依赖会话记忆。
4. YAML 管状态，Markdown 管内容。
5. 到截止时间必须收口，不能无限等回复。
6. 文件、字段、输出文案在不破坏规范的前提下尽量中文。
7. `research` 只负责立项、巡检、停止、总结；真正对外访谈由专属 `research-shared` 会话执行。
8. 访谈外发和跟进只能使用 `accountId=research`，不能退回用户本人身份。
9. 真实调研项目里，每位受访对象的长期访谈通道真值固定为 `agent:research-shared:feishu:direct:<open_id>`；绑定、回收、巡检都围绕这条 direct shared 通道判断。
10. `research-shared:subagent:...` 只允许当 helper/worker 使用；它可以失活、重建或被清理，但不能再当成长期绑定真值。
11. `message` 返回 `ok=true` 只代表“已调用发送”，不代表“已确认发出”。
12. 发送核验必须优先用同一次 `message` 返回里的 `messageId + chatId`；不能再用 `feishu_im_user_get_messages(open_id=...)` 当发送验收依据。
13. 不允许用临时脚本或 `exec` 直改 YAML 充当主流程状态更新。
14. 能用判断题就不用开放问答，能用选择题就不用开放问答。
15. 真实调研默认只用纯文本短问题 + 明确选项，不走卡片。
16. 用户晚 5 分钟、10 分钟、30 分钟甚至更久回复都可以，只要没解绑，回复仍会回到原专属 shared 会话。
17. 截止后但最终飞书报告还没发出时，晚到回复继续纳入并刷新分析；报告一旦发出，项目冻结。
18. 禁止为后续批次提前 `sessions_spawn` 出 live shared 待命会话；`research-shared` 会话只允许在“现在就要 bind + 首发”的同一条执行链路里创建。
19. `shared 协议不完整` 只代表“真实 inter-session 投递缺 strict payload”；不能把“刚 spawn 但还没收到 payload”的待命状态当成协议错误。

## 默认项目目录

项目固定放在：

- `/Users/a123/.openclaw/workspace-research/projects/项目名称/`

默认至少生成：

- `项目总表.yaml`
- `受访对象清单.yaml`
- `发起人访谈纪要.md`
- `调研问题清单.md`
- `阶段总结.md`
- `最终调研报告.md`
- `访谈记录/`

## 共享版正式入口

`research-shared` 共享版只允许通过下面这个正式入口执行本 skill：

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research
```

共享版规则：

- 不直接执行 `python3`、`bash`、`zsh` 去跑本 skill 的源码脚本。
- 不在 workspace 根目录手工创建测试文件、临时文件或旁路结果文件。
- 立项类动作走 `init`。
- 项目推进、巡检、分析、收口类动作走 `manage <subcommand>`。

## 推荐命令

### 1. 初始化项目

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research init \
  --project-name 组织协作访谈 \
  --initiator-name 李经理 \
  --initiator-feishu-id user:ou_xxx \
  --research-goal "了解跨部门协作中的信息断点" \
  --research-scope "产品、销售、交付三方的协作体验" \
  --participant-source-mode 直接名单 \
  --participant-scope-text "核心参与人" \
  --project-deadline-at 2026-05-30T18:00:00+08:00 \
  --project-type 真实调研 \
  --participant "张三:user:ou_zhangsan:销售代表" \
  --participant "李四:user:ou_lisi:产品经理"
```

### 2. 更新截止时间

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage deadline \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --new-deadline-at 2026-05-31T18:00:00+08:00 \
  --changed-by 李经理 \
  --reason "新增两位关键受访对象"
```

### 3. 更新受访对象状态

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage participant \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --name 张三 \
  --status 待回复 \
  --last-outbound-at 2026-05-22T09:00:00+08:00 \
  --followup-count 0 \
  --execution-session-id session-zhangsan \
  --execution-session-key research-shared-zuzhi-xietong-zhangsan \
  --conversation-binding-id research:ou_zhangsan \
  --conversation-binding-status 已绑定 \
  --binding-confirmed-at 2026-05-22T08:59:30+08:00 \
  --binding-confirmation-evidence "status 校验通过：ou_zhangsan -> research-shared-zuzhi-xietong-zhangsan" \
  --binding-target-session-key research-shared-zuzhi-xietong-zhangsan \
  --binding-check-result 已核验通过 \
  --last-message-id om_xxx \
  --last-chat-id oc_xxx \
  --send-confirmation-status 已确认回执
```

### 4. 巡检下一步动作

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage inspect \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 5. 生成手动继续推进后台合同

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage manual-continue-contract \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --cron-jobs-path /Users/a123/.openclaw/cron/jobs.json
```

当用户说“继续推进当前项目”时，`research` 主会话只做两步：

- 先运行 `manual-continue-contract`
- 如果返回 `是否启动后台worker=true`，就启动一个 isolated `research` worker 去执行整轮推进

主会话只负责触发 worker 和接收整轮结果，不直接执行 `spawn / bind / status verify / sessions_send / writeback`。

### 6. 生成推进合同

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage advance \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --cron-jobs-path /Users/a123/.openclaw/cron/jobs.json
```

`advance` 现在是“推进合同生成器 + 状态补偿器”：

- 先回退 `待回复` 但发送确认不足的脏状态
- 再同步当前批次、补自动解绑、补自动注册 cron
- 最后输出 `当前批次对象列表 / 执行合同 / 跟进行动 / 本轮汇报摘要`

真正执行这些合同的是后台 worker，不是用户主会话。

### 7. 后台 worker 执行入口

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage run-batch-worker \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --trigger manual-worker \
  --status prepare \
  --cron-jobs-path /Users/a123/.openclaw/cron/jobs.json
```

固定状态流：

- `prepare`：检查是否已有 active worker；没有则生成带 `workerRunId` 的启动合同
- `started`：只能执行 `prepare` 返回的 `启动命令`，用同一 `workerRunId` 写入 worker 运行态，并重跑 `advance`
- `heartbeat`：只能执行 `prepare` 返回的 `心跳命令`，用同一 `workerRunId` 更新心跳和最近摘要
- `finished`：只能执行 `prepare` 返回的 `完成命令`，用同一 `workerRunId` 清理 worker 运行态，并重算当前批次
- 缺少 `workerRunId` 时必须 fail-closed：返回结构化错误，不允许把 `后台执行中=true` 写盘
- worker 调用 CLI 时，`exec` 每次只允许执行一条命令；禁止用 `&&`、`;`、`|`、`printf` 或 here-doc 把多条 `python3 ...` 拼成一条

### 8. 生成某位受访对象的触达方案

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage outreach-plan \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --name 张三 \
  --requester-session-key <当前research主会话key>
```

### 9. 生成批量派发计划

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage dispatch-plan \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --requester-session-key <当前research主会话key>
```

默认不传 `--batch-size` 时，输出“一次性全发首轮”清单。
只有明确需要限流时，才额外传：

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage dispatch-plan \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --batch-size 10 \
  --batch-interval-minutes 10
```

### 10. 到截止时间后收口

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage finalize \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 11. 生成最新分析结果

```bash
/Users/a123/.openclaw/workspace-research/skills/internal-interview-research/bin/shared-internal-interview-research manage analyze \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 12. 用户要求停止调研时收口并清理巡检

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py stop \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --stopped-by 李经理 \
  --stop-reason "发起人要求停止当前调研" \
  --cron-jobs-path /Users/a123/.openclaw/cron/jobs.json
```

### 13. 生成最终交付摘要

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py delivery \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 14. 准备飞书真实交付

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py prepare-delivery \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 15. 标记飞书最终交付已完成并冻结项目

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py delivery-complete \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --doc-url https://example.feishu.cn/docx/xxx \
  --summary-message-id om_xxx \
  --cron-jobs-path /Users/a123/.openclaw/cron/jobs.json
```

### 16. 补偿回收历史漏写回复

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py recover-replies \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --research-session-root /Users/a123/.openclaw/agents/research/sessions
```

### 17. 清理误触发的待命 shared 会话

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py cleanup-prebuilt-shared \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 18. 冻结观察期结束后关闭项目

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py close-project \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 19. 注册项目巡检任务

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py register-cron \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --cron-jobs-path /Users/a123/.openclaw/cron/jobs.json \
  --interval-minutes 180 \
  --report-mode every-round \
  --auto-created true
```

真实调研项目默认在首轮前置就绪后自动注册两条任务：

- 推进任务：每 3 小时一次，先跑 `run-batch-worker --status prepare`，再严格执行该次 `prepare` 返回的 `启动命令 / 心跳命令 / 完成命令`
- 推进 worker 的 `exec` 必须逐条执行单命令；不要把多个 `outreach-plan` / `inspect` / `participant` 命令拼到一次 `exec`
- 汇报任务：每 3 小时一次，只在本轮有变化时向发起人发短汇报
- 这两条 cron 必须显式注册到 `research` agent，不能依赖默认落到 `main`
- `research` / `research-shared` 的项目回写链路依赖 `tools.exec.host=auto`；如果仍是 `gateway`，shared 会话里的 YAML/Markdown 回写会被 `exec host not allowed` 拦住

项目进入 `stop / delivery-complete / close-project` 终态后，要自动清理这两条任务。

### 18. 生成链路验收测试方案

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py acceptance-plan \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/内部访谈链路验收-2026-05-22 \
  --name 测试号 \
  --config-path /Users/a123/.openclaw/openclaw.json \
  --requester-session-key <当前research主会话key>
```

双人并行验收时，重复传两次 `--name`：

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py acceptance-plan \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/内部访谈双人链路验收-2026-05-22 \
  --name 测试甲 \
  --name 测试乙 \
  --config-path /Users/a123/.openclaw/openclaw.json \
  --requester-session-key <当前research主会话key>
```

注意：

- `--config-path` 只能指向正式配置 `/Users/a123/.openclaw/openclaw.json`
- 不要改成临时裁剪配置、空白配置或 `_temp_*.json`

## 访谈提问规则

默认顺序固定为：

1. 判断题
2. 选择题
3. 开放问答

默认约束：

- 首条私聊固定为：`1 条说明消息 + 1 个短文本选择题`
- 首条不允许一次抛多个问题
- 单轮最多只推进 1 个信息目标
- 单轮最多 1 个追问
- 单人有效问题上限默认 4 个
- 不允许连续两轮都用开放问答，除非对方主动展开长回复

优先采集的 3 类信号：

- `是否使用过`
- `主要使用场景或主要阻力`
- `培训期待或改进方向`

默认收口真值：

- 只要这 3 类信号已经拿齐，就直接收口，不要继续追问
- 如果 3 类信号还没拿齐，但累计有效问题数已经达到 4，也直接收口
- `好的`、`怎么没有反应的`、`问完问题之后会自动解绑吗` 这类非调研流程消息，不计入有效问题数

## 飞书触达规则

内部访谈默认优先使用：

- `feishu_conversation_binding`
- `message`
- `accountId=research`
- 纯文本短问题 + 明确选项

真实调研默认格式：

- 首轮：`1 条说明消息 + 1 个短文本选择题`
- 示例：`关于这次调研涉及的主题，你现在更接近哪种情况？请直接回复：已在使用 / 知道但少用 / 还没开始 / 说不清`
- 后续追问：一次只补 1 个最关键问题

只有链路验收场景才继续使用按钮卡片或 `feishu_ask_user_question`。

## 链路验收测试规则

当用户明确说先不要测真实员工，而是先验收回收链路时：

- 必须先生成一份 `acceptance-plan`
- 默认只允许 1 个受控测试对象
- 默认不注册 cron
- 默认两轮结构化消息就结束
- 第一轮只验证“能否收到首轮触达并明确回复”
- 第二轮只验证“收到回复后能否继续”
- 真正的通过标准不是“消息到了 research-shared”，而是“回复进入指定的执行会话Key，对应专属 shared 会话能继续追问”
- 首轮优先发按钮卡片；如果卡片不可用，允许改成短文本明确选项
- 只要首轮消息真实发出、回复回到同一 shared 会话、第二轮还能继续、项目文件也完成回写，就算链路通过
- 项目文件里不能再出现 `card.create code=200861`、`V2 卡片不支持 action` 这类旧链路备注

如果要验收多人并行链路：

- 默认先做 2 个受控测试对象，不直接扩到 3-5 人
- 两个人都要各自创建 `research-shared` 专属会话
- 两个人都要各自绑定、各自发送、各自回收
- 通过标准要额外增加：互不串会话、互不串项目记录

如果 `acceptance-plan` 返回阻止原因，就先修前置条件，不要直接测真实对象。

## 执行步骤

1. 先在 `research` 中和发起人完成立项访谈，补齐目标、范围、受访对象来源方式。
2. 立刻创建项目目录与 YAML/Markdown 骨架。
3. 如发起人直接给名单，写入 `受访对象清单.yaml`。
4. 如发起人只给范围，先生成建议名单，再等确认；确认前不批量外发。
5. 设计调研问题清单并写入 `调研问题清单.md`，但真正访谈时优先转成判断题/选择题。
6. 截止时间存在后，才进入自动访谈。
7. 对每位受访对象，只在“现在就要执行绑定并首发”的窗口里创建专属 `research-shared` 会话；不要为了下一批待命对象提前 `sessions_spawn`。
8. 固定执行顺序改为：先确认 canonical direct shared 通道真值，再执行 `feishu_conversation_binding(bind) -> feishu_conversation_binding(status verify) -> sessions_send(strict payload) -> shared 内 message(accountId=research)`；如果需要 helper，会在这条链路里临时创建，但 helper 不是长期真值。
9. 没有 strict payload 投递时，不允许把对象推进成 `待首发 / 待回复 / 已形成可回收 shared 会话`；纯 helper 待命不算 ready。
10. `bind` 成功后，必须立刻再跑一次 `feishu_conversation_binding(action=status)` 复核；只有 `绑定记录.targetSessionKey == 执行会话Key`，且这个 `执行会话Key` 是 canonical direct shared key 时，才能把该对象写成 `会话绑定状态=已绑定`。
11. 把 `执行通道真值类型 / 执行会话代理 / 执行会话ID / 执行会话Key / 辅助执行会话ID / 辅助执行会话Key / 会话绑定ID / 会话绑定状态 / 最近一次绑定确认时间 / 最近一次绑定确认依据 / 最近一次绑定目标会话Key / 最近一次绑定检查结果` 写回 `受访对象清单.yaml`，未写回前不允许外发。
12. 发首条私聊前，先运行 `outreach-plan`；它必须同时检查：
   - `openclaw.json` 里的静态 `tools.sessions.visibility`
   - `openclaw.json` 里的静态 `tools.agentToAgent.enabled / allow`
   - 当前 `research` 主通话 Session 的运行时工具证据
   前台口径必须分三层报告：
   - 先说静态配置是否通过
   - 再说 runtime 检查是否通过
   - 最后明确结论属于“静态配置缺失 / 主会话权限快照过期 / 运行时工具检测异常 / shared 投递未放行”中的哪一种
   如果静态配置已正确、但当前主会话 runtime 仍是旧值，才允许提示“重启 gateway 后再在当前主对话触发一次新 turn”。
   如果只是拿不到可靠的 `context.compiled.tools` 证据，就只能报“运行时工具检测异常”，不能再默认建议 `/new`、`/reset`、切新主会话或重复重启。
13. 真正外发时，`research` 只能调用 `sessions_send(sessionKey=<执行会话Key>)` 把任务投递到 canonical direct shared 会话；不允许 `research` 直接用 `message` 兜底外发，也不允许混传 `label`、`.`、空格或其他占位寻址参数。
    - 当 `outreach-plan` 已给出 `首轮触达.工具参数` 后，执行阶段必须直接复用这组参数，不能再临场补 `label`、改 `sessionKey`、改 payload。
    - 如果准备发工具前发现请求里仍存在 `label`，必须先中止，并明确报告：`执行参数未按计划落地，本次调用仍残留 label，尚未真正投递。`
    - 只有 3 个允许键：`sessionKey / message / timeoutSeconds`。
14. `sessions_send.message` 只能使用 `outreach-plan` 生成的严格协议 payload 原文，禁止 research 主会话手写 `现在执行首轮真实调研外发...` 这类自由文本。payload 必须带 `[internal-interview-shared-payload/v1]` 标记，并包含 `project_dir / project_type / participant_name / participant_open_id / execution_session_key / first_touch_message / ingest_reply_command / finalize_participant_command / unbind_rule`。
15. 专属 `research-shared` 会话收到任务后，先校验 payload 是否完整；只有“已经收到 inter-session 投递但缺字段”时才回复 `shared 协议不完整`。纯 `sessions_spawn` 初始化阶段必须静默待投递，不得把待命状态当成协议错误。完整时再调用 `message`，并显式传：
    - `channel=feishu`
    - `accountId=research`
    - `target=user:受访对象open_id`
16. 外发后只有在 shared 会话里拿到同一次 `message` 返回的 `ok=true + messageId + chatId`，才能写 `待回复` 与发送确认字段；如果 shared 没拿到 `messageId + chatId`，必须停在 `待首发`。
17. 不允许再用 `feishu_im_user_get_messages(open_id=...)` 验证首发是否成功；如果 `open_id` 查出来的 `chat_id` 与 `message` 返回不一致，要记为 `核验口径冲突`。
18. 默认先运行 `dispatch-plan` 生成“一次性全发首轮”清单；只有明确需要限流时，才切到分批模式。`dispatch-plan` / `outreach-plan` 明确出现 `禁止预建待命会话=true` 时，不得再私自预热 shared 子会话。
19. `inspect` 只读项目文件并输出建议；`advance` 负责首轮外发、催访、截止提醒、到期封口和补回后刷新分析。若 `inspect` 发现“未首发但已有 live shared 且无 strict payload”，必须先执行 `cleanup-prebuilt-shared`，不得继续复用。
    - 前台汇报只能出现在“一整轮推进结束后 / 本轮遇到明确阻塞 / 项目进入里程碑终态”这 3 种时机。
    - 禁止把 `NO_REPLY`、内部补偿、待机文案、subagent completion 原文直接暴露给发起人。
20. `research -> research-shared` 的投递内容必须显式带上：`project_dir / project_type / participant_name / participant_open_id / execution_session_key / 当前收口规则 / 正式回写命令模板`；shared 缺任何一项都直接报“项目上下文缺失”，禁止临场猜项目。
21. shared 会话禁止读取其他项目文件来补上下文；一旦发现自己读到的项目路径与当前 `project_dir` 不一致，直接报“项目上下文漂移”，停止继续访谈。
22. shared 会话拿到新信息后，必须先写回项目 YAML/Markdown；写回成功后，才能继续追问或收口。不要手工拼状态，统一先执行正式命令：`manage_internal_interview_project.py ingest-reply ...`。
23. `ingest-reply` 至少要负责回写：`最近回复时间 / 最近一次回收时间 / 是否已回收至research / 累计有效问题数 / 已收集信号 / 最近一次业务状态 / 最近一次链路状态 / 对应访谈记录 Markdown`，并返回 `shouldUnbind=true|false` 和 `nextQuestion` 供 shared 会话决定是立刻收尾还是继续下一问。
    - 后续收到用户回复时，先读取当前 turn 的真实 `user` 文本作为 `<latestUserReply>`；`openclaw.runtime-context` 只用于提取 `<replyAt>`、`message_id`、`sender_id`。
    - 如果当前 turn 同时存在真实 `user` 文本和 `openclaw.runtime-context`，真实 `user` 文本是唯一正文真值。
    - 如果没有真实 `user` 文本，不允许执行 `ingest-reply`，必须返回结构化错误 `reply_text_missing`，详情写“当前消息未附正文”。
24. 如果回写失败，就把对象停在 `已收到回复但回写失败` 或 `已完成待回写`，shared 不再继续追问，也不允许口头宣布“已结束”或“已完成”。
25. 首次回复回收必须看 runtime 证据：canonical direct shared transcript 里真实出现入站，或 gateway 日志里出现 `routed via bound conversation <open_id> -> <执行会话Key>`；helper 会话缺失不能等价成解绑。如果只看到主对话 `dispatching to agent (session=agent:research:feishu:direct:...)`，只能判定“回复仍在主对话”，不能写成 shared 回收成功。
26. 任何 `最近回复时间 < 最近发出时间` 的消息，都只能记为“首发前主对话消息”，不能计作本轮 shared 回收。
27. 一旦某个对象达到 `已完成` / `收口完成`，必须立刻走“结束提示 -> 解绑 -> 退回 `research` 主对话`”：
    - 先确认本轮回复已经写回 `受访对象清单.yaml`、`项目总表.yaml`、`访谈记录/*.md`
    - 再由当前专属 `research-shared` 会话发结束提示：
      - 本次调研已完成
      - 后续再发与该调研相关的补充不再纳入记录
      - 当前私聊已切回 `research` 主对话
    - 然后立刻执行 `feishu_conversation_binding(action=unbind, accountId=research, target=user:open_id)`
    - 解绑成功后，必须再执行 `manage_internal_interview_project.py finalize-participant ...`，把 `会话绑定状态=已解绑`、`会话绑定ID=""`、`最近一次业务状态=已完成并自动解绑` 正式写回项目文件
28. 如果 shared 已收到回复但项目文件没更新，优先运行 `recover-replies` 做补偿回收；它会按 shared transcript 逐条补回有效问答、自动忽略非调研流程消息，并在满足收口条件后自动解绑。
29. 如果项目里存在“只有 `messageId` 没有 `chatId`”这类半成品发送状态，`recover-replies` 必须自动清理，不能继续保留成 `待回复`。
    - 如果 shared transcript 里只有 `openclaw.runtime-context`、没有真实 `user` 正文，只能记为 `reply_metadata_only` 或“仅元数据通知”，不能推进 `最近回复时间 / 最近一次回收时间 / 是否已回收至research`。
30. 如果项目里存在“只 spawn 未投递 strict payload”的待命 shared 脏状态，优先运行 `cleanup-prebuilt-shared`，把对象打回 `待创建会话` 后再按正式批次重建。
31. 到截止时间后，把未完成对象标记为 `已超时待收口`，先生成初版分析结果。
32. 如果有人在截止后才回复，只要最终飞书报告还没发出，就把状态改成 `超时后补回`，并刷新分析与交付草案。
33. 如果发起人中途明确说“停止这个调研”或“先停掉”，立刻运行 `stop`：
    - 回收当前已沉淀信息
    - 把未完成对象按现有样本收口
    - 输出停止版最终调研报告
    - 检查并清理相关巡检定时任务
    - 清理会话绑定
34. 运行 `prepare-delivery` 生成 `飞书交付清单.json`，按清单做飞书真实发送。
35. 飞书文档和摘要消息真实发出成功后，运行 `delivery-complete`，立即删除项目 cron，并把项目标记为冻结观察期；冻结期晚到回复只记录，不改主报告。
36. 冻结观察期默认保留 48 小时；到期后运行 `close-project`，统一解绑并关闭项目。

## 默认催访规则

- 首条私聊后 `6h` 未回复：第一次跟进
- 再过 `12h` 未回复：第二次跟进
- 距离截止小于 `6h`：最终截止提醒
- 到截止时间：未完成对象统一转 `已超时待收口`
- 截止后但未发最终报告：允许晚到回复补回
- 发出最终报告后：项目冻结观察期 48 小时，cron 删除；只有未完成对象才允许继续保留绑定，已完成对象必须已经退回 `research` 主对话

跟进文案也保持轻量：

- 先判断能不能继续用按钮题或选择题
- 能点一下就别让对方重新打一段
- 已拿到足够信号就致谢收口

## 输出要求

- 所有关键状态都要落在 YAML
- 所有长文本访谈内容都要落在 Markdown
- 最终报告必须明确：
  - 样本总数
  - 已完成数
  - 已超时数
  - 已拒绝数
  - 样本缺口说明
- 最终交付默认是：
  - 一份飞书文档
  - 一条飞书摘要消息
  - 如飞书文档工具当前不可用，则退回为 Markdown 报告附件 + 摘要消息

## 飞书真实交付规则

项目收口后不要只说“已经生成报告”。

必须继续完成真实交付：

1. 先运行 `prepare-delivery`
2. 读取生成的 `输出/飞书交付清单.json`
3. 优先执行交付清单里的首选顺序：
   - 用 `feishu_create_doc` 创建飞书文档
   - 再用 `message` 工具把摘要消息发给发起人，并附上文档链接
4. 如果 `feishu_create_doc` 因当前上下文限制不可用：
   - 退回到交付清单里的 fallback 顺序
   - 至少把 Markdown 报告附件 + 摘要消息真实发给发起人
5. 没有工具成功返回前，不得说“已交付”
6. 飞书文档与摘要消息都成功后，必须运行 `delivery-complete`，把项目冻结
7. `delivery-complete` 会自动删除项目 cron；48 小时观察期结束后，再运行 `close-project`

优先使用的工具：

- `feishu_create_doc`
- `message`（`channel=feishu`，显式 `target=user:ou_xxx`）

不要默认用 `feishu_im_user_message`。
这个工具是“以用户本人身份发消息”，需要当前 Feishu sender 上下文，不适合 cron / 后台 / 非当前用户直连场景。

如果 `research` 账号当前不可用：

- 不允许切到用户本人身份
- 不允许切到其他备用账号
- 只能暂停外发，并通知发起人等待 `research` 恢复或终止本次访谈

## 异常处理

- 没有截止时间：只能建档，不能自动访谈
- 建议名单未确认：不能开始批量外发
- 受访对象飞书标识缺失：先补对象信息，不直接发送
- helper 会话丢失：先看 canonical direct shared 绑定是否仍有效；helper 失活不等于访谈通道被删
- 只有 `会话绑定状态=已绑定` 但没有 `status` 复核证据：只能记 `待核验` 或 `绑定异常`，不能首发
- canonical `执行会话Key` 一旦变化：旧绑定立刻失效，必须重新 bind + status verify；如果只是 `辅助执行会话ID/Key` 变化，不得把对象打回未绑定
- 如果 `openclaw.json` 已是 `visibility=all`，但 `outreach-plan` / `acceptance-plan` 仍报 `主会话权限快照过期`：不要继续在旧主通话里硬试，直接切到新的 `research` 主会话后重跑
- 真实调研主流程不使用 `feishu_ask_user_question`、卡片发送或 poll 参数；如果看到旧逻辑残留，直接回到 `message + 纯文本明确选项`
- 只有 `messageId` 没有 `chatId`：这是半成品状态，不能继续保留在 `待回复`，必须补偿核验或清理回退
- 没有 `messageId + chatId`：不能把对象写成 `待回复`
- 首发前就收到消息：只能记为 `首发前主对话消息`，不能推进 `最近一次回收时间` 或 `是否已回收至research=true`
- 只拿到 `message ok=true`：只能记 `已调用发送`，不能回报“已确认发出”
- 发送核验时如果 `open_id` 路径和 `chatId` 路径得出不同会话：记为 `核验口径冲突`，停止把状态往成功推进
- `research` 账号不可用：暂停外发并通知发起人，不允许切到用户身份
- 真实调研不使用互动卡片；如果看到旧卡片逻辑，直接切回纯文本选择题
- 用户明确要求停止调研：立即收口并清理巡检任务，不要继续等待后续回复
- 截止时间被修改：必须写入 `截止时间变更记录`
- 到期未回复：先标记 `已超时待收口`，在最终报告发出前允许晚到补回
- 最终报告已发出后再回复：记为 `已关闭后回复`，只落记录，不改主报告
- 绑定期间收到非调研问题：只短提示“当前这条私聊用于本次调研回收；非调研问题请到 `research` 主对话单独提”，不要在 shared 会话里展开
- 已完成并解绑后再收到补充：默认回到 `research` 主对话，不自动重绑，不自动继续记入原调研项目；若确实需要补访，只能由 `research` 主对话显式重新发起
- 如果卡在主通道 visibility：前台汇报必须明确写“静态配置已通过，但当前主通道仍是旧权限快照，需要重建/切换主会话”，不要再笼统说“去看配置”
- 飞书文档创建失败：退回 Markdown 附件发送，不要卡死在“等文档成功”

## 字段说明

字段与状态说明见：

- [字段说明](references/字段说明.md)

## 不要这样做

- 不要把项目状态只留在聊天里
- 不要没有 deadline 就开始自动访谈
- 不要到截止时间后继续无限等待
- 不要把未完成样本当成“默认同意”
- 不要用英文状态值强迫团队理解内部流程，除非工具兼容必须保留
- 不要用 `feishu_im_user_message` 发内部访谈首条私聊
- 不要用你的个人飞书身份代替 `research` 发起访谈
- 不要一上来发 `1）2）3）` 式长问题
- 不要在已经拿到足够信号后继续往下问
