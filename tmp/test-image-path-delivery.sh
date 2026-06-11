#!/bin/bash
# 测试用 path 参数投送图片到话题

# 使用刚才生成的猫狗图片
IMAGE_PATH="/Users/a123/.openclaw/workspace/feishu-deliver/gpt-image2-gen_20260611_161831/cute_10_cats_1_dog.png"

# 话题信息（从最新的 session 中获取）
TARGET="chat:oc_deb2956a37fa31823df419ab084a073f"
THREAD_ID="omt_194fe606458c1b8d"

echo "测试图片投送到话题..."
echo "图片路径: $IMAGE_PATH"
echo "目标群聊: $TARGET"
echo "话题 ID: $THREAD_ID"
echo ""

# 使用 openclaw 的 message 工具（通过 main agent 调用）
# 构造一个测试消息
cat > /Users/a123/.openclaw/tmp/test-message-payload.json << PAYLOAD
{
  "tool": "message",
  "arguments": {
    "channel": "feishu",
    "accountId": "design",
    "action": "send",
    "target": "$TARGET",
    "threadId": "$THREAD_ID",
    "path": "$IMAGE_PATH",
    "caption": "【测试】用 path 参数投送图片（猫狗图）"
  }
}
PAYLOAD

cat /Users/a123/.openclaw/tmp/test-message-payload.json
echo ""
echo "⚠️  注意：需要在 design agent 的 session 中手动调用 message 工具来测试"
echo "或者我可以直接修改 AGENTS.md，让图片投送使用 path 参数"
