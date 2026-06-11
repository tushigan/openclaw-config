#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--preview")
    parser.add_argument("--scene")
    return parser.parse_args()


def alpha_bbox(path: Path) -> list[int] | None:
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return None
    return [bbox[0], bbox[1], bbox[2], bbox[3]]


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    preview_path = Path(args.preview) if args.preview else Path(manifest["preview_path"])
    scene_path = Path(args.scene) if args.scene else Path(manifest["scene_path"])
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    scene_path.parent.mkdir(parents=True, exist_ok=True)

    width = manifest["canvas"]["width"]
    height = manifest["canvas"]["height"]

    background_path = Path(manifest["background_raw_path"])
    background = Image.open(background_path).convert("RGBA")

    # 彻底解决画幅缩小 Bug：画布尺寸必须严格锁定为 manifest 指定的尺寸（即 4K）。
    # 如果 background_raw 还没有被正确 resize，它会在这里被再次保护性拉伸。
    preview = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if background.width != width or background.height != height:
        background = background.resize((width, height), Image.Resampling.LANCZOS)
    preview.alpha_composite(background, (0, 0))

    # v5.1: 新的图层结构 - 原图 + 背景 + 前景组
    group_order = ["00_SOURCE_REF", "01_BG", "05_FOREGROUND_GROUP"]
    image_layers = [
        {
            "group": "00_SOURCE_REF",
            "name": "原图参考",
            "path": manifest["layout_ref"],
            "left": 0,
            "top": 0,
            "crop_to_alpha": False,
            "opacity": 255,
            "hidden": True,
        },
        {
            "group": "01_BG",
            "name": "背景层",
            "path": str(background_path),
            "left": 0,
            "top": 0,
            "crop_to_alpha": False,
            "opacity": 255,
            "hidden": False,
        },
    ]

    # v5.1: 检查是否有前景元素切割结果
    foreground_elements = manifest.get("foreground_elements", [])

    if foreground_elements:
        # 有切割后的元素 - 添加到前景组
        print(f"[PSD Preview] 检测到 {len(foreground_elements)} 个前景元素，将添加到前景组")

        for elem in foreground_elements:
            elem_path = Path(elem["path"])
            if not elem_path.exists():
                print(f"[PSD Preview] ⚠️ 元素文件不存在，跳过: {elem_path}")
                continue

            elem_image = Image.open(elem_path).convert("RGBA")
            preview.alpha_composite(elem_image, (0, 0))

            image_layers.append({
                "group": "05_FOREGROUND_GROUP",
                "name": elem["name"],
                "path": str(elem_path),
                "left": 0,
                "top": 0,
                "crop_to_alpha": True,
                "opacity": 255,
                "hidden": False,
                "alpha_box": alpha_bbox(elem_path),
                "element_info": {
                    "bbox": elem["bbox"],
                    "area": elem["area"],
                    "centroid": elem["centroid"],
                }
            })
    else:
        # 没有切割结果 - 使用原始的前景合并层
        print("[PSD Preview] 未检测到前景元素切割，使用合并的前景层")

        for layer in manifest["layers"]:
            layer_path = Path(layer["layer_path"])
            layer_image = Image.open(layer_path).convert("RGBA")
            preview.alpha_composite(layer_image, (layer["left"], layer["top"]))

            if layer["group"] not in group_order:
                group_order.append(layer["group"])

            image_layers.append(
                {
                    "group": layer["group"],
                    "name": layer["name"],
                    "path": str(layer_path),
                    "left": layer["left"],
                    "top": layer["top"],
                    "crop_to_alpha": True,
                    "opacity": 255,
                    "hidden": layer.get("hidden", False),
                    "alpha_box": alpha_bbox(layer_path),
                }
            )

    preview.save(preview_path)

    # Generate true text layer guides automatically for Title Block
    text_layers = manifest.get("text_layers", [])
    if not text_layers:
        for layer in manifest.get("layers", []):
            if layer["group"] == "03_TITLE":
                # Create a smart editable text layer guide placed on the exact same spot
                text_layers.append({
                    "group": layer["group"],
                    "name": f"[真文字-双击可改] {layer['name']}",
                    "text": "儿童节快乐 (Editable Text)",
                    "left": layer["left"],
                    "top": layer["top"],
                    "width": layer["width"],
                    "height": layer["height"],
                    "fontName": "ArialMT",
                    "fontSize": 48,
                    "fillColor": {"r": 255, "g": 100, "b": 100, "a": 255},
                    "hidden": True,
                    "opacity": 255
                })

    scene = {
        "width": width,
        "height": height,
        "preview_path": str(preview_path),
        "group_order": group_order,
        "image_layers": image_layers,
        "text_layers": text_layers,
        "fonts": manifest.get("fonts", {}),
    }
    scene_path.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")

    print(preview_path)
    print(scene_path)


if __name__ == "__main__":
    main()
