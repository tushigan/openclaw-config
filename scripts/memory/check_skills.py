#!/usr/bin/env python3
"""
OpenClaw 顶层记忆系统 - Skill 集成检查和更新
检查所有 skill，识别需要集成记忆系统的 skill，并生成更新建议
"""

import os
import re
from pathlib import Path

# 需要检查的关键词
MEMORY_KEYWORDS = [
    "品牌", "brand", "项目", "project", "客户", "client",
    "档案", "profile", "记忆", "memory",
    "workspace/projects", "workspace-business/projects",
    "_brand-profile", "project.json"
]

# 需要集成记忆系统的 skill 特征
INTEGRATION_PATTERNS = {
    "brand_related": r"(品牌|brand|调性|定位|positioning|brand_tone|target_audience)",
    "project_related": r"(项目|project|campaign|全案|brief|策略|strategy|创意|creative)",
    "image_generation": r"(生图|生成|海报|poster|设计|design|视觉|visual)",
    "copywriting": r"(文案|copy|写作|writing)",
    "business": r"(商务|业务|报价|quote|合同|contract)"
}


def scan_skill_file(skill_path: str) -> dict:
    """扫描 skill 文件，检测是否需要集成记忆系统"""

    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        "skill_path": skill_path,
        "skill_name": os.path.basename(os.path.dirname(skill_path)),
        "needs_memory": False,
        "reasons": [],
        "patterns_found": [],
        "old_paths_found": [],
        "integration_level": "none"  # none/low/medium/high
    }

    # 检查关键词
    keyword_matches = []
    for keyword in MEMORY_KEYWORDS:
        if keyword in content:
            keyword_matches.append(keyword)

    if keyword_matches:
        result["needs_memory"] = True
        result["reasons"].append(f"包含记忆相关关键词: {', '.join(keyword_matches[:5])}")

    # 检查旧路径
    old_paths = []
    if "workspace/projects" in content:
        old_paths.append("workspace/projects")
    if "workspace-business/projects" in content:
        old_paths.append("workspace-business/projects")

    if old_paths:
        result["old_paths_found"] = old_paths
        result["reasons"].append(f"使用旧项目路径: {', '.join(old_paths)}")

    # 检查集成模式
    for pattern_name, pattern in INTEGRATION_PATTERNS.items():
        if re.search(pattern, content, re.IGNORECASE):
            result["patterns_found"].append(pattern_name)

    # 判断集成级别
    if "brand_related" in result["patterns_found"] or "project_related" in result["patterns_found"]:
        result["integration_level"] = "high"
        result["needs_memory"] = True
    elif "image_generation" in result["patterns_found"] or "copywriting" in result["patterns_found"]:
        result["integration_level"] = "medium"
        result["needs_memory"] = True
    elif "business" in result["patterns_found"]:
        result["integration_level"] = "high"
        result["needs_memory"] = True
    elif keyword_matches:
        result["integration_level"] = "low"

    return result


def generate_integration_guide(scan_result: dict) -> str:
    """生成集成指南"""

    skill_name = scan_result["skill_name"]
    level = scan_result["integration_level"]

    if level == "none":
        return None

    guide = f"""
## {skill_name} - 记忆系统集成指南

**集成级别**: {level.upper()}
**原因**: {'; '.join(scan_result['reasons'])}

### 推荐集成方式:
"""

    if level == "high":
        guide += """
1. **在 SKILL.md 开头添加记忆查询规则**:
   ```markdown
   ## 记忆系统集成（必读）

   执行本 skill 前，必须先查询相关品牌/项目记忆:

   ```bash
   # 查询品牌档案
   python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

   # 查询活跃项目
   python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json

   # 查询品牌资产
   python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json
   ```

   记忆数据用于:
   - 品牌调性、定位、目标受众
   - 品牌资产（Logo、VI、参考图）
   - 项目上下文（策略、创意方向）
   ```

2. **更新所有脚本中的项目路径**:
   - 旧路径: `workspace/projects/品牌名/`
   - 新路径: `/Users/a123/.openclaw/projects/客户名/品牌名/项目名/`

3. **产出归档到任务系统**:
   ```bash
   # 保存任务产出（自动创建版本）
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \\
     --task-id "TASK-xxx" \\
     --file "/path/to/output.png" \\
     --expire-days 30
   ```
"""

    elif level == "medium":
        guide += """
1. **在执行前查询品牌信息**:
   ```bash
   python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json
   ```

2. **使用品牌调性、目标受众等信息优化产出**

3. **可选：产出归档到记忆系统**
"""

    else:  # low
        guide += """
1. **了解记忆查询接口**:
   - 可在需要时调用 `scripts/memory/query.py`
   - 当前无强制集成要求
"""

    if scan_result["old_paths_found"]:
        guide += f"""

### ⚠️ 路径迁移（必须）:
检测到旧路径: {', '.join(scan_result['old_paths_found'])}

**迁移步骤**:
1. 全局替换路径引用
2. 更新脚本中的目录结构假设
3. 测试所有文件读写操作
"""

    return guide


