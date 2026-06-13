# 飞书云盘大文件上传功能 - 使用指南

## 📋 功能概述

v5.1.1 版本新增智能大文件处理功能，根据 PSD 文件大小自动选择最佳交付方式，解决飞书 30MB 文件限制问题。

## 🎯 智能分档策略

| 文件大小 | 交付方式 | 用户体验 | 适用场景 |
|---------|---------|---------|---------|
| **< 30MB** | 直接发送 | ⭐⭐⭐⭐⭐ | 小型海报、简单设计 |
| **30-100MB** | 分卷压缩（18MB/卷） | ⭐⭐⭐ | 中型项目、多图层设计 |
| **> 100MB** | 飞书云盘链接 | ⭐⭐⭐⭐⭐ | 大型项目、复杂设计 |

### 为什么选择 100MB 作为云盘阈值？

1. **飞书限制**：单文件上传限制 30MB，分卷压缩最多支持到 100MB 左右
2. **用户体验**：100MB+ 的文件分卷后可能产生 6+ 个文件，下载和解压体验差
3. **云盘优势**：100MB+ 文件在云盘中下载更稳定，支持断点续传

## 🔄 工作流程

### 场景 1：小文件（< 30MB）

```
用户提供原图
    ↓
生成 PSD（例如：25MB）
    ↓
✅ 直接发送到飞书
    ↓
用户收到：
  - 预览图
  - PSD 文件
```

**用户体验**：⭐⭐⭐⭐⭐ 最快最简单

---

### 场景 2：中型文件（30-100MB）

```
用户提供原图
    ↓
生成 PSD（例如：85MB）
    ↓
✅ 分卷压缩（18MB × 5 = 90MB）
    ↓
发送到飞书：
  - 预览图
  - layered-output-delivery.zip
  - layered-output-delivery.z01
  - layered-output-delivery.z02
  - layered-output-delivery.z03
  - layered-output-delivery.z04
    ↓
用户下载所有分卷 → 解压
```

**用户体验**：⭐⭐⭐ 需要下载多个文件

---

### 场景 3：大文件（> 100MB）— 飞书云盘

```
用户提供原图
    ↓
生成 PSD（例如：125MB）
    ↓
检测文件大小 > 100MB
    ↓
✅ 上传到飞书云盘
    ↓
OpenClaw Agent 调用 feishu_drive_file 工具
    ↓
获取 file_token
    ↓
生成下载链接
    ↓
发送到飞书：
  - 📊 文件信息（尺寸、图层数、大小）
  - 🖼️ 预览图
  - 📥 下载链接
    ↓
用户点击链接 → 飞书云盘 → 下载 PSD
```

**用户体验**：⭐⭐⭐⭐⭐ 一键下载，支持断点续传

---

## 🚀 OpenClaw Agent 执行流程

当 PSD 文件 > 100MB 时，系统会输出以下提示：

```
============================================================
[飞书云盘] 准备上传大文件到云盘
[飞书云盘] 文件: layered-output.psd
[飞书云盘] 大小: 125.34 MB
============================================================

============================================================
⚠️  需要 OpenClaw Agent 执行飞书云盘上传
============================================================
请使用 OpenClaw 的 message 工具调用 feishu_drive_file 上传文件：
1. 调用 feishu_drive_file 工具
2. action: upload
3. file_path: /Users/a123/.openclaw/workspace-design/outputs/job_xxx/layered-output.psd
4. 获取返回的 file_token
5. 生成飞书文件 URL: https://bytedance.larkoffice.com/file/{file_token}
6. 发送消息到用户，包含预览图和下载链接
============================================================
```

### Agent 需要执行的操作

**步骤 1：调用 feishu_drive_file 工具上传**

使用 OpenClaw 的 `message` 工具调用 `feishu_drive_file`：

```json
{
  "tool": "feishu_drive_file",
  "action": "upload",
  "file_path": "/Users/a123/.openclaw/workspace-design/outputs/job_xxx/layered-output.psd"
}
```

**步骤 2：获取返回的 file_token**

工具返回格式：
```json
{
  "file_token": "xxxxxxxxxxxxxxxxx",
  "file_name": "layered-output.psd",
  "size": 131536896
}
```

**步骤 3：生成飞书文件 URL**

```
https://bytedance.larkoffice.com/file/{file_token}
```

**步骤 4：发送消息到用户**

