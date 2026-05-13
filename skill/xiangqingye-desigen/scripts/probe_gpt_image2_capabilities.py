#!/usr/bin/env python3
"""探测 gpt-image-2-pro 在当前网关下的真实调用边界。"""

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw

GEN_SCRIPT = Path("/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py")

SIZE_CASES = [
    ("too_small_512", "512x512"),
    ("known_fail_720", "720x720"),
    ("square_1024", "1024x1024"),
    ("square_1440", "1440x1440"),
    ("square_2048", "2048x2048"),
    ("landscape_16_9", "2560x1440"),
    ("portrait_9_16", "1440x2560"),
    ("ratio_3_1", "3840x1280"),
    ("ratio_1_3", "1280x3840"),
    ("too_long_edge", "4096x4096"),
]

PROMPT_LENGTH_CASES = [
    ("prompt_short", 80),
    ("prompt_medium", 1200),
    ("prompt_long", 4000),
    ("prompt_8000", 8000),
    ("prompt_12000", 12000),
    ("prompt_20000", 20000),
]

REF_COUNT_CASES = [0, 1, 2, 3, 4]


def make_prompt(length: int) -> str:
    base = "电商商品测试图，浅奶油色背景，一个简洁饼干产品示意，中文标题：测试商品。画面干净，商品主体清晰。"
    if len(base) >= length:
        return base[:length]
    filler = " 延续统一风格，保持真实商品结构，不使用英文占位符，不添加手机外框，构图稳定。"
    result = base
    while len(result) < length:
        result += filler
    return result[:length]


def ensure_refs(out_dir: Path) -> list[Path]:
    ref_dir = out_dir / "refs"
    ref_dir.mkdir(parents=True, exist_ok=True)
    refs = []
    for i, color in enumerate([(245, 235, 220), (210, 80, 60), (80, 120, 180), (180, 150, 80)], 1):
        path = ref_dir / f"ref_{i}.png"
        if not path.exists():
            img = Image.new("RGB", (512, 512), color)
            draw = ImageDraw.Draw(img)
            draw.text((120, 240), f"ref {i}", fill=(0, 0, 0))
            img.save(path)
        refs.append(path)
    return refs


def run_case(name: str, prompt: str, size: str, output: Path, refs: list[Path], timeout: int) -> dict:
    prompt_file = output.with_suffix(".txt")
    prompt_file.write_text(prompt, encoding="utf-8")
    cmd = ["python3", str(GEN_SCRIPT), "--prompt-file", str(prompt_file), "-s", size, "-o", str(output)]
    for idx, ref in enumerate(refs):
        if idx == 0:
            cmd.extend(["--ref-style", str(ref)])
        elif idx == 1:
            cmd.extend(["--ref-product", str(ref)])
        elif idx == 2:
            cmd.extend(["--ref-logo", str(ref)])
        else:
            cmd.extend(["--ref-element", str(ref)])

    started = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    elapsed = round(time.time() - started, 2)

    returned_size = None
    if output.exists():
        try:
            returned_size = Image.open(output).size
        except Exception:
            returned_size = None

    return {
        "name": name,
        "size": size,
        "prompt_chars": len(prompt),
        "reference_count": len(refs),
        "success": proc.returncode == 0 and output.exists(),
        "exit_code": proc.returncode,
        "elapsed_seconds": elapsed,
        "output": str(output),
        "returned_size": list(returned_size) if returned_size else None,
        "stdout_tail": proc.stdout[-1200:],
        "stderr_tail": proc.stderr[-1200:],
    }


def summarize(results: list[dict]) -> dict:
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    working_sizes = [r["size"] for r in successes]
    return {
        "total": len(results),
        "success_count": len(successes),
        "failure_count": len(failures),
        "working_sizes": working_sizes,
        "failed_cases": [{"name": r["name"], "size": r["size"], "error": (r["stderr_tail"] or r["stdout_tail"])[-500:]} for r in failures],
        "recommendations": build_recommendations(successes, failures),
    }


