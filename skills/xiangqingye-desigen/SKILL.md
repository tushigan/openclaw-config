---
name: xiangqingye-desigen
description: 从 0 开始规划电商详情页工作流：3 阶段紧凑流程（策略 → 手稿 → 成稿），默认单张方形画板 1920x1920 4 列纵向排列全部屏，全局风格指南确保风格统一，项目化文件管理避免混乱。适用于详情页策划、详情页手稿、电商长图、移动端详情页、PC详情页、详情页生成与拼接。重点服务食品/烘焙/快消品，也可泛化到其他消费品。触发词包括：详情页、详情页手稿、电商长图、移动端详情页、PC详情页、详情页策划、详情页生成、详情页拼接。
---

# xiangqingye-desigen

## 这是什么
这个 skill 不是"直接生一张详情页图"，而是一条 **详情页工作流**。

采用 **3 阶段紧凑流程**，每个阶段只确认一次：

```
阶段 1：策略（载体 + 产品事实 + 分段方案 + 风格指南）  ← 确认点 1
阶段 2：手稿（所有段黑白手稿一次性产出）              ← 确认点 2
阶段 3：成稿（最终设计稿 + 封闭边界硬拼接）            ← 确认点 3
```

不是 7 步逐次确认，而是 3 个阶段各一次确认。全程使用项目化文件管理，过程稿自动归档。

---



## 专业化升级规则（强制执行）

### 一个项目一个独立工作空间

每个详情页项目必须拥有独立项目目录，不允许多个项目混用素材、状态或输出：

```text
outputs/{项目名}_{日期}/
├── progress.json              # 项目状态看板
├── facts.json                 # 产品事实锁定
├── asset_registry.json        # 本项目固定资产注册表
├── platform_profile.json      # 本项目平台/介质规则快照
├── category_profile.json      # 本项目品类方法论快照
├── style_guide.png            # 本项目全局风格指南
├── 策划/
│   ├── strategy_v1.md
│   ├── copywriting_v1.md
│   └── prompt_package/
├── 手稿/
├── 设计/
├── 头图/
├── 参考/
└── 交付/
```

全局 skill 只保存方法论、profile 和脚本；项目素材、确认状态、输出版本必须保存在项目目录内。

### 项目初始化后的强制步骤

创建项目后必须立即执行：

```bash
# 1) 生成平台/品类快照
python scripts/create_project_profiles.py --project-dir {项目目录} --platform tmall_mobile --category food_bakery

# 2) 自动检索品牌资产候选（来自既有品牌资产库/飞书同步目录等）
python scripts/discover_brand_assets.py --project-dir {项目目录} --brand "{品牌名}" --source-dir {品牌资产来源目录}

# 3) 自动检索品牌知识候选（Dify 自动匹配知识库）
python scripts/discover_brand_knowledge.py --project-dir {项目目录} --brand "{品牌名}"

# 4) 用户确认后，再生成正式素材注册表
python scripts/create_asset_registry.py --project-dir {项目目录} --platform tmall_mobile --category food_bakery

# 5) 用户确认知识摘要后，再生成 prompt package
python scripts/build_prompt_package.py --project-dir {项目目录}
```

- `platform_profile.json` 和 `category_profile.json` 是本项目的方法论快照，后续全局规则升级不应影响当前项目。
- `参考/brand_asset_candidates.json` 只是候选资产清单；**未确认前不得写入 `asset_registry.json`。**
- `策划/brand_knowledge_candidates.json` 只是候选知识清单；**未确认前不得写入正式 prompt package。**
- `asset_registry.json` 是后续所有嵌套生图/改图 skill 的唯一素材来源。
- `prompt_package/` 是跨阶段 prompt 的标准输入，后续调用统一使用 `--prompt-file`。
- 若自动检索无结果，不阻断项目：素材继续走手动上传，知识继续走通用品类/profile 规则。

### 上下文隔离原则

详情页 skill 是编排型 skill，内部会嵌套调用生图、改图、拼接、交付能力。为避免长上下文混乱，必须遵守：

1. main 负责项目编排、阶段门禁、文件检核、统一交付和 subagent 分派，**不亲自做策略/文案/生图**。
2. 策略/逐屏文案必须 spawn `strategy` subagent（Claude Opus 4.7）；手稿/成稿图必须 spawn `design` subagent。
3. 分段成稿图应**并行** spawn 多个 design subagent（每段一个），main 等待全部返回后做读回核验。
4. strategy/design 等子代理只读取当前阶段需要的项目文件，不依赖聊天上下文回忆素材。
5. 生图/改图调用必须使用明确文件路径和 `--prompt-file`，不得用复杂内联命令拼接 prompt。
6. 素材角色必须来自 `asset_registry.json`，不得临时猜测”哪张是产品图/包装图/风格图”。
7. 品牌知识只能来自项目内已确认摘要文件，不得把候选检索结果直接塞入 prompt。
8. 每阶段完成后写入标准产物，再由下一阶段读取标准产物继续。
9. main 同时推进多个项目时，每个项目独立走上述 subagent 分派链路，不混用上下文。

### 阶段门禁

推荐项目状态顺序：

```text
intake
→ facts_locked
→ asset_registry_ready
→ strategy_approved
→ wireframe_generated
→ wireframe_qa_passed
→ wireframe_cut_approved
→ design_segments_generated
→ concat_checked
→ head_images_generated（默认需要；仅当用户明确说本项目不要头图时可跳过）
→ delivery_checked
→ delivery_packaged
→ delivered
→ archived（用户确认结束后）
```

未通过上一阶段检查时，不得继续进入下一阶段；如用户明确要求跳过，必须说明风险并记录到交付清单。


## Step 0：初始化项目目录（必须前置）

### 0.1 创建项目目录

使用 `scripts/project_manager.py` 创建按项目/版本/类型分类的目录结构：

```bash
python scripts/project_manager.py init "卡宾熊法式可丽饼" --segments A,B,C,D,E,F --output outputs/
```

产出目录结构：
```
outputs/卡宾熊法式可丽饼_20260429/
├── progress.json          # 状态看板（始终唯一）
├── 策划/                  # 策略文案
├── 手稿/                  # 黑白手稿（v1/, v2/, ...）
├── 设计/                  # 最终设计稿（v1/, v2/, ...）
└── 参考/                  # 用户提供的参考图
```

