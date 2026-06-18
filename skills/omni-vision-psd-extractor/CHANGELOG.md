# Omni-Vision PSD Extractor - 更新日志

## v5.1.1 (2026-06-11) - 飞书云盘大文件上传

### 🎉 新增功能

#### 1. **智能大文件处理**
- ✅ **三档分流策略**：根据 PSD 文件大小自动选择最佳交付方式
  - < 30MB：直接发送到飞书
  - 30-100MB：分卷压缩后发送（18MB/卷）
  - > 100MB：上传到飞书云盘，发送下载链接
- ✅ **自动判断**：无需手动配置，系统自动选择最优方案
- ✅ **无缝交付**：用户始终获得最佳体验

#### 2. **飞书云盘集成**
- ✅ **大文件上传**：> 100MB 的 PSD 自动上传到飞书云盘
- ✅ **下载链接生成**：自动生成飞书云盘下载链接
- ✅ **突破大小限制**：支持任意大小的 PSD 文件
- ✅ **用户体验优化**：一键下载，支持断点续传

#### 3. **OpenClaw Agent 集成**
- ✅ **工具调用**：通过 `feishu_drive_file` 工具上传
- ✅ **自动通知**：上传完成后自动发送通知和下载链接
- ✅ **智能提示**：详细的执行指令和状态反馈

### 📝 使用方法

#### 最简调用（推荐）
```bash
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --feishu-user-id "ou_xxx"
```

**效果**：
- 自动检测 PSD 文件大小
- 自动选择最佳交付方式
- 大文件自动上传到飞书云盘
- 发送预览图和下载链接

### 🔄 工作流程

**小文件（< 30MB）**：
```
生成 PSD → 直接发送到飞书 ✅
```

**中型文件（30-100MB）**：
```
生成 PSD → 分卷压缩 → 发送所有分卷到飞书 ✅
```

**大文件（> 100MB）**：
```
生成 PSD → 上传到飞书云盘 → 获取下载链接 → 发送预览图和链接 ✅
```

### 📊 交付信息

**飞书消息格式**（大文件）：
```
【PSD 文件已生成】

📊 文件信息：
- 尺寸：2048×1536
- 图层：原图 + 背景 + 5个前景元素
- 大小：125.3 MB

📥 下载地址：
https://bytedance.larkoffice.com/file/xxxxxxxxxx

💡 提示：点击链接直接在飞书云盘中下载 PSD 文件
```

### 📚 相关文档

- [README-feishu-drive.md](README-feishu-drive.md) - 飞书云盘功能详细说明

---

## v5.1.0 (2026-06-11) - 自动 2K 缩放 + 前景自动切割

### 🎉 新增功能

#### 1. **自动 2K 缩放**
- ✅ **智能缩放**：上传前自动检查尺寸，超过 2048px 自动缩放
- ✅ **保持比例**：严格保持原始宽高比
- ✅ **对齐优化**：自动对齐到 16 的倍数（提高生成质量）
- ✅ **支持范围**：512px ~ 4096px 任意尺寸输入
- ✅ **自动清理**：临时文件自动删除

#### 2. **前景自动切割**
- ✅ **连通域分析**：基于 OpenCV `connectedComponentsWithStats`
- ✅ **智能过滤**：自动过滤噪点（< 100px）
- ✅ **面积排序**：按面积从大到小排序（主体元素优先）
- ✅ **位置保持**：每个元素保持原画布尺寸和原位置
- ✅ **元素清单**：生成 `elements.json` 包含所有元素信息

#### 3. **全新 PSD 结构**
```
layered-output.psd
├── 👁️‍🗨️ [隐藏] 00_SOURCE_REF (原图参考)
├── 👁️ 01_BG (背景层)
└── 📁 05_FOREGROUND_GROUP (前景组 - 文件夹)
    ├── 👁️ 元素 1 (最大元素)
    ├── 👁️ 元素 2
    ├── 👁️ 元素 3
    └── ...
```

**优势**：
- 每个元素独立可编辑
- 文件夹组织清晰
- 按面积排序便于识别主体

### 📝 使用方法

同 v5.0.0，无需额外参数，自动启用新功能。

### 📚 相关文档

- [README-v5.1.md](README-v5.1.md) - v5.1 详细使用指南
- [SUMMARY-v5.1.md](SUMMARY-v5.1.md) - v5.1 完成总结

---

## v5.0.0 (2026-06-11) - 2层简化版 + Cloudinary URL传输

### 🎉 重大更新

#### 1. **默认 2 层模式**
- ✅ **默认行为**：只生成背景层 + 前景合并层
- ✅ **API 调用**：从 N+1 次降低到 **仅 2 次**
- ✅ **无需前置解析**：不再需要手动列出 `fg_elements`
- ✅ **自动提示词**：背景和前景提示词已内置，附带《万物提取.md》法典

