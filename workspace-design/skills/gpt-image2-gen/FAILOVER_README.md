# gpt-image-2-pro 生图说明

## 当前配置

- **主端点**: `https://n.lconai.com`
- **主模型**: `gpt-image-2-pro`
- **备端点**: `https://cn.aixor.org`
- **备模型**: `gpt-image-2`
- **尺寸限制**: 最长边 ≤ 3840

## 环境变量

```bash
export BANANA_API_URL="https://n.lconai.com"
export BANANA_DEFAULT_MODEL="gpt-image-2-pro"
export BANANA_API_URL_AIXOR="https://cn.aixor.org"
```

## 历史说明

当前图片备节点已经切到 `cn.aixor.org`，并固定请求 `gpt-image-2`。
如需了解更早的旧链路背景，可参考 workspace memory 记录。
