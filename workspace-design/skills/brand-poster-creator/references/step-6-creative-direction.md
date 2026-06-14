# Step 6：创意方向

## 概述

本步骤负责基于已确认信息生成画面创意表达方案，让用户在 prompt 组装之前就能清晰理解最终海报的表达方式。这是 **prompt 之前的创意对齐步骤**。

---

## 6.1 输入来源

创意方向必须严格基于以下已确认信息生成：

- `brief.json` - 需求信息
- `copywriting.json` - 文案策略结果
- `distill_card.json` - 蒸馏卡数据（如有）
- `style_profile.json` - 风格提炼结果（如有）
- 已确认的素材信息（`brief.json.assets`）

---

## 6.2 生成方式

### 6.2.1 运行脚本生成创意表达草案

**必须**通过脚本生成创意表达草案，**禁止** main 直接手写最终版：

```bash
python3 {baseDir}/scripts/generate_creative_direction.py \
  --brief "[项目目录]/brief.json" \
  --copywriting "[项目目录]/copywriting.json" \
  --distill "[项目目录]/distill_card.json" \
  --style-profile "[项目目录]/style_profile.json" \
  --output "[项目目录]/creative_direction.json"
```

**注意**：
- `--distill` 为可选参数；有蒸馏卡时传入
- `--style-profile` 为可选参数；有参考图风格提炼结果时传入
- 脚本输出的是**创意表达草案**，用户确认后才能作为后续 prompt 组装输入

---

## 6.3 输出文件结构

### creative_direction.json 结构

```json
{
  "summary": "一句话总述整张海报要传达的核心表达",
  "scene_concept": "场景概念，说明画面发生在什么节奏/氛围/时刻里",
  "hero_focus": "谁是第一视觉主体，为什么它是主角",
  "supporting_elements": [
    "哪些元素负责烘托氛围",
    "哪些元素只做陪衬，不抢主视觉"
  ],
  "composition_plan": "构图关系说明，强调主体、文案、装饰、留白之间的关系",
  "text_visual_relationship": "文案如何嵌入画面，和视觉主元素如何互相支撑",
  "style_translation": "如果有参考图，说明这次会继承它的哪些风格语言，不继承哪些具体内容",
  "must_hit": [
    "这张图必须打中的表达要点 1",
    "这张图必须打中的表达要点 2"
  ],
  "must_avoid": [
    "这张图明确不要出现的表达偏差 1",
    "这张图明确不要出现的表达偏差 2"
  ]
}
```

### 必需字段

`creative_direction.json` 至少必须包含以下字段：
- `summary` - 核心表达总述
- `hero_focus` - 第一视觉主体
- `composition_plan` - 构图关系
- `text_visual_relationship` - 文案与画面关系
- `must_hit` - 必须打中的表达要点
- `must_avoid` - 必须避免的表达偏差

**缺任一项都不得进入 Step 6（prompt 组装）。**

---

## 6.4 给用户的展示话术

脚本成功产出 `creative_direction.json` 后，main 必须读取其中字段，并按以下格式展示给用户：

```markdown
🎬 **画面创意表达方案确认**

### 这张海报想表达什么
[summary]

### 画面会怎么呈现
- 场景概念：[scene_concept]
- 第一视觉主体：[hero_focus]
- 氛围陪衬元素：[supporting_elements]
- 构图关系：[composition_plan]
- 文案与画面的关系：[text_visual_relationship]
- 风格转译方式：[style_translation]

### 这张图必须打中的感觉
- [must_hit 1]
- [must_hit 2]

### 这张图明确不要走偏的方向
- [must_avoid 1]
- [must_avoid 2]

请确认：
- 回复「确认创意」→ 进入 prompt 组装
- 回复「修改创意：[具体要求]」→ 先调整创意表达方案
```

---

## 6.5 🔴 CHECKPOINT · STOP：创意方向双审门禁（新增 v3.1）

