# 记忆查询强制规范

⚠️ **所有 Agent 必读：项目/品牌查询的唯一入口**

## 问题诊断（2026-06-16）

7个不同 agent 查询"当前有几个项目"，得到了 **2/5/6/7 四种不同答案**。

**根本原因**：
1. 数据源分裂：`workspace/projects/` vs `projects/` 两个目录
2. 注册表不同步：`_registry.json` vs 实际文件系统
3. Agent 各自用不同查询方式（文件扫描/注册表/query.py）
4. `memory_search` 工具索引损坏，全部 agent 调用失败

## 强制规范

### 规则1：禁止直接扫描文件系统

❌ **禁止使用**：
```bash
# 禁止
find $WORKSPACE_DIR/projects -name "project.json"
ls -la $WORKSPACE_DIR/workspace/projects/
cat $WORKSPACE_DIR/workspace/projects/_registry.json
```

✅ **必须使用统一查询接口**：
```bash
# 列出所有项目
python3 $WORKSPACE_DIR/scripts/memory/query.py list-projects --json

# 列出所有活跃项目
python3 $WORKSPACE_DIR/scripts/memory/query.py list-projects --active --json

# 列出所有品牌
python3 $WORKSPACE_DIR/scripts/memory/query.py list-brands --json

# 查询特定品牌档案
python3 $WORKSPACE_DIR/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产
python3 $WORKSPACE_DIR/scripts/memory/query.py assets --brand "品牌名" --json

# 查询品牌的项目
python3 $WORKSPACE_DIR/scripts/memory/query.py project --brand "品牌名" --json
```

### 规则2：memory_search 失败时的降级方案

当 `memory_search` 工具返回错误时：
1. **不要**尝试修复索引（这是系统管理员的工作）
2. **不要**切换到文件系统扫描
3. **立即**使用 `query.py` 接口
4. 在回复中说明："记忆搜索当前不可用，已使用项目档案查询"

### 规则3：数据一致性检查

如果你发现：
- `query.py` 返回的项目数 < 用户预期
- 项目文件存在但查询不到
- 注册表与实际不符

**立即报告**给用户：
```
检测到项目注册表不一致：
- 统一查询接口返回：X 个项目
- 用户提到的项目：Y
- 建议运行修复脚本：
  python3 $WORKSPACE_DIR/scripts/memory/sync_registry.py
```

### 规则4：强制执行的 Agent

以下 agent 必须严格遵守：
- main / main-shared
- strategy / strategy-shared
- design / design-shared
- copywriter / copywriter-shared
- research / research-shared
- business / business-shared
- meeting-analyst / meeting-analyst-shared

## 修复记录

### 2026-06-16：检测到的问题
- 实际文件系统：17 个 project.json 文件
- query.py 返回：5 个项目
- 不同 agent 回答：2/5/6/7 四种答案
- memory_search 索引：全部失效

### 待修复
1. ✅ 统一查询接口强制规范（本文档）
2. ⏳ 修复项目注册表同步机制
3. ⏳ 重建 memory_search 索引
4. ⏳ 清理历史遗留的 workspace/projects/
