#!/usr/bin/env python3
"""
触发词尺寸解析工具

从用户输入中提取尺寸规格（1K/2K/4K），用于 OpenClaw skill 调用
"""
import re
import sys
from typing import Tuple, Optional


def parse_trigger_size(user_input: str) -> Tuple[str, Optional[str]]:
    """
    从用户输入中解析尺寸规格

    参数:
        user_input: 用户原始输入，例如：
            - "无损提取PSD"
            - "无损提取PSD 1K"
            - "原图提取分层 2K"
            - "语义抠图PSD 4K"

    返回:
        (清理后的触发词, 尺寸规格)
        - 触发词：去除尺寸后缀的原始触发词
        - 尺寸规格：None（使用默认）或 "1K"/"2K"/"4K"

    示例:
        >>> parse_trigger_size("无损提取PSD")
        ('无损提取PSD', None)
        >>> parse_trigger_size("无损提取PSD 1K")
        ('无损提取PSD', '1K')
        >>> parse_trigger_size("原图提取分层 2K")
        ('原图提取分层', '2K')
        >>> parse_trigger_size("语义抠图PSD4K")
        ('语义抠图PSD', '4K')
    """
    # 尺寸规格模式：1K, 2K, 4K（大小写不敏感，可以有空格或无空格）
    size_pattern = r'\s*([1248]k)\s*$'

    # 搜索尺寸后缀
    match = re.search(size_pattern, user_input, re.IGNORECASE)

    if match:
        size_spec = match.group(1).upper()  # 标准化为大写
        # 验证是否为支持的尺寸
        if size_spec in ["1K", "2K", "4K"]:
            clean_trigger = user_input[:match.start()].strip()
            return clean_trigger, size_spec

    # 没有找到尺寸规格，返回原始输入和 None
    return user_input.strip(), None


def main():
    """命令行工具入口"""
    if len(sys.argv) < 2:
        print("用法: python parse_trigger_size.py <用户输入>")
        print("\n示例:")
        print('  python parse_trigger_size.py "无损提取PSD"')
        print('  python parse_trigger_size.py "无损提取PSD 1K"')
        print('  python parse_trigger_size.py "原图提取分层 2K"')
        print('  python parse_trigger_size.py "语义抠图PSD 4K"')
        sys.exit(1)

    user_input = " ".join(sys.argv[1:])
    trigger, size = parse_trigger_size(user_input)

    print(f"原始输入: {user_input}")
    print(f"触发词: {trigger}")
    print(f"尺寸规格: {size if size else '默认 (2K)'}")

    # 输出 JSON 格式（便于其他脚本调用）
    import json
    result = {
        "original": user_input,
        "trigger": trigger,
        "size": size,
        "size_default": "2K" if size is None else size
    }
    print(f"\nJSON: {json.dumps(result, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
