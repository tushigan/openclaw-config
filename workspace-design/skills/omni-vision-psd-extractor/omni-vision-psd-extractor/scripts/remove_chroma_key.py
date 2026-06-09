#!/usr/bin/env python3
import argparse
from pathlib import Path
from PIL import Image

def remove_chroma_key(input_path: Path, output_path: Path, mode: str = "green", tolerance: int = 30) -> None:
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    new_data = []

    # Soft matte boundaries
    high_tol = tolerance + 15
    low_tol = max(0, tolerance - 15)

    if mode == "green":
        # V4.0: Professional Sub-pixel Despill & Edge Matting
        # Pure green #00FF00 removal with aggressive anti-aliasing
        for item in data:
            r, g, b, a = item
            
            # Use strict green dominance heuristic
            green_dom = g - max(r, b)
            
            if green_dom > high_tol and g > 100:
                # Core background: 100% transparent
                new_data.append((0, 0, 0, 0))
            elif green_dom > low_tol and g > 60:
                # Semi-transparent border (anti-aliasing zone)
                # Compute alpha smoothly
                alpha_factor = 1.0 - (green_dom - low_tol) / (high_tol - low_tol)
                alpha_factor = max(0.0, min(1.0, alpha_factor))
                
                # Despill: Neutralize the green channel to remove halos
                avg_rb = (r + b) / 2
                g_despill = int(min(g, avg_rb))
                
                new_alpha = int(a * alpha_factor)
                new_data.append((r, g_despill, b, new_alpha))
            else:
                # Foreground zone: Prevent green reflection (Spill suppression)
                avg_rb = (r + b) / 2
                if g > avg_rb and g > 40:
                    # Gentle despill on foreground reflections
                    g_despill = int(avg_rb + (g - avg_rb) * 0.5)
                    new_data.append((r, min(g, g_despill), b, a))
                else:
                    new_data.append(item)
    elif mode == "white":
        # White screen removal with soft alpha transitions
        for item in data:
            r, g, b, a = item
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            if gray > 240:
                # Map white pixels to transparency
                alpha_factor = (255 - gray) / 15.0
                alpha_factor = max(0.0, min(1.0, alpha_factor))
                new_data.append((r, g, b, int(a * alpha_factor)))
            else:
                new_data.append(item)
    elif mode == "black":
        # Black screen removal with soft alpha transitions
        for item in data:
            r, g, b, a = item
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            if gray < 30:
                # Map black pixels to transparency
                alpha_factor = gray / 30.0
                alpha_factor = max(0.0, min(1.0, alpha_factor))
                new_data.append((r, g, b, int(a * alpha_factor)))
            else:
                new_data.append(item)
    else:
        # Custom RGB distance with smooth transition
        try:
            if mode.startswith("#"):
                hex_val = mode.lstrip("#")
                kr = int(hex_val[0:2], 16)
                kg = int(hex_val[2:4], 16)
                kb = int(hex_val[4:6], 16)
            else:
                kr, kg, kb = 0, 255, 0
        except Exception:
            kr, kg, kb = 0, 255, 0

        for item in data:
            r, g, b, a = item
            dist = ((r - kr)**2 + (g - kg)**2 + (b - kb)**2)**0.5
            # Transition window
            if dist < low_tol:
                new_data.append((0, 0, 0, 0))
            elif dist < high_tol:
                alpha_factor = (dist - low_tol) / (high_tol - low_tol)
                alpha_factor = max(0.0, min(1.0, alpha_factor))
                # Despill for custom key colors (blend with black or neutral color)
                new_data.append((r, g, b, int(a * alpha_factor)))
            else:
                new_data.append(item)

    img.putdata(new_data)

    if mode == "green":
        try:
            from PIL import ImageFilter
            r_ch, g_ch, b_ch, a_ch = img.split()
            a_eroded = a_ch.filter(ImageFilter.MinFilter(3))
            a_feathered = a_eroded.filter(ImageFilter.GaussianBlur(radius=1.0))
            img = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_feathered))
        except Exception as e:
            print(f"[warning] Failed to apply alpha matting filter: {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")

def main():
    parser = argparse.ArgumentParser(description="Chroma key remover for reverse PSD layers")
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output image path")
    parser.add_argument("--mode", default="green", help="Mode: green, white, or hex color like #00ff00")
    parser.add_argument("--tolerance", type=int, default=30, help="Chroma key tolerance value")
    args = parser.parse_args()

    remove_chroma_key(Path(args.input), Path(args.output), args.mode, args.tolerance)

if __name__ == "__main__":
    main()
