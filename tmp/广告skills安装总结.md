# 广告 Agency Skills 安装总结

## 安装完成情况

### ✅ 已安装的 Skills

**全局 skills** (`~/.openclaw/skills/`)：
- `kefu-ae/` - 客服AE（用于 Brief 收集、客户需求整理）
- `boss/` - 总控BOSS（用于协调完整品牌战役流程）

**strategy agent skills** (`workspace-strategy/skills/`)：
- `celue-zj/` - 策略总监（用于定位、品牌策略、受众洞察）
- `chuangyi-zj/` - 创意总监（用于创意方向、Big Idea 判断）

**copywriter agent skills** (`workspace-copywriter/skills/`)：
- `wenan/` - 文案（用于 Campaign 主题、Slogan、KV 文案）

**design agent skills** (`workspace-design/skills/`)：
- `sheji/` - 设计（用于视觉方向、KV 概念、品牌视觉系统）

---

## 配置更新情况

### ✅ openclaw.json 已更新

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "skills": ["kefu-ae", "boss"]
      },
      {
        "id": "strategy",
        "skills": ["celue-zj", "chuangyi-zj", "huashu-design", "session-debug-export"]
      },
      {
        "id": "copywriter",
        "skills": ["wenan", "openclaw-changelog-writer", "session-debug-export"]
      },
      {
        "id": "design",
        "skills": ["sheji", "RunningHub", "brand-poster-creator", ...]
      }
    ]
  }
}
```

### ✅ AGENTS.md 已更新（精简方案）

**更新方式**：在各 workspace 的 `AGENTS.md` 中的 `### 0.1 先查 Skill` 章节末尾添加一行引用：

- **workspace/AGENTS.md** (main)：添加了 `- **广告营销任务**：参考 /Users/a123/.openclaw/广告营销任务路由规则.md`
- **workspace-strategy/AGENTS.md**：添加了 `- **广告策略任务**：参考 /Users/a123/.openclaw/广告营销任务路由规则.md`
- **workspace-copywriter/AGENTS.md**：添加了 `- **广告文案任务**：参考 /Users/a123/.openclaw/广告营销任务路由规则.md`
- **workspace-design/AGENTS.md**：添加了 `- **广告设计任务**：参考 /Users/a123/.openclaw/广告营销任务路由规则.md`

**总行数变化**：
- 更新前：693 行
- 更新后：977 行
- **新增：284 行（主要是独立路由规则文件，AGENTS.md 本身只增加了 1 行引用）**

**臃肿评估**：✅ 不臃肿
- 各 AGENTS.md 只增加了 1 行引用
- 详细的触发规则、工作流说明、冲突处理都放在独立的 `广告营销任务路由规则.md` 中
- 保持了 AGENTS.md 的简洁性

---

## 创建的辅助文件

### `/Users/a123/.openclaw/广告营销任务路由规则.md`

统一记录所有广告 skills 的触发规则，包括：
- main agent 触发规则（品牌全案、Brief收集）
- strategy agent 触发规则（定位、竞品分析、创意方向）
- copywriter agent 触发规则（Campaign主题、Slogan、KV文案）
- design agent 触发规则（视觉方向、KV概念）
- 触发优先级说明
- 工作流示例

---

## 冲突预防措施

### ✅ 已处理的冲突点

1. **竞品分析**：
   - 先触发 `celue-zj` skill（策略总监）规划分析框架
   - 再调用 `multi-search-engine` 搜索竞品资料
   - 最后输出结构化分析报告

2. **文案任务**：
   - `brand-poster-creator` 的海报文案（执行层）不触发 `wenan` skill
   - `wenan` skill 负责战略层文案（Campaign 主题、Slogan）

3. **设计任务**：
   - `sheji` skill 是方法论层（输出视觉方向）
   - 现有 design skills 是执行工具层（直接生图）
   - 工作流：`sheji` 输出视觉方向 → 用户确认 → 调用执行 skills

### ✅ 触发优先级

1. 强制路由规则（AGENTS.md 中明确定义）— 最高优先级
2. 广告 skills（方法论层）— 次之
3. 执行 skills（工具层）— 最后

---

## 使用示例

### 示例 1：品牌全案

用户：我要做一个新款运动鞋的上市 campaign，预算 100 万。

**触发流程**：
1. main agent 识别"上市 campaign" → 触发 `boss` skill
2. boss 协调 `kefu-ae` 收集 Brief
3. kefu-ae 列出资料缺口 → 用户补充
4. boss 派发 strategy agent（触发 `celue-zj` 制定策略）
5. strategy 回传策略 → main 确认
6. boss 派发 copywriter（触发 `wenan` 写文案）+ design（触发 `sheji` 规划视觉方向）
7. 最终由 main 统一交付

### 示例 2：竞品分析

用户：帮我做竞品分析，目标是耐克和阿迪达斯。

**触发流程**：
1. strategy agent 识别"竞品分析" → 触发 `celue-zj` skill
2. celue-zj 规划分析框架（定位、策略、差异化维度）
3. celue-zj 内部调用 `multi-search-engine` 搜索竞品资料
4. celue-zj 基于搜索结果输出结构化分析报告

### 示例 3：品牌海报

用户：做张春节品牌海报。

**触发流程**：
1. main agent 识别"品牌海报" → 强制路由到 `brand-poster-creator`（AGENTS.md 已定义）
2. 不触发 `sheji` skill（因为 brand-poster-creator 已包含完整流程）

---

## 备份文件

已创建备份：
- `/Users/a123/.openclaw/openclaw.json.backup-20260611-161700`

---

## 待验证项

- [ ] 重启 OpenClaw gateway，验证配置是否生效
- [ ] 测试触发 `boss` skill："我要做一个品牌全案"
- [ ] 测试触发 `celue-zj` skill："帮我做竞品分析"
- [ ] 测试触发 `wenan` skill："写个 Campaign 主题"
- [ ] 测试触发 `sheji` skill："给我一个视觉方向"
- [ ] 验证与现有 skills 的协作（如 brand-poster-creator、multi-search-engine）

---

## Git 备份命令

```bash
cd ~/.openclaw
git add skills/kefu-ae skills/boss
git add workspace-strategy/skills/celue-zj workspace-strategy/skills/chuangyi-zj
git add workspace-copywriter/skills/wenan
git add workspace-design/skills/sheji
git add workspace/AGENTS.md workspace-strategy/AGENTS.md workspace-copywriter/AGENTS.md workspace-design/AGENTS.md
git add 广告营销任务路由规则.md
git add openclaw.json
git commit -m "新增：安装广告 Agency Skills 六个岗位

- 安装 6 个广告 skills（客服AE/总控BOSS/策略总监/创意总监/文案/设计）
- 按需分配到各 agent（main/strategy/copywriter/design）
- 更新 openclaw.json 配置
- 补充路由规则（精简方案，独立文件引用）
- 创建广告营销任务路由规则.md 统一记录触发规则

安装位置：
- kefu-ae, boss → skills/（main agent 使用）
- celue-zj, chuangyi-zj → workspace-strategy/skills/
- wenan → workspace-copywriter/skills/
- sheji → workspace-design/skills/

AGENTS.md 只增加 1 行引用，保持简洁性。"
git push
```
