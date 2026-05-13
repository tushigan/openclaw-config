#!/usr/bin/env python3
"""Validate and compute pixel dimensions for detail page generation.

Ensures dimensions comply with endpoint requirements:
- Both width and height must be divisible by 16
- Longest edge must not exceed 3840
- Aspect ratio must not exceed 3:1 (or 1:3 for vertical)

Usage:
  python validate_dimensions.py --ratio 1:3 --screens 2
  python validate_dimensions.py --ratio 5:15 --base-width 1152
  python validate_dimensions.py --width 736 --height 2208  # validate existing

Outputs valid pixel dimensions as `WxH` on stdout, or exits with error.
"""
import argparse
import sys
from math import gcd


# Endpoint hard limits (n.lconai.com + gpt-image-2-pro)
MAX_LONG_EDGE = 3840
MIN_DIM = 256
DIVISOR = 16


def round_up(v: int, to: int = DIVISOR) -> int:
    """Round up to the nearest multiple of `to`."""
    return ((v + to - 1) // to) * to


def parse_ratio(raw: str):
    """Parse 'W:H' ratio string, return (w, h) as ints."""
    parts = raw.replace(' ', '').split(':')
    if len(parts) != 2:
        raise ValueError(f'Invalid ratio format: {raw} (expected W:H)')
    w, h = int(parts[0]), int(parts[1])
    if w <= 0 or h <= 0:
        raise ValueError(f'Ratio values must be positive: {raw}')
    return w, h


def compute_dimensions(ratio_w, ratio_h, screens=1, base_width=0):
    """Compute valid pixel dimensions from ratio.

    Strategy:
    1. Scale ratio to target pixel range based on number of screens
    2. Ensure both dimensions are divisible by 16
    3. Ensure longest edge <= MAX_LONG_EDGE
    4. Return (width, height)
    """
    total_ratio_w = ratio_w * screens
    total_ratio_h = ratio_h * screens

    # Determine target width:
    # For mobile detail pages, a comfortable width is 736-1152px
    # We pick the largest width that keeps the height within limits
    if base_width:
        w = base_width
    else:
        # Default: use a reasonable mobile width
        # Height = w * (ratio_h/ratio_w) * screens
        # We want height <= MAX_LONG_EDGE
        # w <= MAX_LONG_EDGE * ratio_w / (ratio_h * screens)
        max_w_by_height = int(MAX_LONG_EDGE * ratio_w / (ratio_h * screens))
        # Also cap at a comfortable mobile width
        w = min(max_w_by_height, 1152)
        # Ensure minimum
        w = max(w, MIN_DIM)

    w = round_up(w)

    # Compute height from ratio
    h = round(w * total_ratio_h / total_ratio_w)
    h = round_up(h)

    # Check longest edge
    long_edge = max(w, h)
    if long_edge > MAX_LONG_EDGE:
        # Scale down proportionally
        scale = MAX_LONG_EDGE / long_edge
        w = round_up(int(w * scale))
        h = round_up(int(h * scale))

    # Final validation
    if w < MIN_DIM or h < MIN_DIM:
        raise ValueError(f'Dimensions too small after scaling: {w}x{h} (min {MIN_DIM})')

    if w % DIVISOR != 0 or h % DIVISOR != 0:
        raise SystemExit(f'Bug: {w}x{h} not divisible by {DIVISOR}')

    return w, h


def validate_dimensions(w, h):
    """Validate existing dimensions against all rules."""
    errors = []

    if w < MIN_DIM or h < MIN_DIM:
        errors.append(f'Dimension too small: {w}x{h} (min {MIN_DIM})')
    if w % DIVISOR != 0:
        errors.append(f'Width {w} not divisible by {DIVISOR}')
    if h % DIVISOR != 0:
        errors.append(f'Height {h} not divisible by {DIVISOR}')
    if max(w, h) > MAX_LONG_EDGE:
        errors.append(f'Long edge {max(w, h)} exceeds limit {MAX_LONG_EDGE}')

    ratio = max(w, h) / min(w, h) if min(w, h) > 0 else float('inf')
    if ratio > 3.0:
        errors.append(f'Aspect ratio 1:{ratio:.1f} exceeds limit 3:1')

    return errors


def main():
    ap = argparse.ArgumentParser(description='Validate/compute detail page dimensions')
    ap.add_argument('--ratio', default='', help='Logical ratio like 1:3 or 5:15')
    ap.add_argument('--screens', type=int, default=1,
                    help='Number of screens in this segment (default 1)')
    ap.add_argument('--base-width', type=int, default=0,
                    help='Force a specific base width')
    ap.add_argument('--width', type=int, default=0, help='Validate existing width')
    ap.add_argument('--height', type=int, default=0, help='Validate existing height')
    ap.add_argument('--canvas', default='', choices=['square'],
                    help='Canvas mode: square for 3840x3840 max square')

    args = ap.parse_args()

    # Mode 0: Square canvas
    if args.canvas == 'square':
        size = MAX_LONG_EDGE  # 3840
        w = round_up(size)
        h = round_up(size)
        errors = validate_dimensions(w, h)
        if errors:
            for e in errors:
                print(f'ERROR: {e}', file=sys.stderr)
            sys.exit(1)
        print(f'{w}x{h}')
        print(f'canvas: square {w}x{h}')
        print(f'long_edge: {max(w, h)} (limit {MAX_LONG_EDGE})')
        print(f'divisible_by_16: width={w % 16 == 0}, height={h % 16 == 0}')
        print('VALID')
        return

    # Mode 1: Validate existing dimensions
    if args.width and args.height:
        errors = validate_dimensions(args.width, args.height)
        if errors:
            for e in errors:
                print(f'ERROR: {e}', file=sys.stderr)
            sys.exit(1)
        print(f'{args.width}x{args.height}')
        print('VALID')
        return

    # Mode 2: Compute from ratio
    if not args.ratio:
        ap.error('Either --ratio, --canvas, or (--width + --height) is required')

    rw, rh = parse_ratio(args.ratio)
    w, h = compute_dimensions(rw, rh, args.screens, args.base_width)

    # Validate
    errors = validate_dimensions(w, h)
    if errors:
        for e in errors:
            print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

    print(f'{w}x{h}')
    print(f'ratio: {rw}:{rh} (×{args.screens} screens)')
    print(f'long_edge: {max(w, h)} (limit {MAX_LONG_EDGE})')
    print(f'divisible_by_16: width={w % 16 == 0}, height={h % 16 == 0}')
    print('VALID')


if __name__ == '__main__':
    main()
