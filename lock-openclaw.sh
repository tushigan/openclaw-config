#!/bin/bash
# lock-openclaw.sh — 一键锁定训虾文件权限（只读保护）
# 用法: bash ~/.openclaw/lock-openclaw.sh

echo "🔒 正在锁定训虾文件..."

# 人格文件 → 只读
for ws in workspace workspace-strategy workspace-design workspace-research workspace-video workspace-meeting workspace-copywriter; do
  for f in AGENTS.md SOUL.md IDENTITY.md USER.md TOOLS.md; do
    filepath="$HOME/.openclaw/$ws/$f"
    [ -f "$filepath" ] && chmod 444 "$filepath"
  done
done
echo "  ✓ 人格文件已锁定"

# Skills 目录 → 只读
chmod -R 444 "$HOME/.openclaw/skills/" 2>/dev/null
find "$HOME/.openclaw/skills/" -type d -exec chmod 555 {} \; 2>/dev/null
echo "  ✓ Skills 目录已锁定"

# 核心配置 → 只读
chmod 444 "$HOME/.openclaw/openclaw.json" 2>/dev/null
chmod 444 "$HOME/.openclaw/exec-approvals.json" 2>/dev/null
chmod 444 "$HOME/.openclaw/cron/jobs.json" 2>/dev/null
echo "  ✓ 核心配置已锁定"

# Credentials → 仅 owner 读写
chmod 600 "$HOME/.openclaw/credentials/"*.json 2>/dev/null
echo "  ✓ Credentials 权限已设置"

echo "🔒 所有训虾文件已锁定！普通用户和 AI 都无法修改。"
