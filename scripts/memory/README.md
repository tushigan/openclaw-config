# OpenClaw 顶层记忆系统

## ⚠️ 重要更新（2026-06-15）：自动注册机制已修复

**问题**：品牌档案创建后未自动注册到 `_registry.json`，导致查询失败

**修复方案**：
1. ✅ 修复 `agency_project/project.py` 中的 `create_or_get_brand()` 函数
2. ✅ 添加 `_sync_brand_to_registry()` 自动同步机制
3. ✅ 新增 `sync_registry.py` 一致性修复工具
4. ✅ 新增 `healthcheck.py` 健康检查工具

**现在的行为**：创建品牌/客户时**自动注册到全局注册表**，查询系统可立即发现新数据

---

## 概述

OpenClaw 顶层记忆系统是一个统一的、5层架构的项目记忆框架，供所有 agent 和 skill 共享使用。

**架构层级**：客户 → 品牌 → 项目 → 任务 → 迭代版本

**核心位置**：`/Users/a123/.openclaw/projects/`（根目录，所有 agent 平等访问）

## ⚠️ 重要更新（2026-06-15）：自动注册机制已修复

**问题**：品牌档案创建后未自动注册到 `_registry.json`，导致查询失败

**修复方案**：
1. ✅ 修复 `agency_project/project.py` 中的 `create_or_get_brand()` 函数
2. ✅ 添加 `_sync_brand_to_registry()` 自动同步机制
3. ✅ 新增 `sync_registry.py` 一致性修复工具
4. ✅ 新增 `healthcheck.py` 健康检查工具

**现在的行为**：创建品牌/客户时**自动注册到全局注册表**，查询系统可立即发现新数据

## 快速开始

### 基础查询（最常用）

```bash
# 查询品牌档案
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 查询品牌资产（Logo、VI、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json

# 查询活跃项目
python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "品牌名" --active --json

# 列出所有品牌
python3 /Users/a123/.openclaw/scripts/memory/query.py list-brands

# 列出所有活跃项目
python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects
```

### 维护工具（新增）

```bash
# 健康检查（推荐定期运行）
python3 /Users/a123/.openclaw/scripts/memory/healthcheck.py

# 修复注册表不一致（如果健康检查发现问题）
python3 /Users/a123/.openclaw/scripts/memory/sync_registry.py

# 预览模式（不实际修改）
python3 /Users/a123/.openclaw/scripts/memory/sync_registry.py --dry-run
```

### 维护工具（新增）

```bash
# 健康检查（推荐定期运行）
python3 /Users/a123/.openclaw/scripts/memory/healthcheck.py

# 修复注册表不一致（如果健康检查发现问题）
python3 /Users/a123/.openclaw/scripts/memory/sync_registry.py

# 预览模式（不实际修改）
python3 /Users/a123/.openclaw/scripts/memory/sync_registry.py --dry-run
```

### 管理操作

```bash
# 创建客户
python3 /Users/a123/.openclaw/scripts/memory/client.py create \
  --name "客户名" --industry "行业" --company-type "甲方"

# 创建品牌
python3 /Users/a123/.openclaw/scripts/memory/brand.py create \
  --client "客户名" \
  --name "品牌名" \
  --positioning "定位" \
  --brand-tone "品牌调性" \
  --target-audience "目标受众" \
  --core-values "价值1" "价值2"

# 更新品牌（带冲突检测）
python3 /Users/a123/.openclaw/scripts/memory/brand.py update \
  --client "客户名" \
  --name "品牌名" \
  --field "brand_tone" \
  --value "新调性"
```

## 目录结构

```
/Users/a123/.openclaw/projects/
├── _registry.json              # 全局注册表
├── 客户名/                      # 第1层：客户
│   ├── _client-profile.json    # 客户档案
│   └── 品牌名/                  # 第2层：品牌
│       ├── _brand-profile.json     # 品牌档案
│       ├── _brand-assets/          # 品牌资产库
│       │   ├── logos/
│       │   ├── vi-manual/
│       │   └── reference-images/
│       └── 项目名/                  # 第3层：项目
│           ├── project.json
│           ├── brief.json
│           ├── strategy.json
│           ├── creative-direction.json
│           ├── materials/
│           ├── outputs/
│           └── tasks/              # 第4层：任务
│               └── TASK-xxx/
│                   └── iterations/  # 第5层：版本
```

## 核心特性

### 1. 统一查询接口

所有 agent 和 skill 通过统一的查询接口访问记忆，确保数据一致性。

### 2. 冲突检测

更新品牌关键字段（调性、定位、目标受众、核心价值观）时，系统会：
- 检测变更
- 分析影响范围
- 要求用户确认
- 记录变更历史

### 3. 版本管理

- 产出文件自动版本化（v1, v2, v3...）
- 图片/视频：30天后自动清理
- 文档：永久保留

### 4. 跨 Agent 共享

