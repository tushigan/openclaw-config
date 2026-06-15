#!/usr/bin/env python3
"""
对比测试 APImart 的两个端点：
1. https://api.apimart.ai
2. https://api.apib.ai
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

API_KEY = "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu"

ENDPOINTS = {
    "apimart.ai": {
        "name": "api.apimart.ai (原始端点)",
        "base_url": "https://api.apimart.ai",
    },
    "apib.ai": {
        "name": "api.apib.ai (备用端点)",
        "base_url": "https://api.apib.ai",
    }
}

TEST_CASES = [
    {"prompt": "一只可爱的橙色小猫", "size": "1024x1024"},
    {"prompt": "现代简约咖啡店", "size": "1024x1024"},
]

def poll_task(base_url, task_id, timeout=120):
    """轮询任务结果"""
    url = f"{base_url}/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    start = time.time()
    poll_count = 0
    ssl_errors = 0

    while time.time() - start < timeout:
        poll_count += 1
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], dict):
                    status = data["data"].get("status", "")
                    progress = data["data"].get("progress", 0)

                    if status in ["succeeded", "completed"]:
                        duration = time.time() - start
                        return {
                            "success": True,
                            "duration": duration,
                            "poll_count": poll_count,
                            "ssl_errors": ssl_errors,
                            "data": data
                        }
                    elif status == "failed":
                        return {"success": False, "error": "任务失败"}

                    if poll_count % 5 == 0:  # 每5次打印一次
                        print(f"    轮询 #{poll_count}: {status} {progress}%")

            time.sleep(2)

        except requests.exceptions.SSLError:
            ssl_errors += 1
            if ssl_errors % 3 == 0:
                print(f"    SSL错误 #{ssl_errors}")
            time.sleep(2)
        except Exception as e:
            time.sleep(2)

    return {
        "success": False,
        "error": "超时",
        "poll_count": poll_count,
        "ssl_errors": ssl_errors,
        "duration": time.time() - start
    }

def test_endpoint(endpoint_key, test_case):
    """测试单个端点"""
    endpoint = ENDPOINTS[endpoint_key]
    print(f"\n{'='*60}")
    print(f"测试: {endpoint['name']}")
    print(f"提示词: {test_case['prompt']}")
    print(f"{'='*60}")

    # 提交任务
    url = f"{endpoint['base_url']}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-image-2",
        "prompt": test_case["prompt"],
        "size": test_case["size"],
        "n": 1,
    }

    try:
        print(f"  [1] 提交任务... ", end="", flush=True)
        start = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        submit_duration = time.time() - start

        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}

        data = response.json()
        task_id = data["data"][0].get("task_id")
        print(f"✅ {submit_duration:.2f}秒 (task: {task_id})")

        # 轮询结果
        print(f"  [2] 等待生成...")
        result = poll_task(endpoint['base_url'], task_id)

        if result["success"]:
            print(f"  [3] ✅ 完成!")
            print(f"      总耗时: {result['duration']:.2f}秒")
            print(f"      轮询次数: {result['poll_count']}")
            print(f"      SSL错误: {result['ssl_errors']}")

            # 下载图片
            image_url = result["data"]["data"].get("url", "")
            if image_url:
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code == 200:
                    size_kb = len(img_response.content) / 1024
                    print(f"      图片大小: {size_kb:.1f} KB")

            return {
                "success": True,
                "submit_duration": submit_duration,
                "total_duration": submit_duration + result["duration"],
                "poll_count": result["poll_count"],
                "ssl_errors": result["ssl_errors"],
            }
        else:
            print(f"  [3] ❌ 失败: {result.get('error', '未知')}")
            print(f"      轮询次数: {result.get('poll_count', 0)}")
            print(f"      SSL错误: {result.get('ssl_errors', 0)}")
            return result

    except requests.exceptions.SSLError as e:
        print(f"❌ SSL错误")
        return {"success": False, "error": "SSL错误 (提交阶段)"}
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        return {"success": False, "error": str(e)[:100]}

def main():
    print("="*80)
    print("APImart 双端点对比测试")
    print("="*80)

    results = {key: [] for key in ENDPOINTS.keys()}

    # 交叉测试
    for test_case in TEST_CASES:
        for endpoint_key in ENDPOINTS.keys():
            result = test_endpoint(endpoint_key, test_case)
            results[endpoint_key].append(result)
            time.sleep(3)

    # 统计结果
    print("\n" + "="*80)
    print("对比结果")
    print("="*80)

    for endpoint_key, endpoint_results in results.items():
        endpoint = ENDPOINTS[endpoint_key]
        success_count = sum(1 for r in endpoint_results if r.get("success"))
        total_count = len(endpoint_results)

        print(f"\n【{endpoint['name']}】")
        print(f"  成功率: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")

        if success_count > 0:
            success_results = [r for r in endpoint_results if r.get("success")]
            avg_duration = sum(r["total_duration"] for r in success_results) / len(success_results)
            total_ssl_errors = sum(r["ssl_errors"] for r in success_results)
            avg_polls = sum(r["poll_count"] for r in success_results) / len(success_results)

            print(f"  平均耗时: {avg_duration:.2f}秒")
            print(f"  平均轮询: {avg_polls:.0f}次")
            print(f"  SSL错误总数: {total_ssl_errors}")
            print(f"  SSL错误率: {total_ssl_errors/(avg_polls*success_count)*100:.1f}%")

    # 推荐
    print("\n" + "="*80)

    apimart_success = sum(1 for r in results["apimart.ai"] if r.get("success"))
    apib_success = sum(1 for r in results["apib.ai"] if r.get("success"))

    if apib_success > apimart_success:
        print("💡 推荐使用: api.apib.ai (更稳定)")
    elif apimart_success > apib_success:
        print("💡 推荐使用: api.apimart.ai (更稳定)")
    elif apib_success == apimart_success and apib_success > 0:
        # 比较 SSL 错误率
        apimart_ssl = sum(r.get("ssl_errors", 0) for r in results["apimart.ai"] if r.get("success"))
        apib_ssl = sum(r.get("ssl_errors", 0) for r in results["apib.ai"] if r.get("success"))

        if apib_ssl < apimart_ssl:
            print("💡 推荐使用: api.apib.ai (SSL错误更少)")
        elif apimart_ssl < apib_ssl:
            print("💡 推荐使用: api.apimart.ai (SSL错误更少)")
        else:
            print("💡 两个端点表现相同，随意选择")
    else:
        print("⚠️  两个端点都不稳定")

if __name__ == "__main__":
    main()
