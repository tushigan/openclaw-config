# 广告 Skills 安装诊断报告

生成时间：2026-06-11 17:58

## ✅ 已完成的配置

### 1. Skills 文件安装 (6个)
所有 skill 已安装到正确位置，包含必要文件：

| Skill | 位置 | SKILL.md | skill.js |
|-------|------|----------|----------|
| 客服AE (kefu-ae) | `/Users/a123/.openclaw/skills/kefu-ae/` | ✅ | ✅ |
| 总控BOSS (boss) | `/Users/a123/.openclaw/skills/boss/` | ✅ | ✅ |
| 策略总监 (celue-zj) | `/Users/a123/.openclaw/workspace-strategy/skills/celue-zj/` | ✅ | ✅ |
| 创意总监 (chuangyi-zj) | `/Users/a123/.openclaw/workspace-strategy/skills/chuangyi-zj/` | ✅ | ✅ |
| 文案 (wenan) | `/Users/a123/.openclaw/workspace-copywriter/skills/wenan/` | ✅ | ✅ |
| 设计 (sheji) | `/Users/a123/.openclaw/workspace-design/skills/sheji/` | ✅ | ✅ |

### 2. openclaw.json 配置 ✅
所有 agent 的 skills 字段都已正确配置：

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

### 3. Skills 加载路径配置 ✅
`openclaw.json` 中的 `skills.load.extraDirs` 包含所有必要路径：

```json
{
  "skills": {
    "load": {
      "extraDirs": [
        "/Users/a123/.openclaw/workspace/skills",
        "/Users/a123/.openclaw/workspace/.agents/skills",
        "/Users/a123/.openclaw/skills",
        "/Users/a123/.openclaw/workspace-strategy/skills",
        "/Users/a123/.openclaw/workspace-design/skills",
        "/Users/a123/.openclaw/workspace-research/skills",
        "/Users/a123/.openclaw/workspace-copywriter/skills",
        "/Users/a123/.openclaw/workspace-business/skills"
      ]
    }
  }
}
```

### 4. Gateway 重启 ✅
已执行 `openclaw daemon restart`，新进程 PID: 99858

### 5. AGENTS.md 路由规则 ✅
已创建独立的路由规则文件 `/Users/a123/.openclaw/广告营销任务路由规则.md`，并在各 workspace 的 AGENTS.md 中添加引用。

## ⚠️ 当前问题

### Skills 可能未被 Gateway 识别

**现象：**
- `openclaw doctor` 显示 `Eligible: 73` skills
- 重启前后数量没有变化（应该增加到 79）

**可能原因：**

1. **OpenClaw 的 skill 加载机制可能需要特定文件结构**
   - 已尝试添加 `skill.js` 文件
   - 可能还需要其他配置文件（如 `package.json`、`metadata.json`）

2. **SKILL.md frontmatter 格式问题**
   - 当前 frontmatter 只有 `name` 和 `description` 字段
   - 可能缺少必要的字段（如 `id`、`version`、`type`）

3. **Skills 加载时序问题**
   - Gateway 可能在配置更新前就完成了 skill 扫描
   - 需要触发 skill 重新扫描

4. **Skill ID 匹配机制**
   - OpenClaw 可能通过特定规则匹配 skill ID
   - 目录名（如 `kefu-ae`）可能需要符合特定命名规范

## 🔍 建议诊断步骤

### 方法 1: 检查现有 working skill 的完整结构
```bash
# 查看一个已加载成功的 skill 的完整文件结构
ls -la /Users/a123/.openclaw/skills/multi-search-engine/
ls -la /Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/
```

### 方法 2: 查看 Gateway 日志中的 skill 加载详情
```bash
# 查看启动时的 skill 加载日志
tail -500 /Users/a123/.openclaw/logs/gateway.log | grep -i "skill"
```

### 方法 3: 尝试手动触发 skill 重新加载
```bash
# 如果 OpenClaw 支持热重载
# 可能需要触发文件变更或调用特定 API
```

### 方法 4: 对比 SKILL.md frontmatter 格式
查看已成功加载的 skill 的 SKILL.md frontmatter，对比格式是否一致。

## 📝 下一步建议

根据上述诊断步骤的结果：

1. **如果是文件结构问题**：补充缺失的配置文件
2. **如果是 frontmatter 格式问题**：修正 SKILL.md 的 frontmatter
3. **如果是加载机制问题**：查阅 OpenClaw 文档或源码了解正确的 skill 注册流程
4. **如果配置正确但未生效**：联系用户在 Feishu 中实际测试，看 agent 是否能调用这些 skills

## 💡 临时解决方案

如果 skills 确实无法被 Gateway 自动识别，可以考虑：

1. **直接在 AGENTS.md 中内联规则**（已完成部分）
2. **使用 subagent 调用方式**手动指定专家 agent
3. **创建 wrapper skills** 通过已有的 skill 机制调用新的广告 skills

## ✅ Git 备份建议

无论诊断结果如何，建议现在就保存当前配置到 git：

```bash
cd ~/.openclaw
git add -A
git commit -m "新增：安装广告 Agency Skills 六个岗位（待验证加载）"
git push
```

这样即使需要调整，也有配置的完整记录。
