#!/usr/bin/env python3
"""
发送审批消息到飞书
绕过 Agent 的回复机制，直接使用飞书 API 发送普通消息
"""
import os
import sys
import json
import requests
from pathlib import Path

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

def get_tenant_access_token():
    """获取飞书 tenant access token"""
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        raise Exception("Missing FEISHU_APP_ID or FEISHU_APP_SECRET")

    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    response = requests.post(
        url,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10
    )
    result = response.json()

    if result.get("code") != 0:
        raise Exception(f"Failed to get token: {result.get('msg', 'Unknown error')}")

    return result["tenant_access_token"]

def get_current_chat_id():
    """
    从环境变量或 OpenClaw 状态文件获取当前群聊 ID

    优先级：
    1. 环境变量 FEISHU_CHAT_ID
    2. 从 OpenClaw 会话状态读取
    3. 默认值（从测试记录中获取）
    """
    # 1. 环境变量
    chat_id = os.getenv("FEISHU_CHAT_ID")
    if chat_id:
        return chat_id

    # 2. 从 OpenClaw 状态文件读取（如果存在）
    state_dir = Path(os.getenv("OPENCLAW_STATE_DIR", Path.home() / ".openclaw" / "state"))
    session_file = state_dir / "current_session.json"
    if session_file.exists():
        try:
            with open(session_file) as f:
                session_data = json.load(f)
                chat_id = session_data.get("feishu_chat_id")
                if chat_id:
                    return chat_id
        except Exception:
            pass

    # 3. 默认值（当前测试使用的群聊 ID）
    return "oc_deb2956a37fa31823df419ab084a073f"

def send_text_message(chat_id: str, content: str, msg_type: str = "text") -> dict:
    """
    发送文本消息到飞书群聊

    Args:
        chat_id: 飞书群聊 ID (格式: oc_xxx)
        content: 消息内容（支持 Markdown 和飞书艾特标签）
        msg_type: 消息类型，默认 "text"

    Returns:
        dict: 发送结果
    """
    token = get_tenant_access_token()

    url = f"{FEISHU_API_BASE}/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 构造消息体
    payload = {
        "receive_id": chat_id,
        "receive_id_type": "chat_id",
        "msg_type": msg_type,
        "content": json.dumps({
            "text": content
        })
    }

    print(f"[发送消息] chat_id={chat_id}", file=sys.stderr)
    print(f"[消息内容] {content[:100]}...", file=sys.stderr)

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    result = response.json()

    if result.get("code") != 0:
        error_msg = f"发送失败: {result.get('msg', 'Unknown error')}"
        print(f"[错误] {error_msg}", file=sys.stderr)
        return {"success": False, "error": error_msg, "result": result}

    message_id = result.get("data", {}).get("message_id")
    print(f"[成功] message_id={message_id}", file=sys.stderr)

    return {
        "success": True,
        "message_id": message_id,
        "result": result
    }

def main():
    import argparse

    parser = argparse.ArgumentParser(description="发送审批消息到飞书")
    parser.add_argument("--chat-id", help="飞书群聊 ID (oc_xxx)，如果不提供则自动获取")
    parser.add_argument("--content", required=True, help="消息内容（支持 Markdown 和艾特标签）")
    parser.add_argument("--msg-type", default="text", help="消息类型（默认: text）")

    args = parser.parse_args()

    # 如果没有提供 chat_id，尝试自动获取
    chat_id = args.chat_id or get_current_chat_id()

    result = send_text_message(chat_id, args.content, args.msg_type)

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()