### 0.2 确认载体与背景信息

问清 4 件事：
1. 这个详情页主要投放在哪个平台？
2. 用户主要是手机看、电脑看，还是双端都要？
3. 这次优先服务哪个载体？
4. 当前要产出的中间物是什么：**策略 / 黑白手稿 / 最终设计稿**？

### 决策规则
- **移动端优先**：按手机纵向阅读逻辑规划
- **PC 优先**：按网页纵向滚动逻辑规划
- **双端都要**：先明确主端，再决定副端是复用还是重排

### 0.3 产品事实锁定（强制执行）

背景信息确认后，立即运行产品事实锁定脚本：

```bash
python scripts/lock_product_facts.py --output {项目目录}/facts.json --brand "品牌名" --product "产品名" --category "类目" --structure clamped --layers 3 --flavors "口味1,口味2,口味3" --main-flavor "主推口味" --emboss bear_face --packaging-required
```

结构类型可选：`solid`（实心）/ `clamped`（夹心）/ `hollow`（空心）/ `coated`（涂层）/ `filled`（注心）/ `molten`（流心）
压纹类型可选：`none` / `bear_face` / `brand_logo` / `pattern`

生成的 `facts.json` 必须注入到后续所有图像生成的 prompt 中。

### 0.4 候选资产与知识确认（强制执行）

项目初始化后，先把自动检索到的候选资产和候选知识发给用户确认：

- `参考/brand_asset_candidates.json`：品牌资产候选（LOGO / IP / 包装 / 风格参考）
- `策划/brand_knowledge_candidates.json`：品牌知识候选（Dify 检索片段）

确认规则：
- 未经用户明确确认，不得生成正式 `asset_registry.json`；若用户暂未确认，可生成 `asset_registry_base.json` 作为占位，但后续成稿阶段不得将其当作正式素材注册表。
- 未经用户明确确认，不得生成正式 `brand_knowledge_confirmed.json`。
- 未确认前，只能把候选内容当作预填充参考，不得直接进入 prompt package。
- 若检索为空，继续手动上传素材 / 使用平台与品类规则，不得卡死流程。

#### 候选确认落盘步骤（强制执行）

用户确认候选资产后，必须执行以下步骤将确认结果落盘：

**品牌资产确认**：
1. 将用户确认的素材角色（`brand_logo` / `product_main` / `packaging` / `style_ref`）写入 `参考/brand_asset_confirmed.json`
2. 格式为：
```json
{
  "confirmed_assets": [
    {"role": "brand_logo", "path": "绝对路径或相对路径"},
    {"role": "product_main", "path": "绝对路径或相对路径"}
  ],
  "confirmed_at": "ISO 8601 时间戳"
}
```
3. 确认文件落盘后，才能运行 `create_asset_registry.py`。

**品牌知识确认**：
1. 将用户确认的知识摘要写入 `策划/brand_knowledge_confirmed.json`
2. 格式为：
```json
{
  "confirmed_items": [{"title": "知识标题", "summary": "一段话摘要"}],
  "confirmed_at": "ISO 8601 时间戳"
}
```
3. 确认文件落盘后，才能运行 `build_prompt_package.py`。
4. 若知识库无匹配结果（候选为空），仍可生成基础 prompt package，但不得编造品牌知识。

#### 自动资产检索脏结果兜底（强制执行）

`discover_brand_assets.py` 的 `--source-dir` 参数可能指向包含大量无关文件的目录。必须遵守以下兜底规则：
- 若 `--source-dir` 下文件数量超过 200 张，或目录总大小超过 2GB，**不得直接扫描整个目录**。
- 若候选结果中同一角色（如 `brand_logo`）匹配超过 50 个文件，说明 source-dir 过脏，**必须停止自动扫描**，改为请用户手动提供 1-3 张关键素材路径。
- 若候选结果明显失真（例如匹配到无关品类/无关品牌/非图片文件），**不得继续用自动候选推进**，必须在报告中说明失真原因，切换为人工上传优先。
- 脏结果兜底触发时，agent 不得将失真候选发给用户确认，必须先说明"自动检索结果不可用，建议手动提供素材"。

#### 脚本输入依赖（强制执行）

| 脚本 | 必须读取的输入 | 行为 |
|------|---------------|------|
| `create_asset_registry.py` | `facts.json` + `参考/brand_asset_confirmed.json` + `platform_profile.json` + `category_profile.json` | 合并产品事实与已确认资产，输出 `asset_registry.json`；若 `brand_asset_confirmed.json` 不存在，输出 `asset_registry_base.json`（仅含产品事实推导的占位素材），后续阶段不得将 `asset_registry_base.json` 当作正式注册表使用 |
| `build_prompt_package.py` | `facts.json` + `asset_registry.json`（或 `asset_registry_base.json`）+ `策划/strategy_v1.md` + `策划/copywriting_v1.md` + `style_guide.png` + 可选 `策划/brand_knowledge_confirmed.json` | 生成 `prompt_package/design_segment_base.txt` + `wireframe_base.txt`；知识为空时不阻断，仅使用平台/品类/策略/事实；若仅存在 `asset_registry_base.json`，只允许生成基础 wireframe / 策划阶段 prompt，不得用于成稿阶段；进入成稿前必须切换为正式 `asset_registry.json` |

### 0.5 计算最优布局方案

```bash
python scripts/calculate_layout.py --screens 6 --screen-height 1280 --carrier mobile
```

推荐策略：
- **方形画板**（默认 1920x1920）：单张画板 4 列纵向排列，一次装全部屏（11+ 屏）
- **竖版画板**（默认 768x1920）：一次装 2-3 屏，适合内容少

---

## 阶段 1：策略（一次确认）

### 1.1 策略规划（必须派给战略专家 subagent）

背景信息确认后，**必须派给战略专家 subagent**，不得默认由 main 手搓：

```bash
openclaw subagents spawn strategy "{品牌名} {产品名} 详情页策略规划" --timeout 600
```

战略专家需要输出：
- 一句话总策略
- 用户购买动机拆解
- 详情页叙事逻辑
- 页面模块框架
- 建议的连续段结构

输出存入 `{项目目录}/策划/strategy_v1.md`。

