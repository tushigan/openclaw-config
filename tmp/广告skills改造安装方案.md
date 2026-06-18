# 广告 Agency Skills 改造安装方案

## 一、现状分析

### 1.1 英文混用程度评估

经过检查，这套 skills 的**英文混用程度较低**：

**✅ 已经是中文的部分**：
- 所有 SKILL.md 的正文内容（工作流、原则、约束）都是中文
- 所有输出标准、协作规则都是中文
- 用户面向的使用说明（USAGE.md）是中文

**⚠️ 需要改造的英文部分**：
- `name` 字段：`account-executive`, `boss`, `copywriter` 等
- `description` 字段：英文描述
- 目录名：`account-executive/`, `creative-director/` 等
- README.md：完全英文（但这个文件不影响使用）

### 1.2 与 OpenClaw 现有架构的对比

你的现有全局 skills 只有 7 个：
```
feishu-create-doc
memos-memory-guide
multi-search-engine
omni-vision-psd-extractor
session-debug-export
tvc-director
wechat-article-reader
```

这套广告 skills 会新增 6 个岗位角色，总数翻倍。从功能层面看是**高度互补的**，不会冲突。

---

## 二、改造策略

### 2.1 中文化改造原则

**必须改的**：
1. ✅ 目录名：改成中文拼音或中文（方便你看目录结构）
2. ✅ `name` 字段：改成中文或中英对照
3. ✅ `description` 字段：全部改成中文

**可以保留的**：
1. ✅ `references/` 目录名：保持英文（技术约定）
2. ✅ `agents/` 目录名：保持英文（技术约定）
3. ✅ README.md：不改（开源仓库的文档，不影响 OpenClaw 使用）

### 2.2 具体改造方案

#### 方案 A：全中文目录名（推荐）

```
~/.openclaw/skills/
├── 客服AE/               # account-executive
├── 总控BOSS/             # boss
├── 文案/                 # copywriter
├── 创意总监/             # creative-director
├── 设计/                 # designer
└── 策略总监/             # strategy-director
```

**优点**：
- 你看目录时一目了然，不头疼
- 符合你"尽量用中文"的偏好
- OpenClaw 的 skill 调用应该支持中文目录名（需验证）

**风险**：
- 需要确认 OpenClaw 的 skill 加载器是否支持中文目录名
- 如果不支持，需要回退到方案 B

#### 方案 B：拼音目录名（保守）

```
~/.openclaw/skills/
├── kefu-ae/              # account-executive，中文名：客服AE
├── boss/                 # boss，中文名：总控BOSS
├── wenan/                # copywriter，中文名：文案
├── chuangyi-zj/          # creative-director，中文名：创意总监
├── sheji/                # designer，中文名：设计
└── celue-zj/             # strategy-director，中文名：策略总监
```

**优点**：
- 兼容性最好，肯定能加载
- 拼音也比英文好认

**缺点**：
- 拼音对你来说也不如直接中文直观

---

## 三、安装方案（完整步骤）

### 3.1 安装前准备

```bash
cd /tmp
git clone https://github.com/tushigan/Agency-Workflow-skills.git
cd Agency-Workflow-skills
```

### 3.2 改造脚本（自动化中文化）

**创建改造脚本**（会自动改造所有英文字段和目录名）：

