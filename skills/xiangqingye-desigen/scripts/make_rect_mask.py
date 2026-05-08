#!/usr/bin/env python3
from PIL import Image, ImageDraw
from pathlib import Path
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--image', required=True)
ap.add_argument('--output', required=True)
ap.add_argument('--freeze-bottom-ratio', type=float, default=None)
ap.add_argument('--freeze-top-ratio', type=float, default=None)
ap.add_argument('--editable-rect', action='append', default=[], help='x1,y1,x2,y2 editable rect in pixels; can repeat')
args = ap.parse_args()

img = Image.open(args.image).convert('RGBA')
w, h = img.size
mask = Image.new('RGBA', (w, h), (0, 0, 0, 255))  # black = preserve by default

def add_editable_rect(rect_str):
    x1, y1, x2, y2 = map(int, rect_str.split(','))
    draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255, 255))

# OpenAI-style local convention for this skill: white = editable, black = preserve
from PIL import ImageDraw
draw = ImageDraw.Draw(mask)

if args.freeze_bottom_ratio is not None:
    cut = int(h * (1 - args.freeze_bottom_ratio))
    draw.rectangle([0, 0, w, cut], fill=(255, 255, 255, 255))

if args.freeze_top_ratio is not None:
    cut = int(h * args.freeze_top_ratio)
    draw.rectangle([0, cut, w, h], fill=(255, 255, 255, 255))

for rect in args.editable_rect:
    add_editable_rect(rect)

out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)
mask.save(out)
print(out)
print(f'{w}x{h}')
