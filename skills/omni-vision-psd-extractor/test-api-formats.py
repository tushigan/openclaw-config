#!/usr/bin/env python3
"""
测试 s.lconai.com 支持的 API 格式

测试三种可能的接口：
1. Gemini Native: /v1beta/models/{model}:generateContent
2. OpenAI Images Edit: /v1/images/edits
3. OpenAI Images Generation: /v1/images/generations
"""

import base64
import json
import os
import sys
from pathlib import Path

# 测试配置
API_KEY = "sk-bSPSorO76pfzfqkbHlWHMK97nkXtXzO5h0bOZpxb3NlF52lw"
BASE_URL = "https://s.lconai.com"
MODEL = "gpt-image-2-pro"
TEST_IMAGE = Path(__file__).parent / "test-image.png"
TEST_PROMPT = "将背景变成蓝色"

print("=" * 80)
print("API 格式测试")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"Model: {MODEL}")
print(f"API Key: {API_KEY[:20]}...")
print()

# 创建一个简单的测试图片（如果不存在）
if not TEST_IMAGE.exists():
    from PIL import Image
    img = Image.new('RGB', (512, 512), color='red')
    img.save(TEST_IMAGE)
    print(f"✅ 创建测试图片: {TEST_IMAGE}")

image_bytes = TEST_IMAGE.read_bytes()
image_b64 = base64.b64encode(image_bytes).decode('ascii')

print()
print("─" * 80)
print("测试 1: Gemini Native API")
print("─" * 80)

try:
    import urllib.request

    endpoint = f"{BASE_URL}/v1beta/models/{MODEL}:generateContent"
    print(f"端点: {endpoint}")

    payload = {
        "contents": [{
            "parts": [
                {"text": TEST_PROMPT},
                {"inlineData": {"mimeType": "image/png", "data": image_b64}}
            ]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )

    print("发送请求...")
    with urllib.request.urlopen(request, timeout=30) as response:
        status = response.status
        body = response.read().decode('utf-8')
        print(f"✅ HTTP {status}")
        print(f"响应: {body[:200]}...")

        data = json.loads(body)
        if "candidates" in data:
            print("✅ Gemini Native 格式成功！")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}")
    print(f"错误: {e.read().decode('utf-8', errors='replace')[:500]}")
except Exception as e:
    print(f"❌ 异常: {e}")

print()
print("─" * 80)
print("测试 2: OpenAI Chat Completions (vision)")
print("─" * 80)

try:
    endpoint = f"{BASE_URL}/v1/chat/completions"
    print(f"端点: {endpoint}")

    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": TEST_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                }
            ]
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )

    print("发送请求...")
    with urllib.request.urlopen(request, timeout=30) as response:
        status = response.status
        body = response.read().decode('utf-8')
        print(f"✅ HTTP {status}")
        print(f"响应: {body[:200]}...")

        data = json.loads(body)
        if "choices" in data:
            print("✅ OpenAI Chat 格式成功！")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}")
    print(f"错误: {e.read().decode('utf-8', errors='replace')[:500]}")
except Exception as e:
    print(f"❌ 异常: {e}")

print()
print("=" * 80)
print("测试完成")
print("=" * 80)
print()
print("结论：")
print("- 如果 Gemini Native 成功 → 继续使用当前格式")
print("- 如果 OpenAI Chat 成功 → 需要改用 Chat Completions 格式")
print("- 如果都失败 → 需要联系 API 提供商确认正确格式")
