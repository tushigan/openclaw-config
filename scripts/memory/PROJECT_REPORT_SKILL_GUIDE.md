# 项目进度查询 Skill

## 触发场景

当用户询问以下内容时，自动调用此 skill：

1. **公司项目进度**
   - "公司目前有哪些项目？"
   - "项目进度怎么样了？"
   - "汇报一下项目情况"
   - "现在在做哪些项目？"

2. **特定品牌查询**
   - "wokenday 有哪些项目？"
   - "然利的任务进度如何？"
   - "小白心里软项目做到哪了？"

3. **特定项目查询**
   - "巧克力小吐司详情页项目进展如何？"
   - "某某项目的任务情况"
   - "某某项目有哪些产出？"

---

## 使用方式

### 场景 1: 用户询问公司整体项目进度

**用户输入**:
```
"公司目前有哪些项目在进行？"
```

**Agent 行为**:
```bash
# 1. 先获取概览
OVERVIEW=$(python3 /Users/a123/.openclaw/scripts/memory/report.py overview --json)

# 2. 解析并回复用户
echo "$OVERVIEW" | jq -r '
"目前公司有 \(.total_clients) 个客户，\(.total_brands) 个品牌，\(.total_projects) 个项目。
活跃项目：\(.total_active_projects) 个

客户和品牌列表：
" + (.clients[] | "• \(.name): " + (.brands[] | .name) | @text)'
```

**Agent 回复示例**:
```
目前公司有 18 个客户，21 个品牌，21 个项目。
活跃项目：17 个

主要客户和品牌：
• 泓一: wokenday, 泓一全案
• 丹夫: 丹夫, 年度整合营销合作报价项目
• 然利客户: 然利
• 未分类客户: 测试品牌, 阿嬷秘诀
...

您想了解哪个客户或品牌的详细情况？
```

---

### 场景 2: 用户询问特定品牌

**用户输入**:
```
"wokenday 品牌有哪些项目在做？"
```

**Agent 行为**:
```bash
# 查询品牌项目
BRAND_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/report.py brand --name "wokenday" --json)

# 解析并回复
echo "$BRAND_INFO" | jq -r '
"品牌：\(.brand)
客户：\(.client)
品牌调性：\(.brand_tone)
品牌定位：\(.positioning)

当前项目（\(.projects | length) 个）：
" + (.projects[] | "
• \(.project_name)
  - 类型：\(.campaign_type)
  - 状态：\(.status) | 阶段：\(.lifecycle_stage)
  - 任务数：\(.tasks | length)
  " + if .latest_work_stage then "  - 最新进展：\(.latest_work_stage)" else "" end + "
  " + if (.tasks | length) > 0 then "  任务列表：\n" + (.tasks[] | "    ◦ \(.task_name) (\(.status), v\(.latest_version))" + if .latest_work_stage then "\n      进展：\(.latest_work_stage)" else "" end) else "" end
)'
```

**Agent 回复示例**:
```
品牌：wokenday
客户：泓一
品牌调性：亲和、松弛、懂生活、有手作温度
品牌定位：面向家庭囤货与节日消费场景的亲和型品牌

当前项目（1 个）：

• 巧克力小吐司详情页
  - 类型：详情页设计
  - 状态：active | 阶段：需求收集
  - 任务数：1
  - 最新进展：wireframe_qa_passed / awaiting wireframe cut confirmation
  
  任务列表：
    ◦ 巧克力小吐司详情页设计 (completed, v3)
      进展：wireframe_qa_passed / awaiting wireframe cut confirmation
```

---

### 场景 3: 用户询问特定项目

**用户输入**:
```
"巧克力小吐司详情页项目进展如何？"
```

**Agent 行为**:
```bash
# 查询项目详情
PROJECT_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/report.py project \
  --project-name "巧克力小吐司详情页" \
  --brand-name "wokenday" \
  --json)

# 解析并回复（包含执行目录和关键文件）
echo "$PROJECT_INFO" | jq -r '
"项目：\(.project.project_name)
客户：\(.client)
品牌：\(.brand.name)
类型：\(.project.campaign_type)
状态：\(.project.status) | 阶段：\(.project.lifecycle_stage)
" + if .project.project_summary then "摘要：\(.project.project_summary)" else "" end + "
" + if .project.current_goal then "当前目标：\(.project.current_goal)" else "" end + "
" + if .project.latest_work_stage then "最新进展：\(.project.latest_work_stage)" else "" end + "
" + if .project.execution_workspace then "执行目录：\(.project.execution_workspace)" else "" end + "

任务详情（\(.tasks | length) 个）：
" + (.tasks[] | "
• \(.task_name) [\(.status)]
  - 类型：\(.task_type) | 版本：v\(.latest_version)
  - 负责：\(.assigned_agent) / \(.assigned_skill)
  " + if .brief then "  - 需求：\(.brief)" else "" end + "
  " + if .latest_work_stage then "  - 最新状态：\(.latest_work_stage)" else "" end + "
  " + if .execution_workspace then "  - 执行目录：\(.execution_workspace)" else "" end + "
  " + if (.key_files | length) > 0 then "  - 关键文件：\n" + (.key_files | to_entries[] | "      ◦ \(.key): \(.value)") else "" end + "
  " + if (.iterations | length) > 0 then "  - 版本历史：\(.iterations | length) 个版本" else "" end
)'
```

