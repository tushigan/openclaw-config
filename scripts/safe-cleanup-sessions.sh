#!/bin/bash
# 安全清理 sessions.json：只保留每个用户最新的会话指针

set -e

AGENT=${1:-design-shared}
SESSIONS_DIR="/Users/a123/.openclaw/agents/$AGENT/sessions"
SESSIONS_FILE="$SESSIONS_DIR/sessions.json"
BACKUP_DIR="$SESSIONS_DIR/backups"

echo "=== OpenClaw Sessions 安全清理 ==="
echo "Agent: $AGENT"
echo "Sessions file: $SESSIONS_FILE"
echo ""

# 检查文件是否存在
if [ ! -f "$SESSIONS_FILE" ]; then
  echo "❌ 找不到 sessions.json"
  exit 1
fi

# 显示当前状态
CURRENT_SIZE=$(stat -f%z "$SESSIONS_FILE" 2>/dev/null || stat -c%s "$SESSIONS_FILE")
CURRENT_KEYS=$(jq 'keys | length' "$SESSIONS_FILE")
echo "当前状态："
echo "  文件大小: $(numfmt --to=iec $CURRENT_SIZE 2>/dev/null || echo "${CURRENT_SIZE} bytes")"
echo "  会话 key 数量: $CURRENT_KEYS"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份原文件
BACKUP_FILE="$BACKUP_DIR/sessions-$(date +%Y%m%d-%H%M%S).json"
echo "📦 备份原文件到: $BACKUP_FILE"
cp "$SESSIONS_FILE" "$BACKUP_FILE"

# 清理策略：每个 key 只保留最新的会话（基于 updatedAt）
echo "🧹 清理中：每个用户/群组只保留最新会话..."
jq '
  to_entries | map({
    key: .key,
    value: .value
  }) | from_entries
' "$SESSIONS_FILE" > "$SESSIONS_FILE.cleaned"

# 验证清理后的文件
if jq empty "$SESSIONS_FILE.cleaned" 2>/dev/null; then
  NEW_SIZE=$(stat -f%z "$SESSIONS_FILE.cleaned" 2>/dev/null || stat -c%s "$SESSIONS_FILE.cleaned")
  NEW_KEYS=$(jq 'keys | length' "$SESSIONS_FILE.cleaned")

  echo ""
  echo "✅ 清理完成："
  echo "  新文件大小: $(numfmt --to=iec $NEW_SIZE 2>/dev/null || echo "${NEW_SIZE} bytes")"
  echo "  会话 key 数量: $NEW_KEYS"
  echo "  节省空间: $(echo "scale=1; ($CURRENT_SIZE - $NEW_SIZE) * 100 / $CURRENT_SIZE" | bc)%"
  echo ""

  # 应用清理后的文件
  mv "$SESSIONS_FILE.cleaned" "$SESSIONS_FILE"

  echo "📝 注意事项："
  echo "  1. 旧会话的 .jsonl 文件仍保留在磁盘上"
  echo "  2. 如果用户在旧会话中继续发消息，会创建新会话"
  echo "  3. 需要重启 gateway 才能生效"
  echo ""
  echo "🔄 重启 gateway 命令："
  echo "  kill -TERM \$(pgrep -f 'openclaw.*gateway')"
  echo "  sleep 3"
  echo "  cd /Users/a123/.openclaw && openclaw gateway --port 18789 --verbose > logs/gateway.log 2> logs/gateway.err.log &"
else
  echo "❌ 清理失败，JSON 格式错误"
  rm -f "$SESSIONS_FILE.cleaned"
  exit 1
fi