main 的职责是：提供完整的背景信息（载体、产品事实、用户参考图、品牌调性），等待 subagent 返回后做读回检核，而不是自己重写策略。

#### 战略子代理失败/中断时的降级方案（新增）

如果出现以下任一情况：
- subagent 长时间无返回 / 被中断
- 当前平台不适合继续等待
- 用户明确要求“你直接出”

则 **main 可以直接接管策略阶段**，不要卡住流程反复重试。

此时 main 的最小执行闭环是：
1. 先锁定产品事实：品牌、品名、载体、当前阶段、口味、规格、卖点、包装形式、保质期。
2. 再对用户提供的素材做视觉拆解，至少覆盖：
   - 产品图：口味锚点、共通结构、可放大食欲点、不可夸大项
   - 包装图：主叙事、硬卖点、视觉语法、风险表述
   - LOGO：品牌气质、配色、轮廓语言
   - 风格参考：构图、材质、氛围、可借鉴与不可照搬项
3. 基于以上信息，直接输出手机端/PC 端详情页策略，包括：
   - 一句话总策略
   - 目标用户与购买动机
   - 叙事主线
   - 6-8 屏模块结构
   - 每屏任务 / 主标题方向 / 信息点 / 建议视觉 / 过渡关系
   - 整体风格指南
   - 必须强调的卖点与必须规避的风险表述
4. 明确标注哪些信息来自已确认事实，哪些只是视觉联想，避免把风味联想写成已证实卖点。

**原则**：优先保证策略阶段能交付，再决定是否回头优化 subagent 流程。

### 1.2 逐屏文案（必须派给战略专家 subagent，一步到位）

策略规划完成后，**必须派给战略专家 subagent** 产出逐屏文案：

```bash
openclaw subagents spawn strategy "{品牌名} {产品名} 详情页逐屏文案" --timeout 600
```

任务指令中必须包含：
- 已确认的策略文件路径（`策划/strategy_v1.md`）
- 产品事实（`facts.json`）
- 分段结构（A/B/C/D 各段对应哪些屏）
- 每屏必须输出：屏幕名称 / 这屏任务 / 主标题 / 副标题 / 关键信息点 / 建议视觉内容 / 信息层级 / 与前后屏的过渡关系 / 所属连续段

输出存入 `{项目目录}/策划/copywriting_v1.md`。

#### 逐屏文案门禁（强制执行）
- 策略阶段输出 `strategy_v*.md` 只是框架，**不能替代**逐屏文案。
- 不得只输出"策略方向""分段方案"就声称策略阶段已完成。
- `copywriting_v*.md` 必须逐屏列出上述 8 项内容，缺一屏即视为未完成。
- main / subagent 不得跳过逐屏文案直接进入手稿阶段；project_manager 在 `update-phase wireframe` 前必须校验 `策划/copywriting_v*.md` 是否存在且包含所有分段对应的屏数。
- 即使用户说"直接进手稿"，也必须先补齐逐屏文案再进入下一阶段（可以简短补，但不能缺）。

#### 逐屏文案确认门禁（强制执行）
- 逐屏文案生成后，**必须把全文发给用户确认**，不得只说"写好了"却把内容留在项目文件里。
- 飞书消息有长度限制时，必须分多条发送或使用文档链接，确保用户能看到每一屏的主标题、副标题、建议视觉。
- 用户确认后，必须执行以下命令标记确认状态：
```bash
python scripts/project_manager.py set-copywriting-flag --confirmed --project-dir {项目目录}
```
- 未执行确认命令前，不得进入阶段 1.3 风格指南或阶段 2 手稿。

### 1.3 生成全局视觉资产

策略和文案确认后，立即生成全局风格指南：

#### 全局风格指南图（一次）
```bash
python scripts/generate_style_guide.py --facts {项目目录}/facts.json --ref-style user_style.png --output {项目目录}/style_guide.png
```

这张图不是最终设计，而是一个"风格色卡"，包含页面背景处理方式、装饰元素风格、色彩体系。

生成后，必须作为 `--ref-style` 注入到**每一个**后续段落的生成中。

### 1.4 确认点 1

更新状态并发送飞书汇报：

```bash
python scripts/project_manager.py update-phase planning --project-dir {项目目录}
python scripts/project_manager.py feishu-report --phase 1 --project-dir {项目目录}
```

用户确认：载体 + 产品事实 + 分段方案 + **逐屏文案全文** + 风格指南。

确认点 1 必须包含：
- 策略方向（一句话总结）
- 逐屏文案每一屏的主标题 / 副标题（用户必须能看到完整文案，不能只看框架）
- 风格指南图
- 只有用户逐屏文案确认后，才能进入后续阶段

---

## 阶段 1.5：头图策略（默认必问，用户明确拒绝才可跳过）

电商详情页项目通常需要配套输出**头图（主图/KV）**，与详情页风格统一，形成完整的销售说服链路。

#### 头图需求确认门禁（强制执行）
- 策略阶段完成后、手稿阶段开始前，**必须主动询问用户是否需要头图**。
- 不得默认假设"用户没提就不要头图"，也不得默认"后面自然会做"。
- 用户明确说"不需要头图"时，执行以下命令后继续手稿阶段：
```bash
python scripts/project_manager.py set-head-flag --not-required --project-dir {项目目录}
```
- 用户确认需要头图时，执行以下命令：
```bash
python scripts/project_manager.py set-head-flag --required --project-dir {项目目录}
```
- 用户未回复或回复模糊时，默认 `head_images_required=true`，并在报告中持续提醒头图待确认。
- 阶段 1.5 虽标注为"可选"，但"问不问"是必选项。不问即视为流程缺陷。

### 1.5.1 头图数量判断

根据商品复杂度自动判断头图数量：

| 商品类型 | 头图数量 | 判断依据 |
|----------|----------|----------|
| 低价简单品（纸巾、零食单品） | 3张 | 单功能、低决策成本、单SKU |
| 标准普通品（护肤品、食品、小家电） | 5张 | 多功能、常规决策、可能多SKU |
| 高客单复杂品（智能家电、家具） | 6-8张 | 复杂功能、高决策、多配件/尺寸适配 |

判断维度：
- 商品复杂度（功能越复杂，图越多）
- 客单价（价格越高，需要更多证明）
- 是否多SKU（多颜色/尺寸需要SKU图）
- 是否礼品属性（礼盒需要包装图）

