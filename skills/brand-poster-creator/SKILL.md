---
name: brand-poster-creator
version: 2.2
description: "品牌海报全流程生成技能。从需求收集、版式锁定、文案策划、生图到交付清理的全链路协调器。触发词：品牌海报、海报生成、做张海报、节日海报、产品海报、春节海报、营销海报"
metadata:
  openclaw:
    requires:
      bins:
        - python3
    emoji: "🎨"
---

# Brand Poster Creator - 品牌海报全流程协调器

用于 `main` 子代理统一调度品牌海报从需求到交付的全流程。

## 触发词

用户说出以下任意内容时激活本技能：
- 品牌海报
- 海报生成 / 做张海报
- 节日海报 / 春节海报 / 中秋海报等
- 产品海报 / 产品 KV
- 营销海报 / 推广海报

## 全局流程

``` 
触发即自动立项：先创建项目目录 + project_state.json + intake_manifest.json + audit_log.jsonl
Step 1：飞书对话卡片 → 用户填写需求
Step 2：检查蒸馏卡 → 有则读取版式坐标 → 无则标记降级模式
Step 2.5：飞书云盘品牌素材检索 → 搜索品牌文件夹 → 获取资产图 → 用户确认
Step 3：信息缺口检查 → 主动追问用户
Step 4：派发 strategy subagent → 完成文案策划
Step 5：回收文案 + 骨架图+坐标表 → 飞书对话卡片展示 → 用户确认/修改
Step 5.5：参考图风格提炼 → 输出 style_profile.json（有参考图时执行）
Step 5.8：基于已确认信息生成画面创意表达方案 → 用户确认/修改
Step 6：调用 prompt-assembler 组装完整 prompt
Step 7：派发 design subagent → 4K 分辨率生图
Step 8：发送成品图 → 用户确认
Step 9：询问是否完成 → 是则清理项目目录中间文件
```

## 项目状态与续跑机制

每个项目目录下必须维护以下状态文件：

```text
project_state.json          # 统一主状态
intake_manifest.json        # 立项/需求收集记录
assets_manifest.json        # 品牌素材检索结果
creative_direction_manifest.json
prompt_manifest.json
generation_manifest.json    # 当前复用 generation_result.json 结构
delivery_manifest.json
audit_log.jsonl             # append-only 审计日志
```

### 主状态文件约定

`project_state.json` 至少包含：
- `current_stage`
- `stage_status`
- `workflow_flags`
- `attempts`
- `resume`
- `last_error_stage`
- `last_error`
- `artifacts`

### 阶段枚举

统一使用以下阶段名：
- `intake`
- `distill`
- `assets`
- `gap_check`
- `copywriting`
- `style_profile`
- `creative_direction`
- `prompt`
- `generation`
- `delivery`
- `cleanup`

### 续跑入口

必须同时支持：

1. **自动续跑**：
```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/project_manager.py \
  reconcile \
  --project-dir "[项目目录]"
```

2. **人工指定阶段强制续跑**：
```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/project_manager.py \
  force-resume \
  --project-dir "[项目目录]" \
  --stage generation \
  --note "用户要求从生图重新开始"
```

### 用户确认落盘规则

以下确认动作不能只停留在聊天里，必须写回对应 manifest 与 `project_state.json`：
- 素材确认
- 文案确认
- 创意确认
- 定稿确认

### 通用阶段落盘入口

如果某一阶段暂时没有独立脚本，也必须通过统一入口写状态：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/project_manager.py \
  stage \
  --project-dir "[项目目录]" \
  --stage copywriting \
  --action complete \
  --reason "文案已确认" \
  --manifest-json '{"status":"confirmed","user_confirmed":true}' \
  --flags-json '{"copywriting_ready":true,"copy_confirmed":true}' \
  --files-json '["copywriting.json"]'
```

适用场景：
- `distill`：蒸馏卡已读取或确认 fallback
- `gap_check`：缺口检查完成
- `copywriting`：文案确认完成
- `style_profile`：风格提炼完成
- `cleanup`：清理完成

## 流程状态可视化

每次回复必须附带当前阶段：

```markdown
📍 **当前阶段**：Step X（阶段名称）
📍 **已完成**：Step 1 → Step 2 → ...
📍 **下一阶段**：Step Y（阶段名称）- 需用户确认后进入
```

---

## Step 1：飞书对话卡片收集需求

激活技能后，立即向用户发送需求收集卡片：

```markdown
🎨 **品牌海报需求收集**