所有 agent（main、design、strategy、copywriter、research、business 等）都能读写记忆系统。

## 使用规范

### 必须遵守的规则

1. **执行品牌相关任务前，先查询品牌档案**
2. **使用品牌调性、定位、目标受众指导产出**
3. **不硬编码路径，始终通过查询接口获取**
4. **品牌关键信息变更必须用户确认**

### 典型工作流

#### 设计任务（design agent）

```bash
# 1. 查询品牌档案
brand=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "优食家族" --json)

# 2. 提取品牌信息
# brand_tone: "温柔、治愈"
# positioning: "儿童营养零食"
# target_audience: "3-12岁儿童的妈妈"

# 3. 查询品牌资产
assets=$(python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "优食家族" --json)

# 4. 使用 Logo 和调性生成设计
```

#### 文案任务（copywriter agent）

```bash
# 1. 查询品牌档案
brand=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "优食家族" --json)

# 2. 查询项目上下文（策略、创意方向）
project=$(python3 /Users/a123/.openclaw/scripts/memory/query.py project --brand "优食家族" --active --json)

# 3. 基于品牌调性和策略撰写文案
```

#### 策略任务（strategy agent）

```bash
# 1. 查询品牌档案
brand=$(python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "优食家族" --json)

# 2. 提取定位、目标受众、核心价值
# 3. 基于品牌基础制定策略
```

## 数据迁移

系统已自动从以下位置迁移数据到新结构：
- `workspace/projects/` → `/Users/a123/.openclaw/projects/`
- `workspace-business/projects/` → `/Users/a123/.openclaw/projects/`

迁移报告：`/Users/a123/.openclaw/projects/_migration_report.json`

## 脚本清单

### 核心脚本

- `scripts/memory/query.py` - 统一查询接口（**最常用**）
- `scripts/memory/client.py` - 客户管理
- `scripts/memory/brand.py` - 品牌管理（带冲突检测）
- `scripts/memory/project.py` - 项目管理（待实现）
- `scripts/memory/task.py` - 任务和版本管理（待实现）

### 工具脚本

- `scripts/memory/migrate.py` - 数据迁移工具
- `scripts/memory/check_skills.py` - Skill 集成检查
- `scripts/memory/test_system.py` - 综合测试
- `scripts/memory/update_all_agents_md.py` - 批量更新 AGENTS.md

### 库文件

- `scripts/memory/lib/schema.py` - 数据结构定义
- `scripts/memory/lib/utils.py` - 工具函数
- `scripts/memory/lib/__init__.py` - 库入口

## 测试

运行综合测试验证系统功能：

```bash
python3 /Users/a123/.openclaw/scripts/memory/test_system.py
```

测试覆盖：
- 客户管理
- 品牌查询
- 品牌资产
- 项目查询
- 冲突检测
- 数据迁移完整性
- 脚本权限

## 常见问题

### Q: 如何查询品牌信息？
```bash
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json
```

### Q: 如何更新品牌调性？
```bash
# 首次尝试（会触发冲突检测）
python3 /Users/a123/.openclaw/scripts/memory/brand.py update \
  --client "客户名" --name "品牌名" --field "brand_tone" --value "新调性"

# 用户确认后
python3 /Users/a123/.openclaw/scripts/memory/brand.py update \
  --client "客户名" --name "品牌名" --field "brand_tone" --value "新调性" \
  --user-confirmed
```

### Q: 旧的项目路径还能用吗？
旧脚本（如 `scripts/init_agency_project.py`）仍可用，路径会自动适配到新结构。但推荐使用新的记忆系统接口。

### Q: 所有 agent 都能访问记忆系统吗？
是的。所有 agent（main、design、strategy、copywriter、research、business、meeting 等）都有权限执行记忆系统脚本。

### Q: 如何查看迁移了哪些数据？
```bash
cat /Users/a123/.openclaw/projects/_migration_report.json
```

## 相关文档

- [Skill 集成指南](SKILL_INTEGRATION_GUIDE.md) - 如何更新 skill 以使用记忆系统
- [CLAUDE.md](../../CLAUDE.md) - OpenClaw 项目总体说明
- [Boss Skill](../../skills/boss/SKILL.md) - 品牌全案工作流

## 更新日志

**2026-06-13**: 
- ✅ 核心架构完成（5层：客户→品牌→项目→任务→版本）
- ✅ 统一查询接口实现
- ✅ 冲突检测机制实现
- ✅ 数据迁移完成（workspace + workspace-business）
- ✅ 所有 workspace AGENTS.md 已更新
- ✅ Boss skill 已更新
- ✅ 14个高优先级 skill 已识别
- ✅ 综合测试通过（8/8）

**待完成**:
- 项目管理脚本（project.py）
- 任务和版本管理脚本（task.py）
- 自动清理脚本（cleanup.py）
- 剩余 skill 的更新
