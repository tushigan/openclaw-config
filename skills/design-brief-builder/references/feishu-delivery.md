# Feishu Delivery

Use this reference only when publishing or updating the design brief to Feishu/Lark in OpenClaw.

## OpenClaw Feishu Integration

OpenClaw uses the `message` tool for Feishu delivery, NOT `lark-cli`. All Feishu document creation and updates go through the `message` tool with appropriate parameters.

## Auth Check

Before creating or updating a Feishu document, verify that the current session has Feishu channel access. OpenClaw handles authentication internally through its channel system.

If you're uncertain about auth status, you can check the session context or ask the user to confirm Feishu access is available.

## Create A Brief Document

Use the `message` tool to create Feishu documents with structured content:

```
message(
  action=send,
  channel=feishu,
  contentType=document,
  content='<title>项目名称 设计Brief</title><callout emoji="✅" background-color="light-green" border-color="green"><p><b>结论：</b>...</p></callout>...'
)
```

Rules:

- Feishu is the default main deliverable when available.
- Use structured blocks: `<callout>`, `<table>`, `<grid>`, `<checkbox>`, `<hr/>`.
- Keep raw transcripts, long strategy notes, and static JSON out of the main brief unless explicitly requested.
- If source material came from a Feishu document, create a separate output document unless the user explicitly asks to update the source.
- **CHECKPOINT**: Before writing to an existing Feishu document, ask for explicit user confirmation.

Markdown fallback is acceptable only when Feishu rich blocks fail, Feishu is unavailable, or the user explicitly asks for Markdown:

```
message(
  action=send,
  channel=feishu,
  contentType=markdown,
  content=$'# 项目名称 设计Brief\n\n## 1. 结论\n...'
)
```

## Compact XML Template

```xml
<title>[项目名称] 设计Brief</title>

<callout emoji="✅" background-color="light-green" border-color="green">
  <p><b>结论：</b>[任务类型 + 是否可进入下一步 + 最大缺口。控制在80字内。]</p>
</callout>

<h1>Brief总表</h1>
<table>
  <thead><tr><th background-color="light-gray">字段</th><th background-color="light-gray">结论</th></tr></thead>
  <tbody>
    <tr><td>设计任务类型</td><td>[包装/产品海报/年节海报/活动主K/详情页]</td></tr>
    <tr><td>产品/品牌/品类</td><td>[一句话]</td></tr>
    <tr><td>渠道/场景</td><td>[关键渠道和场景]</td></tr>
    <tr><td>目标客群</td><td>[谁买/谁用/核心动机]</td></tr>
    <tr><td>设计目标</td><td>[最重要目标]</td></tr>
    <tr><td>关键限制</td><td>[1-2个限制]</td></tr>
  </tbody>
</table>

<h1>卖点与证据</h1>
<table>
  <thead><tr><th background-color="light-gray">产品事实</th><th background-color="light-gray">用户利益</th><th background-color="light-gray">证据/限制</th></tr></thead>
  <tbody>
    <tr><td>[事实]</td><td>[用户利益/可表达卖点]</td><td>[证据或待确认]</td></tr>
  </tbody>
</table>

<h1>分支专项表</h1>
<table>
  <thead><tr><th background-color="light-gray">专项字段</th><th background-color="light-gray">结论</th><th background-color="light-gray">状态</th></tr></thead>
  <tbody>
    <tr><td>[根据路由填写]</td><td>[结论]</td><td>[明确/缺失/待确认]</td></tr>
  </tbody>
</table>

<h1>素材状态</h1>
<table>
  <thead><tr><th background-color="light-gray">素材</th><th background-color="light-gray">状态</th><th background-color="light-gray">下一步</th></tr></thead>
  <tbody>
    <tr><td>[素材]</td><td>[已提供/缺失/待确认]</td><td>[负责人+动作]</td></tr>
  </tbody>
</table>

<h1>下一步行动</h1>
<table>
  <thead><tr><th background-color="light-gray">任务</th><th background-color="light-gray">负责人</th><th background-color="light-gray">状态</th><th background-color="light-gray">用途</th></tr></thead>
  <tbody>
    <tr><td>[关键问题/待补资料]</td><td>[项目经理/客户/文案策划/设计师]</td><td>待处理</td><td>[影响什么判断]</td></tr>
  </tbody>
</table>
```

## Return To User

After publishing, confirm delivery with the message tool return value:

```text
已生成飞书云文档设计 Brief

这份文档是当前 Brief 协作源。请在文档内补全下一步行动后，再进入策略或设计阶段。
```

If publishing fails, check:
- Session has Feishu channel access
- `message` tool returned an error
- Content format is valid

**Critical Rule**: Do NOT just output a local file path or say "已发送" without actually calling the `message` tool. Only after the `message` tool returns successfully can you claim the brief has been delivered.
