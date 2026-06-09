#!/bin/bash

echo "=== 移动 video-expert-analyzer 到 design ==="

echo "1. 复制 main workspace 版本到 design"
cp -r /Users/a123/.openclaw/workspace/skills/video-expert-analyzer /Users/a123/.openclaw/workspace-design/skills/
echo "✓ 已复制到 workspace-design/skills/"

echo -e "\n2. 删除 main workspace 副本"
rm -rf /Users/a123/.openclaw/workspace/skills/video-expert-analyzer
echo "✓ 已删除 main workspace 副本"

echo -e "\n3. 删除 research workspace 副本"
rm -rf /Users/a123/.openclaw/workspace-research/skills/video-expert-analyzer
echo "✓ 已删除 research workspace 副本"

echo -e "\n✅ video-expert-analyzer 已移动到 design workspace"
