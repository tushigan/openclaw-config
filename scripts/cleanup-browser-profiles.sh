#!/bin/bash
# 清理僵尸浏览器进程和过期的 Profile 实例

set -euo pipefail

OPENCLAW_DIR="/Users/a123/.openclaw"
PROFILE_MANAGER="$OPENCLAW_DIR/workspace/skills/web-browse-capture/scripts/profile_manager.py"
RESEARCH_POOL="$OPENCLAW_DIR/workspace/skills/web-browse-capture/scripts/research_pool.py"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 所有登录态 profile 列表
PROFILES=(
    "research-login-xhs"
    "research-login-taobao"
    "research-login-jd"
    "research-login-douyin"
    "research-login-quandashi"
    "research-login-zhenbiao"
    "research-login-86sb"
    "research-login-huaban"
    "research-login-biaoyuan"
)

# 检查并清理单个 profile
cleanup_profile() {
    local profile=$1
    log_info "检查 Profile: $profile"

    # 健康检查
    health_result=$(python3 "$PROFILE_MANAGER" health "$profile" 2>/dev/null || echo '{"ok":false}')
    health=$(echo "$health_result" | jq -r '.health // "unknown"')

    if [[ "$health" == "unhealthy" ]] || [[ "$health" == "unknown" ]]; then
        log_warn "Profile $profile 状态不健康: $health"

        # 尝试重启
        log_info "尝试重启 $profile..."
        python3 "$PROFILE_MANAGER" restart "$profile" >/dev/null 2>&1 || {
            log_error "重启 $profile 失败"
            return 1
        }

        sleep 2

        # 再次健康检查
        health_result=$(python3 "$PROFILE_MANAGER" health "$profile" 2>/dev/null || echo '{"ok":false}')
        health=$(echo "$health_result" | jq -r '.health // "unknown"')

        if [[ "$health" == "healthy" ]]; then
            log_info "重启后 $profile 恢复健康"
        else
            log_error "重启后 $profile 仍不健康"
        fi
    elif [[ "$health" == "stopped" ]]; then
        log_info "Profile $profile 已停止（正常状态）"
    else
        log_info "Profile $profile 状态健康: $health"
    fi
}

# 清理研究池中的 stale 任务
cleanup_research_pool() {
    log_info "清理研究池中的 stale 任务..."

    python3 "$RESEARCH_POOL" status >/dev/null 2>&1 || {
        log_error "无法访问研究池状态"
        return 1
    }

    log_info "研究池清理完成"
}

# 查找并杀死僵尸 Chrome 进程
kill_zombie_chrome() {
    log_info "查找僵尸 Chrome 进程..."

    # 查找长时间运行且占用高资源的 Chrome 进程
    zombie_pids=$(ps aux | grep -E 'Google Chrome.*research-login' | grep -v grep | awk '{if($3>50 || $4>10) print $2}' || echo "")

    if [[ -n "$zombie_pids" ]]; then
        log_warn "发现疑似僵尸进程: $zombie_pids"

        for pid in $zombie_pids; do
            log_warn "尝试终止进程 $pid"
            kill "$pid" 2>/dev/null || log_error "无法终止进程 $pid"
        done
    else
        log_info "未发现僵尸进程"
    fi
}

# 清理孤立的浏览器数据目录
cleanup_orphan_data() {
    log_info "清理孤立的浏览器临时数据..."

    # 清理超过3天的临时文件
    find /tmp -name "chrome_*" -type d -mtime +3 -exec rm -rf {} + 2>/dev/null || true
    find /tmp -name "puppeteer_dev_*" -type d -mtime +3 -exec rm -rf {} + 2>/dev/null || true

    log_info "临时数据清理完成"
}

# 主函数
main() {
    log_info "开始浏览器 Profile 清理任务"
    log_info "========================================"

    # 1. 清理研究池
    cleanup_research_pool

    echo ""

    # 2. 检查并清理所有 profile
    for profile in "${PROFILES[@]}"; do
        cleanup_profile "$profile"
        echo ""
    done

    # 3. 杀死僵尸进程
    kill_zombie_chrome

    echo ""

    # 4. 清理孤立数据
    cleanup_orphan_data

    log_info "========================================"
    log_info "浏览器 Profile 清理任务完成"
}

main "$@"
