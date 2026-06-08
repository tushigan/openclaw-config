#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 全局互斥锁与全局进度计数器定义
state_lock = threading.Lock()
print_lock = threading.Lock()
completed_count = 0
total_parallel_tasks = 0
ROUTE_GUARD_SCRIPT = Path('/Users/a123/.openclaw/scripts/feishu-route-guard.py')

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

class FinishedProcess:
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

def run_with_spinner(cmd, env=None, message="Running", show_spinner=True, timeout=600):
    start_time = time.time()
    
    if not show_spinner:
        try:
            res = subprocess.run(
                cmd,
                env=env,
                text=True,
                capture_output=True,
                encoding="utf-8" if sys.version_info >= (3, 6) else None,
                timeout=timeout
            )
            return FinishedProcess(res.returncode, res.stdout, res.stderr)
        except subprocess.TimeoutExpired as te:
            return FinishedProcess(-9, "", f"Command timed out after {timeout} seconds. te={te}")

    is_windows = sys.platform.startswith('win')
    spinner_frames = ["|", "/", "-", "\\"] if is_windows else ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        encoding="utf-8" if sys.version_info >= (3, 6) else None,
        bufsize=1
    )
    
    stdout_data, stderr_data = [], []
    
    def read_stdout():
        try:
            for line in process.stdout: stdout_data.append(line)
        except Exception: pass
            
    def read_stderr():
        try:
            for line in process.stderr: stderr_data.append(line)
        except Exception: pass
            
    t_out = threading.Thread(target=read_stdout)
    t_err = threading.Thread(target=read_stderr)
    t_out.daemon = True
    t_err.daemon = True
    t_out.start()
    t_err.start()
    
    frame_idx = 0
    try:
        while process.poll() is None:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                process.terminate()
                try: process.wait(timeout=2)
                except Exception: process.kill()
                sys.stdout.write(f"\r\n[Timeout] Process killed after {timeout}s exceeding limit.\n")
                sys.stdout.flush()
                return FinishedProcess(-9, "", f"Command timed out after {timeout} seconds.")

            frame = spinner_frames[frame_idx % len(spinner_frames)]
            status_line = f"\r{frame} {message} (elapsed: {elapsed:.1f}s)...  "
            sys.stdout.write(status_line)
            sys.stdout.flush()
            frame_idx += 1
            time.sleep(0.1)
    except KeyboardInterrupt:
        process.terminate()
        try: process.wait(timeout=2)
        except Exception: process.kill()
        sys.stdout.write("\r\n[Ctrl+C] Process interrupted by user.\n")
        sys.stdout.flush()
        raise
        
    t_out.join(timeout=1)
    t_err.join(timeout=1)
    
    returncode = process.wait()
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()
    
    return FinishedProcess(returncode, "".join(stdout_data), "".join(stderr_data))


def parse_args():
    parser = argparse.ArgumentParser(description="Automate layer extraction using omni-vision semantic mask protocol")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--generator", help="Path to gpt-image2-gen generate.py script")
    parser.add_argument("--mode", choices=["draft", "final", "max"], default="max", help="Sizing mode")
    parser.add_argument("--tolerance", type=int, default=30, help="Chroma key tolerance")
    parser.add_argument("--key-mode", default="green", help="Chroma key mode (green or white)")
    parser.add_argument("--force-gemini", action="store_true", help="Force using Gemini 3.1 flash")
    parser.add_argument("--concurrency", type=int, default=4, help="Number of layers to rebuild concurrently")
    parser.add_argument("--feishu-user-id", default=os.getenv('OPENCLAW_FEISHU_USER_ID', os.getenv('FEISHU_USER_ID', '')), help="Optional Feishu user id")
    parser.add_argument("--feishu-chat-id", default=os.getenv('OPENCLAW_FEISHU_CHAT_ID', os.getenv('FEISHU_CHAT_ID', '')), help="Optional Feishu chat id")
    return parser.parse_args()


def detect_generator():
    paths = [
        Path("h:/openclaw/workspace/PSD-SKILL/gpt-image2-gen/gpt-image2-gen/scripts/generate_failover.py"),
        Path("h:/openclaw/workspace/PSD-SKILL/gpt-image2-gen/gpt-image2-gen/scripts/generate.py"),
        Path("h:/openclaw/.agents/skills/gpt-image2-gen/scripts/generate.py"),
    ]
    for p in paths:
        if p.exists(): return p
    return None

