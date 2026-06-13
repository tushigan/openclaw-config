# API 请求次数完整分析

## 🎯 核心结论

**每次运行 skill 会产生：2 次 API 请求**

---

## 📊 详细流程分析

### Step 1: 生成任务规格（`run_omni_pipeline.py`）

**代码位置**: 第 188-206 行

```python
spec_data = {
    "canvas": {"width": img_w, "height": img_h},
    "layers": [
        {
            "key": "background",      # 任务 1
            "group": "01_BG",
            ...
        },
        {
            "key": "foreground",      # 任务 2
            "group": "05_FOREGROUND",
            ...
        }
    ]
}
```

**结果**: 生成 **2 个图层任务**

---

### Step 2: 构建并行计划（`layer_plan_common.py`）

**代码位置**: 第 238-275 行

```python
def build_parallel_plan(manifest: dict, ...):
    tasks = [background_task(manifest), *layer_tasks(manifest)]
    # tasks 列表只包含 2 个任务
```

**结果**: 任务列表 = **2 个任务** (background + foreground)

---

### Step 3: 执行图层提取（`extract_layers.py`）

**代码位置**: 第 773-778 行

```python
remaining_tasks = [t for t in parallel_tasks if not (...)]

# remaining_tasks 最多 2 个任务
with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
    future_to_task = {
        executor.submit(process_single_task, task, ...) 
        for task in remaining_tasks  # 只有 2 个任务
    }
```

**并发执行**: 2 个任务并发执行（如果都未完成）

---

### Step 4: 单个任务的 API 调用（`extract_layers.py`）

**代码位置**: 第 620-633 行

```python
if force_gemini:
    config = resolve_bound_gemini_config(env)
    attempts = max(1, args.api_retries)  # 默认 3 次重试
    for attempt in range(1, attempts + 1):
        if raw_out.exists():
            raw_out.unlink()
        safe_log(f"[Bound Gemini] API attempt {attempt}/{attempts}")
        res = run_bound_gemini(prompt, source_path, raw_out, env, suggested_size, source_url=source_url)
        if res.returncode == 0 and raw_out.exists():
            generation_success = True
            safe_log(f"✅ [Bound Gemini] Image generated and saved to {raw_out}")
            break  # 成功后立即退出循环
```

**关键点**:
- 每个任务最多重试 **3 次**（`--api-retries=3`）
- **成功后立即 break，不会继续重试**
- 只有失败才会重试

---

## 🔥 实际 API 请求次数计算

### 正常情况（所有请求成功）

```
任务 1 (background): 1 次 API 请求 ✅ 成功 → break
任务 2 (foreground): 1 次 API 请求 ✅ 成功 → break
───────────────────────────────────────────────
总计: 2 次 API 请求
```

### 异常情况（第1次失败，第2次成功）

```
任务 1 (background): 
  - 第 1 次尝试 ❌ 失败
  - 第 2 次尝试 ✅ 成功 → break
  
任务 2 (foreground): 
  - 第 1 次尝试 ✅ 成功 → break
───────────────────────────────────────────────
总计: 3 次 API 请求（1次重试）
```

### 最坏情况（所有尝试都失败）

```
任务 1 (background): 
  - 第 1 次尝试 ❌ 失败
  - 第 2 次尝试 ❌ 失败
  - 第 3 次尝试 ❌ 失败 → 任务失败，整个 job 失败
  
任务 2 (foreground): 
  - 不会执行（因为整个 job 已经失败）
───────────────────────────────────────────────
总计: 3 次 API 请求（2次重试），然后任务终止
```

---

## 📋 请求配置明细

### 第 1 次 API 请求 - Background 层

**请求参数**:
```json
{
  "model": "gpt-image-2-pro",
  "image": "<原图二进制数据>",
  "prompt": "将图片中的背景提取出来。\n\n<万物提取.md 完整内容 ~30KB>",
  "size": "4096x2304",
  "n": 1
}
```

**API 端点**: `https://n.lconai.com/v1/images/edits`

---

### 第 2 次 API 请求 - Foreground 层

**请求参数**:
```json
{
  "model": "gpt-image-2-pro",
  "image": "<原图二进制数据>",
  "prompt": "<元素整理.md 完整内容 ~31KB>",
  "size": "4096x2304",
  "n": 1
}
```

**API 端点**: `https://n.lconai.com/v1/images/edits`

---

## 🚫 不会产生额外请求的地方

### 1. ✅ Cloudinary 上传（不是 API 请求）

**代码位置**: `runtime_config.py` 第 142-291 行

```python
def upload_to_cloudinary(file_path: Path | str) -> str:
    # 这是上传到图床，不是生图 API 请求
```

- 这是图床上传，不计入生图 API
- **仅在 Gemini 协议时使用**
- **当前使用 OpenAI 协议，不会调用此函数**

### 2. ✅ 去绿幕处理（本地操作）

