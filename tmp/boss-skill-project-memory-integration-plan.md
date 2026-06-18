# Boss Skill 项目记忆系统集成计划

## 📌 目标

让 boss skill 的品牌档案和项目记忆系统能够被其他 agent 和 skill 复用，实现：
1. **品牌档案跨项目复用**：同一品牌的多个 Campaign 共享品牌背景信息
2. **跨 agent 协作**：design agent 生成海报时可以读取品牌档案
3. **项目归档**：生成的图片、文案等产出可以归档到项目目录

---

## ✅ 已完成的工作

### 1. 核心代码实现（已完成并测试）

**位置**：`/Users/a123/.openclaw/skills/boss/scripts/agency_project/`

**文件清单**：
- `schemas.py` - 所有 JSON schema 定义（品牌档案、项目、7 阶段文档）
- `project.py` - 核心项目管理函数
- `__init__.py` - 模块导出

**CLI 脚本**（5 个，均已测试通过）：
```bash
# 1. 初始化项目（创建或复用品牌档案 + 创建项目目录）
init_agency_project.py --workspace-root /path --brand-name "品牌名" --campaign-name "Campaign名"

# 2. 查找品牌档案（供跨 agent 使用）
find_brand_profile.py --workspace-root /path --brand-name "品牌名"
# 返回：{"found": true/false, "profile_path": "...", "profile": {...}}

# 3. 查找活跃项目
find_active_project.py --workspace-root /path --brand-name "品牌名"

# 4. 归档材料到项目
archive_material.py --project-dir /path --source-path /file --material-type research|reference|client-assets

# 5. 更新项目阶段
update_stage.py --project-dir /path --stage brief_intake --status completed --user-confirmed
```

### 2. 目录结构设计

```
workspace/projects/
├── _registry.json                    # 全局索引（品牌 + 项目）
├── 可口可乐/                         # 品牌目录
│   ├── _brand-profile.json          # 品牌档案（跨项目复用）
│   ├── _brand-assets/               # 品牌资产库
│   │   ├── logos/
│   │   ├── vi-manual/
│   │   └── reference-images/
│   ├── 2024春节Campaign/            # 项目 1
│   │   ├── project.json            # 项目元数据 + 7 阶段追踪
│   │   ├── brief.json              # AE Brief
│   │   ├── strategy.json           # 策略文档
│   │   ├── creative-direction.json # 创意方向
│   │   ├── materials/              # 材料归档
│   │   │   ├── research/
│   │   │   ├── reference/
│   │   │   └── client-assets/
│   │   └── outputs/                # 产出归档
│   │       ├── copy/
│   │       ├── design/
│   │       └── final/
│   └── 618大促Campaign/             # 项目 2（复用品牌档案）
│       └── ...
```

### 3. 品牌档案内容

**_brand-profile.json** 包含：
- 品牌基本信息：品牌名、英文名、行业、品类
- 品牌定位：positioning、核心价值观（core_values）
- 品牌调性：brand_tone
- 目标受众：target_audience
- VI 规范：colors、fonts、logo_usage_notes
- 历史 Campaign 记录：historical_campaigns
- 关键联系人：key_contacts

### 4. 文档更新

**已更新**：`skills/boss/SKILL.md`
- 添加了完整的"Project Memory System"章节
- 包含所有 CLI 脚本的使用说明
- 跨 agent 协作指引

---

## 🎯 待执行的集成方案

### 方案 A：渐进式集成（推荐 ✅）

#### 阶段 1：非侵入式部署（低风险，立即可用）

**目标**：让系统可用，但不修改现有 skill 代码

**具体任务**：

**1.1 更新 workspace/AGENTS.md（main agent 执行规则）**
```markdown
## X. 品牌项目记忆系统

### X.1 使用场景
- 启动品牌 Campaign 全案项目时，通过 boss skill 建立品牌档案和项目记忆
- 品牌档案存储在 `workspace/projects/{品牌名}/_brand-profile.json`
- 项目记忆存储在 `workspace/projects/{品牌名}/{Campaign名}/project.json`

### X.2 查询品牌档案
当派发 design/copywriter 等 subagent 时，如果任务涉及已建档品牌，可以在派发消息中附带品牌档案信息：

```bash
# 查询品牌档案
python3 /Users/a123/.openclaw/skills/boss/scripts/find_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "可口可乐"
```

返回的 profile 包含品牌定位、调性、VI 规范等，可作为上下文传递给 subagent。

### X.3 归档产出
当 subagent 完成产出后，可将成果归档到项目目录：

```bash
# 归档设计稿到项目
python3 /Users/a123/.openclaw/skills/boss/scripts/archive_material.py \
  --project-dir /Users/a123/.openclaw/workspace/projects/可口可乐/2024春节Campaign \
  --source-path /Users/a123/.openclaw/workspace-design/images/final_poster.png \
  --material-type reference \
  --notes "design agent 生成的春节海报终稿"