使用 `message` 工具发送：

1. 先发送预览图（`reverse-preview.png`）
2. 再发送文本消息，包含：
   - 文件信息
   - 下载链接

消息模板：
```
【PSD 文件已生成】

📊 文件信息：
- 尺寸：2048×1536
- 图层：原图 + 背景 + 5个前景元素
- 大小：125.3 MB

📥 下载地址：
https://bytedance.larkoffice.com/file/xxxxxxxxxxxxxxxxx

💡 提示：点击链接直接在飞书云盘中下载 PSD 文件
```

---

## 📊 输出文件说明

### result-summary.json 结构

当触发飞书云盘上传时，`result-summary.json` 会包含 `feishuDriveUpload` 字段：

```json
{
  "status": "success",
  "source": "/path/to/source.png",
  "createdAt": "2026-06-11T10:30:00Z",
  "paths": {
    "outDir": "/path/to/output",
    "psd": "/path/to/output/layered-output.psd",
    "preview": "/path/to/output/reverse-preview.png",
    "manifest": "/path/to/output/manifest.json",
    "scene": "/path/to/output/scene.json"
  },
  "delivery": {
    "kind": "111omni-n-layer-psd",
    "target": {...},
    "sendResult": {
      "attempted": false,
      "status": "pending_feishu_drive_upload",
      "method": "feishu_drive",
      "upload_info": {...}
    }
  },
  "feishuDriveUpload": {
    "success": true,
    "method": "feishu_drive_upload",
    "tool": "feishu_drive_file",
    "action": "upload",
    "file_path": "/path/to/output/layered-output.psd",
    "file_name": "layered-output.psd",
    "size": 131536896,
    "size_mb": 125.34,
    "instruction": "..."
  }
}
```

---

## 🧪 测试场景

### 测试 1：小文件（直接发送）

```bash
# 生成一个小 PSD（预计 < 30MB）
python3 scripts/run_omni_delivery.py \
  --source "/path/to/small_poster.png" \
  --feishu-user-id "ou_xxx"
```

**预期**：直接发送 PSD 文件和预览图到飞书

---

### 测试 2：中型文件（分卷压缩）

```bash
# 生成一个中型 PSD（预计 30-100MB）
python3 scripts/run_omni_delivery.py \
  --source "/path/to/medium_design.png" \
  --feishu-user-id "ou_xxx"
```

**预期**：生成分卷压缩包（.zip + .z01 + .z02...），发送所有分卷

---

### 测试 3：大文件（飞书云盘）

```bash
# 生成一个大 PSD（预计 > 100MB）
python3 scripts/run_omni_delivery.py \
  --source "/path/to/large_complex_design.png" \
  --feishu-user-id "ou_xxx"
```

**预期**：
1. 输出飞书云盘上传提示
2. `result-summary.json` 包含 `feishuDriveUpload` 字段
3. 等待 OpenClaw Agent 执行上传

---

## ⚙️ 配置选项

### 自定义大小阈值

如果需要修改阈值，编辑 `run_omni_delivery.py`：

```python
# 当前默认值
FEISHU_DIRECT_SEND_THRESHOLD_MB = 30    # < 30MB 直接发送
FEISHU_DRIVE_THRESHOLD_MB = 100         # > 100MB 上传云盘
```

### 禁用云盘上传

如果需要强制使用分卷压缩（不使用云盘），可以修改代码或添加 `--no-feishu-drive` 参数。

---

## 🎊 优势总结

| 维度 | 分卷压缩 | 飞书云盘 |
|------|---------|---------|
| **文件大小限制** | ~100MB | 无限制 |
| **用户体验** | ⭐⭐⭐ 需要下载多个文件 | ⭐⭐⭐⭐⭐ 一键下载 |
| **断点续传** | ❌ | ✅ |
| **在线预览** | ❌ | ✅（飞书云盘） |
| **存储成本** | 无 | 飞书云盘额度 |
| **实现难度** | ⭐ | ⭐⭐ |

**结论**：飞书云盘方案是大文件（> 100MB）的最佳选择！

---

## 📚 相关文档

- [SKILL.md](SKILL.md) - Skill 使用说明（v5.1.1）
- [README-v5.1.md](README-v5.1.md) - v5.1 详细使用指南
- [CHANGELOG.md](CHANGELOG.md) - 版本更新日志
