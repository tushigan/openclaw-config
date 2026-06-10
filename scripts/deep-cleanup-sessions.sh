#!/bin/bash
# 清理 sessions.json：移除旧会话和不必要的大字段

set -e

AGENT=${1:-design-shared}
SESSIONS_DIR="/Users/a123/.openclaw/agents/$AGENT/sessions"
SESSIONS_FILE="$SESSIONS_DIR/sessions.json"
BACKUP_DIR="$SESSIONS_DIR/backups"
DAYS_TO_KEEP=${2:-30}  # 默认保留30天

echo "=== OpenClaw Sessions 深度清理 ==="
echo "Agent: $AGENT"
echo "保留最近 $DAYS_TO_KEEP 天的会话"
echo ""

if [ ! -f "$SESSIONS_FILE" ]; then
  echo "❌ 找不到 sessions.json"
  exit 1
fi

# 显示当前状态
CURRENT_SIZE=$(stat -f%z "$SESSIONS_FILE" 2>/dev/null || stat -c%s "$SESSIONS_FILE")
CURRENT_KEYS=$(jq 'keys | length' "$SESSIONS_FILE")
echo "当前状态："
echo "  文件大小: $(echo $CURRENT_SIZE | awk '{printf "%.2f MB", $1/1024/1024}')"
echo "  会话 key 数量: $CURRENT_KEYS"
echo ""

# 创建备份
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/sessions-$(date +%Y%m%d-%H%M%S).json"
echo "📦 备份到: $BACKUP_FILE"
cp "$SESSIONS_FILE" "$BACKUP_FILE"

# 计算时间阈值（毫秒）
CUTOFF_MS=$(echo "$(date +%s)000 - ($DAYS_TO_KEEP * 86400000)" | bc)

# 清理策略：
# 1. 删除超过 N 天未更新的会话
# 2. 移除不必要的大字段（systemPromptReport, skillsSnapshot）
echo "🧹 清理中..."
jq --arg cutoff "$CUTOFF_MS" '
  to_entries
  | map(select(.value.updatedAt > ($cutoff | tonumber)))
  | map({
      key: .key,
      value: .value | del(.systemPromptReport, .skillsSnapshot)
    })
  | from_entries
' "$SESSIONS_FILE" > "$SESSIONS_FILE.cleaned"

# 验证
if jq empty "$SESSIONS_FILE.cleaned" 2>/dev/null; then
  NEW_SIZE=$(stat -f%z "$SESSIONS_FILE.cleaned" 2>/dev/null || stat -c%s "$SESSIONS_FILE.cleaned")
  NEW_KEYS=$(jq 'keys | length' "$SESSIONS_FILE.cleaned")
  SAVED=$(echo "scale=1; ($CURRENT_SIZE - $NEW_SIZE) * 100 / $CURRENT_SIZE" | bc)

  echo ""
  echo "✅ 清理完成："
  echo "  新文件大小: $(echo $NEW_SIZE | awk '{printf "%.2f MB", $1/1024/1024}')"
  echo "  会话 key 数量: $NEW_KEYS（删除 $((CURRENT_KEYS - NEW_KEYS)) 个）"
  echo "  节省空间: ${SAVED}%"
  echo ""

  # 应用
  mv "$SESSIONS_FILE.cleaned" "$SESSIONS_FILE"

  echo "📝 已删除的字段："
  echo "  - systemPromptReport（系统提示词报告，可从 sessionFile 重建）"
  echo "  - skillsSnapshot（技能快照）"
  echo ""
  echo "🔄 需要重启 gateway 才能生效"
else
  echo "❌ 清理失败"
  rm -f "$SESSIONS_FILE.cleaned"
  exit 1
fi