请提供以下信息：

| 维度 | 说明 | 示例 |
|------|------|------|
| **海报目的** | 产品推广 / 品牌发声 / 年节海报 | 产品推广 |
| **品牌名称** | | 小白心里软 |
| **行业/品类** | | 烘焙食品 |
| **营销节点** | 春节/中秋/618/品牌日等 | 春节 |
| **尺寸比例** | 2:3(手机海报) / 9:16(短视频) / 1:1(朋友圈) / 16:9(Banner) | 2:3 |
| **必露元素** | Logo/IP/产品/文字等 | Logo + IP + 标题文字 |
| **画面主角** | 谁是画面绝对主角？谁只是陪衬？ | IP 是主角，节日元素只陪衬 |
| **禁忌** | 不要的颜色/风格/元素 | 不要低幼卡通感 |
| **是否有蒸馏卡 ID** | 是 → 填写 ID，否 → 留空 | POSTER-DISTILL-P-012 |
| **风格参考** | 上传参考图 或 文字描述 | 暖红色调春节氛围 |

**如果是产品推广类海报**，还需额外提供：
- 产品名称
- 产品卖点（文字描述）
- 产品图片（上传）

请逐项回复，或一次性提供完整信息。
```

收到用户回复后，将所有信息写入项目目录的 `brief.json` 文件，格式如下：

```json
{
  "task_id": "BP-YYYYMMDD-序号",
  "type": "节日海报 | 产品推广 | 品牌发声",
  "brand_name": "品牌名",
  "industry": "行业",
  "festival": "营销节点",
  "ratio": "比例",
  "must_include": ["Logo", "IP"],
  "hero_priority": {
    "hero_1": "绝对主角（如 IP 角色）",
    "hero_2": "陪衬元素（如节日氛围元素）",
    "forbidden_hero": "禁止作为主视觉出现的元素"
  },
  "taboos": "用户禁忌",
  "distill_card_id": "蒸馏卡ID 或空",
  "style_note": "风格参考描述",
  "assets": {
    "style_refs": ["images/style_ref_1.jpg"],
    "logo": "images/logo.jpg",
    "ip": "images/ip.jpg",
    "product": "images/product.jpg"
  }
}
```

### 项目目录结构

每个任务创建独立目录：

```
/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/
├── brief.json              # 需求信息
├── distill_card.json       # 蒸馏卡数据（如有）
├── copywriting.json        # 文案策划结果
├── prompt_draft.md         # 组装好的 prompt
├── images/                 # 中间产物和最终海报
│   ├── skeleton.png        # 骨架图（本地副本）
│   ├── style_ref.png       # 风格参考图
│   ├── product.png         # 产品图
│   ├── logo.png            # Logo
│   └── final_poster.png    # 最终海报
└── cleanup_manifest.json   # 待清理文件清单
```

**任务 ID 生成规则**：`BP-YYYYMMDD-序号`，如 `BP-20260505-001`

### 素材文件处理

用户上传的所有图片文件，统一复制到 `images/` 目录下，使用标准命名：
- `images/style_ref_N.png`（风格参考图，N 从 1 开始递增）
- `images/product.png`（产品图）
- `images/logo.png`（Logo）

---

## Step 2：检查蒸馏卡

读取 `brief.json` 中的 `蒸馏卡 ID` 字段：

### 有蒸馏卡 ID

1. 运行脚本处理蒸馏卡：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/process_distill_card.py \
  --project-dir "[项目目录绝对路径]"
```

2. 脚本自动完成：
   - 读取对应蒸馏卡 JSON 文件：`/Users/a123/.openclaw/workspace/skills/brand-poster-distiller/cards/[ID].json`
   - 将完整 JSON 数据写入 `distill_card.json`
   - 提取 `layout_analysis.elements` 作为版式坐标数据
   - 提取 `layout_analysis.copy_planning_guide` 作为文案策划指南
   - 提取 `layout_analysis.negative_constraints` 作为负面约束
   - 将骨架图复制到 `images/skeleton.png`：优先使用 `skeleton_png` 字段（PNG），若为空则回退 `skeleton_image` 字段（SVG）
   - 写入 `distill_manifest.json`、`project_state.json`、`audit_log.jsonl`

