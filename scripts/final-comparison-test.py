#!/usr/bin/env python3
"""
三端点公平对比测试
- 每个端点10张图
- 统一使用 1920x1080 分辨率（2K以下）
- 统一提示词
- 记录成功率、平均耗时、稳定性
"""

import requests
import json
import time
import base64
from datetime import datetime
from pathlib import Path

# 三个端点配置
ENDPOINTS = {
    "n.lconai.com": {
        "name": "n.lconai.com (主通道)",
        "base_url": "https://n.lconai.com",
        "api_key": "sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8",
        "model": "gpt-image-2-pro",
        "mode": "sync",
    },
    "direct.aixor.org": {
        "name": "direct.aixor.org (备用通道)",
        "base_url": "https://direct.aixor.org",
        "api_key": "sk-Z51Uf6PR1IifVDDRh431r8HtWXyeN194LDBPBDYdopAv67ir",
        "model": "gpt-image-2",
        "mode": "sync",
    },
    "api.apib.ai": {
        "name": "api.apib.ai (APImart)",
        "base_url": "https://api.apib.ai",
        "api_key": "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu",
        "model": "gpt-image-2",
        "mode": "async",
    }
}

# 统一测试参数
TEST_CONFIG = {
    "size": "1920x1080",  # 2K以下
    "count": 10,  # 每个端点10张
    "prompt": "现代简约风格的咖啡店内景，温暖的灯光，木质桌椅，绿植装饰，窗外阳光，高清摄影",
}

