#!/usr/bin/env python3
"""
测试 Cloudinary 上传功能
"""
import sys
from pathlib import Path

# 添加脚本目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime_config import upload_to_cloudinary, load_runtime_env

def test_upload():
    """测试上传功能"""

    # 加载环境变量
    env = load_runtime_env()

    print("=" * 60)
    print("Cloudinary 上传测试")
    print("=" * 60)

    # 检查是否有测试图片
    test_image = Path(__file__).parent.parent / "references" / "万物提取.md"
    if not test_image.exists():
        # 尝试在当前目录查找任意图片
        possible_images = list(Path.cwd().glob("*.png")) + list(Path.cwd().glob("*.jpg"))
        if possible_images:
            test_image = possible_images[0]
        else:
            print("\n[错误] 找不到测试图片文件")
            print("请提供一个图片文件路径作为参数：")
            print(f"  python {Path(__file__).name} /path/to/image.png")
            return 1

    # 如果命令行提供了参数，使用参数作为测试文件
    if len(sys.argv) > 1:
        test_image = Path(sys.argv[1])
        if not test_image.exists():
            print(f"\n[错误] 文件不存在: {test_image}")
            return 1

    print(f"\n测试图片: {test_image}")
    print(f"文件大小: {test_image.stat().st_size / 1024:.2f} KB")

    try:
        print("\n开始上传...")
        url = upload_to_cloudinary(test_image)

        print("\n" + "=" * 60)
        print("✅ 上传成功！")
        print("=" * 60)
        print(f"\nCloudinary URL:\n{url}")
        print("\n你可以在浏览器中打开此 URL 查看图片")
        print("=" * 60)

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 上传失败")
        print("=" * 60)
        print(f"\n错误信息: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_upload())
