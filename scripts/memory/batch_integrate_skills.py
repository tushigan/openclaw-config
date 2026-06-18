#!/usr/bin/env python3
"""
批量为所有 skill 添加记忆系统集成

根据 skill_integration_audit.json 的结果，为每个需要集成的 skill 自动添加：
1. 项目立项逻辑
2. 任务创建逻辑
3. 品牌查询逻辑
4. 产出归档逻辑
"""

import os
import json
from pathlib import Path

OPENCLAW_ROOT = Path("/Users/a123/.openclaw")
AUDIT_REPORT = OPENCLAW_ROOT / "scripts/memory/skill_integration_audit.json"

# Skill 类型到项目类型的映射
CAMPAIGN_TYPE_MAPPING = {
    "品牌全案": "品牌全案",
    "业务对接": "业务对接",
    "海报设计": "海报设计",
    "视频生成": "视频制作",
    "详情页设计": "详情页设计",
    "产品摄影": "产品摄影",
    "通用设计": "设计项目",
    "文案创作": "文案创作",
    "策略创意": "策略制定",
}

# Skill 类型到任务类型的映射
TASK_TYPE_MAPPING = {
    "品牌全案": "campaign",
    "业务对接": "business",
    "海报设计": "poster",
    "视频生成": "video",
    "详情页设计": "detail_page",
    "产品摄影": "photography",
    "通用设计": "design",
    "文案创作": "copy",
    "策略创意": "strategy",
}

# Skill 类型到执行 agent 的映射
AGENT_MAPPING = {
    "品牌全案": "main",
    "业务对接": "main",
    "海报设计": "design",
    "视频生成": "design",
    "详情页设计": "design",
    "产品摄影": "design",
    "通用设计": "design",
    "文案创作": "copywriter",
    "策略创意": "strategy",
}

# Skill 类型到过期天数的映射
EXPIRE_DAYS_MAPPING = {
    "品牌全案": None,  # 文档永久保留
    "业务对接": None,
    "海报设计": 30,
    "视频生成": 30,
    "详情页设计": 30,
    "产品摄影": 30,
    "通用设计": 30,
    "文案创作": None,
    "策略创意": None,
}


def generate_memory_integration_section(skill_name: str, categories: list) -> str:
    """生成记忆系统集成章节"""

    # 使用第一个类别作为主类别
    primary_category = categories[0] if categories else "通用设计"

    campaign_type = CAMPAIGN_TYPE_MAPPING.get(primary_category, "通用项目")
    task_type = TASK_TYPE_MAPPING.get(primary_category, "general")
    agent = AGENT_MAPPING.get(primary_category, "main")
    expire_days = EXPIRE_DAYS_MAPPING.get(primary_category, 30)

    expire_line = f'  --expire-days {expire_days} \\' if expire_days else '  # 文档永久保留 \\'

    return f"""
## 🔴 记忆系统集成（执行前必读）

⚠️ **重要**：执行本 skill 前，必须完成项目立项和任务创建。

### Step 0: 项目立项与任务创建

```bash
# 1. 查询或创建项目（自动创建客户和品牌）
PROJECT_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/project.py get-or-create \\
  --client "${{CLIENT_NAME}}" \\
  --brand "${{BRAND_NAME}}" \\
  --project "${{PROJECT_NAME}}" \\
  --campaign-type "{campaign_type}" \\
  --json)

PROJECT_ID=$(echo $PROJECT_INFO | jq -r '.project_id')
PROJECT_PATH=$(echo $PROJECT_INFO | jq -r '.project_path')

echo "✅ 项目已就绪: $PROJECT_ID"

# 2. 创建任务
TASK_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/task.py create \\
  --project-id "$PROJECT_ID" \\
  --name "${{TASK_NAME}}" \\
  --type "{task_type}" \\
  --agent "{agent}" \\
  --skill "{skill_name}" \\
  --brief "${{TASK_BRIEF}}" \\
  --json)

TASK_ID=$(echo $TASK_INFO | jq -r '.task_id')

echo "✅ 任务已创建: $TASK_ID"

# 3. 查询品牌档案（用于指导创作）
BRAND_INFO=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand \\
  --name "${{BRAND_NAME}}" \\
  --json)

# 提取品牌信息
BRAND_TONE=$(echo $BRAND_INFO | jq -r '.brand_tone')
POSITIONING=$(echo $BRAND_INFO | jq -r '.positioning')
TARGET_AUDIENCE=$(echo $BRAND_INFO | jq -r '.target_audience')
CORE_VALUES=$(echo $BRAND_INFO | jq -r '.core_values | join(", ")')

echo "📋 品牌调性: $BRAND_TONE"
echo "📋 品牌定位: $POSITIONING"
echo "📋 目标受众: $TARGET_AUDIENCE"

# 4. 查询品牌资产（Logo、VI、参考图）
BRAND_ASSETS=$(python3 /Users/a123/.openclaw/scripts/memory/query.py assets \\
  --brand "${{BRAND_NAME}}" \\
  --json)

LOGO_PATH=$(echo $BRAND_ASSETS | jq -r '.logos[0] // empty')
if [ -n "$LOGO_PATH" ]; then
    echo "🎨 品牌 Logo: $LOGO_PATH"
fi
```

**环境变量说明**：

- `CLIENT_NAME`: 客户名称（从用户输入或上下文获取）
- `BRAND_NAME`: 品牌名称
- `PROJECT_NAME`: 项目名称（如"春节营销活动"）
- `TASK_NAME`: 任务名称（如"春节海报设计"）
- `TASK_BRIEF`: 任务简介

**品牌信息使用**：

在执行创作任务时，必须参考品牌档案中的：
- `BRAND_TONE`: 品牌调性（用于指导视觉风格和文案语气）
- `POSITIONING`: 品牌定位（用于确定传播策略）
- `TARGET_AUDIENCE`: 目标受众（用于内容方向）
- `LOGO_PATH`: 品牌 Logo（用于设计中的 Logo 使用）

---
"""


