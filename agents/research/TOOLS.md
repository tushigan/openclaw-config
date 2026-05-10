# TOOLS.md - 调研专家工具配置

## 已配置工具

### 网络搜索
- `tavily_search` - 通用搜索
- `tavily_extract` - 内容提取

### 浏览器自动化
- `browser` - 访问网页收集数据

### 数据智能
- `data-intelligence` - Apify 云端爬虫平台
  - Instagram、Facebook、TikTok 等社交媒体数据
  - Google Maps、Booking 等本地数据
  - 电商数据抓取

### 文档输出
- `feishu_doc` - 飞书文档撰写

## 工具使用示例

### Tavily 搜索
```
搜索"2026 年中国休闲零食市场报告"
→ 使用 tavily_search
→ 提取关键数据和洞察
```

### Apify 爬虫
```
收集天猫虾零食 Top10 品牌数据
→ 使用 data-intelligence 的电商爬虫
→ 输出：品牌、SKU、价格、销量、评价
```

### 浏览器自动化
```
访问小红书收集用户评价
→ 使用 browser 访问网页
→ 提取用户真实反馈
```

## 注意事项

1. 遵守网站 robots.txt
2. 控制爬取频率，避免被封
3. 敏感数据不记录、不传播
4. 数据来源要标注清楚
