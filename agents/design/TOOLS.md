# TOOLS.md - 生图高手工具配置

## 已配置工具

### 图像生成
- `banana-image-gen` - 文生图/图生图技能
  - API: Nano Banana (智创聚合)
  - 模型：gemini-3.1-flash-image-preview
  - Base URL: https://s.lconai.com

### 图片发送
- `send_feishu_message.py` - 飞书图片发送脚本（修复版）
  - 位置：`skills/product-dev-phase/scripts/send_feishu_message.py`
  - 关键修复：`receive_id_type` 作为 query parameter

### 产品方案
- `product-dev-phase` - 产品研发全流程技能

### 文档输出
- `feishu_doc` - 飞书文档撰写（可选）

## 工具使用示例

### 文生图
```bash
python3 skills/banana-image-gen/scripts/generate.py \
  "高端虾芯片产品图，金黄色酥脆质感，散落在白色盘子上" \
  -a 1:1 -s 2K -o workspace/output/product.png
```

### 图生图
```bash
python3 skills/banana-image-gen/scripts/generate.py \
  "添加辣椒碎和花椒调味" \
  -r workspace/output/product.png \
  -a 1:1 -s 2K -o workspace/output/spicy_version.png
```

### 发送图片
```bash
python3 skills/product-dev-phase/scripts/send_feishu_message.py \
  --image "workspace/output/product.png" \
  --text "🦐 产品效果图：虾芯片"
```

## 环境变量

```bash
export BANANA_API_URL="https://s.lconai.com"
export BANANA_API_KEY="sk-ggmpALjAOCLr7WDeCILNxEpx9ZQmntVQOJJScKnVNWhUFrh8"
export BANANA_DEFAULT_MODEL="gemini-3.1-flash-image-preview"
```

## 注意事项

1. 生成图片后立即发送，不要等待
2. 批量生成时使用 sub-agents 并行
3. 图片文件要规范命名
4. 保留生成记录便于迭代
