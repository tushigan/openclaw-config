# 模型托底机制配置说明

## 🎯 当前需求

**主模型**: `gpt-image-2-pro` (OpenAI 协议)  
**托底模型**: `gemini-3.1-flash-image-preview` (Gemini 协议)

**托底触发条件**: 
- 主模型 2 次 API 请求（背景 + 前景）都失败
- 在超时时间内（600秒）无法完成
- 才启用托底模型重试 2 次请求

---

## 📊 当前问题分析

### 问题 1: 模型选择逻辑混乱

**当前 `.env` 配置**:
```bash
OPENCLAW_BOUND_API_KEY=sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8
OPENCLAW_BOUND_BASE_URL=https://n.lconai.com/
OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro
OPENCLAW_BOUND_PROTOCOL=openai
```

**当前代码逻辑** (`extract_layers.py` 第 636-663 行):
```python
force_gemini = (
    env.get("OMNI_USE_GPT_IMAGE2") != "1"  # 如果这个不是 "1"
    and (
        args.force_gemini
        or env.get("OMNI_FORCE_BOUND_GEMINI", "1") == "1"  # 默认是 "1"
        or env.get("BANANA_FORCE_GEMINI") == "1"
    )
)
```

**问题**: 
- 变量名叫 `force_gemini`，但实际是通用的 API 调用开关
- 无论配置的是 `gpt-image-2-pro` 还是 `gemini-3.1-flash-image-preview`，都会走这个分支
- **没有托底机制**，只有单一模型重试

---

## ✅ 解决方案

### 方案 1: 修改 `.env` 配置（最简单）⭐

确保使用 `gpt-image-2-pro` 作为主模型：

```bash
# .env 文件
OPENCLAW_BOUND_API_KEY=sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8
OPENCLAW_BOUND_BASE_URL=https://n.lconai.com/
OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro
OPENCLAW_BOUND_PROTOCOL=openai

# 托底模型配置（新增）
OPENCLAW_FALLBACK_API_KEY=sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8
OPENCLAW_FALLBACK_BASE_URL=https://n.lconai.com/
OPENCLAW_FALLBACK_MODEL_ID=gemini-3.1-flash-image-preview
OPENCLAW_FALLBACK_PROTOCOL=gemini
```

**当前状态验证**:
```bash
# 检查当前配置
cat /Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env | grep OPENCLAW_BOUND

# 应该显示:
# OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro  ✅
# OPENCLAW_BOUND_PROTOCOL=openai  ✅
```

---

### 方案 2: 添加托底机制代码（推荐）⭐⭐⭐

修改 `extract_layers.py` 的重试逻辑，实现真正的托底机制。

#### 修改位置: 第 636-663 行

**新逻辑**:
```python
# Step 1: 主模型（gpt-image-2-pro）重试
config = resolve_bound_gemini_config(env)
attempts = max(1, args.api_retries)  # 默认 3 次

safe_log(f"🎯 [主模型] {config['model']} @ {config['base_url']}")

for attempt in range(1, attempts + 1):
    safe_log(f"[主模型] 尝试 {attempt}/{attempts}")
    res = run_bound_gemini(prompt, source_path, raw_out, env, suggested_size, source_url=source_url)
    
    if res.returncode == 0 and raw_out.exists():
        generation_success = True
        safe_log(f"✅ [主模型] 成功")
        break
    
    safe_log(f"❌ [主模型] 失败: {res.stderr[:200]}")

# Step 2: 主模型失败，启动托底机制
if not generation_success:
    safe_log(f"⚠️  [主模型] 全部失败，启动托底机制")
    
    # 切换到 Gemini 协议
    fallback_env = env.copy()
    fallback_env["OPENCLAW_BOUND_PROTOCOL"] = "gemini"
    fallback_env["OPENCLAW_BOUND_MODEL_ID"] = "gemini-3.1-flash-image-preview"
    
    # Gemini 需要 Cloudinary URL
    if not source_url:
        try:
            source_url = upload_to_cloudinary(source_path)
        except:
            pass  # 失败则使用 Base64
    
    fallback_config = resolve_bound_gemini_config(fallback_env)
    safe_log(f"🔄 [托底模型] {fallback_config['model']} @ {fallback_config['base_url']}")
    
    for attempt in range(1, attempts + 1):
        safe_log(f"[托底模型] 尝试 {attempt}/{attempts}")
        res = run_bound_gemini(prompt, source_path, raw_out, fallback_env, suggested_size, source_url=source_url)
        
        if res.returncode == 0 and raw_out.exists():
            generation_success = True
            safe_log(f"✅ [托底模型] 成功")
            break
        
        safe_log(f"❌ [托底模型] 失败")
```

