#!/usr/bin/env python3
import json

config_path = "/Users/a123/.openclaw/openclaw.json"

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

print("=== 开始删除 video agent 及清理关联配置 ===\n")

# 1. 从 agents.list 删除 video 和 video-shared
original_count = len(config['agents']['list'])
config['agents']['list'] = [
    agent for agent in config['agents']['list']
    if agent['id'] not in ['video', 'video-shared']
]
removed_count = original_count - len(config['agents']['list'])
print(f"✓ 从 agents.list 删除 {removed_count} 个 agent (video, video-shared)")

# 2. 从 agents.defaults.subagents.allowAgents 删除 video
if 'subagents' in config['agents']['defaults'] and 'allowAgents' in config['agents']['defaults']['subagents']:
    defaults_allow = config['agents']['defaults']['subagents']['allowAgents']
    if 'video' in defaults_allow:
        defaults_allow.remove('video')
        print(f"✓ 从 agents.defaults.subagents.allowAgents 删除 video")
        print(f"  更新后: {defaults_allow}")

# 3. 从各 agent 的 subagents.allowAgents 删除 video
updated_agents = []
for agent in config['agents']['list']:
    if 'subagents' in agent and 'allowAgents' in agent['subagents']:
        allow_list = agent['subagents']['allowAgents']
        if 'video' in allow_list:
            allow_list.remove('video')
            updated_agents.append(agent['id'])

if updated_agents:
    print(f"\n✓ 从以下 agent 的 subagents.allowAgents 删除 video:")
    for agent_id in updated_agents:
        print(f"  - {agent_id}")

# 保存配置
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"\n✅ openclaw.json 配置清理完成")
print(f"删除 agent 数量: {removed_count}")
print(f"更新 subagents 配置的 agent 数量: {len(updated_agents) + 1}")  # +1 for defaults
