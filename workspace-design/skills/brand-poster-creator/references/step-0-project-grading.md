# Step 0：项目分级与审批者确认

⚠️ **重要变更（v3.0）**：新增项目分级与审批流程

收集需求后，**必须先确认项目等级和审批者**，再继续后续流程。

---

## 1. 项目等级询问

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

---

## 2. 审批者信息收集

根据用户选择的等级，**动态询问对应的审批者**：

### B级项目

```markdown
请提供以下审批者的姓名：
1. **文案策划判断者**：（负责文案策划审核）
2. **设计判断者**：（负责设计初稿审核）
```

### A级项目

```markdown
请提供以下审批者的姓名：
1. **文案策划判断者**：（负责文案策划审核）
2. **设计判断者**：（负责设计初稿审核）
3. **创意总监**：（负责创意方向二次审核）
```

### S级项目

```markdown
请提供以下审批者的姓名：
1. **文案策划判断者**：（负责文案策划审核）
2. **设计判断者**：（负责设计初稿审核）
3. **创意总监**：（负责创意方向二次审核）
4. **老板**：（负责最终决策）
```

---

## 3. 查询飞书用户信息

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

---

## 4. 初始化项目分级

收集完审批者信息后，运行初始化脚本：

```bash
# 将审批者信息保存到变量
reviewers_json='{"copywriter":{"name":"张三","open_id":"ou_xxx"},...}'

# 初始化项目分级
python3 {baseDir}/scripts/project_grading.py \
  init \
  --project-dir "[项目目录绝对路径]" \
  --grade "$PROJECT_GRADE" \
  --reviewers-json "$reviewers_json"
```

脚本会创建 `project_grading.json` 文件，包含审批流程配置。

---

## 5. 初始化时间记录

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

---

## 6. 向用户确认

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

## 完成后

继续执行 Step 1：需求收集（参见 `{baseDir}/references/step-1-intake.md`）
