#!/usr/bin/env python3
"""
根据位置映射将元素整理图中的元素精准放回原位

输入：
1. 元素整理图（rearranged.png）- 绿幕背景上排列的元素
2. 位置映射文件（position_map.json）- GPT-5.4 生成的位置对应关系
3. 画布尺寸（width, height）- 原图尺寸

输出：
多个独立的元素图层 PNG 文件，每个元素在原图的精确位置
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(description="根据位置映射重组元素到原位")
    parser.add_argument("--rearranged", required=True, help="元素整理图路径")
    parser.add_argument("--position-map", required=True, help="位置映射 JSON 路径")
    parser.add_argument("--canvas-width", type=int, required=True, help="画布宽度")
    parser.add_argument("--canvas-height", type=int, required=True, help="画布高度")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--output-manifest", help="输出元素清单 JSON 路径")
    return parser.parse_args()


def extract_element_from_greenscreen(rearranged_img: np.ndarray, bbox: list) -> np.ndarray:
    """
    从绿幕图中提取单个元素（带透明度）

    Args:
        rearranged_img: 元素整理图（RGBA 格式）
        bbox: [x, y, width, height] 在整理图中的位置

    Returns:
        元素图像（RGBA，保持原画布尺寸，仅在 bbox 区域有内容）
    """
    x, y, w, h = bbox
    x, y, w, h = int(x), int(y), int(w), int(h)

    # 创建空白画布
    canvas_h, canvas_w = rearranged_img.shape[:2]
    element = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)

    # 边界检查
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(canvas_w, x + w)
    y2 = min(canvas_h, y + h)

    if x2 <= x1 or y2 <= y1:
        return element

    # 提取区域
    crop = rearranged_img[y1:y2, x1:x2].copy()

    # 去除绿幕（#00FF00）
    # 绿幕颜色范围
    lower_green = np.array([0, 240, 0])  # RGB
    upper_green = np.array([10, 255, 10])

    # 转换为 RGB 用于颜色检测
    crop_rgb = crop[:, :, :3]

    # 创建绿幕遮罩
    green_mask = cv2.inRange(crop_rgb, lower_green, upper_green)

    # 将绿幕区域设为透明
    crop[green_mask > 0, 3] = 0

    # 放回到画布上
    element[y1:y2, x1:x2] = crop

    return element


def place_element_at_position(element: np.ndarray, original_bbox: list, canvas_width: int, canvas_height: int) -> np.ndarray:
    """
    将元素放置到原图位置（保持原画布尺寸）

    Args:
        element: 从整理图中提取的元素（RGBA，整理图画布尺寸）
        original_bbox: [x, y, width, height] 在原图中的目标位置
        canvas_width: 原图画布宽度
        canvas_height: 原图画布高度

    Returns:
        元素图像（RGBA，原图画布尺寸，元素在目标位置）
    """
    x, y, w, h = original_bbox
    x, y, w, h = int(x), int(y), int(w), int(h)

    # 创建原图尺寸的画布
    canvas = np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)

    # 从元素图中提取非透明区域
    alpha = element[:, :, 3]
    non_transparent = np.where(alpha > 0)

    if len(non_transparent[0]) == 0:
        return canvas

    # 计算元素的实际边界框
    y_min, y_max = non_transparent[0].min(), non_transparent[0].max() + 1
    x_min, x_max = non_transparent[1].min(), non_transparent[1].max() + 1

    # 提取实际内容
    content = element[y_min:y_max, x_min:x_max]

    # 计算缩放比例（如果尺寸不匹配）
    content_h, content_w = content.shape[:2]
    scale_w = w / content_w if content_w > 0 else 1.0
    scale_h = h / content_h if content_h > 0 else 1.0
    scale = min(scale_w, scale_h)  # 保持宽高比

    if abs(scale - 1.0) > 0.05:  # 如果缩放比例差异超过 5%
        new_w = int(content_w * scale)
        new_h = int(content_h * scale)
        content = cv2.resize(content, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # 计算放置位置（居中对齐到目标 bbox）
    placed_h, placed_w = content.shape[:2]
    offset_x = x + (w - placed_w) // 2
    offset_y = y + (h - placed_h) // 2

    # 边界检查
    x1 = max(0, offset_x)
    y1 = max(0, offset_y)
    x2 = min(canvas_width, offset_x + placed_w)
    y2 = min(canvas_height, offset_y + placed_h)

    if x2 <= x1 or y2 <= y1:
        return canvas

    # 计算内容的对应区域
    content_x1 = x1 - offset_x
    content_y1 = y1 - offset_y
    content_x2 = content_x1 + (x2 - x1)
    content_y2 = content_y1 + (y2 - y1)

    # 放置元素
    canvas[y1:y2, x1:x2] = content[content_y1:content_y2, content_x1:content_x2]

    return canvas


def main():
    args = parse_args()

    rearranged_path = Path(args.rearranged)
    position_map_path = Path(args.position_map)
    output_dir = Path(args.output_dir)

    if not rearranged_path.exists():
        print(f"❌ 错误：元素整理图不存在: {rearranged_path}")
        return 1

    if not position_map_path.exists():
        print(f"❌ 错误：位置映射文件不存在: {position_map_path}")
        return 1

    # 读取位置映射
    position_map = json.loads(position_map_path.read_text(encoding="utf-8"))
    elements = position_map.get("elements", [])

    if not elements:
        print(f"❌ 错误：位置映射中没有元素")
        return 1

    print(f"[元素重组] 开始处理...")
    print(f"[元素重组] 元素整理图: {rearranged_path}")
    print(f"[元素重组] 元素数量: {len(elements)}")
    print(f"[元素重组] 画布尺寸: {args.canvas_width}×{args.canvas_height}")

    # 读取元素整理图
    rearranged_img = cv2.imread(str(rearranged_path), cv2.IMREAD_UNCHANGED)
    if rearranged_img is None:
        print(f"❌ 错误：无法读取元素整理图")
        return 1

    # 确保是 RGBA 格式
    if rearranged_img.shape[2] == 3:
        rearranged_img = cv2.cvtColor(rearranged_img, cv2.COLOR_BGR2BGRA)
    else:
        rearranged_img = cv2.cvtColor(rearranged_img, cv2.COLOR_BGRA2RGBA)

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 处理每个元素
    output_elements = []

    for elem in elements:
        elem_id = elem["id"]
        elem_name = elem["name"]
        rearranged_bbox = elem["rearranged_bbox"]
        original_bbox = elem.get("original_bbox")
        confidence = elem.get("confidence", 0.0)

        print(f"\n[{elem_id}] {elem_name}")
        print(f"     整理图位置: {rearranged_bbox}")
        print(f"     原图位置: {original_bbox}")
        print(f"     置信度: {confidence:.2f}")

        if not original_bbox or confidence < 0.5:
            print(f"     ⚠️ 跳过（置信度过低或无法匹配）")
            continue

        # 从整理图中提取元素
        element = extract_element_from_greenscreen(rearranged_img, rearranged_bbox)

        # 放置到原图位置
        placed = place_element_at_position(
            element,
            original_bbox,
            args.canvas_width,
            args.canvas_height
        )

        # 保存元素图层
        output_filename = f"element_{elem_id:02d}.png"
        output_path = output_dir / output_filename

        # 转换回 BGR(A) 用于保存
        placed_bgr = cv2.cvtColor(placed, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(output_path), placed_bgr)

        print(f"     ✅ 已保存: {output_filename}")

        output_elements.append({
            "id": elem_id,
            "name": elem_name,
            "path": str(output_path),
            "bbox": original_bbox,
            "confidence": confidence
        })

    # 保存元素清单
    if args.output_manifest:
        manifest_path = Path(args.output_manifest)
        manifest = {
            "canvas": {
                "width": args.canvas_width,
                "height": args.canvas_height
            },
            "elements": output_elements,
            "total_elements": len(output_elements)
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✅ 元素清单已保存: {manifest_path}")

    print(f"\n{'=' * 60}")
    print(f"✅ 元素重组完成！")
    print(f"   成功处理: {len(output_elements)} / {len(elements)} 个元素")
    print(f"   输出目录: {output_dir}")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
