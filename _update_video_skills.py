#!/usr/bin/env python3
import json

config_path = "/Users/a123/.openclaw/openclaw.json"

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 1. 从全局 defaults 删除 nanobanana-ppt
defaults_skills = config['agents']['defaults']['skills']
if 'nanobanana-ppt' in defaults_skills:
    defaults_skills.remove('nanobanana-ppt')

# 2. 更新 design/design-shared 的独占列表
# 原有: RunningHub, brand-poster-creator, brand-poster-distiller, xiangqingye-desigen,
#       dreamina-cli, psd-layered-rebuilder, product-photography-workflow
# 新增: video-expert-analyzer, video-frames
design_exclusive = [
    'RunningHub',
    'brand-poster-creator',
    'brand-poster-distiller',
    'xiangqingye-desigen',
    'dreamina-cli',
    'psd-layered-rebuilder',
    'product-photography-workflow',
    'video-expert-analyzer',
    'video-frames'
]

for agent in config['agents']['list']:
    if agent['id'] in ['design', 'design-shared']:
        agent['skills'] = design_exclusive.copy()
    # 3. 删除 video/video-shared 的 skills 配置（准备废弃）
    elif agent['id'] in ['video', 'video-shared']:
        if 'skills' in agent:
            del agent['skills']

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 视频/PPT 类 skill 配置完成")
print(f"全局默认: {len(defaults_skills)} 个")
print(f"design 独占: {len(design_exclusive)} 个")
print("已删除: nanobanana-ppt")
print("video agent skills 配置已清空（准备废弃）")