### 无蒸馏卡 ID

在 `brief.json` 中标记 `"distill_mode": "fallback"`，后续进入降级组装流程（见 prompt-assembler.md 第六节）。

---

## Step 2.5：飞书云盘品牌素材检索

根据 `brief.json` 中的 `brand_name`，自动在指定飞书云盘文件夹中搜索品牌子文件夹，获取 Logo、IP 等品牌资产图。

**指定云盘链接**：`https://l5rd0uzm0z.feishu.cn/drive/folder/HrvvfbL8clefhAdSLtUcb7G3nYg`
**folder_token**：`HrvvfbL8clefhAdSLtUcb7G3nYg`

### 执行流程

1. 运行 `fetch_brand_assets.py` 脚本检索品牌素材：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/fetch_brand_assets.py \
  --brand "[brief.json 中的 brand_name]" \
  --folder-token "HrvvfbL8clefhAdSLtUcb7G3nYg" \
  --project-dir "[项目目录绝对路径]" \
  --verbose
```

2. 脚本自动完成：
   - 获取飞书 tenant_access_token
   - 列出云盘根文件夹下的子文件夹
   - 用品牌名模糊匹配子文件夹名称
   - 找到品牌文件夹后，列出其中的图片文件
   - 下载图片到项目目录 `images/` 下（按类型智能命名）
   - 更新 `brief.json` 的 `assets` 字段

3. 根据脚本输出结果，分三种情况处理：

### 情况 A：找到品牌素材（status = "success"）

通过飞书发送找到的素材图给用户确认：

```markdown
📦 **品牌素材检索结果**

根据品牌「[品牌名]」在云盘中找到以下素材：

| 素材类型 | 原始文件名 | 本地路径 | 状态 |
|---------|-----------|---------|------|
| Logo | 品牌Logo.png | images/logo.png | ✅ 已获取 |
| IP 形象 | IP形象.png | images/ip.png | ✅ 已获取 |

[发送素材预览图]

请确认：
- 「确认素材」→ 素材齐全，进入下一步
- 「补充图片」→ 请上传额外的参考图/素材
- 「替换 [类型]」→ 请上传替换该类型的素材
```

### 情况 B：未找到品牌文件夹或文件夹为空（status = "not_found"）

```markdown
📦 **品牌素材检索结果**

⚠️ 未在云盘中找到品牌「[品牌名]」的素材文件夹。

将在下一步信息缺口检查中逐项确认所需素材。你也可以现在直接上传品牌 Logo、IP 形象等素材。
```

跳过 Step 2.5，直接进入 Step 3。

### 情况 C：API 调用失败（status = "error"）

```markdown
📦 **品牌素材检索结果**

❌ 云盘检索失败：[错误信息]

将在下一步信息缺口检查中逐项确认所需素材。
```

跳过 Step 2.5，直接进入 Step 3。不阻断主流程。

### 文件名智能分类规则

脚本根据飞书文件名中的关键词自动归类：

| 素材类型 | 匹配关键词 | 保存文件名 |
|---------|-----------|-----------|
| Logo | logo / Logo / LOGO / 标志 / 商标 | `logo.png` |
| IP 形象 | ip / IP / 形象 / 角色 / 吉祥物 | `ip.png` |
| 产品图 | 产品 / product / 商品 | `product.png` |
| 其他 | 以上均不匹配 | `brand_asset_1.png`、`brand_asset_2.png`... |

同类型多文件时自动追加序号（如 `logo_2.png`、`ip_2.png`）。

### brief.json assets 字段更新

Step 2.5 完成后，`brief.json` 的 `assets` 字段会被脚本自动更新：

```json
{
  "assets": {
    "style_refs": [],
    "logo": "images/logo.png",
    "ip": "images/ip.png",
    "product": "images/product.png",
    "brand_assets": ["images/brand_asset_1.png"],
    "source": "feishu_drive"
  }
}
```

新增字段说明：
- `brand_assets`：无法归入 logo/ip/product 的其他品牌素材路径数组
- `source`：素材来源标记，`"feishu_drive"` 表示来自云盘自动检索，区别于用户手动上传

---

## Step 3：信息缺口检查与追问

在派发文案策划之前，先运行缺口检查脚本：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/check_brief_gaps.py \
  --project-dir "[项目目录绝对路径]"
```

