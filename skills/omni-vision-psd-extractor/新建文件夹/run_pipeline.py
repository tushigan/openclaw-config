#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poster-2k-psd-splitter — 主管线脚本
====================================
整合海报分层 PSD 的全部步骤：
  0. 环境准备
  1. 获取并缩放原图至 2K
  2. 上传原图到 Cloudinary 获取 URL
  3. Gemini 3.1 Flash 双提取（背景 + 前景）
  4. RH 抠图王前景去底
  5. 连通域切割前景元素
  6. 组装 PSD 并分卷压缩

用法示例:
  python run_pipeline.py \
    --source "https://example.com/poster.jpg" \
    --bg-prompt "只保留背景，移除所有人物和文字" \
    --fg-prompt "只保留前景人物，背景填充为纯白色"
"""

import os
import sys
import json

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import time
import base64
import argparse
import subprocess
import struct
import io
import zipfile
import random
import urllib.request
import urllib.error
from pathlib import Path

# ──────────────────────────────────────────────
# 全局常量
# ──────────────────────────────────────────────

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)

CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dc6kesgub/image/upload"
CLOUDINARY_PRESET = "my_n8n_upload"

RH_RUN_URL = "https://www.runninghub.cn/task/openapi/ai-app/run"
RH_QUERY_URL = "https://www.runninghub.cn/openapi/v2/query"
RH_POLL_INTERVAL = 3     # 秒
RH_POLL_MAX_TRIES = 40   # 最多 120 秒

GEMINI_TIMEOUT = 240      # Gemini API 超时秒数


# ──────────────────────────────────────────────
# Step 0: 环境准备
# ──────────────────────────────────────────────

def load_env_file():
    """从技能根目录向上查找 .env 并加载为环境变量"""
    search = SKILL_DIR
    for _ in range(5):
        env_path = os.path.join(search, '.env')
        if os.path.isfile(env_path):
            print(f"[环境] 加载 .env: {env_path}")
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, _, val = line.partition('=')
                    key, val = key.strip(), val.strip().strip('"').strip("'")
                    if key and val:
                        os.environ.setdefault(key, val)
            return
        search = os.path.dirname(search)
    print("[环境] 未找到 .env 文件，使用环境变量和默认值")


def get_config():
    """读取 API 配置，返回 dict"""
    load_env_file()
    cfg = {
        'GEMINI_API_KEY': os.environ.get('OPENCLAW_BOUND_API_KEY', ''),
        'GEMINI_BASE_URL': os.environ.get('OPENCLAW_BOUND_BASE_URL', 'https://s.lconai.com/').rstrip('/'),
        'GEMINI_MODEL': os.environ.get('OPENCLAW_BOUND_MODEL_ID', 'gemini-3.1-flash-image-preview'),
        'RH_API_KEY': os.environ.get('RUNNINGHUB_API_KEY', '4300704c41e344cf920bc83e9ceb65cc'),
        'RH_WEBAPP_ID': os.environ.get('RH_WEBAPP_ID', '2064637853572878337'),
    }
    if not cfg['GEMINI_API_KEY']:
        print("[错误] 未设置 GEMINI_API_KEY / OPENCLAW_BOUND_API_KEY", file=sys.stderr)
        sys.exit(1)
    # 打印摘要（隐藏密钥中间部分）
    masked_key = cfg['GEMINI_API_KEY'][:6] + '***' + cfg['GEMINI_API_KEY'][-4:]
    print(f"[配置] Gemini  → {cfg['GEMINI_BASE_URL']}  模型={cfg['GEMINI_MODEL']}  key={masked_key}")
    print(f"[配置] RH抠图  → webapp={cfg['RH_WEBAPP_ID']}")
    return cfg


# ──────────────────────────────────────────────
# Step 1: 获取并缩放原图
# ──────────────────────────────────────────────

def fetch_and_scale(source, out_dir, max_edge):
    """下载 / 读取原图并缩放至 max_edge，返回保存路径和 (w, h)"""
    from PIL import Image

    # 获取图片字节
    if source.startswith('http://') or source.startswith('https://'):
        print(f"[Step1] 正在下载原图: {source}")
        req = urllib.request.Request(source, headers={'User-Agent': 'poster-pipeline/1.0'})
        resp = urllib.request.urlopen(req, timeout=60)
        img_bytes = resp.read()
        img = Image.open(io.BytesIO(img_bytes))
    else:
        local_path = os.path.abspath(source)
        if not os.path.isfile(local_path):
            print(f"[错误] 本地文件不存在: {local_path}", file=sys.stderr)
            sys.exit(1)
        print(f"[Step1] 读取本地文件: {local_path}")
        img = Image.open(local_path)

    orig_w, orig_h = img.size
    print(f"[Step1] 原始尺寸: {orig_w}×{orig_h}")

    # 缩放
    scale = max_edge / max(orig_w, orig_h)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)

    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA')

    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    save_path = os.path.join(out_dir, '00_source_2k.png')
    img_resized.save(save_path, 'PNG')
    print(f"[Step1] 缩放后尺寸: {new_w}×{new_h}  已保存: {save_path}")

    return save_path, new_w, new_h


# ──────────────────────────────────────────────
# Step 2: Cloudinary 上传
# ──────────────────────────────────────────────

def upload_to_cloudinary(file_path):
    """将本地图片上传到 Cloudinary，返回 secure_url"""
    boundary = '----WebKitFormBoundary' + ''.join(
        random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(16)
    )

    with open(file_path, 'rb') as f:
        file_content = f.read()

    filename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.webp': 'image/webp', '.gif': 'image/gif',
    }
    file_mime = mime_map.get(ext, 'image/png')

    body = bytearray()
    # upload_preset 字段
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(b'Content-Disposition: form-data; name="upload_preset"\r\n\r\n')
    body.extend(f'{CLOUDINARY_PRESET}\r\n'.encode('utf-8'))
    # file 字段
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode('utf-8'))
    body.extend(f'Content-Type: {file_mime}\r\n\r\n'.encode('utf-8'))
    body.extend(file_content)
    body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

    req = urllib.request.Request(CLOUDINARY_URL, data=bytes(body))
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode('utf-8'))
        url = data.get('secure_url')
        if not url:
            print(f"[错误] Cloudinary 未返回 secure_url: {data}", file=sys.stderr)
            sys.exit(1)
        return url
    except urllib.error.URLError as e:
        print(f"[错误] Cloudinary 上传失败: {e}", file=sys.stderr)
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8', errors='replace'), file=sys.stderr)
        sys.exit(1)


# ──────────────────────────────────────────────
# Step 2.5: VLM 自动视觉分析（生成 BgPrompt / FgPrompt）
# ──────────────────────────────────────────────

VLM_ANALYSIS_PROMPT = """你是一个专业的海报视觉分析师。请仔细分析这张海报图片，识别出背景和前景元素。

