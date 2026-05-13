#!/usr/bin/env python3
"""详情页手稿基础 QA：比例、标注、占位符和常见禁用元素检查。"""

import argparse
import json
import re
from pathlib import Path
from PIL import Image

FORBIDDEN_TEXT_PATTERNS = [
    r"第\s*\d+\s*屏",
    r"Screen\s*\d+",
    r"Column\s*\d+",
    r"\d+\s*/\s*\d+",
    r"标题占位",
    r"卖点条",
    r"XXX+",
    r"Lorem",
]


def detect_suspicious_phone_frame(img: Image.Image) -> list[str]:
    warnings = []
    w, h = img.size
    if h > w * 1.8:
        warnings.append("图片整体过窄过高，可能不是 4 列方形手稿。")
    return warnings


def run_ocr_text_check(image_path: Path) -> tuple[list[str], str]:
    text_file = image_path.with_suffix(".ocr.txt")
    if not text_file.exists():
        return [], "未找到同名 .ocr.txt，跳过文字 OCR 检查；如需严格检查，请先生成 OCR 文本。"
    text = text_file.read_text(encoding="utf-8", errors="ignore")
    issues = []
    for pattern in FORBIDDEN_TEXT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"发现禁用文字模式: {pattern}")
    return issues, text


def main():
    parser = argparse.ArgumentParser(description="校验详情页手稿")
    parser.add_argument("image", help="手稿图片路径")
    parser.add_argument("--expected-size", default="2880x2880", help="期望尺寸，默认 2880x2880")
    parser.add_argument("--report", default="", help="报告输出路径")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        raise SystemExit(f"图片不存在: {image_path}")

    expected_w, expected_h = [int(x) for x in args.expected_size.lower().split("x")]
    img = Image.open(image_path).convert("RGB")
    issues = []
    warnings = []

    if img.size != (expected_w, expected_h):
        issues.append(f"尺寸不符合预期: 实际 {img.width}x{img.height}，期望 {expected_w}x{expected_h}")

    if img.width % 16 != 0 or img.height % 16 != 0:
        issues.append("宽高必须可被 16 整除。")

    if abs((img.width / img.height) - (expected_w / expected_h)) > 0.02:
        issues.append("画板比例不符合预期。")

    warnings.extend(detect_suspicious_phone_frame(img))
    text_issues, ocr_text = run_ocr_text_check(image_path)
    issues.extend(text_issues)

    passed = not issues
    report = {
        "image": str(image_path),
        "size": {"width": img.width, "height": img.height},
        "expected_size": args.expected_size,
        "passed": passed,
        "issues": issues,
        "warnings": warnings,
        "ocr_note": ocr_text if isinstance(ocr_text, str) and len(ocr_text) < 160 else "OCR 文本已读取",
        "next_action": "可进入切段确认" if passed else "必须返工手稿或人工确认后再继续",
    }

    report_path = Path(args.report) if args.report else image_path.with_name("wireframe_qa_report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"手稿 QA 报告: {report_path}")
    if passed:
        print("PASS: 手稿基础 QA 通过")
    else:
        print("FAIL: 手稿基础 QA 未通过")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
