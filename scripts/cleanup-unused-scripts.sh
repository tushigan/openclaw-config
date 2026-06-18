#!/usr/bin/env bash
# 清理长期未使用的临时脚本（基于最后访问时间）

set -euo pipefail

# 参数配置
DAYS_UNUSED=${1:-30}  # 默认30天未访问
DRY_RUN=${DRY_RUN:-false}

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

cd /Users/a123/.openclaw || exit 1

log "====== 开始清理未使用的临时脚本 ======"
log "策略: 清理 ${DAYS_UNUSED} 天内未访问的脚本"
log "模式: $([ "$DRY_RUN" = true ] && echo '预览模式（不实际删除）' || echo '执行模式')"

# 1. 清理 workspace*/outputs/ 目录下长期未使用的脚本（排除 node_modules、venv 等依赖目录）
log "[1/3] 扫描 workspace*/outputs/ 目录"
UNUSED_SCRIPTS=$(find workspace*/outputs -type f \( -name "*.py" -o -name "*.sh" -o -name "*.js" \) -atime +${DAYS_UNUSED} ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/venv/*" ! -path "*/__pycache__/*" 2>/dev/null | wc -l | tr -d ' ')
log "发现 $UNUSED_SCRIPTS 个超过 ${DAYS_UNUSED} 天未访问的脚本"

if [[ "$UNUSED_SCRIPTS" -gt 0 ]]; then
    if [[ "$DRY_RUN" == true ]]; then
        log "预览前10个将被删除的文件："
        find workspace*/outputs -type f \( -name "*.py" -o -name "*.sh" -o -name "*.js" \) -atime +${DAYS_UNUSED} ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/venv/*" ! -path "*/__pycache__/*" 2>/dev/null | head -10
    else
        # 先备份到 trash（可恢复）
        find workspace*/outputs -type f \( -name "*.py" -o -name "*.sh" -o -name "*.js" \) -atime +${DAYS_UNUSED} ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/venv/*" ! -path "*/__pycache__/*" -exec trash {} \; 2>/dev/null || {
            # 如果 trash 命令不存在，使用 delete
            find workspace*/outputs -type f \( -name "*.py" -o -name "*.sh" -o -name "*.js" \) -atime +${DAYS_UNUSED} ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/venv/*" ! -path "*/__pycache__/*" -delete 2>/dev/null || true
        }
        log "已清理 $UNUSED_SCRIPTS 个脚本"
    fi
fi

# 2. 清理 workspace*/ 根目录下以 _temp_ 开头的长期未使用脚本
log "[2/3] 扫描 workspace*/ 根目录临时脚本"
UNUSED_TEMP=$(find workspace* -maxdepth 1 -type f \( -name "_temp_*.py" -o -name "_temp_*.sh" -o -name "_temp_*.js" -o -name "_*.py" -o -name "_*.sh" -o -name "_*.js" \) -atime +${DAYS_UNUSED} 2>/dev/null | wc -l | tr -d ' ')
log "发现 $UNUSED_TEMP 个超过 ${DAYS_UNUSED} 天未访问的临时脚本"

if [[ "$UNUSED_TEMP" -gt 0 ]]; then
    if [[ "$DRY_RUN" == true ]]; then
        log "预览将被删除的文件："
        find workspace* -maxdepth 1 -type f \( -name "_temp_*.py" -o -name "_temp_*.sh" -o -name "_temp_*.js" -o -name "_*.py" -o -name "_*.sh" -o -name "_*.js" \) -atime +${DAYS_UNUSED} 2>/dev/null
    else
        find workspace* -maxdepth 1 -type f \( -name "_temp_*.py" -o -name "_temp_*.sh" -o -name "_temp_*.js" -o -name "_*.py" -o -name "_*.sh" -o -name "_*.js" \) -atime +${DAYS_UNUSED} -exec trash {} \; 2>/dev/null || {
            find workspace* -maxdepth 1 -type f \( -name "_temp_*.py" -o -name "_temp_*.sh" -o -name "_temp_*.js" -o -name "_*.py" -o -name "_*.sh" -o -name "_*.js" \) -atime +${DAYS_UNUSED} -delete 2>/dev/null || true
        }
        log "已清理 $UNUSED_TEMP 个临时脚本"
    fi
fi

# 3. 清理项目根目录下以 _ 开头的长期未使用脚本（排除核心工具脚本）
log "[3/3] 扫描根目录临时脚本"
UNUSED_ROOT=$(find . -maxdepth 1 -type f \( -name "_*.py" -o -name "_*.sh" -o -name "_*.js" \) -atime +${DAYS_UNUSED} 2>/dev/null | wc -l | tr -d ' ')
log "发现 $UNUSED_ROOT 个超过 ${DAYS_UNUSED} 天未访问的根目录脚本"

if [[ "$UNUSED_ROOT" -gt 0 ]]; then
    if [[ "$DRY_RUN" == true ]]; then
        log "预览将被删除的文件："
        find . -maxdepth 1 -type f \( -name "_*.py" -o -name "_*.sh" -o -name "_*.js" \) -atime +${DAYS_UNUSED} 2>/dev/null
    else
        find . -maxdepth 1 -type f \( -name "_*.py" -o -name "_*.sh" -o -name "_*.js" \) -atime +${DAYS_UNUSED} -exec trash {} \; 2>/dev/null || {
            find . -maxdepth 1 -type f \( -name "_*.py" -o -name "_*.sh" -o -name "_*.js" \) -atime +${DAYS_UNUSED} -delete 2>/dev/null || true
        }
        log "已清理 $UNUSED_ROOT 个根目录脚本"
    fi
fi

# 统计总结
TOTAL_CLEANED=$((UNUSED_SCRIPTS + UNUSED_TEMP + UNUSED_ROOT))
log "====== 清理完成 ======"
log "总计清理: $TOTAL_CLEANED 个长期未使用的脚本"
log "磁盘空间已优化"
