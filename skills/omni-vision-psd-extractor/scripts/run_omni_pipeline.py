#!/usr/bin/env python3
import argparse
import sys
import subprocess
import json
import shutil
from pathlib import Path

from runtime_config import WORKSPACE_DESIGN, WORKSPACE_MAIN, load_runtime_env

try:
    from PIL import Image
except ImportError:
    print("\n[WARNING] Pillow library not found. Auto-generation requires 'Pillow'. Try: pip install Pillow")
    Image = None

def run_step(cmd, step_name):
    print(f"\n[{step_name}] Starting...")
    print(f"Command: {' '.join(cmd)}")
    
    env = load_runtime_env()

    result = subprocess.run(cmd, env=env)
    
    if result.returncode != 0:
        print(f"\n[ERROR] [{step_name}] Failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    else:
        print(f"[SUCCESS] [{step_name}] Completed successfully.")

def detect_auto_source(conv_id=None):
    import os
    import time
    from pathlib import Path
    
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    candidates = []
    
    # 1. 优先在会话隔离的作用域目录中查找
    if conv_id:
        brain_dir = Path.home() / ".gemini" / "antigravity" / "brain" / conv_id
        if brain_dir.exists():
            try:
                for entry in os.scandir(brain_dir):
                    if entry.is_file() and entry.name.startswith("media__"):
                        p = Path(entry.path)
                        if p.suffix.lower() in valid_exts:
                            try:
                                mtime = entry.stat().st_mtime
                                candidates.append((mtime, p))
                            except Exception:
                                pass
            except Exception as e:
                print(f"[AUTO-SOURCE:WARNING] Failed to scan conversation brain dir {brain_dir}: {e}")
                
            if candidates:
                # 💡 第一性原理核心修正：底图必须是用户发送给 AI 的“最最初始”（最老）的那张图！
                # 按修改时间从旧到新（升序）排序，选择最老的那张图，彻底过滤排障截图污染。
                candidates.sort(key=lambda x: x[0])
                mtime, oldest_path = candidates[0]
                import time as time_mod
                print(f"\n[AUTO-SOURCE] Isolated conversation brain folder. Detected oldest original image: {oldest_path} (mtime: {time_mod.strftime('%Y-%m-%d %H:%M:%S', time_mod.localtime(mtime))})")
                return str(oldest_path)
            else:
                print(f"\n[AUTO-SOURCE:WARNING] No media__ files found in conversation brain folder {brain_dir}. Falling back to global scans.")

    # 2. 全局降级扫描（Downloads 和 Workspace）- 取最新文件
    scan_dirs = [
        Path.home() / "Downloads",
        WORKSPACE_DESIGN,
        WORKSPACE_MAIN,
    ]
    
    for d in scan_dirs:
        if not d.exists():
            continue
        try:
            for entry in os.scandir(d):
                if entry.is_file():
                    p = Path(entry.path)
                    if p.suffix.lower() in valid_exts:
                        # 排除管线自身生成的图层和预览图，防止循环复用
                        name = p.name.lower()
                        if any(x in name for x in ["grid", "preview", "layout_ref", "source-original", "layered-output"]):
                            continue
                        # 排除在 outputs 等各种历史结果目录下的文件，防止循环嵌套
                        if any(excluded in p.parts for excluded in ["outputs", "jobs", "reverse-psd-jobs", "omni-out", ".agents", "node_modules"]):
                            continue
                        try:
                            mtime = entry.stat().st_mtime
                            candidates.append((mtime, p))
                        except Exception:
                            pass
        except Exception as e:
            print(f"[AUTO-SOURCE:WARNING] Failed to scan {d}: {e}")
            
    if not candidates:
        print("\n[ERROR] [AUTO-SOURCE] No source image found in Downloads, workspace, or brain uploads. Please provide --source explicitly.")
        sys.exit(1)
        
    # 全局模式下按修改时间从新到旧排序
    candidates.sort(key=lambda x: x[0], reverse=True)
    mtime, best_path = candidates[0]
    import time as time_mod
    print(f"\n[AUTO-SOURCE] Fallback global scan. Automatically detected most recent image: {best_path} (mtime: {time_mod.strftime('%Y-%m-%d %H:%M:%S', time_mod.localtime(mtime))})")
    return str(best_path)

def main():
    parser = argparse.ArgumentParser(description="Omni-Vision PSD Extractor Pipeline Orchestrator")
    parser.add_argument("--source", default="auto", help="Path to original source image, or 'auto' to auto-detect the most recent image")
    parser.add_argument("--job-spec", required=False, help="Path to generated job-spec.json (optional, used for advanced N-layer mode)")
    parser.add_argument("--out-dir", required=True, help="Path to output directory")
    parser.add_argument("--auto-2-layer", action="store_true", default=True, help="Auto-generate a 2-layer config (background + foreground). This is now the DEFAULT mode.")
    parser.add_argument("--disable-2-layer", action="store_true", help="Disable 2-layer mode and require --job-spec for N-layer mode")
    parser.add_argument("--bg-prompt", type=str, default="【极其重要：绝对禁止凭空生成完全不同的风景！必须严格保持原图中的背景结构、光影和色彩不变，仅仅智能脑补被移除的前景区域。】将图片中的背景提取出来，需要将前景所有元素全部剔除，只保留背景。", help="Prompt for background layer")
    parser.add_argument("--fg-prompt", type=str, default="将图片中除了背景之外的所有前景元素全部提取出来。【极其重要：强制将背景全部填充为纯正的绿幕（纯绿色，Hex: #00FF00）！绝对不要生成假透明像素方格背景！】", help="Prompt for foreground layer")
    parser.add_argument("--prompt-append-file", type=str, default=None, help="File whose content will be appended to both bg and fg prompts")
    parser.add_argument("--conv-id", default=None, help="The current conversation ID to isolate and locate the original uploaded image")
    args = parser.parse_args()

    # 如果用户明确禁用 2-layer 模式，则需要提供 job-spec
    if args.disable_2_layer:
        args.auto_2_layer = False

    if not args.auto_2_layer and not args.job_spec:
        print("\n[ERROR] You must provide either --job-spec or use the default 2-layer mode")
        print("[HINT] Remove --disable-2-layer to use the default 2-layer mode (background + foreground)")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    source_str = args.source
    if source_str.startswith("http://") or source_str.startswith("https://"):
        import urllib.request
        import tempfile
        import os
        print(f"\\n[INIT] Downloading source image from URL: {source_str}")
        fd, temp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        
        req = urllib.request.Request(source_str, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        source_str = temp_path
        print(f"[INIT] Downloaded to: {source_str}")
    elif source_str == "auto":
        source_str = detect_auto_source(args.conv_id)
    source_path = Path(source_str).resolve()
    out_dir = Path(args.out_dir).resolve()
    
    # 焦土清理与尺寸自适应探测
    if args.auto_2_layer:
        print("\n[INIT] Activated --auto-2-layer. Performing scorched-earth cleanup...")
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        img_w, img_h = 4096, 4096
        if source_path.exists():
            try:
                from PIL import Image
                with Image.open(source_path) as img:
                    orig_w, orig_h = img.width, img.height
                
                # --- FORCE 4K SCALING (McKinsey Rule) ---
                max_edge_4k = 4096
                current_max = max(orig_w, orig_h)
                scale = max_edge_4k / current_max
                img_w = int(orig_w * scale)
                img_h = int(orig_h * scale)
                # align to 16
                img_w = max(16, ((img_w + 15) // 16) * 16)
                img_h = max(16, ((img_h + 15) // 16) * 16)
            except Exception as e:
                print(f"[WARNING] Could not read image dimensions: {e}. Defaulting to 4096x4096")
                
        bg_final_prompt = args.bg_prompt
        fg_final_prompt = args.fg_prompt
        if args.prompt_append_file:
            try:
                with open(args.prompt_append_file, "r", encoding="utf-8") as pf:
                    append_content = pf.read()
                    bg_final_prompt += "\n\n[附加高级指令法典]:\n" + append_content
                    fg_final_prompt += "\n\n[附加高级指令法典]:\n" + append_content
            except Exception as e:
                print(f"[WARNING] Could not read prompt-append-file {args.prompt_append_file}: {e}")

        spec_data = {
            "canvas": {"width": img_w, "height": img_h},
            "layers": [
                {
                    "key": "background",
                    "group": "01_BG",
                    "name": "Background",
                    "prompt": bg_final_prompt,
                    "left": 0, "top": 0, "width": img_w, "height": img_h
                },
                {
                    "key": "foreground",
                    "group": "05_FOREGROUND",
                    "name": "Foreground",
                    "prompt": fg_final_prompt,
                    "left": 0, "top": 0, "width": img_w, "height": img_h
                }
            ]
        }
        
        job_spec_path = out_dir / "job-spec.json"
        with open(job_spec_path, "w", encoding="utf-8") as f:
            json.dump(spec_data, f, ensure_ascii=False, indent=2)
        print(f"[INIT] Auto-generated 2-layer spec at: {job_spec_path}")
    else:
        job_spec_path = Path(args.job_spec).resolve()

    manifest_path = out_dir / "manifest.json"
    scene_path = out_dir / "scene.json"
    psd_path = out_dir / "layered-output.psd"

    # Step 1: Init Reverse PSD Job
    step1_cmd = [
        sys.executable, 
        str(script_dir / "init_reverse_psd_job.py"), 
        "--source", str(source_path), 
        "--job-spec", str(job_spec_path), 
        "--out-dir", str(out_dir)
    ]
    run_step(step1_cmd, "Step 1: Init Job & Crop References")

    # Step 2: Extract Layers (It automatically runs build_parallel_layer_plan.py)
    step2_cmd = [
        sys.executable,
        str(script_dir / "extract_layers.py"),
        "--manifest", str(manifest_path)
    ]
    run_step(step2_cmd, "Step 2: Semantic Layer Extraction")

    # Step 3: Build Preview and Scene Map
    step3_cmd = [
        sys.executable,
        str(script_dir / "build_reverse_psd_preview.py"),
        "--manifest", str(manifest_path)
    ]
    run_step(step3_cmd, "Step 3: Build Preview & PSD Scene Structure")

    # Step 4: Assemble PSD via NodeJS
    step4_cmd = [
        "node",
        str(script_dir / "build_reverse_psd.mjs"),
        "--scene", str(scene_path),
        "--output", str(psd_path)
    ]
    run_step(step4_cmd, "Step 4: Assemble PSD File")

    print("\n[Pipeline] All steps completed successfully!")
    print(f"[Pipeline] Final PSD is ready at: {psd_path}")

if __name__ == "__main__":
    main()