def guess_aspect_ratio(size_str):
    try:
        w, h = map(int, size_str.lower().split('x'))
        ratio = w / h
        candidates = [("1:1", 1.0), ("3:4", 0.75), ("4:3", 1.333), ("9:16", 0.5625), ("16:9", 1.7778), ("4:5", 0.8), ("5:4", 1.25), ("2:3", 0.6667), ("3:2", 1.5)]
        return min(candidates, key=lambda x: abs(x[1] - ratio))[0]
    except Exception: return "1:1"

def guess_banana_size(size_str):
    try:
        w, h = map(int, size_str.lower().split('x'))
        max_side = max(w, h)
        if max_side <= 1024: return "1K"
        elif max_side <= 2048: return "2K"
        elif max_side <= 3072: return "3K"
        elif max_side <= 4096: return "4K"
        else: return "5K"
    except Exception: return "2K"

def normalize_feishu_target(value):
    raw = str(value or '').strip()
    if not raw:
        return ''
    if raw.startswith(('chat:', 'user:')):
        return raw
    if raw.startswith('oc_'):
        return 'chat:' + raw
    if raw.startswith('ou_'):
        return 'user:' + raw
    return raw

def check_feishu_media_route(path: Path, user_id: str, chat_id: str):
    target = normalize_feishu_target(chat_id or user_id)
    if not target or not ROUTE_GUARD_SCRIPT.exists():
        return {'ok': bool(target), 'status': 'route_guard_unavailable'}
    cmd = [sys.executable, str(ROUTE_GUARD_SCRIPT), 'check', '--media', str(path), '--target', target, '--json']
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
    except Exception as e:
        return {'ok': True, 'status': 'route_guard_unavailable', 'error': str(e)}
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    return payload or {'ok': result.returncode == 0, 'status': 'route_guard_failed' if result.returncode else 'route_guard_ok'}

def send_feishu_image(path: Path, user_id: str, chat_id: str, key: str, name: str, progress: str):
    if not (user_id or chat_id): return
    target_args = ['--chat-id', chat_id] if chat_id else ['--user-id', user_id]
    target_label = f'chat_id={chat_id}' if chat_id else f'user_id={user_id}'
    route_check = check_feishu_media_route(path, user_id, chat_id)
    if not route_check.get('ok'):
        with print_lock:
            print(f"[{key}][deliver:block] route guard blocked {path.name}: {route_check.get('status', 'unknown')}", file=sys.stderr)
            sys.stdout.flush()
        return

    npx_cmd = 'npx.cmd' if sys.platform.startswith('win') else 'npx'
    cmd = [npx_cmd, '-y', 'lark-cli', 'im', '+messages-send', '--as', 'bot', *target_args, '--image', str(path)]
    with print_lock:
        print(f"[{key}][deliver] Sending generated image {path.name} to Feishu {target_label} ({progress})...")
        sys.stdout.flush()
    
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=180, stdin=subprocess.DEVNULL)
        with print_lock:
            if result.returncode != 0:
                print(f"[{key}][deliver:error] lark-cli failed for {path.name}: {result.stderr.strip()}", file=sys.stderr)
            else:
                print(f"[{key}][deliver] Sent successfully: {path.name}")
            sys.stdout.flush()
    except Exception as e:
        with print_lock:
            print(f"[{key}][deliver:error] Failed to execute lark-cli for {path.name}: {e}", file=sys.stderr)
            sys.stdout.flush()