脚本会自动：
- 检查 `brief.json` 的基础字段是否完整
- 检查 `assets.logo`、`assets.product`、`assets.style_refs` 指向的文件是否真实存在
- 对“产品推广/产品海报”类任务额外检查产品名称、产品卖点、产品图
- 输出缺口清单并写入 `gap_check_manifest.json`、`project_state.json`、`audit_log.jsonl`

检查基准如下：

| 必填项 | 海报目的 = 产品推广 | 海报目的 = 品牌发声/年节海报 |
|--------|-------------------|--------------------------|
| 品牌名称 | 必填 | 必填 |
| 营销节点 | 必填 | 必填 |
| 尺寸比例 | 必填 | 必填 |
| Logo | 必填 | 必填 |
| 产品图 | 必填 | 非必填 |
| 产品卖点 | 必填 | 非必填 |
| 风格参考 | 图片或文字 | 图片或文字 |

**Step 2.5 已获取的素材视为已填补**：如果 `brief.json` 的 `assets` 中已有 `logo`、`ip`、`product` 等字段且文件存在，则不再将对应项标记为缺口。仅当 Step 2.5 未找到素材、用户确认后仍缺少，或用户主动替换时，才在此步骤追问。

**发现缺口时主动向用户索要**，不要自行脑补。

---

## Step 4：派发 strategy subagent 完成文案策划

将以下信息组装成 task，派发 `strategy` 子代理：

```json
{
  "runtime": "subagent",
  "agentId": "strategy",
  "task": "海报文案策划任务（见下方模板）",
  "mode": "run",
  "timeoutSeconds": 600,
  "runTimeoutSeconds": 600,
  "lightContext": true,
  "thinking": "low",
  "model": ""
}
```

**spawn 参数约束（严格遵守，避免重试浪费）：**

| 参数 | 规则 | 说明 |
|------|------|------|
| `thinking` | 只能填 `"low"` / `"medium"` / `"high"` / `"adaptive"` 之一 | **绝对禁止**把思考内容写进此字段，否则报 `Invalid thinking level` 错误 |
| `model` | 留空 `""` 或填白名单内模型 | 白名单：`huoshan/kimi-k2.5`、`huoshan/kimi-k2.6`、`newapi_channel_conn/gpt-5.4`、`newapi_channel_conn/gpt-5.5`、`zhichuang/claude-opus-4-6`。留空则由 strategy agent 使用自身默认模型。**禁止**使用非白名单 provider（如 `aliyun-bailian/kimi-k2.5`） |
| `attachments` | **不要传** | 附件通道未开启（`sessions_spawn.attachments.enabled` 默认 false），传 attachments 会报 `forbidden` 错误。改为在 task 描述中指定文件绝对路径，让子 agent 自行读取 |

### 给 strategy 的任务描述模板

```
你是品牌文案策划专家，需要为以下海报策划文案。

**先读取以下项目文件获取完整上下文，不要凭空编造：**
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/brief.json
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copy_brief_for_strategy.json（如存在）

## 任务信息
- 海报目的：[产品推广 / 品牌发声 / 年节海报]
- 品牌：[品牌名]
- 行业：[行业]
- 营销节点：[节点]

## 版式约束（来自蒸馏卡）
[如果有蒸馏卡，将 copy_planning_guide 完整内容附在这里]
[每个文案区域的类型、排版方向、尺寸占比、字数建议]

## 品牌信息
- 必露元素：[清单]
- 禁忌：[清单]

## 产品信息（如适用）
- 产品名：[产品名]
- 卖点：[卖点列表]

## 输出要求
按蒸馏卡的文案区域逐一策划，每个区域输出：
1. 文案内容（具体中文文字）
2. 对应蒸馏卡元素 ID

将结果写入：/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copywriting.json

格式：
{
  "el-5": { "文案": "把团圆装进礼盒", "字体风格": "大气端庄" },
  "el-7": { "文案": "新年·心意到家", "字体风格": "细体" }
}

完成后回传简短摘要：你采用的文案策略 + 文件是否已成功写入。
```

### 文案结果统一落盘

strategy 子代理写完 `copywriting.json` 后，main 必须继续运行：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/process_copywriting.py \
  --project-dir "[项目目录绝对路径]"
