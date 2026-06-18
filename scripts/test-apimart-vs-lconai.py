#!/usr/bin/env python3
"""
重新测试 APImart（使用正确端点）vs n.lconai.com
"""

import os
import sys
import time
import json
import base64
import requests
from datetime import datetime
from pathlib import Path

# 只测试这两个端点
ENDPOINTS = {
    "lconai": {
        "name": "n.lconai.com (主通道)",
        "base_url": "https://n.lconai.com",
        "api_key": "sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8",
        "model": "gpt-image-2-pro",
        "mode": "sync",
    },
    "apimart": {
        "name": "api.apimart.ai (新端点-修复)",
        "base_url": "https://api.apimart.ai",
        "api_key": "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu",
        "model": "gpt-image-2",
        "mode": "async",
    }
}

TEST_CASES = [
    {
        "name": "简单文生图 1024x1024",
        "prompt": "一只可爱的橙色小猫，坐在窗台上，阳光洒在身上，温暖的氛围",
        "size": "1024x1024",
        "n": 1,
    },
    {
        "name": "横版图 1920x1080",
        "prompt": "现代简约的咖啡店室内，温暖的灯光，木质桌椅，绿植装饰",
        "size": "1920x1080",
        "n": 1,
    },
]

def poll_task_result(endpoint, task_id, timeout=180):
    """轮询异步任务结果 - 使用正确的端点"""
    url = f"{endpoint['base_url']}/v1/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {endpoint['api_key']}",
    }

    start_time = time.time()
    poll_count = 0

    while time.time() - start_time < timeout:
        poll_count += 1
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()

                if "data" in data and isinstance(data["data"], dict):
                    task_data = data["data"]
                    status = task_data.get("status", "")
                    progress = task_data.get("progress", 0)

                    if status in ["succeeded", "completed"]:
                        print(f"   ✅ 任务完成! (轮询 {poll_count} 次)")
                        return data, time.time() - start_time
                    elif status == "failed":
                        print(f"   ❌ 任务失败")
                        return None, time.time() - start_time
                    else:
                        print(f"   轮询 #{poll_count}: 状态={status}, 进度={progress}%")
                        time.sleep(3)
                else:
                    print(f"   轮询 #{poll_count}: 响应格式异常")
                    time.sleep(3)
            else:
                print(f"   轮询 #{poll_count}: HTTP {response.status_code}")
                time.sleep(3)
        except Exception as e:
            print(f"   轮询 #{poll_count}: 异常 {str(e)[:80]}")
            time.sleep(3)

    return None, time.time() - start_time

def test_endpoint(endpoint_key, test_case, output_dir):
    """测试单个端点"""
    endpoint = ENDPOINTS[endpoint_key]

    print(f"\n{'='*60}")
    print(f"测试端点: {endpoint['name']}")
    print(f"测试用例: {test_case['name']}")
    print(f"{'='*60}")

    url = f"{endpoint['base_url']}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {endpoint['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": endpoint["model"],
        "prompt": test_case["prompt"],
        "n": test_case["n"],
        "size": test_case["size"],
        "response_format": "b64_json",
    }

    print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")

    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        submit_duration = time.time() - start_time

        print(f"提交耗时: {submit_duration:.2f}秒")
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # 异步模式
            if endpoint.get("mode") == "async":
                if "data" in data and len(data["data"]) > 0:
                    task_data = data["data"][0]
                    task_id = task_data.get("task_id")

                    if task_id:
                        print(f"任务已提交: {task_id}")
                        print(f"开始轮询结果...")

                        result_data, poll_duration = poll_task_result(endpoint, task_id, timeout=180)
                        total_duration = submit_duration + poll_duration

                        if result_data:
                            # APImart 格式：{"code": 200, "data": {"url": "...", ...}}
                            if "data" in result_data and isinstance(result_data["data"], dict):
                                image_data = result_data["data"]
                                image_url = image_data.get("url", "")

                                if image_url:
                                    print(f"下载图片: {image_url}")
                                    img_response = requests.get(image_url, timeout=30)

                                    if img_response.status_code == 200:
                                        img_bytes = img_response.content
                                        filename = f"{endpoint_key}_{test_case['size']}_{int(time.time())}.png"
                                        filepath = output_dir / filename

                                        with open(filepath, "wb") as f:
                                            f.write(img_bytes)

                                        file_size_kb = len(img_bytes) / 1024
                                        print(f"✅ 成功! 图片已保存: {filepath.name}")
                                        print(f"   总耗时: {total_duration:.2f}秒 (提交 {submit_duration:.2f}秒 + 轮询 {poll_duration:.2f}秒)")
                                        print(f"   文件大小: {file_size_kb:.1f} KB")

                                        return {
                                            "endpoint": endpoint_key,
                                            "endpoint_name": endpoint["name"],
                                            "test_case": test_case["name"],
                                            "status": "success",
                                            "duration": total_duration,
                                            "submit_duration": submit_duration,
                                            "poll_duration": poll_duration,
                                            "file_size_kb": file_size_kb,
                                            "filepath": str(filepath),
                                        }

                        print(f"❌ 失败: 轮询超时或任务失败")
                        return {
                            "endpoint": endpoint_key,
                            "endpoint_name": endpoint["name"],
                            "test_case": test_case["name"],
                            "status": "failed",
                            "error": "轮询超时或任务失败",
                            "duration": total_duration,
                        }

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

                        file_size_kb = len(img_bytes) / 1024
                        print(f"✅ 成功! 图片已保存: {filepath.name}")
                        print(f"   文件大小: {file_size_kb:.1f} KB")

                        return {
                            "endpoint": endpoint_key,
                            "endpoint_name": endpoint["name"],
                            "test_case": test_case["name"],
                            "status": "success",
                            "duration": submit_duration,
                            "file_size_kb": file_size_kb,
                            "filepath": str(filepath),
                        }

        print(f"❌ 失败: HTTP {response.status_code}")
        return {
            "endpoint": endpoint_key,
            "endpoint_name": endpoint["name"],
            "test_case": test_case["name"],
            "status": "failed",
            "error": f"HTTP {response.status_code}",
            "duration": submit_duration,
        }

    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ 异常: {str(e)}")
        return {
            "endpoint": endpoint_key,
            "endpoint_name": endpoint["name"],
            "test_case": test_case["name"],
            "status": "error",
            "error": str(e),
            "duration": duration,
        }

