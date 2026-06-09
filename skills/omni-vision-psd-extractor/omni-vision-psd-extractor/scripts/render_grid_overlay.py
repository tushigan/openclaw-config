#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--step", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.source)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    image = Image.open(source).convert("RGBA")
    
    # 限制最大分辨率，防大图片在传输或处理时导致Maximum call stack size exceeded或内存溢出
    max_size = 2048
    if image.width > max_size or image.height > max_size:
        if image.width > image.height:
            new_w = max_size
            new_h = int(image.height * (max_size / image.width))
        else:
            new_h = max_size
            new_w = int(image.width * (max_size / image.height))
        new_w = ((new_w + 15) // 16) * 16
        new_h = ((new_h + 15) // 16) * 16
        print(f"[info] Grid source too large ({image.width}x{image.height}). Downscaling to {new_w}x{new_h}.")
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    for x in range(0, image.width, args.step):
      draw.line((x, 0, x, image.height), fill=(255, 0, 0, 120), width=1)
      draw.text((x + 2, 2), str(x), fill=(255, 0, 0, 255), font=font)

    for y in range(0, image.height, args.step):
      draw.line((0, y, image.width, y), fill=(255, 0, 0, 120), width=1)
      draw.text((2, y + 2), str(y), fill=(255, 0, 0, 255), font=font)

    image.save(out)
    print(out)


if __name__ == "__main__":
    main()
