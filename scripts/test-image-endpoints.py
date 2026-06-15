#!/usr/bin/env python3
"""
图像生成端点测试脚本
测试三个端点的稳定性和速度：
1. n.lconai.com (主通道)
2. direct.aixor.org (备用通道)
3. api.apimart.ai (新端点)
"""

import os
import sys
import time
import json
import base64
import requests
from datetime import datetime
from pathlib import Path

# 测试配置
ENDPOINTS = {
    "lconai": {
        "name": "n.lconai.com (主通道)",
        "base_url": "https://n.lconai.com",
        "api_key": "sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8",
        "model": "gpt-image-2-pro",
        "mode": "sync",  # 同步返回图片
    },
    "aixor": {
        "name": "direct.aixor.org (备用通道)",
        "base_url": "https://direct.aixor.org",
        "api_key": "sk-Z51Uf6PR1IifVDDRh431r8HtWXyeN194LDBPBDYdopAv67ir",
        "model": "gpt-image-2",
        "mode": "sync",  # 同步返回图片
    },
    "apimart": {
        "name": "api.apimart.ai (新端点)",
        "base_url": "https://api.apimart.ai",
        "api_key": "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu",
        "model": "gpt-image-2",
        "mode": "async",  # 异步任务模式
    }
}

# 测试用例
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
    {
        "name": "竖版图 1080x1920",
        "prompt": "时尚的产品海报，高端化妆品瓶子，干净的白色背景，商业摄影风格",
        "size": "1080x1920",
        "n": 1,
    }
]

def poll_task_result(endpoint, task_id, timeout=120):
    """轮询异步任务结果"""
    # APImart 使用 /v1/tasks/{task_id} 而不是 /v1/images/generations/{task_id}
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

                # APImart 的响应格式：{"code": 200, "data": {"status": "...", "id": "...", ...}}
                if "data" in data and isinstance(data["data"], dict):
                    task_data = data["data"]
                    status = task_data.get("status", "")
                    progress = task_data.get("progress", 0)

                    if status == "succeeded" or status == "completed":
                        return data, time.time() - start_time
                    elif status == "failed":
                        return None, time.time() - start_time
                    else:
                        # 继续轮询
                        print(f"   轮询 #{poll_count}: 状态={status}, 进度={progress}%")
                        time.sleep(3)
                else:
                    print(f"   轮询 #{poll_count}: 响应格式异常")
                    time.sleep(3)
            else:
                print(f"   轮询 #{poll_count}: HTTP {response.status_code}")
                time.sleep(3)
        except Exception as e:
            print(f"   轮询 #{poll_count}: 异常 {str(e)}")
            time.sleep(3)

    return None, time.time() - start_time

