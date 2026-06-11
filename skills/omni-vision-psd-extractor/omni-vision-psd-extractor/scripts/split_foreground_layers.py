#!/usr/bin/env python3
"""
前景层切割工具：将前景透明图切割成多个独立元素
"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import cv2


def split_foreground_layers(foreground_path: Path | str, output_dir: Path | str, canvas_w: int, canvas_h: int, min_area: int = 100) -> list[dict]:
    """
    将前景透明图切割成多个独立元素图层。

    参数:
        foreground_path: 前景透明 PNG 路径
        output_dir: 输出目录
        canvas_w: 画布宽度
        canvas_h: 画布高度
        min_area: 最小元素面积（像素数，默认 100）

    返回:
        元素列表 [{"key": "element_1", "path": "...", "bbox": [x, y, w, h], "area": 1234}, ...]
    """
    foreground_path = Path(foreground_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[切割] 正在分析前景图层: {foreground_path.name}")

    # 读取前景图（RGBA）
    img = Image.open(foreground_path).convert('RGBA')
    img_array = np.array(img)

    # 提取 Alpha 通道
    alpha = img_array[:, :, 3]

    # 二值化：透明 = 0, 不透明 > 0
    _, binary = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)

    # 连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    print(f"[切割] 检测到 {num_labels - 1} 个连通域（包含背景）")

    elements = []

    # 遍历所有连通域（跳过背景 label=0）
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]

        # 过滤太小的区域（噪点）
        if area < min_area:
            print(f"[切割] 跳过小区域 #{i}: 面积 {area} < {min_area} 像素")
            continue

        # 创建当前元素的掩膜
        mask = (labels == i).astype(np.uint8) * 255

        # 在原始画布尺寸上提取该元素
        element_img = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)

        # 只保留该元素的像素
        for c in range(4):  # RGBA
            element_img[:, :, c] = np.where(mask > 0, img_array[:, :, c], 0)

        # 保存为 PNG
        element_key = f"element_{i}"
        element_filename = f"{element_key}.png"
        element_path = output_dir / element_filename

        Image.fromarray(element_img, 'RGBA').save(element_path)

        elements.append({
            "key": element_key,
            "name": f"元素 {i}",
            "path": str(element_path),
            "bbox": [int(x), int(y), int(w), int(h)],
            "area": int(area),
            "centroid": [float(centroids[i][0]), float(centroids[i][1])],
        })

        print(f"[切割] ✅ {element_key}: 位置=({x},{y}), 尺寸={w}×{h}, 面积={area}px")

    # 按面积从大到小排序（主体元素优先）
    elements.sort(key=lambda e: e['area'], reverse=True)

    # 重新编号
    for idx, elem in enumerate(elements, start=1):
        old_key = elem['key']
        elem['key'] = f"element_{idx}"
        elem['name'] = f"元素 {idx}"

        # 重命名文件
        old_path = Path(elem['path'])
        new_path = old_path.parent / f"element_{idx}.png"
        old_path.rename(new_path)
        elem['path'] = str(new_path)

    print(f"\n[切割] 完成！共切割出 {len(elements)} 个元素")
    return elements


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python split_foreground_layers.py <foreground.png> <output_dir> <canvas_w> <canvas_h> [min_area]")
        print("示例: python split_foreground_layers.py fg.png ./elements 2048 1536 100")
        sys.exit(1)

    fg_path = sys.argv[1]
    out_dir = sys.argv[2]
    canvas_w = int(sys.argv[3])
    canvas_h = int(sys.argv[4])
    min_area = int(sys.argv[5]) if len(sys.argv) > 5 else 100

    elements = split_foreground_layers(fg_path, out_dir, canvas_w, canvas_h, min_area)

    # 保存元素清单
    manifest_path = Path(out_dir) / "elements.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 元素清单已保存: {manifest_path}")
    for elem in elements:
        print(f"  - {elem['name']}: {elem['path']} (面积: {elem['area']}px)")
