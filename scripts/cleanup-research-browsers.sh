#!/bin/bash
# 清理所有 research-login 浏览器实例
# 用途：定期清理或任务完成后清理僵尸浏览器进程

set -e

PROFILES=(
    "research-login-xhs"
    "research-login-taobao"
    "research-login-jd"
    "research-login-douyin"
    "research-login-quandashi"
    "research-login-zhenbiao"
    "research-login-86sb"
    "research-login-huaban"
    "research-login-biaoyuan"
)

echo "🧹 开始清理 research-login 浏览器实例..."
echo ""

# 统计清理前的进程数
BEFORE=$(ps aux | grep -i chrome | grep "research-login" | grep -v grep | wc -l | tr -d ' ')
echo "清理前 Chrome 进程数: $BEFORE"
echo ""

# 逐个停止浏览器实例
for profile in "${PROFILES[@]}"; do
    echo "正在停止 $profile..."
    openclaw browser --browser-profile "$profile" stop 2>&1 | grep -v "^🦞" || true
done

echo ""
echo "等待浏览器进程完全退出..."
sleep 3

# 统计清理后的进程数
AFTER=$(ps aux | grep -i chrome | grep "research-login" | grep -v grep | wc -l | tr -d ' ')
echo ""
echo "清理后 Chrome 进程数: $AFTER"
echo "已清理: $((BEFORE - AFTER)) 个进程"

if [ "$AFTER" -gt 0 ]; then
    echo ""
    echo "⚠️  警告：仍有 $AFTER 个浏览器进程未关闭"
    echo "残留进程列表："
    ps aux | grep -i chrome | grep "research-login" | grep -v grep | awk '{print "  - PID " $2 ": " $11}' | head -5
else
    echo ""
    echo "✅ 所有浏览器实例已成功关闭"
fi
