# OpenClaw 文件定期维护清理计划

## 📊 当前磁盘占用分析

### 🔴 高占用目录（需要清理）

| 目录 | 大小 | 文件数 | 说明 | 清理优先级 |
|------|------|--------|------|-----------|
| `workspace-design/outputs` | **28GB** | 6,358 | 设计输出（含8.2GB PSD文件、98MB视频） | 🔴 极高 |
| `workspace/outputs` | **5.3GB** | 3,804 | 主工作区输出文件 | 🔴 极高 |
| `agents/main-shared/sessions` | **1.6GB** | - | 共享主 agent 会话记录 | 🟡 中 |
| `workspace/feishu-deliver` | **11GB** | 2,282 | 飞书交付临时目录 | 🔴 极高 |
| `agents/main/sessions` | **917MB** | - | 主 agent 会话记录 | 🟡 中 |
| `workspace-design/images` | **1.3GB** | - | 设计图片输出 | 🟠 高 |
| `workspace/images` | **575MB** | - | 主工作区图片 | 🟠 高 |
| `workspace-copywriter/images` | **118MB** | 140+ | 文案配图（榴莲包装盒等） | 🟢 低 |
| `tmp/` | **331MB** | 122个子目录 | 临时工作目录 | 🟠 高 |
| `logs/` | **32MB** | 3个超期文件 | 网关日志 | 🟢 低 |

**总计需清理空间预估：47GB+**

| `workspace*/.openclaw-inbound-media` | **2.2GB** | 各 workspace 入站媒体（语音、图片、文档） | 🟠 高 |
| `media/inbound` | **1.3GB** | 根目录媒体入站缓存 | 🟠 高 |

**总计需清理空间预估：50GB+**

### ✅ 低占用目录（暂不需清理）

- `cron/runs`: 1.6MB（定时任务记录，无超期文件）
- `delivery-queue`: 96KB（17个超过3天的文件可清理）
- `feishu/`: 4.7MB（飞书频道数据）
- `tasks/`: 6.3MB（任务历史 SQLite）
- `flows/`: 736KB（流程注册表）

---

## 🎯 清理策略建议

### 策略一：设计输出文件（workspace-design/outputs）

**当前状态：**
- 总大小：28GB
- 包含 8.2GB PSD 源文件（最占空间）
- 包含 98MB 视频文件
- 包含 14 个 Dreamina 项目，43 个运行历史

**清理规则：**
```bash
# 1. 删除超过 60 天的 PSD 源文件（保留最终交付版）
find workspace-design/outputs -type f -name "*.psd" -mtime +60 -delete

# 2. 删除超过 30 天的中间产物和测试文件
find workspace-design/outputs -type d \( -name "*-test" -o -name "*-devcheck" -o -name "dreamina-manual-fetch-*" \) -mtime +30 -exec rm -rf {} +

# 3. 清理 Dreamina 项目中的中间下载文件（保留最终版）
find workspace-design/outputs/dreamina-reference-video/projects/*/runs -type d -name "downloads" -mtime +30 -exec rm -rf {} +

# 4. 压缩超过 90 天的完整项目目录
find workspace-design/outputs -maxdepth 1 -type d -name "project_id=*" -mtime +90 -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} +
```

**预期清理：15-20GB**

---

### 策略二：飞书交付临时目录（workspace/feishu-deliver）

**当前状态：**
- 总大小：11GB
- 文件数：2,282
- 超过 7 天：1,687 个文件
- 超过 30 天：190 个文件

**清理规则：**
```bash
# 已交付超过 7 天的文件应该删除（用户已收到）
find workspace/feishu-deliver -type f -mtime +7 -delete

# 清理空目录
find workspace/feishu-deliver -type d -empty -delete
```

**预期清理：8-10GB**

---

### 策略三：主工作区输出（workspace/outputs）

**当前状态：**
- 总大小：5.3GB
- 总文件数：3,804
- 超过 30 天：957 个文件
- 超过 60 天：115 个文件
- 包含飞书日报归档（22MB）

**清理规则：**
```bash
# 1. 压缩飞书日报归档（超过 30 天的）
find workspace/outputs/feishu_daily -type d -mindepth 1 -maxdepth 1 -mtime +30 -exec tar -czf {}.tar.gz {} \; -exec rm -rf {} +

# 2. 删除超过 60 天的临时 JSON/Markdown 文件
find workspace/outputs -type f \( -name "*.json" -o -name "*.md" \) -mtime +60 ! -path "*/feishu_daily/*" -delete

# 3. 删除超过 90 天的所有输出文件
find workspace/outputs -type f -mtime +90 -delete
```

**预期清理：2-3GB**

---

### 策略四：图片输出文件

**当前状态：**
- workspace/images: 575MB
- workspace-design/images: 1.3GB
- workspace-copywriter/images: 118MB
- 其他 workspace: <100MB
- **超过 30 天的图片总计：106MB**