**Agent 回复示例**:
```
项目：巧克力小吐司详情页
客户：泓一
品牌：wokenday
类型：详情页设计
状态：active | 阶段：需求收集
摘要：WokenDay 巧克力小吐司天猫手机端详情页；当前完成策略、文案、风格指南、头图首版、黑白手稿和 QA，待手稿切段确认。
当前目标：补齐手稿切段预览与 cut_manifest，确认后进入最终成稿。
最新进展：wireframe_qa_passed / awaiting wireframe cut confirmation
执行目录：/Users/a123/.openclaw/workspace-design/outputs/巧克力小吐司详情页_20260617

任务详情（1 个）：

• 巧克力小吐司详情页设计 [completed]
  - 类型：detail_page | 版本：v3
  - 负责：design / xiangqingye-desigen
  - 需求：WokenDay 巧克力小吐司天猫手机端详情页，预包装烘焙，规格300g/12个独立袋；风格干净高级、无印良品式留白；包含详情页长图与5张头图。
  - 最新状态：wireframe_qa_passed / awaiting wireframe cut confirmation
  - 执行目录：/Users/a123/.openclaw/workspace-design/outputs/巧克力小吐司详情页_20260617
  - 关键文件：
      ◦ strategy: /Users/a123/.openclaw/workspace-design/outputs/巧克力小吐司详情页_20260617/策划/strategy_v1.md
      ◦ style_guide: /Users/a123/.openclaw/workspace-design/outputs/巧克力小吐司详情页_20260617/策划/style_guide_v1.md
      ◦ wireframe: /Users/a123/.openclaw/workspace-design/outputs/巧克力小吐司详情页_20260617/线框图/wireframe_v1.png
      ...
  - 版本历史：3 个版本
```

---

## 智能交互流程

### 流程 1: 从概览到详情

```
用户: "公司项目进度怎么样？"
  ↓
Agent: 调用 report.py overview
  ↓
Agent: "目前有 18 个客户，21 个品牌，21 个项目。
       主要客户：泓一、丹夫、然利客户...
       您想了解哪个客户或品牌的详细情况？"
  ↓
用户: "wokenday"
  ↓
Agent: 调用 report.py brand --name "wokenday"
  ↓
Agent: "wokenday 品牌有 1 个项目：巧克力小吐司详情页（详情页设计）
       任务：巧克力小吐司详情页设计，状态已完成，v3 版本
       最新进展：wireframe_qa_passed / awaiting wireframe cut confirmation"
  ↓
用户: "详细情况"
  ↓
Agent: 调用 report.py project --project-name "巧克力小吐司详情页" --brand-name "wokenday"
  ↓
Agent: 提供完整的项目详情（含执行目录、关键文件、版本历史）
```

### 流程 2: 直接查询品牌

```
用户: "然利品牌的项目进度"
  ↓
Agent: 调用 report.py brand --name "然利"
  ↓
Agent: 直接返回品牌的所有项目和任务
```

### 流程 3: 直接查询项目

```
用户: "巧克力小吐司详情页做到哪了？"
  ↓
Agent: 从问题中提取项目名称
  ↓
Agent: 调用 report.py project --project-name "巧克力小吐司详情页"
  ↓
Agent: 返回完整项目详情
```

---

## Agent 集成指导

### 在 Agent 的系统提示词中添加

```markdown
## 项目进度查询能力

当用户询问以下内容时，你应该主动调用项目进度查询工具：

1. **公司整体项目进度**
   - 关键词：公司项目、项目进度、有哪些项目、项目情况
   - 调用：`python3 /Users/a123/.openclaw/scripts/memory/report.py overview --json`

2. **特定品牌查询**
   - 关键词：某某品牌 + 项目/任务/进度
   - 调用：`python3 /Users/a123/.openclaw/scripts/memory/report.py brand --name "品牌名" --json`

3. **特定项目查询**
   - 关键词：某某项目 + 进度/情况/状态
   - 调用：`python3 /Users/a123/.openclaw/scripts/memory/report.py project --project-name "项目名" --json`

**重要**：
- 先查询，再回复用户
- 使用结构化的方式呈现信息
- 如果查询结果有多个选项，引导用户进一步指定
- 在回复中突出关键信息：状态、进展、任务数量、关键文件位置
```

---

## 命令快速参考

### 1. 获取公司项目概览
```bash
python3 /Users/a123/.openclaw/scripts/memory/report.py overview [--json]
```

### 2. 查询品牌项目
```bash
python3 /Users/a123/.openclaw/scripts/memory/report.py brand \
  --name "品牌名" \
  [--json]
```

