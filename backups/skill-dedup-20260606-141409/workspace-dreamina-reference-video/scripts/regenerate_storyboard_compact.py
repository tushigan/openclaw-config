#!/usr/bin/env python3
"""
使用精简模式重新生成故事板（用于解决 ProxyError 问题）

用法：
python3 regenerate_storyboard_compact.py --run-dir /path/to/run
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# 添加 scripts 目录到 Python 路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from scripts.workflow import build_prompts, RATIO_IMAGE_SIZES


def main():
    parser = argparse.ArgumentParser(description="使用精简模式重新生成故事板")
    parser.add_argument("--run-dir", required=True, help="Run 目录路径")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)

    # 读取 brief
    brief_file = run_dir / "brief.json"
    if not brief_file.exists():
        print(json.dumps({"error": f"找不到 brief.json: {brief_file}"}, ensure_ascii=False, indent=2))
        return 1

    with open(brief_file, "r", encoding="utf-8") as f:
        brief = json.load(f)

    # 使用精简模式生成提示词
    print("正在生成精简版提示词...", file=sys.stderr)
    prompts = build_prompts(brief, compact=True)

    storyboard_prompt = prompts["storyboard"]

    print(f"\n精简版故事板提示词大小: {len(storyboard_prompt.encode('utf-8'))} 字节", file=sys.stderr)
    print(f"预计总请求体大小: ~{len(storyboard_prompt.encode('utf-8')) + 525000} 字节 (提示词 + 参考图)", file=sys.stderr)
    print("\n" + "="*80, file=sys.stderr)
    print("精简版提示词内容:", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(storyboard_prompt, file=sys.stderr)
    print("="*80 + "\n", file=sys.stderr)

    # 构建生图命令
    refs_dir = run_dir / "refs"
    original_ref = refs_dir / "original.png"
    identity_ref = refs_dir / "identity-source.png"
    if not identity_ref.exists():
        identity_ref = refs_dir / "identity-board.png"

    storyboard_output = refs_dir / "storyboard.png"

    if not original_ref.exists():
        print(json.dumps({"error": f"找不到参考图: {original_ref}"}, ensure_ascii=False, indent=2))
        return 1

    if not identity_ref.exists():
        print(json.dumps({"error": "找不到身份参考图 (identity-source.png 或 identity-board.png)"}, ensure_ascii=False, indent=2))
        return 1

    # 查找 gpt-image-2-gen 脚本
    gpt_image_script = SCRIPT_DIR.parent.parent.parent / "gpt-image-2-gen" / "scripts" / "gpt-image-2-gen.py"
    if not gpt_image_script.exists():
        # 尝试全局路径
        gpt_image_script = Path("/Users/a123/.openclaw/extensions/gpt-image-2-gen/scripts/gpt-image-2-gen.py")

    if not gpt_image_script.exists():
        print(json.dumps({"error": f"找不到 gpt-image-2-gen.py: {gpt_image_script}"}, ensure_ascii=False, indent=2))
        return 1

    target_size = RATIO_IMAGE_SIZES.get(brief["ratio"], RATIO_IMAGE_SIZES["16:9"])

    command = [
        "python3",
        str(gpt_image_script),
        "--prompt",
        storyboard_prompt,
        "--size",
        target_size,
        "--ref-style",
        str(original_ref),
        "--ref-mascot",
        str(identity_ref),
        "--output",
        str(storyboard_output),
    ]

    print("正在调用生图工具...", file=sys.stderr)
    print(f"命令: {' '.join(command[:3])} ...", file=sys.stderr)

    # 执行命令
    result = subprocess.run(command, capture_output=True, text=True)

    print("\n" + "="*80, file=sys.stderr)
    print("生图结果:", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"返回码: {result.returncode}", file=sys.stderr)
    if result.stdout:
        print(f"标准输出:\n{result.stdout}", file=sys.stderr)
    if result.stderr:
        print(f"标准错误:\n{result.stderr}", file=sys.stderr)
    print("="*80, file=sys.stderr)

    if result.returncode == 0:
        if storyboard_output.exists():
            print(json.dumps({
                "ok": True,
                "message": "精简模式生成成功！",
                "output": str(storyboard_output),
                "prompt_size": len(storyboard_prompt.encode('utf-8')),
                "compression_rate": f"{(1 - len(storyboard_prompt.encode('utf-8')) / 6500) * 100:.1f}%"
            }, ensure_ascii=False, indent=2))
            return 0
        else:
            print(json.dumps({
                "ok": False,
                "message": "命令返回成功但输出文件不存在",
                "expected_output": str(storyboard_output)
            }, ensure_ascii=False, indent=2))
            return 1
    else:
        print(json.dumps({
            "ok": False,
            "message": "生图失败",
            "returncode": result.returncode,
            "stderr": result.stderr,
            "stdout": result.stdout
        }, ensure_ascii=False, indent=2))
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
