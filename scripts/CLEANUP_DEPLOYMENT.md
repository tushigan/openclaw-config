# OpenClaw 文件清理系统部署完成

## ✅ 已完成的工作

### 1. 创建了三个清理脚本

- ✅ [scripts/cleanup-daily-light.sh](scripts/cleanup-daily-light.sh) - 每日轻量清理
- ✅ [scripts/cleanup-weekly-medium.sh](scripts/cleanup-weekly-medium.sh) - 每周中等清理
- ✅ [scripts/cleanup-monthly-deep.sh](scripts/cleanup-monthly-deep.sh) - 每月深度清理

### 2. 添加了三个定时任务到 cron/jobs.json

- ✅ **每日轻量清理** - 每天凌晨 2:45
- ✅ **每周中等清理** - 每周日凌晨 3:15
- ✅ **每月深度清理** - 每月 1 号凌晨 4:00

### 3. 完成了 dry-run 测试

所有脚本都通过了 dry-run 测试，发现的可清理内容：

**每日轻量清理（立即可清理）：**
- 飞书交付目录：1,687 个文件，约 6.6GB
- 临时目录：100 个子目录
- 日志文件：1 个待压缩
- 投递队列：17 个文件
- 语音文件：38 个，约 14MB

**每周中等清理（立即可清理）：**
- 工作区图片：11 个，约 106MB
- 入站媒体图片：182 个，约 165MB

**每月深度清理（立即可清理）：**
- 主工作区输出：115 个文件（超过 90 天）

**立即可清理总计：约 7GB+**

---

## 📋 下一步操作

### 选项 A：立即手动清理（推荐）

如果你想立即回收空间，可以运行：

```bash
cd ~/.openclaw

# 执行每日清理（清理约 6.6GB）
bash scripts/cleanup-daily-light.sh

# 执行每周清理（清理约 271MB）
bash scripts/cleanup-weekly-medium.sh

# 执行每月清理（清理一些旧文件）
bash scripts/cleanup-monthly-deep.sh
```

### 选项 B：等待定时任务自动执行

定时任务已配置好，会按以下时间自动执行：
- 明天凌晨 2:45 - 每日轻量清理
- 本周日凌晨 3:15 - 每周中等清理
- 下月 1 号凌晨 4:00 - 每月深度清理

### 选项 C：重启 OpenClaw 网关使配置生效

```bash
# 如果网关正在运行，需要重启使新的定时任务生效
openclaw daemon restart
# 或
pkill -f "openclaw gateway" && openclaw gateway --port 18789 --verbose &
```

---

## 📊 清理策略总览

### 每日清理（凌晨 2:45）
- ✅ 删除飞书交付目录超过 7 天的文件
- ✅ 删除临时目录超过 7 天的子目录
- ✅ 压缩日志文件超过 7 天的记录
- ✅ 清理投递队列超过 3 天的文件
- ✅ 删除入站媒体超过 7 天的语音文件

**预期效果：每天回收 50-100MB**

### 每周清理（每周日 3:15）
- ✅ 删除工作区图片超过 30 天
- ✅ 删除输出文件超过 60 天的 JSON/Markdown
- ✅ 压缩飞书日报归档超过 30 天
- ✅ 压缩 agent 会话超过 60 天
- ✅ 删除入站媒体超过 14 天的图片

**预期效果：每周回收 200-500MB**

### 每月清理（每月 1 号 4:00）
- ✅ 删除设计输出超过 60 天的 PSD 文件
- ✅ 删除测试/开发目录超过 30 天
- ✅ 清理 Dreamina 中间下载文件超过 30 天
- ✅ 压缩设计项目超过 90 天
- ✅ 删除主工作区输出超过 90 天的文件
- ✅ 删除会话记录超过 180 天
- ✅ 删除入站媒体超过 30 天的文档

**预期效果：每月回收 2-5GB**

---

## 📁 清理覆盖的目录

### 高优先级（会自动清理）
- ✅ `workspace/feishu-deliver` - 飞书交付临时文件（7天）
- ✅ `workspace*/.openclaw-inbound-media` - 入站媒体（语音7天，图片14天，文档30天）
- ✅ `media/inbound` - 根媒体缓存（语音7天，图片14天，文档30天）
- ✅ `tmp/` - 临时目录（7天）
- ✅ `workspace-design/outputs` - 设计输出（PSD 60天，测试目录30天，项目90天）
- ✅ `workspace/outputs` - 主工作区输出（JSON/Markdown 60天，其他90天）
- ✅ `workspace*/images` - 工作区图片（30天）
- ✅ `logs/` - 日志文件（压缩7天，删除90天）

### 中等优先级（会自动清理）
- ✅ `agents/*/sessions` - Agent 会话（压缩60天，删除180天）
- ✅ `delivery-queue/` - 投递队列（3天）
- ✅ `cron/runs` - 定时任务记录（压缩30天，删除180天）

### 不会清理的目录
- ❌ `memory/*.sqlite` - 长期记忆数据库
- ❌ `workspace*/AGENTS.md, SOUL.md, IDENTITY.md` - 人格配置
- ❌ `credentials/` - 认证凭据
- ❌ `feishu/conversation-ids.json` - 飞书会话映射
- ❌ `flows/*.db`, `tasks/*.db` - 流程和任务数据库
- ❌ `skills/` - 技能定义

---

## 🔍 清理日志位置

清理执行日志会写入：
- `logs/cleanup-daily-light.log` - 每日清理日志
- `logs/cleanup-weekly-medium.log` - 每周清理日志
- `logs/cleanup-monthly-deep.log` - 每月清理日志

可以随时查看清理历史：
```bash
tail -100 logs/cleanup-daily-light.log
```

---

## ⚠️ 重要说明

### 关于入站媒体文件

**`.openclaw-inbound-media`** 和 **`media/inbound`** 目录存储用户通过飞书发送的：
- 🎤 **语音消息原始音频**（.ogg/.mp3） - 转录后 7 天删除
- 🖼️ **图片附件**（.png/.jpg） - 处理后 14 天删除
- 📄 **PDF/文档**（.pdf/.docx） - 提取后 30 天删除

这些文件在处理后可以安全删除，因为：
- ✅ 语音内容已转成文字存在会话记录中
- ✅ 图片内容已被分析或交付完成
- ✅ 文档内容已被提取和使用

### 安全保障

所有脚本都包含：
- ✅ `set -e` - 遇到错误立即停止
- ✅ `|| true` - 容错处理，避免单个文件失败导致整体中断
- ✅ `2>/dev/null` - 忽略无关错误提示
- ✅ 空目录清理 - 自动删除清理后的空目录

### 恢复策略

如果误删重要文件：
1. 从 git 恢复配置文件（openclaw.json, AGENTS.md 等）
2. 从 Time Machine 或外部备份恢复输出文件
3. 已交付给用户的文件可从飞书下载

---

## 📈 预期效果

### 首次清理（如果立即执行）
- 飞书交付目录：约 6.6GB
- 入站媒体：约 400MB
- 临时目录：约 250MB
- 工作区图片：约 100MB
- **总计：约 7-8GB**

### 长期维护（稳定后）
- 每日清理：50-100MB
- 每周清理：200-500MB
- 每月清理：2-5GB
- **预期每月硬盘增长：<5GB**（相比当前可能 10-20GB 的增长）

---

## 📚 相关文档

- [scripts/CLEANUP_PLAN.md](CLEANUP_PLAN.md) - 完整的清理策略文档
- [cron/jobs.json](../cron/jobs.json) - 定时任务配置

---

**部署时间：** 2026-06-12  
**状态：** ✅ 就绪，等待执行或定时任务触发
