#!/bin/bash
# Quick export script for current session
# Usage: ./quick_export.sh "issue-description"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw}"

# Default issue description
ISSUE="${1:-debug-session}"

echo "🔍 Finding current session..."

# Try to find the most recent session
SESSION_KEY=$(openclaw sessions --limit 1 --json 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['sessions'][0]['key'] if data.get('sessions') else '')" 2>/dev/null)

if [ -z "$SESSION_KEY" ]; then
    echo "❌ No recent session found. Listing all sessions:"
    openclaw sessions --limit 5
    echo ""
    echo "Please specify session key manually:"
    echo "  python3 \"$SCRIPT_DIR/export_chat_report.py\" --session-key \"YOUR_SESSION_KEY\" --issue \"$ISSUE\""
    exit 1
fi

echo "✅ Found session: $SESSION_KEY"
echo "📝 Issue: $ISSUE"
echo "🚀 Exporting..."

python3 "$SCRIPT_DIR/export_chat_report.py" \
    --workspace "$WORKSPACE" \
    --session-key "$SESSION_KEY" \
    --issue "$ISSUE" \
    --agent-name "小爪" \
    2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✨ Export completed!"
    echo "📂 Check ~/Downloads for the exported file"
else
    echo ""
    echo "❌ Export failed. Please check the error message above."
    exit 1
fi
