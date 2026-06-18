#!/usr/bin/env python3
"""
RH抠图王 (RunningHub Matting) 接口脚本
使用 RunningHub AI 应用 API（扣 HB 算力币，不扣钱包余额）

WebappId: 2064637853572878337
NodeId: 151 (图像输入节点)
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

try:
    import httpx
    USE_HTTPX = True
except ImportError:
    import urllib.request
    import urllib.parse
    USE_HTTPX = False
    print("[Warning] httpx 未安装，使用 urllib（建议: pip install httpx）", file=sys.stderr)


# RH抠图王配置（AI 应用模式 - 扣 HB）
RH_API_KEY = "442de49dcb5247a285b678a4c70e7499"
RH_WEBAPP_ID = 2064637853572878337
RH_NODE_ID = "151"
RH_FIELD_NAME = "url"

# API 端点
RH_SUBMIT_URL = "https://www.runninghub.cn/task/openapi/ai-app/run"
RH_QUERY_URL = "https://www.runninghub.cn/openapi/v2/query"


def parse_args():
    parser = argparse.ArgumentParser(description="RH抠图王 - 云端高精度抠图服务（AI 应用模式 - 扣 HB）")
    parser.add_argument("--input", required=True, help="输入图片路径（绿幕背景）")
    parser.add_argument("--output", required=True, help="输出图片路径（透明背景）")
    parser.add_argument("--mode", default="auto", help="抠图模式（保留参数兼容性）")
    parser.add_argument("--tolerance", type=int, default=30, help="容差值（保留参数兼容性）")
    parser.add_argument("--max-wait", type=int, default=120, help="最大等待时间（秒）")
    parser.add_argument("--poll-interval", type=int, default=3, help="轮询间隔（秒，默认 3 秒）")
    return parser.parse_args()


async def upload_to_cloudinary(image_path: Path) -> str:
    """
    上传图片到 Cloudinary 获取公共 URL
    """
    try:
        # 尝试导入 runtime_config 中的 upload_to_cloudinary
        script_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(script_dir))
        from runtime_config import upload_to_cloudinary as upload_fn

        print(f"[RH抠图王] 正在上传图片到 Cloudinary: {image_path.name}", file=sys.stderr)
        cloudinary_url = upload_fn(str(image_path))
        print(f"[RH抠图王] ✅ Cloudinary URL: {cloudinary_url}", file=sys.stderr)
        return cloudinary_url
    except Exception as e:
        raise Exception(f"图片上传到 Cloudinary 失败: {e}")


async def call_rh_matting_async(input_path: Path, output_path: Path, max_wait: int = 120, poll_interval: int = 3):
    """
    使用 httpx 异步调用 RH抠图王 AI 应用 API
    """
    # 上传图片到 Cloudinary 获取公共 URL
    image_url = await upload_to_cloudinary(input_path)

    print(f"[RH抠图王] 开始调用 AI 应用（WebappId: {RH_WEBAPP_ID}）", file=sys.stderr)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: 提交抠图任务
        payload = {
            "apiKey": RH_API_KEY,
            "webappId": RH_WEBAPP_ID,
            "nodeInfoList": [
                {
                    "nodeId": RH_NODE_ID,
                    "fieldName": RH_FIELD_NAME,
                    "fieldValue": image_url
                }
            ]
        }
        headers = {
            "Authorization": f"Bearer {RH_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            submit_resp = await client.post(RH_SUBMIT_URL, json=payload, headers=headers)
            if submit_resp.status_code != 200:
                raise Exception(f"提交失败 HTTP {submit_resp.status_code}: {submit_resp.text[:500]}")

            submit_data = submit_resp.json()
            if submit_data.get("code") != 0:
                raise Exception(f"任务创建失败: {submit_data.get('msg', submit_data)}")

            task_id = str(submit_data.get("data", {}).get("taskId"))
            if not task_id:
                raise Exception(f"未获取到 taskId: {submit_data}")

            print(f"[RH抠图王] ✅ 任务已提交，taskId: {task_id}", file=sys.stderr)

        except Exception as e:
            raise Exception(f"任务提交失败: {e}")

        # Step 2: 轮询任务状态
        start_time = time.time()
        query_payload = {"taskId": task_id}

        while time.time() - start_time < max_wait:
            await asyncio.sleep(poll_interval)

            try:
                query_resp = await client.post(RH_QUERY_URL, json=query_payload, headers=headers)
                if query_resp.status_code != 200:
                    print(f"[RH抠图王] 查询失败 HTTP {query_resp.status_code}", file=sys.stderr)
                    continue

                query_data = query_resp.json()
                status = query_data.get("status")

                elapsed = int(time.time() - start_time)
                print(f"[RH抠图王] 状态: {status} (已等待 {elapsed}s)", file=sys.stderr)

                if status == "SUCCESS":
                    results = query_data.get("results", [])
                    if not results:
                        raise Exception("任务成功但无结果图片")

                    result_url = results[0].get("url")
                    print(f"[RH抠图王] ✅ 抠图完成，下载结果: {result_url}", file=sys.stderr)

                    # Step 3: 下载结果图片
                    img_resp = await client.get(result_url, timeout=30)
                    if img_resp.status_code != 200:
                        raise Exception(f"图片下载失败 HTTP {img_resp.status_code}")

                    # 保存到输出路径
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(img_resp.content)

                    print(f"[RH抠图王] ✅ 透明PNG已保存: {output_path}", file=sys.stderr)
                    print(f"[RH抠图王] 💰 扣费方式: HB 算力币（非钱包余额）", file=sys.stderr)
                    return True

                elif status == "FAILED":
                    error_msg = query_data.get("errorMessage", "未知错误")
                    error_code = query_data.get("errorCode", "")
                    raise Exception(f"RH抠图王任务失败 (code: {error_code}): {error_msg}")

            except Exception as e:
                print(f"[RH抠图王] 查询出错: {e}", file=sys.stderr)
                continue

        raise Exception(f"RH抠图王等待超时 ({max_wait}s)")


def call_rh_matting_urllib(input_path: Path, output_path: Path, max_wait: int = 120, poll_interval: int = 3):
    """
    使用 urllib 同步调用 RH抠图王 AI 应用 API（备用）
    """
    import urllib.request
    import urllib.error

    # 上传图片到 Cloudinary 获取公共 URL
    try:
        script_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(script_dir))
        from runtime_config import upload_to_cloudinary as upload_fn

        print(f"[RH抠图王] 正在上传图片到 Cloudinary: {input_path.name}", file=sys.stderr)
        image_url = upload_fn(str(input_path))
        print(f"[RH抠图王] ✅ Cloudinary URL: {image_url}", file=sys.stderr)
    except Exception as e:
        raise Exception(f"图片上传到 Cloudinary 失败: {e}")

    print(f"[RH抠图王] 开始调用 AI 应用（WebappId: {RH_WEBAPP_ID}）", file=sys.stderr)

    # Step 1: 提交抠图任务
    payload = {
        "apiKey": RH_API_KEY,
        "webappId": RH_WEBAPP_ID,
        "nodeInfoList": [
            {
                "nodeId": RH_NODE_ID,
                "fieldName": RH_FIELD_NAME,
                "fieldValue": image_url
            }
        ]
    }
    headers = {
        "Authorization": f"Bearer {RH_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        request = urllib.request.Request(
            RH_SUBMIT_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            submit_data = json.loads(response.read().decode('utf-8'))

        if submit_data.get("code") != 0:
            raise Exception(f"任务创建失败: {submit_data.get('msg', submit_data)}")

        task_id = str(submit_data.get("data", {}).get("taskId"))
        if not task_id:
            raise Exception(f"未获取到 taskId: {submit_data}")

        print(f"[RH抠图王] ✅ 任务已提交，taskId: {task_id}", file=sys.stderr)

    except Exception as e:
        raise Exception(f"任务提交失败: {e}")

    # Step 2: 轮询任务状态
    start_time = time.time()
    query_payload = {"taskId": task_id}

    while time.time() - start_time < max_wait:
        time.sleep(poll_interval)

        try:
            request = urllib.request.Request(
                RH_QUERY_URL,
                data=json.dumps(query_payload).encode('utf-8'),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                query_data = json.loads(response.read().decode('utf-8'))

            status = query_data.get("status")
            elapsed = int(time.time() - start_time)
            print(f"[RH抠图王] 状态: {status} (已等待 {elapsed}s)", file=sys.stderr)

            if status == "SUCCESS":
                results = query_data.get("results", [])
                if not results:
                    raise Exception("任务成功但无结果图片")

                result_url = results[0].get("url")
                print(f"[RH抠图王] ✅ 抠图完成，下载结果: {result_url}", file=sys.stderr)

                # Step 3: 下载结果图片
                with urllib.request.urlopen(result_url, timeout=30) as img_resp:
                    img_data = img_resp.read()

                # 保存到输出路径
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(img_data)

                print(f"[RH抠图王] ✅ 透明PNG已保存: {output_path}", file=sys.stderr)
                print(f"[RH抠图王] 💰 扣费方式: HB 算力币（非钱包余额）", file=sys.stderr)
                return True

            elif status == "FAILED":
                error_msg = query_data.get("errorMessage", "未知错误")
                error_code = query_data.get("errorCode", "")
                raise Exception(f"RH抠图王任务失败 (code: {error_code}): {error_msg}")

        except urllib.error.HTTPError as e:
            print(f"[RH抠图王] 查询出错 HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"[RH抠图王] 查询出错: {e}", file=sys.stderr)
            continue

    raise Exception(f"RH抠图王等待超时 ({max_wait}s)")


def main():
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        print(f"❌ 错误：输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[RH抠图王] 输入: {input_path}", file=sys.stderr)
    print(f"[RH抠图王] 输出: {output_path}", file=sys.stderr)
    print(f"[RH抠图王] 💰 扣费模式: AI 应用 API（扣 HB 算力币）", file=sys.stderr)

    try:
        if USE_HTTPX:
            asyncio.run(call_rh_matting_async(input_path, output_path, args.max_wait, args.poll_interval))
        else:
            call_rh_matting_urllib(input_path, output_path, args.max_wait, args.poll_interval)

        print(f"✅ RH抠图王处理完成: {output_path}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"❌ RH抠图王处理失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