def build_recommendations(successes: list[dict], failures: list[dict]) -> list[str]:
    recs = []
    if any(r["size"] == "1440x1440" for r in successes):
        recs.append("头图/方图优先使用 1440x1440 或更高，不再默认 720x720/800x800。")
    if any(r["size"] == "720x720" for r in failures):
        recs.append("720x720 在当前 gpt-image-2-pro 网关下不可用，低于最小像素预算。")
    if any(r["size"] == "4096x4096" for r in failures):
        recs.append("最长边不要超过 3840；4K 方形应避免 4096x4096。")
    if any(r["reference_count"] >= 3 and r["success"] for r in successes):
        recs.append("至少 3 张参考图可用；复杂任务仍建议优先保留 style_guide + product，减少超时风险。")
    return recs


def write_markdown(report: dict, path: Path):
    lines = [
        "# gpt-image-2-pro 能力边界报告",
        "",
        f"生成时间：{report['created_at']}",
        f"测试模式：{report['mode']}",
        "",
        "## 摘要",
        f"- 总用例：{report['summary']['total']}",
        f"- 成功：{report['summary']['success_count']}",
        f"- 失败：{report['summary']['failure_count']}",
        "",
        "## 建议",
    ]
    for rec in report["summary"].get("recommendations", []):
        lines.append(f"- {rec}")
    lines.extend(["", "## 用例结果"])
    for r in report["results"]:
        status = "PASS" if r["success"] else "FAIL"
        lines.append(f"- {status} `{r['name']}` size={r['size']} refs={r['reference_count']} prompt={r['prompt_chars']} chars elapsed={r['elapsed_seconds']}s returned={r['returned_size']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="探测 gpt-image-2-pro 能力边界")
    parser.add_argument("--output-dir", required=True, help="报告和测试图输出目录")
    parser.add_argument("--mode", choices=["quick", "full", "prompt"], default="quick", help="quick 用较少 API 调用；full 跑完整矩阵；prompt 只测提示词长度")
    parser.add_argument("--timeout", type=int, default=600, help="单个用例超时时间秒")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    refs = ensure_refs(out_dir)

    cases = []
    if args.mode != "prompt":
        size_cases = SIZE_CASES if args.mode == "full" else [
            ("known_fail_720", "720x720"),
            ("square_1440", "1440x1440"),
            ("portrait_9_16", "1440x2560"),
            ("ratio_1_3", "1280x3840"),
        ]
        for name, size in size_cases:
            cases.append((name, make_prompt(120), size, []))

    if args.mode == "prompt":
        prompt_cases = [("prompt_long", 4000), ("prompt_8000", 8000), ("prompt_12000", 12000), ("prompt_20000", 20000)]
    else:
        prompt_cases = PROMPT_LENGTH_CASES if args.mode == "full" else [("prompt_long", 4000)]
    for name, length in prompt_cases:
        cases.append((name, make_prompt(length), "1440x1440", []))

    if args.mode != "prompt":
        ref_cases = REF_COUNT_CASES if args.mode == "full" else [1, 3]
        for count in ref_cases:
            cases.append((f"refs_{count}", make_prompt(160), "1440x1440", refs[:count]))

    results = []
    for name, prompt, size, case_refs in cases:
        print(f"RUN {name}: size={size}, refs={len(case_refs)}, prompt={len(prompt)}")
        output = out_dir / f"{name}.png"
        try:
            result = run_case(name, prompt, size, output, case_refs, args.timeout)
        except subprocess.TimeoutExpired as e:
            result = {
                "name": name,
                "size": size,
                "prompt_chars": len(prompt),
                "reference_count": len(case_refs),
                "success": False,
                "exit_code": "timeout",
                "elapsed_seconds": args.timeout,
                "output": str(output),
                "returned_size": None,
                "stdout_tail": (e.stdout or "")[-1200:] if isinstance(e.stdout, str) else "",
                "stderr_tail": (e.stderr or "")[-1200:] if isinstance(e.stderr, str) else "timeout",
            }
        results.append(result)
        print("PASS" if result["success"] else "FAIL")

    report = {
        "created_at": datetime.now().isoformat(),
        "mode": args.mode,
        "generator": str(GEN_SCRIPT),
        "results": results,
        "summary": summarize(results),
    }
    json_path = out_dir / "gpt_image2_capability_report.json"
    md_path = out_dir / "gpt_image2_capability_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"报告: {json_path}")
    print(f"报告: {md_path}")


if __name__ == "__main__":
    main()
