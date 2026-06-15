#!/bin/bash
# 清理任务包装脚本 - 执行清理并发送飞书通知
# 用法: cleanup-with-notification.sh <清理脚本路径> <任务名称>

set -e

CLEANUP_SCRIPT="$1"
TASK_NAME="$2"
TARGET_USER="user:ou_88079e6b06ce40e6851c96928fe1a03b"
OPENCLAW_ROOT="/Users/a123/.openclaw"
TEMP_LOG="/tmp/cleanup-notification-$$.log"

if [[ -z "$CLEANUP_SCRIPT" ]] || [[ -z "$TASK_NAME" ]]; then
    echo "用法: $0 <清理脚本路径> <任务名称>"
    exit 1
fi

if [[ ! -f "$CLEANUP_SCRIPT" ]]; then
    echo "错误：清理脚本不存在: $CLEANUP_SCRIPT"
    exit 1
fi

# 执行清理脚本并捕获输出
echo "执行清理任务: $TASK_NAME"
START_TIME=$(date +%s)

bash "$CLEANUP_SCRIPT" > "$TEMP_LOG" 2>&1
EXIT_CODE=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 解析清理结果
if [[ $EXIT_CODE -eq 0 ]]; then
    # 从日志中提取关键信息（使用 macOS 兼容的 grep）
    DELETED_FILES=$(grep -o '发现 [0-9]* 个文件' "$TEMP_LOG" | grep -o '[0-9]*' | awk '{sum+=$1} END {print sum+0}')
    FREED_SPACE=$(grep -o '约 [0-9.]*[MGT]' "$TEMP_LOG" | head -1 | sed 's/约 //' || echo "未知")

    # 构建通知消息
    MESSAGE="✅ ${TASK_NAME}完成

⏱ 执行时间: ${DURATION}秒
📁 清理文件数: ${DELETED_FILES}个
💾 释放空间: ${FREED_SPACE}

详细日志:
\`\`\`
$(tail -20 "$TEMP_LOG")
\`\`\`"
else
    MESSAGE="❌ ${TASK_NAME}失败

错误码: ${EXIT_CODE}
执行时间: ${DURATION}秒

错误日志:
\`\`\`
$(tail -20 "$TEMP_LOG")
\`\`\`"
fi

# 发送飞书通知
openclaw message send \
    --channel feishu \
    --account main \
    --target "$TARGET_USER" \
    --message "$MESSAGE" 2>&1

if [[ $? -eq 0 ]]; then
    echo "✅ 通知已发送到飞书"
else
    echo "⚠️ 发送通知失败"
fi

# 清理临时日志
rm -f "$TEMP_LOG"

exit $EXIT_CODE
