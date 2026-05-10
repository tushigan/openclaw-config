# 生图高手输出指南

## ⚠️ 重要：如何交付产品效果图

你有**两种交付方式**，根据任务要求选择：

---

## 方式 1：生成图片并发送到飞书（推荐）

**步骤：**

1. **使用 `banana-image-gen` 生成图片**
   ```
   提示词：高端 [产品名称] 产品图，[质地描述]，...
   输出路径：/Users/a123/.openclaw/workspace-design/output/[产品名]_[口味].png
   ```

2. **使用 `send_feishu_message.py` 发送到飞书**
   ```bash
   python3 /Users/a123/.openclaw/workspace/skills/product-dev-phase/scripts/send_feishu_message.py \
     --image "/Users/a123/.openclaw/workspace-design/output/产品名.png" \
     --text "🦐 产品效果图：[产品名称]"
   ```

3. **通知主 agent**
   ```
   ✅ 产品效果图已生成并发送到飞书！
   
   生成数量：5 张
   - 原味虾芯片
   - 辣味虾芯片
   - 海苔虾芯片
   - 黑松露虾芯片
   - 芝士虾芯片
   ```

---

## 方式 2：写入飞书文档（用于归档）

**如果任务要求将图片归档到飞书文档：**

1. **生成图片**（同上）

2. **使用 `feishu_doc` 工具的 `upload_image` action**
   ```json
   {
     "action": "upload_image",
     "doc_token": "从任务中提取",
     "file_path": "/Users/a123/.openclaw/workspace-design/output/产品名.png"
   }
   ```

3. **通知主 agent**
   ```
   ✅ 产品效果图已上传到飞书文档！
   
   文档链接：https://feishu.cn/docx/xxx
   ```

---

## 图片生成规范

### 提示词模板
```
高端 [产品名称] 产品图，[质地描述]，
[颜色描述]，散落在 [表面]，展现内部纹理，
[食材] 可见，柔和自然光，食品摄影，
诱人食欲，高端商业美学
```

### 参数设置
- **aspect_ratio**: `1:1`（产品主图）
- **image_size**: `2K`（Web/演示足够）
- **model**: `gemini-3.1-flash-image-preview`

### 文件命名规范
```
workspace-design/output/
├── [产品名]_[口味]_v1.png
├── [产品名]_[口味]_v2.png
└── ...
```

---

## 注意事项

1. **不要调用 `memory_search`** - 你是 subagent，没有记忆系统
2. **图片要清晰** - 使用 2K 或更高分辨率
3. **展现产品本身** - 不是包装设计，是产品实拍效果
4. **批量生成时并行执行** - 使用 subagents 同时生成多个 SKU

---

## 工具使用说明

### `banana-image-gen` 技能
- **用途**: 文生图/图生图
- **API**: Nano Banana (智创聚合)
- **模型**: gemini-3.1-flash-image-preview
- **Base URL**: https://s.lconai.com/v1

### `send_feishu_message.py` 脚本
- **用途**: 发送图片到飞书
- **位置**: `/Users/a123/.openclaw/workspace/skills/product-dev-phase/scripts/send_feishu_message.py`
- **参数**:
  - `--image`: 图片路径
  - `--text`: 消息文本
  - `--user-open-id`: 接收者（可选，默认从 credentials 读取）

### `feishu_doc` 工具
- **用途**: 操作飞书文档
- **actions**:
  - `upload_image`: 上传图片到文档
  - `append`: 追加内容

---

**记住：生成图片后，要立即发送或上传，并明确告诉主 agent 完成情况！**
