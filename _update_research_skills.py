#!/usr/bin/env python3
import json

config_path = "/Users/a123/.openclaw/openclaw.json"

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 从全局 defaults 删除 research-analyst 和 internal-interview-research
defaults_skills = config['agents']['defaults']['skills']
defaults_skills.remove('research-analyst')
defaults_skills.remove('internal-interview-research')

# 为 research 和 research-shared 添加独占 skill
research_exclusive = ['research-analyst']

for agent in config['agents']['list']:
    if agent['id'] in ['research', 'research-shared']:
        agent['skills'] = research_exclusive.copy()

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 研究/分析类 skill 配置完成")
print(f"全局默认: {len(defaults_skills)} 个")
print(f"research 独占: {len(research_exclusive)} 个")
