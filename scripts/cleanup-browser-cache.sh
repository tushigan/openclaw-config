#!/bin/bash
# 清理超过 15 天的浏览器缓存数据

set -e

BROWSER_DIR="/Users/a123/.openclaw/browser"
DAYS_THRESHOLD=15
LOG_FILE="/Users/a123/.openclaw/logs/cleanup-browser-cache.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting browser cache cleanup (older than ${DAYS_THRESHOLD} days)" >> "$LOG_FILE"

if [ ! -d "$BROWSER_DIR" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Browser directory not found: $BROWSER_DIR" >> "$LOG_FILE"
    exit 0
fi

# 清理旧的 Cache 目录
find "$BROWSER_DIR" -type d -name "Cache" -exec find {} -type f -mtime +${DAYS_THRESHOLD} -delete \; 2>> "$LOG_FILE"

# 清理旧的 Code Cache 目录
find "$BROWSER_DIR" -type d -name "Code Cache" -exec find {} -type f -mtime +${DAYS_THRESHOLD} -delete \; 2>> "$LOG_FILE"

# 清理旧的 GPUCache 目录
find "$BROWSER_DIR" -type d -name "GPUCache" -exec find {} -type f -mtime +${DAYS_THRESHOLD} -delete \; 2>> "$LOG_FILE"

# 清理旧的日志文件
find "$BROWSER_DIR" -type f -name "*.log" -mtime +${DAYS_THRESHOLD} -delete 2>> "$LOG_FILE"

# 统计清理后的大小
CURRENT_SIZE=$(du -sh "$BROWSER_DIR" 2>/dev/null | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleanup completed. Current browser directory size: $CURRENT_SIZE" >> "$LOG_FILE"

exit 0
