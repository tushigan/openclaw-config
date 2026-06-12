# Boss Skill 上线公告

## 🎉 正式上线

**Boss Skill** 现已正式上线，这是 OpenClaw 首个完整的广告公司协作总控 skill。

**触发词**：品牌全案、整合营销、营销战役、Launch Campaign

## 📋 这是什么

Boss skill 是一个**广告公司岗位协作总控**，用于统筹完整的品牌战役和整合营销流程。

### 核心功能

**1. 7 阶段标准化工作流**

严格按照广告行业标准流程推进：

```
1. AE Brief 收集        → Account Executive 收集客户需求
2. 问题目标三方确认     → AE + 策略 + 创意 共同对齐
3. 资料收集            → AE 列出并收集必要资料
4. 策略制定            → Strategy Director 制定策略
5. 创意方向            → Creative Director 制定创意方向
6. 方向三方确认        → AE + 策略 + 创意 共同确认
7. 内容执行            → Copywriter 产出文案 + Designer 产出视觉
```

每个阶段都有用户确认检查点（User Checkpoint），确认后才进入下一阶段。

**2. 多 Agent 岗位协作**

自动协调 OpenClaw 的多个专家 agent：

| 阶段 | 负责 Agent | 调用 Skill |
|------|-----------|-----------|
| 需求收集、资料收集 | `main` | `kefu-ae` |
| 策略制定 | `strategy` | `celue-zj` |
| 创意方向 | `strategy` | `chuangyi-zj` |
| 文案执行 | `copywriter` | `wenan` |
| 设计执行 | `design` 或 `design-shared` | `sheji` + 执行 skills |

**3. 项目记忆系统**

每个品牌全案项目自动建立记忆档案，实现：
- ✅ 品牌信息跨项目复用
- ✅ 项目进度持久化追踪
- ✅ 历史资料自动归档
- ✅ 品牌资产统一管理

## 🗂️ 项目记忆系统详解

### 是什么

项目记忆系统是 boss skill 的核心基础设施，为每个品牌建立档案，为每个营销战役建立项目。

**目录结构**：

```
workspace/projects/
├── _registry.json              # 全局项目注册表
├── 品牌名/
│   ├── _brand-profile.json     # 品牌档案（长期复用）
│   ├── _brand-assets/          # 品牌资产库
│   │   ├── logos/              # 品牌 logo
│   │   ├── vi-manual/          # VI 手册
│   │   └── reference-images/   # 参考图片
│   └── Campaign名称/           # 具体营销战役
│       ├── project.json        # 项目元信息
│       ├── brief.json          # AE Brief
│       ├── problem-alignment.json  # 问题与目标对齐
│       ├── research-request.json   # 资料收集清单
│       ├── strategy.json       # 策略文档
│       ├── creative-direction.json # 创意方向
│       ├── materials/          # 项目素材
│       │   ├── research/       # 调研资料
│       │   ├── reference/      # 参考资料
│       │   └── client-assets/  # 客户提供的素材
│       └── outputs/            # 产出文件
│           ├── copy/           # 文案产出
│           ├── design/         # 设计产出
│           └── final/          # 最终交付物
```

### 品牌档案内容

**品牌档案** (`_brand-profile.json`) 包含：

```json
{
  "brand_name": "品牌名称",
  "brand_name_en": "Brand Name",
  "industry": "行业",
  "category": "品类",
  "positioning": "品牌定位",
  "brand_tone": "品牌调性",
  "target_audience": "目标受众",
  "core_values": ["价值观1", "价值观2"],
  "brand_story": "品牌故事",
  "brand_personality": "品牌人格",
  "unique_value_proposition": "独特价值主张",
  "pain_points": ["痛点1", "痛点2"],
  "competitors": ["竞品1", "竞品2"],
  "visual_guidelines": {
    "primary_colors": ["#色值"],
    "fonts": ["字体"],
    "logo_usage": "使用规范"
  },
  "brand_assets_path": "飞书云盘路径"
}
```

### 自动增长机制

**新品牌建档**：
- 当执行品牌全案任务时，系统自动检测品牌是否已建档
- 如果是新品牌，从任务输入中提取品牌信息
- 提示用户确认后自动创建品牌档案

**品牌定位冲突检测**：
- 执行任务前自动检测当前输入与档案记录的冲突
- 高严重性冲突（定位、行业、VI、调性）→ 必须暂停任务，让用户决定
- 补充型信息（竞品、历史战役）→ 自动合并，任务结束后通知用户

**示例场景**：

