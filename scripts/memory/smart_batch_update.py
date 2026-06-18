#!/usr/bin/env python3
"""
智能批量更新所有高优先级 skill，自动检测标题并添加记忆系统集成指南
"""

import os
import re

# 通用的记忆系统集成模板
MEMORY_INTEGRATION_TEMPLATE = """
## 记忆系统集成（必读）

⚠️ **执行本 skill 前，必须先查询相关品牌档案**

### 查询品牌信息
```bash
# 查询品牌档案（获取调性、定位、目标受众）
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产（获取 Logo、VI 手册、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json

# 查询项目上下文（获取策略、创意方向）
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json
```

### 关键信息提取
从品牌档案中提取：
- **品牌调性** (`brand_tone`) - 决定整体风格和情绪
- **定位** (`positioning`) - 决定表达层级和差异点
- **目标受众** (`target_audience`) - 决定语境和沟通方式
- **核心价值观** (`core_values`) - 决定价值主张

### 品牌一致性要求
- 所有产出必须符合品牌调性
- 表达方式必须匹配目标受众
- 价值主张必须呼应品牌核心价值观
- 使用品牌资产库中的官方素材（Logo、VI 等）

"""

SKILL_PATHS = [
    "/Users/a123/.openclaw/skills/kefu-ae/SKILL.md",
    "/Users/a123/.openclaw/workspace-business/skills/quote-skill/SKILL.md",
    "/Users/a123/.openclaw/workspace-design/skills/brand-poster-distiller/SKILL.md",
    "/Users/a123/.openclaw/workspace-design/skills/dreamina-reference-video/SKILL.md",
    "/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/SKILL.md",
    "/Users/a123/.openclaw/workspace-design/skills/sheji/SKILL.md",
    "/Users/a123/.openclaw/workspace-design/skills/xiangqingye-desigen/SKILL.md",
    "/Users/a123/.openclaw/workspace-strategy/skills/celue-zj/SKILL.md",
    "/Users/a123/.openclaw/workspace-strategy/skills/chuangyi-zj/SKILL.md",
]


def update_skill(file_path):
    """更新单个 skill 文件"""
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经包含记忆系统集成
    if "记忆系统集成" in content or "OpenClaw 顶层记忆系统" in content:
        skill_name = os.path.basename(os.path.dirname(file_path))
        print(f"✅ {skill_name} - 已包含，跳过")
        return False

    # 查找第一个 # 标题（不是 frontmatter）
    lines = content.split('\n')
    insert_index = -1

    in_frontmatter = False
    for i, line in enumerate(lines):
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            continue

        if not in_frontmatter and line.startswith('# '):
            # 找到第一个标题，在下一行插入
            insert_index = i + 1
            break

    if insert_index == -1:
        skill_name = os.path.basename(os.path.dirname(file_path))
        print(f"⚠️ {skill_name} - 未找到插入位置")
        return False

    # 插入记忆系统集成部分
    lines.insert(insert_index, MEMORY_INTEGRATION_TEMPLATE)
    new_content = '\n'.join(lines)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    skill_name = os.path.basename(os.path.dirname(file_path))
    print(f"✅ {skill_name} - 已添加记忆系统集成")
    return True


def main():
    print("=" * 70)
    print("智能批量更新 Skill - 添加记忆系统集成")
    print("=" * 70)

    updated = 0
    failed = 0
    skipped = 0

    for file_path in SKILL_PATHS:
        try:
            result = update_skill(file_path)
            if result:
                updated += 1
            elif result is False and "已包含" in str(result):
                skipped += 1
        except Exception as e:
            print(f"❌ 更新失败: {file_path}")
            print(f"   错误: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"✅ 完成！更新了 {updated} 个 skill，跳过 {skipped} 个，{failed} 个失败")
    print("=" * 70)


if __name__ == '__main__':
    main()
