#!/bin/bash
# 批量更新所有 workspace 的 AGENTS.md，添加记忆查询强制规范

set -e

OPENCLAW_ROOT="/Users/a123/.openclaw"
NOTICE_TEXT='

---

## ⚠️ 记忆查询强制规范（2026-06-16 新增）

**查询项目/品牌信息时，必须使用统一查询接口**，禁止直接扫描文件系统或读取 `_registry.json`。

详细规范：[/Users/a123/.openclaw/scripts/memory/AGENT_QUERY_RULES.md](/Users/a123/.openclaw/scripts/memory/AGENT_QUERY_RULES.md)

**快速参考**：
```bash
# 列出所有项目（包括非 active）
python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects --json

# 只列出 active 项目
python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects --active --json

# 查询品牌档案
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json
```

**禁止使用**：
- ❌ `find $WORKSPACE_DIR/projects -name "project.json"`
- ❌ `cat $WORKSPACE_DIR/projects/_registry.json`
- ❌ 直接扫描文件系统
- ❌ 依赖 `memory_search` 工具（当前索引已损坏）

---
'

for workspace in workspace-strategy workspace-research workspace-design workspace-meeting workspace-copywriter workspace-business; do
  agents_file="$OPENCLAW_ROOT/$workspace/AGENTS.md"

  if [ ! -f "$agents_file" ]; then
    echo "跳过 $workspace (AGENTS.md 不存在)"
    continue
  fi

  echo "处理 $agents_file"

  # 检查是否已经包含规范
  if grep -q "AGENT_QUERY_RULES\|记忆查询强制规范" "$agents_file"; then
    echo "  ✓ 已包含记忆查询规范，跳过"
    continue
  fi

  # 在第一个 ## 0. 总原则 之后添加规范
  if grep -q "^## 0\. 总原则" "$agents_file"; then
    # 找到 "## 0. 总原则" 后的第一个 ### 之前插入
    awk -v notice="$NOTICE_TEXT" '
      /^## 0\. 总原则/ {
        print
        in_section = 1
        next
      }
      in_section && /^### / && !inserted {
        print notice
        inserted = 1
      }
      { print }
    ' "$agents_file" > "$agents_file.new"

    mv "$agents_file.new" "$agents_file"
    echo "  ✓ 已在 '## 0. 总原则' 后添加规范"
  else
    # 如果没有 ## 0. 总原则，在文件开头的第一个 ## 标题之前添加
    awk -v notice="$NOTICE_TEXT" '
      /^## / && !inserted {
        print notice
        inserted = 1
      }
      { print }
    ' "$agents_file" > "$agents_file.new"

    mv "$agents_file.new" "$agents_file"
    echo "  ✓ 已在第一个 ## 标题前添加规范"
  fi
done

echo ""
echo "=== 完成 ==="
echo "已更新所有 workspace 的 AGENTS.md 文件"