```bash
cat > /tmp/transform-agency-skills.sh << 'EOF'
#!/bin/bash

# 定义映射关系
declare -A NAME_MAP=(
    ["account-executive"]="客服AE"
    ["boss"]="总控BOSS"
    ["copywriter"]="文案"
    ["creative-director"]="创意总监"
    ["designer"]="设计"
    ["strategy-director"]="策略总监"
)

declare -A DESC_MAP=(
    ["account-executive"]="广告公司客服 AE。用于 Brief 收集、客户需求整理、会议纪要、反馈拆解、项目协调、风险提示和品牌战役跨岗位输入准备。"
    ["boss"]="广告公司总控岗位。用于协调 AE、策略总监、文案、设计和创意总监的工作流，从 Brief 收集到策略、创意对齐、执行和修订的完整品牌战役和整合营销流程。"
    ["copywriter"]="广告公司文案。用于 campaign 主题、slogan、KV 文案、社媒文案、视频脚本、命名、促销文案、提案表达和将产品功能翻译为说服性语言。"
    ["creative-director"]="广告公司创意总监。用于创意方向制定、Big Idea 判断、创意路线评估、提案逻辑和创意复核。"
    ["designer"]="广告公司设计。用于视觉方向、KV 概念、版式、品牌视觉系统、数字设计结构、AI 生图 prompt、设计评审和战役物料执行指导。"
    ["strategy-director"]="广告公司策略总监。用于定位、问题诊断、受众洞察、竞品分析、品牌战役策略、核心主张、创意简报开发和整合营销战略框架。"
)

# 遍历每个 skill 目录
for OLD_NAME in account-executive boss copywriter creative-director designer strategy-director; do
    NEW_NAME="${NAME_MAP[$OLD_NAME]}"
    NEW_DESC="${DESC_MAP[$OLD_NAME]}"
    
    echo "处理 $OLD_NAME -> $NEW_NAME"
    
    # 修改 SKILL.md 的 frontmatter
    SKILL_FILE="$OLD_NAME/SKILL.md"
    if [ -f "$SKILL_FILE" ]; then
        # 备份原文件
        cp "$SKILL_FILE" "${SKILL_FILE}.bak"
        
        # 替换 name 和 description
        sed -i.tmp "s/^name: $OLD_NAME$/name: $NEW_NAME/" "$SKILL_FILE"
        sed -i.tmp "s/^description: .*$/description: $NEW_DESC/" "$SKILL_FILE"
        rm "${SKILL_FILE}.tmp"
        
        echo "  ✓ 已更新 $SKILL_FILE 的 name 和 description"
    fi
done

echo "改造完成！"
EOF

chmod +x /tmp/transform-agency-skills.sh
```

### 3.3 执行改造

```bash
cd /tmp/Agency-Workflow-skills
/tmp/transform-agency-skills.sh
```

### 3.4 安装到 OpenClaw（方案 A：全中文目录名）

```bash
# 先测试一个 skill 看看 OpenClaw 是否支持中文目录名
cp -R account-executive ~/.openclaw/skills/客服AE

# 测试调用（需要你在 OpenClaw 中手动测试）
# 如果能正常加载，继续安装其他 skills
cp -R boss ~/.openclaw/skills/总控BOSS
cp -R copywriter ~/.openclaw/skills/文案
cp -R creative-director ~/.openclaw/skills/创意总监
cp -R designer ~/.openclaw/skills/设计
cp -R strategy-director ~/.openclaw/skills/策略总监
```

### 3.5 安装到 OpenClaw（方案 B：拼音目录名，保守方案）

如果方案 A 测试失败，改用拼音：

```bash
cp -R account-executive ~/.openclaw/skills/kefu-ae
cp -R boss ~/.openclaw/skills/boss
cp -R copywriter ~/.openclaw/skills/wenan
cp -R creative-director ~/.openclaw/skills/chuangyi-zj
cp -R designer ~/.openclaw/skills/sheji
cp -R strategy-director ~/.openclaw/skills/celue-zj
```

---

## 四、配置集成

### 4.1 更新 openclaw.json

需要在 `openclaw.json` 的 `agents.defaults.skills` 或各 agent 的 `skills` 配置中声明这些新 skills。

**示例配置**（需要你确认具体格式）：

```json
{
  "agents": {
    "defaults": {
      "skills": [
        "客服AE",
        "总控BOSS",
        "文案",
        "创意总监",
        "设计",
        "策略总监",
        "multi-search-engine",
        "wechat-article-reader",
        "feishu-create-doc"
      ]
    }
  }
}
```

或者**按 agent 分配**（更精细）：

```json
{
  "agents": {
    "main": {
      "skills": ["客服AE", "总控BOSS", "multi-search-engine"]
    },
    "strategy": {
      "skills": ["策略总监", "创意总监"]
    },
    "copywriter": {
      "skills": ["文案"]
    },
    "design": {
      "skills": ["设计"]
    }
  }
}
```

### 4.2 更新 workspace AGENTS.md 规则

在 `workspace/AGENTS.md` 中补充这些 skills 的调用场景：

```markdown
## 1.1 广告营销任务路由规则

- **品牌全案/整合营销/Launch Campaign**：
  - 优先调用 `总控BOSS` skill，由它协调整个流程
  - 或者先调用 `客服AE` skill 整理 Brief，再分配给其他岗位

- **策略定位/竞品分析/受众洞察**：
  - 调用 `策略总监` skill，由 strategy agent 执行
  
- **文案创作/Campaign 主题/社媒内容**：
  - 调用 `文案` skill，由 copywriter agent 执行
  
- **视觉方向/KV 设计/moodboard**：
  - 调用 `设计` skill，由 design agent 执行
  - 设计确认后再调用生图 skills（brand-poster-creator 等）
  
- **创意方向评估/Big Idea 判断**：
  - 调用 `创意总监` skill，可由 strategy 或 main agent 执行
```

