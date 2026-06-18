---
name: "multi-search-engine"
description: "默认免费搜索入口。覆盖 17 个搜索源（8 个国内 + 9 个国际），适合新闻、日报、资料、来源、竞品、报告检索。"
---

# Multi Search Engine

这个 skill 是 OpenClaw 的默认免费搜索入口。
默认用来替代 Tavily 作为第一搜索路径。

## 适用场景

- 搜新闻、晨报、日报
- 找来源、找报道、找资料、找报告
- 找竞品、找官网、找 PDF
- 做中国站点、微信、头条、搜狗补查
- 需要站内搜索、时间过滤、精确匹配

## 默认执行顺序

1. 先用当前网关配置的免费 `web.search` provider 做第一轮搜索。
2. 需要国内结果、微信公众号、头条、精确操作符、时间过滤时，再改用下面的搜索引擎 URL 模板配合 `web_fetch`。
3. `web_fetch` 抽取失败，或页面必须交互时，再用 `browser`。
4. 除非用户明确指定，或免费链路明显失效，不要先用 `tavily_search`。

## 搜索策略

- 新闻 / 晨报：至少交叉两路结果。默认 `1 个国内 + 1 个国际`
- 竞品 / 品牌：先官网，再媒体，再电商 / 社媒
- 报告 / PDF：优先 `filetype:pdf` + `site:`
- 中国消费 / 快消话题：优先百度、360、搜狗、微信、头条；再用 Google / DuckDuckGo 交叉
- 海外技术 / 开发资料：优先 Google、DuckDuckGo、Brave，再做 GitHub / Stack Overflow 定向搜索

## 常用操作符

- 站内搜索：`site:example.com 关键词`
- PDF：`关键词 filetype:pdf`
- 精确短语：`"完整短语"`
- 排除词：`关键词 -排除词`
- 或搜索：`A OR B`

## 时间过滤

- Google 过去 1 天：`tbs=qdr:d`
- Google 过去 1 周：`tbs=qdr:w`
- Google 过去 1 月：`tbs=qdr:m`

## 国内搜索源（8）

- Baidu：`https://www.baidu.com/s?wd={keyword}`
- Bing CN：`https://cn.bing.com/search?q={keyword}&ensearch=0`
- Bing INT：`https://cn.bing.com/search?q={keyword}&ensearch=1`
- 360：`https://www.so.com/s?q={keyword}`
- Sogou：`https://sogou.com/web?query={keyword}`
- WeChat：`https://wx.sogou.com/weixin?type=2&query={keyword}`
- Toutiao：`https://so.toutiao.com/search?keyword={keyword}`
- Jisilu：`https://www.jisilu.cn/explore/?keyword={keyword}`

## 国际搜索源（9）

- Google：`https://www.google.com/search?q={keyword}`
- Google HK：`https://www.google.com.hk/search?q={keyword}`
- DuckDuckGo：`https://duckduckgo.com/html/?q={keyword}`
- Yahoo：`https://search.yahoo.com/search?p={keyword}`
- Startpage：`https://www.startpage.com/sp/search?query={keyword}`
- Brave：`https://search.brave.com/search?q={keyword}`
- Ecosia：`https://www.ecosia.org/search?q={keyword}`
- Qwant：`https://www.qwant.com/?q={keyword}`
- WolframAlpha：`https://www.wolframalpha.com/input?i={keyword}`

## 常用模板

### 站内搜索

```text
site:github.com react agent workflow
site:openai.com gpt-5.5
```

### 报告 / PDF

```text
中国 休闲零食 市场 报告 filetype:pdf
AI agent enterprise adoption filetype:pdf
```

### 晨报 / 日报

```text
AI agent 发布 qdr:d
OpenAI Anthropic Google 模型 发布 qdr:d
品牌 营销 AI 快消 零售 qdr:d
```

## 输出要求

- 不只贴一条结果。至少写标题、来源、为什么相关
- 单一路径证据薄弱时，要标注不确定
- 晨报场景宁缺毋滥，不要为了凑数硬拼
- 结果冲突时，优先官网、权威媒体、原始发布
