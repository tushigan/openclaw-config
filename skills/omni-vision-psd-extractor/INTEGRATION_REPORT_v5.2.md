# PSD Skill 接入海报生图机制 - v5.2 升级报告

## 修改日期
2026-06-16

## 修改目标
将 PSD skill 的图层提取流程接入海报 skill 的成熟生图机制（`gpt-image2-gen/scripts/generate.py`），提升生图稳定性和成功率。

---

## 核心问题诊断

### 海报 skill 为什么更稳定？

海报 skill 的 `gpt-image2-gen/scripts/generate.py` 有以下成熟特性：

1. **兼容多种返回格式**
   - 自动兼容 `url` 和 `b64_json` 两种返回格式
   - 根据通道自动选择最佳 `response_format`

2. **智能模型路由**
   - `n.lconai.com`：≤2K 用 `gpt-image-2`，>2K 用 `gpt-image-2-pro`
   - `direct.aixor.org`：始终用 `gpt-image-2`（原生支持 4K）

3. **主备通道 Failover**
   - 主通道失败自动切换到 `direct.aixor.org`
   - 支持 cooldown 机制，避免频繁请求失败的通道

4. **多种请求方式**
   - 支持 `requests` 库和 `curl` 命令
   - 自动选择最适合当前环境的方式

### PSD skill 之前的问题

PSD skill 的 `extract_layers.py` 之前硬编码了 OpenAI edits API 调用：

1. **只认 URL 返回**（第 380-391 行）
   ```python
   image_url = data["data"][0].get("url")
   if not image_url:
       last_error = "No image URL in response."
   ```
   - 如果接口返回 `b64_json`，会被判定为失败

2. **硬绑 `gpt-image-2-pro`**
   - 即使是 1K/2K 输出也用 pro 模型
   - 海报 skill 会自动降级到基础版

3. **没有 Failover**
   - 只打 `n.lconai.com`，失败后只是同通道重试 3 次
   - 没有切到备用通道的逻辑

---

## 解决方案

### 修改策略

将 PSD skill 的默认生图路径从"硬编码 Gemini 直连"切换到"海报 skill 的 gpt-image2-gen"。

### 具体修改

#### 1. 修改 `runtime_config.py` 第 66 行

**修改前**：
```python
env.setdefault("OMNI_FORCE_BOUND_GEMINI", "1")
```

**修改后**：
```python
# 🔥 v5.2: 默认使用海报 skill 的 gpt-image2-gen（支持 failover、兼容 URL/base64、智能模型路由）
# 如需强制使用旧的 Gemini 直连，设置环境变量 OMNI_FORCE_BOUND_GEMINI=1
env.setdefault("OMNI_FORCE_BOUND_GEMINI", "0")
```

#### 2. 修改 `extract_layers.py` 第 638-645 行

**修改前**：
```python
force_gemini = (
    env.get("OMNI_USE_GPT_IMAGE2") != "1"
    and (
        args.force_gemini
        or env.get("OMNI_FORCE_BOUND_GEMINI", "1") == "1"  # 默认值是 "1"
        or env.get("BANANA_FORCE_GEMINI") == "1"
    )
)
```

**修改后**：
```python
# 🔥 v5.2: 默认使用海报 skill 的 gpt-image2-gen（更成熟的生图链路）
# 环境变量默认值从 "1" 改为 "0"，匹配 runtime_config.py 的新默认值
force_gemini = (
    env.get("OMNI_USE_GPT_IMAGE2") != "1"
    and (
        args.force_gemini
        or env.get("OMNI_FORCE_BOUND_GEMINI", "0") == "1"  # 默认值改为 "0"
        or env.get("BANANA_FORCE_GEMINI") == "1"
    )
)
```

---

## 新的执行流程

### 默认路径（推荐）

1. `force_gemini = False`
2. 调用海报 skill 的 `generate.py`
3. 享受完整的 failover、format 兼容、模型智能路由

```python
gen_args = [sys.executable, str(generator_path), "--prompt-file", str(prompt_file), "-s", suggested_size, "-o", str(raw_out)]
gen_args.extend(["--ref-base", source_path])
```

### 备用路径（兼容性保留）

如需使用旧的 Gemini 直连（不推荐），可设置：

```bash
export OMNI_FORCE_BOUND_GEMINI=1
```

或者命令行参数：

```bash
python extract_layers.py --manifest manifest.json --force-gemini
```

---

## 预期效果

### 稳定性提升

- ✅ 兼容 URL 和 base64 返回格式
- ✅ 主通道失败自动切换备用通道
- ✅ 智能选择 gpt-image-2 或 gpt-image-2-pro
- ✅ 支持 curl 和 requests 双重请求方式

### 性能优化

- ✅ 1K/2K 输出自动用基础版模型（更快）
- ✅ 参考图自动压缩（减少上传时间）
- ✅ Cloudinary 图床避免重复上传

### 成本优化

- ✅ 不在小分辨率时浪费 pro 模型额度

---

## 兼容性

### 向后兼容

✅ 保留了所有旧的环境变量和参数：

- `--force-gemini` 参数仍然有效
- `OMNI_FORCE_BOUND_GEMINI=1` 可恢复旧行为
- `BANANA_FORCE_GEMINI=1` 可强制 Gemini 路径

### 现有项目

✅ 现有项目无需修改，自动获得升级

---

## 测试建议

### 基础测试

```bash
cd /Users/a123/.openclaw/skills/omni-vision-psd-extractor

# 测试默认路径（应该走海报 generate.py）
python scripts/run_omni_pipeline.py \
  --source auto \
  --out-dir /tmp/psd-test-v5.2 \
  --target-size 2K
```

### 验证点

1. 日志中应该出现 `Running generator command`（走 generate.py）
2. 不应该出现 `[Bound Gemini]`（旧路径）
3. 生成的图片应该在 `/tmp/psd-test-v5.2/` 目录

### 回退测试

```bash
# 强制使用旧的 Gemini 路径
export OMNI_FORCE_BOUND_GEMINI=1

python scripts/run_omni_pipeline.py \
  --source auto \
  --out-dir /tmp/psd-test-old \
  --target-size 2K
```

验证日志中出现 `[Bound Gemini]` 标记。

---

## 总结

这次修改**最小化侵入**，只改了两处默认值（从 `"1"` 到 `"0"`），就让 PSD skill 接入了海报 skill 的成熟生图机制。

**核心优势**：
- 更稳定（failover + format 兼容）
- 更智能（自动模型路由）
- 更快（小分辨率用基础版）
- 更省钱（不浪费 pro 额度）

**兼容性**：
- 100% 向后兼容
- 随时可通过环境变量回退

---

## 下一步

建议在真实项目中测试几次，确认：

1. 生图成功率是否提升
2. 是否还会出现"只认 URL"的错误
3. failover 是否正常工作

测试通过后，可以考虑删除旧的 `_run_openai_image_edits()` 和 `_run_gemini_generate()` 函数，进一步简化代码。
