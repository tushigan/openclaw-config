#!/bin/bash
# Quick export script for current session
# Usage: ./quick_export.sh "issue-description"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw}"

# Default issue description
ISSUE="${1:-debug-session}"

echo "📝 Issue: $ISSUE"
echo "🚀 Exporting..."

python3 "$SCRIPT_DIR/export_chat_report.py" \
    --workspace "$WORKSPACE" \
    --session-key current \
    --issue "$ISSUE" \
    --agent-name "小爪" \
    2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✨ Export completed!"
    echo "📂 Check ~/Downloads/openclaw 问题汇总 for the exported file"
else
    echo ""
    echo "❌ Export failed. Please check the error message above."
    exit 1
fi
