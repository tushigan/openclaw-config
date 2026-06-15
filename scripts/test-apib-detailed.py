#!/usr/bin/env python3
"""
详细测试 api.apib.ai 端点，记录所有错误类型和原因
模型：gpt-image-2
"""

import requests
import json
import time
from datetime import datetime

API_KEY = "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu"
BASE_URL = "https://api.apib.ai"
MODEL = "gpt-image-2"

TEST_CASES = [
    {"name": "测试1", "prompt": "一只可爱的橙色小猫", "size": "1024x1024"},
    {"name": "测试2", "prompt": "现代咖啡店内景", "size": "1024x1024"},
    {"name": "测试3", "prompt": "产品摄影白底", "size": "1024x1024"},
]

def log(msg, level="INFO"):
    """带时间戳的日志"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {msg}")

def submit_task(test_case):
    """提交生图任务"""
    url = f"{BASE_URL}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "prompt": test_case["prompt"],
        "size": test_case["size"],
        "n": 1,
    }

    log(f"提交任务: {test_case['name']}", "INFO")
    log(f"  模型: {MODEL}", "INFO")
    log(f"  尺寸: {test_case['size']}", "INFO")
    log(f"  提示词: {test_case['prompt']}", "INFO")

    try:
        start = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        duration = time.time() - start

        log(f"  提交耗时: {duration:.2f}秒", "INFO")
        log(f"  HTTP状态: {response.status_code}", "INFO")

        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                task_id = data["data"][0].get("task_id")
                log(f"  ✅ 任务已提交: {task_id}", "SUCCESS")
                return {"success": True, "task_id": task_id, "submit_time": duration}
            else:
                log(f"  ❌ 响应格式错误: {json.dumps(data, ensure_ascii=False)}", "ERROR")
                return {"success": False, "error_type": "RESPONSE_FORMAT_ERROR", "response": data}
        else:
            error_text = response.text[:500]
            log(f"  ❌ HTTP错误 {response.status_code}: {error_text}", "ERROR")
            return {"success": False, "error_type": f"HTTP_{response.status_code}", "error": error_text}

    except requests.exceptions.SSLError as e:
        log(f"  ❌ SSL错误: {str(e)[:200]}", "ERROR")
        return {"success": False, "error_type": "SSL_ERROR", "error": str(e)[:200]}
    except requests.exceptions.Timeout:
        log(f"  ❌ 超时（30秒）", "ERROR")
        return {"success": False, "error_type": "TIMEOUT", "error": "Request timeout"}
    except requests.exceptions.ConnectionError as e:
        log(f"  ❌ 连接错误: {str(e)[:200]}", "ERROR")
        return {"success": False, "error_type": "CONNECTION_ERROR", "error": str(e)[:200]}
    except Exception as e:
        log(f"  ❌ 未知错误: {str(e)[:200]}", "ERROR")
        return {"success": False, "error_type": "UNKNOWN_ERROR", "error": str(e)[:200]}

def poll_task(task_id, max_polls=60):
    """轮询任务结果"""
    url = f"{BASE_URL}/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    log(f"开始轮询任务: {task_id}", "INFO")

    poll_count = 0
    ssl_errors = 0
    timeout_errors = 0
    other_errors = 0
    start_time = time.time()

    while poll_count < max_polls:
        poll_count += 1

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "data" in data and isinstance(data["data"], dict):
                    task_data = data["data"]
                    status = task_data.get("status", "unknown")
                    progress = task_data.get("progress", 0)

                    if poll_count % 5 == 1:  # 每5次打印一次
                        log(f"  轮询 #{poll_count}: 状态={status}, 进度={progress}%", "INFO")

                    if status in ["succeeded", "completed"]:
                        duration = time.time() - start_time
                        log(f"  ✅ 任务完成! 耗时 {duration:.2f}秒", "SUCCESS")
                        log(f"  统计: 轮询{poll_count}次, SSL错误{ssl_errors}次, 超时{timeout_errors}次", "INFO")

                        image_url = task_data.get("url", "")
                        if image_url:
                            return {
                                "success": True,
                                "duration": duration,
                                "poll_count": poll_count,
                                "ssl_errors": ssl_errors,
                                "timeout_errors": timeout_errors,
                                "url": image_url,
                            }
                        else:
                            log(f"  ❌ 任务完成但没有图片URL", "ERROR")
                            return {
                                "success": False,
                                "error_type": "NO_IMAGE_URL",
                                "poll_count": poll_count,
                                "ssl_errors": ssl_errors,
                            }

                    elif status == "failed":
                        log(f"  ❌ 任务失败", "ERROR")
                        return {
                            "success": False,
                            "error_type": "TASK_FAILED",
                            "poll_count": poll_count,
                            "ssl_errors": ssl_errors,
                        }

                else:
                    log(f"  ⚠️  轮询 #{poll_count}: 响应格式异常", "WARN")

            elif response.status_code == 404:
                log(f"  ⚠️  轮询 #{poll_count}: HTTP 404 (任务不存在)", "WARN")
            else:
                log(f"  ⚠️  轮询 #{poll_count}: HTTP {response.status_code}", "WARN")

            time.sleep(2)

        except requests.exceptions.SSLError as e:
            ssl_errors += 1
            if ssl_errors <= 3:
                log(f"  ⚠️  轮询 #{poll_count}: SSL错误 #{ssl_errors}", "WARN")
            time.sleep(2)

        except requests.exceptions.Timeout:
            timeout_errors += 1
            if timeout_errors <= 3:
                log(f"  ⚠️  轮询 #{poll_count}: 超时 #{timeout_errors}", "WARN")
            time.sleep(2)

        except Exception as e:
            other_errors += 1
            if other_errors <= 3:
                log(f"  ⚠️  轮询 #{poll_count}: 其他错误 {str(e)[:100]}", "WARN")
            time.sleep(2)

    # 轮询超时
    duration = time.time() - start_time
    log(f"  ❌ 轮询超时 ({duration:.2f}秒)", "ERROR")
    log(f"  统计: 轮询{poll_count}次, SSL错误{ssl_errors}次, 超时{timeout_errors}次", "INFO")

    return {
        "success": False,
        "error_type": "POLL_TIMEOUT",
        "duration": duration,
        "poll_count": poll_count,
        "ssl_errors": ssl_errors,
        "timeout_errors": timeout_errors,
    }

def main():
    print("="*80)
    print(f"api.apib.ai 端点详细测试")
    print(f"模型: {MODEL}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = []

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}/{len(TEST_CASES)}: {test_case['name']}")
        print(f"{'='*80}")

        # 提交任务
        submit_result = submit_task(test_case)

        if submit_result["success"]:
            task_id = submit_result["task_id"]

            # 轮询结果
            poll_result = poll_task(task_id)

            result = {
                "test_case": test_case["name"],
                "submit": submit_result,
                "poll": poll_result,
                "overall_success": poll_result["success"],
            }
        else:
            result = {
                "test_case": test_case["name"],
                "submit": submit_result,
                "poll": None,
                "overall_success": False,
            }

        results.append(result)

        # 间隔
        if i < len(TEST_CASES):
            log("等待3秒后继续...", "INFO")
            time.sleep(3)

    # 统计
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}\n")

    success_count = sum(1 for r in results if r["overall_success"])
    total_count = len(results)

    print(f"成功率: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)\n")

    # 错误统计
    error_types = {}
    for r in results:
        if not r["overall_success"]:
            if r["submit"]["success"]:
                # 轮询阶段失败
                error_type = r["poll"]["error_type"]
            else:
                # 提交阶段失败
                error_type = r["submit"]["error_type"]

            error_types[error_type] = error_types.get(error_type, 0) + 1

    if error_types:
        print("错误类型统计:")
        for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
            print(f"  - {error_type}: {count} 次")

    # SSL错误统计
    total_ssl_errors = sum(r["poll"]["ssl_errors"] for r in results if r["poll"] and "ssl_errors" in r["poll"])
    if total_ssl_errors > 0:
        print(f"\nSSL 错误总数: {total_ssl_errors} 次")

    # 保存详细结果
    output_file = f"/Users/a123/.openclaw/workspace-design/images/endpoint-tests/apib-详细测试-{int(time.time())}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存: {output_file}")

if __name__ == "__main__":
    main()