**清理规则：**
```bash
# 删除超过 30 天的图片及关联 JSON
find workspace*/images -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -mtime +30 -delete
find workspace*/images -type f -name "*.delivery.json" -mtime +30 -delete
find workspace*/images -type f -name "*.result.json" -mtime +30 -delete
```

**预期清理：500MB-1GB**

---

### 策略五：Agent 会话记录

**当前状态：**
- agents/main-shared/sessions: 1.6GB
- agents/main/sessions: 917MB
- agents/design-shared/sessions: 575MB
- 其他 agents: <200MB 每个
- **超过 60 天的会话：30 个文件**
- **超过 90 天的会话：0 个文件**（说明会话都比较新）

**清理规则：**
```bash
# 压缩超过 60 天的会话记录（不删除，保留用于调试）
find agents/*/sessions -type f -name "*.jsonl" -mtime +60 -exec gzip {} \;

# 删除超过 180 天的会话记录
find agents/*/sessions -type f \( -name "*.jsonl" -o -name "*.jsonl.gz" \) -mtime +180 -delete
```

**预期清理：100-200MB（压缩节省）**

---

### 策略六：临时目录清理

**当前状态：**
- tmp/: 331MB，122 个子目录
- 超过 7 天的子目录：100 个

**清理规则：**
```bash
# 删除超过 7 天的临时目录
find tmp -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

**预期清理：250-300MB**

---

### 策略七：日志文件清理

**当前状态：**
- logs/: 32MB
- 超过 7 天的日志：52KB
- 超过 30 天的日志：3 个文件

**清理规则：**
```bash
# 压缩超过 7 天的日志
find logs -type f -name "*.log" -mtime +7 ! -name "*.gz" -exec gzip {} \;

# 删除超过 90 天的压缩日志
find logs -type f -name "*.log.gz" -mtime +90 -delete
```

**预期清理：10-15MB**

---

### 策略八：入站媒体文件清理（.openclaw-inbound-media）

**当前状态：**
- media/inbound: 1.3GB
- workspace*/.openclaw-inbound-media: 2.2GB（分散在各 workspace）
- 包含：语音消息（.ogg/.mp3）16MB、图片/PDF/文档 2.9GB
- 超过 7 天：528 个文件
- 超过 30 天：183 个文件（约 22MB）

**清理规则：**
```bash
# 1. 删除超过 7 天的语音文件（已转录完成）
find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" \) -mtime +7 -delete

# 2. 删除超过 14 天的图片文件（已处理完成）
find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -mtime +14 -delete

# 3. 删除超过 30 天的文档文件
find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.xlsx" \) -mtime +30 -delete

# 4. 清理空目录
find workspace*/.openclaw-inbound-media media/inbound -type d -empty -delete
```

**预期清理：1-2GB**

---

### 策略九：其他运行记录清理

**清理规则：**
```bash
# 清理投递队列超过 3 天的文件
find delivery-queue -type f -mtime +3 -delete

# 压缩定时任务运行记录（超过 30 天）
find cron/runs -type f -mtime +30 -exec gzip {} \;