```
```

**1.2 更新 workspace-design/AGENTS.md（design agent 执行规则）**
```markdown
## X. 跨项目品牌档案协作

### X.1 接收品牌档案上下文
当 main agent 派发品牌相关的视觉任务时，如果消息中包含品牌档案信息（brand_profile），优先使用该信息作为设计依据：
- 品牌定位（positioning）
- 品牌调性（brand_tone）
- VI 规范（colors, fonts, logo_usage_notes）
- 目标受众（target_audience）

### X.2 主动查询品牌档案（可选）
如果用户直接向 design agent 提出品牌相关任务，可主动查询品牌档案：

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/find_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名"
```

如果 `found: false`，说明该品牌未建档，继续现有流程（飞书素材检索或用户输入）。

### X.3 产出归档（可选）
如果明确知道当前任务属于某个 Campaign 项目，可将成果归档：

```bash
# 先查找活跃项目
python3 /Users/a123/.openclaw/skills/boss/scripts/find_active_project.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名"

# 如果找到项目，归档产出
python3 /Users/a123/.openclaw/skills/boss/scripts/archive_material.py \
  --project-dir {project_dir} \
  --source-path {生成的图片路径} \
  --material-type reference
```
```

**1.3 更新 workspace/projects/.gitkeep**
```markdown
## 跨 Agent 使用示例

### Design Agent 查询品牌档案

```python
#!/usr/bin/env python3
import json
import subprocess

result = subprocess.run([
    "python3", 
    "/Users/a123/.openclaw/skills/boss/scripts/find_brand_profile.py",
    "--workspace-root", "/Users/a123/.openclaw/workspace",
    "--brand-name", "可口可乐"
], capture_output=True, text=True)

profile_data = json.loads(result.stdout)

if profile_data["found"]:
    profile = profile_data["profile"]
    print(f"品牌定位: {profile['positioning']}")
    print(f"品牌调性: {profile['brand_tone']}")
    print(f"VI 色彩: {profile['vi_guidelines']['colors']}")
else:
    print("品牌档案未找到，使用默认流程")
```

### Main Agent 派发任务时传递品牌档案

```json
{
  "runtime": "subagent",
  "agentId": "design",
  "task": "生成可口可乐春节海报...",
  "context": {
    "brand_profile": {
      "brand_name": "可口可乐",
      "positioning": "...",
      "brand_tone": "...",
      "vi_guidelines": {...}
    }
  }
}
```
```

**预期效果**：
- ✅ 系统立即可用
- ✅ 零破坏性（不修改现有 skill 代码）
- ✅ 使用方式：main agent 手动查询品牌档案 → 传递给 subagent
- ⚠️ 需要 main agent 主动协调（不是自动）

---

#### 阶段 2：skill 集成增强（可选，按需执行）

**目标**：让现有 skill 自动感知品牌档案系统

**2.1 brand-poster-creator 集成（优先级：高）**

**修改位置**：`workspace-design/skills/brand-poster-creator/SKILL.md` Step 2.5 品牌素材检索

**集成逻辑**：
```
Step 2.5 品牌素材检索
├─ 1. 先查询品牌档案系统（新增）
│   └─ 如果找到 → 自动填充品牌背景信息到 brief.json
├─ 2. 查询飞书云盘品牌素材（现有）
│   └─ 如果找到 → 下载 Logo/IP/产品图
└─ 3. 如果都没找到 → 用户手动输入
```

**代码修改**：在 `fetch_brand_assets.py` 之前添加：
```python
# 新增：查询品牌档案
import subprocess
result = subprocess.run([
    "python3",
    "/Users/a123/.openclaw/skills/boss/scripts/find_brand_profile.py",
    "--workspace-root", str(workspace_root),
    "--brand-name", brand_name
], capture_output=True, text=True)

profile_data = json.loads(result.stdout)
if profile_data["found"]:
    profile = profile_data["profile"]
    # 自动填充到 brief.json
    brief.update({
        "brand_positioning": profile["positioning"],
        "brand_tone": profile["brand_tone"],
        "target_audience": profile["target_audience"],
        "vi_colors": profile["vi_guidelines"]["colors"],
        "brand_profile_source": "agency_project_system"
    })
    print(f"✅ 已从品牌档案系统加载品牌信息")
else:
    print(f"ℹ️ 品牌档案未找到，继续飞书素材检索流程")

