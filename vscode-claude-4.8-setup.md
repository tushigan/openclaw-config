# VS Code 中使用 Claude Opus 4.8 配置指南

本文档记录了如何在 VS Code 中正确配置和使用 Claude Opus 4.8 模型。

## 配置概览

我们使用两个主要的 API 提供商来访问 Claude Opus 4.8：

1. **cc-vibe**（主要通道）
2. **aixor**（备用通道）

两个提供商都使用 Anthropic Messages API 标准接口。

---

## 提供商配置

### 1. cc-vibe 提供商（主通道）

- **API 端点**: `https://cc-vibe.com`
- **API Key**: `sk-95494df1158f1b4fff9a08db03767881e219ff15316ceb8290403ed099c67ffb`
- **API 类型**: `anthropic-messages`（兼容 Anthropic Messages API）

**支持的模型**：
- `claude-opus-4-8` ✅ 当前使用
- `claude-opus-4-7`
- `claude-opus-4-6`

**模型规格**：
- 上下文窗口：100 万 tokens
- 最大输出：20,000 tokens
- 支持推理模式（reasoning）
- 支持多模态输入（文本 + 图片）

**定价**：
- 输入：$2.5 / 1M tokens
- 输出：$12.5 / 1M tokens

---

### 2. aixor 提供商（备用通道）

- **API 端点**: `https://aixor.org`
- **API Key**: `sk-DrxncFmDyewhmXaxsArKtRTPX77H8QmwDLr7s13EHYl4hZtj`
- **API 类型**: `anthropic-messages`

**支持的模型**：
- `claude-opus-4-8` ✅ 备用
- `claude-opus-4-7`
- `claude-opus-4-6`

**模型规格**：与 cc-vibe 相同

---

## 在 VS Code 中配置使用

### 方式一：通过 Continue 扩展

