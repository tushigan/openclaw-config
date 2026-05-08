#!/bin/bash
# unlock-openclaw.sh — 一键解锁训虾文件权限（admin 修改时使用）
# 用法: bash ~/.openclaw/unlock-openclaw.sh
# 修改完成后请立即运行 lock-openclaw.sh 重新锁定

echo "🔓 正在解锁训虾文件..."

# 人格文件 → 可写
for ws in workspace workspace-strategy workspace-design workspace-research workspace-video workspace-meeting workspace-copywriter; do
  for f in AGENTS.md SOUL.md IDENTITY.md USER.md TOOLS.md; do
    filepath="$HOME/.openclaw/$ws/$f"
    [ -f "$filepath" ] && chmod 644 "$filepath"
  done
done
echo "  ✓ 人格文件已解锁"

# Skills 目录 → 可写
chmod -R 644 "$HOME/.openclaw/skills/" 2>/dev/null
find "$HOME/.openclaw/skills/" -type d -exec chmod 755 {} \; 2>/dev/null
echo "  ✓ Skills 目录已解锁"

# 核心配置 → 可写
chmod 644 "$HOME/.openclaw/openclaw.json" 2>/dev/null
chmod 644 "$HOME/.openclaw/exec-approvals.json" 2>/dev/null
chmod 644 "$HOME/.openclaw/cron/jobs.json" 2>/dev/null
echo "  ✓ 核心配置已解锁"

# Credentials → owner 读写
chmod 600 "$HOME/.openclaw/credentials/"*.json 2>/dev/null
echo "  ✓ Credentials 权限已设置"

echo ""
echo "⚠️  训虾文件已解锁！修改完成后请立即重新锁定："
echo "   bash ~/.openclaw/lock-openclaw.sh"