### 1.5.2 5张头图分工结构（默认标准品）

多张头图不是重复，而是**递进式销售说服链路**：

| 顺序 | 角色 | 核心问题 | 内容要求 |
|------|------|----------|----------|
| 第1张 | 主视觉 | 这是什么？值不值得看？ | 商品主体/场景/品牌调性/一句核心利益 |
| 第2张 | 核心卖点 | 为什么买它？ | 1-3个关键卖点，参数转利益 |
| 第3张 | 使用场景 | 我怎么用？适合我吗？ | 目标人群、使用环境、使用结果 |
| 第4张 | 细节证明 | 好在哪里？靠谱吗？ | 材质、结构、成分、工艺、效果、认证 |
| 第5张 | 规格确认 | 我会收到什么？ | 包装、尺寸、容量、套装、配件、SKU |

**核心原则**：一张头图只讲一个核心主题，最多补充 2-3 个辅助卖点。

### 1.5.3 头图规格

**生成规格与交付规格必须拆开**：

| 平台 | 交付规格 | 模型生成规格 |
|------|----------|-------------|
| 淘宝/天猫/京东 | 800x800 | 1440x1440，生成后缩放导出 |
| 拼多多 | 750x750 | 1440x1440，生成后缩放导出 |
| 品牌官网 | 1000x1000 或 1200x1200 | 1440x1440，生成后缩放导出 |

- 模型默认生成最小安全档是 `1440x1440`。
- `800x800` / `750x750` 只是最终交付给平台的尺寸，**不能直接作为 gpt-image-2-pro 的输入尺寸**。
- 平台若要求特殊尺寸，先生成 1440x1440 高清稿，再按需缩放导出。

### 1.5.4 头图风格统一

头图必须与详情页共用：
- `style_guide.png`（风格指南）
- 产品参考图
- 品牌 LOGO
- 包装参考图

输出存入 `{项目目录}/策划/head_image_strategy_v1.md`

### 1.5.5 执行命令

```bash
# 生成头图 prompt 文件
python scripts/create_head_prompts.py --project-dir {项目目录}

# 执行头图批量生成（模型生成最小 1440x1440，不要传 800x800）
bash scripts/generate_head_images.sh {项目目录} v1 1440x1440
```

生成完成后，如需平台交付尺寸（800x800 等），另行缩放导出。

---

## 阶段 2：手稿（一次确认）

### 2.0 分派给生图专家（强制执行）

手稿图的生成**必须派给生图专家 subagent**，main 不得直接调用生图脚本：

```bash
openclaw subagents spawn design "{品牌名} {产品名} 详情页黑白手稿" --timeout 600
```

main 的职责：
- 提供完整的项目文件路径（`facts.json`、`策划/copywriting_v1.md`、`策划/strategy_v1.md`、`prompt_package/wireframe_base.txt`、`asset_registry.json`）
- 明确画板尺寸（默认 1920x1920；用户明确要求高分辨率时才升高）、4 列纵向排列、屏数分配
- 等待 subagent 返回后，做读回 QA（不得因为"子代理已返回"就视为合格）

只有当 subagent 长时间无返回 / 被中断 / 用户明确要求"你直接出"时，main 才允许降级直接调用生图脚本。

### 2.1 手稿生成规则

#### 方形画板策略（单张 4 列纵向）
用 **1 张方形画板**（默认 1920x1920）**4 列纵向排列**展示全部屏幕，而非 6 段分开生成。

- **每列是一个完整的纵向滚动长页面片段**（3-4 屏/列）
- **屏与屏之间没有边框线、分隔线**，内容自然连贯过渡
- 只有 4 列之间有细灰色竖线分隔
- **不要添加 "Column 1/2/3/4" 等标注**（避免污染后续设计稿）

示例（11 屏）：
```
第1列：S1-S3 开场认知
第2列：S4-S6 原料+主推
第3列：S7-S9 口味详情
第4列：S10-S11 收尾购买
```

#### 版式变化规则
- **并列关系锁版式**：同一系列页面统一结构，保持系列感
- **非并列关系有变化**：不同功能的页面版式不同，避免机械统一

#### 尺寸验证（强制执行）
每次生图前必须调用：
```bash
python scripts/validate_dimensions.py --canvas square
```

#### 手稿精度要求
- 产品图用**简笔画轮廓**（不是 × 占位或实心块）
- 文字用**具体文案**（不是"标题占位""卖点条"）
- 字体有明确的**大小层级**（大粗体标题 / 细体副标题 / 小字正文）
- 像专业的 UI/UX wireframe 设计稿，不是潦草草图
- 质量目标必须达到“彩稿前最后一次结构确认”精度，而不是仅能表达版面分布的结构示意
- **默认直接输出高精度正式手稿**，不采用“先低精度预览、再高精度正式版”的双阶段流程。
- 若用户只是想先看方向，也应基于同一套正式手稿链路直接输出可读的高精度版本，而不是另起低精度预览链路。

#### 手稿唯一执行路径（强制执行）
- **黑白手稿阶段默认且唯一使用 skill 规定的生图链路生成**，不得临时改用 Python / Pillow / 手写线框 / 其它未在本 skill 中定义的替代方式来“先凑一版”。
- **默认只允许单次高精度正式手稿输出**，不得把低精度草图作为标准中间产物，再二次升级为正式版。
- 如当前手稿质量不达标，必须回到本 skill 规定的原始生成链路重做，**不得**为了补救而擅自切换到 skill 外方案。
- 只有当用户明确要求“只出临时结构草图 / 不走正式手稿链路”时，才允许偏离本阶段标准，并且必须显式说明这是降级产物。
- 若使用 subagent 生成手稿，主编排仍必须按本 skill 标准做读回、QA、切段和确认，不能因为“子代理已返回”就视为合格。

#### 手稿阶段重新锚定规则（强制执行）
- 每次进入手稿阶段，或因用户反馈而重做手稿时，必须重新阅读本节手稿规则，不能只凭前文记忆继续执行。
- 进入手稿阶段前，必须重新读取本项目的 `facts.json`、`asset_registry.json`、`platform_profile.json`、`category_profile.json`、`策划/brand_knowledge_confirmed.json`（如有）以及 `策划/prompt_package/wireframe_base.txt`，不得只依赖聊天上下文回忆要求。
- 用户对手稿提出明确修改要求且未要求先看方案时，默认立即执行重做；但执行方式仍必须受本节“唯一执行路径”约束。