#### 2. **Cloudinary URL 传输**
- ✅ **原图只上传 1 次**：所有图层共享同一 URL
- ✅ **节省传输流量**：从 Base64 模式的 53MB 降低到 5MB（节省 90%+）
- ✅ **智能缓存机制**：并发处理前预上传，避免重复
- ✅ **自动回退**：上传失败时自动降级到单次上传

### 📝 使用方法

#### 最简调用（推荐）
```bash
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --feishu-user-id "ou_xxx"
```

**效果**：
- 自动提取背景层
- 自动提取所有前景元素（合并）
- 注入《万物提取.md》高级指令
- 生成 PSD + 预览图 + 分卷压缩包
- 自动发送到飞书

#### 自定义提示词
```bash
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --feishu-user-id "ou_xxx" \
  --bg-prompt "提取背景，保持光影氛围" \
  --fg-prompt "提取所有前景元素（人物、文字、Logo、装饰）"
```

#### 高级：强制 N 层模式（不推荐）
```bash
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --fg-elements "品牌Logo,主标题,人物,装饰" \
  --force-n-layer
```

### 🔧 技术细节

#### API 调用流程
```
1. Cloudinary 上传原图 → 获得 URL (1次，约5MB)
   ↓
2. Gemini API #1: 背景层提取 (URL模式，~300 bytes)
   ↓
3. Gemini API #2: 前景层提取 (URL模式，~300 bytes)
   ↓
4. 前景去绿幕 → 透明PNG
   ↓
5. 组装 PSD → 压缩分卷 → 交付
```

**总传输流量**：5MB + 600 bytes ≈ 5MB  
**总 API 调用**：2 次

#### 默认提示词

**背景层**：
```
【极其重要：绝对禁止凭空生成完全不同的风景！必须严格保持原图中的背景结构、
光影和色彩不变，仅仅智能脑补被移除的前景区域。】
将图片中的背景提取出来，需要将前景所有元素全部剔除，只保留背景。

[附加高级指令法典]:
<万物提取.md 完整内容 240行>
```

**前景层**：
```
将图片中除了背景之外的所有前景元素全部提取出来。
【极其重要：强制将背景全部填充为纯正的绿幕（纯绿色，Hex: #00FF00）！
绝对不要生成假透明像素方格背景！】

[附加高级指令法典]:
<万物提取.md 完整内容 240行>
```

### 📊 性能对比

| 指标 | v4.0 (Base64 N层) | v5.0 (URL 2层) | 提升 |
|------|------------------|----------------|------|
| API 调用次数 | 8 次 | 2 次 | **75%↓** |
| 原图传输次数 | 8 次 | 1 次 | **87.5%↓** |
| 传输流量 | 53.2 MB | 5 MB | **90.6%↓** |
| 请求体大小 | 6.67 MB/次 | 300 bytes/次 | **99.99%↓** |

### ⚙️ 配置说明

#### 环境变量（自动加载）
```bash
OPENCLAW_BOUND_API_KEY=sk-ldeV7GIgtTHI...  # Gemini API Key
OPENCLAW_BOUND_BASE_URL=https://s.lconai.com/  # API 端点
OPENCLAW_BOUND_MODEL_ID=gemini-3.1-flash-image-preview  # 模型
```

#### Cloudinary 配置（已内置）
```python
CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dc6kesgub/image/upload"
CLOUDINARY_PRESET = "my_n8n_upload"
```

### 🔄 从 v4.0 迁移

#### 旧命令（v4.0）
```bash
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --bg-prompt "背景" \
  --fg-elements "Logo,标题,人物,装饰" \
  --feishu-user-id "ou_xxx"
```

#### 新命令（v5.0，推荐）
```bash
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --feishu-user-id "ou_xxx"
```

**差异**：
- ❌ 不再需要 `--fg-elements`（自动合并提取）
- ❌ 不再需要 `--allow-2-layer`（已是默认）
- ✅ 提示词已内置（可选自定义）

### 🐛 已知问题

无

### 📚 参考文档

- [SKILL.md](SKILL.md) - 完整使用说明
- [万物提取.md](references/万物提取.md) - 高级提取法典
- [测试脚本](scripts/test_cloudinary_upload.py) - Cloudinary 上传测试

---

## v4.0.0 (历史版本)

### 特性
- N 层精细拆分（需要 `--fg-elements`）
- Base64 内联传输
- 支持 4K 画布

### 问题
- API 调用次数多（N+1 次）
- 传输流量大（每次传完整原图）
- 需要手动前置视觉解析

**此版本已废弃，请升级到 v5.0**
