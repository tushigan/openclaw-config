# ✅ v5.2.1 模型和缩放更新

## 📋 修改内容

### 1. **缩放目标：4K → 2K**

**文件**: `run_omni_pipeline.py`

**修改前**:
```python
# --- FORCE 4K SCALING (McKinsey Rule) ---
max_edge_4k = 4096
```

**修改后**:
```python
# --- FORCE 2K SCALING (v5.2 规则：缩放到 2048px) ---
max_edge_2k = 2048
```

**新增逻辑**:
- ✅ 如果原图最长边 > 2048px，自动缩放到 2K
- ✅ 如果原图最长边 ≤ 2048px，保持原尺寸不变
- ✅ 输出缩放信息日志

**示例输出**:
```
[INIT] 原图尺寸: 4096×3072
[INIT] 缩放到 2K: 2048×1536 (缩放比例: 50.00%)
```

---

### 2. **模型更换：Gemini → GPT-Image-2-Pro**

**文件**: `runtime_config.py`

**修改前**:
```python
or "gemini-3.1-flash-image-preview"
```

**修改后**:
```python
or "gpt-image-2-pro"  # v5.2: 默认使用 gpt-image-2-pro
```

**影响范围**:
- ✅ API #1（背景提取）使用 `gpt-image-2-pro`
- ✅ API #2（元素整理）使用 `gpt-image-2-pro`

**请求参数**: 保持不变（继续使用 Gemini API 格式）

---

### 3. **故障转移机制：GPT 首发 + Gemini 兜底**

**文件**: `extract_layers.py`

**新增逻辑**:
```python
models_to_try = [
    {
        "name": "gpt-image-2-pro",
        "timeout": 600,  # 10分钟
        "description": "首选模型"
    },
    {
        "name": "gemini-3.1-flash-image-preview",
        "timeout": 240,  # 4分钟
        "description": "兜底模型"
    }
]
```

**工作流程**:
1. ✅ 首先尝试 `gpt-image-2-pro`，超时设置为 **10分钟**
2. ✅ 如果 GPT 失败（超时、HTTP 错误、异常），自动切换到 `gemini-3.1-flash-image-preview`
3. ✅ Gemini 作为兜底模型，超时 4分钟
4. ✅ 两个模型使用相同的提示词
5. ✅ 在 result.json 中记录使用的模型和是否触发兜底（`is_fallback` 字段）

**日志输出示例**:
```
[API] 尝试使用 首选模型: gpt-image-2-pro (超时: 600秒)
[API] 正在调用 gpt-image-2-pro (style=camel, timeout=600s)...
[API] ✅ gpt-image-2-pro 生成成功！
```

或触发兜底时：
```
[API] 尝试使用 首选模型: gpt-image-2-pro (超时: 600秒)
[API] ❌ gpt-image-2-pro 失败: timeout
[API] ⚠️ gpt-image-2-pro 失败，切换到下一个模型...
[API] 尝试使用 兜底模型: gemini-3.1-flash-image-preview (超时: 240秒)
[API] ✅ gemini-3.1-flash-image-preview 生成成功！
[API] 💡 使用了兜底模型
```

---

## 🎯 工作流程（更新后）

```
原图（任意尺寸）
    ↓
检查尺寸
    ├─ > 2048px → 缩放到 2K
    └─ ≤ 2048px → 保持原尺寸
    ↓
API #1: 提取背景（gpt-image-2-pro）
    ↓
API #2: 元素整理（gpt-image-2-pro）
    ↓
GPT-5.4 位置匹配
    ↓
精准原位重组
    ↓
组装 PSD
```

---

## 📊 对比

| 项目 | v5.2 | v5.2.1 |
|------|------|--------|
| **缩放目标** | 4K (4096px) | **2K (2048px)** ✨ |
| **缩放逻辑** | 总是缩放到 4K | 智能缩放（> 2K 才缩放） ✨ |
| **生成模型** | gemini-3.1-flash-image-preview | **gpt-image-2-pro** ✨ |
| **请求格式** | Gemini API | Gemini API（不变） |

---

## ✅ 优势

1. **性能提升** - 2K 分辨率减少 75% 像素处理量
2. **速度更快** - API 生成时间显著降低
3. **质量保证** - 2K 分辨率对大多数海报设计足够
4. **更好的模型** - gpt-image-2-pro 可能提供更好的生成质量

---

## 🚀 立即使用

```bash
python3 scripts/run_omni_pipeline.py \
  --source "/path/to/image.png" \
  --out-dir "/tmp/test_v5.2.1"
```

**🎉 v5.2.1 已就绪！**