#### 手稿禁止规则（强制执行）
- **禁止手机外框**：不要画手机模型/外壳/刘海/状态栏/底部横条，页面内容直接铺满整个画板
- **禁止屏数标注**：不要添加"第1屏"、"Screen 1"、"1/11"等数字标注
- **禁止列标注**：不要添加"Column 1"、"第1列"等文字标注
- **禁止边框线**：屏与屏之间不要画分隔线或边框（4列之间的细灰色竖线除外）

### 2.2 手稿 QA（强制执行）

手稿生成后，必须先做基础 QA，不能直接进入成稿：

```bash
python scripts/validate_wireframe.py {项目目录}/手稿/v1/wireframe_all.png --expected-size 1920x1920 --report {项目目录}/手稿/v1/wireframe_qa_report.json
```

检查重点：
- 尺寸和比例是否符合默认 1920x1920 方形 4 列画板
- 是否出现手机外框、刘海、状态栏、底部横条
- 是否出现“第1屏”“Screen 1”“1/11”“Column 1”等标注
- 是否出现“标题占位”“卖点条”“XXX”“Lorem”等占位内容
- 产品是否用轮廓表达，而不是 × 占位或实心块

#### 手稿阶段完成声明门禁（强制执行）
- **未生成正式手稿文件前**，不得对用户说“手稿已完成”“已经做好了”。
- **未通过 QA 前**，不得对用户说“可以进入成稿”或“下一步直接做设计稿”。
- **若 QA 发现问题**，默认动作是返工；只有用户明确接受风险时，才允许带风险继续，并且必须把风险说清楚。
- **subagent 返回成功 / 口头说已完成 / 只产出临时草图** 都不算阶段完成，main 必须读回正式产物并完成本节 QA 后，才能进入切段确认。
- 任何低精度预览图、草图图、方向试探图都**不能**冒充本阶段正式交付物，也不能作为跳过 QA / 切段确认的依据。

如 QA 未通过，必须返工或询问用户是否接受风险，不能默认进入最终设计稿。

### 2.3 手稿切段确认（强制新增确认点）

手稿 QA 通过后，切段生成预览与确认清单：

```text
{项目目录}/手稿/v1/cut_preview/
├── segment_A_preview.png           # 推荐切点预览，可来自启发式分析
├── segment_A_confirmed.png         # 用户确认后才能作为正式输入
├── segment_B_confirmed.png
├── segment_C_confirmed.png
├── segment_D_confirmed.png
├── cut_report.md
└── cut_manifest.json               # status=confirmed，记录 confirmed_file 与切点来源
```

强制规则：
- `segment_*_confirmed.png` 才是正式确认段图；`segment_*.png`、`*_wide.png`、临时脚本裁切结果都不能直接进入成稿。
- `cut_manifest.json` 必须存在，且 `status` 必须为 `confirmed`；其中要记录每段的 `confirmed_file` 与 `source`。
- `source` 仅允许使用 `annotation`、`whitespace_analysis`、`manual`、`confirmed_preview` 这几类显式来源，避免把固定四列整高裁切伪装成正式确认结果。
- 必须把切段预览、`cut_report.md` 和确认结果发给用户确认。只有用户明确确认切段结构正确后，才能进入阶段 3 成稿。

### 2.4 确认点 2

所有手稿生成并通过 QA、切段预览确认后，一次性展示给用户确认：

```bash
python scripts/project_manager.py update-phase wireframe --project-dir {项目目录}
python scripts/project_manager.py feishu-report --phase 2 --project-dir {项目目录}
```

---

## 阶段 3：成稿（一次确认）

### 3.1 最终设计稿生成

#### 分派给生图专家并行生成（强制执行）

分段 prompt 生成后，各段的成稿图**必须派给生图专家 subagent 并行生成**：

```bash
# 为每段并行 spawn design subagent（A/B/C/D 同时执行）
openclaw subagents spawn design "{品牌名} {产品名} 成稿 A 段" --timeout 600 &
openclaw subagents spawn design "{品牌名} {产品名} 成稿 B 段" --timeout 600 &
openclaw subagents spawn design "{品牌名} {产品名} 成稿 C 段" --timeout 600 &
openclaw subagents spawn design "{品牌名} {产品名} 成稿 D 段" --timeout 600 &
wait
```

每个 design subagent 的任务指令中必须包含：
- 该段的 prompt 文件路径（`设计/v1/prompt_{段}.txt`）
- 对应手稿切段图路径（`手稿/v1/cut_preview/segment_{段}_confirmed.png`）
- 全局风格指南路径（`style_guide.png`）
- 目标尺寸（默认 `768x1920`；用户明确要求高分辨率时可升高）
- 封闭边界规则

main 的职责：
- 先用 `create_design_segment_prompts.py` 生成所有段的 prompt
- 然后并行 spawn 多个 design subagent，每段一个
- 等待全部返回后，逐个做尺寸验证和边界检查
- 不能因为"子代理已返回"就视为合格，必须读回核验

**降级方案**：如果 subagent 平台不支持并行，或用户明确要求快速单段试验，可回退到 `bash scripts/generate_segment_batch.sh` 串行脚本，但必须在报告中说明这是降级路径。

#### 统一正式执行入口（强制执行）

手稿通过 QA 和切段确认后，后续成稿默认必须优先走统一批量脚本入口，不允许 main / subagent 临时手拼内联命令绕开：

```bash
python3 scripts/create_design_segment_prompts.py --project-dir {项目目录} --version v1
bash scripts/generate_segment_batch.sh --project-dir {项目目录} --version v1 --size 768x1920
```

统一入口必须承担以下门禁职责：
- 重新读取 `facts.json`、`asset_registry.json`、`platform_profile.json`、`category_profile.json`
- 重新读取 `style_guide.png`、`策划/strategy_v1.md`、`策划/copywriting_v1.md`
- 重新读取 `策划/prompt_package/design_segment_base.txt`、`策划/prompt_package/wireframe_base.txt`
- 检查 `cut_manifest.json` 存在且 `status=confirmed`
- 仅消费 `segment_*_confirmed.png` 这类正式确认段图；缺失即失败
- 参考图角色必须来自 `asset_registry.json`，不得靠猜文件名临时兜底
- `prompt_*.txt` 必须由正式脚本生成，不得默认由 main / subagent 手写临时 prompt 代替

