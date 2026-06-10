# Sessions 性能优化方案

## 问题诊断

design-shared agent 的 sessions.json 达到 2.1MB，包含：
- 21个用户 × 30会话 = 630+ 会话
- 15个群组 × 平均30会话 = 450+ 会话  
- 32个 subagent × 平均37会话 = 1184+ 会话
- **总计超过 2200+ 会话记录**

每次 gateway 加载/保存会话时都要解析/序列化这 2.1MB 数据，导致：
- CPU 占用高（JSON 解析开销）
- 内存占用大（会话对象常驻）
- 磁盘 I/O 频繁

## 立即优化（清理历史会话）

### 1. 备份当前会话
```bash
cd /Users/a123/.openclaw/agents/design-shared/sessions
cp sessions.json sessions.json.backup-$(date +%Y%m%d-%H%M%S)
```

### 2. 清理旧会话（保留最近50条）
```bash
# 使用 jq 过滤每个用户/群组只保留最近10条会话
jq 'to_entries | map({
  key: .key,
  value: .value | sort_by(.timestamp) | reverse | .[0:10]
}) | from_entries' sessions.json.backup-* > sessions.json.cleaned

# 查看清理效果
ls -lh sessions.json*
```

### 3. 应用清理后的文件
```bash
mv sessions.json sessions.json.old
mv sessions.json.cleaned sessions.json

# 重启 gateway 生效
kill -TERM $(pgrep -f "openclaw.*gateway")
sleep 3
cd /Users/a123/.openclaw
openclaw gateway --port 18789 --verbose > logs/gateway.log 2> logs/gateway.err.log &
```

## 中期优化（添加自动清理）

### 创建定期清理脚本
```bash
#!/bin/bash
# scripts/cleanup-old-sessions.sh

MAX_SESSIONS_PER_KEY=15
BACKUP_DIR="/Users/a123/.openclaw/backups/sessions"

mkdir -p "$BACKUP_DIR"

for agent in design-shared strategy-shared main-shared; do
  SESSIONS_FILE="/Users/a123/.openclaw/agents/$agent/sessions/sessions.json"
  
  if [ -f "$SESSIONS_FILE" ]; then
    SIZE=$(stat -f%z "$SESSIONS_FILE")
    
    # 如果超过 1MB 就清理
    if [ "$SIZE" -gt 1048576 ]; then
      echo "Cleaning $agent sessions (size: ${SIZE} bytes)"
      
      # 备份
      cp "$SESSIONS_FILE" "$BACKUP_DIR/${agent}-$(date +%Y%m%d-%H%M%S).json"
      
      # 清理（保留每个 key 最近15条）
      jq --arg max "$MAX_SESSIONS_PER_KEY" '
        to_entries | map({
          key: .key,
          value: .value | sort_by(.timestamp) | reverse | .[0:($max|tonumber)]
        }) | from_entries
      ' "$SESSIONS_FILE" > "$SESSIONS_FILE.tmp" && mv "$SESSIONS_FILE.tmp" "$SESSIONS_FILE"
      
      echo "Cleaned: $(stat -f%z "$SESSIONS_FILE") bytes"
    fi
  fi
done
```

### 添加到 cron（每天凌晨3点清理）
```json
{
  "id": "cleanup-sessions",
  "schedule": {
    "kind": "cron",
    "expr": "0 3 * * *"
  },
  "payload": {
    "exec": "/Users/a123/.openclaw/scripts/cleanup-old-sessions.sh"
  }
}
```

## 长期方案（架构优化）

### 1. 会话存储改用 SQLite
- 当前：单个大 JSON 文件
- 优化：迁移到 SQLite 数据库（类似 memory/ 下的设计）
- 好处：增量读写，索引查询，自动压缩

### 2. 限制并发 agent 数量
在 openclaw.json 添加：
```json
{
  "agents": {
    "design-shared": {
      "concurrency": {
        "maxSessions": 50,
        "queueStrategy": "fifo"
      }
    }
  }
}
```

### 3. 分离热数据和冷数据
- 热数据：最近24小时会话（内存）
- 冷数据：历史会话（归档到压缩文件）
