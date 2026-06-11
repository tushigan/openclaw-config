# Boss Skill 项目记忆系统 - 全局集成方案 v2

## 执行日期
2026-06-11

## 变更概述
将项目记忆系统集成到**所有涉及品牌/项目工作的 agent**，确保项目记忆在整个协作链路中全局可用。

---

## 一、涉及的 Agent 范围

### 1.1 核心集成 Agent（必须集成）

| Agent | 工作域 | 集成原因 | 集成优先级 |
|-------|--------|----------|-----------|
| **main** | 主协调 | 项目入口，负责派发任务时传递品牌上下文 | P0 |
| **strategy** | 品牌策略 | 品牌定位、叙事依赖品牌档案 | P0 |
| **design** | 视觉创作 | 海报、包装等视觉内容需要品牌素材和调性 | P0 |
| **copywriter** | 文案创作 | 文案需要品牌调性、价值观、故事 | P0 |
| **research** | 市场调研 | 调研需要了解品牌背景和项目目标 | P1 |
| **business** | 项目承接 | 项目立项阶段创建品牌档案和项目记忆 | P1 |

### 1.2 不需要集成的 Agent

| Agent | 工作域 | 不集成原因 |
|-------|--------|-----------|
| **meeting-analyst** | 会议分析 | 纯会议记录处理，不涉及品牌项目工作 |

---

## 二、权限验证结果（已完成）

### 2.1 目录权限
- ✅ `/Users/a123/.openclaw/workspace/projects/` 存在，drwx------ (a123:staff)
- ✅ 所有 agent（包括 shared 版本）都以 Unix 用户 `a123` 运行
- ✅ 所有 agent 对该目录都有完整读写权限

### 2.2 命令执行权限（exec-approvals.json）
- ✅ main / main-shared: python3, bash, cp, mkdir 已批准
- ✅ design / design-shared: python3, bash, cp, mkdir 已批准
- ✅ strategy / strategy-shared: python3, bash 已批准
- ✅ research / research-shared: python3, bash 已批准
- ✅ copywriter / copywriter-shared: python3, bash 已批准

### 2.3 虾权机制说明
- **虾权 (Xia Quan)** = Feishu 聊天权限隔离，不是文件系统权限
- **训虾权** = admin users (credentials/feishu-admin-users.json)
- **用虾权** = regular users
- Shared agent 的虾权隔离只影响 Feishu 消息路由，不影响文件系统访问

---

## 三、CLI 脚本现状（已完成）

已实现 5 个 CLI 脚本，测试通过：

| 脚本 | 功能 | 测试状态 |
|------|------|----------|
| `find_brand_profile.py` | 查询品牌档案 | ✅ 通过（返回 found:false 不抛错）|
| `list_active_projects.py` | 列出活跃项目 | ✅ 通过 |
| `get_project_status.py` | 获取项目状态 | ✅ 通过 |
| `update_project_stage.py` | 更新项目阶段 | ✅ 通过 |
| `archive_project.py` | 归档项目 | ✅ 通过 |

---

## 四、集成内容设计

### 4.1 AGENTS.md 集成内容（标准模板）

每个 agent 的 AGENTS.md 都添加以下章节：

```markdown
## X. 项目记忆系统集成

### X.1 品牌档案查询

在执行品牌相关任务前，先查询是否存在品牌档案：

```bash
python3 /Users/a123/.openclaw/workspace/projects/scripts/find_brand_profile.py "品牌名称"
```

返回格式：
```json
{
  "found": true,
  "profile_path": "/Users/a123/.openclaw/workspace/projects/品牌名称/_brand-profile.json",
  "profile": {
    "brand_name": "品牌名称",
    "industry": "行业",
    "core_values": ["价值观1", "价值观2"],
    "target_audience": "目标受众",
    "brand_story": "品牌故事",
    "visual_guidelines": {
      "primary_colors": ["#色值"],
      "fonts": ["字体"],
      "logo_usage": "使用规范"
    }
  }
}
```

若 `found: false`，说明品牌尚未建档，继续执行时按无档案状态处理。

### X.2 活跃项目查询

查询当前活跃的项目（未归档）：

```bash
python3 /Users/a123/.openclaw/workspace/projects/scripts/list_active_projects.py
```

### X.3 项目状态查询

查询特定项目的执行状态和检查点：

```bash
python3 /Users/a123/.openclaw/workspace/projects/scripts/get_project_status.py "品牌名称/项目目录名"
```

### X.4 跨 Agent 协作规则

- **main 派发任务时**：如果查到品牌档案，在派发给 strategy/design/copywriter 时，通过任务描述传递品牌档案路径或关键信息
- **strategy/design/copywriter 接收任务时**：优先查询品牌档案，再开始执行
- **design 生成视觉内容时**：从品牌档案中读取 visual_guidelines、logo_path、brand_assets_path
- **copywriter 创作文案时**：从品牌档案中读取 core_values、brand_story、tone_of_voice

### X.5 品牌素材归档

完成品牌相关任务后，将关键产出归档到品牌项目目录：

```bash
# 示例：归档海报到项目目录
cp /Users/a123/.openclaw/workspace-design/images/海报.png \
   /Users/a123/.openclaw/workspace/projects/品牌名称/项目目录/outputs/海报_v1.png
```
```

### 4.2 各 Agent 特定集成点

#### 4.2.1 main agent
- **集成位置**：`## 1. 路由规则` 章节后添加 `## 1.5 项目记忆集成`
- **集成内容**：
  - 接收品牌任务时先查询品牌档案
  - 派发给 strategy/design/copywriter 时传递品牌上下文
  - 统一交付时归档关键产出

