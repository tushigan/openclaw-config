#!/usr/bin/env python3
"""检查详情页分段是否具备硬拼接条件。"""

import argparse
import json
from pathlib import Path
from PIL import Image, ImageStat


def band_stats(img: Image.Image, top: bool, height: int = 60) -> dict:
    crop = img.crop((0, 0, img.width, min(height, img.height))) if top else img.crop((0, max(0, img.height - height), img.width, img.height))
    stat = ImageStat.Stat(crop.convert("RGB"))
    return {
        "mean": [round(x, 2) for x in stat.mean],
        "stddev": [round(x, 2) for x in stat.stddev],
    }


def main():
    parser = argparse.ArgumentParser(description="检查分段边界和拼接就绪状态")
    parser.add_argument("segments", nargs="+", help="分段图片路径，按拼接顺序")
    parser.add_argument("--report", default="", help="报告输出路径")
    args = parser.parse_args()

    paths = [Path(p) for p in args.segments]
    for path in paths:
        if not path.exists():
            raise SystemExit(f"分段不存在: {path}")

    images = [Image.open(path).convert("RGB") for path in paths]
    widths = [img.width for img in images]
    issues = []
    warnings = []

    if len(set(widths)) != 1:
        issues.append(f"分段宽度不一致: {widths}")

    details = []
    for i, (path, img) in enumerate(zip(paths, images), 1):
        top = band_stats(img, True)
        bottom = band_stats(img, False)
        if img.width % 16 != 0 or img.height % 16 != 0:
            warnings.append(f"{path.name}: 宽高不可被 16 整除，后续再生图可能不稳定。")
        details.append({
            "index": i,
            "path": str(path),
            "size": {"width": img.width, "height": img.height},
            "top_band": top,
            "bottom_band": bottom,
        })

    if len(images) < 2:
        warnings.append("只有一个分段，无法验证多段硬拼接关系。")

    report = {
        "passed": not issues,
        "issues": issues,
        "warnings": warnings,
        "segments": details,
        "rule": "所有分段必须宽度一致，并在 prompt 中强制完整上下收边；本脚本做基础拼接就绪检查。",
        "next_action": "可执行 hard_concat.py" if not issues else "修正分段后再拼接",
    }

    report_path = Path(args.report) if args.report else paths[0].parent / "boundary_check_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"边界检查报告: {report_path}")

    if issues:
        print("FAIL: 分段拼接检查未通过")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)
    print("PASS: 分段基础拼接检查通过")


if __name__ == "__main__":
    main()
