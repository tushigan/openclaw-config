#!/usr/bin/env python3
"""
深入分析 SSL 错误：
1. 对比 api.apib.ai 和 n.lconai.com 的 SSL 行为
2. 测试不同的 SSL 配置
3. 找出解决方案
"""

import requests
import ssl
import time
from urllib3.util.ssl_ import create_urllib3_context

# 禁用 SSL 警告（仅用于测试）
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENDPOINTS = {
    "apib": {
        "name": "api.apib.ai",
        "url": "https://api.apib.ai/v1/images/generations",
        "api_key": "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu",
    },
    "lconai": {
        "name": "n.lconai.com",
        "url": "https://n.lconai.com/v1/images/generations",
        "api_key": "sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8",
    }
}

def test_ssl_connection(endpoint_key, method="default"):
    """测试 SSL 连接"""
    endpoint = ENDPOINTS[endpoint_key]

    headers = {
        "Authorization": f"Bearer {endpoint['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-image-2-pro" if endpoint_key == "lconai" else "gpt-image-2",
        "prompt": "test",
        "size": "1024x1024",
        "n": 1,
    }

    try:
        if method == "default":
            # 默认配置
            response = requests.post(
                endpoint["url"],
                headers=headers,
                json=payload,
                timeout=10
            )
        elif method == "no_verify":
            # 跳过证书验证
            response = requests.post(
                endpoint["url"],
                headers=headers,
                json=payload,
                timeout=10,
                verify=False
            )
        elif method == "legacy_ssl":
            # 使用旧版 SSL 配置
            session = requests.Session()

            # 自定义 SSL 上下文
            class SSLAdapter(requests.adapters.HTTPAdapter):
                def init_poolmanager(self, *args, **kwargs):
                    ctx = create_urllib3_context()
                    ctx.set_ciphers('DEFAULT@SECLEVEL=1')
                    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
                    kwargs['ssl_context'] = ctx
                    return super().init_poolmanager(*args, **kwargs)

            session.mount('https://', SSLAdapter())
            response = session.post(
                endpoint["url"],
                headers=headers,
                json=payload,
                timeout=10
            )

        return {
            "success": True,
            "status": response.status_code,
            "method": method,
        }

    except requests.exceptions.SSLError as e:
        error_msg = str(e)

        # 分析具体的 SSL 错误类型
        if "UNEXPECTED_EOF_WHILE_READING" in error_msg:
            error_type = "UNEXPECTED_EOF"
        elif "CERTIFICATE_VERIFY_FAILED" in error_msg:
            error_type = "CERT_VERIFY_FAILED"
        elif "WRONG_VERSION_NUMBER" in error_msg:
            error_type = "WRONG_VERSION"
        elif "HANDSHAKE_FAILURE" in error_msg:
            error_type = "HANDSHAKE_FAILURE"
        else:
            error_type = "OTHER_SSL_ERROR"

        return {
            "success": False,
            "error_type": error_type,
            "error_msg": error_msg[:200],
            "method": method,
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error_type": "TIMEOUT",
            "method": method,
        }

    except Exception as e:
        return {
            "success": False,
            "error_type": "OTHER_ERROR",
            "error_msg": str(e)[:200],
            "method": method,
        }

def main():
    print("="*80)
    print("SSL 错误深度分析")
    print("="*80)

    methods = ["default", "no_verify", "legacy_ssl"]
    test_count = 10

    for endpoint_key in ["apib", "lconai"]:
        endpoint = ENDPOINTS[endpoint_key]
        print(f"\n{'='*80}")
        print(f"测试端点: {endpoint['name']}")
        print(f"{'='*80}\n")

        for method in methods:
            print(f"方法: {method}")
            print("-" * 60)

            results = []
            for i in range(test_count):
                result = test_ssl_connection(endpoint_key, method)
                results.append(result)

                if result["success"]:
                    print(f"  #{i+1}: ✅ HTTP {result['status']}")
                else:
                    print(f"  #{i+1}: ❌ {result['error_type']}")

                time.sleep(0.5)

            # 统计
            success_count = sum(1 for r in results if r["success"])
            success_rate = success_count / test_count * 100

            print(f"\n  成功率: {success_count}/{test_count} ({success_rate:.0f}%)")

            # 错误类型统计
            error_types = {}
            for r in results:
                if not r["success"]:
                    error_type = r["error_type"]
                    error_types[error_type] = error_types.get(error_type, 0) + 1

            if error_types:
                print(f"  错误类型:")
                for error_type, count in error_types.items():
                    print(f"    - {error_type}: {count}次")

            print()

        time.sleep(2)

    # 总结
    print("="*80)
    print("结论")
    print("="*80)
    print("""
SSL 错误分析:

1. UNEXPECTED_EOF_WHILE_READING
   - 最常见的错误
   - 服务器在 SSL 握手或数据传输时突然关闭连接
   - 可能原因：服务器负载高、网络不稳定、CDN问题

2. 解决方案：
   - 使用重试机制（最有效）
   - 增加超时时间
   - 使用连接池
   - 考虑降低请求频率

3. verify=False（不推荐）：
   - 跳过证书验证可以避免证书问题
   - 但不能解决 UNEXPECTED_EOF 问题
   - 会降低安全性

4. 使用旧版 SSL（可能有效）：
   - 降低 SSL 安全级别
   - 可能绕过某些兼容性问题
   - 但也有安全风险
    """)

if __name__ == "__main__":
    main()
