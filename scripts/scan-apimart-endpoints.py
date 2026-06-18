#!/usr/bin/env python3
"""
测试 APImart 可能的备用端点
常见模式：api.xxx.com, api-cn.xxx.com, cn.api.xxx.com, api.xxx.cn
"""

import requests
import time

API_KEY = "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu"

# 可能的备用端点
POSSIBLE_ENDPOINTS = [
    "https://api.apimart.ai",           # 原始端点
    "https://api.apib.ai",              # 文档域名对应
    "https://api-cn.apimart.ai",        # 国内端点
    "https://cn.api.apimart.ai",        # 国内端点变体
    "https://api.apimart.cn",           # .cn 域名
    "https://api-cn.apib.ai",           # APIB 国内端点
    "https://cn-api.apimart.ai",        # 另一种格式
    "https://apib.ai/api",              # 子路径形式
]

def test_endpoint(base_url):
    """测试端点连通性"""
    print(f"\n测试: {base_url}")
    print("-" * 60)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # 1. 测试根路径
    try:
        response = requests.get(base_url, headers=headers, timeout=5)
        print(f"  根路径: HTTP {response.status_code}")
    except requests.exceptions.SSLError as e:
        print(f"  根路径: ❌ SSL错误 - {str(e)[:80]}")
        return False
    except Exception as e:
        print(f"  根路径: ❌ {str(e)[:80]}")
        return False

    # 2. 测试 API 端点
    test_url = f"{base_url}/v1/images/generations"
    payload = {
        "model": "gpt-image-2",
        "prompt": "test",
        "size": "1024x1024",
        "n": 1,
    }

    try:
        start = time.time()
        response = requests.post(test_url, headers=headers, json=payload, timeout=10)
        duration = time.time() - start

        print(f"  生图接口: HTTP {response.status_code} ({duration:.2f}秒)")

        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功! 响应: {str(data)[:150]}")
            return True
        elif response.status_code == 401:
            print(f"  ⚠️  认证错误（但端点存在）")
            return True  # 端点存在，只是认证问题
        else:
            print(f"  响应: {response.text[:150]}")
            return False

    except requests.exceptions.SSLError as e:
        print(f"  生图接口: ❌ SSL错误")
        return False
    except requests.exceptions.ConnectTimeout:
        print(f"  生图接口: ❌ 连接超时")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"  生图接口: ❌ 连接失败")
        return False
    except Exception as e:
        print(f"  生图接口: ❌ {str(e)[:80]}")
        return False

def main():
    print("=" * 80)
    print("APImart 备用端点扫描")
    print("=" * 80)

    available_endpoints = []

    for endpoint in POSSIBLE_ENDPOINTS:
        is_available = test_endpoint(endpoint)
        if is_available:
            available_endpoints.append(endpoint)
        time.sleep(1)  # 避免请求过快

    print("\n" + "=" * 80)
    print("扫描结果")
    print("=" * 80)

    if available_endpoints:
        print(f"\n✅ 找到 {len(available_endpoints)} 个可用端点:\n")
        for i, endpoint in enumerate(available_endpoints, 1):
            print(f"  {i}. {endpoint}")
    else:
        print("\n❌ 未找到可用的备用端点")
        print("\n建议:")
        print("  1. 查看官方文档是否有端点列表")
        print("  2. 联系 APImart 技术支持询问备用端点")
        print("  3. 检查是否有 MCP 服务器配置")

if __name__ == "__main__":
    main()