只有当用户明确要求临时实验、单段试跑或脱离正式链路排障时，才允许偏离该入口，并且必须显式说明这是非标准路径。

#### 总原则
- 不要默认直接生成完整超长图
- 优先根据已确认的连续段来生成
- 不要把手稿当精确版式模板硬锁，手稿适合当结构参考

#### 封闭边界硬拼接（强制执行）

**核心原则**：每一段必须是**完整的独立设计块**，上下边界都做完整收口，可直接垂直堆叠。

每段生成时必须包含：
- **顶部边界**：完整的色带（40-60px 高度）+ 装饰元素，风格继承 `style_guide.png`
- **底部边界**：完整的色带（40-60px 高度）+ 装饰元素，风格继承 `style_guide.png`
  - 例外：最后一段底部需要完整的页面结束设计（Footer）

**Prompt 模板**（必须注入）：
```
IMPORTANT: This segment must be a COMPLETE INDEPENDENT DESIGN BLOCK with FULL TOP AND BOTTOM BOUNDARY DESIGN.
【Top boundary】Complete finished design with a color band matching the project style guide (40-60px height), with subtle decorative elements consistent with the overall design language.
【Bottom boundary】COMPLETE FINISHED DESIGN with a color band matching the project style guide (40-60px height), with subtle decorative elements consistent with the overall design language.
This segment should look like a complete standalone card/module, ready for hard stacking.
```

最后一段额外添加：
```
【Final segment】Bottom has complete page ending with footer elements, full page closing design.
```

#### 参考图注入规则（强制）
每一段生成时，必须注入以下参考图（顺序优先级）：

1. `--ref-style {项目目录}/style_guide.png`（全局风格指南）— **必须有**
2. `--ref-product`（产品图）— **强烈建议有**
3. `--ref-logo`（品牌 LOGO）— 如有则注入

**超时处理规则**：
- 复杂 prompt + 多张参考图容易触发 600s 超时
- 遇到超时：简化 prompt，减少参考图数量（优先保留 style_guide + 产品图）
- 先用简化版验证布局可行，再逐步增加参考图

#### 端点规则
- **统一使用端点**：`n.lconai.com`，模型 `gpt-image-2-pro`
- 最长边 ≤ 3840
- 宽高需可被 16 整除
- 最大宽高比 ≤ 3:1

每次生成前必须执行 `scripts/validate_dimensions.py` 验证尺寸。

#### 生成命令
```bash
python {gpt-image2-gen}/scripts/generate.py --prompt-file {项目目录}/设计/v1/prompt_A.txt --ref-wireframe {项目目录}/手稿/v1/cut_preview/segment_A_confirmed.png --size 768x1920 --ref-style {项目目录}/style_guide.png --ref-product {项目目录}/参考/product_main.jpg --output {项目目录}/设计/v1/segment_A.png
```

### 3.2 拼接交付

#### 分段边界检查（强制执行）

所有最终分段生成后，必须先检查拼接就绪状态：

```bash
python scripts/validate_segment_boundaries.py {项目目录}/设计/v1/segment_1.png {项目目录}/设计/v1/segment_2.png {项目目录}/设计/v1/segment_3.png {项目目录}/设计/v1/segment_4.png --report {项目目录}/设计/v1/boundary_check_report.json
```

检查重点：
- 分段宽度一致
- 每段为完整独立设计块
- 顶部/底部有完整收边，不需要 blend、crop 或颜色校正
- 最后一段有完整页面结束设计

#### 封闭边界硬拼接（唯一方法）

边界检查通过后，所有段直接垂直堆叠，无需 blend、无需 crop、无需颜色校正：

```bash
python scripts/hard_concat.py {项目目录}/设计/v1/merged_final.png {项目目录}/设计/v1/segment_1.png {项目目录}/设计/v1/segment_2.png {项目目录}/设计/v1/segment_3.png {项目目录}/设计/v1/segment_4.png
```

**原理**：
- 每段上下边界已做完整收口（奶油色色带 + 金色装饰）
- 直接垂直堆叠即可形成连贯视觉流
- 无需额外 blend/crop/color correction

**代码示例**：
```python
from PIL import Image
import sys

# 纯硬拼接：直接垂直堆叠
images = [Image.open(p).convert('RGB') for p in sys.argv[2:]]
w = images[0].width
total_h = sum(img.height for img in images)
result = Image.new('RGB', (w, total_h), (255, 255, 255))
y = 0
for img in images:
    result.paste(img, (0, y))
    y += img.height
result.save(sys.argv[1], quality=95)
```

### 3.3 确认点 3

```bash
python scripts/project_manager.py update-phase design --project-dir {项目目录}
python scripts/project_manager.py feishu-report --phase 3 --project-dir {项目目录}
```

用户看最终拼接长图，确认或反馈。

---

## 阶段 4：飞书交付（强制执行）

详情页拼接长图通常超过飞书单张图片限制，必须打包交付。最终交付不是简单压缩，而是“检核 → 打包 → 发送 → 用户确认结束 → 归档整理”的闭环。

### 4.1 交付规则

| 场景 | 处理方式 |
|------|----------|
| 图片 ≤ 10MB | 仅限中途评审时可作为图片发送；最终交付不走图片直发 |
| 图片 > 10MB | 禁止直接发图，必须作为文件或进入 ZIP |
| 拼接长图 + 分段图 + 头图 | 打包成 ZIP 压缩包，保留高清无损 PNG |
| 压缩包 ≤ 30MB | 直接通过飞书发送文件 |
| 压缩包 > 30MB | 分卷压缩（每卷 28MB，预留余量），分多个文件发送 |

最终图不做二次压缩，不为发送便利降低图片质量；只通过 ZIP/分卷解决飞书限制。

### 4.1.1 交付前检核（强制执行）

打包前必须运行：

```bash
python scripts/validate_delivery.py --project-dir {项目目录}
```

