# PSD Skill 超时配置修改 - v5.3.3

## 修改日期
2026-06-16

## 修改内容

### 统一超时时长：10 分钟（600 秒）

所有 API 请求（多模态模型和 AI 绘图模型）的超时时长统一改为 **600 秒**。

---

## 修改位置

### 1. **run_with_spinner 默认超时** (第 56 行)
```python
# 修改前
def run_with_spinner(cmd, env=None, message="Running", show_spinner=True, timeout=240):

# 修改后
def run_with_spinner(cmd, env=None, message="Running", show_spinner=True, timeout=600):
```

**影响范围**：所有通过 `run_with_spinner` 执行的子进程调用

---

### 2. **OpenAI Image Edits API 请求** (第 321 行)
```python
# 修改前
with urllib.request.urlopen(request, timeout=600) as response:  # 已经是 10 分钟

# 修改后
with urllib.request.urlopen(request, timeout=600) as response:  # 保持 10 分钟
```

**影响范围**：OpenAI /v1/images/edits 协议请求

---

### 3. **生成图片下载** (第 388 行)
```python
# 修改前
with urllib.request.urlopen(image_url, timeout=60) as img_response:

# 修改后
with urllib.request.urlopen(image_url, timeout=600) as img_response:
```

**影响范围**：从 API 返回的 URL 下载生成的图片

---

### 4. **Gemini API 请求** (第 541 行)
```python
# 修改前
with urllib.request.urlopen(request, timeout=240) as response:

# 修改后
with urllib.request.urlopen(request, timeout=600) as response:
```

**影响范围**：Gemini 协议的图像生成请求

---

### 5. **飞书图片发送** (第 615 行)
```python
# 修改前
result = subprocess.run(cmd, text=True, capture_output=True, timeout=180, stdin=subprocess.DEVNULL)

# 修改后
result = subprocess.run(cmd, text=True, capture_output=True, timeout=600, stdin=subprocess.DEVNULL)
```

**影响范围**：通过 lark-cli 发送图片到飞书

---

### 6. **RH 抠图王云端服务** (第 835 行)
```python
# 修改前
timeout=150

# 修改后
timeout=600
```

**影响范围**：RH 抠图王云端抠图服务调用

---

### 7. **本地去绿幕处理** (第 863 行)
```python
# 修改前
timeout=60

# 修改后
timeout=600
```

**影响范围**：本地绿幕去除处理（RH 抠图王失败后的降级方案）

---

## 未修改的超时设置

以下超时设置**不需要修改**（用于进程清理和线程同步）：

```python
process.wait(timeout=2)    # 进程清理等待
t_out.join(timeout=1)      # 线程 join 超时
t_err.join(timeout=1)      # 线程 join 超时
```

---

## 影响分析

### ✅ 正面影响

1. **更高的成功率**
   - 复杂图像生成不再因超时而失败
   - 大尺寸图像（4K）有足够时间完成
   - 多元素提取有更充裕的处理时间

2. **更好的用户体验**
   - 减少因超时导致的任务失败
   - 降低用户重试次数
   - 提高整体稳定性

### ⚠️ 潜在风险

1. **资源占用时间延长**
   - 单个请求最长可能占用 10 分钟
   - 并发任务时可能导致资源排队

2. **失败检测延迟**
   - 真正的失败（如 API 宕机）需要 10 分钟才能检测到
   - 建议配合监控和告警机制

---

## 适用场景

### ✅ 适合长超时的场景

1. **4K 图像生成**
   - 大尺寸图像需要更长处理时间
   - 示例：4096×3072 的背景提取

2. **复杂前景元素**
   - 多个元素、细节丰富的前景
   - 示例：包含人物、文字、Logo、装饰的海报

3. **网络波动环境**
   - API 服务器响应慢
   - 网络不稳定时需要更长容错时间

### ⚠️ 可能不需要 10 分钟的场景

1. **1K 简单图像**
   - 小尺寸图像通常 30-60 秒完成
   - 但 10 分钟超时不影响快速完成

2. **单元素提取**
   - 简单背景或单一前景
   - 实际可能 1-2 分钟完成

---

## 监控建议

### 关键指标

1. **实际处理时长分布**
   ```
   < 1 分钟：XX%
   1-3 分钟：XX%
   3-5 分钟：XX%
   5-10 分钟：XX%
   > 10 分钟（超时）：XX%
   ```

2. **超时失败率**
   - 修改前：X%
   - 修改后：X%

3. **平均任务完成时间**
   - 修改前：X 秒
   - 修改后：X 秒

### 告警阈值建议

- **单次请求 > 5 分钟**：记录日志
- **超时失败率 > 5%**：告警
- **平均时长 > 3 分钟**：检查 API 性能

---

## 回滚方案

如果发现 10 分钟超时导致问题，可以快速回滚：

```bash
# 1. 备份当前版本
cp scripts/extract_layers.py scripts/extract_layers.py.bak.600s

# 2. 批量恢复到 240 秒
sed -i '' 's/timeout=600/timeout=240/g' scripts/extract_layers.py

# 3. 验证语法
python3 -m py_compile scripts/extract_layers.py
```

或使用分级超时策略：
- 简单任务：240 秒（4 分钟）
- 复杂任务：600 秒（10 分钟）

---

## 版本历史

- **v5.3.3** (2026-06-16): 统一超时时长为 10 分钟（600 秒）
- **v5.3.2** (2026-06-16): 智能兜底机制
- **v5.3.1** (2026-06-16): urllib 导入修复

---

## 测试建议

### 测试用例

1. **4K 图像提取**
   ```bash
   python3 scripts/run_omni_delivery.py \
     --source "/path/to/4k-image.png" \
     --target-size "4K" \
     --feishu-user-id "ou_xxx"
   ```

2. **复杂海报提取**
   - 包含多个元素（人物、文字、Logo）
   - 观察实际处理时长

3. **网络模拟测试**
   - 模拟慢速网络环境
   - 验证超时机制是否正常工作

---

**修改人**: Claude (Kiro AI Assistant)  
**验证状态**: ✅ 语法验证通过  
**部署状态**: 待生产测试
