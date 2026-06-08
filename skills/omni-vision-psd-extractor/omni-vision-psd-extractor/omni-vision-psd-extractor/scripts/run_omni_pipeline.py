#!/usr/bin/env python3
import argparse
import sys
import subprocess
import json
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("\n[WARNING] Pillow library not found. Auto-generation requires 'Pillow'. Try: pip install Pillow")
    Image = None

def run_step(cmd, step_name):
    print(f"\n[{step_name}] Starting...")
    print(f"Command: {' '.join(cmd)}")
    
    # 强制让子进程继承当前进程的 stdout 和 stderr，并将编码强制设定为 UTF-8
    env = None
    if sys.platform.startswith('win'):
        import os
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

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
                # 💡 第一性原理核心修正：取用户最新发送的图片作为源图
                # 按修改时间从新到旧（降序）排序，选择最新的一张
                candidates.sort(key=lambda x: x[0], reverse=True)
                mtime, oldest_path = candidates[0]
                import time as time_mod
                print(f"\n[AUTO-SOURCE] Isolated conversation brain folder. Detected newest original image: {oldest_path} (mtime: {time_mod.strftime('%Y-%m-%d %H:%M:%S', time_mod.localtime(mtime))})")
                return str(oldest_path)
            else:
                print(f"\n[AUTO-SOURCE:WARNING] No media__ files found in conversation brain folder {brain_dir}. Falling back to global scans.")

    # 2. 全局降级扫描（Downloads 和 Workspace）- 取最新文件
    scan_dirs = [
        Path.home() / "Downloads"
    ]
    curr_dir = Path(__file__).resolve()
    while curr_dir.parent != curr_dir:
        if (curr_dir / ".agents").exists():
            scan_dirs.append(curr_dir / "workspace")
            break
        curr_dir = curr_dir.parent
    
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
    parser.add_argument("--job-spec", required=False, help="Path to generated job-spec.json (optional if --auto-2-layer is used)")
    parser.add_argument("--out-dir", required=True, help="Path to output directory")
    # 🔒 语义修正：auto-extract 支持 2层到N层，--auto-2-layer 保留为向下兼容别名
    parser.add_argument("--auto-extract", "--auto-2-layer", action="store_true",
        dest="auto_2_layer",
        help="Auto-generate layer config and bypass manual job-spec (supports 2-layer or N-layer element explosion mode)")
    parser.add_argument("--bg-prompt", type=str,
        default="【极其重要：绝对禁止凭空生成完全不同的风景！必须严格保持原图中的背景结构、光影和色彩不变，仅仅智能脑补被移除的前景区域。】将图片中的背景提取出来，需要将前景所有元素全部剔除，只保留背景。",
        help="Prompt for background layer")
    parser.add_argument("--fg-prompt", type=str,
        default="将图片中除了背景之外的所有前景元素全部提取出来。【极其重要：强制将背景全部填充为纯正的绿幕（纯绿色，Hex: #00FF00）！绝对不要生成假透明像素方格背景！】",
        help="Prompt for foreground layer (used when no --fg-elements given)")
    parser.add_argument("--fg-elements", type=str, default=None,
        help="逗号分隔的前景元素列表，例如 '品牌Logo,主标题,IP角色,气球,纸飞机,风车,积木'。传入后每个元素独立生成一个图层")
    parser.add_argument("--prompt-append-file", type=str, default=None, help="File whose content will be appended to both bg and fg prompts")
    parser.add_argument("--conv-id", default=None, help="The current conversation ID to isolate and locate the original uploaded image")
    args = parser.parse_args()

    if not args.auto_2_layer and not args.job_spec:
        print("\n[ERROR] You must provide either --job-spec or --auto-2-layer")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    source_str = args.source
    if source_str.startswith("http://") or source_str.startswith("https://"):
        import urllib.request
        import urllib.parse
        import tempfile
        import os
        print(f"\n[INIT] Downloading source image from URL: {source_str}")

        # 智能推断扩展名：优先从 URL 路径推断，兜底用 .png
        def _infer_ext_from_url(url: str) -> str:
            path_part = urllib.parse.urlparse(url).path.lower()
            for cand in ('.png', '.jpg', '.jpeg', '.webp'):
                if path_part.endswith(cand):
                    return '.jpg' if cand == '.jpeg' else cand
            return '.png'  # 兜底，Cloudinary 默认返回 PNG-compatible

        ext = _infer_ext_from_url(source_str)

        req = urllib.request.Request(source_str, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            # 进一步用 Content-Type 校验
            content_type = response.getheader('Content-Type', '').lower()
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            
            fd, temp_path = tempfile.mkstemp(suffix=ext)
            os.close(fd)
            with open(temp_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

        source_str = temp_path
        print(f"[INIT] Downloaded to: {source_str} (ext={ext})")
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

        layers = [
            {
                "key": "background",
                "group": "01_BG",
                "name": "Background",
                "prompt": bg_final_prompt,
                "left": 0, "top": 0, "width": img_w, "height": img_h
            }
        ]

        # --- 麦肯锡闭环：N层元素拆分模式 vs 传统2层模式 ---
        if args.fg_elements:
            element_list = [e.strip() for e in args.fg_elements.split(",") if e.strip()]
            print(f"[INIT] 🎯 N-Layer Explosion Mode: {len(element_list)} foreground elements → {len(element_list)} independent layers")
            for i, elem in enumerate(element_list):
                elem_key = f"fg_{i+1:02d}_{elem[:20].replace(' ', '_')}"
                elem_prompt = (
                    f"只提取图片中的【{elem}】这个元素，其他所有内容必须完全消除。"
                    f"【极其重要：强制将该元素之外的所有区域全部填充为纯正的绿幕（纯绿色，Hex: #00FF00），"
                    f"绝对不要生成假透明的像素方格背景！保持该元素在原图中的绝对位置坐标不变！】"
                )
                if args.prompt_append_file:
                    try:
                        with open(args.prompt_append_file, "r", encoding="utf-8") as pf:
                            elem_prompt += "\n\n[附加高级指令法典]:\n" + pf.read()
                    except Exception as e:
                        print(f"[WARNING] Could not read prompt-append-file: {e}")
                layers.append({
                    "key": elem_key,
                    "group": "05_FOREGROUND",
                    "name": elem,
                    "prompt": elem_prompt,
                    "left": 0, "top": 0, "width": img_w, "height": img_h
                })
        else:
            # 传统2层模式（无元素列表时）
            layers.append({
                "key": "foreground",
                "group": "05_FOREGROUND",
                "name": "Foreground",
                "prompt": fg_final_prompt,
                "left": 0, "top": 0, "width": img_w, "height": img_h
            })

        spec_data = {
            "canvas": {"width": img_w, "height": img_h},
            "layers": layers
        }

        job_spec_path = out_dir / "job-spec.json"
        with open(job_spec_path, "w", encoding="utf-8") as f:
            json.dump(spec_data, f, ensure_ascii=False, indent=2)
        n_layers = len(layers)
        print(f"[INIT] Auto-generated {n_layers}-layer spec at: {job_spec_path}")
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

    # Step 5: Extreme Compression
    print("\n[Step 5: Extreme Compression] Starting ZIP compression...")
    import zipfile
    import os
    zip_path = psd_path.with_suffix('.psd.zip')
    psd_size_mb = os.path.getsize(psd_path) / (1024 * 1024) if psd_path.exists() else 0
    try:
        # Use LZMA for extreme compression (will reduce 300MB PSD to <30MB)
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_LZMA) as zf:
            zf.write(psd_path, psd_path.name)
        comp_type = "LZMA"
    except Exception as e:
        print(f"[WARNING] LZMA compression failed or not available ({e}). Falling back to DEFLATED.")
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(psd_path, psd_path.name)
        comp_type = "DEFLATED"
        
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024) if zip_path.exists() else 0
    print(f"[SUCCESS] [Step 5: Extreme Compression] Compressed from {psd_size_mb:.2f}MB to {zip_size_mb:.2f}MB using {comp_type}.")

    print("\n[Pipeline] All steps completed successfully!")
    print(f"[Pipeline] Final PSD is ready at: {psd_path}")
    print(f"[Pipeline] Compressed ZIP is ready at: {zip_path} (Please send this file to the user)")

if __name__ == "__main__":
    main()
