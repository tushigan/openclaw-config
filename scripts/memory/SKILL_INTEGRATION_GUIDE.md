# OpenClaw Skill 记忆系统集成指南

生成时间: Sat Jun 13 16:14:54 CST 2026

---

## 🔴 高优先级 Skill（必须集成）


## boss - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, brand, 项目, project, 客户; 使用旧项目路径: workspace/projects

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```


### ⚠️ 路径迁移（必须）:
检测到旧路径: workspace/projects

**迁移步骤**:
1. 全局替换路径引用
2. 更新脚本中的目录结构假设
3. 测试所有文件读写操作

---


## kefu-ae - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, 项目, project, 客户

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## business-project-intake - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 项目, project, 客户, workspace-business/projects, project.json; 使用旧项目路径: workspace-business/projects

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```


### ⚠️ 路径迁移（必须）:
检测到旧路径: workspace-business/projects

**迁移步骤**:
1. 全局替换路径引用
2. 更新脚本中的目录结构假设
3. 测试所有文件读写操作

---


## quote-skill - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, 项目, project, 客户, client; 使用旧项目路径: workspace-business/projects

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```


### ⚠️ 路径迁移（必须）:
检测到旧路径: workspace-business/projects

**迁移步骤**:
1. 全局替换路径引用
2. 更新脚本中的目录结构假设
3. 测试所有文件读写操作

---


## wenan - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, brand

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## brand-poster-creator - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, brand, 项目, project, 档案; 使用旧项目路径: workspace/projects

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```


### ⚠️ 路径迁移（必须）:
检测到旧路径: workspace/projects

**迁移步骤**:
1. 全局替换路径引用
2. 更新脚本中的目录结构假设
3. 测试所有文件读写操作

---


## brand-poster-distiller - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, brand

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## dreamina-reference-video - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 客户

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## gpt-image2-gen - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: brand

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## product-photography-workflow - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 项目, project, profile

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## sheji - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, 记忆

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## xiangqingye-desigen - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, brand, 项目, project, profile

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## celue-zj - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, 客户

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---


## chuangyi-zj - 记忆系统集成指南

**集成级别**: HIGH
**原因**: 包含记忆相关关键词: 品牌, 项目, 客户, client, 记忆

### 推荐集成方式:

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
   python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
     --task-id "TASK-xxx" \
     --file "/path/to/output.png" \
     --expire-days 30
   ```

---

## 🟡 中优先级 Skill（建议集成）

## 🟢 低优先级 Skill（可选集成）

