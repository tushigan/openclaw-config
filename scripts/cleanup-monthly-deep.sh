#!/bin/bash
# OpenClaw 每月深度清理脚本
# 执行时间：约 10-20 分钟
# 预期清理：2-5GB/月

set -e

OPENCLAW_ROOT="/Users/a123/.openclaw"
LOG_FILE="$OPENCLAW_ROOT/logs/cleanup-monthly-deep.log"
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

log "========== 每月深度清理开始 =========="

cd "$OPENCLAW_ROOT"

# 1. 删除 workspace-design/outputs 超过 60 天的 PSD 文件
log "[1/7] 清理 PSD 源文件（超过 60 天）"
OLD_PSD=$(find workspace-design/outputs -type f -name "*.psd" -mtime +60 2>/dev/null | wc -l | tr -d ' ')
OLD_PSD_SIZE=$(find workspace-design/outputs -type f -name "*.psd" -mtime +60 -exec du -ch {} + 2>/dev/null | tail -1 | awk '{print $1}')
log "发现 $OLD_PSD 个 PSD 文件，约 $OLD_PSD_SIZE"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_PSD" -gt 0 ]]; then
    find workspace-design/outputs -type f -name "*.psd" -mtime +60 -delete 2>/dev/null || true
    log "已删除"
fi

# 2. 删除超过 30 天的测试/开发目录
log "[2/7] 清理测试和开发目录（超过 30 天）"
OLD_TEST_DIRS=$(find workspace-design/outputs -type d \( -name "*-test" -o -name "*-devcheck" -o -name "dreamina-manual-fetch-*" \) -mtime +30 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_TEST_DIRS 个目录"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_TEST_DIRS" -gt 0 ]]; then
    find workspace-design/outputs -type d \( -name "*-test" -o -name "*-devcheck" -o -name "dreamina-manual-fetch-*" \) -mtime +30 -exec rm -rf {} + 2>/dev/null || true
    log "已删除"
fi

# 3. 清理 Dreamina 项目中超过 30 天的中间下载文件
log "[3/7] 清理 Dreamina 中间下载文件（超过 30 天）"
OLD_DOWNLOADS=$(find workspace-design/outputs/dreamina-reference-video/projects/*/runs -type d -name "downloads" -mtime +30 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_DOWNLOADS 个下载目录"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_DOWNLOADS" -gt 0 ]]; then
    find workspace-design/outputs/dreamina-reference-video/projects/*/runs -type d -name "downloads" -mtime +30 -exec rm -rf {} + 2>/dev/null || true
    log "已删除"
fi

# 4. 压缩超过 90 天的完整设计项目
log "[4/7] 压缩设计项目目录（超过 90 天）"
OLD_PROJECTS=$(find workspace-design/outputs -maxdepth 1 -type d -name "project_id=*" -mtime +90 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_PROJECTS 个项目目录"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_PROJECTS" -gt 0 ]]; then
    find workspace-design/outputs -maxdepth 1 -type d -name "project_id=*" -mtime +90 -exec bash -c 'tar -czf "{}.tar.gz" "{}" && rm -rf "{}"' \; 2>/dev/null || true
    log "已压缩"
fi

# 5. 删除 workspace/outputs 超过 90 天的文件
log "[5/7] 清理主工作区输出（超过 90 天）"
OLD_MAIN_OUTPUTS=$(find workspace/outputs -type f -mtime +90 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_MAIN_OUTPUTS 个文件"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_MAIN_OUTPUTS" -gt 0 ]]; then
    find workspace/outputs -type f -mtime +90 -delete 2>/dev/null || true
    log "已删除"
fi

# 6. 删除超过 180 天的会话记录
log "[6/7] 清理超期会话记录（超过 180 天）"
OLD_OLD_SESSIONS=$(find agents/*/sessions -type f \( -name "*.jsonl" -o -name "*.jsonl.gz" \) -mtime +180 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_OLD_SESSIONS 个会话文件"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_OLD_SESSIONS" -gt 0 ]]; then
    find agents/*/sessions -type f \( -name "*.jsonl" -o -name "*.jsonl.gz" \) -mtime +180 -delete 2>/dev/null || true
    log "已删除"
fi

# 7. 删除入站媒体中超过 30 天的文档文件
log "[7/7] 清理入站媒体文档（超过 30 天）"
OLD_DOCS=$(find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.xlsx" \) -mtime +30 2>/dev/null | wc -l | tr -d ' ')
log "发现 $OLD_DOCS 个文档文件"

if [[ "$DRY_RUN" == false ]] && [[ "$OLD_DOCS" -gt 0 ]]; then
    find workspace*/.openclaw-inbound-media media/inbound -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.xlsx" \) -mtime +30 -delete 2>/dev/null || true
    log "已删除"
fi

# 删除超过 90 天的压缩日志
if [[ "$DRY_RUN" == false ]]; then
    find logs -type f -name "*.log.gz" -mtime +90 -delete 2>/dev/null || true
    find cron/runs -type f -mtime +180 -delete 2>/dev/null || true
fi

# 清理空目录
if [[ "$DRY_RUN" == false ]]; then
    find workspace-design/outputs workspace/outputs workspace*/.openclaw-inbound-media media/inbound agents/*/sessions -type d -empty -delete 2>/dev/null || true
fi

log "========== 每月深度清理完成 =========="
log ""