```

脚本会自动：
- 校验 `copywriting.json` 是否存在且结构有效
- 规范化每个区域的 `文案` / `字体风格` 字段
- 写入 `copywriting_manifest.json`、`project_state.json`、`audit_log.jsonl`
- 将阶段推进到 `style_profile` / `creative_direction` 前的可续跑状态

---

## Step 5：文案 + 版式确认

回收 strategy 产出的文案，结合蒸馏卡的版式数据，以飞书对话卡片形式展示给用户确认：

```markdown
📋 **海报文案与版式确认**

### 版式骨架图
[发送骨架图图片]

### 版式坐标与文案对照表

| 区域 | 类型 | 位置坐标 | 排版方向 | 策划文案 |
|------|------|---------|---------|---------|
| 主标题区 | title | x:5% y:4% 90%×22% | 横排 | 把团圆装进礼盒 |
| 副标题区 | subtitle | x:22% y:26% 56%×4% | 横排 | 新年·心意到家 |
| 左侧竖排 | body_text | x:2% y:42% 5%×40% | 竖排 | 五谷为养 匠心烘焙 |
| 右侧竖排 | body_text | x:93% y:42% 5%×40% | 竖排 | 送礼自用 皆是心意 |
| 底部节日 | subtitle | x:20% y:92% 60%×5% | 横排 | 新春佳节 万家团圆 |
| 底部说明 | body_text | x:8% y:97% 84%×3% | 横排 | 小白心里软·手工烘焙 |

### 参考素材
- [ ] 版式骨架图（已锁定）
- [ ] 风格参考图（已上传 N 张）
- [ ] 产品图（已上传）
- [ ] Logo（已上传）

请确认：
- 回复「确认文案」→ 进入生图阶段
- 回复「修改 [区域] → [新文案]」→ 调整对应区域
```

### 用户确认后的文件处理

- 回复「确认文案」：`copywriting.json` 保留并进入后续风格提炼 / 创意表达
- 回复「修改文案：[具体要求]」：更新文案后重新运行 `process_copywriting.py`
- 文案阶段结束后必须先落盘，再进入下一步

---

## Step 5.5：参考图风格提炼

**条件**：用户提供了风格参考图时执行此步骤。无参考图时跳过。

### 操作

1. 读取风格参考图（`brief.json` → `assets.style_refs`）
2. 先完成风格分析并产出 `style_profile.json`
3. 再运行统一落盘脚本：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/process_style_profile.py \
  --project-dir "[项目目录绝对路径]"
```

脚本会自动：
- 检查 `brief.json` 与 `assets.style_refs` 中的参考图是否真实存在
- 无参考图时将 `style_profile` 阶段标记为 `skipped`
- 有参考图时校验 `style_profile.json` 的结构是否完整
- 写入 `style_profile_manifest.json`、`project_state.json`、`audit_log.jsonl`

### style_profile.json 结构

```json
{
  "overall_mood": "整体气质一句话（如：明快热闹、节庆感强）",
  "background": "背景区域的风格描述（如：明快热闹、色彩鲜活的背景，带一点手绘插画感和民俗氛围）",
  "decorative": "装饰区域的风格描述（如：节庆氛围装饰如粽叶彩绳小灯笼，风格与参考图一致，不喧宾夺主）",
  "main_visual_style": "主视觉的风格描述（如：手绘插画风格，色彩饱满柔和）",
  "color": ["色彩关键词1", "色彩关键词2"],
  "mood": ["情绪关键词1", "情绪关键词2"],
  "material": ["材质关键词1", "材质关键词2"],
  "avoid": ["需避免的风格关键词1", "需避免的风格关键词2"],
  "content_do_not_inherit": ["不得从参考图继承的具体内容语义，如雪地、冬天、圣诞装饰"],
  "season_override_hint": "若 brief 营销节点与参考图季节冲突，以 brief 为准，只保留风格不保留季节场景。"
}
```

### 提炼维度（至少覆盖）

| 维度 | 示例关键词 |
|------|-----------|
| 色彩关系 | 低饱和/高饱和/清亮/厚重/暖调/冷调 |
| 画面气质 | 童趣/节庆/梦幻/手作/插画感/复古/潮流 |
| 材质语言 | 纸感/油画感/扁平插画/厚涂/颗粒/丝网印刷感 |
| 光感与空间 | 通透/柔光/平光/强对比/层次浓/空间压扁 |
| 装饰密度 | 留白多/元素满/边角点缀/中央聚焦/背景丰富 |
| 情绪 | 热闹/温柔/松弛/隆重/轻快/治愈 |
| 内容禁继承 | 冬天/雪地/圣诞/冰雪/厚冬装/原参考图剧情 |

