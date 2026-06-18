#!/bin/bash

echo "=== 处理 multi-search-engine 去重 ==="

if [ -f "/Users/a123/.openclaw/skills/multi-search-engine/test-prompts.json" ]; then
  echo "复制 test-prompts.json 到 research 版本"
  cp /Users/a123/.openclaw/skills/multi-search-engine/test-prompts.json /Users/a123/.openclaw/workspace-research/skills/multi-search-engine/
  echo "✓ 已复制"
else
  echo "⚠️  test-prompts.json 不存在"
fi

echo "删除全局版本 multi-search-engine"
rm -rf /Users/a123/.openclaw/skills/multi-search-engine
echo "✓ 已删除"

echo -e "\n✅ multi-search-engine 去重完成，保留 research 版本"