#### 4.2.2 strategy agent
- **集成位置**：`## 0. 总原则` 章节后添加 `## 0.5 项目记忆集成`
- **集成内容**：
  - 品牌策略任务开始前查询品牌档案
  - 从档案中读取行业、定位、核心价值观
  - 策略产出归档到项目目录

#### 4.2.3 design agent
- **集成位置**：`## 1. 输出要求` 章节后添加 `## 1.3 项目记忆集成`
- **集成内容**：
  - 视觉任务开始前查询品牌档案
  - 从档案中读取 visual_guidelines、logo_path、brand_assets_path
  - 视觉产出归档到项目目录
  - **brand-poster-creator skill 集成**（见下文）

#### 4.2.4 copywriter agent
- **集成位置**：`## 1. 输出要求` 章节后添加 `## 1.3 项目记忆集成`
- **集成内容**：
  - 文案任务开始前查询品牌档案
  - 从档案中读取 core_values、brand_story、tone_of_voice
  - 文案产出归档到项目目录

#### 4.2.5 research agent
- **集成位置**：`## 1. 输出要求` 章节后添加 `## 1.3 项目记忆集成`
- **集成内容**：
  - 品牌调研任务开始前查询品牌档案和项目目标
  - 调研产出归档到项目目录

---

## 五、Brand-Poster-Creator Skill 集成

### 5.1 集成位置
`/Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/SKILL.md`

### 5.2 集成方式
在 **Step 2.5 品牌素材获取** 之前插入 **Step 2.4 品牌档案查询**：

```markdown
### Step 2.4 品牌档案查询（新增）

**目标**：查询品牌是否已建档，获取品牌基础信息

**执行**：
```bash
python3 /Users/a123/.openclaw/workspace/projects/scripts/find_brand_profile.py "${BRAND_NAME}"
```

**输出**：
- 若 `found: true`：
  - 读取 `profile.visual_guidelines`（色彩、字体、logo 规范）
  - 读取 `profile.brand_assets_path`（飞书云盘素材路径）
  - 读取 `profile.core_values`（品牌核心价值观，用于文案创意）
- 若 `found: false`：
  - 记录"品牌未建档"状态
  - 继续执行后续流程（Step 2.5 从飞书云盘搜索素材）

**降级策略**：
- 品牌未建档时，不影响后续流程
- Step 2.5 仍然执行飞书云盘素材搜索
- 若 Step 2.5 也未找到，走 manager.skip_stage() 流程
```

### 5.3 修改点
1. `SKILL.md` 文档更新（添加 Step 2.4）
2. 不修改现有脚本代码（保持向后兼容）
3. 未来优化：修改 `scripts/fetch_brand_assets.py` 支持从品牌档案读取 `brand_assets_path`

---

## 六、执行计划

### 阶段 1：文档集成（非侵入式，零风险）

| 序号 | 操作 | 文件 | 风险 |
|------|------|------|------|
| 1 | 更新 main AGENTS.md | `/Users/a123/.openclaw/workspace/AGENTS.md` | 低 |
| 2 | 更新 strategy AGENTS.md | `/Users/a123/.openclaw/workspace-strategy/AGENTS.md` | 低 |
| 3 | 更新 design AGENTS.md | `/Users/a123/.openclaw/workspace-design/AGENTS.md` | 低 |
| 4 | 更新 copywriter AGENTS.md | `/Users/a123/.openclaw/workspace-copywriter/AGENTS.md` | 低 |
| 5 | 更新 research AGENTS.md | `/Users/a123/.openclaw/workspace-research/AGENTS.md` | 低 |
| 6 | 更新 projects/.gitkeep | `/Users/a123/.openclaw/workspace/projects/.gitkeep` | 低 |

### 阶段 2：Skill 集成（可选）

| 序号 | 操作 | 文件 | 风险 |
|------|------|------|------|
| 1 | 更新 brand-poster-creator SKILL.md | `/Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/SKILL.md` | 中 |
| 2 | 测试 brand-poster-creator 新流程 | - | 中 |

### 阶段 3：Git 备份

| 序号 | 操作 | 命令 | 备注 |
|------|------|------|------|
| 1 | 提交更改 | `git add -A && git commit -m "集成：Boss skill 项目记忆系统全局部署"` | - |
| 2 | 推送到远端 | `git push` | - |

---

## 七、回滚方案

如果集成后发现问题，回滚步骤：

```bash
cd /Users/a123/.openclaw
git log --oneline -5  # 查看最近提交
git revert <commit_hash>  # 回滚到指定提交
git push
```

或手动恢复：从 git 历史中读取旧版 AGENTS.md，覆盖回去。

---

## 八、验证清单

- [ ] 所有 agent 的 AGENTS.md 都添加了项目记忆集成章节
- [ ] main agent 派发任务时能正确传递品牌上下文
- [ ] design agent 能从品牌档案读取视觉规范
- [ ] copywriter agent 能从品牌档案读取品牌调性
- [ ] brand-poster-creator skill 能优先查询品牌档案
- [ ] 所有更改已提交到 git

---

## 九、后续优化建议

1. **自动归档**：在 skill 执行完成后，自动归档产出到项目目录
2. **品牌档案模板**：创建标准品牌档案模板，降低建档成本
3. **项目仪表盘**：开发 Web 界面展示所有活跃项目状态
4. **跨平台同步**：将项目记忆同步到 Memos 或飞书云文档

---

**方案制定人**：Claude (Kiro)  
**审核状态**：待用户确认  
**执行状态**：待执行
