#!/bin/bash
# OpenClaw 每周中等清理脚本
# 执行时间：约 5-10 分钟
# 预期清理：200-500MB/周

set -e

OPENCLAW_ROOT="/Users/a123/.openclaw"
LOG_FILE="$OPENCLAW_ROOT/logs/cleanup-weekly-medium.log"
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

log "========== 每周中等清理开始 =========="

cd "$OPENCLAW_ROOT"

# 1. 删除 workspace*/images 超过 30 天的图片及关联 JSON
log "[1/5] 清理工作区图片（超过 30 天）"
OLD_IMAGES=$(find workspace*/images -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -mtime +30 2>/dev/null | wc -l | tr -d ' ')
OLD_IMAGES_SIZE=$(find workspace*/images -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -mtime +30 -exec du -ch {} + 2>/dev/null | tail -1 | awk '{print $1}')
log "发现 $OLD_IMAGES 个图片文件，约 $OLD_IMAGES_SIZE"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_IMAGES" -gt 0 ]]; then
    find workspace*/images -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -mtime +30 -delete 2>/dev/null || true
    find workspace*/images -type f -name "*.delivery.json" -mtime +30 -delete 2>/dev/null || true
    find workspace*/images -type f -name "*.result.json" -mtime +30 -delete 2>/dev/null || true
    log "已删除"
fi

# 2. 删除 workspace*/outputs 超过 60 天的 JSON/Markdown
log "[2/5] 清理输出文件（超过 60 天的 JSON/Markdown）"
OLD_DOCS=$(find workspace*/outputs -type f \( -name "*.json" -o -name "*.md" \) -mtime +60 ! -path "*/feishu_daily/*" 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_DOCS 个文档文件"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_DOCS" -gt 0 ]]; then
    find workspace*/outputs -type f \( -name "*.json" -o -name "*.md" \) -mtime +60 ! -path "*/feishu_daily/*" -delete 2>/dev/null || true
    log "已删除"
fi

# 3. 压缩飞书日报归档（超过 30 天）
log "[3/5] 压缩飞书日报归档（超过 30 天）"
OLD_REPORTS=$(find workspace/outputs/feishu_daily -type d -mindepth 1 -maxdepth 1 -mtime +30 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_REPORTS 个目录"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_REPORTS" -gt 0 ]]; then
    find workspace/outputs/feishu_daily -type d -mindepth 1 -maxdepth 1 -mtime +30 -exec bash -c 'tar -czf "{}.tar.gz" "{}" && rm -rf "{}"' \; 2>/dev/null || true
    log "已压缩"
fi

# 4. 压缩 agent 会话超过 60 天的记录
log "[4/5] 压缩 agent 会话记录（超过 60 天）"
OLD_SESSIONS=$(find agents/*/sessions -type f -name "*.jsonl" -mtime +60 ! -name "*.gz" 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_SESSIONS 个会话文件"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_SESSIONS" -gt 0 ]]; then
    find agents/*/sessions -type f -name "*.jsonl" -mtime +60 ! -name "*.gz" -exec gzip {} \; 2>/dev/null || true
    log "已压缩"
fi

# 5. 删除入站媒体中超过 14 天的图片文件
log "[5/5] 清理入站媒体图片（超过 14 天）"
OLD_INBOUND_IMAGES=$(find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -mtime +14 2>/dev/null | wc -l | tr -d ' ')
OLD_INBOUND_SIZE=$(find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -mtime +14 -exec du -ch {} + 2>/dev/null | tail -1 | awk '{print $1}')
log "发现 $OLD_INBOUND_IMAGES 个图片文件，约 $OLD_INBOUND_SIZE"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_INBOUND_IMAGES" -gt 0 ]]; then
    find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -mtime +14 -delete 2>/dev/null || true
    log "已删除"
fi

# 清理空目录
if [[ "$DRY_RUN" == false ]]; then
    find workspace*/images workspace*/outputs workspace*/.openclaw-inbound-media media/inbound agents/*/sessions -type d -empty -delete 2>/dev/null || true
fi

log "========== 每周中等清理完成 =========="
log ""
