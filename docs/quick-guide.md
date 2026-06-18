# OpenClaw 平台爬取优化 - 快速使用指南

## 核心命令速查

### 1. 检查平台锁状态
```bash
python3 /Users/a123/.openclaw/workspace/skills/web-browse-capture/scripts/research_pool.py status
```

### 2. 强制释放卡住的任务
```bash
python3 /Users/a123/.openclaw/workspace/skills/web-browse-capture/scripts/research_pool.py force-release <job_id> <platform>
```

### 3. 检查浏览器 Profile 健康
```bash
python3 /Users/a123/.openclaw/workspace/skills/web-browse-capture/scripts/profile_manager.py health <profile>
```

### 4. 重置 Profile 到干净状态
```bash
python3 /Users/a123/.openclaw/workspace/skills/web-browse-capture/scripts/profile_manager.py reset <profile>
```

### 5. 清理所有僵尸进程
```bash
bash /Users/a123/.openclaw/scripts/cleanup-browser-profiles.sh
```

---

## 新增的强制规则

### 获取平台锁后必须执行

1. **健康检查**（如果不健康则重置）
```bash
python3 profile_manager.py health <profile>
python3 profile_manager.py reset <profile>  # 如果 health != "healthy"
```

2. **页面状态验证**
- 验证当前页面不是旧任务的搜索词
- 如果页面状态错误，先导航到 `about:blank` 清空

### 任务运行期间必须执行

3. **发送心跳**（任务超过5分钟）
```bash
# 每 3-4 分钟执行一次
python3 research_pool.py heartbeat <job_id> <platform>
```

### 抖音商城搜索特别规则

4. **强制使用商城入口**
```python
# 正确
search_url = f"https://www.douyin.com/search/{keyword}?type=goods"

# 错误（会落到综合搜索）
search_url = f"https://www.douyin.com/search/{keyword}"
```

5. **验证页面类型**
- 检查 URL 包含 `type=goods`
- 检查页面包含"价格"、"销量"等商品特征
- 如果是 `type=general` 立即调用 `block`

---

## 常见故障快速修复

### 问题：任务长时间排队
```bash
# 1. 查看谁占着锁
python3 research_pool.py status | grep -A 5 "taobao"

# 2. 强制释放
python3 research_pool.py force-release <stuck_job_id> taobao
```

### 问题：浏览器频繁超时
```bash
# 1. 健康检查
python3 profile_manager.py health research-login-taobao

# 2. 重置 profile
python3 profile_manager.py reset research-login-taobao
```

### 问题：系统资源耗尽（EAGAIN）
```bash
# 执行完整清理
bash /Users/a123/.openclaw/scripts/cleanup-browser-profiles.sh
```

---

## 监控建议

### 定时执行清理（建议添加到 crontab）
```bash
# 每30分钟清理一次
*/30 * * * * /Users/a123/.openclaw/scripts/cleanup-browser-profiles.sh >> /Users/a123/.openclaw/logs/cleanup.log 2>&1
```

### 查看清理日志
```bash
tail -f /Users/a123/.openclaw/logs/cleanup.log
```

---

## 完整文档

详细说明请参考：`/Users/a123/.openclaw/docs/optimization-report-20260610.md`
