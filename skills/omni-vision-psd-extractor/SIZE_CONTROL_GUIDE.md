# 触发词尺寸控制使用指南

## 功能说明

从 v5.3.0 开始，`omni-vision-psd-extractor` 支持通过触发词后缀控制输出尺寸。

## 使用方法

### 触发词格式

```
<触发词> [尺寸规格]
```

**支持的尺寸规格**：
- `1K` → 1024px 最长边
- `2K` → 2048px 最长边（默认）
- `4K` → 4096px 最长边
- 无后缀 → 默认 2K

### 使用示例

| 用户输入 | 实际尺寸 | 说明 |
|---------|---------|------|
| `无损提取PSD` | 2048px | 默认 2K |
| `无损提取PSD 1K` | 1024px | 指定 1K |
| `无损提取PSD 2K` | 2048px | 指定 2K |
| `无损提取PSD 4K` | 4096px | 指定 4K |
| `原图提取分层 1K` | 1024px | 指定 1K |
| `语义抠图PSD 4K` | 4096px | 指定 4K |

## 工作原理

### 1. 触发词解析

使用 `scripts/parse_trigger_size.py` 解析用户输入：

```python
from scripts.parse_trigger_size import parse_trigger_size

trigger, size = parse_trigger_size("无损提取PSD 1K")
# trigger = "无损提取PSD"
# size = "1K"
```

### 2. 尺寸缩放

使用 `scripts/resize_to_2k.py` 中的通用接口：

```python
from scripts.resize_to_2k import resize_image

# 缩放到 1K
output_path, w, h = resize_image(
    input_path="input.png",
    output_path="output.png",
    target_size="1K"
)
```

### 3. 流程传递

尺寸参数在整个 pipeline 中传递：

```
用户输入 "无损提取PSD 1K"
  ↓
parse_trigger_size() → size="1K"
  ↓
run_omni_delivery.py --target-size "1K"
  ↓
run_omni_pipeline.py --target-size "1K"
  ↓
resize_image(target_size="1K")
  ↓
API 请求使用 1024×768 画布
  ↓
PSD 输出 1024×768
```

## 缩放规则

### 算法特性

- **按最长边缩放**：保持宽高比
- **强制缩放**：无论原图大小，都会缩放到目标尺寸
- **16px 对齐**：宽高自动对齐到 16 的倍数（提高生成质量）
- **高质量重采样**：使用 LANCZOS 算法

### 缩放示例

#### 原图 4096×3072

| 目标尺寸 | 输出尺寸 | 缩放比例 |
|---------|---------|---------|
| 1K | 1024×768 | 25% |
| 2K | 2048×1536 | 50% |
| 4K | 4096×3072 | 100% |

#### 原图 1920×1080

| 目标尺寸 | 输出尺寸 | 缩放比例 |
|---------|---------|---------|
| 1K | 1024×576 | 53% |
| 2K | 2048×1152 | 107% |
| 4K | 4096×2304 | 213% |

#### 原图 3840×2160

| 目标尺寸 | 输出尺寸 | 缩放比例 |
|---------|---------|---------|
| 1K | 1024×576 | 27% |
| 2K | 2048×1152 | 53% |
| 4K | 4096×2304 | 107% |

## OpenClaw 集成

### Agent 调用示例

```javascript
// 解析用户输入
const userInput = "无损提取PSD 1K";
const parseResult = await exec({
  command: `python3 scripts/parse_trigger_size.py "${userInput}"`,
  captureOutput: true
});

const { trigger, size } = JSON.parse(parseResult.stdout);

// 调用 skill
await exec({
  command: `python3 scripts/run_omni_delivery.py`,
  args: [
    "--source", sourcePath,
    "--target-size", size || "2K",
    "--feishu-user-id", userId
  ]
});
```

### Skill 执行规则更新

在 `AGENTS.md` 中添加：

```markdown
## Skill 调用规则

### omni-vision-psd-extractor

1. 解析用户输入，提取尺寸后缀
2. 使用 `parse_trigger_size.py` 解析触发词
3. 将 `--target-size` 传递给入口脚本
4. 默认使用 2K（无后缀时）
```

## 命令行调用

### 直接指定尺寸

```bash
# 1K 输出
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --target-size "1K" \
  --feishu-user-id "ou_xxx"

# 2K 输出（默认）
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --target-size "2K" \
  --feishu-user-id "ou_xxx"

# 4K 输出
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --target-size "4K" \
  --feishu-user-id "ou_xxx"
```

### 使用触发词解析

```bash
# 解析触发词
PARSE_RESULT=$(python3 scripts/parse_trigger_size.py "无损提取PSD 1K")
SIZE=$(echo "$PARSE_RESULT" | grep "JSON:" | cut -d' ' -f2- | jq -r '.size_default')

# 调用 skill
python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --target-size "$SIZE" \
  --feishu-user-id "ou_xxx"
```

## 测试验证

### 单元测试

```bash
# 测试触发词解析
python3 scripts/parse_trigger_size.py "无损提取PSD"
python3 scripts/parse_trigger_size.py "无损提取PSD 1K"
python3 scripts/parse_trigger_size.py "原图提取分层 2K"
python3 scripts/parse_trigger_size.py "语义抠图PSD 4K"

# 测试尺寸缩放
python3 -c "
from scripts.resize_to_2k import resize_image
resize_image('test.png', 'output_1k.png', '1K')
resize_image('test.png', 'output_2k.png', '2K')
resize_image('test.png', 'output_4k.png', '4K')
"
```

### 集成测试

```bash
# 完整流程测试
python3 scripts/run_omni_delivery.py \
  --source "/path/to/test.png" \
  --target-size "1K" \
  --out-dir "/tmp/test_1k" \
  --no-send

# 验证输出尺寸
python3 -c "
from PIL import Image
img = Image.open('/tmp/test_1k/layered-output.psd')
print(f'输出尺寸: {img.width}×{img.height}')
"
```

## 常见问题

### Q: 原图小于目标尺寸会放大吗？

A: 是的。v5.3 的强制缩放策略会将原图缩放到目标尺寸，无论放大还是缩小。

### Q: 可以使用其他尺寸吗（如 3K）？

A: 当前仅支持 1K/2K/4K。如需其他尺寸，可以直接传递像素值：

```bash
python3 scripts/run_omni_delivery.py \
  --source "image.png" \
  --target-size "3072" \
  --feishu-user-id "ou_xxx"
```

### Q: 尺寸对齐到 16 会改变目标尺寸吗？

A: 会有微小变化。例如：
- 原图 4095×3071 → 目标 2K → 实际 2048×1536（对齐到 16）
- 偏差通常在 ±8px 以内

### Q: 如何验证最终 PSD 尺寸？

A: 读取 `result-summary.json`：

```bash
jq '.paths.psd' out_dir/result-summary.json | xargs python3 -c "
from PIL import Image
import sys
img = Image.open(sys.argv[1])
print(f'{img.width}×{img.height}')
"
```

## 版本兼容性

- **v5.3.0+**：完整支持触发词尺寸控制
- **v5.0-5.2**：仅支持固定 2K/4K
- **v4.x**：不支持自动缩放

## 更新日志

- **2026-06-16**: v5.3.0 发布，新增触发词尺寸控制功能
- 新增 `parse_trigger_size.py` 触发词解析工具
- 重构 `resize_to_2k.py` 支持通用尺寸
- 更新 `run_omni_delivery.py` 和 `run_omni_pipeline.py` 支持 `--target-size` 参数
- 更新 `SKILL.md` 文档说明新功能
