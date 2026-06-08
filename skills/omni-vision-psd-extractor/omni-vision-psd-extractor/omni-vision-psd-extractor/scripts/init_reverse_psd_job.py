#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--job-spec", required=True)
    parser.add_argument("--out-dir", required=True)
    return parser.parse_args()


def crop_image(image: Image.Image, spec: dict[str, int]) -> Image.Image:
    left = spec["left"]
    top = spec["top"]
    right = left + spec["width"]
    bottom = top + spec["height"]
    return image.crop((left, top, right, bottom))


def main() -> None:
    args = parse_args()
    source = Path(args.source)
    job_spec_path = Path(args.job_spec)
    out_dir = Path(args.out_dir)

    job = json.loads(job_spec_path.read_text(encoding="utf-8"))
    canvas = job["canvas"]
    
    layers = job.get("layers", [])
    if not layers:
        layers = [{
            "key": "foreground",
            "group": "05_FOREGROUND",
            "name": "Foreground",
            "prompt": "Foreground",
            "left": 0, 
            "top": 0, 
            "width": canvas["width"], 
            "height": canvas["height"]
        }]

    refs_dir = out_dir / "refs"
    raw_dir = out_dir / "raw"
    layer_dir = out_dir / "layers"
    refs_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    layer_dir.mkdir(parents=True, exist_ok=True)

    source_image = Image.open(source).convert("RGBA")
    
    # 限制最大分辨率，防大图片在传输或处理时导致Maximum call stack size exceeded或内存溢出
    max_size = 4096
    orig_w = source_image.width
    orig_h = source_image.height
    if orig_w > max_size or orig_h > max_size:
        if orig_w > orig_h:
            new_w = max_size
            new_h = int(orig_h * (max_size / orig_w))
        else:
            new_h = max_size
            new_w = int(orig_w * (max_size / orig_h))
        new_w = ((new_w + 15) // 16) * 16
        new_h = ((new_h + 15) // 16) * 16
        
        scale_x = new_w / orig_w
        scale_y = new_h / orig_h
        print(f"[info] Source image exceeds max limit. Downscaling from {orig_w}x{orig_h} to {new_w}x{new_h} (scale={scale_x:.4f})")
        source_image = source_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 对应缩放 canvas 宽度和高度
        orig_canvas_w = canvas["width"]
        orig_canvas_h = canvas["height"]
        new_canvas_w = ((int(orig_canvas_w * scale_x) + 15) // 16) * 16
        new_canvas_h = ((int(orig_canvas_h * scale_y) + 15) // 16) * 16
        
        canvas_scale_x = new_canvas_w / orig_canvas_w
        canvas_scale_y = new_canvas_h / orig_canvas_h
        
        canvas["width"] = new_canvas_w
        canvas["height"] = new_canvas_h
        
        # 对应缩放所有图层的 bbox 坐标
        for layer in layers:
            layer["left"] = int(layer["left"] * canvas_scale_x)
            layer["top"] = int(layer["top"] * canvas_scale_y)
            layer["width"] = int(layer["width"] * canvas_scale_x)
            layer["height"] = int(layer["height"] * canvas_scale_y)

    layout = source_image.resize((canvas["width"], canvas["height"]), Image.Resampling.LANCZOS)

    source_copy = refs_dir / "source-original.png"
    layout_ref = refs_dir / "layout_ref.png"
    source_image.save(source_copy)
    layout.save(layout_ref)

    manifest_layers = []
    for layer in layers:
        # 🔒 麦肯锡闭环修复：小尺寸元素不再静默丢弃，改为"全画幅安全提取模式"
        # 气球、纸飞机、小图标等前景元素在 N层模式下尺寸可能很小（<200px），
        # 但它们是用户明确要求提取的元素，丢弃就是功能性缺失。
        # 全画幅模式：直接用整张画布作为 ref_path，让 API 在全图上语义定位目标元素。
        if max(int(layer["width"]), int(layer["height"])) < 200 and layer["group"] not in ["02_LOGO", "03_TITLE"]:
            print(f"[info] Layer '{layer['key']}' (size={int(layer['width'])}x{int(layer['height'])}) is small (<200px). "
                  f"Switching to full-canvas safe-extract mode instead of discarding.")
            # 扩展为全画幅
            layer["left"] = 0
            layer["top"] = 0
            layer["width"] = canvas["width"]
            layer["height"] = canvas["height"]

        ref_path = refs_dir / f'{layer["key"]}_ref.png'
        raw_path = raw_dir / f'{layer["key"]}.png'
        layer_path = layer_dir / f'{layer["key"]}.png'

        # =========================================
        # 核心修复：为 BBox 添加极度宽松的动态“出血”范围 (Padding)
        # 防止大模型猜测的坐标过紧，导致边缘（如飞机尖端、伸出的手、飘带等）被物理刀锋切断。
        # 横向/纵向各扩充 50% + 150像素的缓冲带，并严格限制在画布边界内。
        # 由于合成脚本会自动去透明度并精准对齐，扩充得再大也不会导致错位！
        # =========================================
        padding_x = int(layer["width"] * 0.5) + 150
        padding_y = int(layer["height"] * 0.5) + 150
        
        orig_left = layer["left"]
        orig_top = layer["top"]
        orig_right = orig_left + layer["width"]
        orig_bottom = orig_top + layer["height"]
        
        new_left = max(0, orig_left - padding_x)
        new_top = max(0, orig_top - padding_y)
        new_right = min(canvas["width"], orig_right + padding_x)
        new_bottom = min(canvas["height"], orig_bottom + padding_y)
        
        # 将扩充后的安全坐标覆写回 layer 对象，
        # 这样底层切图和后续的 PSD 合成对齐将完美继承这个带有外扩的安全范围！
        layer["left"] = new_left
        layer["top"] = new_top
        layer["width"] = new_right - new_left
        layer["height"] = new_bottom - new_top

        crop = crop_image(layout, layer)
        crop.save(ref_path)

        manifest_layers.append(
            {
                "key": layer["key"],
                "group": layer["group"],
                "name": layer["name"],
                "prompt": layer.get("prompt", layer.get("name", layer["key"])),
                "left": layer["left"],
                "top": layer["top"],
                "width": layer["width"],
                "height": layer["height"],
                "ref_path": str(ref_path),
                "raw_path": str(raw_path),
                "layer_path": str(layer_path),
                "hidden": bool(layer.get("hidden", False)),
                "lossless_extract": bool(layer.get("lossless_extract", layer["group"] in ["02_LOGO", "03_TITLE"])),
            }
        )

    manifest = {
        "source_path": str(source_copy),
        "layout_ref": str(layout_ref),
        "background_raw_path": str(raw_dir / "background.png"),
        "parallel_plan_path": str(out_dir / "parallel-plan.json"),
        "parallel_state_path": str(out_dir / "parallel-state.json"),
        "preview_path": str(out_dir / "reverse-preview.png"),
        "scene_path": str(out_dir / "scene.json"),
        "psd_path": str(out_dir / "layered-output.psd"),
        "canvas": canvas,
        "layers": manifest_layers,
    }

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(manifest_path)


if __name__ == "__main__":
    main()
