#!/usr/bin/env python3
"""Merge detail-page panels into one long image with unified width.

Usage:
  python merge_panels.py output.jpg input1 input2 [input3 ...]
  python merge_panels.py output.jpg input1 input2 --overlap 120
  python merge_panels.py output.png input1 input2 input3 --width 1152 --bg white
  python merge_panels.py output.jpg input1 input2 input3 --blend 80

Features:
- unify all panel widths before merge
- optional overlap cropping between adjacent panels (--overlap)
- gradient blend between adjacent panels (--blend) — recommended for seamless joins
- jpg/png output inferred from extension
- background color control
"""
from PIL import Image
from pathlib import Path
import argparse


def parse_bg(value: str):
    value = value.lower().strip()
    if value == 'white':
        return (255, 255, 255)
    if value == 'black':
        return (0, 0, 0)
    if value.startswith('#') and len(value) == 7:
        return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))
    raise ValueError(f'Unsupported bg color: {value}')


def blend_overlap(img_a: Image.Image, img_b: Image.Image, blend_px: int) -> Image.Image:
    """Blend the bottom of img_a with the top of img_b using linear gradient.

    Uses PIL's Image.composite with a gradient mask — no numpy needed.
    """
    w = img_a.width
    h_a = img_a.height
    h_b = img_b.height

    # Extract overlap zones
    zone_a_top = max(0, h_a - blend_px)
    zone_a = img_a.crop((0, zone_a_top, w, h_a))
    zone_b = img_b.crop((0, 0, w, min(blend_px, h_b)))

    # Ensure same height
    actual_blend = min(zone_a.height, zone_b.height)
    zone_a = zone_a.crop((0, 0, w, actual_blend))
    zone_b = zone_b.crop((0, 0, w, actual_blend))

    # Create gradient mask: black (0) at top → white (255) at bottom
    mask = Image.new('L', (w, actual_blend))
    for y in range(actual_blend):
        alpha = int(255 * y / max(actual_blend - 1, 1))
        for x in range(w):
            mask.putpixel((x, y), alpha)

    # Composite: zone_a at top (mask=0), zone_b at bottom (mask=255)
    return Image.composite(zone_b, zone_a, mask)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output')
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('--width', type=int, default=0, help='force output width; default=max input width')
    ap.add_argument('--overlap', type=int, default=0, help='crop this many pixels from the top of each panel except the first')
    ap.add_argument('--blend', type=int, default=0, help='blend N pixels between adjacent panels using gradient crossfade (recommended for seamless joins)')
    ap.add_argument('--bg', default='white', help='white | black | #RRGGBB')
    ap.add_argument('--quality', type=int, default=90)
    args = ap.parse_args()

    if args.overlap > 0 and args.blend > 0:
        raise SystemExit('Use either --overlap or --blend, not both')

    imgs = [Image.open(p).convert('RGB') for p in args.inputs]
    target_w = args.width or max(im.width for im in imgs)
    bg = parse_bg(args.bg)

    # Normalize widths
    resized = []
    for im in imgs:
        if im.width != target_w:
            new_h = round(im.height * target_w / im.width)
            im = im.resize((target_w, new_h), Image.Resampling.LANCZOS)
        resized.append(im)

    # Mode 1: gradient blend
    if args.blend > 0:
        blend_px = args.blend
        strips = []  # list of (image, is_blend_strip)

        # First panel (without its bottom blend zone)
        first = resized[0]
        if len(resized) > 1:
            strips.append(first.crop((0, 0, first.width, first.height - blend_px)))
        else:
            strips.append(first)

        # Middle panels and blend strips
        for i in range(1, len(resized)):
            prev = resized[i - 1]
            curr = resized[i]

            # Create blend strip from bottom of prev + top of curr
            blended = blend_overlap(prev, curr, blend_px)
            strips.append(blended)

            # Add current panel (without its top blend zone)
            if i < len(resized) - 1:
                strips.append(curr.crop((0, blend_px, curr.width, curr.height)))
            else:
                strips.append(curr.crop((0, blend_px, curr.width, curr.height)))

        # Calculate total height and paste
        total_h = sum(s.height for s in strips)
        canvas = Image.new('RGB', (target_w, total_h), bg)
        y = 0
        for s in strips:
            canvas.paste(s, (0, y))
            y += s.height

    # Mode 2: overlap crop (original behavior)
    elif args.overlap > 0:
        processed = []
        for idx, im in enumerate(resized):
            if idx > 0:
                crop_top = min(args.overlap, im.height - 1)
                im = im.crop((0, crop_top, im.width, im.height))
            processed.append(im)

        total_h = sum(im.height for im in processed)
        canvas = Image.new('RGB', (target_w, total_h), bg)
        y = 0
        for im in processed:
            canvas.paste(im, (0, y))
            y += im.height

    # Mode 3: simple concat
    else:
        total_h = sum(im.height for im in resized)
        canvas = Image.new('RGB', (target_w, total_h), bg)
        y = 0
        for im in resized:
            canvas.paste(im, (0, y))
            y += im.height

    out = Path(args.output)
    ext = out.suffix.lower()
    if ext in ['.jpg', '.jpeg']:
        canvas.save(out, 'JPEG', quality=args.quality, optimize=True)
    elif ext == '.png':
        canvas.save(out, 'PNG')
    else:
        raise SystemExit('Output must end with .jpg/.jpeg/.png')

    print(str(out))
    print('final_size', canvas.size)
    print('target_width', target_w)
    if args.blend > 0:
        print('blend_px', args.blend)
    elif args.overlap > 0:
        print('overlap', args.overlap)


if __name__ == '__main__':
    main()
