#!/usr/bin/env python3
"""Calculate optimal canvas size and segment layout for detail page generation.

Given the model hard limits (max 3840px long edge, max 3:1 aspect ratio,
divisible by 16), this script determines how to fit N screens into the
fewest possible segments using a square or vertical canvas strategy.

Usage:
  python calculate_layout.py --screens 6 --screen-height 1280 --carrier mobile
  python calculate_layout.py --screens 3 --screen-height 1280 --carrier mobile
  python calculate_layout.py --total-height 7680 --carrier mobile
"""
import argparse
import json
import math
import sys


# Model hard limits
MAX_LONG_EDGE = 3840
MAX_RATIO = 3.0  # max(w/h, h/w) <= 3:1
DIVISOR = 16

# Typical mobile screen heights (for reference)
# At width 768-1152, a typical screen is ~1024-1536px tall


def round_up_16(v: int) -> int:
    return ((v + 15) // 16) * 16


def can_fit_rect(width: int, height: int) -> tuple[bool, list[str]]:
    """Check if a rect fits within model constraints."""
    errors = []
    if width < 256 or height < 256:
        errors.append(f'Too small: {width}x{height}')
    if width % DIVISOR != 0:
        errors.append(f'Width {width} not divisible by {DIVISOR}')
    if height % DIVISOR != 0:
        errors.append(f'Height {height} not divisible by {DIVISOR}')
    if max(width, height) > MAX_LONG_EDGE:
        errors.append(f'Long edge {max(width, height)} exceeds {MAX_LONG_EDGE}')
    ratio = max(width, height) / min(width, height) if min(width, height) > 0 else float('inf')
    if ratio > MAX_RATIO:
        errors.append(f'Aspect ratio 1:{ratio:.1f} exceeds 3:1')
    return len(errors) == 0, errors


def calculate_vertical_canvas(total_height: int, preferred_width: int = 1152):
    """Calculate how many vertical strips are needed for total_height.

    Strategy: try to fit as much as possible into one vertical canvas,
    split into multiple if total_height exceeds model limits.
    """
    # Maximum height for a given width under 3:1 ratio constraint
    max_h_by_ratio = int(preferred_width * MAX_RATIO)
    # Also capped by MAX_LONG_EDGE
    max_h = min(max_h_by_ratio, MAX_LONG_EDGE)
    max_h = round_up_16(max_h)

    if total_height <= max_h:
        # Fits in one vertical canvas
        h = round_up_16(total_height)
        valid, errors = can_fit_rect(preferred_width, h)
        if valid:
            return {
                'strategy': 'vertical_single',
                'segments': [{
                    'width': preferred_width,
                    'height': h,
                    'screens_in_segment': 'all',
                }],
                'total_segments': 1,
            }

    # Need to split
    segments = []
    remaining = total_height
    seg_idx = 0
    while remaining > 0:
        seg_h = min(remaining, max_h)
        seg_h = round_up_16(seg_h)
        segments.append({
            'width': preferred_width,
            'height': seg_h,
            'segment_index': seg_idx + 1,
        })
        remaining -= seg_h
        seg_idx += 1

    return {
        'strategy': 'vertical_multi',
        'segments': segments,
        'total_segments': len(segments),
    }


def calculate_square_canvas(total_height: int, preferred_width: int = 1152):
    """Calculate using square canvas strategy.

    Use 3840x3840 square, arrange content in vertical columns.
    This maximizes content per image.
    """
    square_size = round_up_16(MAX_LONG_EDGE)  # 3840
    # Each column uses preferred_width, so columns = 3840 // preferred_width
    columns = max(1, square_size // preferred_width)
    # Height available per column
    col_height = square_size

    # Total content area needed
    total_area = preferred_width * total_height
    # Can we fit in one square?
    cols_needed = math.ceil(total_height / col_height)
    actual_cols = min(cols_needed, columns)

    if cols_needed <= 1:
        # Fits in one column of the square
        h = round_up_16(total_height)
        return {
            'strategy': 'square_single',
            'canvas': f'{preferred_width}x{h}',
            'total_segments': 1,
            'segments': [{
                'width': preferred_width,
                'height': h,
                'layout': 'single_column',
                'screens_in_segment': 'all',
            }],
        }
    elif actual_cols <= columns:
        # Fits in one square, arranged in columns
        return {
            'strategy': 'square_multi_column',
            'canvas': f'{square_size}x{square_size}',
            'total_segments': 1,
            'segments': [{
                'width': square_size,
                'height': square_size,
                'layout': f'{actual_cols}_column_grid',
                'column_width': preferred_width,
                'column_height': col_height,
                'screens_in_segment': 'all',
            }],
        }
    else:
        # Need multiple squares
        squares = math.ceil(total_height / col_height)
        segments = []
        for i in range(squares):
            seg_h = min(col_height, total_height - i * col_height)
            segments.append({
                'width': square_size if i < squares - 1 else preferred_width,
                'height': square_size if i < squares - 1 else round_up_16(seg_h),
                'segment_index': i + 1,
            })
        return {
            'strategy': 'square_multi_square',
            'total_segments': squares,
            'segments': segments,
        }


def recommend_layout(screens: int, screen_height: int, carrier: str = 'mobile',
                     strategy: str = 'auto'):
    """Recommend optimal layout for given content."""
    total_height = screens * screen_height

    if strategy == 'auto':
        # Try square first (fewer segments)
        square_result = calculate_square_canvas(total_height)
        vertical_result = calculate_vertical_canvas(total_height)

        if square_result['total_segments'] <= vertical_result['total_segments']:
            result = square_result
        else:
            result = vertical_result
    elif strategy == 'square':
        result = calculate_square_canvas(total_height)
    else:
        result = calculate_vertical_canvas(total_height)

    # Add screen distribution info
    if screens > 0 and 'segments' in result:
        screens_per_seg = screens / result['total_segments']
        for i, seg in enumerate(result['segments']):
            seg['estimated_screens'] = min(
                screens_per_seg + (1 if i < screens % result['total_segments'] else 0),
                screens
            )
        result['total_screens'] = screens
        result['screen_height'] = screen_height
        result['total_height'] = total_height

    return result


def format_recommendation(result: dict) -> str:
    """Format recommendation for human reading."""
    lines = []
    strategy = result.get('strategy', 'unknown')

    if strategy == 'square_single':
        seg = result['segments'][0]
        lines.append(f"推荐方案：单段竖版")
        lines.append(f"  画板尺寸: {seg['width']}x{seg['height']}")
        lines.append(f"  容纳屏数: 全部 {result.get('total_screens', '?')} 屏")
        lines.append(f"  生成次数: 1 次")
    elif strategy == 'square_multi_column':
        seg = result['segments'][0]
        lines.append(f"推荐方案：方形画板多列布局")
        lines.append(f"  画板尺寸: {seg['width']}x{seg['height']}")
        lines.append(f"  列数: {seg.get('layout', '?')}")
        lines.append(f"  列宽: {seg.get('column_width', '?')}")
        lines.append(f"  列高: {seg.get('column_height', '?')}")
        lines.append(f"  容纳屏数: 全部 {result.get('total_screens', '?')} 屏")
        lines.append(f"  生成次数: 1 次")
    elif strategy == 'square_multi_square':
        lines.append(f"推荐方案：多张方形画板")
        lines.append(f"  需要方形数: {result['total_segments']}")
        for seg in result['segments']:
            idx = seg.get('segment_index', '?')
            lines.append(f"  段 {idx}: {seg['width']}x{seg['height']}")
    elif strategy == 'vertical_single':
        seg = result['segments'][0]
        lines.append(f"推荐方案：单段竖版")
        lines.append(f"  画板尺寸: {seg['width']}x{seg['height']}")
        lines.append(f"  容纳屏数: 全部 {result.get('total_screens', '?')} 屏")
        lines.append(f"  生成次数: 1 次")
    else:
        lines.append(f"推荐方案：多段竖版拼接")
        lines.append(f"  需要段数: {result['total_segments']}")
        for seg in result['segments']:
            idx = seg.get('segment_index', '?')
            lines.append(f"  段 {idx}: {seg['width']}x{seg['height']}")

    lines.append(f"  总内容高度: {result.get('total_height', '?')}px")
    lines.append(f"  屏幕高度: {result.get('screen_height', '?')}px")
    lines.append(f"  屏幕数量: {result.get('total_screens', '?')}")

    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description='Calculate optimal detail page layout')
    ap.add_argument('--screens', type=int, default=0,
                    help='Total number of screens')
    ap.add_argument('--screen-height', type=int, default=1280,
                    help='Height per screen in pixels (default 1280)')
    ap.add_argument('--total-height', type=int, default=0,
                    help='Total content height (alternative to --screens)')
    ap.add_argument('--carrier', default='mobile',
                    help='Target carrier: mobile/pc (default mobile)')
    ap.add_argument('--strategy', default='auto',
                    choices=['auto', 'square', 'vertical'],
                    help='Layout strategy (default auto)')
    ap.add_argument('--json', action='store_true',
                    help='Output as JSON')

    args = ap.parse_args()

    if args.total_height:
        total_height = args.total_height
        screens = 0
    elif args.screens:
        total_height = args.screens * args.screen_height
        screens = args.screens
    else:
        ap.error('Either --screens or --total-height is required')

    result = recommend_layout(screens, args.screen_height, args.carrier, args.strategy)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_recommendation(result))


if __name__ == '__main__':
    main()