**未得到文案策划判断者 + 设计判断者双方确认前，禁止进入 Step 7（生图）。**

⚠️ **重要变更（v3.1）**：创意方向现在需要文案和设计双方审核，因为涉及两个专业维度。

---

### 6.5.1 为什么需要双审

创意方向包含两个专业维度：
- **文案维度**：核心表达、文案与画面关系、must_hit/must_avoid
- **设计维度**：场景概念、视觉主体、构图关系、风格转译

因此需要：
- 文案策划判断者确认创意表达准确
- 设计判断者确认视觉呈现可行

---

### 6.5.2 请求创意方向审批

展示创意方向后，**立即触发双审流程**：

```bash
# 请求创意方向双审
python3 {baseDir}/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "creative_direction_dual" \
  --artifact "creative_direction.json"
```

脚本会返回 JSON，包含两个审批者的艾特标签：
```json
{
  "milestone": "creative_direction_dual",
  "title": "创意方向确认",
  "reviewers": [
    {"name": "肖宁劼", "open_id": "ou_xxx", "role": "copywriter"},
    {"name": "林育丰", "open_id": "ou_yyy", "role": "designer"}
  ],
  "ai_driver": {"name": "涂是淦", "open_id": "ou_zzz"},
  "mention_tags": [
    "<at user_id=\"ou_xxx\">肖宁劼</at>",
    "<at user_id=\"ou_yyy\">林育丰</at>",
    "<at user_id=\"ou_zzz\">涂是淦</at>"
  ],
  "message": "<at user_id=\"ou_xxx\">肖宁劼</at> <at user_id=\"ou_yyy\">林育丰</at> 创意方向已生成，请审核确认",
  "note": "需要文案策划和设计双方都确认，或AI驱动者确认"
}
```

---

### 6.5.3 向用户发送审批请求

⚠️ **关键**：使用 send_approval_message.py 脚本直接发送飞书消息，完全绕过流式输出。

🔴 **强制方法**：使用脚本分两次发送（脚本会自动获取群聊 ID）

**第1次调用脚本**（发送艾特消息）：
```bash
python3 {baseDir}/scripts/send_approval_message.py \
  --content "{使用脚本返回的 .message 字段}"
```

**第2次调用脚本**（发送表格）：
```bash
python3 {baseDir}/scripts/send_approval_message.py \
  --content "| 维度 | 内容 |
|------|------|
| 这张海报想表达 | [从 creative_direction.json 提取] |
| 场景概念 | [从 creative_direction.json 提取] |
| 视觉主体 | [从 creative_direction.json 提取] |
| 必须打中 | [从 creative_direction.json 提取] |
| 必须避免 | [从 creative_direction.json 提取] |

请回复：
- 「通过」→ 进入生图阶段
- 「修改：具体要求」→ 调整创意方向
- 「拒绝：原因」→ 终止项目"
```

**实际示例**：

第1次：
```bash
MESSAGE='<at user_id="ou_b5d2c0a6787a3acc8bc889b15280ae11">肖宁劼</at> <at user_id="ou_2253f3cfcdb6e0ae8707cee2ea10a57c">林育丰</at> 创意方向已生成，请审核确认'

python3 $WORKSPACE_DIR/workspace-design/skills/brand-poster-creator/scripts/send_approval_message.py \
  --content "$MESSAGE"
```

第2次：
```bash
TABLE='| 维度 | 内容 |
|------|------|
| 这张海报想表达 | 验证流程闭环 |
| 场景概念 | 中性、专业、干净的流程视觉 |
| 视觉主体 | 流程闭环图形 |
| 必须打中 | 流程清晰、专业可信 |
| 必须避免 | 营销化、过度装饰 |

请回复：
- 「通过」→ 进入生图阶段
- 「修改：具体要求」→ 调整创意方向
- 「拒绝：原因」→ 终止项目'

python3 $WORKSPACE_DIR/workspace-design/skills/brand-poster-creator/scripts/send_approval_message.py \
  --content "$TABLE"
```

