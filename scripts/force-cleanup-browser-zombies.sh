#!/bin/bash
# 强制清理僵尸浏览器进程
# 用于清理 OpenClaw 无法正常关闭的浏览器实例

set -e

echo "🧹 强制清理僵尸浏览器进程..."
echo ""

# 统计清理前的进程数
BEFORE=$(ps aux | grep -i chrome | grep "research-login" | grep -v grep | wc -l | tr -d ' ')
echo "清理前 Chrome 进程数: $BEFORE"

if [ "$BEFORE" -eq 0 ]; then
    echo "✅ 没有发现僵尸浏览器进程"
    exit 0
fi

echo ""
echo "正在强制终止所有 research-login 浏览器进程..."

# 使用 pkill 强制终止
pkill -f "research-login.*user-data.*remote-debugging-port" 2>&1 || true

echo "等待进程完全退出..."
sleep 3

# 统计清理后的进程数
AFTER=$(ps aux | grep -i chrome | grep "research-login" | grep -v grep | wc -l | tr -d ' ')
echo ""
echo "清理后 Chrome 进程数: $AFTER"
echo "已清理: $((BEFORE - AFTER)) 个进程"

if [ "$AFTER" -gt 0 ]; then
    echo ""
    echo "⚠️  警告：仍有 $AFTER 个僵尸进程未清理"
    echo "残留进程列表："
    ps aux | grep -i chrome | grep "research-login" | grep -v grep | awk '{print "  - PID " $2 ": " $11 " " $12}' | head -5
    echo ""
    echo "💡 提示：可能需要手动 kill 这些进程：sudo kill -9 <PID>"
    exit 1
else
    echo ""
    echo "✅ 所有僵尸浏览器进程已成功清理"
    exit 0
fi
