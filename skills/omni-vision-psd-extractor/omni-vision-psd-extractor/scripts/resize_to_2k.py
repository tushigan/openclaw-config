#!/usr/bin/env python3
"""
图片预处理工具：缩放到 2K 分辨率
"""
from pathlib import Path
from PIL import Image


def resize_to_2k(input_path: Path | str, output_path: Path | str = None, max_edge: int = 2048) -> tuple[Path, int, int]:
    """
    将图片缩放到 2K 分辨率（最长边 2048px），保持宽高比。

    参数:
        input_path: 输入图片路径
        output_path: 输出图片路径（可选，默认为输入路径 + "_2k" 后缀）
        max_edge: 最长边目标尺寸（默认 2048px）

    返回:
        (输出路径, 新宽度, 新高度)
    """
    input_path = Path(input_path)

    # 打开图片
    with Image.open(input_path) as img:
        orig_w, orig_h = img.size
        print(f"[缩放] 原始尺寸: {orig_w}×{orig_h}")

        # 如果已经小于等于 2K，直接返回
        if max(orig_w, orig_h) <= max_edge:
            print(f"[缩放] 图片已经小于 {max_edge}px，无需缩放")
            if output_path:
                img.save(output_path)
                return Path(output_path), orig_w, orig_h
            return input_path, orig_w, orig_h

        # 计算缩放比例
        scale = max_edge / max(orig_w, orig_h)
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
            output_path = input_path.parent / f"{input_path.stem}_2k{input_path.suffix}"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img_resized.save(output_path, 'PNG')

        print(f"[缩放] 已保存: {output_path}")
        return output_path, new_w, new_h


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python resize_to_2k.py <input_image> [output_image]")
        sys.exit(1)

    input_img = sys.argv[1]
    output_img = sys.argv[2] if len(sys.argv) > 2 else None

    result_path, w, h = resize_to_2k(input_img, output_img)
    print(f"\n✅ 完成！输出文件: {result_path} ({w}×{h})")
