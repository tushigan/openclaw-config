#!/usr/bin/env python3
"""
批量为 skill 集成记忆系统查询规则
"""

import os
import sys

MEMORY_INTEGRATION_TEMPLATE = '''## 🔴 记忆系统集成（执行前必读）

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

'''

SKILLS = [
    ("wenan", "workspace-copywriter", "copywriter", "copywriting", "文案创作"),
    ("brand-poster-creator", "workspace-design", "design", "design", "品牌海报"),
    ("brand-poster-distiller", "workspace-design", "design", "design", "品牌海报"),
    ("dreamina-reference-video", "workspace-design", "design", "video", "视频创作"),
    ("gpt-image2-gen", "workspace-design", "design", "design", "图片生成"),
    ("product-photography-workflow", "workspace-design", "design", "design", "产品摄影"),
    ("sheji", "workspace-design", "design", "design", "视觉设计"),
    ("xiangqingye-desigen", "workspace-design", "design", "design", "详情页设计"),
    ("celue-zj", "workspace-strategy", "strategy", "strategy", "策略制定"),
    ("chuangyi-zj", "workspace-strategy", "strategy", "creative", "创意方向"),
]


def integrate_skill(skill_name, workspace, agent, task_type, campaign_type):
    """为 skill 集成记忆系统"""
    skill_path = f"/Users/a123/.openclaw/{workspace}/skills/{skill_name}/SKILL.md"

    if not os.path.exists(skill_path):
        print(f"❌ {skill_name}: 文件不存在 {skill_path}")
        return False

    # 读取原文件
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经集成
    if '## 🔴 记忆系统集成（执行前必读）' in content:
        print(f"⏭️  {skill_name}: 已经集成，跳过")
        return True

    # 生成集成内容
    integration = MEMORY_INTEGRATION_TEMPLATE.format(
        skill_name=skill_name,
        agent=agent,
        task_type=task_type,
        campaign_type=campaign_type
    )

    # 在 frontmatter 后插入
    lines = content.split('\n')
    insert_pos = 0

    # 找到 frontmatter 结束位置
    in_frontmatter = False
    for i, line in enumerate(lines):
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                insert_pos = i + 1
                break

    # 插入集成内容
    lines.insert(insert_pos, '\n' + integration)
    new_content = '\n'.join(lines)

    # 写回文件
    with open(skill_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ {skill_name}: 集成完成")
    return True


def main():
    print("开始批量集成记忆系统...\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for skill_name, workspace, agent, task_type, campaign_type in SKILLS:
        result = integrate_skill(skill_name, workspace, agent, task_type, campaign_type)
        if result is True:
            success_count += 1
        elif result is False:
            fail_count += 1
        else:
            skip_count += 1

    print(f"\n=== 集成完成 ===")
    print(f"✅ 成功: {success_count}")
    print(f"⏭️  跳过: {skip_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"总计: {len(SKILLS)}")


if __name__ == '__main__':
    main()
