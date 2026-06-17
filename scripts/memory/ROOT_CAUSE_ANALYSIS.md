# 根因分析报告：为什么小白心里软和 wokenday 没有正确进入记忆系统

生成时间: 2026-06-17

---

## 🔍 问题概述

### 发现的问题

1. **小白心里软**：13 个海报产出 + 1 个 TVC 项目，但没有在记忆系统中立项
2. **wokenday**：20+ 个海报产出，品牌归属错误（未本 → 应该是泓一）

---

## 🎯 根因分析

### 根因 1: 迁移脚本的缺陷（最主要）

**问题**：
- `migrate.py` 只迁移有 `_brand-profile.json` 的品牌
- `workspace/projects/小白/` 目录缺少品牌档案
- 导致整个品牌被跳过，TVC 项目和所有产出都未迁移

**影响范围**：
- 所有没有品牌档案的旧项目都会被跳过
- 迁移报告显示：从 workspace/projects 迁移了 0 个客户

**技术细节**：
```python
# 迁移脚本的逻辑（有缺陷）
for client_dir in workspace_projects.iterdir():
    for brand_dir in client_dir.iterdir():
        brand_profile = brand_dir / "_brand-profile.json"
        if not brand_profile.exists():
            continue  # ❌ 直接跳过！没有记录日志
```

---

### 根因 2: 项目结构不标准

**问题**：
- 旧项目（如 `小白TVC_20260612/`）没有 `project.json`
- 不是通过 `boss` skill 或 `init_agency_project.py` 正式立项
- 缺少标准的元数据和结构

**示例对比**：

**旧结构（有问题）**：
```
workspace/projects/小白/
└── 小白TVC_20260612/          # ❌ 缺少 project.json
    ├── direction-confirmation.md
    ├── problem-alignment-v0.2.md
    └── research-material-request-v0.3.md
```

**新结构（正确）**：
```
projects/泓一/wokenday/项目名/
├── project.json               # ✅ 有元数据
├── brief.json
├── strategy.json
├── materials/
├── outputs/
└── tasks/
```

---

### 根因 3: 产出分散存储

**问题**：
- 大量产出直接保存在 `workspace-design/images/`
- 没有通过 `task.py save-output` 归档
- 产出与项目/任务没有关联

**数据**：
- 小白心里软：13 个图片 + 4 个脚本/提示词
- wokenday：20+ 个海报产出

**缺失的关联**：
```
❌ 当前状态：
   workspace-design/images/xiaobai_fathersday_poster_v2_2.png
   → 没有关联到任何项目、任务或品牌

✅ 应该是：
   projects/客户/小白心里软/父亲节营销/tasks/TASK-xxx/iterations/v2/
   → 有完整的元数据：品牌、项目、任务、版本、prompt、模型
```

---

### 根因 4: Skill 集成不完整（已修复）

**问题**：
- 在 2026-06-17 之前，skill 没有集成记忆系统
- 设计师直接在 `workspace-design` 工作
- 没有触发项目立项和任务创建流程

**时间线**：
- 2026-06-12：小白 TVC 项目创建（旧格式）
- 2026-06-15：wokenday 品牌创建（但归属错误）
- 2026-06-16：大量海报产出（未立项）
- **2026-06-17**：Skill 全量集成完成（今天）

---

## ✅ 已完成的修复

### 修复 1: Skill 全量集成（今天完成）

- ✅ 所有 20 个 skill 已集成记忆系统
- ✅ 每个 skill 现在都会自动立项和归档
- ✅ 所有测试通过

### 修复 2: wokenday 品牌归属

- ✅ 已移动：未本/wokenday → 泓一/wokenday
- ✅ 已更新 client_id
- ✅ 已更新注册表

---

## ⚠️ 待修复的问题

### 问题 1: 小白心里软未立项

**当前状态**：
- ❌ 没有客户档案
- ❌ 没有品牌档案
- ❌ 没有项目
- ❌ 没有任务
- ✅ 有 13 个海报产出（但未关联）
- ✅ 有 1 个 TVC 项目目录（旧格式）

**需要操作**：
1. 确认客户名称（「小白」公司？还是其他？）
2. 创建客户档案
3. 创建品牌档案（品牌调性、定位、受众等）
4. 为每个营销活动创建项目（如父亲节、四宫格等）
5. 为每个海报创建任务
6. 归档所有产出到记忆系统

### 问题 2: wokenday 和小白的产出未归档

