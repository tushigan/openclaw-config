# 更新日志 - v5.3.0 触发词尺寸控制

**发布日期**: 2026-06-16

## 新增功能

### 🎯 触发词尺寸控制

用户可以在触发词后直接指定输出尺寸，无需修改配置或传递复杂参数。

**使用示例**:
```
无损提取PSD        → 默认 2K (2048px)
无损提取PSD 1K     → 1024px 最长边
无损提取PSD 2K     → 2048px 最长边
无损提取PSD 4K     → 4096px 最长边
```

### 📐 统一尺寸缩放

- **强制缩放**: 无论原图大小，都会按最长边缩放到目标尺寸
- **保持宽高比**: 智能等比例缩放
- **16px 对齐**: 自动对齐到 16 的倍数，提高生成质量
- **高质量重采样**: 使用 LANCZOS 算法

### 🔧 新增工具

1. **`parse_trigger_size.py`**: 触发词解析工具
   - 从用户输入中提取尺寸规格
   - 支持 1K/2K/4K 大小写不敏感
   - 返回清理后的触发词和尺寸参数

2. **`test_size_control.py`**: 功能测试脚本
   - 触发词解析测试
   - 尺寸规格解析测试
   - 缩放计算测试
   - 集成流程测试

## 修改文件

### 脚本更新

1. **`resize_to_2k.py`** → 重构为通用尺寸处理
   - 新增 `parse_target_size()`: 解析尺寸规格（1K/2K/4K/整数）
   - 新增 `resize_image()`: 通用缩放接口，支持任意目标尺寸
   - 保留 `resize_to_2k()`: 向后兼容别名
   - 修复类型注解兼容性（Python 3.9+）

2. **`run_omni_delivery.py`**
   - 新增 `--target-size` 参数（默认 "2K"）
   - 将目标尺寸传递给 pipeline

3. **`run_omni_pipeline.py`**
   - 新增 `--target-size` 参数
   - 使用 `parse_target_size()` 解析目标尺寸
   - 自动计算缩放后的画布尺寸
   - 替换原有的硬编码 4K 逻辑

### 文档更新

1. **`SKILL.md`**
   - 版本号更新: v5.2.0 → v5.3.0
   - 新增触发词尺寸控制说明
   - 更新推荐命令示例
   - 更新尺寸处理说明
   - 更新 OpenClaw 执行规则
   - 更新版本历史

2. **`SIZE_CONTROL_GUIDE.md`** (新增)
   - 完整的使用指南
   - 触发词格式说明
   - 工作原理详解
   - 缩放规则和示例
   - OpenClaw 集成方法
   - 命令行调用示例
   - 测试验证方法
   - 常见问题解答

## 测试结果

所有测试通过 ✅:

```
✅ PASS: 触发词解析 (7/7 测试通过)
✅ PASS: 尺寸规格解析 (9/9 测试通过)
✅ PASS: 尺寸缩放计算 (6/6 测试通过)
✅ PASS: 集成流程 (3/3 测试通过)
```

### 测试覆盖

- ✅ 触发词解析（有/无尺寸后缀）
- ✅ 尺寸规格解析（1K/2K/4K，大小写不敏感）
- ✅ 缩放比例计算（多种原始尺寸 × 多种目标尺寸）
- ✅ 16px 对齐验证
- ✅ 参数传递流程
- ✅ 向后兼容性

## 技术细节

### 架构变更

```
v5.2.0: 硬编码 2K/4K
用户输入 → run_omni_delivery.py → run_omni_pipeline.py (固定 4K)

v5.3.0: 动态尺寸控制
用户输入 "无损提取PSD 1K"
  ↓
parse_trigger_size() → trigger="无损提取PSD", size="1K"
  ↓
run_omni_delivery.py --target-size "1K"
  ↓
run_omni_pipeline.py --target-size "1K"
  ↓
parse_target_size("1K") → 1024
  ↓
resize_image(target_size="1K")
  ↓
API 请求 1024×768 画布
  ↓
PSD 输出 1024×768
```

### 缩放算法改进

**v5.2.0 逻辑**:
```python
# 固定 4K
max_edge_4k = 4096
scale = max_edge_4k / current_max
```

**v5.3.0 逻辑**:
```python
# 动态目标尺寸
target_max_edge = parse_target_size(args.target_size)  # 1024/2048/4096
scale = target_max_edge / current_max
```

### 向后兼容性

- ✅ 保留 `resize_to_2k()` 函数别名
- ✅ 默认参数 `--target-size "2K"` 保持原有行为
- ✅ 无触发词后缀时自动使用 2K
- ✅ 所有旧脚本无需修改

## 使用示例

### OpenClaw Agent 调用

```javascript
// 解析用户输入
const userInput = message.content; // "无损提取PSD 1K"

// 方案 1: 使用解析工具
const parseCmd = `python3 ${skillDir}/scripts/parse_trigger_size.py "${userInput}"`;
const parseResult = await exec(parseCmd);
const { trigger, size_default } = JSON.parse(parseResult.stdout);

// 方案 2: 直接传递（推荐）
await exec({
  command: `python3 ${skillDir}/scripts/run_omni_delivery.py`,
  args: [
    "--source", sourceImagePath,
    "--target-size", size_default, // "1K"
    "--feishu-user-id", userId
  ]
});
```

### 命令行直接调用

```bash
# 1K 输出
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --target-size "1K" \
  --feishu-user-id "ou_xxx"

# 2K 输出（默认）
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --feishu-user-id "ou_xxx"

# 4K 输出
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --target-size "4K" \
  --feishu-user-id "ou_xxx"
```

## 已知限制

1. **仅支持 1K/2K/4K**: 其他尺寸需要传递整数像素值
2. **强制缩放**: 小图会被放大到目标尺寸（可能影响质量）
3. **16px 对齐**: 实际输出尺寸可能有 ±8px 的微小偏差

## 未来计划

- [ ] 支持更多预设尺寸（如 3K）
- [ ] 添加 `--no-upscale` 选项（小图不放大）
- [ ] 支持自定义对齐参数（如 32px 对齐）
- [ ] 添加尺寸验证和警告（如原图太小时）

## 迁移指南

### 从 v5.2.0 升级

无需修改现有代码，默认行为保持不变（2K 输出）。

如需使用新功能，只需在触发词后添加尺寸后缀：

```
旧: "无损提取PSD"       → 2K 输出
新: "无损提取PSD 1K"    → 1K 输出
新: "无损提取PSD 4K"    → 4K 输出
```

### 从 v5.0-5.1 升级

默认尺寸从 2K 更改为可配置，但仍默认为 2K。无需修改。

## 问题反馈

如遇到问题，请提供：
1. 触发词输入
2. 原图尺寸
3. 预期输出尺寸
4. 实际输出尺寸
5. `result-summary.json` 内容

## 贡献者

- 设计: @user
- 实现: @Claude (Opus 4.8)
- 测试: 自动化测试脚本

## 相关链接

- [SKILL.md](SKILL.md) - Skill 使用文档
- [SIZE_CONTROL_GUIDE.md](SIZE_CONTROL_GUIDE.md) - 尺寸控制详细指南
- [scripts/parse_trigger_size.py](scripts/parse_trigger_size.py) - 触发词解析工具
- [scripts/test_size_control.py](scripts/test_size_control.py) - 功能测试脚本
