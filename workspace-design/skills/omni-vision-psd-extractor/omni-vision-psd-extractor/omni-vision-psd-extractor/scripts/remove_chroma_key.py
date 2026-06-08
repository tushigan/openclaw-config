#!/usr/bin/env python3
import argparse
from pathlib import Path
from PIL import Image

def remove_chroma_key(input_path: Path, output_path: Path, mode: str = "green", tolerance: int = 30) -> None:
    img = Image.open(input_path).convert("RGBA")
    high_tol = tolerance + 15
    low_tol = max(0, tolerance - 15)

    try:
        import numpy as np
        data = np.array(img, dtype=np.float32)
        r, g, b, a = data[..., 0], data[..., 1], data[..., 2], data[..., 3]
        
        if mode == "green":
            max_rb = np.maximum(r, b)
            green_dom = g - max_rb
            
            # core background
            bg_mask = (green_dom > high_tol) & (g > 100)
            a[bg_mask] = 0
            
            # anti-aliasing zone
            aa_mask = (green_dom > low_tol) & (green_dom <= high_tol) & (g > 60)
            if np.any(aa_mask):
                alpha_factor = 1.0 - (green_dom[aa_mask] - low_tol) / (high_tol - low_tol)
                alpha_factor = np.clip(alpha_factor, 0.0, 1.0)
                avg_rb = (r[aa_mask] + b[aa_mask]) / 2.0
                g_despill = np.minimum(g[aa_mask], avg_rb)
                g[aa_mask] = g_despill
                a[aa_mask] = a[aa_mask] * alpha_factor
                
            # foreground spill suppression
            avg_rb_full = (r + b) / 2.0
            fg_mask = (~bg_mask) & (~aa_mask) & (g > avg_rb_full) & (g > 40)
            if np.any(fg_mask):
                g_despill_fg = avg_rb_full[fg_mask] + (g[fg_mask] - avg_rb_full[fg_mask]) * 0.5
                g[fg_mask] = np.minimum(g[fg_mask], g_despill_fg)

        elif mode == "white":
            gray = 0.299 * r + 0.587 * g + 0.114 * b
            white_mask = gray > 240
            if np.any(white_mask):
                alpha_factor = (255.0 - gray[white_mask]) / 15.0
                alpha_factor = np.clip(alpha_factor, 0.0, 1.0)
                a[white_mask] = a[white_mask] * alpha_factor

        elif mode == "black":
            gray = 0.299 * r + 0.587 * g + 0.114 * b
            black_mask = gray < 30
            if np.any(black_mask):
                alpha_factor = gray[black_mask] / 30.0
                alpha_factor = np.clip(alpha_factor, 0.0, 1.0)
                a[black_mask] = a[black_mask] * alpha_factor

        else:
            try:
                if mode.startswith("#"):
                    hex_val = mode.lstrip("#")
                    kr, kg, kb = int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16)
                else:
                    kr, kg, kb = 0, 255, 0
            except Exception:
                kr, kg, kb = 0, 255, 0
                
            dist = np.sqrt((r - kr)**2 + (g - kg)**2 + (b - kb)**2)
            bg_mask = dist < low_tol
            a[bg_mask] = 0
            
            aa_mask = (dist >= low_tol) & (dist < high_tol)
            if np.any(aa_mask):
                alpha_factor = (dist[aa_mask] - low_tol) / (high_tol - low_tol)
                alpha_factor = np.clip(alpha_factor, 0.0, 1.0)
                a[aa_mask] = a[aa_mask] * alpha_factor

        img = Image.fromarray(np.clip(data, 0, 255).astype(np.uint8), "RGBA")

    except ImportError:
        # Fallback Graceful Degradation: Pure Python loops
        print("[fallback] Numpy not found. Using pure python loop.")
        data = img.getdata()
        new_data = []
        if mode == "green":
            for item in data:
                r, g, b, a = item
                green_dom = g - max(r, b)
                if green_dom > high_tol and g > 100:
                    new_data.append((0, 0, 0, 0))
                elif green_dom > low_tol and g > 60:
                    alpha_factor = max(0.0, min(1.0, 1.0 - (green_dom - low_tol) / (high_tol - low_tol)))
                    avg_rb = (r + b) / 2
                    g_despill = int(min(g, avg_rb))
                    new_data.append((r, g_despill, b, int(a * alpha_factor)))
                else:
                    avg_rb = (r + b) / 2
                    if g > avg_rb and g > 40:
                        g_despill = int(avg_rb + (g - avg_rb) * 0.5)
                        new_data.append((r, min(g, g_despill), b, a))
                    else:
                        new_data.append(item)
        elif mode == "white":
            for item in data:
                r, g, b, a = item
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                if gray > 240:
                    alpha_factor = max(0.0, min(1.0, (255 - gray) / 15.0))
                    new_data.append((r, g, b, int(a * alpha_factor)))
                else:
                    new_data.append(item)
        elif mode == "black":
            for item in data:
                r, g, b, a = item
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                if gray < 30:
                    alpha_factor = max(0.0, min(1.0, gray / 30.0))
                    new_data.append((r, g, b, int(a * alpha_factor)))
                else:
                    new_data.append(item)
        else:
            try:
                if mode.startswith("#"):
                    hex_val = mode.lstrip("#")
                    kr, kg, kb = int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16)
                else:
                    kr, kg, kb = 0, 255, 0
            except Exception:
                kr, kg, kb = 0, 255, 0

            for item in data:
                r, g, b, a = item
                dist = ((r - kr)**2 + (g - kg)**2 + (b - kb)**2)**0.5
                if dist < low_tol:
                    new_data.append((0, 0, 0, 0))
                elif dist < high_tol:
                    alpha_factor = max(0.0, min(1.0, (dist - low_tol) / (high_tol - low_tol)))
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
