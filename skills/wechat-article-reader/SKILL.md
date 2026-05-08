---
name: wechat-article-reader
description: "读取微信公众号文章全文。当用户提供 mp.weixin.qq.com 链接时自动调用。支持提取标题、作者、发布时间、摘要、正文 HTML/Markdown/纯文本、图片列表。无需登录、无需额外配置。触发词：公众号文章、微信文章、mp.weixin、公众号链接、微信链接。"
metadata: {"openclaw":{"emoji":"📖","requires":{"bins":["python3"]}}}
---

# WeChat Article Reader

读取微信公众号文章全文，提取标题、作者、发布时间、摘要、正文与图片资源。

## 何时使用

- 用户提供 `mp.weixin.qq.com` 开头的链接
- 用户提到"帮我读一下这篇公众号文章"
- 用户分享微信文章链接并要求提取内容

## 使用方法

直接运行脚本，传入文章 URL：

```bash
python3 {baseDir}/scripts/fetch_wechat_article.py <url>
```

可选输出格式：

```bash
python3 {baseDir}/scripts/fetch_wechat_article.py <url> --format text
python3 {baseDir}/scripts/fetch_wechat_article.py <url> --format json
python3 {baseDir}/scripts/fetch_wechat_article.py <url> --format markdown
python3 {baseDir}/scripts/fetch_wechat_article.py <url> --format html
python3 {baseDir}/scripts/fetch_wechat_article.py <url> --save-dir /Users/a123/.openclaw/workspace/outputs/wechat-articles
```

## 输出内容

- 标题
- 作者/公众号
- 发布时间（如能提取）
- 摘要（如有）
- 正文 HTML（尽量保留原始结构）
- 正文 Markdown（近似保留段落、标题、图片）
- 正文纯文本
- 图片链接列表
- 是否检测到验证页外壳
- 可选保存为 JSON / Markdown / 纯文本 / body HTML / 可直接打开的归档 HTML

## 注意事项

- 微信公众号文章常带验证页外壳，但页面源码里可能仍包含正文载荷
- 本脚本优先解析 `content_noencode / JsDecode(...)`，失败时回退到 `js_content`
- 不需要登录、不需要额外配置
- 如文章被删除或设置了更严格的访问限制，脚本会返回错误提示
