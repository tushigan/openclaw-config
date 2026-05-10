#!/bin/bash
# cleanup-ghost-group-sessions.sh
# 清理飞书幽灵群会话（ou_ 开头的用户 ID 被错误创建为 group 会话）
# 由 crontab 定期执行

SESSIONS_FILE="/Users/a123/.openclaw/agents/main/sessions/sessions.json"
LOG_FILE="/Users/a123/.openclaw/logs/ghost-cleanup.log"

if [ ! -f "$SESSIONS_FILE" ]; then
    echo "$(date -Iseconds) sessions.json not found" >> "$LOG_FILE"
    exit 0
fi

RESULT=$(python3 -c "
import json, os

sessions_file = '$SESSIONS_FILE'
with open(sessions_file, 'r') as f:
    data = json.load(f)

ghost_keys = [k for k in data if 'feishu:group:ou_' in k]
if not ghost_keys:
    print('no_ghosts')
    exit()

ghost_files = []
for k in ghost_keys:
    sf = data[k].get('sessionFile', '')
    if sf:
        ghost_files.append(sf)
    del data[k]

with open(sessions_file, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

for f in ghost_files:
    if os.path.exists(f):
        os.remove(f)

print(f'removed:{len(ghost_keys)}')
" 2>&1)

echo "$(date -Iseconds) $RESULT" >> "$LOG_FILE"