# 删除超过 180 天的定时任务记录
find cron/runs -type f -mtime +180 -delete
```

**预期清理：50-100MB**

---

## 📅 建议的定时清理任务

### 任务 1：每日轻量清理（凌晨 2:30）

```json
{
  "id": "daily-lightweight-cleanup",
  "name": "每日轻量清理",
  "description": "清理已交付文件、临时目录、压缩旧日志",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "30 2 * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "systemEvent",
    "event": "exec",
    "command": "bash /Users/a123/.openclaw/scripts/cleanup-daily-light.sh"
  },
  "delivery": {
    "mode": "none"
  }
}
```

**清理内容：**
- 删除 feishu-deliver 超过 7 天的文件
- 删除 tmp 超过 7 天的子目录
- 压缩 logs 超过 7 天的日志
- 清理 delivery-queue 超过 3 天的文件
- 删除入站媒体中超过 7 天的语音文件
- 删除入站媒体中超过 14 天的图片文件

---

### 任务 2：每周中等清理（每周日凌晨 3:00）

```json
{
  "id": "weekly-medium-cleanup",
  "name": "每周中等清理",
  "description": "清理超过 30 天的图片、JSON、Markdown 文件",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 3 * * 0",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "systemEvent",
    "event": "exec",
    "command": "bash /Users/a123/.openclaw/scripts/cleanup-weekly-medium.sh"
  },
  "delivery": {
    "mode": "none"
  }
}
```

**清理内容：**
- 删除 workspace*/images 超过 30 天的图片及关联 JSON
- 删除 workspace*/outputs 超过 60 天的 JSON/Markdown
- 压缩飞书日报归档超过 30 天的目录
- 压缩 agent 会话超过 60 天的记录

---

### 任务 3：每月深度清理（每月 1 号凌晨 4:00）

```json
{
  "id": "monthly-deep-cleanup",
  "name": "每月深度清理",
  "description": "清理设计产物、PSD 源文件、旧会话记录",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 4 1 * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "systemEvent",
    "event": "exec",
    "command": "bash /Users/a123/.openclaw/scripts/cleanup-monthly-deep.sh"
  },
  "delivery": {
    "mode": "none"
  }
}
```

**清理内容：**
- 删除 workspace-design/outputs 超过 60 天的 PSD 文件
- 清理 Dreamina 项目中超过 30 天的中间下载文件
- 压缩超过 90 天的完整设计项目
- 删除 workspace/outputs 超过 90 天的文件
- 删除超过 180 天的会话记录和日志

---

## 🛠️ 实施步骤

### 第一步：创建清理脚本

创建三个清理脚本：

1. **每日轻量清理脚本**
   - 文件：`scripts/cleanup-daily-light.sh`
   - 执行时间：约 1-2 分钟
   - 预期清理：50-100MB/天

2. **每周中等清理脚本**
   - 文件：`scripts/cleanup-weekly-medium.sh`
   - 执行时间：约 5-10 分钟
   - 预期清理：200-500MB/周

3. **每月深度清理脚本**
   - 文件：`scripts/cleanup-monthly-deep.sh`
   - 执行时间：约 10-20 分钟
   - 预期清理：2-5GB/月

### 第二步：添加定时任务

修改 `cron/jobs.json`，添加上述三个定时任务。

### 第三步：测试运行

在正式启用前，先手动执行一次（使用 dry-run 模式）：

```bash
bash /Users/a123/.openclaw/scripts/cleanup-daily-light.sh --dry-run
bash /Users/a123/.openclaw/scripts/cleanup-weekly-medium.sh --dry-run
bash /Users/a123/.openclaw/scripts/cleanup-monthly-deep.sh --dry-run
```

### 第四步：启用并监控

- 启用定时任务
- 每周检查清理日志
- 根据实际情况调整保留天数

---

## 📈 预期效果

### 立即清理（首次运行）
- **设计输出清理：15-20GB**
- **飞书交付目录：8-10GB**
- **主工作区输出：2-3GB**
- **入站媒体文件：1-2GB**
- **图片文件：500MB-1GB**
- **临时目录：250-300MB**
- **其他：200MB**

**首次清理总计：约 28-38GB**

### 长期维护（稳定后）
- 每日清理：50-100MB
- 每周清理：200-500MB
- 每月清理：2-5GB

**预期每月增长：<5GB**（相比当前每月可能 10-20GB 的增长）

---

## ⚠️ 注意事项

### 不要清理的目录

以下目录包含重要配置或运行时数据，**不应清理**：

- `memory/*.sqlite` - Agent 长期记忆数据库
- `workspace*/AGENTS.md`, `SOUL.md`, `IDENTITY.md` - 人格配置
- `credentials/` - 认证凭据
- `feishu/conversation-ids.json` - 飞书会话映射
- `flows/*.db`, `tasks/*.db` - 流程和任务数据库
- `agents/*/agent/models.json` - Agent 模型配置
- `skills/` - 技能定义（除非明确归档）
- `workspace*/.openclaw-inbound-media` 和 `media/inbound` - **可以清理**，但建议保留 7-30 天

### 语音文件说明

`.openclaw-inbound-media` 和 `media/inbound` 目录存储的是：
- 用户通过飞书发送的**语音消息原始音频**（.ogg/.mp3）
- 用户发送的**图片附件**（.png/.jpg）
- 用户上传的**PDF/文档**（.pdf/.docx）

这些文件在处理后（语音转录、图片分析、文档提取）可以安全删除，因为：
- ✅ 语音内容已转成文字存在会话记录中
- ✅ 图片内容已被分析或交付完成
- ✅ 文档内容已被提取和使用

**建议保留期**：
- 语音文件：7 天（转录后即可删除）
- 图片文件：14 天（处理/交付后可删除）
- 文档文件：30 天（提取后可删除）

### 清理前备份

首次执行深度清理前，建议备份：

```bash
# 备份到外部存储
tar -czf ~/openclaw-backup-$(date +%Y%m%d).tar.gz \
  ~/.openclaw/workspace-design/outputs \
  ~/.openclaw/workspace/outputs \
  ~/.openclaw/agents/*/sessions
```

### 恢复策略

如果误删重要文件：

1. 从 git 恢复配置文件
2. 从 Time Machine 或外部备份恢复输出文件
3. 已交付给用户的文件可从飞书下载

---

## 📝 变更日志

- **2026-06-12**: 初始版本，基于磁盘占用分析创建清理计划