你必须严格输出以下 JSON 格式，不要输出任何多余文字：

{
  "background": "详细描述背景是什么（颜色、渐变、场景、材质、氛围等）",
  "foreground_elements": "列出所有前景元素，用中文逗号分隔（如：人物,文字标题,Logo,装饰图标,气球等）",
  "lighting": "描述光影、色温和氛围特征"
}"""


def auto_analyze_image(cfg, image_url, vlm_model='gpt-5.4'):
    """
    使用 VLM（视觉语言模型）自动分析海报图片，
    返回自动生成的 (bg_prompt, fg_prompt)。
    """
    base_url = cfg['GEMINI_BASE_URL'].rstrip('/')
    api_key = cfg['GEMINI_API_KEY']

    # 使用 OpenAI 兼容的 Chat Completions 格式
    api_url = f"{base_url}/v1/chat/completions"

    payload = {
        "model": vlm_model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": VLM_ANALYSIS_PROMPT}
            ]
        }],
        "max_tokens": 1024,
        "temperature": 0.3,
    }

    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(api_url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {api_key}')

    print(f"[自动分析] 正在调用 VLM ({vlm_model}) 分析海报内容...")

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        print(f"[错误] VLM API HTTP {e.code}: {err_body[:500]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[错误] VLM API 请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 解析 OpenAI 格式响应
    choices = data.get('choices', [])
    if not choices:
        print(f"[错误] VLM 未返回结果: {json.dumps(data, ensure_ascii=False)[:500]}", file=sys.stderr)
        sys.exit(1)

    raw_text = choices[0].get('message', {}).get('content', '')
    print(f"[自动分析] VLM 原始返回:\n{raw_text}")

    # 提取 JSON（兼容 markdown 代码块包裹）
    json_text = raw_text.strip()
    if '```' in json_text:
        # 去掉 ```json ... ``` 包裹
        import re
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', json_text, re.DOTALL)
        if m:
            json_text = m.group(1).strip()

    try:
        analysis = json.loads(json_text)
    except json.JSONDecodeError:
        print(f"[警告] VLM 返回非法 JSON，使用通用提示词")
        analysis = {
            'background': '海报背景',
            'foreground_elements': '前景元素',
            'lighting': '标准光照',
        }

    bg_desc = analysis.get('background', '海报背景')
    fg_elems = analysis.get('foreground_elements', '前景元素')
    lighting = analysis.get('lighting', '')

    # 组装 BgPrompt
    bg_prompt = (
        f"【极其重要：严格保持原图中的背景结构、光影和色彩不变，仅智能脑补被移除的前景区域。"
        f"强制锁定原图光影质感：{lighting}】"
        f"将图片中的背景完整提取出来。背景是{bg_desc}。"
        f"需要将{fg_elems}全部剔除，只保留纯净的背景。"
        f"被剔除区域要自然填充，与周围背景无缝融合。"
    )

    # 组装 FgPrompt
    fg_prompt = (
        f"【极其重要：将背景全部填充为纯白色(#FFFFFF)，只保留前景元素！】"
        f"将图片中除了背景之外的所有前景元素提取出来，包括{fg_elems}。"
        f"背景区域必须全部变为纯白色，前景元素保持原始质感和细节不变。"
    )

    print(f"[自动分析] ✅ 已自动生成提示词")
    print(f"  BgPrompt: {bg_prompt[:80]}...")
    print(f"  FgPrompt: {fg_prompt[:80]}...")

    return bg_prompt, fg_prompt


# ──────────────────────────────────────────────
# Step 3: Gemini 3.1 Flash 双提取
# ──────────────────────────────────────────────

def calc_aspect_ratio(w, h):
    """从宽高计算最接近的标准宽高比字符串"""
    ratio = w / h
    candidates = [
        (1.0, '1:1'), (4 / 3, '4:3'), (3 / 4, '3:4'),
        (16 / 9, '16:9'), (9 / 16, '9:16'), (3 / 2, '3:2'),
        (2 / 3, '2:3'), (16 / 10, '16:10'), (10 / 16, '10:16'),
    ]
    best = min(candidates, key=lambda x: abs(x[0] - ratio))
    return best[1]


def gemini_image_generate(cfg, image_url, prompt, canvas_w, canvas_h):
    """
    调用 Gemini Native 协议进行图片生成/编辑，返回 PIL.Image。
    使用 responseModalities=IMAGE 模式。
    """
    from PIL import Image as PILImage

    aspect = calc_aspect_ratio(canvas_w, canvas_h)
    api_url = (
        f"{cfg['GEMINI_BASE_URL']}/v1beta/models/{cfg['GEMINI_MODEL']}:generateContent"
        f"?key={cfg['GEMINI_API_KEY']}"
    )

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": f"{image_url} {prompt}"}
            ]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect,
                "imageSize": "2K"
            }
        }
    }

    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(api_url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')

    try:
        resp = urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT)
        data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        print(f"[错误] Gemini API HTTP {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[错误] Gemini API 请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 解析响应
    candidates = data.get('candidates', [])
    if not candidates:
        print(f"[错误] Gemini 未返回候选结果: {json.dumps(data, ensure_ascii=False)[:500]}", file=sys.stderr)
        sys.exit(1)

    parts = candidates[0].get('content', {}).get('parts', [])
    if not parts:
        print(f"[错误] Gemini 候选结果无 parts: {json.dumps(candidates[0], ensure_ascii=False)[:500]}", file=sys.stderr)
        sys.exit(1)

    inline_data = parts[0].get('inlineData')
    if not inline_data:
        # 可能返回了文本而非图片
        text_resp = parts[0].get('text', '')
        print(f"[警告] Gemini 返回文本而非图片: {text_resp[:300]}", file=sys.stderr)
        print("[错误] 无法获取图片数据，请检查提示词或模型配置", file=sys.stderr)
        sys.exit(1)

    b64_data = inline_data['data']
    img_bytes = base64.b64decode(b64_data)
    img = PILImage.open(io.BytesIO(img_bytes))
    return img


def extract_bg_fg(cfg, source_url, bg_prompt, fg_prompt, canvas_w, canvas_h, out_dir):
    """执行背景和前景双提取，返回 (bg_path, fg_raw_path)"""

    # 3.1 背景提取
    print(f"[Step3.1] 正在提取背景...")
    print(f"  提示词: {bg_prompt}")
    bg_img = gemini_image_generate(cfg, source_url, bg_prompt, canvas_w, canvas_h)
    bg_path = os.path.join(out_dir, '01_background.png')
    bg_img.save(bg_path, 'PNG')
    print(f"[Step3.1] 背景已保存: {bg_path}  尺寸={bg_img.size}")

    # 3.2 前景提取
    print(f"[Step3.2] 正在提取前景...")
    print(f"  提示词: {fg_prompt}")
    fg_img = gemini_image_generate(cfg, source_url, fg_prompt, canvas_w, canvas_h)
    fg_raw_path = os.path.join(out_dir, '02_foreground_raw.png')
    fg_img.save(fg_raw_path, 'PNG')
    print(f"[Step3.2] 前景已保存: {fg_raw_path}  尺寸={fg_img.size}")

    return bg_path, fg_raw_path


# ──────────────────────────────────────────────
# Step 4: RH 抠图王 — 前景去底
# ──────────────────────────────────────────────

def rh_matting(cfg, fg_raw_path, out_dir):
    """将前景 raw 上传 Cloudinary → 调用 RH 抠图王 → 下载透明 PNG"""

    # 4.1 上传前景到 Cloudinary
    print("[Step4] 正在上传前景到 Cloudinary...")
    fg_url = upload_to_cloudinary(fg_raw_path)
    print(f"[Step4] 前景 URL: {fg_url}")

    # 4.2 提交 RH 抠图任务
    webapp_id_raw = cfg['RH_WEBAPP_ID']
    # RH API 要求 webappId 为数字类型
    try:
        webapp_id = int(webapp_id_raw)
    except ValueError:
        webapp_id = webapp_id_raw

    run_payload = {
        "apiKey": cfg['RH_API_KEY'],
        "webappId": webapp_id,
        "nodeInfoList": [{
            "nodeId": "151",
            "fieldName": "url",
            "fieldValue": fg_url
        }]
    }

    body = json.dumps(run_payload).encode('utf-8')
    req = urllib.request.Request(RH_RUN_URL, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[错误] RH 提交任务失败: {e}", file=sys.stderr)
        sys.exit(1)

    task_id = data.get('data', {}).get('taskId') if isinstance(data.get('data'), dict) else data.get('taskId')
    if not task_id:
        # 兼容多种响应格式
        task_id = data.get('data') if isinstance(data.get('data'), str) else None
    if not task_id:
        print(f"[错误] RH 未返回 taskId: {json.dumps(data, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    print(f"[Step4] RH 任务已提交，taskId={task_id}")

    # 4.3 轮询等待完成
    query_payload = {
        "taskId": task_id,
        "apiKey": cfg['RH_API_KEY']
    }

    for attempt in range(1, RH_POLL_MAX_TRIES + 1):
        time.sleep(RH_POLL_INTERVAL)

        body = json.dumps(query_payload).encode('utf-8')
        req = urllib.request.Request(RH_QUERY_URL, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')

        try:
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode('utf-8'))
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"[Step4] 轮询 #{attempt} 网络错误: {e}")
            continue

        status = result.get('data', {}).get('taskStatus') or result.get('status', '')
        print(f"[Step4] 轮询 #{attempt}/{RH_POLL_MAX_TRIES}  状态={status}")

        if status == 'SUCCESS':
            # 提取结果 URL
            results = result.get('data', {}).get('results', [])
            if not results:
                print(f"[错误] RH 成功但无结果: {json.dumps(result, ensure_ascii=False)[:500]}", file=sys.stderr)
                sys.exit(1)

            result_url = results[0].get('url') or results[0].get('fileUrl', '')
            if not result_url:
                print(f"[错误] RH 结果中无 URL: {results[0]}", file=sys.stderr)
                sys.exit(1)

            # 下载透明 PNG
            print(f"[Step4] 正在下载抠图结果: {result_url}")
            dl_req = urllib.request.Request(result_url, headers={'User-Agent': 'poster-pipeline/1.0'})
            dl_resp = urllib.request.urlopen(dl_req, timeout=60)
            matted_bytes = dl_resp.read()

            matted_path = os.path.join(out_dir, '03_foreground_matted.png')
            with open(matted_path, 'wb') as f:
                f.write(matted_bytes)

            print(f"[Step4] 抠图结果已保存: {matted_path}")
            return matted_path

        elif status in ('FAILED', 'TIMEOUT', 'ERROR'):
            print(f"[错误] RH 任务失败: status={status}", file=sys.stderr)
            print(f"  详情: {json.dumps(result, ensure_ascii=False)[:500]}", file=sys.stderr)
            sys.exit(1)

    print(f"[错误] RH 轮询超时（{RH_POLL_MAX_TRIES * RH_POLL_INTERVAL}秒）", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────
# Step 5: 连通域切割 — 前景元素分离
# ──────────────────────────────────────────────

def split_elements(matted_path, out_dir, min_area_ratio=0.0005):
    """
    使用 OpenCV 将透明 PNG 按连通域分割为独立元素。
    如果 cv2 未安装，返回整张前景作为单一图层。
    """
    from PIL import Image as PILImage

    try:
        import cv2
        import numpy as np
    except ImportError:
        print("[警告] 未安装 opencv-python，跳过连通域切割，将整张前景作为单一图层")
        img = PILImage.open(matted_path)
        elem_dir = os.path.join(out_dir, 'elements')
        os.makedirs(elem_dir, exist_ok=True)
        elem_path = os.path.join(elem_dir, 'elem_001.png')
        img.save(elem_path, 'PNG')
        return [{
            'path': elem_path,
            'left': 0,
            'top': 0,
            'width': img.width,
            'height': img.height,
        }]

    print("[Step5] 正在进行连通域分析...")

    img = PILImage.open(matted_path).convert('RGBA')
    arr = np.array(img)
    alpha = arr[:, :, 3]

    # Alpha → 二值图
    _, binary = cv2.threshold(alpha, 15, 255, cv2.THRESH_BINARY)

    # 形态学开运算 — 断开微弱连接
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # 小闭合修复
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close)

    # 连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)

    total_area = img.width * img.height
    elem_dir = os.path.join(out_dir, 'elements')
    os.makedirs(elem_dir, exist_ok=True)
    elements = []
    elem_idx = 0

    for i in range(1, num_labels):  # 跳过背景 label 0
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area_ratio * total_area:
            continue  # 过滤噪点

        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        # 膨胀恢复开运算切掉的边缘
        mask_i = (labels == i).astype(np.uint8) * 255
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (12, 12))
        mask_dilated = cv2.dilate(mask_i, kernel_dilate)
        # 与原始 alpha 取交集
        mask_final = cv2.bitwise_and(mask_dilated, alpha)

        # 裁切元素
        crop = arr[y:y + h, x:x + w].copy()
        mask_crop = mask_final[y:y + h, x:x + w]
        crop[:, :, 3] = np.minimum(crop[:, :, 3], mask_crop)  # 应用 mask

        elem_img = PILImage.fromarray(crop, 'RGBA')
        elem_idx += 1
        elem_path = os.path.join(elem_dir, f'elem_{elem_idx:03d}.png')
        elem_img.save(elem_path, 'PNG')

        elements.append({
            'path': elem_path,
            'left': int(x),
            'top': int(y),
            'width': int(w),
            'height': int(h),
        })

    print(f"[Step5] 共检测到 {num_labels - 1} 个连通域，保留 {len(elements)} 个有效元素")

    # 如果没有有效元素，回退为整张前景
    if not elements:
        print("[Step5] 未检测到有效元素，回退为整张前景作为单一图层")
        elem_path = os.path.join(elem_dir, 'elem_001.png')
        img.save(elem_path, 'PNG')
        elements.append({
            'path': elem_path,
            'left': 0,
            'top': 0,
            'width': img.width,
            'height': img.height,
        })

    return elements


# ──────────────────────────────────────────────
# Step 6: 组装 PSD 并分卷压缩
# ──────────────────────────────────────────────

def build_scene_json(canvas_w, canvas_h, source_2k_path, bg_path, elements, out_dir):
    """生成 scene.json 供 Node.js PSD 构建器使用，返回 json 路径"""
    image_layers = [
        {
            'group': '00_ORIGINAL',
            'name': 'Original Poster (Reference)',
            'path': os.path.abspath(source_2k_path),
            'left': 0, 'top': 0,
            'opacity': 255, 'hidden': True,
            'crop_to_alpha': False,
        },
        {
            'group': '01_BG',
            'name': 'Clean Background',
            'path': os.path.abspath(bg_path),
            'left': 0, 'top': 0,
            'opacity': 255, 'hidden': False,
            'crop_to_alpha': False,
        },
    ]

    for idx, elem in enumerate(elements):
        image_layers.append({
            'group': '05_FOREGROUND',
            'name': f'Element {idx + 1}',
            'path': os.path.abspath(elem['path']),
            'left': elem['left'],
            'top': elem['top'],
            'opacity': 255,
            'hidden': False,
            'crop_to_alpha': True,
        })

    scene = {
        'width': canvas_w,
        'height': canvas_h,
        'preview_path': os.path.abspath(source_2k_path),
        'group_order': ['00_ORIGINAL', '01_BG', '05_FOREGROUND'],
        'image_layers': image_layers,
    }

    scene_path = os.path.join(out_dir, 'scene.json')
    with open(scene_path, 'w', encoding='utf-8') as f:
        json.dump(scene, f, ensure_ascii=False, indent=2)

    print(f"[Step6.1] scene.json 已生成: {scene_path}")
    return scene_path


def invoke_psd_builder(scene_json_path, psd_output_path):
    """调用 Node.js PSD 构建器"""
    builder_path = os.path.join(SCRIPTS_DIR, 'build_psd.mjs')

    if not os.path.isfile(builder_path):
        print(f"[警告] 未找到 PSD 构建器: {builder_path}", file=sys.stderr)
        print("[警告] 跳过 PSD 组装步骤，请确保 build_psd.mjs 存在", file=sys.stderr)
        return False

    print(f"[Step6.2] 正在调用 PSD 构建器...")
    try:
        subprocess.run(
            ['node', builder_path, '--scene', scene_json_path, '--output', psd_output_path],
            check=True,
        )
        print(f"[Step6.2] PSD 已生成: {psd_output_path}")
        return True
    except FileNotFoundError:
        print("[错误] Node.js 未安装或不在 PATH 中", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"[错误] PSD 构建器执行失败 (exit={e.returncode})", file=sys.stderr)
        return False


def volume_compress(psd_path, max_bytes, out_dir):
    """将 PSD 文件分卷压缩，返回分卷文件路径列表"""
    psd_name = os.path.basename(psd_path)
    zip_base = os.path.join(out_dir, f'{psd_name}.zip')

    # 先创建完整的 zip
    with zipfile.ZipFile(zip_base, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(psd_path, psd_name)

    zip_size = os.path.getsize(zip_base)
    if zip_size <= max_bytes:
        print(f'[分卷压缩] PSD 压缩后 {zip_size / 1024 / 1024:.1f}MB，无需分卷')
        return [zip_base]

    # 需要分卷：读取完整 zip 然后拆分
    with open(zip_base, 'rb') as f:
        data = f.read()

    os.remove(zip_base)

    volumes = []
    part = 1
    for offset in range(0, len(data), max_bytes):
        chunk = data[offset:offset + max_bytes]
        vol_path = f'{zip_base}.{part:03d}'
        with open(vol_path, 'wb') as vf:
            vf.write(chunk)
        volumes.append(vol_path)
        part += 1

    print(f'[分卷压缩] 已分为 {len(volumes)} 个分卷（每卷 ≤{max_bytes / 1024 / 1024:.0f}MB）')
    return volumes


# ──────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='海报分层 PSD 主管线 — 一键生成分层 PSD',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--source', required=True, help='原图来源（URL 或本地路径）')
    parser.add_argument('--bg-prompt', default=None, help='背景提取提示词（可选，不提供则自动VLM分析）')
    parser.add_argument('--fg-prompt', default=None, help='前景提取提示词（可选，不提供则自动VLM分析）')
    parser.add_argument('--out-dir', default=None, help='输出目录（默认 ~/.openclaw/workspace/poster-psd-out）')
    parser.add_argument('--conv-id', default=None, help='会话 ID（用于 Antigravity 图片查找）')
    parser.add_argument('--max-edge', type=int, default=2048, help='最长边像素数（默认 2048）')
    parser.add_argument('--volume-size', type=int, default=30, help='分卷大小 MB（默认 30）')
    parser.add_argument('--vlm-model', default='gpt-5.4', help='VLM 视觉分析模型（默认 gpt-5.4）')
    args = parser.parse_args()

    # 确定输出目录
    if args.out_dir:
        out_dir = os.path.abspath(args.out_dir)
    else:
        out_dir = os.path.join(os.path.expanduser('~'), '.openclaw', 'workspace', 'poster-psd-out')

    os.makedirs(out_dir, exist_ok=True)
    print("=" * 60)
    print("  海报分层 PSD 管线 — poster-2k-psd-splitter")
    print("=" * 60)
    print(f"[输出目录] {out_dir}")
    print()

    # ── Step 0: 环境准备 ──
    print("━━━ Step 0: 环境准备 ━━━")
    cfg = get_config()
    print()

    # ── Step 1: 获取并缩放原图 ──
    print("━━━ Step 1: 获取并缩放原图 ━━━")
    source_2k_path, canvas_w, canvas_h = fetch_and_scale(args.source, out_dir, args.max_edge)
    print()

    # ── Step 2: 上传原图到 Cloudinary ──
    print("━━━ Step 2: 上传原图到 Cloudinary ━━━")
    source_url = upload_to_cloudinary(source_2k_path)
    print(f"[Step2] 原图 URL: {source_url}")
    print()

    # ── Step 2.5: 自动视觉分析（如未手动提供 prompt）──
    if args.bg_prompt and args.fg_prompt:
        bg_prompt = args.bg_prompt
        fg_prompt = args.fg_prompt
        print("━━━ Step 2.5: 使用手动提供的提示词 ━━━")
        print(f"  BgPrompt: {bg_prompt[:60]}...")
        print(f"  FgPrompt: {fg_prompt[:60]}...")
    else:
        print("━━━ Step 2.5: VLM 自动视觉分析 ━━━")
        bg_prompt, fg_prompt = auto_analyze_image(cfg, source_url, args.vlm_model)
    print()

    # ── Step 3: Gemini 双提取 ──
    print("━━━ Step 3: Gemini 3.1 Flash 双提取 ━━━")
    bg_path, fg_raw_path = extract_bg_fg(
        cfg, source_url, bg_prompt, fg_prompt,
        canvas_w, canvas_h, out_dir,
    )
    print()

    # ── Step 4: RH 抠图王 ──
    print("━━━ Step 4: RH 抠图王前景去底 ━━━")
    matted_path = rh_matting(cfg, fg_raw_path, out_dir)
    print()

    # ── Step 5: 连通域切割 ──
    print("━━━ Step 5: 连通域切割 ━━━")
    elements = split_elements(matted_path, out_dir)
    for elem in elements:
        print(f"  → {os.path.basename(elem['path'])}  "
              f"pos=({elem['left']},{elem['top']})  "
              f"size={elem['width']}×{elem['height']}")
    print()

    # ── Step 6: 组装 PSD 并分卷压缩 ──
    print("━━━ Step 6: 组装 PSD 并分卷压缩 ━━━")
    scene_json_path = build_scene_json(canvas_w, canvas_h, source_2k_path, bg_path, elements, out_dir)

    psd_output_path = os.path.join(out_dir, 'layered-output.psd')
    psd_ok = invoke_psd_builder(scene_json_path, psd_output_path)

    volumes = []
    if psd_ok and os.path.isfile(psd_output_path):
        max_bytes = args.volume_size * 1024 * 1024
        volumes = volume_compress(psd_output_path, max_bytes, out_dir)
    print()

    # ── 最终输出汇总 ──
    print("=" * 60)
    print("  管线执行完成 — 输出文件清单")
    print("=" * 60)
    print(f"  原图 (2K)    : {source_2k_path}")
    print(f"  背景         : {bg_path}")
    print(f"  前景 (raw)   : {fg_raw_path}")
    print(f"  前景 (matted): {matted_path}")
    for elem in elements:
        print(f"  元素         : {elem['path']}")
    print(f"  scene.json   : {scene_json_path}")
    if psd_ok:
        print(f"  PSD 文件     : {psd_output_path}")
    if volumes:
        for v in volumes:
            print(f"  压缩分卷     : {v}")
    print("=" * 60)


if __name__ == '__main__':
    main()
