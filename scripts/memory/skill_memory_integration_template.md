# Skill 记忆系统集成模板

本模板用于为所有 skill 添加统一的记忆系统集成逻辑。

## 集成步骤

### Step 0: 项目立项（在 SKILL.md 开头添加）

```markdown
## 🔴 记忆系统集成（必须先执行）

执行本 skill 前，必须完成项目立项和任务创建：

### 1. 查询/创建项目

```bash
# 方式一：自动创建（推荐）
PROJECT_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/project.py get-or-create \
  --client "客户名" \
  --brand "品牌名" \
  --project "项目名" \
  --campaign-type "海报设计" \
  --json)

PROJECT_ID=$(echo $PROJECT_INFO | jq -r '.project_id')
PROJECT_PATH=$(echo $PROJECT_INFO | jq -r '.project_path')

# 方式二：仅查询（如果项目已存在）
PROJECT_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/project.py get \
  --client "客户名" \
  --brand "品牌名" \
  --project "项目名" \
  --json)
```

### 2. 创建任务

```bash
TASK_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/task.py create \
  --project-id "$PROJECT_ID" \
  --name "任务名称" \
  --type "poster" \
  --agent "design" \
  --skill "$(basename $(dirname $SKILL_PATH))" \
  --brief "任务简介" \
  --json)

TASK_ID=$(echo $TASK_INFO | jq -r '.task_id')
```

### 3. 查询品牌档案（用于指导创作）

```bash
BRAND_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand \
  --name "品牌名" \
  --json)

# 提取品牌信息
BRAND_TONE=$(echo $BRAND_INFO | jq -r '.brand_tone')
POSITIONING=$(echo $BRAND_INFO | jq -r '.positioning')
TARGET_AUDIENCE=$(echo $BRAND_INFO | jq -r '.target_audience')

# 查询品牌资产（Logo、VI、参考图）
BRAND_ASSETS=$(python3 /Users/a123/.openclaw/scripts/memory/query.py assets \
  --brand "品牌名" \
  --json)
```
```

### Step Final: 产出归档（在 SKILL.md 结尾添加）

```markdown
## 📦 产出归档

任务完成后，必须将产出归档到记忆系统：

```bash
# 归档产出文件
python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
  --task-id "$TASK_ID" \
  --file "$OUTPUT_FILE_PATH" \
  --note "版本说明" \
  --expire-days 30 \
  --prompt "$GENERATION_PROMPT" \
  --model "$MODEL_USED"

# 更新任务状态为完成
python3 /Users/a123/.openclaw/scripts/memory/task.py update-status \
  --task-id "$TASK_ID" \
  --status "completed"
```

归档后的产出会：
- 自动版本化（v1, v2, v3...）
- 记录生成参数和 prompt
- 设置过期时间（图片/视频 30 天，文档永久保留）
- 可通过任务 ID 追溯所有历史版本
```
```

## 变量说明

集成时需要根据 skill 的实际情况调整以下变量：

| 变量 | 说明 | 示例 |
|------|------|------|
| `campaign-type` | 项目类型 | 海报设计/TVC制作/详情页设计/产品摄影 |
| `--type` | 任务类型 | poster/copy/video/tvc/design/research |
| `--agent` | 执行 agent | design/copywriter/strategy/main |
| `--skill` | skill 名称 | brand-poster-creator/dreamina-reference-video |
| `--expire-days` | 过期天数 | 30（图片/视频）/ 60（PSD）/ 不设置（文档永久） |

## 集成检查清单

每个 skill 集成后必须检查：

- [ ] SKILL.md 开头添加了"记忆系统集成"章节
- [ ] 包含项目立项逻辑（get-or-create）
- [ ] 包含任务创建逻辑（task create）
- [ ] 包含品牌查询逻辑（query brand）
- [ ] SKILL.md 结尾添加了"产出归档"章节
- [ ] 包含产出保存逻辑（task save-output）
- [ ] 包含任务状态更新逻辑（update-status）
- [ ] 移除或更新所有旧路径引用（workspace/projects → /Users/a123/.openclaw/projects）
