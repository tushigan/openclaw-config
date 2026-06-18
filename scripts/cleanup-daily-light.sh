#!/bin/bash
# OpenClaw 每日轻量清理脚本
# 执行时间：约 1-2 分钟
# 预期清理：50-100MB/天

set -e

OPENCLAW_ROOT="/Users/a123/.openclaw"
LOG_FILE="$OPENCLAW_ROOT/logs/cleanup-daily-light.log"
DRY_RUN=false

# 解析参数
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "[DRY RUN MODE] 不会实际删除文件"
fi

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 统计函数
count_files() {
    local pattern="$1"
    find $pattern 2>/dev/null | wc -l | tr -d ' '
}

# 计算大小函数
calc_size() {
    local pattern="$1"
    du -ch $pattern 2>/dev/null | tail -1 | awk '{print $1}'
}

log "========== 每日轻量清理开始 =========="

cd "$OPENCLAW_ROOT"

# 1. 清理 feishu-deliver 超过 7 天的文件
log "[1/5] 清理飞书交付目录（超过 7 天）"
OLD_FILES=$(find workspace/feishu-deliver -type f -mtime +7 2>/dev/null | wc -l | tr -d ' ')
OLD_SIZE=$(find workspace/feishu-deliver -type f -mtime +7 -exec du -ch {} + 2>/dev/null | tail -1 | awk '{print $1}')
log "发现 $OLD_FILES 个文件，约 $OLD_SIZE"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_FILES" -gt 0 ]]; then
    find workspace/feishu-deliver -type f -mtime +7 -delete 2>/dev/null || true
    log "已删除"
fi

# 2. 清理 tmp 超过 7 天的子目录
log "[2/5] 清理临时目录（超过 7 天）"
OLD_DIRS=$(find tmp -maxdepth 1 -type d -mtime +7 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_DIRS 个子目录"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_DIRS" -gt 0 ]]; then
    find tmp -maxdepth 1 -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    log "已删除"
fi

# 3. 压缩 logs 超过 7 天的日志
log "[3/5] 压缩日志文件（超过 7 天）"
OLD_LOGS=$(find logs -type f -name "*.log" -mtime +7 ! -name "*.gz" 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_LOGS 个日志文件"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_LOGS" -gt 0 ]]; then
    find logs -type f -name "*.log" -mtime +7 ! -name "*.gz" -exec gzip {} \; 2>/dev/null || true
    log "已压缩"
fi

# 4. 清理 delivery-queue 超过 3 天的文件
log "[4/5] 清理投递队列（超过 3 天）"
OLD_QUEUE=$(find delivery-queue -type f -mtime +3 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_QUEUE 个文件"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_QUEUE" -gt 0 ]]; then
    find delivery-queue -type f -mtime +3 -delete 2>/dev/null || true
    log "已删除"
fi

# 5. 清理入站媒体中超过 7 天的语音文件
log "[5/5] 清理入站媒体语音文件（超过 7 天）"
OLD_AUDIO=$(find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" \) -mtime +7 2>/dev/null | wc -l | tr -d ' ')
OLD_AUDIO_SIZE=$(find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" \) -mtime +7 -exec du -ch {} + 2>/dev/null | tail -1 | awk '{print $1}')
log "发现 $OLD_AUDIO 个音频文件，约 $OLD_AUDIO_SIZE"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_AUDIO" -gt 0 ]]; then
    find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.ogg" -o -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" \) -mtime +7 -delete 2>/dev/null || true
    log "已删除"
fi

# 清理空目录
if [[ "$DRY_RUN" == false ]]; then
    find workspace/feishu-deliver workspace*/.openclaw-inbound-media media/inbound tmp delivery-queue -type d -empty -delete 2>/dev/null || true
fi

log "========== 每日轻量清理完成 =========="
log ""
