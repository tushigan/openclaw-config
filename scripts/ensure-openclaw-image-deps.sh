#!/bin/bash
# ensure-openclaw-image-deps.sh - 校验并补齐 OpenClaw 图片处理依赖

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }

if ! command -v npm >/dev/null 2>&1; then
    error "未找到 npm，无法检查 OpenClaw 运行依赖"
    exit 1
fi

NPM_GLOBAL_ROOT="$(npm root -g 2>/dev/null || true)"
OPENCLAW_DIR="${NPM_GLOBAL_ROOT}/openclaw"

if [ -z "${NPM_GLOBAL_ROOT}" ] || [ ! -d "${OPENCLAW_DIR}" ]; then
    error "未找到全局 OpenClaw 安装目录: ${OPENCLAW_DIR}"
    exit 1
fi

info "检查 OpenClaw 图片处理依赖..."
info "OpenClaw 目录: ${OPENCLAW_DIR}"

if (
    cd "${OPENCLAW_DIR}" &&
    node -e "import('sharp').then(() => process.exit(0)).catch(() => process.exit(1))"
); then
    ok "sharp 已可用，图片处理依赖正常"
    exit 0
fi

warn "sharp 缺失，开始最小化补装..."
(
    cd "${OPENCLAW_DIR}" &&
    npm install sharp --no-save
)

if (
    cd "${OPENCLAW_DIR}" &&
    node -e "import('sharp').then(() => process.exit(0)).catch(() => process.exit(1))"
); then
    ok "sharp 安装完成，图片处理依赖已恢复"
    exit 0
fi

error "sharp 安装后仍不可用，请手动检查 ${OPENCLAW_DIR}"
exit 1
