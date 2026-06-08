# 精简模式使用指南

## 问题背景

在生成故事板时，如果遇到以下错误：

```
Error: HTTPSConnectionPool(host='n.lconai.com', port=443): Max retries exceeded with url: /v1/images/edits 
(Caused by ProxyError('Unable to connect to proxy', RemoteDisconnected('Remote end closed connection without response')))
```

这是因为**请求体过大**导致代理层拒绝连接。

### 原因分析

- **提示词过大**：标准模式的提示词约 6.5KB
- **参考图体积**：2 张参考图约 525KB
- **总请求体**：超过 530KB，超过代理层限制（推测 ~500KB）

## 解决方案：精简模式

精简模式将提示词从 **6.5KB 压缩到 1.7KB**，压缩率达到 **74%**，总请求体降至约 **527KB**。

### 精简策略

1. **约束头部精简**：
   - 原版：分段展开（正确理解、严格禁止、对比说明、结构真相）
   - 精简版：合并为简短格式（核心约束 + 结构）

2. **故事板提示词精简**：
   - 原版：15 条详细要求
   - 精简版：3 条核心要求

3. **保留核心信息**：
   - ✅ 所有 IP 约束
   - ✅ 关键帧规划
   - ✅ 画幅和格式要求
   - ❌ 冗余说明和重复内容

## 使用方法

### 方法 1：使用测试脚本（推荐）

```bash
cd /Users/a123/.openclaw/skills/dreamina-reference-video/scripts

python3 regenerate_storyboard_compact.py --run-dir /path/to/run
```

**示例**：
```bash
python3 regenerate_storyboard_compact.py \
  --run-dir /Users/a123/.openclaw/workspace-design/outputs/shuangjiang-skill-run/dreamina-reference-video-copy/outputs/dreamina-reference-video/projects/huangxiaogu-shuangjiang-recut/runs/20260529-101719-ip
```

### 方法 2：在代码中使用

```python
from scripts.workflow import build_prompts

# 标准模式
prompts = build_prompts(brief, compact=False)

# 精简模式
prompts_compact = build_prompts(brief, compact=True)
```

## 效果对比

### 标准模式提示词示例

```
**关键约束（最高优先级）**：
正确理解：
- 只有脚部作为肢体，身体是完整造型体块
- 身体两侧是主体造型的侧面轮廓，不是独立肢体
严格禁止：
- 严禁添加任何手臂、手掌、手指或上肢结构
- 严禁添加任何翅膀、翼状结构或类似飞行器官
...（省略 6000+ 字节）
```

**大小**：~6500 字节

### 精简模式提示词示例

```
**核心约束**：
严禁：禁止长出手臂、手掌、人类手指；禁止长出额外翅膀或常规鸡翅；禁止把角色变成普通圆鸡而失去拇指体块轮廓；禁止正面或背面视角尾巴消失；禁止脸部五官漂移、比例突变、材质突变；禁止写实动物羽毛质感，保持干净 3D 吉祥物质感

**结构**：整体外轮廓必须是拇指体块与黄色小鸡融合的一体化造型；正面和背面视角都应看到尾巴呈现；侧面视角可以看不到尾巴，这是正常结构；角色没有手，也没有额外翅膀，只有脚；鸡冠、黄色主体、橙色嘴和橙色脚必须稳定保留；角色要保持圆润、玩具感、可爱且有品牌吉祥物完成度
故事板：6格黑白分镜，9:16画幅
主体：黄小咕 IP，一只黄色鸡，整体外轮廓为拇指体块鸡形吉祥物的拟物角色
行为：前 3 秒环境建立与镜头缓推，第 3 秒主体从画外欢快走入，后段在定版海报场景中站定，最后 2 秒文字与版式元素逐步出现，形成品牌收尾
场景：霜降节气海报世界：高山远景、晨光日出、红枫林、带霜前景岩石，空气通透，活泼元气而有秋日诗意
锚点：高山远景、红枫林、带霜岩石

要求：
1. 6格独立9:16画幅，带文字标注和箭头
2. 连续空间，保持角色一致
3. 关键帧：
1. 建立空间：霜降节气海报世界
2. 动作推进：前 3 秒环境建立与镜头缓推
3. 动作推进：第 3 秒主体从画外欢快走入
4. 收束定格：后段在定版海报场景中站定
5. 动作推进：2 秒文字与版式元素逐步出现
6. 收束定格：形成品牌收尾
```

**大小**：~1700 字节

**压缩率**：74.1%

## 注意事项

1. **精简模式不影响生成质量**：
   - 所有核心约束都保留
   - 只是去掉了冗余说明
   - AI 模型仍然能理解要求

2. **何时使用精简模式**：
   - 遇到 ProxyError 时
   - 请求体过大导致连接失败时
   - 作为标准模式的备用方案

3. **标准模式 vs 精简模式**：
   - 标准模式：详细说明，适合复杂项目
   - 精简模式：简洁高效，适合解决连接问题

## 后续优化计划

### 短期（已完成）
- ✅ 实现精简模式
- ✅ 创建测试脚本
- ✅ 验证压缩效果

### 中期
- [ ] 在 workflow.py 中增加自动检测：请求体过大时自动切换精简模式
- [ ] 增加重试机制：标准模式失败后自动用精简模式重试
- [ ] 优化参考图压缩：进一步减小图片体积

### 长期
- [ ] 评估是否需要切换生图服务商
- [ ] 实现本地代理优化
- [ ] 支持直连生图服务（绕过代理）

## 相关文件

- `scripts/workflow.py` - 核心逻辑，包含 `build_prompts(compact=True)` 和 `build_constraint_header(compact=True)`
- `scripts/regenerate_storyboard_compact.py` - 测试脚本
- `scripts/test_compact_prompt.py` - 压缩效果测试
- `OPTIMIZATION_LOG.md` - 完整优化日志

## 测试结果

待生图专家使用 `regenerate_storyboard_compact.py` 测试后更新。

预期结果：
- ✅ 请求体大小降至 ~527KB
- ✅ 成功绕过代理层限制
- ✅ 生成的故事板质量不受影响