# 继续现有的飞书云盘素材检索...
```

**优点**：
- ✅ 自动化：无需 main agent 手动查询和传递
- ✅ 兼容性：如果品牌档案不存在，不影响现有流程
- ✅ 渐进式：先改一个 skill，验证效果

**风险**：
- ⚠️ 需要修改 brand-poster-creator 代码
- ⚠️ 需要测试验证

**2.2 其他 skill 集成（优先级：中）**

按相同逻辑集成：
- `xiangqingye-desigen`（详情页设计）
- `packaging-design`（包装设计）
- 未来新增的品牌相关 skill

---

### 方案 B：深度集成（不推荐 ❌）

**内容**：修改所有生图 skill，强制要求先查找品牌档案

**风险**：
- ❌ 改动面大，容易引入 bug
- ❌ 对非品牌项目（个人设计、临时任务）造成干扰
- ❌ 需要大量测试验证

**不推荐原因**：过度工程化，收益不高

---

## 📊 权限验证结果

✅ **已验证：所有 agent（包括 shared 版本）对 workspace/projects/ 有完整读写权限**

验证依据：
1. 所有 OpenClaw 进程都以 a123 用户身份运行
2. 虾权隔离是飞书用户权限隔离，不是文件系统隔离
3. shared agent 的 exec-approvals 白名单已包含 `python3`、`bash`、`cp`、`mkdir` 等
4. 实际测试验证了文件读写权限

---

## 🎬 推荐执行路径

### 立即执行（阶段 1）

1. ✅ 更新 `workspace/AGENTS.md` - 添加品牌项目记忆系统使用说明
2. ✅ 更新 `workspace-design/AGENTS.md` - 添加跨项目品牌档案协作说明
3. ✅ 更新 `workspace/projects/.gitkeep` - 补充跨 agent 使用示例
4. ✅ 提交 git 版本备份

**预期效果**：
- 虾指挥（main + boss skill）可以建立品牌档案
- 生图大师（design agent）可以手动查询品牌档案
- 系统立即可用，零风险

### 后续优化（阶段 2，按需执行）

5. ⏳ 修改 `brand-poster-creator` skill，集成品牌档案自动查询
6. ⏳ 测试验证集成效果
7. ⏳ 根据使用体验，决定是否集成到其他 skill

---

## 📝 使用流程示例

### 场景 1：main agent 通过 boss skill 建立品牌项目

```bash
# 用户：虾指挥，帮我建立可口可乐 2024 春节 Campaign 项目

# main agent 调用 boss skill
# boss skill 内部调用：
python3 /Users/a123/.openclaw/skills/boss/scripts/init_agency_project.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "可口可乐" \
  --campaign-name "2024春节Campaign" \
  --campaign-type "节日营销" \
  --brand-name-en "Coca-Cola" \
  --industry "饮料" \
  --category "碳酸饮料" \
  --positioning "开启畅爽时刻" \
  --brand-tone "年轻活力、乐观积极" \
  --target-audience "18-35岁都市年轻人" \
  --core-values "快乐,分享,正能量"

# 返回：
# {
#   "project_dir": "/Users/a123/.openclaw/workspace/projects/可口可乐/2024春节Campaign",
#   "brand_profile_created": false,  # 已存在，复用
#   "project_created": true
# }
```

### 场景 2：design agent 生成海报时读取品牌档案

```bash
# 用户：生图大师，生成可口可乐春节海报

# design agent 调用 brand-poster-creator skill
# skill 内部（阶段 2 集成后）：
python3 /Users/a123/.openclaw/skills/boss/scripts/find_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "可口可乐"

# 返回：
# {
#   "found": true,
#   "profile": {
#     "positioning": "开启畅爽时刻",
#     "brand_tone": "年轻活力、乐观积极",
#     "vi_guidelines": {
#       "colors": ["#F40009", "#FFFFFF"],
#       "fonts": ["Coca-Cola Script", "Trade Gothic"]
#     }
#   }
# }

# skill 自动使用这些信息生成海报
```

### 场景 3：main agent 派发任务时传递品牌档案（阶段 1）

```python
# main agent 先查询品牌档案
profile_result = exec("python3 .../find_brand_profile.py --brand-name 可口可乐")
profile = json.loads(profile_result)["profile"]

# 派发 design subagent 时附带品牌信息
spawn_subagent({
    "agentId": "design",
    "task": "生成可口可乐春节海报，主题：团圆时刻",
    "context": {
        "brand_profile": profile  # 传递品牌档案
    }
})
```

---

## ❓ 待确认事项

请确认以下内容：

1. **执行范围**：
   - [ ] 只执行阶段 1（文档更新，立即可用，零风险）
   - [ ] 同时执行阶段 1 + 阶段 2（含 brand-poster-creator 集成）
   - [ ] 其他？

2. **文档更新内容**：
   - [ ] 同意以上 AGENTS.md 的更新内容
   - [ ] 需要调整？请说明

3. **Git 备份**：
   - [ ] 更新完成后立即提交 git 版本
   - [ ] 暂不提交

4. **测试验证**：
   - [ ] 我（Claude）代为测试基本流程
   - [ ] 你自己测试
   - [ ] 不需要测试，直接上线

请告诉我你的决定，我立即执行。
