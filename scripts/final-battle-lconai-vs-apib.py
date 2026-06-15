#!/usr/bin/env python3
"""
最终对决：n.lconai.com vs api.apib.ai (APImart 最佳端点)
"""

import requests
import json
import base64
import time
from datetime import datetime
from pathlib import Path

ENDPOINTS = {
    "lconai": {
        "name": "n.lconai.com (主通道)",
        "base_url": "https://n.lconai.com",
        "api_key": "sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8",
        "model": "gpt-image-2-pro",
        "mode": "sync",
    },
    "apib": {
        "name": "api.apib.ai (APImart 最佳端点)",
        "base_url": "https://api.apib.ai",
        "api_key": "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu",
        "model": "gpt-image-2",
        "mode": "async",
    }
}

TEST_CASES = [
    {"name": "小猫 1024x1024", "prompt": "一只可爱的橙色小猫，坐在窗台上", "size": "1024x1024"},
    {"name": "咖啡店 1920x1080", "prompt": "现代简约的咖啡店室内，温暖灯光", "size": "1920x1080"},
    {"name": "产品海报 1080x1920", "prompt": "时尚产品海报，高端化妆品，白色背景", "size": "1080x1920"},
]

def poll_task(base_url, task_id, api_key, timeout=120):
    """轮询 APImart 任务"""
    url = f"{base_url}/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    start = time.time()
    ssl_errors = 0

    while time.time() - start < timeout:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], dict):
                    status = data["data"].get("status", "")
                    if status in ["succeeded", "completed"]:
                        return data, time.time() - start, ssl_errors
                    elif status == "failed":
                        return None, time.time() - start, ssl_errors
            time.sleep(2)
        except requests.exceptions.SSLError:
            ssl_errors += 1
            time.sleep(2)
        except:
            time.sleep(2)

    return None, time.time() - start, ssl_errors

def test_endpoint(endpoint_key, test_case, output_dir):
    """测试端点"""
    endpoint = ENDPOINTS[endpoint_key]

    print(f"\n{'='*60}")
    print(f"{endpoint['name']} - {test_case['name']}")
    print(f"{'='*60}")

    url = f"{endpoint['base_url']}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {endpoint['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": endpoint["model"],
        "prompt": test_case["prompt"],
        "size": test_case["size"],
        "n": 1,
        "response_format": "b64_json",
    }

    start_time = time.time()

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        submit_duration = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return {"success": False, "duration": submit_duration}

        data = response.json()

        # 异步模式
        if endpoint["mode"] == "async":
            task_id = data["data"][0].get("task_id")
            print(f"提交: {submit_duration:.2f}秒, 任务: {task_id}")
            print(f"轮询中...", end="", flush=True)

            result, poll_duration, ssl_errors = poll_task(
                endpoint['base_url'], task_id, endpoint['api_key']
            )

            total_duration = submit_duration + poll_duration

            if result and "data" in result:
                image_url = result["data"].get("url", "")
                if image_url:
                    img_response = requests.get(image_url, timeout=30)
                    if img_response.status_code == 200:
                        filename = f"{endpoint_key}_{test_case['size']}_{int(time.time())}.png"
                        filepath = output_dir / filename
                        with open(filepath, "wb") as f:
                            f.write(img_response.content)

                        size_kb = len(img_response.content) / 1024
                        print(f" ✅ 成功!")
                        print(f"  总耗时: {total_duration:.2f}秒 (提交 {submit_duration:.2f}秒 + 生成 {poll_duration:.2f}秒)")
                        print(f"  SSL错误: {ssl_errors} 次")
                        print(f"  文件: {size_kb:.1f} KB")

                        return {
                            "success": True,
                            "duration": total_duration,
                            "submit_duration": submit_duration,
                            "poll_duration": poll_duration,
                            "ssl_errors": ssl_errors,
                            "file_size_kb": size_kb,
                        }

            print(f" ❌ 失败")
            return {"success": False, "duration": total_duration, "ssl_errors": ssl_errors}

        # 同步模式
        else:
            if "data" in data and len(data["data"]) > 0:
                image_data = data["data"][0]
                if "b64_json" in image_data:
                    img_bytes = base64.b64decode(image_data["b64_json"])
                    filename = f"{endpoint_key}_{test_case['size']}_{int(time.time())}.png"
                    filepath = output_dir / filename
                    with open(filepath, "wb") as f:
                        f.write(img_bytes)

                    size_kb = len(img_bytes) / 1024
                    print(f"✅ 成功!")
                    print(f"  耗时: {submit_duration:.2f}秒")
                    print(f"  文件: {size_kb:.1f} KB")

                    return {
                        "success": True,
                        "duration": submit_duration,
                        "file_size_kb": size_kb,
                    }

        return {"success": False, "duration": submit_duration}

    except Exception as e:
        print(f"❌ 异常: {str(e)[:60]}")
        return {"success": False, "duration": time.time() - start_time, "error": str(e)[:100]}

def main():
    output_dir = Path("/Users/a123/.openclaw/workspace-design/images/endpoint-tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("最终对决：n.lconai.com vs api.apib.ai")
    print("="*80)

    results = {key: [] for key in ENDPOINTS.keys()}

    for test_case in TEST_CASES:
        for endpoint_key in ENDPOINTS.keys():
            result = test_endpoint(endpoint_key, test_case, output_dir)
            results[endpoint_key].append(result)
            time.sleep(2)

    # 统计
    print("\n" + "="*80)
    print("🏆 最终对比结果")
    print("="*80)

    comparison = []
    for endpoint_key, endpoint_results in results.items():
        endpoint = ENDPOINTS[endpoint_key]
        success = [r for r in endpoint_results if r.get("success")]
        success_count = len(success)
        total_count = len(endpoint_results)

        print(f"\n【{endpoint['name']}】")
        print(f"  成功率: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")

        if success_count > 0:
            avg_duration = sum(r["duration"] for r in success) / success_count
            min_duration = min(r["duration"] for r in success)
            max_duration = max(r["duration"] for r in success)

            print(f"  平均耗时: {avg_duration:.2f}秒")
            print(f"  速度范围: {min_duration:.2f}秒 - {max_duration:.2f}秒")

            if endpoint_key == "apib":
                total_ssl = sum(r.get("ssl_errors", 0) for r in success)
                print(f"  SSL错误: {total_ssl} 次")

            comparison.append({
                "name": endpoint["name"],
                "success_rate": success_count / total_count,
                "avg_duration": avg_duration,
            })

    # 推荐
    print("\n" + "="*80)
    print("📊 综合评估")
    print("="*80 + "\n")

    if len(comparison) == 2:
        comparison.sort(key=lambda x: (-x["success_rate"], x["avg_duration"]))

        winner = comparison[0]
        runner = comparison[1]

        print(f"🥇 第一名: {winner['name']}")
        print(f"   成功率 {winner['success_rate']*100:.0f}%, 平均 {winner['avg_duration']:.2f}秒")

        print(f"\n🥈 第二名: {runner['name']}")
        print(f"   成功率 {runner['success_rate']*100:.0f}%, 平均 {runner['avg_duration']:.2f}秒")

        if winner['success_rate'] == runner['success_rate']:
            speed_diff = ((runner['avg_duration'] - winner['avg_duration']) / runner['avg_duration']) * 100
            print(f"\n💡 速度优势: {winner['name']} 比 {runner['name']} 快 {speed_diff:.1f}%")

if __name__ == "__main__":
    main()
