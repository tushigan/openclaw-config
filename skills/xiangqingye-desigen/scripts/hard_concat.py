#!/usr/bin/env python3
"""Pure hard concatenation for closed-boundary segments.

Each segment is a complete independent design block with:
- Top boundary: cream band + gold decorative elements
- Bottom boundary: cream band + gold decorative elements

Direct vertical stacking, NO blend, NO crop, NO color correction.
"""
from PIL import Image
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: hard_concat.py <output> <segment1> <segment2> ...")
        sys.exit(1)

    output = sys.argv[1]
    inputs = sys.argv[2:]

    # Load segments
    segments = []
    for path in inputs:
        img = Image.open(path).convert('RGB')
        segments.append(img)
        print(f'Loaded: {path} ({img.width}x{img.height})')

    if len(segments) < 2:
        print('Need at least 2 segments')
        sys.exit(1)

    # Verify width consistency
    widths = [s.width for s in segments]
    if len(set(widths)) > 1:
        print(f'Width mismatch: {widths}')
        sys.exit(1)

    w = widths[0]

    # Pure hard concat: direct vertical stacking
    total_h = sum(s.height for s in segments)
    result = Image.new('RGB', (w, total_h), (255, 255, 255))

    y = 0
    for i, seg in enumerate(segments):
        result.paste(seg, (0, y))
        print(f'Stacked segment {i + 1} at y={y}')
        y += seg.height

    result.save(output, quality=95)
    print(f'\nSaved: {output} ({result.width}x{result.height})')


if __name__ == '__main__':
    main()