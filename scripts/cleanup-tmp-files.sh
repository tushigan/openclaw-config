#!/bin/bash
# 清理超过 7 天的临时文件

set -e

TMP_DIR="/Users/a123/.openclaw/tmp"
DAYS_THRESHOLD=7
LOG_FILE="/Users/a123/.openclaw/logs/cleanup-tmp-files.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting tmp files cleanup (older than ${DAYS_THRESHOLD} days)" >> "$LOG_FILE"

if [ ! -d "$TMP_DIR" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tmp directory not found: $TMP_DIR" >> "$LOG_FILE"
    exit 0
fi

# 清理旧文件
DELETED_COUNT=$(find "$TMP_DIR" -type f -mtime +${DAYS_THRESHOLD} 2>/dev/null | wc -l)
find "$TMP_DIR" -type f -mtime +${DAYS_THRESHOLD} -delete 2>> "$LOG_FILE"

# 清理空目录
find "$TMP_DIR" -type d -empty -delete 2>> "$LOG_FILE"

# 统计清理后的大小
CURRENT_SIZE=$(du -sh "$TMP_DIR" 2>/dev/null | cut -f1)
REMAINING_FILES=$(find "$TMP_DIR" -type f 2>/dev/null | wc -l)

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleanup completed. Deleted: $DELETED_COUNT files. Remaining: $REMAINING_FILES files, Size: $CURRENT_SIZE" >> "$LOG_FILE"

exit 0
