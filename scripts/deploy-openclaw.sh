#!/bin/bash
# deploy-openclaw.sh - OpenClaw 配置部署脚本
#
# 用法:
#   ./scripts/deploy-openclaw.sh <github-repo-url> [target-dir]
#
# 示例:
#   ./scripts/deploy-openclaw.sh https://github.com/user/openclaw-config.git
#   ./scripts/deploy-openclaw.sh https://github.com/user/openclaw-config.git /home/user/.openclaw
#
# 功能:
#   1. 克隆配置仓库到目标目录
#   2. 替换硬编码路径（适配新机器用户名）
#   3. 从脱敏模板恢复配置文件（需手动填写 API keys）
#   4. 验证部署结果

set -e

GITHUB_REPO="${1:?用法: $0 <github-repo-url> [target-dir]}"
TARGET_DIR="${2:-$HOME/.openclaw}"
CURRENT_USER="a123"
NEW_USER=$(basename "$HOME")

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }

echo ""
echo "========================================="
echo "  OpenClaw 配置部署"
echo "========================================="
echo ""

# ---- 1. 检查目标目录 ----
info "目标目录: $TARGET_DIR"

if [ -d "$TARGET_DIR/.git" ]; then
    warn "目标目录已存在 git 仓库"
    read -p "是否删除并重新克隆? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        rm -rf "$TARGET_DIR"
    else
        error "部署中止"
        exit 1
    fi
elif [ -d "$TARGET_DIR" ] && [ "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
    warn "目标目录非空: $TARGET_DIR"
    read -p "是否继续? (y/N): " confirm
    [[ $confirm =~ ^[Yy]$ ]] || { error "部署中止"; exit 1; }
fi

# ---- 2. 安装 OpenClaw ----
if ! command -v openclaw &>/dev/null; then
    info "安装 OpenClaw..."
    npm install -g openclaw || { error "OpenClaw 安装失败"; exit 1; }
    ok "OpenClaw 安装完成"
else
    ok "OpenClaw 已安装: $(openclaw --version 2>/dev/null || echo 'unknown')"
fi

# ---- 3. 克隆配置仓库 ----
info "克隆配置仓库..."
if [ -d "$TARGET_DIR" ]; then
    git clone "$GITHUB_REPO" "$TARGET_DIR/openclaw-config-tmp" || { error "克隆失败"; exit 1; }
    # 合并到目标目录
    cp -r "$TARGET_DIR/openclaw-config-tmp/"* "$TARGET_DIR/" 2>/dev/null || true
    cp -r "$TARGET_DIR/openclaw-config-tmp/".[!.]* "$TARGET_DIR/" 2>/dev/null || true
    rm -rf "$TARGET_DIR/openclaw-config-tmp"
else
    git clone "$GITHUB_REPO" "$TARGET_DIR" || { error "克隆失败"; exit 1; }
fi
ok "配置仓库克隆完成"

cd "$TARGET_DIR"

# ---- 4. 替换路径 ----
if [ "$CURRENT_USER" != "$NEW_USER" ]; then
    info "替换路径: /Users/$CURRENT_USER → /Users/$NEW_USER"
    find . -type f \( -name "*.json" -o -name "*.json.template" -o -name "*.sh" -o -name "*.md" \) \
        ! -path "./.git/*" \
        -exec sed -i '' "s|/Users/$CURRENT_USER/.openclaw|/Users/$NEW_USER/.openclaw|g" {} \;
    ok "路径替换完成"
else
    info "用户名相同 ($NEW_USER)，跳过路径替换"
fi

# ---- 5. 从模板恢复敏感配置 ----
info "从脱敏模板恢复配置文件..."

restored=0
skipped=0

for template in agents/*/agent/models.json.template agents/*/agent/auth-profiles.json.template openclaw.json.template; do
    if [ -f "$template" ]; then
        target="${template%.template}"
        if [ ! -f "$target" ]; then
            cp "$template" "$target"
            restored=$((restored + 1))
            echo "  已复制: $template → $target"
        else
            skipped=$((skipped + 1))
            echo "  已存在: $target (跳过)"
        fi
    fi
done

if [ $restored -gt 0 ]; then
    echo ""
    warn "============================================="
    warn "  需要手动配置 API Keys！"
    warn "============================================="
    echo ""
    echo "已从模板创建以下配置文件，需要填写真实 API keys："
    echo ""
    echo "  1. openclaw.json"
    echo "     - 各 provider 的 apiKey 字段"
    echo "     - 飞书 appSecret 字段"
    echo ""
    echo "  2. agents/*/agent/models.json"
    echo "     - 各 provider 的 apiKey 字段"
    echo ""
    echo "  3. agents/*/agent/auth-profiles.json"
    echo "     - OAuth access/refresh tokens"
    echo ""
    echo "模板中使用以下占位符标记需要替换的位置："
    echo "  {{API_KEY_xxx}}    → 真实 API Key"
    echo "  {{APP_SECRET}}     → 飞书 App Secret"
    echo "  {{OAUTH_ACCESS}}   → OAuth access token"
    echo "  {{OAUTH_REFRESH}}  → OAuth refresh token"
    echo "  {{OAUTH_EXPIRES}}  → OAuth 过期时间戳"
    echo ""
    echo "搜索占位符："
    echo "  grep -r '{{' $TARGET_DIR/agents/ $TARGET_DIR/openclaw.json 2>/dev/null"
    echo ""
fi

# ---- 6. 处理主 workspace ----
echo ""
info "主 workspace 说明："
echo "  主 workspace (workspace/) 有独立的 git 仓库。"
echo "  如果需要恢复主 workspace 配置："
echo "  1. 将 workspace 仓库克隆到 $TARGET_DIR/workspace/"
echo "  2. 或从备份手动复制"
echo ""

# ---- 7. 创建必要目录 ----
info "创建运行时目录..."
mkdir -p memory logs flows identity feishu tasks
mkdir -p agents/*/sessions 2>/dev/null || true
mkdir -p workspace/images workspace/outputs workspace/feishu-deliver 2>/dev/null || true
ok "运行时目录创建完成"

# ---- 8. 验证 ----
echo ""
info "验证部署..."

errors=0
if [ ! -f "openclaw.json" ]; then
    error "缺少 openclaw.json"
    errors=$((errors + 1))
fi

if [ ! -f ".gitignore" ]; then
    error "缺少 .gitignore"
    errors=$((errors + 1))
fi

# 检查是否还有未替换的占位符
if grep -q '{{API_KEY' openclaw.json 2>/dev/null; then
    warn "openclaw.json 中仍有占位符，需要填写 API keys"
    errors=$((errors + 1))
fi

if [ $errors -eq 0 ]; then
    ok "基础验证通过"
else
    warn "有 $errors 个问题需要处理"
fi

# ---- 9. 完成 ----
echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "下一步："
echo "  1. 配置 API keys（见上方说明）"
echo "  2. 运行健康检查: openclaw doctor"
echo "  3. 启动网关: openclaw gateway --port 18789 --verbose"
echo ""