检核内容：
- 是否有完整拼接长图 `merged_final.png`
- 是否有最终分段高清图 `segment_*.png`
- 是否有头图 `head_*.png`（默认必检；仅当用户明确说本项目不要头图时可跳过）
- 是否有 `facts.json`、`asset_registry.json`、平台/品类 profile 快照
- 是否有策略/文案文件
- 是否存在超过 10MB 的图片，提醒不能直接发图

如缺少关键交付物，必须主动提醒用户：等待补齐、重新执行，还是按现状交付。

### 4.2 分卷压缩命令

```bash
# 使用 zip 分卷压缩（每卷 28MB，预留 2MB 余量）
zip -s 28m output.zip segment_A.png segment_B.png segment_C.png segment_D.png merged_final.png

# 生成的文件：
# output.zip (第一个分卷)
# output.z01 (第二个分卷)
# output.z02 (第三个分卷)
# ...
```

### 4.3 交付流程脚本

使用 `scripts/deliver_package.sh` 自动处理：

```bash
bash scripts/deliver_package.sh --project-dir {项目目录} --output-dir {项目目录}/交付
```

脚本自动执行：
1. 检查文件总大小
2. 决定是否需要分卷
3. 生成压缩包或分卷文件
4. 输出到 `交付/` 目录
5. 返回文件列表供飞书发送

### 4.4 飞书发送

压缩包生成后，通过飞书发送文件：

```bash
# 将压缩包复制到飞书交付目录
cp {项目目录}/交付/*.zip /Users/a123/.openclaw/workspace/feishu-deliver/
cp {项目目录}/交付/*.z01 /Users/a123/.openclaw/workspace/feishu-deliver/  # 如有分卷

# 使用飞书发文件能力发送
```

注意：
- 中途让用户看效果时，可以发图片。
- **最终整套交付时，不管单张图是否小于 10MB，都不要直接发 `merged_final.png`、`segment_*.png`、`head_*.png`。**
- 最终整套交付必须以 ZIP/分卷文件为准。

### 4.5 交付物清单

最终交付必须包含：

| 文件 | 说明 |
|------|------|
| `merged_final.png` | 完整拼接长图（本地保留） |
| `segment_A/B/C/D.png` | 各段独立设计稿（本地保留） |
| `{项目名}_交付.zip` 或 `{项目名}_交付.z01/.z02/...` | 飞书发送的压缩包/分卷 |

### 4.6 禁止行为

- **禁止直接发超过 10MB 的图片**：飞书图片限制会失败
- **禁止直接发拼接长图**：超长图无法通过飞书单张发送
- **禁止只发单段不发包**：用户需要完整交付物
- **禁止压缩包超过 30MB 直接发**：会被飞书拒绝
- **禁止不发分卷的后续卷**：用户无法完整解压
- **禁止打包未确认稿/过程稿/失败稿**：最终交付只能包含用户确认过的最终稿
- **禁止在用户确认项目前清理过程稿**：必须先完成交付并征询用户是否结束项目

### 4.7 项目结束与归档

用户收到交付文件后，必须询问是否结束项目。用户确认结束后，才可执行整理：

```bash
python scripts/archive_project.py --project-dir {项目目录}
```

整理原则：
- 保留最终长图、最终分段图、最终头图、交付包、交付清单
- 保留 `facts.json`、`asset_registry.json`、平台/品类 profile、核心策略/文案
- 过程稿移动到 `过程稿归档/`，不要直接删除
- 按项目名和日期归档，便于未来检索

---

## 项目文件管理规范

### 目录结构

```
outputs/{项目名}_{日期}/
├── progress.json             # 状态看板（始终唯一）
├── facts.json                # 产品事实锁定
├── style_guide.png           # 全局风格指南
├── 策划/
│   ├── strategy_v1.md
│   └── copywriting_v1.md
├── 手稿/
│   ├── v1/
│   │   └── wireframe_all.png  # 单张 4 列方形画板
│   └── v2/
│       └── wireframe_all.png  # 修改后
├── 设计/
│   └── v1/
│       ├── segment_1.png
│       ├── segment_2.png
│       └── merged_final.png  # 拼接长图
└── 参考/
    └── user_style.png
```

### 文件管理命令

```bash
# 存入文件
python scripts/project_manager.py put 手稿 A --file wireframe_all.png --project-dir {项目目录}

# 更新状态
python scripts/project_manager.py status A approved --project-dir {项目目录}

# 查看当前状态
python scripts/project_manager.py report --project-dir {项目目录}
```

---



## gpt-image-2-pro 能力边界与调用效率（强制参考）

详情页 skill 是编排型 skill，内部嵌套调用 `/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py`。在正式项目开始前，如模型、网关或 endpoint 有变化，应运行能力探测：

```bash
python scripts/probe_gpt_image2_capabilities.py --output-dir {项目目录}/能力探测 --mode quick --timeout 600
```

已实测 quick 结果（2026-05-01）：
- `720x720` 失败：低于当前 gpt-image-2-pro 最小像素预算。
- `1440x1440` 成功：方图/头图默认应优先使用 1440x1440 或更高。
- `1440x2560` 成功：适合 9:16 竖图。
- `1280x3840` 成功：1:3 极限长边可用，但耗时更长。
- 4000 字 prompt 成功，但耗时明显增加。
- 1 张和 3 张参考图成功；追加实测 4、5、6 张参考图也成功。

调用建议：
1. 头图/KV 不再默认 800x800，应使用 1440x1440；如平台要求 800x800，先生成 1440x1440 高清图，再按需另行导出。
2. 详情页分段默认使用 `768x1920` 这类低于 2K、可被 16 整除且比例 ≤ 3:1 的尺寸；用户明确要求高分辨率时才升高。
3. 不要使用 720x720、800x800 直接调用 gpt-image-2-pro。
4. prompt 超过 1000 字必须写入 `--prompt-file`，不要内联。
5. 参考图数量越多越慢；默认稳定档保留 `style_guide + product`，增强档用 3 张，4-6 张只在复杂商品、规格确认、包装/套装、需要 logo 锁定时使用，并必须标明每张图角色。
6. 看到 “Invalid size ... below minimum pixel budget” 时，不要重试同尺寸，直接升到 1440x1440 或等比例更大尺寸。
7. 看到长耗时或超时，先减少参考图数量，再缩短 prompt，最后降低尺寸；不要先牺牲已确认的产品事实或风格指南。

