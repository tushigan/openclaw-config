#!/bin/bash
# 清除旧的 thread session，强制重新创建

SESSION_KEY="agent:design-shared:feishu:group:oc_deb2956a37fa31823df419ab084a073f:thread:omt_194faeeb794e1b95"
SESSION_ID="9a984cad-89d2-4d91-bf3b-50edfcc1a84b"

echo "准备清除旧的 thread session..."
echo "Session Key: $SESSION_KEY"
echo "Session ID: $SESSION_ID"
echo ""

# 1. 从 sessions.json 中删除这个 session
echo "1. 从 sessions.json 中删除 session 条目..."
jq "del(.\"$SESSION_KEY\")" /Users/a123/.openclaw/agents/design-shared/sessions/sessions.json > /Users/a123/.openclaw/agents/design-shared/sessions/sessions.json.tmp
mv /Users/a123/.openclaw/agents/design-shared/sessions/sessions.json.tmp /Users/a123/.openclaw/agents/design-shared/sessions/sessions.json

# 2. 移动相关文件到备份目录
BACKUP_DIR="/Users/a123/.openclaw/tmp/session-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "2. 移动相关文件到 $BACKUP_DIR ..."
mv /Users/a123/.openclaw/agents/design-shared/sessions/${SESSION_ID}* "$BACKUP_DIR/" 2>/dev/null || true

echo ""
echo "✅ 清除完成！"
echo ""
echo "现在在同一个话题中发起新的图片生成请求，将会创建新的 session 并加载最新的 AGENTS.md 规则。"