🔴 **关键要点**：
1. **必须使用脚本发送**（不是 message 工具，不是直接回复）
2. **分两次调用脚本**（第1次艾特，第2次表格）
3. **脚本会自动获取群聊 ID**（不需要传 --chat-id 参数）
4. **使用 exec 工具执行**（确保脚本真正执行）

🔴 **严格禁止**：
- ❌ 直接回复给用户（会触发流式输出）
- ❌ 使用 message 工具（可能仍然有系统行为）
- ❌ 不调用脚本就发送审批消息

🔍 **技术原理**：
- Python 脚本 → 直接调用飞书 API
- 完全绕过 Claude Code 的输出机制
- 飞书 API 发送普通消息 → 艾特标签生效
- 脚本自动获取群聊 ID → 简化使用

---

### 6.5.4 记录审批响应

**等待审批响应**。收到回复后，记录审批结果：

```bash
# 记录审批响应
python3 {baseDir}/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "creative_direction_dual" \
  --decision "approved" \
  --feedback "创意方向符合预期" \
  --responder-open-id "[回复者的 open_id]"
```

**审批通过条件**（满足任一即可）：
- ✅ 文案策划判断者 + 设计判断者都回复"通过"
- ✅ AI驱动者回复"通过"（拥有最高决策权，可代替任何审批者）

---

### 6.5.5 处理不同的审批结果

#### approved（通过）

创意方向审批通过，继续进入 Step 7 生图。

向用户确认：
```markdown
✅ 创意方向审批通过，进入生图阶段
```

#### revision_needed（需要修改）

1. **记录反馈意见**到 `project_grading.json`
2. **根据反馈修改 `creative_direction.json`**
3. **重新展示给用户**
4. **再次请求审批**（回到 6.5.2）

#### rejected（拒绝）

1. **记录拒绝原因**
2. **终止项目**
3. **生成复盘报告**

---

### 6.5.6 审批门禁规则

**未通过创意方向审批前，禁止进入 Step 7（生图）。**

### 确认条件

- `project_grading.json` 中 `creative_direction_dual` 节点的 `status` 必须为 `approved`
- 或用户在超时后选择继续（仅B级项目）

### 禁止行为

- ❌ **自动假设用户已确认**
- ❌ **沉默视为同意**
- ❌ **绕过审批流程直接进入生图**
- ❌ **只收到一方确认就继续**（除非是AI驱动者确认）
- ❌ **在审批状态为 `waiting` 或 `pending` 时继续执行后续步骤**

---

### 6.5.7 AI驱动者特殊权限说明

**AI驱动者（项目发起人）拥有所有审批节点的最高决策权。**

原因：
- AI驱动者可能已在线下与文案/设计判断者沟通确认
- 回到线上直接反馈结果，无需等待双方在线回复

因此：
- 创意方向审批会同时艾特文案判断者、设计判断者和AI驱动者
- AI驱动者回复"通过"即可代表双方确认
- 这适用于所有审批节点（文案审批、创意方向、设计审批等）

---

## 6.6 用户确认后的文件处理

### 情况 A：回复「确认创意」

- 保留当前 `creative_direction.json`
- 进入 Step 7（prompt 组装）

### 情况 B：回复「修改创意：[具体要求]」

1. 先根据要求更新 `creative_direction.json`
2. 再重新展示给用户确认
3. 等待用户再次确认后才进入下一步

**未完成创意确认前，不得进入 prompt 组装。**

---

## 6.7 关键规则

### ✅ 必须遵守

