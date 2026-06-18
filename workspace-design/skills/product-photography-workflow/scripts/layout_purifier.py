#!/usr/bin/env python3
"""
机位参考图纯净化处理模块

用于将包含纹理细节的机位预览图转换为纯净的位置参考图，
只保留形状和位置信息，完全去除纹理细节。

这对于烘焙产品等质感敏感的品类尤为重要，可以避免模型从机位参考图中
"借用"错误的纹理特征。
"""

import numpy as np
from PIL import Image
import cv2
from pathlib import Path


def create_pure_silhouette(input_path: str, output_path: str) -> None:
    """
    生成纯色剪影版本：只保留形状，完全去除纹理

    这是最推荐的模式，特别适合烘焙产品等质感敏感的品类。

    Args:
        input_path: 输入图片路径（机位预览图）
        output_path: 输出图片路径
    """
    img = Image.open(input_path).convert('L')

    # 二值化：将图像转换为纯黑白
    img = img.point(lambda x: 0 if x < 200 else 255)

    # 形态学处理：填充空洞、平滑边缘
    img_array = np.array(img)
    kernel = np.ones((5, 5), np.uint8)
    img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
    img_array = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, kernel)

    # 创建纯色剪影：产品区域填充为灰色，背景为白色
    mask = img_array < 128
    result = np.ones_like(img_array) * 255
    result[mask] = 128  # 纯灰色填充，无任何纹理

    Image.fromarray(result).save(output_path)
    print(f"✓ 生成纯色剪影版本: {output_path}")


def create_pure_outline(input_path: str, output_path: str) -> None:
    """
    生成纯轮廓线版本：只保留外轮廓，内部完全空白

    适合需要精确控制产品边界但不希望填充影响内部细节的场景。

    Args:
        input_path: 输入图片路径（机位预览图）
        output_path: 输出图片路径
    """
    img = Image.open(input_path).convert('L')
    img = img.point(lambda x: 0 if x < 200 else 255)

    img_array = np.array(img)

    # 边缘检测
    edges = cv2.Canny(img_array, 50, 150)

    # 膨胀边缘使其更明显
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=2)

    # 创建纯白背景 + 黑色轮廓线
    result = np.ones_like(img_array) * 255
    result[edges > 0] = 0

    Image.fromarray(result).save(output_path)
    print(f"✓ 生成纯轮廓线版本: {output_path}")


def create_pure_geometric(input_path: str, output_path: str) -> None:
    """
    生成几何形状版本：将产品简化为基本几何形状

    适合需要更抽象的位置参考的场景。

    Args:
        input_path: 输入图片路径（机位预览图）
        output_path: 输出图片路径
    """
    img = Image.open(input_path).convert('L')
    img = img.point(lambda x: 0 if x < 200 else 255)

    img_array = np.array(img)

    # 强力形态学处理：简化为基本形状
    kernel = np.ones((15, 15), np.uint8)
    img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
    img_array = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, kernel)

    # 高斯模糊 + 再次二值化：进一步简化
    img_array = cv2.GaussianBlur(img_array, (21, 21), 0)
    img_array = (img_array < 128).astype(np.uint8) * 255

    # 创建几何形状版本
    mask = img_array > 128
    result = np.ones_like(img_array) * 255
    result[~mask] = 100  # 深灰色填充

    Image.fromarray(result).save(output_path)
    print(f"✓ 生成几何形状版本: {output_path}")


def purify_layout_reference(
    input_path: str,
    output_dir: str = None,
    modes: list[str] = None
) -> dict[str, str]:
    """
    批量生成纯净机位参考图

    Args:
        input_path: 输入图片路径（机位预览图）
        output_dir: 输出目录（默认与输入文件同目录）
        modes: 要生成的模式列表，可选值：['silhouette', 'outline', 'geometric']
               默认只生成 silhouette（推荐用于烘焙产品）

    Returns:
        dict: 各模式对应的输出文件路径
    """
    input_path = Path(input_path)

    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    if modes is None:
        modes = ['silhouette']  # 默认只生成最推荐的模式

    # 构建输出文件名
    base_name = input_path.stem

    results = {}

    if 'silhouette' in modes:
        output_path = output_dir / f"{base_name}_pure_silhouette.png"
        create_pure_silhouette(str(input_path), str(output_path))
        results['silhouette'] = str(output_path)

    if 'outline' in modes:
        output_path = output_dir / f"{base_name}_pure_outline.png"
        create_pure_outline(str(input_path), str(output_path))
        results['outline'] = str(output_path)

    if 'geometric' in modes:
        output_path = output_dir / f"{base_name}_pure_geometric.png"
        create_pure_geometric(str(input_path), str(output_path))
        results['geometric'] = str(output_path)

    return results


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python layout_purifier.py <input_image> [output_dir] [modes]")
        print("示例: python layout_purifier.py camera_preview.png ./output silhouette,outline")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    modes = sys.argv[3].split(',') if len(sys.argv) > 3 else ['silhouette']

    results = purify_layout_reference(input_path, output_dir, modes)

    print("\n生成完成:")
    for mode, path in results.items():
        print(f"  {mode}: {path}")
