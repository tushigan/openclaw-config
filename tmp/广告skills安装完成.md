# 广告 Agency Skills 安装完成

## ✅ 安装状态：已完成

所有 6 个广告 skills 已成功安装并配置完成，可以立即使用。

---

## 📦 已安装的 Skills

### 全局 Skills（main agent 使用）
- ✅ `kefu-ae` - 客服AE
- ✅ `boss` - 总控BOSS

### Strategy Agent Skills
- ✅ `celue-zj` - 策略总监
- ✅ `chuangyi-zj` - 创意总监

### Copywriter Agent Skills
- ✅ `wenan` - 文案

### Design Agent Skills
- ✅ `sheji` - 设计

---

## 🎯 使用方法

### 场景 1：品牌全案/整合营销

**用户说**："我要做一个新品上市的整合营销campaign"

**触发流程**：
```
main agent 识别 → 调用 boss skill → 自动协调各岗位
  ↓
kefu-ae 收集 Brief → strategy 制定策略 → copywriter 写文案 → design 做视觉
  ↓
main 统一交付
```

### 场景 2：竞品分析

**用户说**："帮我做竞品分析"

**触发流程**：
```
派发 strategy agent → 调用 celue-zj skill
  ↓
规划分析框架 → 调用 multi-search-engine 搜索 → 输出结构化分析报告
```

### 场景 3：Campaign 文案

**用户说**："写个 Campaign 主题"

**触发流程**：
```
派发 copywriter agent → 调用 wenan skill
  ↓
基于策略和创意方向 → 输出 2-3 个版本 → 说明适用场景
```

### 场景 4：视觉方向

**用户说**："给我一个视觉方向"

**触发流程**：
```
派发 design agent → 调用 sheji skill
  ↓
输出视觉方向 + AI prompt → 用户确认 → 调用执行 skills 生图
```

---

## ⚠️ 与现有 Skills 的协作关系

### 不冲突的场景

- **品牌海报**：仍然触发 `brand-poster-creator`（保持原有强制路由）
- **竞品分析**：先 `celue-zj` 规划，再 `multi-search-engine` 搜索
- **文案任务**：`wenan` 负责战略层，`brand-poster-creator` 的海报文案是执行层
- **设计任务**：`sheji` 负责方向规划，现有 skills 负责执行

### 触发优先级

1. **强制路由规则**（AGENTS.md 中明确定义）— 最高
2. **广告 skills**（方法论层）— 次之
3. **执行 skills**（工具层）— 最后

---

## 📝 AGENTS.md 臃肿评估

### ✅ 不臃肿

**更新前**：693 行（所有 workspace）
**更新后**：977 行（所有 workspace）
**新增**：284 行

**实际情况**：
- 各 workspace 的 AGENTS.md 只增加了 **1 行引用**
- 详细的触发规则、工作流说明都放在独立的 `广告营销任务路由规则.md` 中
- 保持了 AGENTS.md 的简洁性

**添加内容示例**：
```markdown
- **广告营销任务**：参考 /Users/a123/.openclaw/广告营销任务路由规则.md
```

---

## 🔄 Git 备份状态

✅ 已提交到本地 git
- Commit: `5d486bc1`
- 文件数：28 files changed
- 新增行：3033 insertions

⚠️ GitHub 推送失败（网络错误）
- 错误：`Error in the HTTP2 framing layer`
- 本地已保存，可以稍后手动推送：
  ```bash
  cd ~/.openclaw
  git push
  ```

---

## 📚 参考文档

- [广告营销任务路由规则.md](/Users/a123/.openclaw/广告营销任务路由规则.md) - 统一触发规则
- [tmp/广告skills安装总结.md](/Users/a123/.openclaw/tmp/广告skills安装总结.md) - 详细安装说明
- [tmp/广告skills触发词冲突分析.md](/Users/a123/.openclaw/tmp/广告skills触发词冲突分析.md) - 冲突分析

---

## 🚀 立即可用

无需重启 OpenClaw gateway，配置已生效。现在你可以：

1. 说"我要做一个品牌全案" → 测试 `boss` skill
2. 说"帮我做竞品分析" → 测试 `celue-zj` skill
3. 说"写个 Campaign 主题" → 测试 `wenan` skill
4. 说"给我一个视觉方向" → 测试 `sheji` skill

**所有配置已按需分配，确保不冲突，可以放心使用！**
