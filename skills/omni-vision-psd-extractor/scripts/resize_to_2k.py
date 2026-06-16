#!/usr/bin/env python3
"""
图片预处理工具：缩放到指定分辨率（支持 1K/2K/4K）
"""
from pathlib import Path
from typing import Union
from PIL import Image


def parse_target_size(size_spec: Union[str, int]) -> int:
    """
    解析目标尺寸规格

    参数:
        size_spec: 尺寸规格，可以是：
            - "1K" / "1k" -> 1024
            - "2K" / "2k" -> 2048
            - "4K" / "4k" -> 4096
            - 整数（如 2048）-> 直接返回

    返回:
        目标尺寸（像素）
    """
    if isinstance(size_spec, int):
        return size_spec

    size_map = {
        "1k": 1024,
        "2k": 2048,
        "4k": 4096,
    }

    normalized = str(size_spec).strip().lower()
    if normalized in size_map:
        return size_map[normalized]

    # 尝试解析为整数
    try:
        return int(size_spec)
    except ValueError:
        raise ValueError(f"无效的尺寸规格: {size_spec}. 支持的格式: 1K, 2K, 4K 或整数像素值")


def resize_image(
    input_path: Union[Path, str],
    output_path: Union[Path, str] = None,
    target_size: Union[str, int] = "2K",
    force_resize: bool = False
) -> tuple:
    """
    将图片缩放到指定分辨率（最长边），保持宽高比。

    参数:
        input_path: 输入图片路径
        output_path: 输出图片路径（可选，默认为输入路径 + "_<size>" 后缀）
        target_size: 目标尺寸规格（1K/2K/4K 或整数像素值，默认 2K）
        force_resize: 强制缩放（即使原图小于目标尺寸也会缩放，默认 False）

    返回:
        (输出路径, 新宽度, 新高度)
    """
    input_path = Path(input_path)
    max_edge = parse_target_size(target_size)

    # 打开图片
    with Image.open(input_path) as img:
        orig_w, orig_h = img.size
        print(f"[缩放] 原始尺寸: {orig_w}×{orig_h}")
        print(f"[缩放] 目标规格: {target_size} ({max_edge}px)")

        # 如果已经等于目标尺寸且不强制缩放，直接返回
        current_max = max(orig_w, orig_h)
        if not force_resize and current_max <= max_edge:
            print(f"[缩放] 图片最长边 {current_max}px ≤ 目标 {max_edge}px，无需缩放")
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(output_path)
                return output_path, orig_w, orig_h
            return input_path, orig_w, orig_h

        # 计算缩放比例（按最长边缩放）
        scale = max_edge / current_max
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        # 对齐到 16 的倍数（提高生成质量）
        new_w = max(16, ((new_w + 15) // 16) * 16)
        new_h = max(16, ((new_h + 15) // 16) * 16)

        print(f"[缩放] 目标尺寸: {new_w}×{new_h} (缩放比例: {scale:.2%})")

        # 转换色彩模式
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')

        # 缩放
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 保存
        if output_path is None:
            size_suffix = str(target_size).lower() if isinstance(target_size, str) else f"{max_edge}px"
            output_path = input_path.parent / f"{input_path.stem}_{size_suffix}{input_path.suffix}"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img_resized.save(output_path, 'PNG')

        print(f"[缩放] 已保存: {output_path}")
        return output_path, new_w, new_h


# 保持向后兼容的别名
def resize_to_2k(input_path: Union[Path, str], output_path: Union[Path, str] = None, max_edge: int = 2048) -> tuple:
    """向后兼容的接口，使用 resize_image 实现"""
    return resize_image(input_path, output_path, target_size=max_edge)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python resize_image.py <input_image> [output_image] [target_size]")
        print("示例:")
        print("  python resize_image.py input.png output.png 1K")
        print("  python resize_image.py input.png output.png 2K")
        print("  python resize_image.py input.png output.png 4K")
        print("  python resize_image.py input.png output.png 2048")
        sys.exit(1)

    input_img = sys.argv[1]
    output_img = sys.argv[2] if len(sys.argv) > 2 else None
    target = sys.argv[3] if len(sys.argv) > 3 else "2K"

    result_path, w, h = resize_image(input_img, output_img, target_size=target)
    print(f"\n✅ 完成！输出文件: {result_path} ({w}×{h})")
