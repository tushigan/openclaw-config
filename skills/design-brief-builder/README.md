# Design Brief Builder - OpenClaw 版本

## 简介

这是一个设计 Brief 整理 skill，用于把散乱的项目信息（聊天记录、飞书文档、口头需求、产品事实、渠道客群、素材状态等）整理成标准设计 Brief，并自动路由到：

- **包装 Brief**：包材、盒型、刀模、货架陈列等
- **海报 Brief**：产品海报、年节海报、活动主 K
- **详情页 Brief**：电商详情页、销售页、转化页

## 安装位置

此 skill 已安装到虾指挥（main agent）的 workspace-local skills 目录：

```
/Users/a123/.openclaw/workspace/skills/design-brief-builder/
```

**独占性使用**：此 skill 仅在虾指挥（main agent）的 workspace 中可用，其他 agent 无法访问。

## 使用方式

在虾指挥的飞书对话或命令行中直接提出设计 Brief 整理需求，skill 会自动触发。

### 触发条件

当你的需求包含以下关键词或场景时，虾指挥会自动调用此 skill：

- 整理设计 Brief / 做个 Brief / 整理项目信息
- 包装设计 Brief / 海报 Brief / 详情页 Brief
- 提供了散乱的产品信息、渠道客群、素材状态等
- 飞书文档中的项目信息需要结构化

### 示例对话

#### 示例 1：包装 Brief

```
用户：把下面聊天记录整理成标准设计Brief，并输出飞书云文档：
产品是帕玛森芝士凤梨酥，卖场长销单盒装，目标25-40岁女性。
徐闻凤梨，馅料中凤梨>=80%，进口帕玛森芝士干酪粉，安佳黄油>=6.4%。
有品牌色彩体系，包装要突出购买理由。
配料表完整，但包装结构、刀模、竞品和货架照片还没给。

虾指挥：（调用 design-brief-builder skill）
✅ 已生成飞书云文档设计 Brief

这份文档是当前 Brief 协作源。请在文档内补全下一步行动后，再进入策略或设计阶段。
```

#### 示例 2：产品海报 Brief

```
用户：帮我整理一个产品海报Brief。
产品是低糖黑芝麻丸，准备发小红书和朋友圈，重点讲低糖、独立小袋、办公室下午茶不负担。
已有产品图和品牌logo，没有活动机制，想要一个竖版产品海报。

虾指挥：（调用 design-brief-builder skill）
✅ 已生成飞书云文档设计 Brief
```

#### 示例 3：详情页 Brief

```
用户：帮我整理电商详情页Brief。
产品是儿童奶酪棒，准备上抖音和天猫，首屏要讲高钙和新西兰全脂乳粉，
页面要解决家长担心添加剂、甜度、适合年龄和冷链的问题。
已有包装图、产品图、检测报告截图，缺少场景图和用户评价。

虾指挥：（调用 design-brief-builder skill）
✅ 已生成飞书云文档设计 Brief
```

## 核心特性

### 1. 自动路由

根据任务关键词自动判断是包装、海报还是详情页：

| 关键词 | 路由 |
|-------|------|
| 包装、包材、盒型、袋型、瓶身、罐体、礼盒、刀模、货架、陈列、SKU、包装升级 | `包装` |
| 海报、主图、主视觉、KV、活动图、促销图、节日图、年节海报、朋友圈图、门店物料 | `海报` |
| 详情页、销售页、长图、电商页、首屏、转化、模块、卖点证据链、用户疑虑 | `详情页` |

### 2. 产品事实驱动

从产品事实库推导卖点，避免无依据的创意：

```
产品事实 → 用户利益 → 可表达卖点 → 证据/限制
```

### 3. 飞书云文档交付

默认输出为飞书云文档（结构化表格 + 标注），支持团队协作。包含：

- 结论（任务类型 + 是否可进入下一步 + 最大缺口）
- Brief 总表
- 卖点与证据
- 分支专项表（根据路由动态生成）
- 素材状态
- 下一步行动

### 4. 状态标注

每个字段标注为：`明确`、`推测`、`缺失`、`待确认`

### 5. 问题门控

只在关键信息缺失时提问（最多 3 个高价值问题），避免打断流程。

## 文件结构

```
design-brief-builder/
├── SKILL.md                      # Skill 工作流定义
├── README.md                     # 本文档
├── test-prompts.json             # 测试用例
└── references/
    ├── branch-fields.md          # 包装/海报/详情页分支字段定义
    └── feishu-delivery.md        # 飞书集成说明（已适配 OpenClaw）
```

## 与 OpenClaw 的集成

### 飞书工具调用

已将原 Codex 的 `lark-cli` 命令适配为 OpenClaw 的 `message` 工具：

```javascript
// 创建飞书云文档
message(
  action=send,
  channel=feishu,
  contentType=document,
  content='<title>项目名称 设计Brief</title>...'
)
```

### 交付规范

符合虾指挥的交付标准（AGENTS.md 2.1 节）：

- ✅ 调用 `message` 工具真实发送
- ✅ 等待工具返回成功
- ✅ 确认交付（不只回本地路径）

### 协作链路

Brief 整理完成后，可以无缝进入下游环节：

```
design-brief-builder → strategy (策略) → design (生图) → copywriter (文案)
```

## 注意事项

1. **独占使用**：此 skill 仅在虾指挥（main agent）workspace 中可用
2. **飞书优先**：默认输出飞书云文档，Markdown/JSON 仅作 fallback
3. **不发明事实**：所有卖点必须有产品事实依据，不确定的标记为"待确认"
4. **分支专项**：包装/海报/详情页有各自的专项字段，不混用
5. **确认机制**：写入已有飞书文档前会先确认

## 测试验证

可以使用 `test-prompts.json` 中的测试用例验证 skill 是否正常工作：

```bash
# 在虾指挥的飞书对话中粘贴测试 prompt
cat /Users/a123/.openclaw/workspace/skills/design-brief-builder/test-prompts.json
```

## 版本历史

- **v1.0.0** (2026-06-08): 从 Codex plugin 转换为 OpenClaw skill
  - 移除 Codex 特有的 `.codex-plugin/` 和 `agents/openai.yaml`
  - 适配 OpenClaw 的 `message` 工具（替换 `lark-cli`）
  - 安装到虾指挥 workspace-local skills 目录
  - 验证与 OpenClaw 工具链的兼容性

## 维护

如需修改或优化此 skill，可以使用 OpenClaw 的 darwin-skill 进行自动优化：

```bash
openclaw skills optimize design-brief-builder
```

或手动编辑 `SKILL.md` 和 reference 文件。
