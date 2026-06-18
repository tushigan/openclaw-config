# TOOLS.md - OpenClaw 工具能力边界说明

本文件统一说明各 agent 可用工具的能力边界、使用限制和最佳实践。

## 文件操作工具

### write 工具

**能力**：写入文本文件到指定路径

**限制**：
- `content` 参数：建议 <3000 行（约 150KB 文本）
- 超限表现：参数丢失、静默失败、工具调用缺少 content 参数
- 硬限制：单次调用约 3000-5000 行代码

**解决方案**：
- ≥3000 行内容必须分批写入多文件
- 大型 HTML（≥10 页 PPT）：每页独立文件
- 长文档：按章节分文件
- 数据文件：按批次分文件

**最佳实践**：
```bash
# 错误：一次性写入 5000 行
write(path="large.html", content="<5000行HTML>")  # ❌ content 参数会丢失

# 正确：分批写入
mkdir -p slides/
write(path="slides/slide-01.html", content="<200行>")  # ✓
write(path="slides/slide-02.html", content="<200行>")  # ✓
...
```

### read 工具

**能力**：读取文本文件内容

**限制**：
- 单次读取建议 <10MB
- 超大文件可能导致内存占用过高

**最佳实践**：
- 使用 `offset` 和 `limit` 参数分段读取大文件
- 读取前先检查文件大小：`ls -lh <file>`

## 外部进程工具

### exec 工具

**能力**：执行 shell 命令

**限制**：
- **并发进程数**：避免连续启动 >10 个独立进程
- **资源密集型进程**（Chrome/Node/浏览器）：避免短时间启动 >5 个
- **文件描述符**：每个进程会占用多个文件描述符，快速启动大型进程可能导致资源耗尽

**超限表现**：
- `spawn EAGAIN` 错误
- `Resource temporarily unavailable`
- 进程启动失败，但系统进程数限制未达到

**解决方案**：
- 使用脚本封装，内部复用资源实例
- Playwright/Puppeteer 类任务：启动 1 个 browser，循环内复用 context
- 批量截图：不要每次调用 `npx playwright screenshot`，改用 Python `playwright` 库的长期浏览器实例

**最佳实践**：
```python
# 错误：每页启动独立进程
for i in range(18):
    subprocess.run(['npx', 'playwright', 'screenshot', f'page-{i}.html'])  # ❌

# 正确：复用浏览器实例
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()  # 只启动一次
    context = browser.new_context()
    for i in range(18):
        page = context.new_page()
        page.goto(f'page-{i}.html')
        page.screenshot(path=f'page-{i}.png')
        page.close()  # 立即释放
    browser.close()
```

## 外部服务工具

### sessions_spawn（派发 subagent）

**能力**：派发专家 agent 执行子任务

**超时建议**：
- 简单任务：60 秒
- 常规任务：600 秒（10 分钟）
- 深度调研：1800 秒（30 分钟）
- **禁止**：timeout=0（无限等待）

**最佳实践**：
- 任务描述要清晰完整，包含上下文
- 传递绝对路径而非相对路径
- 预估任务复杂度，设置合理超时

### message 工具（Feishu 消息发送）

**能力**：向 Feishu 用户/群组发送消息和文件

**参数说明**：
- 文本消息：使用 `content` 参数
- 图片/文件：使用 `path` 参数（绝对路径）
- **注意**：`image` 参数不存在，发送图片必须用 `path`

**最佳实践**：
```python
# 发送文本
message(content="任务已完成")

# 发送图片（正确）
message(path="/Users/a123/.openclaw/workspace/images/result.png")  # ✓

# 错误用法
message(image="/path/to/image.png")  # ❌ image 参数不存在
```

## 浏览器自动化工具

### browser 工具

**能力**：控制浏览器进行自动化操作

**限制**：
- 每个 browser 实例会占用大量内存（~500MB）
- 同时运行多个 browser 实例可能导致系统资源不足

**最佳实践**：
- 长时间任务使用单个 browser 实例，循环内创建/关闭 page
- 任务完成后立即关闭 browser
- 避免创建超过 3 个并发 browser 实例

## 工具选择决策树

```
任务类型判断
├─ 生成 ≥10 页 PPT → huashu-design 分批模式（每批 3-5 页）
├─ 调研多个来源 → multi-search-engine 并行
├─ 需要外部专家 → sessions_spawn 对应 agent
├─ 批量文件生成（≥8 个）→ 先写脚本，分批执行
├─ 大文件操作（>3000 行）→ 分批写入/分段读取
└─ 资源密集型任务（截图/渲染）→ 复用实例而非每次启动新进程
```

## 常见错误和解决方案

### 错误 1：write 工具 content 参数丢失

**表现**：
```
Validation failed for tool "write": content: must have required properties content
```

**原因**：尝试一次性写入超过 3000 行内容

**解决**：改用分批生成策略，每次写入 <3000 行

### 错误 2：spawn EAGAIN

**表现**：
```
Error: spawn EAGAIN
Resource temporarily unavailable
```

**原因**：短时间内启动过多独立进程（特别是 Chrome/Node）

**解决**：
- 改用长期运行的进程实例
- 在进程启动间增加延迟（sleep 1-2 秒）
- 检查并提高文件描述符限制：`ulimit -n 4096`

### 错误 3：subagent 超时

**表现**：
```
Subagent timeout after 600 seconds
```

**原因**：任务复杂度超出预估时间

**解决**：
- 增加 timeout 参数（深度调研用 1800s）
- 将复杂任务拆解为多个小任务
- 检查 subagent 是否卡在等待用户输入

## 版本历史

- 2026-06-10：初始版本，基于战略专家执行失败问题分析
