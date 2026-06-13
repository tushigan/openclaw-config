---
name: brand-poster-creator
version: 3.0
description: "品牌海报全流程生成技能（含项目分级与审批流）。从需求收集、版式锁定、文案策划、生图到交付清理的全链路协调器，支持 B/A/S 三级项目管理、自动审批提醒、时间记录与复盘分析。触发词：品牌海报、海报生成、做张海报、节日海报、产品海报、春节海报、营销海报"
metadata:
  openclaw:
    requires:
      bins:
        - python3
    emoji: "🎨"
---

# Brand Poster Creator - 品牌海报全流程协调器

用于 `main` 子代理统一调度品牌海报从需求到交付的全流程。

## 记忆系统集成（必读）

⚠️ **生成品牌海报前，必须先查询品牌档案和资产**

### 查询品牌信息
```bash
# 1. 查询品牌档案（获取调性、定位、目标受众）
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 2. 查询品牌资产（获取 Logo、VI 手册、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json
```

### 关键信息提取
从品牌档案中提取：
- **品牌调性** (`brand_tone`) - 决定画面氛围和色彩情绪
- **定位** (`positioning`) - 决定视觉语言和风格层级
- **目标受众** (`target_audience`) - 决定画面语境和表达方式

从品牌资产中提取：
- **Logo 路径** (`logos[]`) - 用于 ref_order.json 的 logo 角色
- **VI 手册** (`vi_manual[]`) - 参考标准色、字体规范
- **参考图** (`reference_images[]`) - 风格参考或产品参考

### 海报生成流程集成
1. **Step 0（新增）**：查询品牌档案和资产
2. Step 1：飞书对话卡片收集需求
3. Step 2：检查蒸馏卡获取版式
4. Step 2.5：**优先使用记忆系统中的品牌资产**，再补充飞书云盘检索
5. 后续步骤按原流程执行