### 关键规则

- **提炼结果必须来自参考图，不能脑补。** 任何风格描述都必须能在参考图中找到视觉依据。
- **参考图只负责回答“怎么画”，不负责回答“画什么”。** 主题、季节、场景、叙事、营销节点必须以 `brief.json` 为准。
- 无参考图时跳过此步骤，`process_style_profile.py` 应将该阶段标记为 `skipped`，`assemble_prompt.py` 使用中性回退（不带风格偏向的默认描述）。
- `avoid` 字段用于明确排除与参考图气质相反的风格（如参考图是暖调节庆感，则 avoid 里应包含"低饱和"、"性冷淡"、"留白过多"）。
- **必须识别参考图中的具体内容语义**（季节、天气、场景、节庆道具、原始剧情），这些内容默认不得进入正向风格描述。
- 若参考图场景与 brief 冲突，应将冲突内容写入 `content_do_not_inherit`，并通过 `season_override_hint` 明确声明“以 brief 为准”。
- 允许继承：配色、材质、笔触、光感、装饰密度、整体氛围。
- 不允许默认继承：季节、天气、地貌、场景地点、节庆道具、角色剧情动作。
- 有风格参考图时，未成功生成并落盘 `style_profile.json` 不得进入 Step 5.8。

---

## Step 5.8：画面创意表达方案确认

在组装 prompt 之前，必须基于当前所有已确认信息，先向用户展示一版**画面创意表达方案**，让用户用纯文字就能清晰理解最终海报打算如何表达，再决定是否进入 prompt 组装。

### 输入来源

- `brief.json`
- `copywriting.json`
- `distill_card.json`（如有）
- `style_profile.json`（如有）
- 已确认的素材信息（`brief.json.assets`）

### 输出文件

- `creative_direction.json`

### 生成方式

必须先通过脚本生成创意表达草案，禁止 main 直接手写最终版：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/generate_creative_direction.py \
  --brief "[项目目录]/brief.json" \
  --copywriting "[项目目录]/copywriting.json" \
  --distill "[项目目录]/distill_card.json" \
  --style-profile "[项目目录]/style_profile.json" \
  --output "[项目目录]/creative_direction.json"
```

**注意**：
- `--distill` 为可选参数；有蒸馏卡时传入。
- `--style-profile` 为可选参数；有参考图风格提炼结果时传入。
- 脚本输出的是**创意表达草案**，用户确认后才能作为后续 prompt 组装输入。

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

### 给用户的展示话术

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

### 用户确认后的文件处理

- 回复「确认创意」：保留当前 `creative_direction.json` 进入 Step 6
- 回复「修改创意：[具体要求]」：先根据要求更新 `creative_direction.json`，再重新展示给用户确认
- 未完成创意确认前，**不得**进入 prompt 组装

### 关键规则

- 这是 **prompt 之前的创意对齐步骤**，目标是先确认“这张图怎么表达”，不是直接展示 prompt 细节。
- 方案必须严格基于已确认信息生成，不得新增用户未确认的产品卖点、人物设定、节庆道具或剧情。
- 若有参考图，只能转译其视觉语言，不得把原参考图中的具体场景、天气、剧情直接搬过来。
- 若用户在此步骤提出创意修正，必须先更新 `creative_direction.json`，再进入下一步。
- `creative_direction.json` 至少必须包含：`summary`、`hero_focus`、`composition_plan`、`text_visual_relationship`、`must_hit`、`must_avoid`。缺任一项都不得进入 Step 6。

---

## Step 6：运行 assemble_prompt.py 脚本组装 prompt

**必须通过脚本生成 prompt，禁止手写。**

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/assemble_prompt.py \
  --brief "[项目目录]/brief.json" \
  --distill "[项目目录]/distill_card.json" \
  --copywriting "[项目目录]/copywriting.json" \
  --style-profile "[项目目录]/style_profile.json" \
  --creative-direction "[项目目录]/creative_direction.json" \
  --output "[项目目录]/prompt_draft.md"
```

