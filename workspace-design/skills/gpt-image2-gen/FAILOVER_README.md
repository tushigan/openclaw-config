# gpt-image-2 双通道生图说明

## 当前配置

- **主端点**: `https://cn.aixor.org`（快速48秒）
- **主模型**: `gpt-image-2`（原生支持 4K，无需 pro）
- **备端点**: `https://n.lconai.com`（稳定81秒）
- **备模型**: 智能路由（≤2K 用 gpt-image-2，>2K 自动切换到 gpt-image-2-pro）
- **默认分辨率**: `1920x1080`（提升速度）
- **尺寸限制**: 最长边 ≤ 3840

## 环境变量

```bash
export BANANA_API_URL="https://cn.aixor.org"
export BANANA_DEFAULT_MODEL="gpt-image-2"
export BANANA_API_URL_AIXOR="https://n.lconai.com"
```

## 智能模型路由

脚本会根据端点和分辨率自动选择合适的模型，**不依赖上游调用方的请求**：

- **cn.aixor.org**: 
  - 所有分辨率强制使用 `gpt-image-2`（原生支持 4K）
  - 即使请求 `gpt-image-2-pro`，也会自动降级到 `gpt-image-2`
  
- **n.lconai.com**: 
  - ≤2048: 强制使用 `gpt-image-2`（自动降级 pro 请求）
  - >2048: 强制使用 `gpt-image-2-pro`（自动升级基础版请求）

**这确保了**：
- 不浪费成本（≤2K 时避免使用昂贵的 pro）
- 不会失败（>2K 时自动升级到支持高分辨率的 pro）
- 对上游调用方透明（无需关心模型选择细节）

## 历史说明

2026-06-02 更新：主通道切换到 cn.aixor.org（快速），备用通道切换到 n.lconai.com（稳定），添加智能模型路由。
如需了解更早的旧链路背景，可参考 workspace memory 记录。
