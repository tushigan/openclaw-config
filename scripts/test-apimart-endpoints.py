#!/usr/bin/env python3
"""
测试 APImart 的各种可能的任务查询端点
"""

import requests
import json
import time

API_KEY = "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu"
BASE_URL = "https://api.apimart.ai"

# 先提交一个任务
def submit_task():
    url = f"{BASE_URL}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-image-2",
        "prompt": "一只可爱的橙色小猫",
        "size": "1024x1024",
        "n": 1,
    }

    print("提交任务...")
    response = requests.post(url, headers=headers, json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 200:
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            task_id = data["data"][0].get("task_id")
            return task_id

    return None

# 尝试不同的查询端点
def try_query_endpoints(task_id):
    if not task_id:
        print("没有 task_id，跳过查询测试")
        return

    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    # 可能的查询端点列表
    possible_endpoints = [
        f"/v1/images/generations/{task_id}",  # 之前测试的（失败）
        f"/v1/images/tasks/{task_id}",        # 常见的异步任务端点
        f"/v1/tasks/{task_id}",                # 更简洁的任务端点
        f"/v1/images/{task_id}",               # 直接用 images
        f"/v1/images/generation/{task_id}",    # 单数形式
        f"/v1/image/tasks/{task_id}",          # image 单数
    ]

    print(f"\n测试 task_id: {task_id}")
    print("="*60)

    for endpoint in possible_endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n尝试: {endpoint}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                print(f"  ✅ 成功! 找到正确端点!")
                print(f"  响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
                return endpoint
            elif response.status_code == 404:
                print(f"  ❌ 404 Not Found")
            else:
                print(f"  ⚠️  其他错误")
                try:
                    print(f"  响应: {response.json()}")
                except:
                    print(f"  响应: {response.text[:200]}")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)[:100]}")

        time.sleep(1)  # 避免请求过快

    print("\n所有端点都失败了")
    return None

if __name__ == "__main__":
    print("APImart 异步任务查询端点测试\n")

    # 提交任务
    task_id = submit_task()

    if task_id:
        print(f"\n等待 5 秒让任务开始处理...")
        time.sleep(5)

        # 尝试查询
        correct_endpoint = try_query_endpoints(task_id)

        if correct_endpoint:
            print(f"\n🎉 找到正确的查询端点: {correct_endpoint}")
        else:
            print(f"\n⚠️  未找到有效的查询端点")
            print(f"建议：")
            print(f"1. 查看完整的 API 文档: https://docs.apib.ai/cn/api-reference/images/gpt-image-2/generation")
            print(f"2. 联系 APImart 技术支持")
            print(f"3. 检查是否需要使用 webhook 回调而不是轮询")