def log(msg, level="INFO"):
    """带时间戳的日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def poll_async_task(base_url, api_key, task_id, max_polls=90):
    """轮询异步任务（APImart）"""
    url = f"{base_url}/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    ssl_errors = 0
    start = time.time()

    for poll_count in range(1, max_polls + 1):
        try:
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()

                if "data" in data and isinstance(data["data"], dict):
                    task_data = data["data"]
                    status = task_data.get("status", "")
                    progress = task_data.get("progress", 0)

                    if status in ["succeeded", "completed"]:
                        duration = time.time() - start

                        # 提取图片 URL（使用正确的格式）
                        if "result" in task_data and "images" in task_data["result"]:
                            images = task_data["result"]["images"]
                            if len(images) > 0 and "url" in images[0]:
                                url_data = images[0]["url"]
                                image_url = url_data[0] if isinstance(url_data, list) else url_data

                                return {
                                    "success": True,
                                    "duration": duration,
                                    "poll_count": poll_count,
                                    "ssl_errors": ssl_errors,
                                    "url": image_url,
                                }

                        return {
                            "success": False,
                            "error": "NO_URL",
                            "duration": duration,
                            "ssl_errors": ssl_errors,
                        }

                    elif status == "failed":
                        return {
                            "success": False,
                            "error": "TASK_FAILED",
                            "duration": time.time() - start,
                            "ssl_errors": ssl_errors,
                        }

            time.sleep(2)

        except requests.exceptions.SSLError:
            ssl_errors += 1
            time.sleep(2)
        except:
            time.sleep(2)

    return {
        "success": False,
        "error": "TIMEOUT",
        "duration": time.time() - start,
        "ssl_errors": ssl_errors,
    }

def test_single_image(endpoint_key, test_num, output_dir):
    """测试生成单张图片"""
    endpoint = ENDPOINTS[endpoint_key]

    log(f"[{endpoint['name']}] 开始测试 #{test_num}", "INFO")

    # 提交请求
    url = f"{endpoint['base_url']}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {endpoint['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": endpoint["model"],
        "prompt": TEST_CONFIG["prompt"],
        "size": TEST_CONFIG["size"],
        "n": 1,
        "response_format": "b64_json",
    }

    start_time = time.time()

    try:
        # 提交
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        submit_duration = time.time() - start_time

        if response.status_code != 200:
            log(f"  ❌ 提交失败: HTTP {response.status_code}", "ERROR")
            return {
                "success": False,
                "error": f"HTTP_{response.status_code}",
                "submit_duration": submit_duration,
            }

        data = response.json()

        # 异步模式（APImart）
        if endpoint["mode"] == "async":
            task_id = data["data"][0]["task_id"]
            log(f"  ⏳ 任务提交成功: {task_id} ({submit_duration:.2f}秒)", "INFO")

            # 轮询
            result = poll_async_task(endpoint["base_url"], endpoint["api_key"], task_id)

            if result["success"]:
                total_duration = submit_duration + result["duration"]
                log(f"  ✅ 生成成功: {total_duration:.2f}秒 (SSL错误{result['ssl_errors']}次)", "SUCCESS")

                # 下载图片
                img_response = requests.get(result["url"], timeout=30)
                if img_response.status_code == 200:
                    filename = f"{endpoint_key}_{test_num}_{int(time.time())}.png"
                    filepath = output_dir / filename

                    with open(filepath, "wb") as f:
                        f.write(img_response.content)

                    size_kb = len(img_response.content) / 1024

                    return {
                        "success": True,
                        "submit_duration": submit_duration,
                        "total_duration": total_duration,
                        "ssl_errors": result["ssl_errors"],
                        "file_size_kb": size_kb,
                        "filepath": str(filepath),
                    }

            log(f"  ❌ 生成失败: {result.get('error', '未知')}", "ERROR")
            return result

        # 同步模式
        else:
            duration = submit_duration

            if "data" in data and len(data["data"]) > 0:
                image_data = data["data"][0]

                if "b64_json" in image_data:
                    img_bytes = base64.b64decode(image_data["b64_json"])
                    filename = f"{endpoint_key}_{test_num}_{int(time.time())}.png"
                    filepath = output_dir / filename

                    with open(filepath, "wb") as f:
                        f.write(img_bytes)

                    size_kb = len(img_bytes) / 1024
                    log(f"  ✅ 生成成功: {duration:.2f}秒", "SUCCESS")

                    return {
                        "success": True,
                        "total_duration": duration,
                        "file_size_kb": size_kb,
                        "filepath": str(filepath),
                    }

            log(f"  ❌ 响应格式错误", "ERROR")
            return {
                "success": False,
                "error": "RESPONSE_FORMAT",
                "duration": duration,
            }

    except requests.exceptions.SSLError as e:
        duration = time.time() - start_time
        log(f"  ❌ SSL错误: {str(e)[:80]}", "ERROR")
        return {
            "success": False,
            "error": "SSL_ERROR",
            "duration": duration,
        }

    except requests.exceptions.Timeout:
        duration = time.time() - start_time
        log(f"  ❌ 超时: {duration:.2f}秒", "ERROR")
        return {
            "success": False,
            "error": "TIMEOUT",
            "duration": duration,
        }

    except Exception as e:
        duration = time.time() - start_time
        log(f"  ❌ 异常: {str(e)[:80]}", "ERROR")
        return {
            "success": False,
            "error": str(e)[:100],
            "duration": duration,
        }

def print_statistics(endpoint_key, results):
    """打印单个端点的统计数据"""
    endpoint = ENDPOINTS[endpoint_key]

    print(f"\n{'='*80}")
    print(f"【{endpoint['name']}】统计结果")
    print(f"{'='*80}")

    success_results = [r for r in results if r.get("success")]
    success_count = len(success_results)
    total_count = len(results)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0

    print(f"\n成功率: {success_count}/{total_count} ({success_rate:.1f}%)")

    if success_count > 0:
        durations = [r["total_duration"] for r in success_results]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        print(f"平均耗时: {avg_duration:.2f}秒")
        print(f"最快: {min_duration:.2f}秒")
        print(f"最慢: {max_duration:.2f}秒")
        print(f"耗时标准差: {((sum((d - avg_duration)**2 for d in durations) / len(durations)) ** 0.5):.2f}秒")

        # SSL 错误统计
        if endpoint["mode"] == "async":
            total_ssl = sum(r.get("ssl_errors", 0) for r in success_results)
            print(f"SSL错误总数: {total_ssl}次")

        # 文件大小
        avg_size = sum(r["file_size_kb"] for r in success_results) / len(success_results)
        print(f"平均文件大小: {avg_size:.1f} KB")

    # 错误统计
    failed_results = [r for r in results if not r.get("success")]
    if failed_results:
        print(f"\n失败统计:")
        error_types = {}
        for r in failed_results:
            error = r.get("error", "UNKNOWN")
            error_types[error] = error_types.get(error, 0) + 1

        for error, count in sorted(error_types.items(), key=lambda x: -x[1]):
            print(f"  - {error}: {count}次")

def main():
    output_dir = Path("/Users/a123/.openclaw/workspace-design/images/endpoint-tests/final-comparison")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("三端点公平对比测试")
    print("="*80)
    print(f"分辨率: {TEST_CONFIG['size']}")
    print(f"每端点图片数: {TEST_CONFIG['count']}")
    print(f"提示词: {TEST_CONFIG['prompt']}")
    print(f"输出目录: {output_dir}")
    print("="*80)

    all_results = {}

    # 测试每个端点
    for endpoint_key in ENDPOINTS.keys():
        endpoint = ENDPOINTS[endpoint_key]

        print(f"\n\n{'#'*80}")
        print(f"# 开始测试: {endpoint['name']}")
        print(f"{'#'*80}\n")

        results = []

        for i in range(1, TEST_CONFIG["count"] + 1):
            result = test_single_image(endpoint_key, i, output_dir)
            results.append(result)

            # 每次测试间隔3秒
            if i < TEST_CONFIG["count"]:
                time.sleep(3)

        all_results[endpoint_key] = results

        # 打印当前端点统计
        print_statistics(endpoint_key, results)

        # 端点之间间隔5秒
        print(f"\n等待5秒后测试下一个端点...")
        time.sleep(5)

    # 保存详细结果
    result_file = output_dir / f"comparison-{int(time.time())}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump({
            "config": TEST_CONFIG,
            "results": all_results,
            "timestamp": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存: {result_file}")

    # 最终对比
    print(f"\n\n{'='*80}")
    print("最终对比")
    print(f"{'='*80}\n")

    comparison = []
    for endpoint_key, results in all_results.items():
        endpoint = ENDPOINTS[endpoint_key]
        success = [r for r in results if r.get("success")]
        success_count = len(success)
        total = len(results)
        success_rate = (success_count / total * 100) if total > 0 else 0

        avg_duration = 0
        if success:
            avg_duration = sum(r["total_duration"] for r in success) / len(success)

        comparison.append({
            "endpoint": endpoint["name"],
            "success_rate": success_rate,
            "success_count": success_count,
            "total": total,
            "avg_duration": avg_duration,
        })

    # 按成功率排序
    comparison.sort(key=lambda x: (-x["success_rate"], x["avg_duration"]))

    print(f"{'排名':<6} {'端点':<35} {'成功率':<15} {'平均耗时':<12}")
    print(f"{'-'*80}")

    for i, comp in enumerate(comparison, 1):
        rate_str = f"{comp['success_rate']:.1f}% ({comp['success_count']}/{comp['total']})"
        duration_str = f"{comp['avg_duration']:.2f}秒" if comp['avg_duration'] > 0 else "N/A"

        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        print(f"{medal} {i:<4} {comp['endpoint']:<35} {rate_str:<15} {duration_str:<12}")

    if comparison and comparison[0]["success_rate"] > 0:
        print(f"\n💡 推荐使用: {comparison[0]['endpoint']}")

if __name__ == "__main__":
    main()
