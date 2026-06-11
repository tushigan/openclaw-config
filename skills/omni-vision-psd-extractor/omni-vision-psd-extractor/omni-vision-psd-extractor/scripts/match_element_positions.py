#!/usr/bin/env python3
"""
使用 GPT-5.4 多模态模型进行元素位置匹配

输入：
1. 原图（source.png）
2. 元素整理后的绿幕图（rearranged.png）

输出：
position_map.json - 每个元素在原图中的位置信息
{
  "elements": [
    {
      "id": 1,
      "name": "元素名称",
      "rearranged_bbox": [x, y, w, h],  // 在整理图中的位置
      "original_bbox": [x, y, w, h],     // 在原图中的位置
      "confidence": 0.95
    },
    ...
  ]
}
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests


def parse_args():
    parser = argparse.ArgumentParser(description="使用 GPT-5.4 匹配元素位置")
    parser.add_argument("--source", required=True, help="原图路径")
    parser.add_argument("--rearranged", required=True, help="元素整理后的绿幕图路径")
    parser.add_argument("--output", required=True, help="输出位置映射 JSON 路径")
    parser.add_argument("--api-key", help="API Key（可从环境变量 OPENCLAW_VLM_API_KEY 读取）")
    parser.add_argument("--api-base", help="API Base URL（可从环境变量 OPENCLAW_VLM_BASE_URL 读取）")
    parser.add_argument("--model", help="模型名称（可从环境变量 OPENCLAW_VLM_MODEL 读取）")
    return parser.parse_args()


def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_gpt5_4_vision(
    source_base64: str,
    rearranged_base64: str,
    api_key: str,
    api_base: str,
    model: str
) -> dict:
    """
    调用 GPT-5.4 进行元素位置匹配

    返回格式：
    {
      "elements": [
        {
          "id": 1,
          "name": "...",
          "rearranged_bbox": [x, y, w, h],
          "original_bbox": [x, y, w, h],
          "confidence": 0.95
        }
      ]
    }
    """

    prompt = """你是一个专业的图像分析专家。现在有两张图片：

**图片1（原图）**：包含多个视觉元素的原始设计图
**图片2（元素整理图）**：将图片1中的元素提取出来，重新排列在绿幕背景上的整理图

你的任务是：
1. 识别图片2（元素整理图）中的每一个独立元素
2. 对于每个元素，找到它在图片1（原图）中的对应位置
3. 使用 bbox（边界框）格式 [x, y, width, height] 标注位置

要求：
- 仔细比对元素的视觉特征（形状、颜色、纹理、细节）
- 每个元素必须找到在原图中的精确位置
- bbox 坐标使用像素值（相对于图片左上角为原点）
- 返回严格的 JSON 格式

返回格式：
```json
{
  "elements": [
    {
      "id": 1,
      "name": "元素描述（如：主标题文字、人物图片、Logo等）",
      "rearranged_bbox": [x, y, width, height],
      "original_bbox": [x, y, width, height],
      "confidence": 0.95
    }
  ]
}
```

注意：
- id 从 1 开始递增
- confidence 表示匹配置信度（0-1）
- 如果某个元素在原图中找不到对应位置，设置 confidence 为 0，original_bbox 为 null
- 必须返回纯 JSON，不要有任何其他文字说明
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{source_base64}",
                            "detail": "high"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{rearranged_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.1
    }

    response = requests.post(
        f"{api_base}/chat/completions",
        headers=headers,
        json=payload,
        timeout=600  # 改为10分钟，与 gpt-image-2-pro 超时一致
    )

    if response.status_code != 200:
        raise Exception(f"API 请求失败: {response.status_code} - {response.text}")

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    # 提取 JSON（去除可能的 markdown 代码块标记）
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    return json.loads(content)


def main():
    args = parse_args()

    source_path = Path(args.source)
    rearranged_path = Path(args.rearranged)
    output_path = Path(args.output)

    if not source_path.exists():
        print(f"❌ 错误：原图不存在: {source_path}")
        return 1

    if not rearranged_path.exists():
        print(f"❌ 错误：元素整理图不存在: {rearranged_path}")
        return 1

    # 从 OpenClaw 环境变量读取配置（优先级：命令行参数 > 环境变量 > 默认值）
    api_key = args.api_key or os.getenv("OPENCLAW_VLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    api_base = args.api_base or os.getenv("OPENCLAW_VLM_BASE_URL") or "https://aixor.org/v1"
    model = args.model or os.getenv("OPENCLAW_VLM_MODEL") or "gpt-5.4"

    if not api_key:
        print("❌ 错误：未提供 API Key")
        print("   请通过以下方式之一提供：")
        print("   1. --api-key 参数")
        print("   2. OPENCLAW_VLM_API_KEY 环境变量")
        print("   3. OPENAI_API_KEY 环境变量")
        return 1

    print(f"[位置匹配] 开始分析...")
    print(f"[位置匹配] 原图: {source_path}")
    print(f"[位置匹配] 元素整理图: {rearranged_path}")
    print(f"[位置匹配] API Base: {api_base}")
    print(f"[位置匹配] 模型: {model}")

    # 编码图片
    print(f"[位置匹配] 正在编码图片...")
    source_base64 = encode_image_to_base64(str(source_path))
    rearranged_base64 = encode_image_to_base64(str(rearranged_path))

    # 调用 GPT-5.4
    print(f"[位置匹配] 正在调用 {model} 进行位置匹配...")
    try:
        position_map = call_gpt5_4_vision(
            source_base64,
            rearranged_base64,
            api_key,
            api_base,
            model
        )
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        return 1

    # 保存结果
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(position_map, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ 位置匹配完成！")
    print(f"[位置匹配] 识别元素数量: {len(position_map.get('elements', []))}")
    print(f"[位置匹配] 输出文件: {output_path}")

    # 打印匹配结果摘要
    print(f"\n{'=' * 60}")
    print(f"元素匹配结果摘要:")
    print(f"{'=' * 60}")
    for elem in position_map.get("elements", []):
        print(f"  [{elem['id']}] {elem['name']}")
        print(f"      整理图位置: {elem['rearranged_bbox']}")
        print(f"      原图位置: {elem['original_bbox']}")
        print(f"      置信度: {elem['confidence']:.2f}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
