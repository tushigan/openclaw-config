#!/bin/bash

echo "=== 删除 video 工作区 ==="

echo "1. 删除 workspace-ppt 软链接"
rm /Users/a123/.openclaw/workspace-ppt
echo "✓ 已删除"

echo -e "\n2. 删除 workspace-video 目录"
rm -rf /Users/a123/.openclaw/workspace-video
echo "✓ 已删除"

echo -e "\n✅ video 工作区已完全移除"
