#!/bin/bash

echo "测试新安装的 6 个广告 skills 是否被 OpenClaw 识别..."
echo ""

# 检查各个 skill 目录
echo "=== 1. 检查 skill 文件是否存在 ==="
skills=(
  "/Users/a123/.openclaw/skills/kefu-ae:客服AE"
  "/Users/a123/.openclaw/skills/boss:总控BOSS"
  "/Users/a123/.openclaw/workspace-strategy/skills/celue-zj:策略总监"
  "/Users/a123/.openclaw/workspace-strategy/skills/chuangyi-zj:创意总监"
  "/Users/a123/.openclaw/workspace-copywriter/skills/wenan:文案"
  "/Users/a123/.openclaw/workspace-design/skills/sheji:设计"
)

for skill in "${skills[@]}"; do
  path="${skill%%:*}"
  name="${skill##*:}"
  if [ -f "$path/SKILL.md" ]; then
    echo "✅ $name: $path/SKILL.md 存在"
  else
    echo "❌ $name: $path/SKILL.md 不存在"
  fi
done

echo ""
echo "=== 2. 检查 openclaw.json 配置 ==="
echo "main agent skills:"
openclaw config get agents.list --json | jq -r '.[] | select(.id=="main") | .skills[]'

echo ""
echo "strategy agent skills:"
openclaw config get agents.list --json | jq -r '.[] | select(.id=="strategy") | .skills[]'

echo ""
echo "copywriter agent skills:"
openclaw config get agents.list --json | jq -r '.[] | select(.id=="copywriter") | .skills[]'

echo ""
echo "design agent skills:"
openclaw config get agents.list --json | jq -r '.[] | select(.id=="design") | .skills[]'

echo ""
echo "=== 3. 检查 gateway 进程状态 ==="
ps aux | grep -E "openclaw.*gateway" | grep -v grep

echo ""
echo "=== 4. 测试完成 ==="
