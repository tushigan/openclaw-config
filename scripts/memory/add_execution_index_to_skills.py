#!/usr/bin/env python3
"""
全量更新：为所有 skill 添加执行目录索引机制

目标：
1. 更新 project.py 和 task.py，创建时自动初始化执行目录字段
2. 更新所有 20 个 skill 的 SKILL.md，添加执行目录索引逻辑
3. 确保所有项目/任务都能回溯到实际执行工作目录和关键文件
"""

import os
import json
from pathlib import Path

OPENCLAW_ROOT = Path("/Users/a123/.openclaw")

# 执行目录索引模板
EXECUTION_INDEX_TEMPLATE = """
## 📁 执行目录索引设置

在任务执行过程中，需要维护执行目录与记忆系统的关联：

### 1. 设置执行工作目录

```bash
# 定义实际执行工作目录（根据 skill 类型调整）
EXECUTION_WORKSPACE="/Users/a123/.openclaw/workspace-design/outputs/${PROJECT_NAME}_$(date +%Y%m%d)"

# 或者
EXECUTION_WORKSPACE="/Users/a123/.openclaw/workspace-strategy/outputs/${PROJECT_NAME}_$(date +%Y%m%d)"

# 创建执行目录
mkdir -p "$EXECUTION_WORKSPACE"
```

### 2. 更新项目的执行目录索引

```bash
# 更新 project.json
python3 /Users/a123/.openclaw/scripts/memory/project.py update-execution \
  --project-id "$PROJECT_ID" \
  --execution-workspace "$EXECUTION_WORKSPACE" \
  --work-stage "策略制定"
```

### 3. 更新任务的执行目录索引

```bash
# 更新 task.json
python3 /Users/a123/.openclaw/scripts/memory/task.py update-execution \
  --task-id "$TASK_ID" \
  --execution-workspace "$EXECUTION_WORKSPACE" \
  --work-stage "初稿完成" \
  --key-file "strategy" "$EXECUTION_WORKSPACE/strategy_v1.md" \
  --key-file "wireframe" "$EXECUTION_WORKSPACE/wireframe_v1.png"
```

### 4. 创建执行索引文件（可选但推荐）

```bash
# 在项目目录创建索引文件
cat > "$PROJECT_PATH/execution_index.json" << 'EOF'
{
  "execution_workspace": "$EXECUTION_WORKSPACE",
  "key_files": {
    "strategy": "$EXECUTION_WORKSPACE/strategy_v1.md",
    "wireframe": "$EXECUTION_WORKSPACE/wireframe_v1.png",
    "final_output": "$EXECUTION_WORKSPACE/final_v1.png"
  },
  "work_stages": [
    {"stage": "策略制定", "completed_at": "2026-06-17T10:00:00"},
    {"stage": "初稿设计", "completed_at": "2026-06-17T15:00:00"}
  ],
  "last_updated": "$(date -Iseconds)"
}
EOF

# 创建可读的 README
cat > "$PROJECT_PATH/README_执行索引.md" << 'EOF'
# 执行目录索引

## 实际执行工作目录
$EXECUTION_WORKSPACE

## 关键文件
- 策略文档: strategy_v1.md
- 线框图: wireframe_v1.png
- 最终产出: final_v1.png

## 工作阶段
- [x] 策略制定
- [x] 初稿设计
- [ ] 最终成稿
EOF
```

### 5. 在执行工作目录创建回链（推荐）

```bash
# 在执行工作目录创建指向记忆系统的链接
cat > "$EXECUTION_WORKSPACE/memory_link.json" << EOF
{
  "project_id": "$PROJECT_ID",
  "task_id": "$TASK_ID",
  "project_path": "$PROJECT_PATH",
  "task_path": "$TASK_PATH",
  "memory_system_root": "/Users/a123/.openclaw/projects"
}
EOF
```

**为什么需要执行目录索引？**

1. **回溯能力**：未来回忆项目时，能准确找到所有执行文件
2. **关键文件定位**：知道策略文档、设计稿、最终产出的具体位置
3. **工作连续性**：不同 agent 接手时能快速了解工作状态和文件位置
4. **审计追溯**：完整记录从立项到交付的所有关键节点和文件

---
"""

