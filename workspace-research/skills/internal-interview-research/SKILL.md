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
7. 访谈外发和跟进只能使用 `research` 账号，不能退回用户本人身份。
8. 能用判断题就不用开放问答，能用选择题就不用开放问答。
9. 默认优先用飞书互动卡片，先让对方点一下，再决定要不要继续问。

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

## 推荐命令

### 1. 初始化项目

```bash
python3 {baseDir}/scripts/init_internal_interview_project.py \
  --workspace-root /Users/a123/.openclaw/workspace-research \
  --project-name 组织协作访谈 \
  --initiator-name 李经理 \
  --initiator-feishu-id user:ou_xxx \
  --research-goal "了解跨部门协作中的信息断点" \
  --research-scope "产品、销售、交付三方的协作体验" \
  --participant-source-mode 直接名单 \
  --participant-scope-text "核心参与人" \
  --project-deadline-at 2026-05-30T18:00:00+08:00 \
  --participant "张三:user:ou_zhangsan:销售代表" \
  --participant "李四:user:ou_lisi:产品经理"
```

### 2. 更新截止时间

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py deadline \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --new-deadline-at 2026-05-31T18:00:00+08:00 \
  --changed-by 李经理 \
  --reason "新增两位关键受访对象"
```

### 3. 更新受访对象状态

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py participant \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --name 张三 \
  --status 待回复 \
  --last-outbound-at 2026-05-22T09:00:00+08:00 \
  --followup-count 0
```

### 4. 巡检下一步动作

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py inspect \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 5. 生成某位受访对象的触达方案

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py outreach-plan \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --name 张三
```

### 6. 到截止时间后收口

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py finalize \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 7. 用户要求停止调研时收口并清理巡检

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py stop \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --stopped-by 李经理 \
  --stop-reason "发起人要求停止当前调研" \
  --cron-jobs-path /Users/a123/.openclaw/cron/jobs.json
```

### 8. 生成最终交付摘要

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py delivery \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 9. 准备飞书真实交付

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py prepare-delivery \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈
```

### 10. 注册项目巡检任务

```bash
python3 {baseDir}/scripts/manage_internal_interview_project.py register-cron \
  --project-dir /Users/a123/.openclaw/workspace-research/projects/组织协作访谈 \
  --cron-jobs-path /Users/a123/.openclaw/cron/jobs.json
```

## 访谈提问规则

默认顺序固定为：

1. 判断题
2. 选择题
3. 开放问答

默认约束：

- 首条私聊固定为：`1 条说明消息 + 1 个判断题互动卡片`
- 首条不允许一次抛多个问题
- 单轮最多只推进 1 个信息目标
- 单轮最多 1 个追问
- 单人有效问题上限默认 4 个
- 不允许连续两轮都用开放问答，除非对方主动展开长回复

优先采集的 3 类信号：

- `是否使用过`
- `主要使用场景或主要阻力`
- `培训期待或改进方向`

只要这 3 类信号已经拿齐，就直接收口，不要继续追问。

## 飞书触达规则

内部访谈默认优先使用：

- `message`
- `accountId=research`
- 飞书互动卡片

判断题默认用双按钮卡片。

选择题默认用 3-4 个按钮卡片。

如果按钮不足以表达，再退化为单选选择卡片。

如果当前卡片能力不可用，再退化为短文本选项消息，但仍保持“短问题 + 明确选项”，不要立刻切成长问答。

## 执行步骤

1. 先和发起人完成立项访谈，补齐目标、范围、受访对象来源方式。
2. 立刻创建项目目录与 YAML/Markdown 骨架。
3. 如发起人直接给名单，写入 `受访对象清单.yaml`。
4. 如发起人只给范围，先生成建议名单，再等确认；确认前不批量外发。
5. 设计调研问题清单并写入 `调研问题清单.md`，但真正访谈时优先转成判断题/选择题。
6. 截止时间存在后，才进入自动访谈。
7. 发首条私聊前，先运行 `outreach-plan`，确认发送账号、首轮说明消息、判断题卡片和文本降级方案。
8. 每次飞书对话推进后，更新受访对象状态、最近发出时间、最近回复时间、已跟进次数、访谈记录路径、完成摘要，以及最近一次提问方式、累计按钮题次数、累计开放题次数、已收集信号。
9. 通过巡检动作决定继续等待、第一次跟进、第二次跟进、最终截止提醒，或到期封口。
10. 到截止时间后，把未完成对象标记为“已超时”，进入分析总结。
11. 如果发起人中途明确说“停止这个调研”或“先停掉”，立刻运行 `stop`：
    - 回收当前已沉淀信息
    - 把未完成对象按现有样本收口
    - 输出停止版最终调研报告
    - 检查并清理相关巡检定时任务
12. 运行 `prepare-delivery` 生成 `飞书交付清单.json`，按清单做飞书真实发送。

## 默认催访规则

- 首条私聊后 `6h` 未回复：第一次跟进
- 再过 `12h` 未回复：第二次跟进
- 距离截止小于 `6h`：最终截止提醒
- 到截止时间：未完成对象统一封口

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
- `research` 账号不可用：暂停外发并通知发起人，不允许切到用户身份
- 互动卡片当前不可用：退化为短文本选项消息，不要立刻改成长问答
- 用户明确要求停止调研：立即收口并清理巡检任务，不要继续等待后续回复
- 截止时间被修改：必须写入 `截止时间变更记录`
- 到期未回复：标记“已超时”，不要无限催访
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