def generate_output_archive_section(skill_name: str, categories: list) -> str:
    """生成产出归档章节"""

    primary_category = categories[0] if categories else "通用设计"
    expire_days = EXPIRE_DAYS_MAPPING.get(primary_category, 30)

    if expire_days:
        expire_line = f'  --expire-days {expire_days} \\'
        expire_note = f"（{expire_days}天后自动清理）"
    else:
        expire_line = '  # 文档永久保留（不设置过期时间）\\'
        expire_note = "（永久保留）"

    return f"""

---

## 📦 产出归档（执行后必须）

任务完成后，必须将产出归档到记忆系统：

```bash
# 1. 保存产出到任务系统
python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \\
  --task-id "$TASK_ID" \\
  --file "${{OUTPUT_FILE_PATH}}" \\
  --note "${{VERSION_NOTE}}" \\
{expire_line}
  --prompt "${{GENERATION_PROMPT}}" \\
  --model "${{MODEL_USED}}" \\
  --json

echo "✅ 产出已归档{expire_note}"

# 2. 更新任务状态
python3 /Users/a123/.openclaw/scripts/memory/task.py update-status \\
  --task-id "$TASK_ID" \\
  --status "completed"

echo "✅ 任务状态已更新为完成"

# 3. 查看任务的所有版本
python3 /Users/a123/.openclaw/scripts/memory/task.py list-iterations \\
  --task-id "$TASK_ID"
```

**变量说明**：

- `OUTPUT_FILE_PATH`: 产出文件的绝对路径
- `VERSION_NOTE`: 版本说明（如"初稿"、"客户反馈后修改"）
- `GENERATION_PROMPT`: 生成时使用的 prompt（可选）
- `MODEL_USED`: 使用的模型名称（可选）

**归档后的效果**：

- ✅ 自动版本化（v1, v2, v3...）
- ✅ 记录生成参数和 prompt
- ✅ 设置过期时间{expire_note}
- ✅ 可通过任务 ID 追溯所有历史版本
- ✅ 产出文件自动复制到项目 tasks 目录下

---
"""


def integrate_skill(skill_path: Path, skill_name: str, categories: list):
    """为单个 skill 集成记忆系统"""

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"  ⚠️  SKILL.md 不存在: {skill_path}")
        return False

    # 读取现有内容
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经集成
    if "🔴 记忆系统集成" in content:
        print(f"  ℹ️  已集成，跳过")
        return True

    # 生成集成章节
    integration_section = generate_memory_integration_section(skill_name, categories)
    archive_section = generate_output_archive_section(skill_name, categories)

    # 找到插入位置（在 frontmatter 之后）
    lines = content.split('\n')
    insert_index = 0
    in_frontmatter = False

    for i, line in enumerate(lines):
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                # frontmatter 结束
                insert_index = i + 1
                break

    # 插入集成章节到开头
    lines.insert(insert_index, integration_section)

    # 添加归档章节到结尾
    new_content = '\n'.join(lines) + archive_section

    # 备份原文件
    backup_path = skill_md.parent / f"SKILL.md.backup.{os.getpid()}"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 写入新内容
    with open(skill_md, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✅ 集成完成（备份: {backup_path.name}）")
    return True


def main():
    print("🚀 开始批量集成记忆系统到所有 skill\n")

    # 加载审计报告
    with open(AUDIT_REPORT, 'r', encoding='utf-8') as f:
        audit_data = json.load(f)

    needs_integration = audit_data.get("needs_integration", [])

    print(f"📋 需要集成的 skill 数量: {len(needs_integration)}\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for item in needs_integration:
        skill_name = item["name"]
        skill_path_str = item["path"]
        categories = item["categories"]
        priority = item["priority"]
        missing = item["missing"]

        priority_label = {
            2: "🔴 高",
            1: "🟡 中",
            0: "🟢 低"
        }.get(priority, "⚪ 未知")

        print(f"{priority_label} {skill_name}")
        print(f"  路径: {skill_path_str}")
        print(f"  类别: {', '.join(categories)}")
        print(f"  缺失: {', '.join(missing)}")

        skill_path = OPENCLAW_ROOT / skill_path_str

        if not skill_path.exists():
            print(f"  ❌ 路径不存在")
            fail_count += 1
            print()
            continue

        result = integrate_skill(skill_path, skill_name, categories)

        if result:
            success_count += 1
        else:
            skip_count += 1

        print()

    # 统计总结
    print("="*80)
    print(f"✅ 集成完成: {success_count}")
    print(f"ℹ️  已跳过: {skip_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"📊 总计: {len(needs_integration)}")
    print("="*80)

    if success_count > 0:
        print(f"\n✅ 成功为 {success_count} 个 skill 添加记忆系统集成")
        print("📝 每个集成的 skill 都已创建备份文件（.backup.*）")
        print("🔍 请检查修改后的 SKILL.md 确保格式正确")


if __name__ == "__main__":
    main()
