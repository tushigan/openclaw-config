# PSD Skill 兜底机制测试文档

## 功能说明

当 PSD skill 的自有 API 配置（`OPENCLAW_BOUND_*`）请求失败后，会自动切换到海报 skill 的 `gpt-image2-gen` 共享配置进行兜底。

## 兜底流程

```
主 API 调用失败
    ↓
检测到失败 (returncode != 0 或输出文件不存在)
    ↓
查找 gpt-image2-gen 脚本
    ↓
使用相同的 prompt、尺寸、source_path
    ↓
调用 gpt-image2-gen（继承海报 skill 的 API 配置）
    ↓
成功 → 继续后续流程（去绿幕、组装 PSD）
失败 → 记录双重失败，返回错误
```

## 兜底特性

### ✅ 保持一致性
- **相同的 prompt**：使用主 API 失败时的完整提示词
- **相同的尺寸**：保持 `suggested_size` 不变
- **相同的底图**：使用 `--ref-base` 传递原图路径

### ✅ 状态记录
失败后的状态文件会记录：
```json
{
  "tasks": {
    "bg": {
      "fallback_used": "gpt-image2-gen",
      "fallback_success": true,
      "status": "completed"
    }
  }
}
```

### ✅ 日志可追溯
```
⚠️ Generation failed for 'bg' after primary API attempts: [错误信息]
🔄 [兜底机制] 切换到 gpt-image2-gen 共享 skill（海报 skill 配置）
📍 找到 gpt-image2-gen: /Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py
🚀 [兜底] 执行 gpt-image2-gen 调用...
✅ [兜底成功] gpt-image2-gen 生成成功: /path/to/output.png
```

## 配置依赖

### PSD Skill 主配置
`.env` 文件中的配置：
```bash
OPENCLAW_BOUND_API_KEY=sk-xxx
OPENCLAW_BOUND_BASE_URL=https://n.lconai.com/
OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro
OPENCLAW_BOUND_PROTOCOL=openai
```

### 兜底配置（继承自 gpt-image2-gen）
位置：`/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/`

兜底调用会自动继承 `gpt-image2-gen` 的 API 配置：
- 从 `gpt-image2-gen` 的 `.env` 或全局 `.env` 读取
- 使用 `BANANA_API_KEY` 或其他配置的 key
- 支持多端点 failover（n.lconai.com / direct.aixor.org）

## 触发场景

兜底机制会在以下情况触发：

1. **主 API 请求失败**（HTTP 错误、超时、认证失败）
2. **API 返回非 0 退出码**
3. **输出文件未生成**（即使 API 返回成功）
4. **所有重试次数用尽**（`--api-retries` 参数）

## 测试方法

### 方法 1：临时破坏主配置
```bash
# 1. 备份当前配置
cp /Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env /tmp/psd-env-backup

# 2. 故意设置错误的 API key
sed -i '' 's/OPENCLAW_BOUND_API_KEY=.*/OPENCLAW_BOUND_API_KEY=invalid-key/' \
  /Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env

# 3. 运行 PSD skill 测试
python3 /Users/a123/.openclaw/skills/omni-vision-psd-extractor/scripts/run_omni_delivery.py \
  --source "/path/to/test.png" \
  --target-size "2K" \
  --feishu-user-id "ou_xxx"

# 4. 观察日志，应该看到：
#    - 主 API 失败
#    - 自动切换到 gpt-image2-gen
#    - 兜底成功

# 5. 恢复配置
mv /tmp/psd-env-backup /Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env
```

### 方法 2：检查状态文件
运行后检查输出目录中的 `state.json`：
```bash
cat /Users/a123/.openclaw/workspace-design/outputs/omni-vision-psd-extractor/*/state.json | jq '.tasks'
```

应该看到：
```json
{
  "bg": {
    "fallback_used": "gpt-image2-gen",
    "fallback_success": true
  },
  "fg": {
    "fallback_used": "gpt-image2-gen",
    "fallback_success": true
  }
}
```

## 失败场景处理

### 场景 1：主 API 失败 + 兜底成功
- ✅ 任务继续执行
- ✅ 生成 PSD 文件
- ✅ 正常交付
- 📊 状态标记 `fallback_success: true`

### 场景 2：主 API 失败 + 兜底失败
- ❌ 任务终止
- 📝 记录双重失败原因
- 🔴 状态标记 `status: "failed"`
- 📊 错误信息包含主失败和兜底失败

### 场景 3：找不到 gpt-image2-gen
- ❌ 任务终止
- 📝 记录 `fallback_available: false`
- 💡 提示用户检查 workspace-design 是否完整

## 性能影响

- **额外延迟**：主 API 失败后增加 1 次兜底请求（~10-30 秒）
- **成功率提升**：双保险机制，大幅降低因单一 API 故障导致的任务失败
- **成本**：兜底请求会消耗额外 API quota（仅失败时）

## 版本历史

- **v5.3.2** (2026-06-16): 新增兜底机制，主 API 失败后自动切换到 gpt-image2-gen 共享配置