def update_skill_md(skill_path: Path, skill_name: str):
    """为单个 skill 添加执行目录索引章节"""

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"  ⚠️  SKILL.md 不存在: {skill_path}")
        return False

    # 读取内容
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经有执行目录索引
    if "执行目录索引设置" in content:
        print(f"  ℹ️  已包含执行目录索引，跳过")
        return True

    # 找到产出归档章节的位置（在 Step Final 之后插入）
    if "## 📦 产出归档" in content:
        # 在产出归档章节之前插入
        content = content.replace(
            "## 📦 产出归档",
            EXECUTION_INDEX_TEMPLATE + "\n## 📦 产出归档"
        )
    elif "Step Final" in content or "产出归档" in content:
        # 如果有其他形式的归档章节，在末尾添加
        content += "\n" + EXECUTION_INDEX_TEMPLATE
    else:
        # 如果没有归档章节，直接在末尾添加
        content += "\n" + EXECUTION_INDEX_TEMPLATE

    # 备份
    backup_path = skill_md.parent / f"SKILL.md.backup.execution_index"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 写入
    with open(skill_md, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✅ 已添加执行目录索引章节")
    return True

def main():
    print("=" * 80)
    print("全量更新：为所有 skill 添加执行目录索引机制")
    print("=" * 80)
    print()

    # 需要更新的 skill 列表（20个）
    skills = [
        ("skills/boss", "boss"),
        ("workspace-business/skills/business-project-intake", "business-project-intake"),
        ("workspace-design/skills/xiangqingye-desigen", "xiangqingye-desigen"),
        ("workspace-design/skills/product-photography-workflow", "product-photography-workflow"),
        ("skills/kefu-ae", "kefu-ae"),
        ("workspace-business/skills/quote-skill", "quote-skill"),
        ("workspace-design/skills/brand-poster-creator", "brand-poster-creator"),
        ("workspace-design/skills/brand-poster-distiller", "brand-poster-distiller"),
        ("skills/tvc-director", "tvc-director"),
        ("workspace-design/skills/video-expert-analyzer", "video-expert-analyzer"),
        ("workspace-design/skills/dreamina-reference-video", "dreamina-reference-video"),
        ("workspace-design/skills/dreamina-cli", "dreamina-cli"),
        ("workspace-design/skills/sheji", "sheji"),
        ("workspace-design/skills/gpt-image2-gen", "gpt-image2-gen"),
        ("workspace-design/skills/image-deglaze", "image-deglaze"),
        ("workspace-design/skills/image-upscale-realesrgan", "image-upscale-realesrgan"),
        ("workspace-strategy/skills/huashu-design", "huashu-design"),
        ("workspace-strategy/skills/wenan", "wenan"),
        ("workspace-strategy/skills/celue-zj", "celue-zj"),
        ("workspace-strategy/skills/chuangyi-zj", "chuangyi-zj"),
    ]

    success_count = 0
    skip_count = 0
    fail_count = 0

    for skill_path_str, skill_name in skills:
        print(f"处理: {skill_name}")
        print(f"  路径: {skill_path_str}")

        skill_path = OPENCLAW_ROOT / skill_path_str

        if not skill_path.exists():
            print(f"  ❌ 路径不存在")
            fail_count += 1
            print()
            continue

        result = update_skill_md(skill_path, skill_name)

        if result:
            success_count += 1
        else:
            skip_count += 1

        print()

    # 统计
    print("=" * 80)
    print("更新完成")
    print("=" * 80)
    print(f"✅ 成功: {success_count}")
    print(f"ℹ️  跳过: {skip_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"📊 总计: {len(skills)}")
    print()

    if success_count > 0:
        print(f"✅ 已为 {success_count} 个 skill 添加执行目录索引机制")
        print()
        print("下一步：")
        print("1. 更新 project.py 添加 update-execution 命令")
        print("2. 更新 task.py 添加 update-execution 命令")
        print("3. 测试执行目录索引功能")

if __name__ == "__main__":
    main()
