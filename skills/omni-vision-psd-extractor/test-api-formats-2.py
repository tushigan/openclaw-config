#!/usr/bin/env python3
"""
测试 OpenAI 图像生成接口
"""

import base64
import json
import os
from pathlib import Path
import urllib.request

API_KEY = "sk-bSPSorO76pfzfqkbHlWHMK97nkXtXzO5h0bOZpxb3NlF52lw"
BASE_URL = "https://s.lconai.com"
MODEL = "gpt-image-2-pro"
TEST_IMAGE = Path(__file__).parent / "test-image.png"
TEST_PROMPT = "将背景变成蓝色，保持其他部分不变"

print("=" * 80)
print("测试 3: 带图像输入的 Gemini Native (responseModalities)")
print("=" * 80)

image_bytes = TEST_IMAGE.read_bytes()
image_b64 = base64.b64encode(image_bytes).decode('ascii')

# 尝试 responseModalities=IMAGE
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
try:
    with urllib.request.urlopen(request, timeout=120) as response:
        status = response.status
        body = response.read().decode('utf-8')
        print(f"✅ HTTP {status}")

        data = json.loads(body)
        print("响应结构:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500])

except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}")
    error_body = e.read().decode('utf-8', errors='replace')
    print(f"错误: {error_body}")
except Exception as e:
    print(f"❌ 异常: {e}")

print()
print("=" * 80)
print("测试 4: OpenAI 兼容的图像编辑 API (/v1/images/edits)")
print("=" * 80)

# 需要构建 multipart/form-data
import io

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

# 构建请求体
parts = []
parts.append(f'--{boundary}')
parts.append('Content-Disposition: form-data; name="model"')
parts.append('')
parts.append(MODEL)

parts.append(f'--{boundary}')
parts.append('Content-Disposition: form-data; name="prompt"')
parts.append('')
parts.append(TEST_PROMPT)

parts.append(f'--{boundary}')
parts.append('Content-Disposition: form-data; name="image"; filename="test.png"')
parts.append('Content-Type: image/png')
parts.append('')

body_text = '\r\n'.join(parts) + '\r\n'
body = body_text.encode('utf-8') + image_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

endpoint = f"{BASE_URL}/v1/images/edits"
print(f"端点: {endpoint}")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": f"multipart/form-data; boundary={boundary}"
}

request = urllib.request.Request(
    endpoint,
    data=body,
    headers=headers,
    method="POST"
)

print("发送请求...")
try:
    with urllib.request.urlopen(request, timeout=60) as response:
        status = response.status
        body = response.read().decode('utf-8')
        print(f"✅ HTTP {status}")

        data = json.loads(body)
        print("响应结构:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
        print("✅ /v1/images/edits 接口成功！")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}")
    error_body = e.read().decode('utf-8', errors='replace')
    print(f"错误: {error_body}")
except Exception as e:
    print(f"❌ 异常: {e}")
