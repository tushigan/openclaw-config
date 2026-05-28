#!/bin/bash
# 检测最近的 session 中是否有伪交付

set -euo pipefail

# 默认检查最近 1 小时
MINUTES=${1:-60}

echo "=== 检测最近 ${MINUTES} 分钟的伪交付 ==="
echo ""

total_sessions=0
fake_delivery_sessions=0

find /Users/a123/.openclaw/agents/main-shared/sessions -name "*.jsonl" -mmin -"${MINUTES}" 2>/dev/null | while read session; do
  total_sessions=$((total_sessions + 1))

  # 统计 MEDIA: 输出次数
  fake_count=$(grep -c "MEDIA:/" "$session" 2>/dev/null || echo 0)

  # 统计 message 工具调用次数
  tool_count=$(grep -c '"toolName":"message"' "$session" 2>/dev/null || echo 0)

  # 统计 message 工具成功返回次数
  success_count=$(grep -c '"ok":true.*"messageId"' "$session" 2>/dev/null || echo 0)

  if [ "$fake_count" -gt 0 ]; then
    fake_delivery_sessions=$((fake_delivery_sessions + 1))

    session_name=$(basename "$session")
    session_time=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$session" 2>/dev/null || echo "未知时间")

    echo "⚠️  发现伪交付: $session_name"
    echo "   时间: $session_time"
    echo "   MEDIA: 输出次数: $fake_count"
    echo "   message 工具调用次数: $tool_count"
    echo "   message 工具成功次数: $success_count"

    if [ "$tool_count" -eq 0 ]; then
      echo "   ❌ 严重：完全没有调用 message 工具"
    elif [ "$success_count" -eq 0 ]; then
      echo "   ⚠️  警告：调用了 message 工具但没有成功返回"
    elif [ "$fake_count" -gt "$success_count" ]; then
      echo "   ⚠️  警告：MEDIA: 输出次数多于成功发送次数"
    fi

    echo ""
  fi
done

echo "=== 检测完成 ==="
echo "总会话数: $total_sessions"
echo "伪交付会话数: $fake_delivery_sessions"

if [ "$fake_delivery_sessions" -gt 0 ]; then
  echo ""
  echo "建议："
  echo "1. 检查 brand-poster-creator/SKILL.md Step 8 的交付规则是否生效"
  echo "2. 检查 workspace/AGENTS.md 规则 2.1 是否被遵守"
  echo "3. 考虑在 skill 中增加更强的技术强制验证"
  exit 1
else
  echo "✅ 未发现伪交付问题"
  exit 0
fi
