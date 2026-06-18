#!/usr/bin/env python3
"""
修复版：使用正确的响应格式测试 api.apib.ai
"""

import requests
import json
import time
from pathlib import Path

API_KEY = "sk-W0cZXStLFrEmvitvq9F1bzUfHMwFahchDTMTInSf3qsILsIu"
BASE_URL = "https://api.apib.ai"
MODEL = "gpt-image-2"

TEST_CASES = [
    {"name": "小猫", "prompt": "一只可爱的橙色小猫", "size": "1024x1024"},
    {"name": "咖啡店", "prompt": "现代咖啡店内景", "size": "1024x1024"},
]

def poll_task(task_id, max_polls=60):
    """轮询任务结果 - 使用正确的响应格式"""
    url = f"{BASE_URL}/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    ssl_errors = 0
    start_time = time.time()

    for poll_count in range(1, max_polls + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "data" in data and isinstance(data["data"], dict):
                    task_data = data["data"]
                    status = task_data.get("status", "")
                    progress = task_data.get("progress", 0)

                    if poll_count % 10 == 1:
                        print(f"    轮询 #{poll_count}: {status} {progress}%")

                    if status in ["succeeded", "completed"]:
                        duration = time.time() - start_time

                        # ✅ 修复：使用正确的响应格式
                        if "result" in task_data and "images" in task_data["result"]:
                            images = task_data["result"]["images"]
                            if len(images) > 0 and "url" in images[0]:
                                # url 是数组
                                image_urls = images[0]["url"]
                                image_url = image_urls[0] if isinstance(image_urls, list) else image_urls

                                return {
                                    "success": True,
                                    "duration": duration,
                                    "poll_count": poll_count,
                                    "ssl_errors": ssl_errors,
                                    "url": image_url,
                                    "expires_at": images[0].get("expires_at"),
                                }

                        # 没有找到图片URL
                        return {
                            "success": False,
                            "error": "NO_IMAGE_URL",
                            "duration": duration,
                            "poll_count": poll_count,
                            "ssl_errors": ssl_errors,
                        }

                    elif status == "failed":
                        return {
                            "success": False,
                            "error": "TASK_FAILED",
                            "duration": time.time() - start_time,
                            "poll_count": poll_count,
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
        "duration": time.time() - start_time,
        "poll_count": max_polls,
        "ssl_errors": ssl_errors,
    }

def test_case(test_case, output_dir):
    """测试一个用例"""
    print(f"\n{'='*60}")
    print(f"测试: {test_case['name']}")
    print(f"{'='*60}")

    # 提交任务
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

    try:
        print(f"  [1] 提交任务...", end=" ", flush=True)
        start = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        submit_time = time.time() - start

        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP_{response.status_code}"}

        data = response.json()
        task_id = data["data"][0]["task_id"]
        print(f"✅ {submit_time:.2f}秒")
        print(f"      任务ID: {task_id}")

        # 轮询
        print(f"  [2] 等待生成...")
        result = poll_task(task_id)

        if result["success"]:
            print(f"  [3] ✅ 成功!")
            print(f"      总耗时: {result['duration']:.2f}秒")
            print(f"      轮询: {result['poll_count']}次")
            print(f"      SSL错误: {result['ssl_errors']}次")

            # 下载图片
            print(f"  [4] 下载图片...", end=" ", flush=True)
            img_response = requests.get(result["url"], timeout=30)

            if img_response.status_code == 200:
                filename = f"apib_fixed_{test_case['size']}_{int(time.time())}.png"
                filepath = output_dir / filename

                with open(filepath, "wb") as f:
                    f.write(img_response.content)

                size_kb = len(img_response.content) / 1024
                print(f"✅ {size_kb:.1f} KB")

                result["file_size_kb"] = size_kb
                result["filepath"] = str(filepath)
            else:
                print(f"❌ HTTP {img_response.status_code}")

            return result
        else:
            print(f"  [3] ❌ 失败: {result.get('error', '未知')}")
            print(f"      耗时: {result['duration']:.2f}秒")
            print(f"      SSL错误: {result['ssl_errors']}次")
            return result

    except requests.exceptions.SSLError:
        print(f"❌ SSL错误")
        return {"success": False, "error": "SSL_ERROR"}
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        return {"success": False, "error": str(e)[:100]}

def main():
    output_dir = Path("/Users/a123/.openclaw/workspace-design/images/endpoint-tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("api.apib.ai 修复版测试（正确的响应格式）")
    print("="*60)

    results = []
    for tc in TEST_CASES:
        result = test_case(tc, output_dir)
        results.append(result)
        time.sleep(3)

    # 统计
    print(f"\n{'='*60}")
    print("测试结果")
    print(f"{'='*60}\n")

    success = [r for r in results if r.get("success")]
    success_count = len(success)
    total = len(results)

    print(f"成功率: {success_count}/{total} ({success_count/total*100:.0f}%)")

    if success:
        avg_duration = sum(r["duration"] for r in success) / len(success)
        total_ssl = sum(r["ssl_errors"] for r in success)

        print(f"平均耗时: {avg_duration:.2f}秒")
        print(f"SSL错误: {total_ssl}次")

        if success_count == total:
            print(f"\n🎉 所有测试通过！api.apib.ai 可以正常使用了！")

if __name__ == "__main__":
    main()
