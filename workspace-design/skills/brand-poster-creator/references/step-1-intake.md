# Step 1：需求收集

## 概述

本步骤负责通过飞书对话卡片收集用户需求，包括项目分级、审批者确认、基础信息收集，并初始化项目目录结构。

---

## 1.1 触发技能后立即发送需求收集卡片

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

---

## 1.2 项目分级与审批者确认

⚠️ **重要变更（v3.0）**：新增项目分级与审批流程

收集需求后，**必须先确认项目等级和审批者**，再继续后续流程。

### 1.2.1 项目等级询问

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

### 1.2.2 审批者信息收集

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

### 1.2.3 初始化项目分级

收集完审批者信息后，运行初始化脚本：

```bash
# 将审批者信息保存到临时文件
reviewers_json='{"copywriter":{"name":"张三","open_id":"ou_xxx"},...}'

# 初始化项目分级
python3 {baseDir}/scripts/project_grading.py \
  init \
  --project-dir "[项目目录绝对路径]" \
  --grade "$PROJECT_GRADE" \
  --reviewers-json "$reviewers_json"
```

脚本会创建 `project_grading.json` 文件，包含审批流程配置。

### 1.2.4 初始化时间记录

同时初始化时间记录：

```bash
# 记录项目启动时间
python3 {baseDir}/scripts/time_tracking.py \
  record \
  --project-dir "[项目目录绝对路径]" \
  --stage "intake" \
  --event-type "start" \
  --actor "human"
```

### 1.2.5 向用户确认

展示确认信息：

```markdown
✅ **项目分级已确认**

- **项目等级**：B级 - 日常项目
- **审批流程**：
  1. 文案策划完成 → 张三 审核
  2. 设计初稿完成 → 李四 审核

系统将在关键节点自动艾特对应审批者，并记录审批时间。
```

---

## 1.3 收集需求信息并写入 brief.json

收到用户需求信息后，记录 intake 阶段完成时间：

```bash
python3 {baseDir}/scripts/time_tracking.py \
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

---

## 1.4 项目目录结构

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

---

## 1.5 素材文件处理

用户上传的所有图片文件，统一复制到 `images/` 目录下，使用标准命名：
- `images/style_ref_N.png`（风格参考图，N 从 1 开始递增）
- `images/product.png`（产品图）
- `images/logo.png`（Logo）

---

## 完成后执行下一步

需求收集和项目初始化完成后，进入 **Step 2：品牌档案查询**。
