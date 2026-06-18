#!/bin/bash

echo "=== 处理 multi-search-engine 全局化 ==="

echo "1. 复制 research 版本到全局"
cp -r /Users/a123/.openclaw/workspace-research/skills/multi-search-engine /Users/a123/.openclaw/skills/
echo "✓ 已复制到全局"

echo -e "\n2. 删除 research 本地副本"
rm -rf /Users/a123/.openclaw/workspace-research/skills/multi-search-engine
echo "✓ 已删除 research 副本"

echo -e "\n3. 删除 strategy 本地副本"
rm -rf /Users/a123/.openclaw/workspace-strategy/skills/multi-search-engine
echo "✓ 已删除 strategy 副本"

echo -e "\n✅ multi-search-engine 已全局化"
