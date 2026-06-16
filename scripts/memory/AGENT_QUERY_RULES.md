# Agent 记忆查询强制规范

**适用范围**：所有 OpenClaw agent（main, strategy, research, design, meeting-analyst, copywriter, business 及其 shared 变体）

---

## 问题诊断（2026-06-16）

7个不同 agent 查询"当前有几个项目"，得到了 **2/5/6/7 四种不同答案**。

**根本原因**：
1. ❌ 数据源分裂：部分 agent 扫描文件系统，部分读注册表，部分用 query.py
2. ❌ 深度不一致：3层扫描只能找到9个，递归扫描能找到22个
3. ❌ `memory_search` 工具索引损坏，全部失效

---

## ✅ 唯一正确的查询方式

### 列出所有项目（包括非 active）

```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects --json
```

返回：**22个项目**（包括 active、completed、子项目、测试项目）

### 只列出 active 项目

```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects --active --json
```

返回：**5个 active 项目**（不含子项目）

### 查询特定品牌

```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json
```

### 查询品牌资产

```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json
```

### 查询品牌的所有项目

```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --json
```

### 列出所有品牌

```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py list-brands --json
```

---

## ❌ 禁止使用的查询方式

### 禁止直接扫描文件系统

```bash
# ❌ 禁止
find $WORKSPACE_DIR/projects -name "project.json"
ls -la $WORKSPACE_DIR/workspace/projects/
for dir in $WORKSPACE_DIR/projects/*/*/; do ...; done
```

**原因**：
- 路径结构不规范（有些3层，有些4层，有些嵌套在 outputs/ 下）
- 会扫描到测试项目和子项目
- 不同 agent 实现的扫描逻辑不一致

### 禁止直接读注册表

```bash
# ❌ 禁止
cat $WORKSPACE_DIR/projects/_registry.json
cat $WORKSPACE_DIR/workspace/projects/_registry.json
```

**原因**：
- 注册表只记录1个项目，严重过时
- 有多个历史版本的注册表文件
- 注册机制已失效

### 禁止依赖 memory_search 工具

```bash
# ❌ 当前不可用
# memory_search 索引已损坏，全部 agent 调用都会失败
```

**降级方案**：
- `memory_search` 失败时，立即切换到 `query.py`
- 在回复中说明："记忆搜索当前不可用，已使用项目档案查询"

---

## 📊 数据验证（2026-06-16）

| 查询方式 | 返回数量 | 说明 |
|---------|---------|------|
| `query.py list-projects` | **22个** | ✅ 正确：包含所有项目 |
| `query.py list-projects --active` | **5个** | ✅ 正确：只含 active 状态项目 |
| 文件系统 3层扫描 | 9个 | ❌ 错误：漏掉子项目和嵌套项目 |
| 读 `_registry.json` | 1个 | ❌ 错误：注册表严重过时 |
| `memory_search` | 失败 | ❌ 错误：索引损坏 |

---

## 🔧 如何判断数据不一致

如果你在查询时发现：
- 用户提到的项目查询不到
- 项目数量明显少于预期
- 不同查询方式返回不同结果

**立即报告给用户**：

```
⚠️ 检测到项目数据不一致

查询结果：X 个项目
用户预期：Y 个项目

建议运行数据修复：
  python3 /Users/a123/.openclaw/scripts/memory/sync_registry.py

或联系管理员检查项目目录结构。
```

---

## 📝 修复记录

### 2026-06-16 修复内容

1. ✅ `query.py` 改为递归扫描（不限深度）
2. ✅ 添加 `--active` 和 `--all` 参数
3. ✅ 添加 `is_subproject` 字段标记子项目
4. ✅ 添加 `path` 字段显示完整相对路径
5. ✅ 创建本强制规范文档
6. ✅ 更新 `workspace/AGENTS.md` 添加强制规范引用

### 待修复

- ⏳ 清理历史遗留的 `workspace/projects/` 目录
- ⏳ 修复 `projects/projects/` 双层嵌套路径
- ⏳ 重建 `memory_search` 索引
- ⏳ 统一项目 status 字段（当前有 unknown/active/completed/revising/references_generated 等）
- ⏳ 清理测试项目（Boss测试客户_*）