def test_endpoint(endpoint_key, test_case, output_dir):
    """测试单个端点"""
    endpoint = ENDPOINTS[endpoint_key]

    print(f"\n{'='*60}")
    print(f"测试端点: {endpoint['name']}")
    print(f"测试用例: {test_case['name']}")
    print(f"{'='*60}")

    # 检查 API Key
    if not endpoint["api_key"]:
        return {
            "endpoint": endpoint_key,
            "test_case": test_case["name"],
            "status": "skipped",
            "error": "API Key 未配置",
            "duration": 0,
        }

    # 构建请求
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

    print(f"请求参数: model={endpoint['model']}, size={test_case['size']}, mode={endpoint.get('mode', 'sync')}")
    print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")

    # 发送请求
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        submit_duration = time.time() - start_time

        print(f"提交耗时: {submit_duration:.2f}秒")
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # 异步模式：需要轮询任务结果
            if endpoint.get("mode") == "async":
                if "data" in data and len(data["data"]) > 0:
                    task_data = data["data"][0]
                    task_id = task_data.get("task_id")

                    if task_id:
                        print(f"任务已提交: {task_id}")
                        print(f"开始轮询结果...")

                        result_data, poll_duration = poll_task_result(endpoint, task_id)
                        total_duration = submit_duration + poll_duration

                        print(f"轮询耗时: {poll_duration:.2f}秒")
                        print(f"总耗时: {total_duration:.2f}秒")

                        if result_data:
                            # 提取图片 URL - APImart 格式：{"code": 200, "data": {"url": "..."}}
                            if "data" in result_data and isinstance(result_data["data"], dict):
                                image_data = result_data["data"]
                                image_url = image_data.get("url", "")

                                if image_url:
                                    # 下载图片
                                    print(f"下载图片: {image_url}")
                                    img_response = requests.get(image_url, timeout=30)

                                    if img_response.status_code == 200:
                                        img_bytes = img_response.content
                                        filename = f"{endpoint_key}_{test_case['size']}_{int(time.time())}.png"
                                        filepath = output_dir / filename

                                        with open(filepath, "wb") as f:
                                            f.write(img_bytes)

                                        file_size_kb = len(img_bytes) / 1024
                                        print(f"✅ 成功! 图片已保存: {filepath}")
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

                print(f"❌ 失败: 未返回 task_id")
                return {
                    "endpoint": endpoint_key,
                    "endpoint_name": endpoint["name"],
                    "test_case": test_case["name"],
                    "status": "failed",
                    "error": "未返回 task_id",
                    "duration": submit_duration,
                }

            # 同步模式：直接返回图片
            else:
                duration = submit_duration

                # 保存图片
                if "data" in data and len(data["data"]) > 0:
                    image_data = data["data"][0]

                    if "b64_json" in image_data:
                        # 解码并保存
                        img_bytes = base64.b64decode(image_data["b64_json"])
                        filename = f"{endpoint_key}_{test_case['size']}_{int(time.time())}.png"
                        filepath = output_dir / filename

                        with open(filepath, "wb") as f:
                            f.write(img_bytes)

                        file_size_kb = len(img_bytes) / 1024
                        print(f"✅ 成功! 图片已保存: {filepath}")
                        print(f"   文件大小: {file_size_kb:.1f} KB")

                        return {
                            "endpoint": endpoint_key,
                            "endpoint_name": endpoint["name"],
                            "test_case": test_case["name"],
                            "status": "success",
                            "duration": duration,
                            "file_size_kb": file_size_kb,
                            "filepath": str(filepath),
                        }
                    elif "url" in image_data:
                        print(f"✅ 成功! 返回 URL: {image_data['url']}")
                        return {
                            "endpoint": endpoint_key,
                            "endpoint_name": endpoint["name"],
                            "test_case": test_case["name"],
                            "status": "success",
                            "duration": duration,
                            "url": image_data["url"],
                        }

                print(f"❌ 失败: 响应格式异常")
                return {
                    "endpoint": endpoint_key,
                    "endpoint_name": endpoint["name"],
                    "test_case": test_case["name"],
                    "status": "failed",
                    "error": "响应格式异常",
                    "duration": duration,
                    "response": data,
                }
        else:
            duration = submit_duration
            print(f"❌ 失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误信息: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                print(f"   错误信息: {response.text}")

            return {
                "endpoint": endpoint_key,
                "endpoint_name": endpoint["name"],
                "test_case": test_case["name"],
                "status": "failed",
                "error": f"HTTP {response.status_code}",
                "duration": duration,
                "response_text": response.text[:500],
            }

    except requests.exceptions.Timeout:
        duration = time.time() - start_time
        print(f"❌ 超时 ({duration:.2f}秒)")
        return {
            "endpoint": endpoint_key,
            "endpoint_name": endpoint["name"],
            "test_case": test_case["name"],
            "status": "timeout",
            "duration": duration,
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
    print("测试摘要")
    print(f"{'='*80}\n")

    # 按端点分组
    by_endpoint = {}
    for result in results:
        ep = result["endpoint"]
        if ep not in by_endpoint:
            by_endpoint[ep] = []
        by_endpoint[ep].append(result)

    # 统计每个端点
    for endpoint_key, endpoint_results in by_endpoint.items():
        endpoint_name = ENDPOINTS[endpoint_key]["name"]
        print(f"\n【{endpoint_name}】")
        print(f"{'-'*60}")

        success_count = sum(1 for r in endpoint_results if r["status"] == "success")
        total_count = len(endpoint_results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        # 计算平均耗时（只统计成功的）
        success_durations = [r["duration"] for r in endpoint_results if r["status"] == "success"]
        avg_duration = sum(success_durations) / len(success_durations) if success_durations else 0

        print(f"成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
        if success_durations:
            print(f"平均耗时: {avg_duration:.2f}秒")
            print(f"最快: {min(success_durations):.2f}秒")
            print(f"最慢: {max(success_durations):.2f}秒")

        # 详细结果
        print("\n详细结果:")
        for r in endpoint_results:
            status_icon = "✅" if r["status"] == "success" else "❌"
            duration_str = f"{r['duration']:.2f}秒" if r["duration"] > 0 else "N/A"
            print(f"  {status_icon} {r['test_case']}: {r['status']} ({duration_str})")
            if r["status"] != "success" and "error" in r:
                print(f"      错误: {r['error']}")

    # 综合对比
    print(f"\n{'='*80}")
    print("综合对比")
    print(f"{'='*80}\n")

    comparison = []
    for endpoint_key in by_endpoint.keys():
        endpoint_results = by_endpoint[endpoint_key]
        success_count = sum(1 for r in endpoint_results if r["status"] == "success")
        total_count = len(endpoint_results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        success_durations = [r["duration"] for r in endpoint_results if r["status"] == "success"]
        avg_duration = sum(success_durations) / len(success_durations) if success_durations else 999

        comparison.append({
            "endpoint": ENDPOINTS[endpoint_key]["name"],
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "success_count": success_count,
            "total_count": total_count,
        })

    # 按成功率排序
    comparison.sort(key=lambda x: (-x["success_rate"], x["avg_duration"]))

    print(f"{'排名':<6} {'端点':<35} {'成功率':<12} {'平均耗时':<12}")
    print(f"{'-'*80}")
    for i, comp in enumerate(comparison, 1):
        success_rate_str = f"{comp['success_rate']:.1f}% ({comp['success_count']}/{comp['total_count']})"
        duration_str = f"{comp['avg_duration']:.2f}秒" if comp['avg_duration'] < 999 else "N/A"
        print(f"{i:<6} {comp['endpoint']:<35} {success_rate_str:<12} {duration_str:<12}")

    # 推荐
    if comparison and comparison[0]["success_rate"] > 0:
        print(f"\n💡 推荐使用: {comparison[0]['endpoint']}")
        print(f"   原因: 成功率 {comparison[0]['success_rate']:.1f}%, 平均耗时 {comparison[0]['avg_duration']:.2f}秒")

def main():
    # 创建输出目录
    output_dir = Path("/Users/a123/.openclaw/workspace-design/images/endpoint-tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("图像生成端点测试")
    print(f"输出目录: {output_dir}")
    print(f"测试用例数: {len(TEST_CASES)}")
    print(f"测试端点数: {len(ENDPOINTS)}")

    # 执行测试
    results = []
    for test_case in TEST_CASES:
        for endpoint_key in ENDPOINTS.keys():
            result = test_endpoint(endpoint_key, test_case, output_dir)
            results.append(result)

            # 间隔一下，避免请求过快
            time.sleep(2)

    # 保存结果
    result_file = output_dir / f"test-results-{int(time.time())}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\n详细结果已保存到: {result_file}")

    # 打印摘要
    print_summary(results)

if __name__ == "__main__":
    main()