def process_single_task(task, args, env, generator_path, remove_chroma_script, manifest, source_path, state, state_path, anchor_key, is_parallel=True):
    global completed_count
    key = task["key"]
    
    def safe_log(msg):
        with print_lock:
            print(f"[{key}] {msg}")
            sys.stdout.flush()
            
    with state_lock:
        task_state = state["tasks"].get(key, {})
        is_completed = task_state.get("status") == "completed" and Path(task["layer_path"]).exists()
        
    if is_completed:
        safe_log(f"Layer '{key}' is already completed. Skipping.")
        if is_parallel:
            with state_lock: completed_count += 1
        return True

    safe_log(f"Starting semantic extraction layer: {task['name']} (group={task['group']})")

    # == 核心：组装提取 Prompt ==
    prompt = task.get("prompt_spec") or task.get("prompt")
    if not prompt or prompt.lower() in ["", "foreground", "background"]:
        script_dir = Path(__file__).resolve().parent
        wanwu_path = script_dir.parent / "references" / "万物提取.md"
        wanwu_text = wanwu_path.read_text(encoding="utf-8") if wanwu_path.exists() else ""
        
        if task["kind"] == "background":
            prompt = f"将图片中的背景提取出来，其他保持不变。\n\n{wanwu_text}"
        else:
            prompt = f"将图片中除了背景之外的所有东西都提取出来。强制将所有背景填充为纯正的绿幕（纯绿色，Hex: #00FF00），绝对不要生成假透明像素方格！其他保持不变。\n\n{wanwu_text}"

    suggested_size = task["size_plan"]["suggested_size"]
    raw_out = Path(task["raw_path"])
    layer_out = Path(task["layer_path"])

    is_lossless = task.get("lossless_extract", False)
    force_gemini = args.force_gemini or env.get("BANANA_FORCE_GEMINI") == "1"
    fallback_success = False
    is_generation_fallback_triggered = False
    res = None

    if force_gemini:
        safe_log(f"⚡ [Gemini Direct] Force Gemini active. Bypassing gpt-image2-gen...")
        banana_script = Path("h:/openclaw/.agents/skills/nano-banana-image-gen/scripts/generate.mjs")
        if banana_script.exists():
            banana_ratio = guess_aspect_ratio(suggested_size)
            banana_size = guess_banana_size(suggested_size)
            
            banana_cmd = ["node", str(banana_script), "香蕉2", prompt, "--aspectRatio", banana_ratio, "--size", banana_size]
            res = run_with_spinner(banana_cmd, env=env, message=f"[Gemini Direct] Extracting layer '{key}' via Gemini", show_spinner=not is_parallel)
            
            if res.returncode == 0:
                filepath_line = None
                for line in res.stdout.splitlines():
                    if "[NanoBanana] 已保存至:" in line:
                        filepath_line = line.split("[NanoBanana] 已保存至:")[-1].strip()
                        break
                if filepath_line and Path(filepath_line).exists():
                    import shutil
                    raw_out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(filepath_line, str(raw_out))
                    fallback_success = True
                    is_generation_fallback_triggered = True
                    safe_log(f"✅ [Gemini Direct] Image generated and saved to {raw_out}")
            else:
                safe_log(f"❌ [Gemini Direct] NanoBanana generation failed: {res.stderr}")
    else:
        prompt_file = raw_out.with_suffix(".prompt.txt")
        prompt_file.write_text(prompt, encoding="utf-8")

        gen_args = [sys.executable, str(generator_path), "--prompt-file", str(prompt_file), "-s", suggested_size, "-o", str(raw_out)]

        # 严格遵守“唯一本源”法则，只发送原图作为底图进行提取
        gen_args.extend(["--ref-base", source_path])

        safe_log(f"Running generator command for '{key}'...")
        res = run_with_spinner(gen_args, env=env, message=f"[API: edits] Extracting layer '{key}'", show_spinner=not is_parallel)
        
        if (res.returncode != 0 or not raw_out.exists()) and task["kind"] != "background" and env.get("BANANA_DISABLE_EDITS") != "1":
            safe_log(f"⚠️  [Chroma Failover] edits generation failed. Retrying with BANANA_DISABLE_EDITS=1 (generations fallback)...")
            fallback_env = env.copy()
            fallback_env["BANANA_DISABLE_EDITS"] = "1"
            res_fallback = run_with_spinner(gen_args, env=fallback_env, message=f"[Chroma Failover] Retrying '{key}' via fallback", show_spinner=not is_parallel)
            if res_fallback.returncode == 0 and raw_out.exists():
                res, fallback_success, is_generation_fallback_triggered = res_fallback, True, True
                safe_log(f"✅ [Chroma Failover] generations fallback retry succeeded! Image saved to {raw_out}")

        if not fallback_success and (res.returncode != 0 or not raw_out.exists()):
            safe_log(f"⚠️  [Progressive Fallback] Primary APIs failed. Activating V4.0 Progressive Fallback Mesh (Stripping complex Prompt)...")
            simple_prompt = prompt.split("\n\n[附加高级指令法典]:")[0].split("\n\n")[0].strip()
            if task["kind"] != "background" and "绿幕" not in simple_prompt:
                 simple_prompt += " (强制将背景填充为纯正的绿幕 #00FF00，绝不要方格背景)"
                 
            simple_prompt_file = raw_out.with_suffix(".simple.prompt.txt")
            simple_prompt_file.write_text(simple_prompt, encoding="utf-8")
            
            fallback_args = [sys.executable, str(generator_path), "--prompt-file", str(simple_prompt_file), "-s", suggested_size, "-o", str(raw_out), "--ref-base", source_path]
            res_mesh = run_with_spinner(fallback_args, env=env, message=f"[Fallback Mesh] Retrying '{key}' with simple prompt", show_spinner=not is_parallel)
            
            if res_mesh.returncode == 0 and raw_out.exists():
                res, fallback_success, is_generation_fallback_triggered = res_mesh, True, True
                safe_log(f"✅ [Fallback Mesh] Simplified prompt succeeded! Image saved to {raw_out}")

        if not fallback_success and (res.returncode != 0 or not raw_out.exists()):
            safe_log(f"⚠️  [Chroma Failover] gpt-image-2-pro failed for '{key}'. Switching to NanoBanana fallback...")
            banana_script = Path("h:/openclaw/.agents/skills/nano-banana-image-gen/scripts/generate.mjs")
            if banana_script.exists():
                banana_ratio = guess_aspect_ratio(suggested_size)
                banana_size = guess_banana_size(suggested_size)
                banana_cmd = ["node", str(banana_script), "香蕉2", prompt, "--aspectRatio", banana_ratio, "--size", banana_size]
                banana_res = run_with_spinner(banana_cmd, env=env, message=f"[Chroma Failover] Rebuilding '{key}' via NanoBanana", show_spinner=not is_parallel)
                if banana_res.returncode == 0:
                    filepath_line = None
                    for line in banana_res.stdout.splitlines():
                        if "[NanoBanana] 已保存至:" in line:
                            filepath_line = line.split("[NanoBanana] 已保存至:")[-1].strip()
                            break
                    if filepath_line and Path(filepath_line).exists():
                        import shutil
                        raw_out.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(filepath_line, str(raw_out))
                        fallback_success = True
                        safe_log(f"✅ [Chroma Failover] Fallback succeeded! Copied image to {raw_out}")

    if not fallback_success and (res is None or res.returncode != 0 or not raw_out.exists()):
        safe_log(f"⚠️  [Chroma Failover] ALL APIs failed. Activating Trinary Offline Auto-Recovery...")
        ref_path = task.get("ref_path")
        if ref_path and Path(ref_path).exists():
            try:
                from PIL import Image
                ref_img = Image.open(ref_path).convert("RGBA")
                w_target, h_target = map(int, suggested_size.lower().split('x'))
                ref_resized = ref_img.resize((w_target, h_target), Image.Resampling.LANCZOS)
                raw_out.parent.mkdir(parents=True, exist_ok=True)
                ref_resized.save(raw_out)
                fallback_success = True
                safe_log(f"✅ [Chroma Failover] Offline recovery succeeded! Extracted reference slice to {raw_out}")
            except Exception as recovery_err:
                pass

    if not fallback_success and (res is None or res.returncode != 0 or not raw_out.exists()):
        error_msg = res.stderr if (res and res.returncode != 0) else "Output file not found"
        safe_log(f"Generation failed for '{key}': {error_msg}")
        with state_lock:
            task_state = state["tasks"].get(key, {})
            task_state["status"] = "failed"
            task_state["error"] = error_msg
            with open(state_path, "w", encoding="utf-8") as f: json.dump(state, f, ensure_ascii=False, indent=2)
        return False

    if task["kind"] == "background":
        if str(raw_out) != str(layer_out):
            layer_out.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(str(raw_out), str(layer_out))
    else:
        safe_log(f"Removing chroma key background from {raw_out} to {layer_out}...")
        tolerance_val = 38 if (is_generation_fallback_triggered or env.get("BANANA_DISABLE_EDITS") == "1") else args.tolerance
        chroma_cmd = [sys.executable, str(remove_chroma_script), "--input", str(raw_out), "--output", str(layer_out), "--mode", args.key_mode, "--tolerance", str(tolerance_val)]
        res = run_with_spinner(chroma_cmd, env=env, message=f"[Chroma Key] Removing green background from '{key}'", show_spinner=not is_parallel)
        if res.returncode != 0:
            with state_lock:
                task_state = state["tasks"].get(key, {})
                task_state["status"] = "failed"
                task_state["error"] = res.stderr
                with open(state_path, "w", encoding="utf-8") as f: json.dump(state, f, ensure_ascii=False, indent=2)
            return False

    with state_lock:
        task_state = state["tasks"].get(key, {})
        task_state["status"] = "completed"
        task_state["result_path"] = str(layer_out)
        task_state["error"] = ""
        if key == anchor_key: state["anchor_completed"] = True
        if is_parallel: completed_count += 1
        with open(state_path, "w", encoding="utf-8") as f: json.dump(state, f, ensure_ascii=False, indent=2)

    # 尺寸对齐
    target_size = task["size_plan"]["target_size"]
    w_target, h_target = map(int, target_size.lower().split('x'))
    try:
        from PIL import Image
        with Image.open(layer_out) as img:
            layer_img = img.convert("RGBA")
            
        if layer_img.width != w_target or layer_img.height != h_target:
            orig_ratio = layer_img.width / layer_img.height
            target_ratio = w_target / h_target
            if abs(orig_ratio - target_ratio) / target_ratio > 0.05:
                scale = min(w_target / layer_img.width, h_target / layer_img.height)
                new_w, new_h = int(layer_img.width * scale), int(layer_img.height * scale)
                resized_img = layer_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                padded_img = Image.new("RGBA", (w_target, h_target), (0, 0, 0, 0))
                padded_img.paste(resized_img, ((w_target - new_w) // 2, (h_target - new_h) // 2))
                layer_img = padded_img
            else:
                layer_img = layer_img.resize((w_target, h_target), Image.Resampling.LANCZOS)
            layer_img.save(layer_out)
    except Exception as e:
        safe_log(f"⚠️ [Resize Warning] Failed to resize layer {key}: {e}")

    if task["kind"] != "background":
        try:
            safe_log(f"Generating lossless high-res fallback for {key} from reference slice...")
            from PIL import Image
            ref_img = Image.open(task["ref_path"]).convert("RGBA")
            w_target, h_target = map(int, suggested_size.lower().split('x'))
            ref_resized = ref_img.resize((w_target, h_target), Image.Resampling.LANCZOS)
            
            lossless_raw = raw_out.parent / f"{key}_lossless_raw.png"
            lossless_layer = layer_out.parent / f"{key}_lossless.png"
            ref_resized.save(lossless_raw)
            
            safe_log(f"Removing white background from lossless fallback to {lossless_layer}...")
            chroma_cmd = [
                sys.executable,
                str(remove_chroma_script),
                "--input", str(lossless_raw),
                "--output", str(lossless_layer),
                "--mode", "white",
                "--tolerance", "30"
            ]
            run_with_spinner(chroma_cmd, env=env, message=f"[Chroma Key] Removing white background for lossless fallback of '{key}'", show_spinner=not is_parallel)
            safe_log(f"✅ Lossless high-res fallback created at {lossless_layer}")
        except Exception as e:
            safe_log(f"⚠️ Failed to generate lossless fallback for {key}: {e}")

    feishu_user, feishu_chat = args.feishu_user_id.strip(), args.feishu_chat_id.strip()
    if feishu_user or feishu_chat:
        send_feishu_image(layer_out, feishu_user, feishu_chat, key, task["name"], f"{completed_count}/{total_parallel_tasks}" if is_parallel else "1/1")

    return True

def main():
    args = parse_args()
    manifest_path = Path(args.manifest)
    if not manifest_path.exists(): sys.exit(1)

    generator_path = Path(args.generator) if args.generator else detect_generator()
    if not generator_path or not generator_path.exists(): sys.exit(1)

    job_dir = manifest_path.parent
    plan_path = job_dir / "parallel-plan.json"
    state_path = job_dir / "parallel-state.json"

    # 使用本地同目录下的脚本
    original_script_dir = Path(__file__).resolve().parent
    build_plan_script = original_script_dir / "build_parallel_layer_plan.py"
    remove_chroma_script = original_script_dir / "remove_chroma_key.py"

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    if not plan_path.exists() or not state_path.exists():
        cmd = [sys.executable, str(build_plan_script), "--manifest", str(manifest_path), "--mode", args.mode, "--plan-out", str(plan_path), "--state-out", str(state_path)]
        res = run_with_spinner(cmd, env=env, message="[Build Plan] Generating parallel plan and state")
        if res.returncode != 0: sys.exit(1)

    with open(plan_path, "r", encoding="utf-8") as f: plan = json.load(f)
    with open(state_path, "r", encoding="utf-8") as f: state = json.load(f)
    manifest = json.load(open(manifest_path, "r", encoding="utf-8"))
    source_path = manifest["source_path"]

    tasks, anchor_key = plan["tasks"], plan["anchor_key"]
    global total_parallel_tasks, completed_count

    parallel_tasks = tasks
    total_parallel_tasks = len(parallel_tasks)
    
    with state_lock:
        completed_count = sum(1 for t in parallel_tasks if state["tasks"].get(t["key"], {}).get("status") == "completed" and Path(t["layer_path"]).exists())
    
    remaining_tasks = [t for t in parallel_tasks if not (state["tasks"].get(t["key"], {}).get("status") == "completed" and Path(t["layer_path"]).exists())]

    if not remaining_tasks: sys.exit(0)

    success = True
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        future_to_task = {executor.submit(process_single_task, task, args, env, generator_path, remove_chroma_script, manifest, source_path, state, state_path, anchor_key, True): task for task in remaining_tasks}
        for future in as_completed(future_to_task):
            try:
                if not future.result(): success = False
            except Exception: success = False

    if not success: sys.exit(1)

if __name__ == "__main__": main()
