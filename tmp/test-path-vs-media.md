# 测试计划：验证 path 参数能否解决话题投送问题

## 发现
- **视频投送**：使用 `path` 参数 → 正确投送到话题 ✅
- **图片投送**：使用 `media` 参数 → 创建新话题 ❌

## 测试方法

### 方法 1：直接在话题中请求（推荐）
在飞书话题中向 @ 生图高手 发送：
```
帮我把这张图片投送到当前话题：
/Users/a123/.openclaw/workspace/feishu-deliver/gpt-image2-gen_20260611_161831/cute_10_cats_1_dog.png
```

让 design agent 手动调用 message 工具时明确使用 path 参数。

### 方法 2：修改 AGENTS.md 规则（更系统）
在 workspace-design/AGENTS.md 中添加规则，强制图片投送使用 path 参数。

## 关键参数对比

### 视频（成功）
```json
{
  "path": "/Users/a123/.openclaw/workspace/feishu-deliver/xxx.mp4",
  "target": "chat:oc_xxx",
  "threadId": "omt_xxx"
}
```

### 图片（失败）
```json
{
  "media": "/Users/a123/.openclaw/workspace/feishu-deliver/xxx.png",
  "target": "chat:oc_xxx", 
  "threadId": "omt_xxx"
}
```

### 建议修改为
```json
{
  "path": "/Users/a123/.openclaw/workspace/feishu-deliver/xxx.png",  // 改用 path
  "target": "chat:oc_xxx",
  "threadId": "omt_xxx"
}
```