1. **这是 prompt 之前的创意对齐步骤**：目标是先确认"这张图怎么表达"，不是直接展示 prompt 细节
2. **方案必须严格基于已确认信息生成**：不得新增用户未确认的产品卖点、人物设定、节庆道具或剧情
3. **若有参考图，只能转译其视觉语言**：不得把原参考图中的具体场景、天气、剧情直接搬过来
4. **若用户提出创意修正**：必须先更新 `creative_direction.json`，再进入下一步
5. **必需字段缺一不可**：至少包含 `summary`、`hero_focus`、`composition_plan`、`text_visual_relationship`、`must_hit`、`must_avoid`

### ❌ 禁止行为

1. **不得跳过脚本手写创意方向**
2. **不得新增用户未确认的内容**
3. **不得把参考图的具体场景/天气/剧情继承到创意中**
4. **不得在用户未确认时进入 prompt 组装**
5. **不得缺少必需字段**

---

## 6.8 参考图风格转译规则

如果有参考图，`style_translation` 字段必须明确说明：

### 允许继承

- 配色关系（暖调/冷调/高饱和/低饱和）
- 材质语言（纸感/油画感/扁平插画/厚涂）
- 光感与空间（通透/柔光/平光/强对比）
- 装饰密度（留白多/元素满/边角点缀）
- 情绪（热闹/温柔/松弛/隆重）

### 不允许默认继承

- 季节（冬天/夏天/春天/秋天）
- 天气（雪地/雨天/晴天）
- 地貌（沙漠/海边/森林）
- 场景地点（室内/户外/特定场所）
- 节庆道具（圣诞树/月饼/粽子等与 brief 节点不符的）
- 角色剧情动作（人物姿态/表情/服装）

### 示例

**正确**：
```json
{
  "style_translation": "继承参考图的暖红色调、手绘插画感、柔和光感和节庆氛围密度；不继承参考图中的冬季雪地场景、圣诞装饰和原始人物角色，改为春节氛围和品牌 IP"
}
```

**错误**：
```json
{
  "style_translation": "完全按照参考图风格，保持雪地场景和圣诞氛围"
}
```

---

## 6.9 创意表达方案示例

### 示例 1：春节产品海报

```json
{
  "summary": "用温暖手绘插画风格，展现小白心里软 IP 在春节氛围中送上团圆礼盒的温情时刻",
  "scene_concept": "节庆氛围浓厚但不喧宾夺主，背景是明快热闹的春节装饰，主角是品牌 IP 和产品礼盒",
  "hero_focus": "小白心里软 IP 是第一视觉主体，占据画面中央偏上位置，产品礼盒作为第二主角紧密关联",
  "supporting_elements": [
    "春节装饰（灯笼、彩绳、红包）负责烘托节庆氛围",
    "背景纹样（祥云、花卉）只做陪衬，不抢主视觉"
  ],
  "composition_plan": "中央主视觉区为 IP + 产品，顶部为主标题区，底部为副标题和品牌信息区，左右两侧留白适中，前景有装饰点缀",
  "text_visual_relationship": "主标题「把团圆装进礼盒」位于顶部，与 IP 手持礼盒的动作形成呼应；副标题「新年·心意到家」位于底部，与产品形成闭合",
  "style_translation": "继承参考图的暖红色调、手绘插画感、柔和光感和节庆氛围密度；不继承参考图中的冬季雪地场景、圣诞装饰，改为春节氛围",
  "must_hit": [
    "温暖的春节团圆感",
    "品牌 IP 的亲和力",
    "产品礼盒的精致感"
  ],
  "must_avoid": [
    "低幼卡通感",
    "过于商业化的促销氛围",
    "冬季/圣诞元素"
  ]
}
```

---

## 6.10 与 Step 6（风格提炼）的关系

- 如果 Step 6 已完成风格提炼，`style_translation` 字段必须基于 `style_profile.json` 中的风格关键词
- 如果没有参考图，`style_translation` 字段可省略或填写"无参考图，使用品牌标准视觉语言"

---

## 完成后执行下一步

创意方向确认完成后，进入 **Step 7：Prompt 组装**。
