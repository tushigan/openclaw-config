# OpenClaw 生图 Skill 和脚本端点配置总览

生成时间：2026-06-10

## 📋 端点配置汇总

### 1. **GPT-Image-2 系列**（图像生成主力）

#### 主端点
- **URL**: `https://n.lconai.com`
- **API Key**: `BANANA_API_KEY` = `sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8`
- **支持模型**: 
  - `gpt-image-2` (最高 2048×2048)
  - `gpt-image-2-pro` (最高 4096×4096)
- **限制**: gpt-image-2 仅支持 2K 以下，超过需用 gpt-image-2-pro

#### 备用端点
- **URL**: `https://direct.aixor.org`
- **API Key**: `BANANA_API_KEY_AIXOR` = `sk-Z51Uf6PR1IifVDDRh431r8HtWXyeN194LDBPBDYdopAv67ir`
- **支持模型**: 
  - `gpt-image-2` (原生支持 4096×4096)
- **优势**: gpt-image-2 在此端点原生支持 4K，无需切换到 pro 模型

#### 默认模型
- **环境变量**: `BANANA_DEFAULT_MODEL` = `gpt-image-2-pro`

---

### 2. **Kling 视频生成**（已停用）

- **Access Key**: `KLING_ACCESS_KEY` = `AnEe3anTH3DBYmRaGL4erJnHGm4JryYt`
- **Secret Key**: `KLING_SECRET_KEY` = `GmBDrQJAbJCaggTNAfh99AnnFJraERRh`
- **状态**: ⚠️ **相关 skill 已删除，仅保留凭证备用**
- **历史用途**: 视频生成任务
- **残留位置**: `skills-store（暂时不用的）/nanobanana-ppt/kling_api.py`

---

### 3. **Dreamina（即梦）视频生成**

- **认证方式**: OAuth Device Flow（本地登录状态）
- **端点**: 火山引擎 Volcengine API（`visual.volcengineapi.com`）
- **CLI 工具**: `dreamina` 命令行工具
- **用途**: 
  - `text2image`: 文生图（但不推荐用于图片生成）
  - `image2video`: 图生视频
  - `multiframe2video`: 多帧视频
  - `multimodal2video`: 多模态视频（支持 seedance2.0 系列）
- **注意**: 此工具仅用于视频生成，禁止用于图片生成任务

---

### 4. **其他服务端点**

#### Dify
- **Base URL**: `https://api.dify.ai/v1`
- **API Key**: `DIFY_API_KEY` = `dataset-FuF4YEjxusledZ8GCpNvOspc`
- **用途**: 知识库和对话 API

#### Memos
- **API Key**: `MEMOS_API_KEY` = `mpg-0vkXHAIrB3sDZF2Tz48qtXFZMMm+Wat6etTxR9ES`
- **用途**: 记忆管理

#### SiliconFlow
- **API Key**: `SILICONFLOW_API_KEY` = `sk-zvblrfaqzsyhfkmkidldxoasptohnoguxkgainhclgkgjeyq`
- **用途**: 待确认

---

## 🔧 核心生图 Skills 和脚本

### 1. **gpt-image2-gen** (核心统一生图 skill)

**位置**: `workspace-design/skills/gpt-image2-gen/`

**核心脚本**:
- `scripts/generate.py`: 主生图脚本
- `scripts/generate_failover.py`: 智能多端点故障转移包装器

**端点配置**:
```python
ENDPOINT_KEYS = {
    'n.lconai.com': os.getenv('BANANA_API_KEY', ''),
    'direct.aixor.org': os.getenv('BANANA_API_KEY_AIXOR', ''),
}
```

**故障转移逻辑**:
1. 首次请求：先尝试主端点 (n.lconai.com)
2. 主端点失败：自动切换到备用端点 (direct.aixor.org) 并记住状态
3. 后续请求：继续使用上次成功的端点
4. 状态文件：`~/.openclaw/.gpt_image_failover_state.json`

**环境变量**:
- `BANANA_API_URL`: 主端点 URL
- `BANANA_API_KEY`: 主端点 API Key
- `BANANA_API_URL_BACKUP`: 备用端点 URL（实际使用 `BANANA_API_URL_AIXOR`）
- `BANANA_API_KEY_BACKUP`: 备用端点 API Key（实际使用 `BANANA_API_KEY_AIXOR`）
- `BANANA_ENABLE_FAILOVER`: 启用故障转移（默认 true）
- `BANANA_MAX_RETRIES`: 每个端点最大重试次数（默认 2）
- `BANANA_RETRY_DELAY`: 重试间隔秒数（默认 1.0）
- `BANANA_FORCE_PRIMARY`: 强制使用主端点（默认 false）

**分辨率支持**:
- n.lconai.com: gpt-image-2 最高 2K，gpt-image-2-pro 最高 4K
- direct.aixor.org: gpt-image-2 原生支持 4K

---

### 2. **brand-poster-creator** (品牌海报生成)

**位置**: `workspace-design/skills/brand-poster-creator/`

**核心脚本**:
- `scripts/generate_image_lconai.py`: 薄壳转发层（委托给 gpt-image2-gen）

**端点配置**: 
- **不再自己调用 API**，所有生图请求转发给 `gpt-image2-gen/scripts/generate.py`
- 通过环境变量传递端点覆盖：
  - `--api-key` → `BANANA_API_KEY`
  - `--base-url` → `BANANA_API_URL`

**架构设计**:
- 完整的品牌海报 workflow (Phase 1-4)
- 真正的 API 调用统一到 gpt-image2-gen
- 保持老参数签名兼容性，逐步迁移

---

### 3. **xiangqingye-desigen** (详情页设计)

**位置**: `workspace-design/skills/xiangqingye-desigen/`