能力报告输出：
- `gpt_image2_capability_report.json`
- `gpt_image2_capability_report.md`
- `gpt_image2_prompt_length_report.json`
- `gpt_image2_prompt_length_report.md`

### Prompt 长度实测规则

已实测 prompt 长度（2026-05-01）：
- 4000 字符成功，返回 1440x1440。
- 8000 字符成功，返回 1440x1440。
- 12000 字符成功，返回 1440x1440。
- 20000 字符成功，返回 1440x1440。

生产建议：
- 500–1500 字：默认稳定档，适合头图和简单段。
- 1500–4000 字：复杂段稳定档。
- 4000–8000 字：谨慎档，适合复杂详情页分段。
- 8000–12000 字：仅在结构很复杂且已经模块化时使用。
- 12000–20000 字：能力边界已实测通过，但不建议常规使用，应拆为分段 prompt。
- 所有超过 1000 字的 prompt 必须使用 `--prompt-file`。
- 不以“行数”作为规则，以字符数、耗时和实测成功率作为规则。

后续如果网关能力变化，以最新能力报告为准。


## 命令构造规则（强制执行）

网关 exec preflight 安全检查会拒绝复杂命令，必须遵守以下规则：

### 允许的命令格式
- 直接执行：`python3 /path/to/script.py --arg1 val1 --arg2 val2`
- 单行命令：不带 `\` 换行、不带 `&&`、不带 `$(...)`、不带 `set -e`
- 脚本执行：`bash /path/to/script.sh`（脚本内容可以复杂）

### 禁止的命令格式
| 模式 | 示例 | 被拒绝原因 |
|------|------|-----------|
| 多行换行 `\` | `python3 script.py \`<br>`--arg1 val1 \` | 网关认为是"复杂命令" |
| Shell 变量替换 | `$(cat prompt.txt)` | 需要子shell执行 |
| 链式命令 `&&` | `mkdir -p dir && python3 script.py` | 多命令组合 |
| 前置 `set -e` | `set -e\nmkdir -p...` | shell内置命令 |
| 带 `export` | `export KEY=val && python3...` | 环境变量设置 |
| `cd` 前置 | `cd /path && python3...` | 目录切换 |

### 推荐做法

当需要多步操作（如创建目录 + 生成多段）时：

1. **先写 shell 脚本封装逻辑**
   ```bash
   #!/bin/bash
   set -euo pipefail
   mkdir -p /path/to/output
   python3 /path/to/generate.py --prompt "段A" -o /path/to/output/segment_A.png
   python3 /path/to/generate.py --prompt "段B" -o /path/to/output/segment_B.png
   ```

2. **执行脚本**
   ```bash
   bash /path/to/script.sh
   ```

3. **禁止先尝试复杂命令失败后再切脚本**，应该直接用脚本方式

### 错误信息识别

如果看到以下错误，说明命令被网关拒绝：
```
exec preflight: complex interpreter invocation detected; refusing to run without script preflight validation.
```

解决方案：把命令封装到 shell 脚本中，然后执行脚本。

---

## 不要做的事

1. 不问载体，直接按移动端开做
2. 不确认背景信息，就直接写策略
3. **策略/逐屏文案必须 spawn strategy subagent**，main 自己硬做是降级路径，只有 3 种降级条件满足时才允许
4. 一屏一张地切详情页
5. 6 段分开生成手稿（用单张方形画板 4 列纵向）
6. 一上来直接赌完整超长图
7. 把手稿当成精确版式模板强锁
8. 还没锁产品结构事实，就开始画产品
9. 拼接前不统一宽度
10. 为了迎合像素尺寸，破坏详情页纵向比例逻辑
11. 不通过 `validate_dimensions.py` 验证就手动换算像素
12. 在同一个 turn 内分多批发消息（回复原子性）
13. 使用 aixor 端点（已废弃，统一用 n.lconai.com）
14. 生成段落时不使用共享的风格指南
15. 手稿中使用 "Column 1/2/3/4" 等标注
16. 屏与屏之间画边框线或分隔线
17. 手稿用 × 占位或实心块代替产品轮廓
18. 手稿用"标题占位""卖点条"代替具体文案
19. **手稿画手机外框/刘海/状态栏 — 页面内容直接铺满画板**
20. **手稿添加屏数标注（"第1屏"、"Screen 1"、"1/11"等数字）— 不需要标注**
21. **生成段时使用"开放式边界"（上下边界不做收口）— 必须使用封闭边界**
22. **拼接时使用 blend/overlap/crop — 封闭边界硬拼接无需这些**
23. **注入过多参考图导致超时 — 复杂段优先保留 style_guide + 产品图**
24. **使用 smart_merge.py 或 merge_panels.py — 已废弃，改用 hard_concat.py**
25. **手稿图必须由 design subagent 生成**，main 直接调生图脚本是降级路径
26. **分段成稿图必须并行 spawn design subagent**，不得串行逐段生成拖慢整体进度

---

## 分辨率速查表

gpt-image-2-pro 支持的官方分辨率（长边 ≤ 3840，宽高比 ≤ 3:1，宽高可被 16 整除）：

| 预设名 | 尺寸 | 说明 |
|--------|------|------|
| `4k_1_1` | 2880x2880 | 最大方形（手稿画板） |
| `4k_16_9` | 3840x2160 | 最大横向 |
| `4k_9_16` | 2160x3840 | 最大纵向 |
| `fast_1_1` | 1920x1920 | 默认快速方形画板 |
| `2k_1_1` | 1440x1440 | 2K 方形（头图默认最小安全档） |
| `1k_1_1` | 720x720 | **当前 endpoint 实测不可用**，低于最小像素预算，请勿使用 |

**注意**：
- 头图生产默认最小安全档是 `1440x1440`（2K 方形），不是 `800x800` 或 `720x720`。
- `720x720` 虽是理论预设，但当前 endpoint 实测返回错误，标注在此仅作警示。
- 平台若要求 800x800，请先生成 1440x1440 高清图再缩放导出。

当前内置常用预设可通过 `--list-presets` 查看。

生图超时（600s）时属瞬态网络抖动，可重试。复杂 prompt + 2 张参考图 + 高分辨率时超时概率更高，建议先无参考图验证布局。