def print_summary(results):
    """打印测试摘要"""
    print(f"\n\n{'='*80}")
    print("🎯 最终对比结果")
    print(f"{'='*80}\n")

    by_endpoint = {}
    for result in results:
        ep = result["endpoint"]
        if ep not in by_endpoint:
            by_endpoint[ep] = []
        by_endpoint[ep].append(result)

    comparison = []
    for endpoint_key in by_endpoint.keys():
        endpoint_results = by_endpoint[endpoint_key]
        success_count = sum(1 for r in endpoint_results if r["status"] == "success")
        total_count = len(endpoint_results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        success_durations = [r["duration"] for r in endpoint_results if r["status"] == "success"]
        avg_duration = sum(success_durations) / len(success_durations) if success_durations else 999
        min_duration = min(success_durations) if success_durations else 0
        max_duration = max(success_durations) if success_durations else 0

        comparison.append({
            "endpoint": ENDPOINTS[endpoint_key]["name"],
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "success_count": success_count,
            "total_count": total_count,
        })

        print(f"【{ENDPOINTS[endpoint_key]['name']}】")
        print(f"  成功率: {success_rate:.0f}% ({success_count}/{total_count})")
        if success_durations:
            print(f"  平均耗时: {avg_duration:.2f}秒")
            print(f"  速度范围: {min_duration:.2f}秒 - {max_duration:.2f}秒")
        print()

    comparison.sort(key=lambda x: (-x["success_rate"], x["avg_duration"]))

    if len(comparison) > 1 and comparison[0]["success_rate"] > 0 and comparison[1]["success_rate"] > 0:
        winner = comparison[0]
        runner_up = comparison[1]

        print(f"{'='*80}")
        print("📊 综合评估\n")
        print(f"🥇 第一名: {winner['endpoint']}")
        print(f"   成功率 {winner['success_rate']:.0f}%, 平均耗时 {winner['avg_duration']:.2f}秒")
        print(f"\n🥈 第二名: {runner_up['endpoint']}")
        print(f"   成功率 {runner_up['success_rate']:.0f}%, 平均耗时 {runner_up['avg_duration']:.2f}秒")

        if winner['avg_duration'] < runner_up['avg_duration']:
            speed_advantage = ((runner_up['avg_duration'] - winner['avg_duration']) / runner_up['avg_duration']) * 100
            print(f"\n💡 {winner['endpoint']} 比 {runner_up['endpoint']} 快 {speed_advantage:.1f}%")

def main():
    output_dir = Path("/Users/a123/.openclaw/workspace-design/images/endpoint-tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("APImart vs n.lconai.com 对比测试（使用正确的 API 端点）")
    print("=" * 80)

    results = []
    for test_case in TEST_CASES:
        for endpoint_key in ENDPOINTS.keys():
            result = test_endpoint(endpoint_key, test_case, output_dir)
            results.append(result)
            time.sleep(2)

    result_file = output_dir / f"apimart-comparison-{int(time.time())}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存到: {result_file}")
    print_summary(results)

if __name__ == "__main__":
    main()
