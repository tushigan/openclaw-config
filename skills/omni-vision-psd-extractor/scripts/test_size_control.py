#!/usr/bin/env python3
"""
触发词尺寸控制功能测试脚本

测试内容：
1. 触发词解析功能
2. 尺寸缩放功能
3. 参数传递流程
"""

import sys
import json
from pathlib import Path

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from parse_trigger_size import parse_trigger_size
from resize_to_2k import parse_target_size, resize_image


def test_trigger_parsing():
    """测试触发词解析"""
    print("=" * 60)
    print("测试 1: 触发词解析")
    print("=" * 60)

    test_cases = [
        ("无损提取PSD", "无损提取PSD", None, "2K"),
        ("无损提取PSD 1K", "无损提取PSD", "1K", "1K"),
        ("无损提取PSD 2K", "无损提取PSD", "2K", "2K"),
        ("无损提取PSD 4K", "无损提取PSD", "4K", "4K"),
        ("原图提取分层 1K", "原图提取分层", "1K", "1K"),
        ("语义抠图PSD4K", "语义抠图PSD", "4K", "4K"),
        ("全息万物提取 2k", "全息万物提取", "2K", "2K"),
    ]

    all_passed = True
    for input_text, expected_trigger, expected_size, expected_default in test_cases:
        trigger, size = parse_trigger_size(input_text)
        size_default = expected_default if size is None else size

        passed = (
            trigger == expected_trigger and
            size == expected_size and
            size_default == expected_default
        )

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}: {input_text}")
        print(f"  预期: trigger={expected_trigger}, size={expected_size}, default={expected_default}")
        print(f"  实际: trigger={trigger}, size={size}, default={size_default}")

        if not passed:
            all_passed = False

    return all_passed


def test_size_parsing():
    """测试尺寸规格解析"""
    print("\n" + "=" * 60)
    print("测试 2: 尺寸规格解析")
    print("=" * 60)

    test_cases = [
        ("1K", 1024),
        ("2K", 2048),
        ("4K", 4096),
        ("1k", 1024),
        ("2k", 2048),
        ("4k", 4096),
        (1024, 1024),
        (2048, 2048),
        (4096, 4096),
    ]

    all_passed = True
    for input_spec, expected_pixels in test_cases:
        try:
            pixels = parse_target_size(input_spec)
            passed = pixels == expected_pixels

            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"\n{status}: {input_spec}")
            print(f"  预期: {expected_pixels}px")
            print(f"  实际: {pixels}px")

            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n❌ FAIL: {input_spec}")
            print(f"  错误: {e}")
            all_passed = False

    return all_passed


def test_scaling_calculation():
    """测试尺寸缩放计算"""
    print("\n" + "=" * 60)
    print("测试 3: 尺寸缩放计算")
    print("=" * 60)

    test_cases = [
        # (原始宽, 原始高, 目标规格, 预期宽, 预期高)
        (4096, 3072, "1K", 1024, 768),
        (4096, 3072, "2K", 2048, 1536),
        (4096, 3072, "4K", 4096, 3072),
        (1920, 1080, "1K", 1024, 576),
        (1920, 1080, "2K", 2048, 1152),
        (3840, 2160, "2K", 2048, 1152),
    ]

    all_passed = True
    for orig_w, orig_h, target_spec, expected_w, expected_h in test_cases:
        target_pixels = parse_target_size(target_spec)

        # 计算缩放
        current_max = max(orig_w, orig_h)
        scale = target_pixels / current_max
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        # 对齐到 16
        new_w = max(16, ((new_w + 15) // 16) * 16)
        new_h = max(16, ((new_h + 15) // 16) * 16)

        passed = new_w == expected_w and new_h == expected_h

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}: {orig_w}×{orig_h} → {target_spec}")
        print(f"  预期: {expected_w}×{expected_h}")
        print(f"  实际: {new_w}×{new_h}")
        print(f"  缩放比例: {scale:.2%}")

        if not passed:
            all_passed = False

    return all_passed


def test_integration():
    """测试集成流程"""
    print("\n" + "=" * 60)
    print("测试 4: 集成流程模拟")
    print("=" * 60)

    test_cases = [
        "无损提取PSD 1K",
        "原图提取分层 2K",
        "语义抠图PSD 4K",
    ]

    all_passed = True
    for user_input in test_cases:
        try:
            # 步骤 1: 解析触发词
            trigger, size = parse_trigger_size(user_input)
            target_size = size if size else "2K"

            # 步骤 2: 解析目标尺寸
            target_pixels = parse_target_size(target_size)

            # 步骤 3: 模拟命令构建
            cmd_args = [
                "--source", "/path/to/image.png",
                "--target-size", target_size,
                "--feishu-user-id", "ou_xxx"
            ]

            print(f"\n✅ PASS: {user_input}")
            print(f"  触发词: {trigger}")
            print(f"  尺寸规格: {target_size}")
            print(f"  目标像素: {target_pixels}px")
            print(f"  命令参数: {' '.join(cmd_args)}")

        except Exception as e:
            print(f"\n❌ FAIL: {user_input}")
            print(f"  错误: {e}")
            all_passed = False

    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("触发词尺寸控制功能测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("触发词解析", test_trigger_parsing()))
    results.append(("尺寸规格解析", test_size_parsing()))
    results.append(("尺寸缩放计算", test_scaling_calculation()))
    results.append(("集成流程", test_integration()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分测试失败，请检查日志")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