如果使用 [Continue](https://continue.dev) 扩展，配置文件位于 `~/.continue/config.json`：

```json
{
  "models": [
    {
      "title": "Claude Opus 4.8 (cc-vibe)",
      "provider": "anthropic",
      "model": "claude-opus-4-8",
      "apiKey": "sk-95494df1158f1b4fff9a08db03767881e219ff15316ceb8290403ed099c67ffb",
      "apiBase": "https://cc-vibe.com"
    },
    {
      "title": "Claude Opus 4.8 (aixor)",
      "provider": "anthropic",
      "model": "claude-opus-4-8",
      "apiKey": "sk-DrxncFmDyewhmXaxsArKtRTPX77H8QmwDLr7s13EHYl4hZtj",
      "apiBase": "https://aixor.org"
    }
  ]
}
```

### 方式二：通过 Cline/Claude Dev 扩展

如果使用 Cline（原 Claude Dev），在 VS Code 设置中配置：

1. 打开 VS Code 设置（`Cmd + ,`）
2. 搜索 "Cline" 或 "Claude Dev"
3. 配置以下参数：

```
API Provider: Anthropic
API Key: sk-95494df1158f1b4fff9a08db03767881e219ff15316ceb8290403ed099c67ffb
Base URL: https://cc-vibe.com
Model: claude-opus-4-8
```

### 方式三：通过 REST Client 直接调用

如果使用 VS Code 的 REST Client 扩展进行 API 测试：

```http
### Claude Opus 4.8 API 调用示例
POST https://cc-vibe.com/v1/messages
Content-Type: application/json
x-api-key: sk-95494df1158f1b4fff9a08db03767881e219ff15316ceb8290403ed099c67ffb
anthropic-version: 2023-06-01

{
  "model": "claude-opus-4-8",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下你自己。"
    }
  ]
}
```

---

## OpenClaw 中的配置

在 OpenClaw 系统中，Claude Opus 4.8 已配置在以下 agents：

### 1. main agent（龙虾总指挥）
```json
{
  "model": {
    "primary": "cc-vibe/claude-opus-4-8",
    "fallbacks": ["aixor/claude-opus-4-8"]
  }
}
```

### 2. strategy agent（战略专家）
```json
{
  "model": {
    "primary": "cc-vibe/claude-opus-4-8",
    "fallbacks": ["aixor/claude-opus-4-8"]
  }
}
```

### 3. copywriter agent（文案策划专家）
```json
{
  "model": {
    "primary": "cc-vibe/claude-opus-4-8",
    "fallbacks": ["aixor/claude-opus-4-8"]
  }
}
```

配置文件位置：`~/.openclaw/openclaw.json`

---

## API 调用流程

### 标准 Anthropic Messages API 格式

```bash
curl https://cc-vibe.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-95494df1158f1b4fff9a08db03767881e219ff15316ceb8290403ed099c67ffb" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-opus-4-8",
    "max_tokens": 4096,
    "messages": [
      {
        "role": "user",
        "content": "Hello, Claude!"
      }
    ]
  }'
```

### 关键请求头

| Header | 值 | 说明 |
|--------|-----|------|
| `Content-Type` | `application/json` | 必需 |
| `x-api-key` | `sk-95494...` | API 密钥（也可用 `Authorization: Bearer sk-...`） |
| `anthropic-version` | `2023-06-01` | API 版本号 |

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | string | 模型名称（`claude-opus-4-8`） |
| `max_tokens` | integer | 最大输出 tokens（最多 20,000） |
| `messages` | array | 对话消息数组 |
| `temperature` | float | 温度参数（可选，0-1） |
| `system` | string | 系统提示词（可选） |
| `thinking` | object | 推理配置（可选） |

---

## 推理模式（Reasoning）

Claude Opus 4.8 支持扩展思考（Extended Thinking）功能：

```json
{
  "model": "claude-opus-4-8",
  "max_tokens": 4096,
  "thinking": {
    "type": "enabled",
    "budget_tokens": 10000
  },
  "messages": [
    {
      "role": "user",
      "content": "请解决这个复杂的数学问题..."
    }
  ]
}
```

---

## 多模态输入

支持图片输入（base64 或 URL）：

```json
{
  "model": "claude-opus-4-8",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAA..."
          }
        },
        {
          "type": "text",
          "text": "请描述这张图片的内容"
        }
      ]
    }
  ]
}
```

---

## 故障切换策略

OpenClaw 配置了自动故障切换：

1. **优先使用 cc-vibe**：稳定性高，响应速度快
2. **自动切换到 aixor**：当 cc-vibe 不可用时自动切换
3. **负载均衡**：可以手动调整主备顺序

---

## 测试连接

### 快速测试脚本

在 `~/.openclaw/scripts/` 目录下已有测试脚本：

```bash
# 测试 aixor 提供商
node ~/.openclaw/scripts/test-aixor-anthropic.js

# 测试所有 API 端点
node ~/.openclaw/scripts/test-api-endpoints.js
```

### 手动测试

```bash
# 测试 cc-vibe
curl -X POST https://cc-vibe.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-95494df1158f1b4fff9a08db03767881e219ff15316ceb8290403ed099c67ffb" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-opus-4-8","max_tokens":100,"messages":[{"role":"user","content":"测试"}]}'

# 测试 aixor
curl -X POST https://aixor.org/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-DrxncFmDyewhmXaxsArKtRTPX77H8QmwDLr7s13EHYl4hZtj" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-opus-4-8","max_tokens":100,"messages":[{"role":"user","content":"测试"}]}'
```

---

## 常见问题

### 1. API 调用失败

**排查步骤**：
1. 检查 API Key 是否正确
2. 检查网络连接
3. 验证 API 端点是否可访问
4. 查看返回的错误信息

### 2. 模型选择错误

确保模型名称为 `claude-opus-4-8`（不是 `claude-4-opus` 或其他变体）

### 3. 超时问题

如果遇到超时，可以调整：
- OpenClaw 配置中的 `timeoutSeconds`（默认 1800 秒）
- VS Code 扩展的超时设置

### 4. 推理模式不工作

确保在请求中包含 `thinking` 配置，并设置足够的 `budget_tokens`

---

## 安全建议

⚠️ **重要提醒**：

1. **不要将 API Key 提交到 Git 仓库**
   - 已在 `.gitignore` 中排除 `openclaw.json`
   - 使用模板文件 `openclaw.json.template` 进行版本管理

2. **定期轮换 API Key**
   - 建议每 3-6 个月更换一次

3. **监控使用量和成本**
   - 定期检查 token 使用情况
   - 设置预算告警

4. **限制访问权限**
   - 仅在必要的 agent 中启用高级模型
   - 共享版本（`*-shared`）使用更经济的模型

---

## 版本历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2026-06-11 | 1.0 | 初始版本，记录当前配置 |

---

## 相关资源

- [Anthropic API 文档](https://docs.anthropic.com/)
- [Claude Opus 4 系列模型文档](https://docs.anthropic.com/claude/docs/models-overview)
- [OpenClaw 配置文档](./CLAUDE.md)
- [测试脚本目录](./scripts/)

---

## 维护记录

- **当前主要模型**: `cc-vibe/claude-opus-4-8`
- **备用模型**: `aixor/claude-opus-4-8`
- **配置文件**: `/Users/a123/.openclaw/openclaw.json`
- **最后更新**: 2026-06-11