```
用户：做个春节战役，品牌是"XX烘焙"，社区亲民烘焙

系统：⚠️ 品牌定位冲突
档案记录：高端烘焙连锁
当前输入：社区亲民烘焙

如何处理？
1. 使用档案记录（高端烘焙连锁）- 保持品牌策略一致性
2. 更新档案为新信息（社区亲民烘焙）- 品牌定位升级
3. 仅本次使用新信息，不更新档案 - 特殊项目临时定位
```

### 跨 Agent 协作

**策略制定时**：
- `strategy` agent 自动读取品牌档案
- 获取品牌定位、目标受众、核心价值观
- 基于品牌基因制定策略

**设计执行时**：
- `design` agent 自动读取品牌档案
- 获取品牌 VI 规范、logo、品牌色
- 确保视觉输出符合品牌规范

**产出归档时**：
- 文案、设计产出自动归档到项目 `outputs/` 目录
- 客户提供的素材归档到 `materials/` 目录
- 所有产出可追溯、可复用

## 🎯 派发机制优化

在上线的同时，我们对派发机制进行了重大优化，确保工作流的确定性。

### 优化前的问题

- ❌ 只定义了"角色"（Strategy Director），没有明确 agent ID
- ❌ 没有派发模板，依赖 main agent 自己决定如何派发
- ❌ 没有强制要求在派发时指定 skill
- ⚠️ 存在风险：main 可能不派发而是自己执行；专家 agent 可能不调用 skill

### 优化后的机制

**1. 明确的 Agent 映射**

每个阶段精确指定要派发给哪个 agent：

| 阶段 | 派发给 | 调用 Skill |
|------|--------|-----------|
| 策略制定 | **`strategy`** | **`celue-zj`** |
| 创意方向 | **`strategy`** | **`chuangyi-zj`** |
| 文案执行 | **`copywriter`** | **`wenan`** |
| 设计执行 | **`design`** | **`sheji`** + 执行 skills |

**2. 标准派发模板**

提供了完整的派发模板，确保每次派发都包含：
- 明确的 agent ID
- 强制的 skill 指定："**必须使用 XXX skill**"
- 完整的前置信息（品牌档案、已确认产出、具体需求）
- 明确的输出要求

**3. 派发验证检查点**

每次派发前必须验证：
- ✅ 派发对象是否正确
- ✅ Skill 是否明确指定
- ✅ 前置条件是否满足
- ✅ 上下文是否完整传递
- ✅ 模板是否正确使用

**4. 强制约束**

- ❌ 禁止跳过派发（策略、创意、文案、设计必须派发）
- ❌ 禁止省略 skill 指定
- ❌ 禁止模糊派发
- ❌ 禁止私自兜底

## 💡 怎么用

### 基本使用

**触发 Boss Skill**：

```
用户：我要做一个春节营销战役，品牌是"XX 烘焙"
```

系统会自动：
1. 检测到"营销战役"关键词，触发 boss skill
2. 检查品牌档案是否存在
3. 启动 AE Brief 收集流程

### 完整流程示例

**阶段 1：AE Brief 收集**

```
系统（AE 角色）：
我来帮您收集 brief 信息。

已知信息：
- 品牌：XX 烘焙
- 项目类型：春节营销战役

待确认信息：
1. 项目目标是什么？（品牌曝光 / 销售转化 / 新品推广）
2. 目标受众是谁？
3. 预算范围？
4. 传播渠道？（线上 / 线下 / 全渠道）
5. 时间节点？
```

**阶段 2：问题目标三方确认**

```
系统（AE 起草）：
基于 brief，我起草了问题和目标：

要解决的问题：
- 春节期间如何突破竞品包围，提升品牌声量

项目目标：
- 品牌曝光量提升 30%
- 春节期间销售额增长 20%

现在需要策略总监和创意总监确认...

（系统内部协调 strategy 和 main 的创意视角进行确认）
```

**阶段 3：资料收集**

```
系统（AE 角色）：
根据已确认的问题和目标，需要收集以下资料：

必需资料：
✅ 品牌档案（已有）
❌ 春节期间烘焙行业竞品投放分析
❌ 目标受众春节消费行为洞察
❌ 历史春节战役效果数据

请提供缺失的资料，或我可以帮您调研...
```

**阶段 4：策略制定**

```
系统（派发给 strategy agent）：
正在派发策略制定任务给策略总监...

（内部派发）
{
  "agentId": "strategy",
  "task": "【策略制定任务】\n\n**必须使用 celue-zj skill**\n\n..."
}

（strategy agent 返回策略文档）

系统：
策略总监已完成策略制定，核心主张：「XX」
策略文档：/workspace-strategy/outputs/strategy_20260612.md

请确认策略方向...
```

**阶段 5-7：创意、文案、设计**

依次派发给对应的专家 agent，每个阶段都有用户确认检查点。