### 3. 查询项目详情
```bash
python3 /Users/a123/.openclaw/scripts/memory/report.py project \
  --project-id "PROJECT-xxx" \
  [--json]

# 或
python3 /Users/a123/.openclaw/scripts/memory/report.py project \
  --project-name "项目名" \
  --brand-name "品牌名" \
  [--json]
```

---

## 返回数据结构

### overview 返回
```json
{
  "total_clients": 18,
  "total_brands": 21,
  "total_projects": 21,
  "total_active_projects": 17,
  "clients": [
    {
      "name": "客户名",
      "client_id": "CLI-xxx",
      "brands": [
        {
          "name": "品牌名",
          "brand_id": "BRD-xxx",
          "brand_tone": "品牌调性",
          "positioning": "品牌定位",
          "projects": [
            {
              "name": "项目名",
              "project_id": "PROJECT-xxx",
              "campaign_type": "项目类型",
              "status": "active",
              "lifecycle_stage": "执行阶段",
              "task_count": 1,
              "active_tasks": 0,
              "completed_tasks": 1,
              "latest_work_stage": "最新进展"
            }
          ]
        }
      ]
    }
  ]
}
```

### brand 返回
```json
{
  "client": "客户名",
  "brand": "品牌名",
  "brand_id": "BRD-xxx",
  "brand_tone": "品牌调性",
  "positioning": "品牌定位",
  "target_audience": "目标受众",
  "projects": [
    {
      "project_name": "项目名",
      "project_id": "PROJECT-xxx",
      "campaign_type": "项目类型",
      "status": "active",
      "lifecycle_stage": "执行阶段",
      "latest_work_stage": "最新进展",
      "tasks": [
        {
          "task_id": "TASK-xxx",
          "task_name": "任务名",
          "task_type": "任务类型",
          "status": "completed",
          "latest_version": 3,
          "latest_work_stage": "最新进展"
        }
      ]
    }
  ]
}
```

### project 返回
```json
{
  "client": "客户名",
  "brand": {
    "name": "品牌名",
    "brand_tone": "品牌调性",
    "positioning": "品牌定位"
  },
  "project": {
    "project_id": "PROJECT-xxx",
    "project_name": "项目名",
    "campaign_type": "项目类型",
    "status": "active",
    "lifecycle_stage": "执行阶段",
    "project_summary": "项目摘要",
    "current_goal": "当前目标",
    "latest_work_stage": "最新进展",
    "execution_workspace": "执行目录路径"
  },
  "tasks": [
    {
      "task_id": "TASK-xxx",
      "task_name": "任务名",
      "task_type": "任务类型",
      "status": "completed",
      "latest_version": 3,
      "latest_work_stage": "最新进展",
      "execution_workspace": "执行目录路径",
      "key_files": {
        "strategy": "/path/to/strategy.md",
        "wireframe": "/path/to/wireframe.png"
      },
      "iterations": [
        {
          "version": 1,
          "output_file_path": "/path/to/v1/output.png",
          "created_at": "2026-06-17T10:00:00",
          "notes": "版本说明"
        }
      ]
    }
  ]
}
```

---

## 最佳实践

1. **主动查询**
   - 用户一旦提到"项目"、"进度"、"品牌"等关键词，立即查询
   - 不要猜测或使用旧数据

2. **结构化呈现**
   - 使用清晰的层级结构
   - 突出关键信息（状态、进展、任务数）
   - 提供执行目录和关键文件路径

3. **引导式交互**
   - 如果结果太多，引导用户进一步指定
   - 提供下一步操作建议

4. **实时数据**
   - 每次都查询最新数据
   - 不缓存查询结果

---

## 示例对话

**用户**: "公司目前有哪些项目？"

**Agent**: 
```
让我查询一下公司当前的项目情况...

📊 公司项目进度概览

目前有 18 个客户，21 个品牌，21 个项目，其中 17 个处于活跃状态。

主要客户和品牌：
• 泓一: wokenday, 泓一全案
• 丹夫: 丹夫, 年度整合营销合作报价项目
• 然利客户: 然利
• 未分类客户: 测试品牌, 阿嬷秘诀
• 三鹰食品: 三鹰食品
• 花生姑娘: 花生姑娘
...

您想了解哪个客户或品牌的详细情况？
```

**用户**: "wokenday"

**Agent**:
```
正在查询 wokenday 品牌的项目情况...

🎨 品牌: wokenday
客户: 泓一
品牌调性: 亲和、松弛、懂生活、有手作温度
品牌定位: 面向家庭囤货与节日消费场景的亲和型品牌

当前项目（1 个）:

🟢 巧克力小吐司详情页
  - 类型: 详情页设计
  - 状态: active | 阶段: 需求收集
  - 最新进展: wireframe_qa_passed / awaiting wireframe cut confirmation
  
  任务列表:
    ✅ 巧克力小吐司详情页设计 (已完成, v3)
       进展: 线框图 QA 通过，等待切段确认

需要查看这个项目的详细情况吗？
```

---

这个 skill 现在已经可以让所有 agent 自动触发项目进度查询！
