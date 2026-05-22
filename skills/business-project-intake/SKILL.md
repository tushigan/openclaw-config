---
name: business-project-intake
description: Use when business docking requests need project background collection, durable project setup, material archiving, progress tracking, or quote handoff preparation before formal quoting.
metadata:
  openclaw:
    requires:
      bins:
        - python3
---

# 业务对接立项 Skill

## 适用场景

这个 skill 用来处理业务对接、项目立项、材料归档、进展维护，以及进入报价前的交接准备。

它适合以下情况：

- 用户发来新的业务需求，还没正式报价
- 一个老项目又继续推进，需要续接背景和材料
- 飞书录音、聊天截图、现场拍照、需求文档要沉淀进项目
- 业务已经聊到可以准备报价，但还没正式切入报价输出

## 主目录

业务项目固定放在：

- `/Users/a123/.openclaw/workspace-business/projects/客户名/项目名/`

正式报价子项目固定放在：

- `/Users/a123/.openclaw/workspace-business/projects/客户名/项目名/quote/`

## 最少立项字段

正式建档前，至少确认：

1. `客户名`
2. `项目名`
3. `当前目标`
4. 至少一份 `来源材料`

字段不够时，不正式建档，只补缺的最少字段。

## 固定工作流

1. 先判断这是新项目还是旧项目
2. 旧项目先读 `project.json`、`progress.json`、`tasks.json`、`materials.json`
3. 新项目先判断最少字段是否已满足
4. 满足后运行 `scripts/init_business_project.py`
5. 新材料进入后，运行 `scripts/archive_project_material.py`
6. 涉及录音时，先转写或整理纪要，再回写项目进展和待办
7. 只有当项目已进入 `待报价` 且用户明确说开始报价时，才准备 `quote-handoff.json`
8. 正式报价仍交给 `quote-skill`
9. 若当前会话来自 Feishu，且本轮需要向用户交付真实文件，必须执行真实发送动作，不能只回复本地路径或 `MEDIA:/...`

## 材料处理规则

- 录音放到 `materials/audio/`
- 聊天截图、现场拍照、参考图放到 `materials/images/`
- 文档、PDF、表格放到 `materials/docs/`
- 聊天摘录或结构化摘要放到 `materials/chat/`

每次复制材料后，都必须更新 `materials.json`。

## 录音默认动作

收到录音时，默认要完成：

1. 归档原文件
2. 形成纪要或摘要
3. 更新 `progress.json`
4. 更新 `project.json`
5. 更新 `tasks.json`

## 报价切换规则

不要因为“感觉快报价了”就提前进入报价流程。

只有同时满足：

1. 当前阶段已到 `待报价`
2. 用户明确说开始报价

才运行：

1. `scripts/prepare_quote_handoff.py`
2. `quote-skill` 的报价初始化与输出流程
3. `scripts/sync_quote_state.py`

## 飞书交付边界

1. 业务立项阶段若只是做内部归档、项目回写、准备报价交接，向上游 agent 回传时可以给绝对路径，但必须明确写“尚未对最终用户发送”。
2. 一旦进入用户直连会话，且用户明确要文件、纪要、报价或交接件，就必须发送真实文件或真实文档链接，不能把本地路径当成交付完成。
3. 正式报价文件的用户交付，以 `quote-skill` 的飞书交付规则为准；业务专家不得只把 `quote/` 目录下的 `HTML` 路径发给用户。

## 常用脚本

1. `scripts/init_business_project.py`
   - 初始化业务项目目录和五份主 JSON
2. `scripts/archive_project_material.py`
   - 复制一份材料进项目目录，并登记到 `materials.json`
3. `scripts/prepare_quote_handoff.py`
   - 生成或更新 `quote-handoff.json`
4. `scripts/sync_quote_state.py`
   - 报价完成后，把报价状态和输出结果回写到业务项目

## 输出后必须落盘什么

1. `project.json`
2. `materials.json`
3. `progress.json`
4. `tasks.json`
5. `quote-handoff.json`