### 品牌档案查询

**手动查询品牌档案**：

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/find_brand_profile.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名"
```

**新建品牌档案**：

```bash
python3 /Users/a123/.openclaw/skills/boss/scripts/init_agency_project.py \
  --workspace-root /Users/a123/.openclaw/workspace \
  --brand-name "品牌名" \
  --campaign-name "春节战役_20260612" \
  --industry "烘焙" \
  --target-audience "25-35岁都市白领" \
  --core-values "新鲜手作,用心品质"
```

### 单点任务使用

如果只需要某个单点产出（如只要策略，不需要执行）：

```
用户：基于 XX 品牌，帮我做个产品上市策略

系统：
检测到品牌档案，读取品牌信息...
这是单点策略任务，我会跳过 brief 收集，直接进入策略制定。

但需要确认：
1. 产品信息：[...]
2. 上市目标：[...]
...
```

### 跨项目复用

**场景：同一品牌的多个战役**

```
第一次：春节战役
- 系统创建品牌档案
- 收集品牌定位、VI、目标受众等信息

第二次：618 战役（同一品牌）
- 系统自动读取品牌档案
- 无需重复收集品牌信息
- 直接进入战役策划

第三次：中秋战役（同一品牌）
- 系统继续复用品牌档案
- 历史战役的经验和资料都在项目目录中
```

## 📚 相关文档

- **SKILL.md** - Boss skill 完整定义和工作流
- **OPTIMIZATION.md** - 派发机制优化详解
- **references/workflow.md** - 完整品牌全案工作流参考

## 🔧 常用脚本

**品牌档案管理**：
```bash
# 查找品牌档案
python3 skills/boss/scripts/find_brand_profile.py --brand-name "品牌名"

# 查找活跃项目
python3 skills/boss/scripts/find_active_project.py --brand-name "品牌名"

# 更新品牌档案
python3 skills/boss/scripts/update_brand_profile.py \
  --brand-name "品牌名" \
  --field "positioning" \
  --value "新定位"

# 检测品牌定位冲突
python3 skills/boss/scripts/detect_brand_conflicts.py \
  --brand-name "品牌名" \
  --new-info '{"positioning":"新定位"}'
```

**项目管理**：
```bash
# 初始化新项目
python3 skills/boss/scripts/init_agency_project.py \
  --brand-name "品牌名" \
  --campaign-name "战役名"

# 归档项目材料
python3 skills/boss/scripts/archive_material.py \
  --project-dir "项目路径" \
  --source-path "文件路径" \
  --material-type "research"

# 更新项目阶段状态
python3 skills/boss/scripts/update_stage.py \
  --project-dir "项目路径" \
  --stage "strategy" \
  --status "completed"
```

## 🎓 最佳实践

### 1. 品牌建档优先
- 长期合作的品牌，第一次执行时就建立品牌档案
- 品牌信息越完整，后续项目执行越高效

### 2. 阶段门严格执行
- 每个阶段必须获得用户确认后才进入下一阶段
- 发现资料缺口时，先补齐再继续

### 3. 产出及时归档
- 文案、设计产出及时归档到项目 `outputs/` 目录
- 客户提供的素材归档到 `materials/` 目录

### 4. 品牌定位冲突处理
- 遇到品牌定位冲突时，优先使用档案记录
- 确需更新定位时，记录变更原因

### 5. 多 Agent 协作
- 策略、创意、文案、设计阶段必须派发给专家 agent
- main agent 负责协调和统一交付，不替代专家执行

## 🐛 已知限制

1. **项目记忆系统目前仅支持本地存储**
   - 品牌档案和项目数据存储在 `workspace/projects/`
   - 不支持跨设备同步（未来可通过飞书云盘或 Git 解决）

2. **品牌档案更新需要手动确认**
   - 品牌定位等高严重性字段冲突时，必须用户手动确认
   - 自动合并功能仅限补充型信息

3. **派发失败时需要手动重试**
   - 如果专家 agent 不可用，系统会报告但不会自动重试
   - 需要用户确认后手动重试或使用 shared variant

## 📅 版本信息

- **版本**：v1.0
- **上线日期**：2026-06-12
- **最新优化**：派发机制优化（2026-06-12）
- **Git 提交**：b3a80a9b

## 🙋 反馈与支持

如果在使用过程中遇到问题或有改进建议，请：
1. 查看 `SKILL.md` 了解完整工作流
2. 查看 `OPTIMIZATION.md` 了解派发机制
3. 向 main agent 反馈具体问题

---

**开始使用**：直接对 main agent 说"我要做一个 [品牌全案/整合营销/营销战役]"即可触发 boss skill。