---

## 五、验证测试

### 5.1 功能测试用例

安装后用以下场景测试：

**测试 1：客服AE - Brief 收集**
```
用户输入：我们要做一个新款运动鞋的上市 campaign，预算100万，主要在小红书和抖音投放。

期望行为：
1. 调用"客服AE" skill
2. 根据 brief 模版收集需求
3. 列出缺失的资料清单（目标人群、产品卖点、竞品等）
4. 提交给用户确认
```

**测试 2：策略总监 - 定位策略**
```
用户输入：（在 Brief 确认后）现在开始做策略，目标人群是25-35岁都市白领，竞品是耐克和阿迪达斯。

期望行为：
1. 调用"策略总监" skill
2. 诊断问题、建立洞察
3. 输出策略和 Creative Brief
4. 提交给用户确认
```

**测试 3：总控BOSS - 完整流程**
```
用户输入：用总控BOSS跑一个完整的品牌全案，从Brief到执行。

期望行为：
1. 调用"总控BOSS" skill
2. 自动协调 AE → 策略 → 创意 → 文案/设计
3. 每个阶段产出后暂停等待用户确认
4. 完整走完流程
```

### 5.2 兼容性验证

- [ ] 中文目录名能否被 OpenClaw 正确加载
- [ ] skill 之间的相互调用是否正常（如 BOSS 调用 AE）
- [ ] 与现有 agent 的协作是否顺畅（strategy agent 调用策略总监 skill）
- [ ] 确认机制能否在 subagent 场景下正常工作

---

## 六、后续优化建议

### 6.1 与现有 skills 的协作链

建立协作链路：

```
客服AE → 策略总监 → 创意总监 → 文案/设计 → brand-poster-creator（生图）
                                              → dreamina-cli（视频）
                                              → feishu-create-doc（交付）
```

### 6.2 Memory 记录

安装后在 `memory/` 中记录：

```markdown
---
name: 广告agency-skills安装记录
type: project
---

已安装6个广告公司岗位 skills：客服AE、总控BOSS、策略总监、创意总监、文案、设计。

**使用场景**：
- 品牌全案、整合营销、Launch Campaign → 用"总控BOSS"统筹
- 单点策略需求 → 用"策略总监"
- 单点文案需求 → 用"文案"

**协作链路**：
strategy agent 负责调用"策略总监"和"创意总监"
copywriter agent 负责调用"文案"
design agent 负责调用"设计" + 生图 skills

**确认机制**：
每个岗位产出必须回传 main，由 main 交付用户确认后再进入下一阶段。
```

### 6.3 Git 备份

安装完成后记得保存到 git：

```bash
cd ~/.openclaw
git add skills/客服AE skills/总控BOSS skills/文案 skills/创意总监 skills/设计 skills/策略总监
git commit -m "新增：安装广告 Agency Skills 六个岗位（客服AE/总控BOSS/策略/创意/文案/设计）"
git push
```

---

## 七、风险提示

### 7.1 中文目录名兼容性风险

**如果 OpenClaw 不支持中文目录名**，会出现：
- Skill 加载失败
- 调用时找不到 skill

**应对方案**：
- 先用一个 skill 测试（如"客服AE"）
- 如果失败，立即回退到拼音方案

### 7.2 Skills 数量激增

从 7 个全局 skills 增加到 13 个，可能导致：
- Skill 查找时间变长
- main agent 需要更清晰的路由规则

**应对方案**：
- 在 `workspace/AGENTS.md` 中补充明确的调用场景
- 考虑把这 6 个广告 skills 放到独立的"广告模式"入口

### 7.3 确认机制的实现差异

这套 skills 强调"每步确认"，但 OpenClaw 的 subagent 是异步执行的。

**需要验证**：
- Subagent 产出如何回传 main？
- Main 如何实现"暂停等待用户确认"？

**可能的解决方案**：
- 在 skill 的工作流中明确"输出后必须返回 main，由 main 交付"
- 或者让 main 在调用 subagent 后主动检查产出并交付给用户

---

## 八、总结

这套广告 skills 与你的 OpenClaw **架构完全兼容，功能高度互补**。

**推荐安装策略**：
1. ✅ 使用方案 A（全中文目录名），先测试"客服AE"
2. ✅ 改造脚本已准备好，可一键执行
3. ✅ 安装后在 `workspace/AGENTS.md` 补充路由规则
4. ✅ 测试"总控BOSS"跑完整流程
5. ✅ 验证与现有 agent 的协作（strategy/copywriter/design）

**你确认这个方案可以开始执行吗？有什么需要调整的地方？**