**当前状态**：
- wokenday: 20+ 个海报在 workspace-design/images/
- 小白: 13 个海报在 workspace-design/images/
- 都没有关联到项目和任务

**需要操作**：
1. 为每个产出创建对应的任务
2. 使用 `task.py save-output` 归档
3. 记录生成参数、prompt、模型等元数据

---

## 🔧 长期解决方案

### 方案 1: 改进迁移脚本

**目标**：发现并迁移所有项目，即使缺少品牌档案

```python
# 改进后的逻辑
for brand_dir in client_dir.iterdir():
    brand_profile = brand_dir / "_brand-profile.json"
    
    if not brand_profile.exists():
        # ✅ 不要直接跳过，而是：
        # 1. 记录警告日志
        # 2. 尝试从项目目录推断品牌信息
        # 3. 创建基础品牌档案
        # 4. 继续迁移项目
        log_warning(f"品牌缺少档案: {brand_dir}")
        brand_profile = create_minimal_brand_profile(brand_dir)
    
    # 继续迁移...
```

### 方案 2: 自动发现和补救脚本

**目标**：定期扫描 workspace-design，发现未立项的产出

```bash
# 每日运行
python3 scripts/memory/discover_orphan_outputs.py

# 输出示例：
# ⚠️  发现 35 个未关联的产出：
#    - xiaobai_fathersday_poster_v2_2.png
#    - woken_day_poster_final_material_v1.png
#    ...
# 
# 建议操作：
#    1. 为这些产出补充立项
#    2. 归档到记忆系统
```

### 方案 3: 强制 Skill 集成检查

**目标**：确保所有 skill 都正确集成记忆系统

```python
# 在 skill 执行前检查
def before_skill_execution(skill_name):
    if not has_memory_integration(skill_name):
        raise Error(f"Skill {skill_name} 未集成记忆系统")
    
    if not has_project_context():
        raise Error("缺少项目上下文，请先立项")
```

### 方案 4: 健康检查自动化

**目标**：定期检查记忆系统一致性

```bash
# 每周运行
python3 scripts/memory/healthcheck.py

# 检查内容：
# - 注册表与文件系统是否一致
# - 是否有孤儿产出
# - 是否有缺失的品牌档案
# - 品牌归属是否正确
```

---

## 📊 影响评估

### 已发现的受影响数据

| 品牌 | 产出数量 | 状态 | 优先级 |
|------|---------|------|--------|
| 小白心里软 | 13 个海报 + 1 个 TVC | 未立项 | 🔴 高 |
| wokenday | 20+ 个海报 | 品牌归属已修复，产出未归档 | 🟡 中 |

### 可能还存在的问题

**需要排查**：
1. workspace-design/images/ 中是否还有其他未关联的产出？
2. workspace/projects/ 中是否还有其他缺少品牌档案的项目？
3. workspace-business/projects/ 中的项目是否都正确迁移？

---

## 🎯 下一步行动

### 立即行动（高优先级）

1. **确认小白心里软的客户信息**
   - 客户名称
   - 品牌调性、定位、目标受众
   
2. **为小白心里软补充立项**
   - 创建客户和品牌档案
   - 根据海报主题创建项目（父亲节、四宫格等）
   - 为每个海报创建任务并归档

3. **为 wokenday 补充任务**
   - 根据海报主题创建项目
   - 归档所有产出

### 中期行动（本周完成）

4. **改进迁移脚本**
   - 添加对缺失品牌档案的处理
   - 增加详细的日志和报告

5. **创建孤儿产出发现脚本**
   - 扫描 workspace-design/images/
   - 生成未关联产出报告

6. **全面审计**
   - 检查所有旧项目目录
   - 确保没有遗漏的数据

### 长期行动（持续优化）

7. **建立健康检查机制**
   - 定期自动检查
   - 异常告警

8. **完善文档**
   - 更新迁移指南
   - 添加最佳实践

---

## 📝 经验教训

1. **数据迁移要全面**
   - 不要因为缺少某个文件就跳过整个目录
   - 要有详细的日志和报告

2. **建立强制检查点**
   - Skill 执行前必须检查是否已立项
   - 产出保存必须通过统一接口

3. **定期审计很重要**
   - 不要等问题积累
   - 自动化发现和修复

4. **历史数据需要补救**
   - 新系统上线后要处理旧数据
   - 不能只关注新产出

---

**报告生成**: 2026-06-17 17:10:00
**状态**: 部分修复完成，待用户确认小白心里软信息后继续