### 品牌一致性保障
- 画面风格必须符合品牌调性
- Logo 使用品牌资产库中的官方文件
- 色彩参考品牌 VI 规范
- 视觉语言匹配目标受众审美

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
Step 3.5：低清烘焙产品参考适配 → 原始产品图锁身份，可选质地参考锁组织；默认不生成中间 AI 产品图
Step 4：派发 strategy → copywriter subagents → 完成文案策略与具体文案
Step 5：回收文案 + 骨架图+坐标表 → 飞书对话卡片展示 → 用户确认/修改
Step 5.5：参考图风格提炼 → 输出 style_profile.json（有参考图时执行）
Step 5.8：基于已确认信息生成画面创意表达方案 → 用户确认/修改
Step 6：调用 prompt-assembler 组装完整 prompt
Step 7：派发 design subagent → 默认低于 2K 的快速生图；用户明确要求高清/4K 时才升高
Step 8：发送成品图 → 用户确认
Step 9：询问是否完成 → 是则清理项目目录中间文件
```

## 反例黑名单速查

以下动作一律不要做；命中任一项时停下，回到对应步骤修正。

| 场景 | 不要做 | 正确动作 |
|------|--------|----------|
| 素材角色 | 不要把风格参考图、Logo、IP、产品图混成普通参考图 | 写入 `brief.json.assets`，由 `assemble_prompt.py` 生成 `ref_order.json` |
| 风格参考 | 不要继承参考图中的非品牌人物、服装、脸型、身份或原剧情 | 只提炼画风、色彩、光感、动势，并写入 `content_do_not_inherit` |
| Logo/IP | 不要只在 prompt 里写“保留 Logo/IP”就直接生图 | `ref_order.json` 必须包含匹配路径的 `logo` / `ip` 角色 |
| Prompt | 不要手写、追加、拼接或临场改 `prompt_draft.md` | 只运行 `assemble_prompt.py`，失败就修脚本或素材数据 |
| Prompt 模式 | 不要把固定坐标和自由构图混成一套半硬半软提示词 | 有版式数据走固定版式坐标；无码版式数据走自由构图与阅读动线 |
| 生图入口 | 不要绕过 `execute_generation.py` 直接调用 `gpt-image2-gen` | 先固化 `prompt_draft.md`、`ref_order.json`、`run.sh`，再执行正式入口 |
| 多张出图 | 不要写多条 `generate.py` 顺序命令伪装并行 | 单 prompt 多张用 `execute_generation.py --count N`，由底层并行 fan-out |
| 多方向出图 | 不要手写 `prompt_A/B/C.txt` 或手动复制项目改状态 | 用户明确“三个都要/每个方向各出”时，运行 `split_direction_projects.py` 拆成多个独立项目 |
| Logo 验收 | 不要把 `ref_order.json` 含 `logo` 当成成品 Logo 正确 | `ref_order.json` 只证明已挂载；交付前必须视觉核验成品中的 Logo 是否接近官方文件 |
| 正式失败 | 不要用 Python/PIL/ImageMagick/本地贴图顶替正式海报 | 记录失败事实，修复 provider/权限/路径后重试 |
| 交付 | 不要回复 `MEDIA:`、本地路径或“图片在目录里”冒充发送 | 调用真实飞书图片发送工具，并记录 `messageId/chatId` |
| 清理 | 不要未确认就清理项目，也不要直接 `rm` | 用户确认后运行 `cleanup_project.py --confirmed` |

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

### 保护路径执行规则

OpenClaw 子 agent 若直接执行 `/Users/a123/.openclaw/skills/brand-poster-creator/scripts/*.py` 被保护路径策略拦截，必须在当前 workspace 写临时 launcher，用 `runpy.run_path` 调用原脚本；不得复制 skill 脚本、不得修改保护路径权限、不得把脚本搬到各 agent 工作区。

```bash
python3 - <<'EOF'
from pathlib import Path

launcher = Path("/Users/a123/.openclaw/workspace-design/_temp_brand_poster/run_skill_script.py")
launcher.parent.mkdir(parents=True, exist_ok=True)
launcher.write_text(
    "import runpy, sys\n"
    "sys.argv = ['project_manager.py', 'reconcile', '--project-dir', sys.argv[1]]\n"
    "runpy.run_path('/Users/a123/.openclaw/skills/brand-poster-creator/scripts/project_manager.py', run_name='__main__')\n",
    encoding="utf-8",
)
EOF

python3 /Users/a123/.openclaw/workspace-design/_temp_brand_poster/run_skill_script.py "[项目目录绝对路径]"
```

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
- 产品图片（上传；小尺寸产品图也可用，系统会自动启用产品保真与真实质感适配策略；如有高清图可补充，但不得把高清图作为继续生成的前置要求）

请逐项回复，或一次性提供完整信息。
```

### Step 1.1：项目分级与审批者确认

⚠️ **重要变更（v3.0）**：新增项目分级与审批流程

收集需求后，**必须先确认项目等级和审批者**，再继续后续流程。

#### 1.1.1 项目等级询问

向用户展示项目等级说明：

```markdown
📊 **项目等级确认**

请选择本次项目的等级：

| 等级 | 名称 | 审批者 | 适用场景 |
|------|------|--------|----------|
| **B级** | 日常项目 | 文案策划 + 设计师 | 常规海报、节日营销物料等日常需求 |
| **A级** | 重要项目 | 文案策划 + 设计师 + 创意总监 | 重要产品发布、品牌战役等需要总监审核的项目 |
| **S级** | 战略项目 | 文案策划 + 设计师 + 创意总监 + 老板 | 年度品牌战役、重大发布会等需要最高决策者审批的项目 |

请回复项目等级：B / A / S
```

用户回复后，记录等级到变量 `$PROJECT_GRADE`。

#### 1.1.2 审批者信息收集

根据用户选择的等级，**动态询问对应的审批者**：

**B级项目**：
```markdown
请提供以下审批者的姓名：
1. **文案策划判断者**：（负责文案策划审核）
2. **设计判断者**：（负责设计初稿审核）
```

**A级项目**：
```markdown
请提供以下审批者的姓名：
1. **文案策划判断者**：（负责文案策划审核）
2. **设计判断者**：（负责设计初稿审核）
3. **创意总监**：（负责创意方向二次审核）
```

**S级项目**：
```markdown
请提供以下审批者的姓名：
1. **文案策划判断者**：（负责文案策划审核）
2. **设计判断者**：（负责设计初稿审核）
3. **创意总监**：（负责创意方向二次审核）
4. **老板**：（负责最终决策）
```

用户回复后，**逐个查询飞书用户信息**：

```bash
# 对每个审批者，调用 feishu_search_user 工具查询 open_id
# 示例：查询"张三"
# 工具返回：{"name": "张三", "open_id": "ou_xxxxx"}
```

将查询结果组装成 JSON 格式：

```json
{
  "copywriter": {
    "name": "张三",
    "open_id": "ou_xxxxx"
  },
  "designer": {
    "name": "李四",
    "open_id": "ou_yyyyy"
  },
  "creative_director": {
    "name": "王五",
    "open_id": "ou_zzzzz"
  },
  "boss": {
    "name": "赵六",
    "open_id": "ou_wwwww"
  }
}
```

**注意**：
- B级项目只需要 `copywriter` 和 `designer`
- A级项目需要 `copywriter`、`designer`、`creative_director`
- S级项目需要全部四个角色

#### 1.1.3 初始化项目分级

收集完审批者信息后，运行初始化脚本：

```bash
# 将审批者信息保存到临时文件
reviewers_json='{"copywriter":{"name":"张三","open_id":"ou_xxx"},...}'

# 初始化项目分级
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  init \
  --project-dir "[项目目录绝对路径]" \
  --grade "$PROJECT_GRADE" \
  --reviewers-json "$reviewers_json"
```

脚本会创建 `project_grading.json` 文件，包含审批流程配置。

#### 1.1.4 初始化时间记录

同时初始化时间记录：

```bash
# 记录项目启动时间
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "intake" \
  --event-type "start" \
  --actor "human"
```

#### 1.1.5 向用户确认

展示确认信息：

```markdown
✅ **项目分级已确认**

- **项目等级**：B级 - 日常项目
- **审批流程**：
  1. 文案策划完成 → 张三 审核
  2. 设计初稿完成 → 李四 审核

系统将在关键节点自动艾特对应审批者，并记录审批时间。
```

### Step 1.2：收集需求信息

收到用户需求信息后，记录 intake 阶段完成时间：

```bash
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "intake" \
  --event-type "complete" \
  --actor "human"
```

然后将需求信息写入项目目录的 `brief.json` 文件，格式如下：

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
    "product": "images/product.jpg",
    "product_texture_refs": ["images/product_texture_ref_1.jpg"]
  }
}
```

### 项目目录结构

每个任务创建独立目录：

```
/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/
├── brief.json              # 需求信息
├── distill_card.json       # 蒸馏卡数据（如有）
├── copy_strategy.json      # strategy 产出的文案策略
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

3. 版式有效性分支：
   - 若 `layout_analysis.elements` 存在且至少包含 1 个有效区域，后续 prompt 进入固定版式坐标模式
   - 若蒸馏卡存在但 `layout_analysis.elements` 为空、缺失或全是无效元素，必须在 `distill_manifest.json` 记录 `layout_status="empty_elements"`，并在 `brief.json` 标记 `"distill_mode": "fallback"`；后续进入自由构图与阅读动线模式，不得伪造坐标
   - 若蒸馏卡 JSON 无法读取，停止当前阶段并展示错误；不得用手写坐标继续

### 无蒸馏卡 ID

在 `brief.json` 中标记 `"distill_mode": "fallback"`，后续进入降级组装流程（见 prompt-assembler.md 第六节）。

---

## Step 2.4：品牌档案查询（项目记忆系统集成）

根据 `brief.json` 中的 `brand_name`，查询是否已建立品牌档案。

### 目标

获取品牌基础信息、视觉规范、品牌素材路径等，优化后续素材检索和创意生成流程。

### 执行流程

1. 运行品牌档案查询脚本：

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/find_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "$(jq -r '.brand_name' brief.json)"
```

2. 脚本返回 JSON 格式：

```json
{
  "found": true,
  "profile_path": "/Users/a123/.openclaw/workspace/projects/品牌名称/_brand-profile.json",
  "profile": {
    "brand_name": "品牌名称",
    "industry": "行业",
    "core_values": ["价值观1", "价值观2"],
    "target_audience": "目标受众",
    "brand_story": "品牌故事",
    "visual_guidelines": {
      "primary_colors": ["#色值1", "#色值2"],
      "fonts": ["字体1", "字体2"],
      "logo_usage": "使用规范"
    },
    "brand_assets_path": "飞书云盘路径或本地路径",
    "tone_of_voice": "品牌语气"
  }
}
```

### 结果处理

#### 情况 A：找到品牌档案（found = true）

1. 记录品牌档案信息到项目状态：
   - 将 `profile` 写入项目目录的 `brand_profile_cache.json`
   - 在 `project_state.json` 中标记 `"brand_profile_found": true`

2. 提取关键信息用于后续流程：
   - **视觉规范**：`visual_guidelines.primary_colors`（用于 prompt 生成的色彩约束）
   - **品牌素材路径**：`brand_assets_path`（用于 Step 2.5 素材检索优先路径）
   - **品牌价值观**：`core_values`（用于 Step 3 文案创意方向）
   - **品牌语气**：`tone_of_voice`（用于文案风格）

3. 向用户告知：
   ```
   ✅ 已找到品牌档案
   - 品牌主色：[列出 primary_colors]
   - 品牌素材路径：[brand_assets_path]
   - 将优先使用品牌档案中的视觉规范和素材路径
   ```

#### 情况 B：未找到品牌档案（found = false）

**新增：自动建档流程**

1. 从 `brief.json` 提取可用的品牌信息：

```bash
# 提取品牌信息
brand_info=$(jq '{
  brand_name: .brand_name,
  industry: .industry,
  target_audience: (.target_audience // ""),
  core_values: (if .core_message then [.core_message] else [] end),
  brand_tone: (.brand_tone // "")
}' brief.json)
```

2. **暂停任务，询问用户是否创建品牌档案**：

向用户展示提取的信息，提供两个选项：

```markdown
🆕 检测到新品牌"XX"，是否创建品牌档案？

当前已知信息：
- 品牌名称：XX
- 行业/品类：[从 brief.json.industry 提取]
- 目标受众：[从 brief.json.target_audience 提取]
- 核心信息：[从 brief.json.core_message 提取]

创建品牌档案的好处：
✅ 后续项目可复用品牌信息（视觉规范、品牌调性、素材路径）
✅ 确保品牌输出物的一致性
✅ 减少重复填写信息的工作量

选项：
1. **创建档案并继续**（推荐：适合长期合作品牌）
2. **仅本次使用，不建档**（适合一次性项目或测试）
```

3. **用户选择"创建档案并继续"**：

调用 `init_agency_project.py` 创建品牌档案：

```bash
# 解析 brand_info 中的各字段
brand_name=$(echo "$brand_info" | jq -r '.brand_name')
industry=$(echo "$brand_info" | jq -r '.industry // ""')
target_audience=$(echo "$brand_info" | jq -r '.target_audience // ""')
core_values=$(echo "$brand_info" | jq -r '.core_values | join(",")')

# 创建品牌档案和项目
python3 /Users/a123/.openclaw/skills/boss/scripts/init_agency_project.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "$brand_name" \
  --campaign-name "海报项目_$(date +%Y%m%d)" \
  --campaign-type "poster" \
  --industry "$industry" \
  --target-audience "$target_audience" \
  --core-values "$core_values"
```

创建成功后：
- 在 `project_state.json` 中标记 `"brand_profile_found": true`
- 将档案信息写入 `brand_profile_cache.json`
- 向用户确认：
  ```
  ✅ 品牌档案已创建
  - 档案位置：/Users/a123/.openclaw/workspace/projects/XX/_brand-profile.json
  - 已记录品牌信息，后续项目将自动复用
  ```

4. **用户选择"仅本次使用，不建档"**：

- 在 `project_state.json` 中标记 `"brand_profile_found": false`
- 继续执行后续流程（Step 2.5 飞书云盘素材搜索）
- 向用户告知：
  ```
  ℹ️ 品牌未建档，将使用通用流程
  - 将从飞书云盘搜索品牌素材
  - 下次执行相同品牌任务时，仍会提示是否建档
  ```

**新增：冲突检测流程（品牌档案已存在时）**

在 **情况 A：找到品牌档案** 的步骤 1 之后，新增以下步骤：

1.5. **检测品牌信息冲突**：

```bash
# 从 brief.json 提取新信息
new_info=$(jq '{
  industry: .industry,
  target_audience: (.target_audience // ""),
  core_values: (if .core_message then [.core_message] else [] end),
  brand_tone: (.brand_tone // "")
}' brief.json)

# 检测冲突
conflicts=$(python3 /Users/a123/.openclaw/skills/boss/scripts/detect_brand_conflicts.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "$(jq -r '.brand_name' brief.json)" \
  --new-info "$new_info")

has_conflict=$(echo "$conflicts" | jq -r '.has_conflict')
```

1.6. **处理高严重性冲突**：

如果 `has_conflict = true`，提取冲突详情并**暂停任务**：

```bash
high_conflicts=$(echo "$conflicts" | jq '[.conflicts[] | select(.severity == "high")]')
conflict_count=$(echo "$high_conflicts" | jq 'length')

if [ "$conflict_count" -gt 0 ]; then
  # 向用户展示冲突
  echo "$high_conflicts" | jq -r '.[] | "⚠️ 冲突字段：\(.field)\n档案记录：\(.archived)\n当前输入：\(.new_input)\n"'
fi
```

向用户展示冲突并提供选项：

```markdown
⚠️ 品牌信息冲突检测

检测到以下冲突：

**字段：行业**
- 档案记录：烘焙
- 当前输入：餐饮

如何处理？
1. **使用档案记录**（烘焙）- 保持品牌一致性
2. **更新档案为新信息**（餐饮）- 档案可能过时，需更新
3. **仅本次使用新信息，不更新档案** - 临时偏差，档案不变
```

根据用户选择执行：

**选项 1：使用档案记录**
- 使用档案中的值继续执行
- 不更新档案

**选项 2：更新档案为新信息**
```bash
# 更新档案
python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "$brand_name" \
  --field "industry" \
  --value "餐饮" \
  --operation replace
```

**选项 3：仅本次使用新信息**
- 使用新值继续执行
- 不更新档案

1.7. **自动合并低严重性补充信息**：

```bash
supplements=$(echo "$conflicts" | jq -r '.supplements')
supplement_count=$(echo "$supplements" | jq 'length')

if [ "$supplement_count" -gt 0 ]; then
  # 自动合并补充信息
  echo "$supplements" | jq -c '.[]' | while read -r item; do
    field=$(echo "$item" | jq -r '.field')
    new_value=$(echo "$item" | jq -c '.new_input')
    
    # 调用更新脚本（append 操作）
    python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py \
      --workspace-root /Users/a123/.openclaw/workspace \
      --brand-name "$brand_name" \
      --field "$field" \
      --value "$new_value" \
      --operation append
  done
  
  # 记录补充信息，任务结束后通知用户
  echo "$supplements" | jq -r '.[] | "- \(.field): 新增 \(.new_input | tostring)"' > supplement_log.txt
fi
```

任务结束后，向用户通知补充信息：

```markdown
✅ 已补充品牌档案：
- 核心价值观：新增"用心品质"、"匠心传承"
- 目标受众：扩展为"25-45岁女性"
```

### 降级策略

- 品牌未建档时，**不影响后续流程**
- Step 2.5 仍然执行飞书云盘素材搜索
- 若 Step 2.5 也未找到素材，走现有的 `manager.skip_stage()` 流程

### 与 Step 2.5 的协作

- 若品牌档案中有 `brand_assets_path`（飞书云盘路径），Step 2.5 优先在该路径下搜索
- 若品牌档案中的路径无效或未找到素材，Step 2.5 回退到默认根目录搜索

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
- 对小尺寸产品图输出 `quality_warnings`，但不把它当作信息缺口或阻塞条件
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

**小尺寸产品图处理规则**：
- 产品图存在但短边 < 900px 时，不得回退成“必须补高清图”。
- `check_brief_gaps.py` 只记录质量提醒：该图用于锁定产品身份、轮廓、配色、基础材质，不把压缩像素当作微观纹理依据。
- 后续 `assemble_prompt.py` 必须自动加入“小尺寸产品参考图适配策略”。若用户提供 `assets.product_texture_refs`，优先使用“原始产品图锁身份 + 质地参考锁组织”；没有质地参考且压缩纹理风险明显时，才使用低频软代理图降低噪点影响。
- 只有产品图完全缺失，或产品身份无法判断时，才向用户索要补充素材。

---

## Step 3.5：低清烘焙产品参考适配

只有同时满足以下条件时，才启用烘焙产品参考适配：
- 海报类型是产品推广/产品海报，且 `brief.json.product_name` 存在
- 产品属于面包/吐司/糕点/烘焙类
- 产品图存在但短边 < 900px，或用户明确反馈切面有木屑感、鳞片感、干硬、过锐化、孔洞过均匀等问题

默认策略改为“身份与质地分离”，不再生成中间 AI 产品 hero 参考：
- `brief.json.assets.product` 保留用户原始产品图，用于锁定产品身份、圆顶轮廓、可可色相、整体比例和品牌/包装关系。
- 如果用户提供真实质地/切面参考，写入 `brief.json.assets.product_texture_refs`，用于锁定面包组织的柔软度、湿润感、孔隙尺度、低局部对比和非均匀分布。
- 有 `product_texture_refs` 时，跳过低频软代理，不运行任何“产品 hero 参考生成”；后续 prompt 直接把“原始产品图 + 质地参考图”作为两个不同角色传入。
- 不得要求用户必须补高清产品图才能继续；小图是质量风险，不是流程阻塞。

只有在没有可用质地参考、且低清产品图明显会把压缩噪点/暗斑误读成孔洞时，才运行低频软代理作为降级适配：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/normalize_product_reference.py \
  --project-dir "[项目目录绝对路径]"
```

软代理脚本会自动：
- 读取 `brief.json.assets.product`
- 判断产品图尺寸与烘焙品类
- 先保留产品身份、轮廓、配色与基础材质，再用确定性图像处理生成低频软代理图，避免把低清暗斑/压缩噪点直接放大成蜂窝、木屑或鳞片纹理
- 将结果压缩为轻量 JPEG，写入 `images/product_realism_ref.jpg`
- 保留原始产品图到 `brief.json.assets.product_original`
- 将 `brief.json.assets.product` 更新为软代理图，供后续 prompt 与生图使用
- 写入 `product_reference_manifest.json` 与 `audit_log.jsonl`

**硬门禁**：
- 低清烘焙产品不得由 agent 手写 `product_realize_prompt.txt`、临时生成 `product_realized.png` 后直接塞回 `brief.json.assets.product`
- 若存在 `assets.product_texture_refs`，`assemble_prompt.py` 必须跳过低清门禁，并在 prompt 中写明“产品身份与质地参考分离”
- 若没有 `assets.product_texture_refs` 且产品图低清，必须以 `normalize_product_reference.py` 为标准入口，生成 `product_reference_manifest.json` 与对应 `brief.json.assets.product_normalization` 记录
- `assemble_prompt.py` 会检查该门禁；低清烘焙产品既没有质地参考、也没有标准软代理 manifest 时，会直接失败，要求先回到 Step 3.5
- 默认不得调用生图 API 生成 `product_bakery_hero_ref.png`、`product_realized.png` 或其它中间 AI 产品图；除非用户明确要求做实验对比，否则该路线不进入正式工作流

失败处理：
- 如果已有真实质地参考，直接继续 prompt 组装。
- 如果没有质地参考且软代理生成失败，不阻塞主流程，但必须记录质量风险；不得向用户声称烘焙质感问题已经被彻底解决。
- 不得因此要求用户必须补高清产品图。

跳过规则：
- 非产品推广/产品海报场景：跳过。
- 非烘焙/面包/吐司/糕点品类：跳过。
- 产品图尺寸足够且用户未反馈组织质感问题：跳过。
- 已提供 `assets.product_texture_refs`：跳过软代理与任何中间 AI 产品图。
- 除非用户明确要求实验对比，不得为其它品类生成烘焙适配产品参考。

---

## Step 4：派发 strategy → copywriter 完成文案策划

文案阶段必须分两段执行：
1. `strategy` 负责传播策略、卖点排序、文案框架，不直接写最终 `copywriting.json`
2. `copywriter` 负责标题、副标题、区域文案、多版本表达，并写入最终 `copywriting.json`

### 4.1 派发 strategy：产出文案策略

```json
{
  "runtime": "subagent",
  "agentId": "strategy",
  "task": "海报文案策略任务（见下方模板）",
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
| `model` | 留空 `""` 或填白名单内模型 | 白名单：`huoshan/kimi-k2.5`、`huoshan/kimi-k2.6`、`newapi_channel_conn/gpt-5.4`、`newapi_channel_conn/gpt-5.5`、`zhichuang/claude-opus-4-6`。留空则由目标 agent 使用自身默认模型。**禁止**使用非白名单 provider（如 `aliyun-bailian/kimi-k2.5`） |
| `attachments` | **不要传** | 附件通道未开启（`sessions_spawn.attachments.enabled` 默认 false），传 attachments 会报 `forbidden` 错误。改为在 task 描述中指定文件绝对路径，让子 agent 自行读取 |

### 给 strategy 的任务描述模板

```
你是品牌策略专家，需要为以下海报制定文案策略。不要写最终文案。

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
输出文案策略，不写最终文案。必须包含：
1. 核心传播主张
2. 卖点优先级
3. 标题/副标题/辅助文案的语气和长度建议
4. 每个蒸馏卡文案区域的表达任务
5. 禁止使用的表达方向

将结果写入：/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copy_strategy.json

格式：
{
  "core_message": "核心传播主张",
  "selling_points_priority": ["卖点1", "卖点2"],
  "tone": "语气",
  "area_guidance": {
    "el-5": { "role": "主标题", "task": "表达任务", "length_hint": "8-12字" },
    "el-7": { "role": "副标题", "task": "表达任务", "length_hint": "12-18字" }
  },
  "must_avoid": ["禁止表达1", "禁止表达2"]
}

完成后只回传：`copy_strategy.json` 路径 + 一句话策略摘要。
```

### 4.2 派发 copywriter：产出最终文案

strategy 完成后，main 必须确认 `copy_strategy.json` 存在，再派发 `copywriter` 子代理：

```json
{
  "runtime": "subagent",
  "agentId": "copywriter",
  "task": "海报最终文案撰写任务（见下方模板）",
  "mode": "run",
  "timeoutSeconds": 600,
  "runTimeoutSeconds": 600,
  "lightContext": true,
  "thinking": "low",
  "model": ""
}
```

**给 copywriter 的任务描述模板：**

```
你是文案策划专家，需要基于策略文件为海报写最终可上画面的文案。

**先读取以下项目文件，不要凭空编造：**
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/brief.json
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copy_strategy.json
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copy_brief_for_strategy.json（如存在）

## 输出要求
按蒸馏卡文案区域逐一输出最终文案。每个区域必须包含：
1. 文案内容（具体中文文字，可直接上画面）
2. 字体风格建议
3. 对应蒸馏卡元素 ID

将结果写入：/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copywriting.json

格式：
{
  "el-5": { "文案": "把团圆装进礼盒", "字体风格": "大气端庄" },
  "el-7": { "文案": "新年·心意到家", "字体风格": "细体" }
}

完成后只回传：`copywriting.json` 路径 + 一句话文案策略说明。
```

**禁止行为**：
- 不得跳过 `strategy` 直接让 `copywriter` 凭空写
- 不得让 `strategy` 直接写最终 `copywriting.json`
- 不得让 main 手写最终文案顶替 copywriter
- 不得在 `copy_strategy.json` 缺失时进入 Step 5

### 文案结果统一落盘

copywriter 子代理写完 `copywriting.json` 后，main 必须继续运行：

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

回收 copywriter 产出的文案，结合蒸馏卡的版式数据，以飞书对话卡片形式展示给用户确认：

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

### Step 5.1：请求文案审批（新增 v3.0）

文案展示给用户后，**立即触发审批流程**：

```bash
# 1. 记录 AI 文案生成完成时间
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "copywriting" \
  --event-type "complete" \
  --actor "ai"

# 2. 请求文案审批
approval_request=$(python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "copywriting" \
  --artifact "copywriting.json")

# 3. 提取艾特消息
mention_message=$(echo "$approval_request" | jq -r '.message')
```

向用户发送审批请求：

```markdown
✅ **文案策划完成**

[展示文案内容]

$mention_message

请审核确认：
- 回复「通过」→ 文案审批通过，进入设计阶段
- 回复「修改：[具体要求]」→ 需要修改文案
- 回复「拒绝：[原因]」→ 终止项目
```

### Step 5.2：记录审批响应

**等待文案判断者回复**。收到回复后，记录审批结果：

```bash
# 根据用户回复，判断决策类型
# "通过" → approved
# "修改：xxx" → revision_needed
# "拒绝：xxx" → rejected

# 记录审批响应
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "copywriting" \
  --decision "approved" \
  --feedback "文案符合品牌调性"

# 记录人工审核完成时间
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "copywriting" \
  --event-type "complete" \
  --actor "human"
```

**处理不同的审批结果**：

1. **approved（通过）**：继续进入 Step 5.5 风格提炼
2. **revision_needed（需要修改）**：
   - 记录反馈意见
   - 重新修改 `copywriting.json`
   - 重新运行 `process_copywriting.py`
   - 再次请求审批（回到 Step 5.1）
3. **rejected（拒绝）**：
   - 记录拒绝原因
   - 终止项目
   - 生成复盘报告

### 🔴 CHECKPOINT · STOP：文案审批门禁

**未通过文案审批前，禁止进入 Step 5.5（风格提炼）或 Step 5.8（创意表达）。**

确认条件：
- `project_grading.json` 中 `copywriting` 节点的 `status` 必须为 `approved`
- 或用户在超时后选择继续（仅B级项目）

**禁止行为**：
- 自动假设用户已确认
- 沉默视为同意
- 绕过审批流程直接进入下一步
- 在审批状态为 `waiting` 或 `pending` 时继续执行后续步骤

### 用户确认后的文件处理

- 回复「确认文案」：`copywriting.json` 保留并进入后续风格提炼 / 创意表达
- 回复「修改文案：[具体要求]」：更新文案后重新运行 `process_copywriting.py`
- 文案阶段结束后必须先落盘，再进入下一步

### 多方向都要出图时的拆分入口

如果 `copywriting.json` 是多方案结构（包含 `options` 数组），且用户明确回复「三个都要」「每个方向各出」「A/B/C 都生成」「每个方案各 N 张」，不得在同一个项目里手写多份 prompt 或手动复制目录。

必须先运行：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/split_direction_projects.py \
  --project-dir "[项目目录绝对路径]"
```

脚本会自动产出：
- `[任务ID]-A`、`[任务ID]-B`、`[任务ID]-C` 等独立项目目录
- 每个子项目自己的 `brief.json`、`copywriting.json`、`selected_direction.json`
- 父项目的 `direction_split_manifest.json`
- 子项目已修复/规范化的 `project_state.json`

拆分后，每个子项目从 Step 5.5 / Step 5.8 继续；如果用户要求每个方向各出 `N` 张，则每个子项目的 `run.sh` 都写入同一个 `--count N`。这些子项目可以并行派发给 design agent 执行，但每个子项目内部仍必须通过 `assemble_prompt.py` 和 `execute_generation.py`。

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
- 若风格参考图里出现非品牌人物、学生、模特、卡通角色或与品牌 IP 冲突的角色形象，必须写入 `content_do_not_inherit`，并在后续创意与 prompt 中明确“只继承画风/色彩/动势，不继承参考图人物、服装、脸型、身份”。
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

### 🔴 CHECKPOINT · STOP：创意确认门禁（保留原有逻辑）

**未得到用户明确确认前，禁止进入 Step 6（prompt 组装）。**

注意：创意方向确认不触发审批流程，仍由对话中的用户直接确认。审批流程只在**设计成品完成后**触发（见 Step 7.5）。

确认方式：
- 用户回复「确认创意」或「OK」或「可以」或「没问题」
- 或用户提出具体修改要求后再次确认

**禁止行为**：
- 自动假设用户已确认
- 沉默视为同意
- 直接进入下一步
- 在用户未回复时继续执行后续步骤

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
`--creative-direction` 在用户已确认画面创意表达方案后为必传参数，不得跳过。

脚本自动完成：
1. 读取 brief.json + distill_card.json + copywriting.json + creative_direction.json（如有）
2. 按规则程序化组装 prompt（参考图排序：风格→骨架→产品→IP→Logo）
3. 内置校验：检查无工作流术语、坐标覆盖率、文案覆盖率、参考图角色挂载是否冲突、创意表达是否缺失主视觉锚点
4. 输出 prompt_draft.md 与 ref_order.json

### Step 6.1：Prompt 版式模式

`assemble_prompt.py` 必须根据是否存在有效版式元素选择不同 layout adapter：

**A. 固定版式坐标模式**
- 触发条件：`distill_card.json.layout_analysis.elements` 存在有效元素。
- prompt 中使用 `== 画面布局（固定版式坐标） ==`。
- 每个区域必须输出 `x / y / 宽 / 高 / z`，并绑定区域角色、文案或素材。
- 用户确认的文案必须落到对应区域；缺失则阻塞。
- 模型只在固定区域内做视觉表达，不得自行重排。

**B. 自由构图与阅读动线模式**
- 触发条件：没有有效版式元素。
- prompt 中使用 `== 画面布局（自由构图与阅读动线） ==`。
- 不得生成 `x:`、`y:`、坐标框、占位框或“放置在适当位置”。
- 使用相对区域约束：顶部信息区、中部主视觉区、底部信息区、前中后景层次。
- 锁定第一视觉、辅助视觉、禁忌主角和阅读顺序；允许模型在相对区域内自然构图。
- 产品、礼盒、包装、食品等静物主视觉使用“陈列姿态、光影承托、场景关系”，不要套用人物动作或站姿语言。

**脚本成功（退出码 0）后，向用户展示 prompt 摘要：**

```markdown
📝 **生图 Prompt 已组装完成**

- 参考图数量：N 张
- 区域数量：N 个
- 负面约束：N 条
- 分辨率：默认低于 2K；用户明确要求高清/4K/打印时才升高

请确认本次抽卡几张：
- 回复「确认生图」或「确认」→ 按默认 1 张执行
- 回复「抽 2 张 / 2 张 / 3 张」→ 按对应张数执行
- 最多 10 张；如果用户回复超过 10 张，一律按 10 张执行
```

**脚本失败（退出码 ≠ 0）时**：展示校验错误，修复后重新运行。

**🔴 CHECKPOINT · STOP：进入 Step 7 前必须满足以下条件**：
- `prompt_draft.md` 已生成
- `ref_order.json` 已生成，且其中所有 `path` 都必须是**绝对路径**
- 已确认本次抽卡张数；若用户只回复「确认生图 / 确认 / OK / 可以」，视为默认 `1` 张；若用户回复大于 `10`，必须截断为 `10`
- 若已执行 Step 5.8，则 `creative_direction.json` 必须存在，且其中至少包含 `summary`、`hero_focus`、`composition_plan`
- 若 `hero_priority.hero_1` 明确为“产品”，则 `brief.json.assets.product` 必须存在且不可为空
- 若是低清烘焙产品，必须满足二选一：已有 `assets.product_texture_refs`，或已生成 `product_reference_manifest.json`；不得用手写/临时生成的 `product_realized.png` 绕过 Step 3.5
- 若同时存在 `assets.product` 与 `assets.ip`，两者路径不得相同
- 若脚本报告参考图角色冲突，必须先回到素材确认/修正，不得继续生图
- `ref_order.json` 中每个参考图路径对应的文件都必须真实存在，缺任意一个都不得进入生图
- 若 `must_include` 要求 Logo/IP，`ref_order.json` 必须分别包含 `logo`/`ip` 角色，且路径必须匹配 `brief.json.assets.logo` / `brief.json.assets.ip`
- `assets.style_refs` 只能放**真实风格参考图**；禁止把上一版 AI 成图、`current_base_ref.png`、`final_poster.png` 等项目输出图继续当 `style_ref`

**禁止规则**：
- 脚本输出即为最终 prompt，main agent **不得手动追加、修改、拼接任何内容**到 prompt_draft.md
- 蒸馏卡的 `copy_planning_guide`、`notes`、`Distill ID` 等内部字段不得出现在 prompt 中
- 如果 prompt 不完整，必须修复脚本后重新运行，不得手补
- 脚本同时输出 `ref_order.json`，记录参考图传图顺序，run.sh 必须按此顺序传图
- 如果项目是面包/吐司/烘焙类产品，prompt 中必须显式约束“切面组织真实、湿润回弹、低局部对比、商业软吐司闭合细密组织、孔隙少量且柔和、不要酸面包/欧包/夏巴塔式大开孔、不要均匀蜂窝孔/干海绵/木屑感/网状雕刻/鳞片状/硬描边纹理”，避免把食品组织做成假锐化
- 如果产品参考图分辨率低、角度不完整，或目标姿态与产品参考差异很大，必须在 prompt 中明确“小尺寸产品参考图只锁定身份、轮廓、配色与基础材质，不把压缩像素放大成微观纹理”，不能强行重塑成不存在的完美正面产品
- 对面包/吐司等切面敏感产品，若产品图短边 < 900px，必须自动启用烘焙参考适配：优先使用原始产品图锁身份 + `product_texture_refs` 锁真实组织；没有质地参考时才运行低频软代理。默认不得生成中间 AI 产品 hero 参考；不得要求用户必须补高清图才继续
- 如果 `hero_priority.hero_1` 指定产品为第一主角，脚本必须自动生成“产品主视觉区域”约束；有固定版式但缺产品主图区时明确补足坐标，无有效版式时只使用中部主视觉区、上下信息区等相对区域，不得伪造坐标
- 如果二维码区域不需要二维码，prompt 必须写明“不要画二维码、边框、占位框、半透明矩形或按钮框”，防止模型生成空框

---

## Step 7：派发 design subagent 生图

### 🔴 CHECKPOINT · STOP：main 写完，子 agent 只跑

生图任务由 main 在主会话完成全部策划和脚本编写，子 agent 只负责执行脚本并等待结果。**不要把 prompt、参考图信息、蒸馏卡数据等塞进子 agent 任务描述。**

**强制约束**：
- main 先把生图所需决策全部固化到 `prompt_draft.md`、`ref_order.json`、`run.sh`、`generation_result.json` 约定结构中
- design subagent 视为**执行器**，不是策划者；不得自行补全需求、重写 prompt、调整参考图顺序、改动模型参数或解释项目背景
- 如执行中发现缺文件、参数冲突、输出异常，子 agent 只返回失败事实与结果文件路径，由 main 回到上一阶段修复后再重派，不得让子 agent 临场自行决策
- **绝对禁止** design subagent 在正式生图失败后自行改用 Python / PIL / Pillow / ImageMagick / 本地贴图 / 手工拼图生成“正式海报”
- 若正式生图报配额、权限、模型接口错误，只能保留失败记录并回报 main；除非用户明确要“临时示意图/降级草图”，否则不得产出任何本地合成海报

### 7.1 main 先写好生图脚本

在派发子 agent 之前，main 必须先写好 `run.sh` 到项目目录：

```bash
#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]"
EXEC_SCRIPT="/Users/a123/.openclaw/skills/brand-poster-creator/scripts/execute_generation.py"

python3 "${EXEC_SCRIPT}" --project-dir "${PROJECT_DIR}" --size 1080x1920 --aspect 9:16 --model gpt-image-2 --count 1
```

**注意**：
- 如果用户要求“一次多抽几张 / 给 N 个备选 / 多来几版”，main 必须把数量写进 `run.sh` 的 `--count N`（1-10）。底层 `gpt-image2-gen` 会并行生成，不要手写串行循环。
- 如果用户说“三个都要 / 每个方案各出”，必须先按 Step 5 的 `split_direction_projects.py` 拆成多个子项目；每个子项目分别生成自己的 `prompt_draft.md`、`ref_order.json`、`run.sh`，不得手写 `prompt_A/B/C.txt` 直接生图。
- **参考图顺序由 `assemble_prompt.py` 输出的 `ref_order.json` 决定**，不再手写。run.sh 从该文件动态读取，确保与 prompt 中的参考图编号严格对应
- role 到参数的映射固定为：`style_ref → --ref-style`、`skeleton → --ref-layout`、`product → --ref-product`、`ip → --ref-ip`、`logo → --ref-logo`
- 底层生图器必须保持 `ref_order.json` 的参考图顺序；prompt 中的参考图编号采用 1-based 编号，必须与底层 stdout 的 `Reference list` 和 `Reference images` 顺序一致
- 当项目包含品牌 Logo/IP 时，禁止绕过 `execute_generation.py` 直接调用 `gpt-image2-gen`；否则无法校验 Logo/IP 是否被正确挂载
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

3. 如果 `generation_result.json` 中 `ok=true`，再确认 `output_paths` 中的所有输出文件都存在。默认 1 张时至少存在：
   /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/images/final_poster.png

4. 完成后只回传：`generation_result.json` 路径；若成功，再附上 `output_paths` 中所有海报路径。

不要修改脚本内容，不要改变参数，不要读取其他无关文件。
不要自行编写任何 Python/PIL/Pillow/ImageMagick/HTML Canvas 拼图脚本，不要产出本地合成海报顶替正式生图结果。
```

### 7.3 回收结果

子 agent 完成后（遵守 AGENTS.md 0.7.1 等待完成事件规则）：
1. 先读取 `generation_result.json`，确认 `ok=true`
2. 再检查 `output_paths` 中所有图片是否真实存在；若缺少 `output_paths`，至少检查 `images/final_poster.png`
3. 确认文件大小合理（不应为 0 字节）
4. 对每张成品做视觉核验：IP 必须来自 `brief.json.assets.ip`，不得变成风格参考图人物；Logo 必须看起来是官方 Logo，而不是模型临摹的相似文字
5. `ref_order.json` 中包含 `logo` / `ip` 只证明参考图已挂载，不得作为成品保真的结论
6. 若 Logo 需要文件级精确，优先重新生成并预留 Logo 区；仍不稳定时，允许在正式生图成功后做一次受控品牌安全修正：只把官方 Logo 文件放回预留区域，不得重画主体、文案或版式，并在 `generation_result.json` / `delivery_manifest.json` 记录该修正
7. 若任一条件不满足，视为执行失败或品牌保真风险，先查看 `stdout/stderr` 日志，不得向用户播报“已出图”
8. 只有全部通过后，才按 Step 8 流程发送成品图给用户

### 7.4 正式生图失败后的处理

如果 `generation_result.json` 中出现以下任一信号：
- `ok=false`
- `fallback_allowed=false`
- `error_category=quota_insufficient`
- `error_category=permission_denied`
- `error_category=provider_error`

则必须执行以下规则：

1. 停在 `generation failed`
2. 回报失败事实、错误摘要、日志路径、处理动作
3. 回报以下处理选项：
   - 充值 / 恢复配额
   - 切换可用 provider
   - 修复权限或路径
4. **不得**让 design subagent 自行改走本地拼图、本地贴图、PIL 合成、手工排字顶替正式结果
5. 只有用户明确接受“临时示意图/降级草图”时，才允许走非正式链路，并且必须先说明这不是正式海报交付

---

## Step 8：发送成品图 → 用户确认

仅当 `generation_result.json.ok=true` 且成品文件真实存在后，才将成品图发送给用户确认。

**补偿入口（强制）**：
用户追问”进度 / 好了没 / 图片呢 / 发图 / 没收到 / 继续”时，如果当前项目已经有 `generation_result.json.ok=true` 或 `delivery_manifest.json`，必须先恢复到 Step 8 检查交付状态。

若 `delivery_manifest.json.delivery_status` 不是成功状态，或缺少 `delivery_evidence.message_id/chat_id`，说明还没有真实发送成功。此时禁止回复本地路径、`MEDIA:/...`、”图片已在目录里”或”交付副本已生成”；必须继续执行真实飞书发送。

若子 agent 只返回了 `feishu-deliver` 路径，也只能视为”发送副本已准备”，不能视为”已发给用户”。

### 8.1 🔴 CHECKPOINT · STOP：交付前强制检查（必须执行）

在发送前，main 必须先执行交付检查脚本：

```bash
python3 <<'EOF'
import json
import os
import sys

project_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
image_path = f"{project_dir}/images/final_poster.png"

# 检查文件存在
if not os.path.exists(image_path):
    print(json.dumps({"status": "error", "message": "图片文件不存在"}, ensure_ascii=False))
    sys.exit(1)

# 检查文件大小
size = os.path.getsize(image_path)
print(json.dumps({
    "status": "ready",
    "image_path": image_path,
    "size_bytes": size,
    "size_mb": round(size / 1024 / 1024, 2),
    "delivery_instruction": {
        "tool": "message",
        "action": "send",
        "channel": "feishu",
        "media": image_path,
        "mimeType": "image/png"
    },
    "warning": "必须调用 message 工具发送，不得输出 MEDIA: 文本"
}, indent=2, ensure_ascii=False))
EOF
```

**检查脚本输出后，必须按照 `delivery_instruction` 调用 message 工具。**

### 8.2 准备交付清单

在发送前，main 必须先执行：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/prepare_feishu_delivery.py \
  --project-dir /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]
```

该脚本会产出：
- `/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/delivery_manifest.json`
- 交付目录中的预览图 / 原图副本 / 原图 zip（按大小条件分流）

### 8.3 真实发送规则（硬约束）

**错误示例（用户收不到图片）**：
```
❌ 错误：MEDIA:/Users/a123/.openclaw/workspace/brand-poster-projects/BP-xxx/images/final_poster.png
❌ 错误：图片路径：/Users/a123/.openclaw/workspace/brand-poster-projects/BP-xxx/images/final_poster.png
❌ 错误：图片已在 images/ 目录里
❌ 错误：发上来了（但没有调用 message 工具）
```

**正确示例（真实发送）**：
```
✅ 正确：调用 message 工具
message(action=send, channel=feishu, media=/Users/a123/.openclaw/workspace/brand-poster-projects/BP-xxx/images/final_poster.png, mimeType=image/png)

✅ 正确：等待返回
{“ok”: true, “messageId”: “om_xxx”, “chatId”: “oc_xxx”}

✅ 正确：确认交付
已发送图片 (messageId: om_xxx)
```

**记住**：`MEDIA:` 只是文本输出，不是真实发送！用户在飞书中看不到任何图片！

发送规则：
1. 先读取 `delivery_manifest.json`
2. 必须读取 `agent_delivery_contract`，并按其中的 `send_plan.message_tool_arguments` 调用真实飞书媒体发送工具：
   - 首选 `message(action=send, channel=feishu, accountId=main, media=..., mimeType=...)`
   - 若当前运行环境提供 `feishu-send-image` 等等效图片工具，使用等效图片工具
   - `delivery_target.chat_id/user_id` 为空时，必须使用当前飞书会话绑定继续发送；这不是停止理由
3. **绝对禁止**把 `MEDIA:/absolute/path`、本地绝对路径、`file://...` 或目录说明作为回复文本冒充交付
4. 工具返回 `ok=true` 且有 `messageId/chatId` 后，才允许说”已发送/已发群里/交付完成”
5. **如果没有看到 message 工具的返回值，说明没有真实发送，必须重新调用 message 工具**
6. 发送成功后必须运行：

```bash
python3 /Users/a123/.openclaw/skills/brand-poster-creator/scripts/record_feishu_delivery.py \
  --project-dir /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID] \
  --sent-path [本次真实发送的图片路径] \
  --message-id [飞书发送工具返回的 messageId] \
  --chat-id [飞书发送工具返回的 chatId] \
  --method "message(media)"
```

7. 若 `delivery_mode=direct_image`：
   - 真实发送 `deliverables.original_copy.path`
8. 若 `delivery_mode=preview_and_zip`：
   - 只真实发送 `deliverables.preview_image.path` 供飞书预览
   - 明确告诉用户：当前发送的是压缩预览图，原始高清图已保留，后续修改将继续使用原图，不会基于预览图反复压缩
   - 用户确认定稿后，再发送 `deliverables.original_zip.path` 作为原图交付包
9. 任何”局部修改””继续调整””重新生成”都必须继续引用 `edit_source_image` 指向的原图，不得把 preview 图当作修改输入

### 8.4 🔴 CHECKPOINT · STOP：交付验证清单（必须全部通过）

在说”已发送”之前，必须确认：
- ✅ 调用了 `message` 工具（不是输出 `MEDIA:` 文本）
- ✅ `message` 工具返回了 `{“ok”: true, “messageId”: “...”, “chatId”: “...”}`
- ✅ 记录了 `messageId` 和 `chatId` 到 `delivery_manifest.json`
- ✅ 向用户回复中包含 `messageId`（证明真实发送）

**如果以上任一条不满足，说明交付失败，必须重新发送。**

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
- 「确认定稿」→ 进入设计审批流程
- 「局部修改 [具体描述]」→ 调整后重新生图
```

### 8.5：请求设计审批（新增 v3.0）

用户确认设计成品后，**触发设计审批流程**：

```bash
# 1. 记录 AI 设计完成时间
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "design" \
  --event-type "complete" \
  --actor "ai"

# 2. 请求设计审批
approval_request=$(python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "design" \
  --artifact "images/final_poster.png")

# 3. 提取艾特消息
mention_message=$(echo "$approval_request" | jq -r '.message')
```

向用户发送审批请求：

```markdown
✅ **设计初稿完成**

[已发送设计成品图]

$mention_message

请审核确认：
- 回复「通过」→ 设计审批通过
  - B级项目：直接进入交付流程
  - A/S级项目：进入创意总监审核
- 回复「修改：[具体要求]」→ 需要调整设计
- 回复「拒绝：[原因]」→ 终止项目
```

### 8.6：记录设计审批响应

**等待设计判断者回复**。收到回复后，记录审批结果：

```bash
# 记录审批响应
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "design" \
  --decision "approved" \
  --feedback "设计效果符合预期"

# 记录人工审核完成时间
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "design" \
  --event-type "complete" \
  --actor "human"
```

**处理不同的审批结果**：

1. **approved（通过）**：
   - **B级项目**：设计审批通过后，直接进入 Step 9 最终确认
   - **A级项目**：需要继续创意总监审核（Step 8.7）
   - **S级项目**：需要继续创意总监审核（Step 8.7）

2. **revision_needed（需要修改）**：
   - 记录反馈意见
   - 根据反馈调整设计或重新生成
   - 再次请求审批（回到 Step 8.5）

3. **rejected（拒绝）**：
   - 记录拒绝原因
   - 终止项目
   - 生成复盘报告

### 8.7：创意总监审核（仅 A/S 级项目）

**仅当项目等级为 A 或 S 时执行此步骤。**

设计判断者通过后，触发创意总监审核：

```bash
# 请求创意总监审批
approval_request=$(python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "creative_direction" \
  --artifact "images/final_poster.png")

mention_message=$(echo "$approval_request" | jq -r '.message')
```

向用户发送审批请求：

```markdown
✅ **设计判断者已通过，进入创意总监审核**

$mention_message

请审核确认：
- 回复「通过」→ 创意总监审批通过
  - A级项目：进入交付流程
  - S级项目：进入老板最终决策
- 回复「修改：[具体要求]」→ 需要调整创意方向
- 回复「拒绝：[原因]」→ 终止项目
```

记录审批响应：

```bash
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "creative_direction" \
  --decision "approved" \
  --feedback "创意方向符合战略定位"
```

### 8.8：老板最终决策（仅 S 级项目）

**仅当项目等级为 S 时执行此步骤。**

创意总监通过后，触发老板最终审批：

```bash
# 请求老板最终审批
approval_request=$(python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  request \
  --project-dir "[项目目录绝对路径]" \
  --milestone "final_approval" \
  --artifact "images/final_poster.png")

mention_message=$(echo "$approval_request" | jq -r '.message')
```

向用户发送审批请求：

```markdown
✅ **创意总监已通过，进入老板最终决策**

$mention_message

请审核确认：
- 回复「通过」→ 项目最终批准，进入交付流程
- 回复「修改：[具体要求]」→ 需要调整
- 回复「拒绝：[原因]」→ 终止项目
```

记录审批响应：

```bash
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  respond \
  --project-dir "[项目目录绝对路径]" \
  --milestone "final_approval" \
  --decision "approved" \
  --feedback "符合战略目标，批准上线"
```

### 8.9：审批超时处理

在等待审批过程中，定期检查超时：

```bash
# 检查超时
timeout_check=$(python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  check_timeout \
  --project-dir "[项目目录绝对路径]")

timeout_count=$(echo "$timeout_check" | jq '.timeout_steps | length')
```

如果发现超时（`timeout_count > 0`），根据项目等级处理：

**B级项目**：自动通过
```bash
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  handle_timeout \
  --project-dir "[项目目录绝对路径]" \
  --milestone "[超时的节点]" \
  --timeout-action "auto_approve"
```

**A/S级项目**：提醒或升级
```bash
# 先提醒一次
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  handle_timeout \
  --project-dir "[项目目录绝对路径]" \
  --milestone "[超时的节点]" \
  --timeout-action "remind"

# 如果再次超时，升级给项目经理
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/project_grading.py \
  handle_timeout \
  --project-dir "[项目目录绝对路径]" \
  --milestone "[超时的节点]" \
  --timeout-action "escalate"
```

---

## Step 9：任务完成确认与清理

**前置条件**：所有必需的审批节点均已通过。

### 9.1：生成复盘报告

无论用户是否清理文件，都生成复盘报告：

```bash
# 生成复盘报告
python3 /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/scripts/time_tracking.py \
  retrospective \
  --project-dir "[项目目录绝对路径]" \
  --output "[项目目录绝对路径]/project_retrospective.md"
```

向用户展示项目完成信息：

```markdown
🎉 **项目审批流程已完成**

- 项目等级：[B/A/S]
- 审批通过节点：
  ✅ 文案策划审核
  ✅ 设计初稿审核
  [如果是 A/S 级] ✅ 创意总监审核
  [如果是 S 级] ✅ 老板最终决策

📊 **项目数据摘要**：
- 总耗时：XX 分钟
- AI 处理时间：XX 分钟（XX%）
- 人工审核时间：XX 分钟（XX%）
- 审批响应平均时长：XX 分钟

详细复盘报告已生成：project_retrospective.md

请选择：
- 回复「完成」→ 清理项目中间文件
- 回复「保留」→ 保留所有文件，不清理
```

### 9.2：清理项目文件（可选）

如果用户选择「完成」，运行清理脚本：

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

### 🔴 CHECKPOINT · STOP：清理安全约束

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
