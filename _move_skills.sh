#!/bin/bash
cd /Users/a123/.openclaw

echo "=== 1. 处理 dreamina-cli ==="
if [ -d "skills/dreamina-cli" ]; then
  echo "删除全局旧版本 dreamina-cli"
  rm -rf skills/dreamina-cli
  echo "✓ 已删除"
else
  echo "全局版本不存在"
fi

echo -e "\n=== 2. 处理 dreamina-reference-video ==="
if [ -L "workspace-design/skills/dreamina-reference-video" ]; then
  echo "删除 workspace-design 中的软链接"
  rm workspace-design/skills/dreamina-reference-video
  echo "✓ 已删除软链接"
fi

if [ -d "skills/dreamina-reference-video" ]; then
  echo "移动全局版本到 workspace-design"
  mv skills/dreamina-reference-video workspace-design/skills/
  echo "✓ 已移动"
fi

echo -e "\n=== 3. 移动其他设计类 skill ==="
for skill in brand-poster-creator xiangqingye-desigen image-deglaze; do
  if [ -d "skills/$skill" ]; then
    echo "移动 $skill 到 workspace-design/skills/"
    mv "skills/$skill" workspace-design/skills/
    echo "✓ $skill 已移动"
  else
    echo "⚠️  skills/$skill 不存在"
  fi
done

echo -e "\n=== 4. 创建 workspace-business/skills 目录 ==="
mkdir -p workspace-business/skills

echo -e "\n=== 5. 移动业务类 skill ==="
for skill in quote-skill business-project-intake; do
  if [ -d "skills/$skill" ]; then
    echo "移动 $skill 到 workspace-business/skills/"
    mv "skills/$skill" workspace-business/skills/
    echo "✓ $skill 已移动"
  else
    echo "⚠️  skills/$skill 不存在"
  fi
done

echo -e "\n✅ 所有 skill 文件移动完成"
