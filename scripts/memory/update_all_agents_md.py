#!/usr/bin/env python3
"""
快速更新所有 workspace 的 AGENTS.md，添加记忆系统使用规范
"""

import os

MEMORY_INTEGRATION_SECTION = """
## 记忆系统集成（所有 Agent 必读）

⚠️ **OpenClaw 顶层记忆系统已启用** - 所有 agent 和 skill 必须使用统一的记忆查询接口。

### 核心原则

1. **执行任何品牌相关任务前，先查询品牌档案**
2. **产出必须符合品牌调性、定位、目标受众**
3. **项目产出自动归档到记忆系统**
4. **品牌关键信息变更会触发冲突检测，需用户确认**

### 统一查询接口

```bash
# 查询品牌档案（获取调性、定位、受众、核心价值）
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产（获取 Logo、VI 手册、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json

# 查询活跃项目（获取策略、创意方向、项目上下文）
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json

# 查询指定项目
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --campaign "项目名" --json

# 列出所有品牌
python3 /Users/a123/.openclaw/scripts/memory/query.py list-brands --json

# 列出所有活跃项目
python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects --json
```

### 典型使用场景

#### 场景 1：生图任务（design agent）
```bash
# 1. 查询品牌档案
brand_data=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "优食家族" --json)

# 2. 提取品牌调性、定位
# brand_tone: "温柔、治愈"
# positioning: "儿童营养零食"
# target_audience: "3-12岁儿童的妈妈"

# 3. 查询品牌资产
assets=$(python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "优食家族" --json)

# 4. 使用 Logo 路径和品牌调性生成图片
# logos: ["/path/to/logo.png"]

# 5. 生成时确保符合品牌调性
```

#### 场景 2：文案任务（copywriter agent）
```bash
# 1. 查询品牌档案
brand_data=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "优食家族" --json)

# 2. 查询项目上下文（获取策略、创意方向）
project_data=$(python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "优食家族" --active --json)

# 3. 基于品牌调性、策略、创意方向撰写文案
```

#### 场景 3：策略任务（strategy agent）
```bash
# 1. 查询品牌档案
brand_data=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "优食家族" --json)

# 2. 提取品牌定位、目标受众、核心价值
# 3. 基于品牌基础制定策略
```

### 记忆系统目录结构

```
/Users/a123/.openclaw/projects/  # ⚠️ 所有项目数据统一在根目录
├── _registry.json
├── 客户名/
│   ├── _client-profile.json    # 客户档案
│   └── 品牌名/
│       ├── _brand-profile.json  # 品牌档案（调性、定位、受众、价值观）
│       ├── _brand-assets/       # 品牌资产库
│       │   ├── logos/
│       │   ├── vi-manual/
│       │   └── reference-images/
│       └── 项目名/
│           ├── project.json     # 项目档案
│           ├── brief.json
│           ├── strategy.json
│           ├── creative-direction.json
│           ├── materials/
│           └── outputs/
```

### 冲突检测机制

当尝试更新品牌关键字段时（调性、定位、目标受众、核心价值观），系统会：

1. 检测字段变更
2. 分析影响范围（关联项目数量、活跃项目）
3. 生成用户确认请求
4. 用户确认后才执行更新
5. 记录变更历史

示例：
```bash
python3 /Users/a123/.openclaw/scripts/memory/brand.py update \
  --client "客户名" \
  --name "品牌名" \
  --field "brand_tone" \
  --value "活力、年轻"

# 输出：
# ⚠️ 检测到品牌档案变更
# 品牌：优食家族
# 字段：brand_tone
# 原值：温柔、治愈
# 新值：活力、年轻
#
# 影响范围：
# - 关联项目总数：3 个
# - 活跃项目：2 个
# - 品牌调性变更将影响后续所有创意和视觉产出
#
# 是否确认此变更？
# • 若确认，请在命令中添加 --user-confirmed 参数重新执行
```

### 执行规范

1. **禁止硬编码路径** - 始终通过查询接口获取路径
2. **禁止假设品牌信息** - 必须从档案读取
3. **禁止绕过冲突检测** - 关键字段变更必须用户确认
4. **产出必须归档** - 所有最终产出应保存到记忆系统

### 常见错误

❌ 直接假设品牌调性："这个品牌应该是年轻活力的"
✅ 查询品牌档案，使用实际记录的调性

❌ 使用旧路径：`workspace/projects/品牌名/`
✅ 使用新路径：`/Users/a123/.openclaw/projects/客户名/品牌名/项目名/`

❌ 跳过品牌档案查询直接生图
✅ 先查询品牌档案和资产，再生成

---
"""


def update_agents_md(workspace_path: str):
    """更新 workspace 的 AGENTS.md"""
    agents_md_path = os.path.join(workspace_path, "AGENTS.md")

    if not os.path.exists(agents_md_path):
        print(f"⚠️ {agents_md_path} 不存在，跳过")
        return False

    with open(agents_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经包含记忆系统集成部分
    if "记忆系统集成" in content or "OpenClaw 顶层记忆系统" in content:
        print(f"✅ {workspace_path} - 已包含记忆系统集成，跳过")
        return False

    # 在文件开头添加记忆系统集成部分
    new_content = MEMORY_INTEGRATION_SECTION + "\n" + content

    with open(agents_md_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ {workspace_path} - 已添加记忆系统集成")
    return True


def main():
    workspaces = [
        "/Users/a123/.openclaw/workspace",
        "/Users/a123/.openclaw/workspace-strategy",
        "/Users/a123/.openclaw/workspace-design",
        "/Users/a123/.openclaw/workspace-copywriter",
        "/Users/a123/.openclaw/workspace-research",
        "/Users/a123/.openclaw/workspace-business",
        "/Users/a123/.openclaw/workspace-meeting",
    ]

    print("=" * 70)
    print("批量更新 workspace AGENTS.md - 添加记忆系统集成")
    print("=" * 70)

    updated = 0
    for workspace in workspaces:
        if os.path.exists(workspace):
            if update_agents_md(workspace):
                updated += 1

    print("\n" + "=" * 70)
    print(f"✅ 完成！更新了 {updated} 个 workspace")
    print("=" * 70)


if __name__ == '__main__':
    main()