---

## 📋 完整的重试流程（新方案）

```
任务开始
    ↓
【主模型】gpt-image-2-pro (OpenAI 协议)
    ├─ 尝试 1/3
    ├─ 尝试 2/3
    └─ 尝试 3/3
    ↓
主模型全部失败？
    ├─ ✅ 成功 → 继续下一步
    └─ ❌ 失败 → 启动托底
         ↓
    【托底模型】gemini-3.1-flash-image-preview (Gemini 协议)
         ├─ 上传到 Cloudinary（如果需要）
         ├─ 尝试 1/3
         ├─ 尝试 2/3
         └─ 尝试 3/3
         ↓
    托底模型全部失败？
         ├─ ✅ 成功 → 继续下一步
         └─ ❌ 失败 → 任务失败
```

**总 API 请求次数**:
- 最少：2 次（2 个图层，主模型全部成功）
- 正常：6 次（2 个图层 × 3 次重试，主模型全部成功）
- 最多：12 次（2 个图层 × 3 次主模型 + 3 次托底模型）

---

## 🔍 当前配置验证

### 检查命令
```bash
cd /Users/a123/.openclaw/skills/omni-vision-psd-extractor/

# 检查主模型配置
grep "OPENCLAW_BOUND" .env

# 应该看到:
# OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro  ✅ 正确
# OPENCLAW_BOUND_PROTOCOL=openai  ✅ 正确
```

### 运行测试
```bash
# 测试主模型配置
python3 -c "
from scripts.runtime_config import load_runtime_env, resolve_bound_gemini_config
env = load_runtime_env()
config = resolve_bound_gemini_config(env)
print(f'模型: {config[\"model\"]}')
print(f'协议: {config[\"protocol\"]}')
print(f'端点: {config[\"endpoint\"]}')
"

# 应该输出:
# 模型: gpt-image-2-pro
# 协议: openai
# 端点: https://n.lconai.com/v1/images/edits
```

---

## ⚠️ 发现的问题

### 问题: 日志显示使用了 Gemini

如果日志中出现：
```
⚡ [Bound Gemini] Using gemini-3.1-flash-image-preview
```

**原因**:
1. `.env` 文件被覆盖或修改
2. `OPENCLAW_BOUND_MODEL_ID` 不是 `gpt-image-2-pro`
3. `OPENCLAW_BOUND_PROTOCOL` 不是 `openai`

**解决**:
```bash
# 重新编辑 .env
nano /Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env

# 确保:
OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro
OPENCLAW_BOUND_PROTOCOL=openai
```

---

## 🎯 推荐操作步骤

### Step 1: 验证当前配置
```bash
cd /Users/a123/.openclaw/skills/omni-vision-psd-extractor/
cat .env | grep OPENCLAW_BOUND_MODEL_ID
cat .env | grep OPENCLAW_BOUND_PROTOCOL
```

### Step 2: 如果配置正确，添加托底机制

我将创建一个补丁脚本来实现托底逻辑。

### Step 3: 测试

运行 skill，查看日志：
- ✅ 应该看到：`🎯 [主模型] gpt-image-2-pro`
- ✅ 主模型失败时：`🔄 [托底模型] gemini-3.1-flash-image-preview`

---

## 📝 总结

**当前状态**:
- ✅ `.env` 配置正确（gpt-image-2-pro + openai）
- ❌ 代码缺少托底机制

**需要做的**:
1. 确认 `.env` 配置正确
2. 添加托底机制代码
3. 测试验证

**预期结果**:
- 主模型：`gpt-image-2-pro` (优先使用)
- 托底模型：`gemini-3.1-flash-image-preview` (主模型失败时)
- 每个图层最多 6 次尝试（3 次主 + 3 次托底）

---

*文档生成时间: 2026-06-15*
*版本: v5.2.1*