**相关脚本**:
- `scripts/generate_style_guide.py`
- `scripts/generate_typography_ref.py`
- `scripts/mask_edit_openai_compat.py`
- `scripts/probe_gpt_image2_capabilities.py`

**端点配置**: 
- 调用 `BANANA_API_URL` 和 `BANANA_API_KEY`
- 使用 OpenAI 兼容接口格式

---

### 4. **product-photography-workflow** (商品摄影)

**位置**: `workspace-design/skills/product-photography-workflow/`

**相关脚本**:
- `scripts/run_generation.py`
- `scripts/run_camera_preview.py`
- `scripts/common.py`

**端点配置**: 
- 使用 `BANANA_API_URL` 和 `BANANA_API_KEY`

---

### 5. **omni-vision-psd-extractor** (PSD 图层提取)

**位置**: 
- `skills/omni-vision-psd-extractor/`
- `workspace-design/skills/omni-vision-psd-extractor/`

**相关脚本**:
- `scripts/extract_layers.py`
- `scripts/runtime_config.py`
- `scripts/run_omni_delivery.py`

**端点配置**: 
- 使用独立的 Gemini 端点（omni-bound）
- 不走共享的 gpt-image2-gen 路由
- 具体端点配置在 `runtime_config.py` 中

---

### 6. **dreamina-cli** (即梦视频生成)

**位置**: `workspace-design/skills/dreamina-cli/`

**核心工具**: `dreamina` CLI (系统命令)

**认证**: OAuth Device Flow

**用途**: 
- ✅ 视频生成（text2image, image2video, multiframe2video, multimodal2video）
- ❌ 禁止用于图片生成任务

**端点**: 火山引擎 API（内置于 CLI）

---

### 7. **dreamina-reference-video** (参考视频处理)

**位置**: `workspace-design/skills/dreamina-reference-video/`

**相关脚本**:
- `scripts/workflow.py`

**依赖**: 调用 `dreamina-cli` skill

---

## 🔄 故障转移机制

### generate_failover.py 工作流程

```
用户请求
    ↓
读取状态文件 (~/.openclaw/.gpt_image_failover_state.json)
    ↓
确定尝试顺序
    ├─ 首次请求 → 主端点优先
    ├─ 上次备用成功 → 继续用备用
    └─ 强制主端点 → 仅用主端点
    ↓
按顺序尝试端点（每个端点重试 2 次）
    ├─ 主端点 (n.lconai.com)
    │   ├─ 尝试 1
    │   ├─ 尝试 2 (失败后 1 秒延迟)
    │   └─ 失败 → 切换到备用
    └─ 备用端点 (direct.aixor.org)
        ├─ 尝试 1
        ├─ 尝试 2
        └─ 成功 → 保存状态
    ↓
返回结果 + 更新状态文件
```

### 状态文件格式

```json
{
  "current_endpoint": "primary" | "backup",
  "last_success": timestamp
}
```

---

## 📝 使用建议

### 1. 图片生成任务优先级

1. **优先使用**: `gpt-image2-gen` (统一入口)
2. **海报类**: `brand-poster-creator` (内部调用 gpt-image2-gen)
3. **详情页**: `xiangqingye-desigen`
4. **商品摄影**: `product-photography-workflow`

### 2. 视频生成任务

- **优先使用**: `dreamina-cli` (即梦)
- **备选**: Kling API（通过环境变量配置）

### 3. 端点选择策略

- **2K 以下图片**: 主端点 gpt-image-2 足够
- **4K 图片**: 
  - 主端点需用 gpt-image-2-pro
  - 备用端点可用 gpt-image-2 原生支持
- **稳定性要求高**: 启用 failover 机制（默认已启用）

### 4. 端点覆盖

临时切换端点：
```bash
# 强制使用备用端点
BANANA_API_URL="https://direct.aixor.org" \
BANANA_API_KEY="$BANANA_API_KEY_AIXOR" \
python scripts/generate.py ...

# 强制使用主端点（禁用 failover）
BANANA_FORCE_PRIMARY=true \
python scripts/generate_failover.py ...
```

---

## ⚠️ 注意事项

1. **Dreamina 不用于图片生成**: 虽然 dreamina CLI 有 text2image 命令，但明确禁止用于图片生成任务，必须用 gpt-image2-gen

2. **端点隔离**: 
   - 主端点和备用端点使用不同的 API Key
   - 互相独立，互不影响配额

3. **分辨率限制**: 
   - 主端点 gpt-image-2 不支持 >2K，需切换到 gpt-image-2-pro
   - 备用端点 gpt-image-2 原生支持 4K

4. **代理禁用**: 所有生图脚本都显式禁用系统代理，直连端点

5. **状态持久化**: Failover 状态存储在 `~/.openclaw/.gpt_image_failover_state.json`

6. **凭证管理**: 所有敏感 API Key 存储在 `~/.openclaw/.env`，不提交到 git

---

## 🔍 调试命令

```bash
# 查看当前 failover 状态
cat ~/.openclaw/.gpt_image_failover_state.json

# 测试主端点
BANANA_FORCE_PRIMARY=true python workspace-design/skills/gpt-image2-gen/scripts/generate_failover.py \
  --prompt "test" --filename "/tmp/test.png" --size "1024x1024"

# 测试备用端点
BANANA_API_URL="$BANANA_API_URL_AIXOR" \
BANANA_API_KEY="$BANANA_API_KEY_AIXOR" \
python workspace-design/skills/gpt-image2-gen/scripts/generate.py \
  --prompt "test" --filename "/tmp/test.png" --size "1024x1024"

# 重置 failover 状态
rm ~/.openclaw/.gpt_image_failover_state.json

# 查看 dreamina 登录状态
dreamina user_credit
```
