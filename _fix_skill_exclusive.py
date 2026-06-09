#!/usr/bin/env python3
import json

config_path = "/Users/a123/.openclaw/openclaw.json"

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

print("=== 修正 skill 独占配置 ===\n")

# 1. 从 defaults 删除应该独占的 skill
defaults_skills = config['agents']['defaults']['skills']
to_remove_from_defaults = ['dreamina-reference-video', 'image-deglaze', 'quote-skill', 'business-project-intake']

for skill in to_remove_from_defaults:
    if skill in defaults_skills:
        defaults_skills.remove(skill)
        print(f"✓ 从 defaults 删除: {skill}")

print(f"\n更新后 defaults.skills 数量: {len(defaults_skills)}")

# 2. 更新 design/design-shared 的独占列表（添加 dreamina-reference-video 和 image-deglaze）
design_exclusive = [
    'RunningHub',
    'brand-poster-creator',
    'brand-poster-distiller',
    'xiangqingye-desigen',
    'dreamina-cli',
    'dreamina-reference-video',  # 新增
    'image-deglaze',  # 新增
    'psd-layered-rebuilder',
    'product-photography-workflow',
    'video-expert-analyzer',
    'video-frames',
    'session-debug-export'
]

for agent in config['agents']['list']:
    if agent['id'] in ['design', 'design-shared']:
        agent['skills'] = design_exclusive.copy()
        print(f"✓ 更新 {agent['id']} skills ({len(design_exclusive)} 个)")

# 3. 为 business/business-shared 设置独占列表
business_exclusive = ['quote-skill', 'business-project-intake']

for agent in config['agents']['list']:
    if agent['id'] in ['business', 'business-shared']:
        agent['skills'] = business_exclusive.copy()
        print(f"✓ 设置 {agent['id']} skills ({len(business_exclusive)} 个)")

# 保存配置
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"\n✅ openclaw.json 配置修正完成")
print(f"- defaults.skills: {len(defaults_skills)} 个")
print(f"- design/design-shared: {len(design_exclusive)} 个独占")
print(f"- business/business-shared: {len(business_exclusive)} 个独占")
