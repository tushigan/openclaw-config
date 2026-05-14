#!/usr/bin/env python3
"""输出单张图片尺寸。"""

import argparse
from pathlib import Path
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description="输出图片尺寸")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(Image.open(args.path).size)


if __name__ == "__main__":
    main()