**注意**：`--style-profile` 为可选参数。有 `style_profile.json` 时传入，无则省略（脚本会使用中性回退描述）。
`--creative-direction` 为强烈建议参数；一旦用户已确认画面创意表达方案，则必须传入，不得跳过。

脚本自动完成：
1. 读取 brief.json + distill_card.json + copywriting.json + creative_direction.json（如有）
2. 按规则程序化组装 prompt（参考图排序：风格→骨架→产品→IP→Logo）
3. 内置校验：检查无工作流术语、坐标覆盖率、文案覆盖率、参考图角色挂载是否冲突、创意表达是否缺失主视觉锚点
4. 输出 prompt_draft.md 与 ref_order.json

**脚本成功（退出码 0）后，向用户展示 prompt 摘要：**

```markdown
📝 **生图 Prompt 已组装完成**

- 参考图数量：N 张
- 区域数量：N 个
- 负面约束：N 条
- 分辨率：4K

回复「确认生图」进入下一步。
```

**脚本失败（退出码 ≠ 0）时**：展示校验错误，修复后重新运行。

**进入 Step 7 前必须满足以下条件**：
- `prompt_draft.md` 已生成
- `ref_order.json` 已生成，且其中所有 `path` 都必须是**绝对路径**
- 若已执行 Step 5.8，则 `creative_direction.json` 必须存在，且其中至少包含 `summary`、`hero_focus`、`composition_plan`
- 若 `hero_priority.hero_1` 明确为“产品”，则 `brief.json.assets.product` 必须存在且不可为空
- 若同时存在 `assets.product` 与 `assets.ip`，两者路径不得相同
- 若脚本报告参考图角色冲突，必须先回到素材确认/修正，不得继续生图
- `ref_order.json` 中每个参考图路径对应的文件都必须真实存在，缺任意一个都不得进入生图

**禁止规则**：
- 脚本输出即为最终 prompt，main agent **不得手动追加、修改、拼接任何内容**到 prompt_draft.md
- 蒸馏卡的 `copy_planning_guide`、`notes`、`Distill ID` 等内部字段不得出现在 prompt 中
- 如果 prompt 不完整，必须修复脚本后重新运行，不得手补
- 脚本同时输出 `ref_order.json`，记录参考图传图顺序，run.sh 必须按此顺序传图

---

## Step 7：派发 design subagent 生图

### 核心原则：main 写完，子 agent 只跑

生图任务由 main 在主会话完成全部策划和脚本编写，子 agent 只负责执行脚本并等待结果。**不要把 prompt、参考图信息、蒸馏卡数据等塞进子 agent 任务描述。**

### 7.1 main 先写好生图脚本

在派发子 agent 之前，main 必须先写好 `run.sh` 到项目目录：

```bash
#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]"
EXEC_SCRIPT="/Users/a123/.openclaw/skills/brand-poster-creator/scripts/execute_generation.py"

python3 "${EXEC_SCRIPT}" --project-dir "${PROJECT_DIR}" --size 2160x3840 --aspect 9:16 --model gpt-image-2-pro
```

**注意**：
- **参考图顺序由 `assemble_prompt.py` 输出的 `ref_order.json` 决定**，不再手写。run.sh 从该文件动态读取，确保与 prompt 中的参考图编号严格对应
- role 到参数的映射固定为：`style_ref → --ref-style`、`skeleton → --reference`、`product → --ref-product`、`ip → --ref-ip`、`logo → --ref-logo`
- 所有路径使用绝对路径，不用相对路径
- prompt 从 `prompt_draft.md` 读取，不内联
- 脚本执行后必须产出 `generation_result.json` 与 stdout/stderr 日志，作为唯一验收依据

脚本写完后，main 确认文件存在且内容正确，再进入下一步。

### 7.2 派发子 agent（执行型，不塞上下文）

```json
{
  "runtime": "subagent",
  "agentId": "design",
  "task": "海报生图：执行脚本",
  "mode": "run",
  "timeoutSeconds": 600,
  "runTimeoutSeconds": 600,
  "lightContext": true,
  "thinking": "low",
  "model": ""
}
```

**spawn 参数约束同 Step 4：**
- `thinking`：只填 `"low"` / `"medium"` / `"high"` / `"adaptive"`，禁止填思考内容
- `model`：留空或用白名单内模型，禁止用非白名单 provider
- `attachments`：不要传，附件通道未开启

**给子 agent 的任务描述（固定模板，不改动）：**