def main():
    skill_files = [
        "./skills/anysearch/SKILL.md",
        "./skills/boss/SKILL.md",
        "./skills/kefu-ae/SKILL.md",
        "./workspace-business/skills/business-project-intake/SKILL.md",
        "./workspace-business/skills/quote-skill/SKILL.md",
        "./workspace-copywriter/skills/wenan/SKILL.md",
        "./workspace-design/skills/brand-poster-creator/SKILL.md",
        "./workspace-design/skills/brand-poster-distiller/SKILL.md",
        "./workspace-design/skills/dreamina-reference-video/SKILL.md",
        "./workspace-design/skills/gpt-image2-gen/SKILL.md",
        "./workspace-design/skills/product-photography-workflow/SKILL.md",
        "./workspace-design/skills/sheji/SKILL.md",
        "./workspace-design/skills/xiangqingye-desigen/SKILL.md",
        "./workspace-strategy/skills/celue-zj/SKILL.md",
        "./workspace-strategy/skills/chuangyi-zj/SKILL.md",
    ]

    print("=" * 70)
    print("OpenClaw Skill 记忆系统集成检查")
    print("=" * 70)

    high_priority = []
    medium_priority = []
    low_priority = []
    no_integration = []

    for skill_file in skill_files:
        if not os.path.exists(skill_file):
            continue

        print(f"\n检查: {skill_file}")
        result = scan_skill_file(skill_file)

        if result["integration_level"] == "high":
            high_priority.append(result)
            print("  🔴 高优先级 - 必须集成")
        elif result["integration_level"] == "medium":
            medium_priority.append(result)
            print("  🟡 中优先级 - 建议集成")
        elif result["integration_level"] == "low":
            low_priority.append(result)
            print("  🟢 低优先级 - 可选集成")
        else:
            no_integration.append(result)
            print("  ⚪ 无需集成")

        if result["reasons"]:
            for reason in result["reasons"]:
                print(f"     - {reason}")

    # 生成报告
    print("\n" + "=" * 70)
    print("📊 集成检查报告")
    print("=" * 70)
    print(f"🔴 高优先级: {len(high_priority)} 个")
    print(f"🟡 中优先级: {len(medium_priority)} 个")
    print(f"🟢 低优先级: {len(low_priority)} 个")
    print(f"⚪ 无需集成: {len(no_integration)} 个")

    # 生成集成指南
    guide_path = "/Users/a123/.openclaw/scripts/memory/SKILL_INTEGRATION_GUIDE.md"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write("# OpenClaw Skill 记忆系统集成指南\n\n")
        f.write(f"生成时间: {os.popen('date').read().strip()}\n\n")
        f.write("---\n\n")

        f.write("## 🔴 高优先级 Skill（必须集成）\n\n")
        for result in high_priority:
            guide = generate_integration_guide(result)
            if guide:
                f.write(guide)
                f.write("\n---\n\n")

        f.write("## 🟡 中优先级 Skill（建议集成）\n\n")
        for result in medium_priority:
            guide = generate_integration_guide(result)
            if guide:
                f.write(guide)
                f.write("\n---\n\n")

        f.write("## 🟢 低优先级 Skill（可选集成）\n\n")
        for result in low_priority:
            f.write(f"- {result['skill_name']}\n")

    print(f"\n✅ 集成指南已生成: {guide_path}")

    # 输出高优先级列表
    print("\n" + "=" * 70)
    print("🔴 高优先级 Skill（需要立即更新）:")
    print("=" * 70)
    for result in high_priority:
        print(f"  • {result['skill_name']}")
        if result['old_paths_found']:
            print(f"    ⚠️ 使用旧路径: {', '.join(result['old_paths_found'])}")

    return high_priority


if __name__ == '__main__':
    main()