**代码位置**: `extract_layers.py` 第 660-675 行

```python
chroma_cmd = [sys.executable, str(remove_chroma_script), ...]
# 这是本地 Python 脚本，不是 API 请求
```

### 3. ✅ 前景切割（本地 OpenCV）

**代码位置**: `extract_layers.py` 第 815-881 行

```python
split_cmd = [sys.executable, str(split_script), ...]
# 这是本地 OpenCV 处理，不是 API 请求
```

### 4. ✅ PSD 组装（本地 Node.js）

**代码位置**: `run_omni_pipeline.py` 第 246-251 行

```python
step4_cmd = ["node", str(script_dir / "build_reverse_psd.mjs"), ...]
# 这是本地 PSD 组装，不是 API 请求
```

---

## 🔒 防止多次请求的保障机制

### 保障 1: 固定任务数量

**文件**: `run_omni_pipeline.py` 第 188-206 行

```python
spec_data = {
    "layers": [
        {"key": "background", ...},  # 只有 2 个
        {"key": "foreground", ...}
    ]
}
```

✅ **硬编码只生成 2 个图层任务**

---

### 保障 2: 成功后立即 break

**文件**: `extract_layers.py` 第 620-633 行

```python
for attempt in range(1, attempts + 1):
    res = run_bound_gemini(...)
    if res.returncode == 0 and raw_out.exists():
        generation_success = True
        break  # ✅ 成功后立即退出，不继续重试
```

---

### 保障 3: 任何图层失败则整个 job 失败

**文件**: `extract_layers.py` 第 649-658 行

```python
if not generation_success:
    safe_log(f"Generation failed for '{key}' after strict API attempts: {error_msg}")
    with state_lock:
        task_state["status"] = "failed"
    return False  # ✅ 返回 False，整个 job 终止
```

---

### 保障 4: 状态缓存机制

**文件**: `extract_layers.py` 第 564-578 行

```python
with state_lock:
    task_state = state["tasks"].get(key, {})
    is_completed = task_state.get("status") == "completed" and Path(task["layer_path"]).exists()

if is_completed:
    safe_log(f"Layer '{key}' is already completed. Skipping.")
    return True  # ✅ 已完成的任务不会重复执行
```

---

## 📈 历史问题分析（为什么之前会有 7-8 次请求）

### 可能原因 1: 使用了 N 层模式（v4.0 旧版本）

```python
# 旧版本可能定义了多个图层
spec_data = {
    "layers": [
        {"key": "background"},
        {"key": "subject"},
        {"key": "logo"},
        {"key": "title"},
        {"key": "decor_1"},
        {"key": "decor_2"},
        {"key": "decor_3"},
        ...
    ]
}
# 每个图层 1 次 API = 7-8 次 API
```

**当前已修复**: 强制使用 2 层模式（第 113 行 `--auto-2-layer` 默认开启）

---

### 可能原因 2: 重试机制被误触发

```python
# 如果每次都失败重试
任务 1: 3 次重试
任务 2: 3 次重试
任务 3: 3 次重试
...
# 总计可能达到 9-12 次
```

**当前已修复**: 成功后立即 break，不继续重试

---

### 可能原因 3: 没有状态缓存，重复执行

```python
# 旧版本可能没有状态检查
# 导致同一个任务被重复执行
```

**当前已修复**: 第 564-578 行有完整的状态缓存机制

---

## ✅ 最终结论

### 正常情况下的 API 请求次数

```
┌─────────────────────────────────────────┐
│  每次运行产生：2 次 API 请求             │
│                                         │
│  - 第 1 次: 背景层提取                   │
│  - 第 2 次: 前景层元素整理               │
│                                         │
│  成本降低：75%（相比旧版 N 层模式）       │
└─────────────────────────────────────────┘
```

### 异常情况（重试）

```
- 最少: 2 次（全部成功）
- 最多: 6 次（每个任务都失败 2 次，第 3 次成功）
- 极端: 3 次（任务 1 失败 3 次后终止）
```

### 不会产生的请求

```
❌ Cloudinary 上传（图床，非生图 API）
❌ 去绿幕处理（本地脚本）
❌ 前景切割（本地 OpenCV）
❌ PSD 组装（本地 Node.js）
❌ 飞书云盘上传（飞书 API，非生图 API）
```

---

## 🎯 验证方法

### 运行 skill 后检查日志

```bash
grep -i "API attempt\|API 第.*次请求完成" <日志文件>
```

应该看到：
```
[background] API attempt 1/3
✅ [Bound Gemini] Image generated and saved to ...
[foreground] API attempt 1/3
✅ [Bound Gemini] Image generated and saved to ...
```

总共 **2 次** "API attempt 1/3" 且都成功 = **2 次 API 请求**

---

*分析完成时间：2026-06-12*
*版本：v5.2.0-cloud-drive-only*
