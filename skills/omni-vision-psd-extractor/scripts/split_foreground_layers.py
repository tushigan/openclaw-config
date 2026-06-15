#!/usr/bin/env python3
"""
前景层切割工具：将透明前景图按视觉间隔切割成多个独立元素。
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
import cv2


class DisjointSet:
    def __init__(self, values: list[int]):
        self.parent = {value: value for value in values}

    def find(self, value: int) -> int:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2 = ax + aw
    ay2 = ay + ah
    bx2 = bx + bw
    by2 = by + bh
    dx = max(bx - ax2, ax - bx2, 0)
    dy = max(by - ay2, ay - by2, 0)
    return math.hypot(dx, dy)


def vertical_overlap_ratio(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    _ax, ay, _aw, ah = a
    _bx, by, _bw, bh = b
    overlap = max(0, min(ay + ah, by + bh) - max(ay, by))
    return overlap / max(1, min(ah, bh))


def horizontal_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    ax, _ay, aw, _ah = a
    bx, _by, bw, _bh = b
    ax2 = ax + aw
    bx2 = bx + bw
    return max(bx - ax2, ax - bx2, 0)


def clamp(value: float, low: int, high: int) -> int:
    return max(low, min(high, int(round(value))))


def estimate_merge_gap(components: list[dict], width: int, height: int) -> int:
    """Estimate the transparent gap that should still count as one visual element."""
    min_side = min(width, height)
    base_gap = clamp(min_side * 0.02, 12, 34)
    max_gap = clamp(min_side * 0.06, 18, 72)

    if len(components) < 3:
        return base_gap

    gaps: list[float] = []
    for comp in components:
        distances = [
            bbox_gap(comp["bbox"], other["bbox"])
            for other in components
            if other["label"] != comp["label"]
        ]
        if distances:
            nearest = min(distances)
            if 0 < nearest <= max_gap * 2:
                gaps.append(nearest)

    if len(gaps) < 4:
        return base_gap

    gaps = sorted(gaps)
    best_split: tuple[float, float] | None = None
    for left, right in zip(gaps, gaps[1:]):
        if right > max_gap:
            break
        if right - left >= max(6, base_gap * 0.45) and right / max(left, 1.0) >= 1.65:
            best_split = (left, right)

    if best_split:
        return clamp((best_split[0] + best_split[1]) / 2, 8, max_gap)
    return base_gap


def extract_components(binary: np.ndarray, min_area: int) -> tuple[np.ndarray, list[dict]]:
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    primitive_min_area = max(4, min(50, min_area // 5))
    components: list[dict] = []

    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        if int(area) < primitive_min_area:
            continue
        components.append({
            "label": label,
            "bbox": (int(x), int(y), int(w), int(h)),
            "area": int(area),
            "centroid": (float(centroids[label][0]), float(centroids[label][1])),
        })

    return labels, components


def should_merge(a: dict, b: dict, merge_gap: int, width: int, height: int) -> bool:
    gap = bbox_gap(a["bbox"], b["bbox"])
    if gap <= merge_gap:
        return True

    # Text and small marks often consist of separate characters/strokes. If they sit on
    # the same baseline and the gap is still modest, keep the line together.
    min_side = min(width, height)
    text_like_height = max(18, int(min_side * 0.075))
    _ax, ay, _aw, ah = a["bbox"]
    _bx, by, _bw, bh = b["bbox"]
    same_line = (
        ah <= text_like_height
        and bh <= text_like_height
        and vertical_overlap_ratio(a["bbox"], b["bbox"]) >= 0.55
        and abs((ay + ah / 2) - (by + bh / 2)) <= max(ah, bh) * 0.55
    )
    if same_line and horizontal_gap(a["bbox"], b["bbox"]) <= merge_gap * 2.8:
        return True

    return False


def grouped_component_labels(components: list[dict], merge_gap: int, width: int, height: int) -> list[list[int]]:
    labels = [comp["label"] for comp in components]
    dsu = DisjointSet(labels)

    for idx, comp in enumerate(components):
        for other in components[idx + 1:]:
            if should_merge(comp, other, merge_gap, width, height):
                dsu.union(comp["label"], other["label"])

    grouped: dict[int, list[int]] = defaultdict(list)
    for label in labels:
        grouped[dsu.find(label)].append(label)
    return list(grouped.values())


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    points = cv2.findNonZero(mask.astype(np.uint8))
    if points is None:
        return None
    x, y, w, h = cv2.boundingRect(points)
    return int(x), int(y), int(w), int(h)


def split_foreground_layers(
    foreground_path: Path | str,
    output_dir: Path | str,
    canvas_w: int,
    canvas_h: int,
    min_area: int = 100,
    merge_gap: int | None = None,
    alpha_threshold: int = 8,
) -> list[dict]:
    """
    将前景透明图切割成多个独立元素图层。

    参数:
        foreground_path: 前景透明 PNG 路径
        output_dir: 输出目录
        canvas_w: 画布宽度
        canvas_h: 画布高度
        min_area: 最小元素面积（像素数，默认 100）
        merge_gap: 小于等于该透明间隔的碎片会合并为同一元素；None 表示自动估算
        alpha_threshold: alpha 大于该值才参与切割骨架，低 alpha 边缘仍会尽量保留

    返回:
        元素列表 [{"key": "element_1", "path": "...", "bbox": [x, y, w, h], "area": 1234}, ...]
    """
    foreground_path = Path(foreground_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[切割] 正在分析前景图层: {foreground_path.name}")

    # 读取前景图（RGBA）
    img = Image.open(foreground_path).convert('RGBA')
    if img.size != (canvas_w, canvas_h):
        print(f"[切割] 前景尺寸 {img.width}×{img.height} 与画布 {canvas_w}×{canvas_h} 不一致，已按画布缩放")
        img = img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
    img_array = np.array(img)

    # 提取 Alpha 通道
    alpha = img_array[:, :, 3]

    # 二值化：使用略高阈值做结构判断，避免半透明边缘噪点影响分组
    _, binary = cv2.threshold(alpha, alpha_threshold, 255, cv2.THRESH_BINARY)

    labels, components = extract_components(binary, min_area)

    print(f"[切割] 检测到 {len(components)} 个基础碎片")

    if not components:
        print("\n[切割] 未检测到可切割元素")
        return []

    if merge_gap is None:
        merge_gap = estimate_merge_gap(components, canvas_w, canvas_h)
    print(f"[切割] 自动间隔阈值: {merge_gap}px（小于该间隔的碎片会合并）")

    elements = []
    grouped_labels = grouped_component_labels(components, merge_gap, canvas_w, canvas_h)

    # 根据聚类结果生成元素，仍输出原画布尺寸，保证 PSD 中位置可对齐
    for group_idx, labels_in_group in enumerate(grouped_labels, start=1):
        core_mask = np.isin(labels, labels_in_group)
        core_area = int(np.count_nonzero(core_mask))

        # 过滤太小的区域（噪点）
        if core_area < min_area:
            print(f"[切割] 跳过小区域 #{group_idx}: 面积 {core_area} < {min_area} 像素")
            continue

        # 把低 alpha 的柔边像素带回来，避免切割后边缘发硬。
        soft_mask = cv2.dilate(core_mask.astype(np.uint8), np.ones((3, 3), dtype=np.uint8), iterations=1).astype(bool)
        soft_mask = np.logical_and(soft_mask, alpha > 0)

        bbox = mask_bbox(soft_mask)
        if bbox is None:
            continue
        x, y, w, h = bbox

        # 在原始画布尺寸上提取该元素
        element_img = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)

        # 只保留该元素的像素
        for c in range(4):  # RGBA
            element_img[:, :, c] = np.where(soft_mask, img_array[:, :, c], 0)

        elements.append({
            "image": element_img,
            "bbox": [int(x), int(y), int(w), int(h)],
            "area": core_area,
            "component_count": len(labels_in_group),
            "centroid": [
                float(np.mean(np.where(core_mask)[1])),
                float(np.mean(np.where(core_mask)[0])),
            ],
        })

        print(
            f"[切割] ✅ group_{group_idx}: 位置=({x},{y}), "
            f"尺寸={w}×{h}, 面积={core_area}px, 碎片={len(labels_in_group)}"
        )

    # 按面积从大到小排序（主体元素优先）
    elements.sort(key=lambda e: e['area'], reverse=True)

    final_elements = []
    for idx, elem in enumerate(elements, start=1):
        element_key = f"element_{idx}"
        element_path = output_dir / f"{element_key}.png"
        Image.fromarray(elem.pop("image")).save(element_path)
        final_elements.append({
            "key": element_key,
            "name": f"元素 {idx}",
            "path": str(element_path),
            "bbox": elem["bbox"],
            "area": elem["area"],
            "centroid": elem["centroid"],
            "component_count": elem["component_count"],
            "merge_gap": merge_gap,
        })

    print(f"\n[切割] 完成！共切割出 {len(final_elements)} 个元素")
    return final_elements


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按透明间隔把前景 PNG 切割成独立图层")
    parser.add_argument("foreground")
    parser.add_argument("output_dir")
    parser.add_argument("canvas_w", type=int)
    parser.add_argument("canvas_h", type=int)
    parser.add_argument("min_area", type=int, nargs="?", default=100)
    parser.add_argument("--merge-gap", type=int, default=None, help="小于等于该透明间隔的碎片合并为同一元素；默认自动估算")
    parser.add_argument("--alpha-threshold", type=int, default=8, help="用于切割骨架的 alpha 阈值")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    elements = split_foreground_layers(
        args.foreground,
        args.output_dir,
        args.canvas_w,
        args.canvas_h,
        args.min_area,
        merge_gap=args.merge_gap,
        alpha_threshold=args.alpha_threshold,
    )

    # 保存元素清单
    manifest_path = Path(args.output_dir) / "elements.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 元素清单已保存: {manifest_path}")
    for elem in elements:
        print(f"  - {elem['name']}: {elem['path']} (面积: {elem['area']}px)")