```
你是品牌海报生图专家。按以下步骤执行，不要解释、不复述需求、不做方案：

1. 执行以下脚本：
   bash /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/run.sh

2. 读取并确认以下结果文件存在：
   /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/generation_result.json

3. 如果 `generation_result.json` 中 `ok=true`，再确认输出文件存在：
   /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/images/final_poster.png

4. 完成后只回传：`generation_result.json` 路径；若成功，再附上 `final_poster.png` 路径。

不要修改脚本内容，不要改变参数，不要读取其他无关文件。
```

### 7.3 回收结果

子 agent 完成后（遵守 AGENTS.md 0.7.1 等待完成事件规则）：
1. 先读取 `generation_result.json`，确认 `ok=true`
2. 再检查 `images/final_poster.png` 是否真实存在
3. 确认文件大小合理（不应为 0 字节）
4. 若任一条件不满足，视为执行失败，先查看 `stdout/stderr` 日志，不得向用户播报“已出图”
5. 只有全部通过后，才按 Step 8 流程发送成品图给用户

---

## Step 8：发送成品图 → 用户确认

仅当 `generation_result.json.ok=true` 且成品文件真实存在后，才将成品图发送给用户确认。

在发送前，main 必须先执行：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/prepare_feishu_delivery.py \
  --project-dir /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]
```

该脚本会产出：
- `/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/delivery_manifest.json`
- 交付目录中的预览图 / 原图副本 / 原图 zip（按大小条件分流）

发送规则：
1. 先读取 `delivery_manifest.json`
2. 若 `delivery_mode=direct_image`：
   - 直接发送 `deliverables.original_copy.path`
3. 若 `delivery_mode=preview_and_zip`：
   - 只发送 `deliverables.preview_image.path` 供飞书预览
   - 明确告诉用户：当前发送的是压缩预览图，原始高清图已保留，后续修改将继续使用原图，不会基于预览图反复压缩
   - 用户确认定稿后，再发送 `deliverables.original_zip.path` 作为原图交付包
4. 任何“局部修改”“继续调整”“重新生成”都必须继续引用 `edit_source_image` 指向的原图，不得把 preview 图当作修改输入

给用户的话术：

```markdown
🎉 **海报已生成**

- 若当前收到的是原图：可直接按原清晰度确认
- 若当前收到的是预览图：这是为适配飞书大小限制自动生成的压缩预览，原始高清图已保留；若你确认定稿，我再把原图 zip 包发给你
- 后续如需局部修改，我会继续基于原图处理，不会使用压缩预览图反复修改

请确认：
- 文案位置是否正确
- 产品外观是否保真
- 整体视觉效果是否满意

请选择：
- 「确认定稿」→ 完成；若当前为预览图，再补发原图 zip
- 「局部修改 [具体描述]」→ 调整后重新生图
```

---

## Step 9：任务完成确认与清理

当用户确认定稿且不再继续修改时，才允许执行清理。

### 执行方式

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/cleanup_project.py \
  --project-dir "[项目目录绝对路径]" \
  --confirmed
```

### 清理规则

脚本会使用 `trash` 删除中间文件，**不会**直接使用 `rm`。

默认保留：
- `brief.json`
- `copywriting.json`
- `generation_result.json`
- `delivery_manifest.json`
- `cleanup_manifest.json`
- `project_state.json`
- `audit_log.jsonl`
- `images/final_poster.png`

默认清理：
- `logs/` 下日志文件
- `images/` 下非最终交付图片
- `prompt_draft.md`
- `distill_card.json`
- `creative_direction.json`
- `style_profile.json`
- `ref_order.json`
- `distill_manifest.json`
- `gap_check_manifest.json`
- `style_profile_manifest.json`
- `creative_direction_manifest.json`
- `prompt_manifest.json`

### 安全约束

- 未传 `--confirmed` 时，脚本必须拒绝执行并记录失败状态
- 未得到用户“已完成/可清理”明确确认前，不得调用清理脚本
- 清理完成后必须生成 `cleanup_manifest.json`，并同步更新 `project_state.json` 与 `audit_log.jsonl`

**若用户选择保留，则不执行清理脚本。**

---

## 环境变量

```bash
# 智创聚合 API
export BANANA_API_URL="https://n.lconai.com"
export BANANA_API_KEY="sk-your-api-key"

# 飞书 API
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```
