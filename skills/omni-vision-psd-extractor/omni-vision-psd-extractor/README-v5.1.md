# Omni-Vision PSD Extractor v5.1 - 使用指南

## 🎉 v5.1 新特性

### 1. **自动 2K 缩放**
- ✅ 上传 Cloudinary 前自动缩放到 2048px（最长边）
- ✅ 保持原始宽高比
- ✅ 对齐到 16 的倍数（提高生成质量）
- ✅ 支持 512px ~ 4096px 任意尺寸输入

### 2. **前景自动切割**
- ✅ 前景透明层自动切割成多个独立元素
- ✅ 基于连通域分析（OpenCV）
- ✅ 按面积排序（主体元素优先）
- ✅ 过滤噪点（最小面积 100px）

### 3. **全新 PSD 结构**
```
PSD 文件
├── 00_SOURCE_REF (隐藏)
│   └── 原图参考
├── 01_BG
│   └── 背景层
└── 05_FOREGROUND_GROUP (文件夹)
    ├── 元素 1 (最大)
    ├── 元素 2
    ├── 元素 3
    └── ...
```

---

## 📝 使用方法

### **最简调用**
```bash
cd /Users/a123/.openclaw/skills/omni-vision-psd-extractor

python3 scripts/run_omni_delivery.py \
  --source "/path/to/image.png" \
  --feishu-user-id "ou_xxx"
```

**自动完成**：
1. ✅ 缩放到 2K（如需要）
2. ✅ 上传到 Cloudinary
3. ✅ 提取背景层
4. ✅ 提取前景层
5. ✅ 切割前景成多个元素
6. ✅ 组装 PSD（原图 + 背景 + 前景组）
7. ✅ 生成预览 + 压缩分卷
8. ✅ 发送到飞书

---

## 🔄 完整工作流程

```
用户提供原图 (任意尺寸)
    ↓
1. 检查尺寸 → 如果超过 2048px，缩放到 2K
    ↓
2. 上传到 Cloudinary → 获得 URL
    ↓
3. Gemini API #1: 提取背景层
   输入: Cloudinary URL + 背景提示词 + 万物提取法典
   输出: 背景层 PNG
    ↓
4. Gemini API #2: 提取前景层（合并）
   输入: Cloudinary URL + 前景提示词 + 万物提取法典
   输出: 前景层 PNG（绿幕背景）
    ↓
5. 去绿幕处理
   输入: 前景层 PNG
   输出: 前景透明层 PNG
    ↓
6. 【新】前景切割
   输入: 前景透明层 PNG
   算法: 连通域分析 (cv2.connectedComponentsWithStats)
   输出: 元素1.png, 元素2.png, ..., 元素N.png
   过滤: 面积 < 100px 的噪点
   排序: 按面积从大到小
    ↓
7. 组装 PSD
   结构: 原图(隐藏) + 背景层 + 前景组(文件夹)
   输出: layered-output.psd
    ↓
8. 生成预览
   输出: reverse-preview.png (所有图层叠加)
    ↓
9. 压缩分卷
   输出: layered-output-delivery.zip + .z01, .z02...
    ↓
10. 交付到飞书
```

---

## 📊 输出文件结构

```
/output/job_xxx/
├── layered-output.psd              # ⭐ 分层 PSD（新结构）
├── reverse-preview.png             # 预览图
├── layered-output-delivery.zip     # 压缩包
├── layered-output-delivery.z01     # 分卷（如需要）
├── manifest.json                   # 元数据（包含元素信息）
├── scene.json                      # PSD 组装蓝图
├── result-summary.json             # 交付摘要
│
├── raw/                            # 原始生成图层
│   ├── background.png
│   ├── background.result.json
│   ├── foreground.png              # 绿幕背景
│   └── foreground.result.json
│
├── layers/                         # 处理后图层
│   ├── background.png
│   └── foreground.png              # 透明 PNG
│
└── elements/                       # ⭐ 前景元素（新增）
    ├── element_1.png               # 最大元素
    ├── element_2.png
    ├── ...
    └── elements.json               # 元素清单
```

---

## 🎨 PSD 图层结构示例

在 Photoshop 中打开 `layered-output.psd`：

```
layered-output.psd
│
├── 👁️‍🗨️ [隐藏] 00_SOURCE_REF
│   └── 原图参考 (用于对比)
│
├── 👁️ 01_BG
│   └── 背景层 (完整背景)
│
└── 📁 05_FOREGROUND_GROUP (前景组)
    ├── 👁️ 元素 1 (面积: 51234px)  ← 最大元素
    ├── 👁️ 元素 2 (面积: 28901px)
    ├── 👁️ 元素 3 (面积: 15678px)
    ├── 👁️ 元素 4 (面积: 8456px)
    └── 👁️ 元素 5 (面积: 3421px)
```

**好处**：
- ✅ 每个元素独立控制（显示/隐藏/透明度/位置）
- ✅ 按面积排序（主体在最上层）
- ✅ 原图保留（方便对比）
- ✅ 文件夹组织（结构清晰）

---

## 🧪 测试步骤

### 1. **测试图片缩放**
```bash
cd scripts
python3 resize_to_2k.py /path/to/large_image.png /tmp/test_2k.png
```

**预期输出**：
```
[缩放] 原始尺寸: 4096×3072
[缩放] 目标尺寸: 2048×1536 (缩放比例: 50.00%)
[缩放] 已保存: /tmp/test_2k.png

✅ 完成！输出文件: /tmp/test_2k.png (2048×1536)
```

### 2. **测试前景切割**
```bash
cd scripts
python3 split_foreground_layers.py \
  /path/to/foreground_transparent.png \
  /tmp/elements \
  2048 \
  1536 \
  100
```

**预期输出**：
```
[切割] 正在分析前景图层: foreground_transparent.png
[切割] 检测到 8 个连通域（包含背景）
[切割] ✅ element_1: 位置=(120,200), 尺寸=800×600, 面积=51234px
[切割] ✅ element_2: 位置=(500,100), 尺寸=400×300, 面积=28901px
...
[切割] 完成！共切割出 5 个元素

✅ 元素清单已保存: /tmp/elements/elements.json
```

### 3. **测试完整流程**
```bash
python3 scripts/run_omni_delivery.py \
  --source "/path/to/test_poster.png" \
  --out-dir "/tmp/omni_test_v5.1" \
  --feishu-user-id "ou_xxx"
```

**预期日志**：
```
[Cloudinary] 图片尺寸 4096×3072 超过 2K，正在缩放...
[Cloudinary] 已缩放到 2048×1536，临时文件: /tmp/...
[Cloudinary] 正在上传图片: ... (1234.5 KB)
[Cloudinary] 上传成功: https://res.cloudinary.com/...
[Cloudinary] 已清理临时文件

[background] ✅ [Bound Gemini] Image generated and saved...
[foreground] ✅ [Bound Gemini] Image generated and saved...

============================================================
[前景切割] 开始切割前景层...
============================================================
[切割] 检测到 5 个连通域
[切割] ✅ element_1: 面积=51234px
...
[前景切割] ✅ 切割完成！
[前景切割] 共切割出 5 个元素
============================================================

[PSD Preview] 检测到 5 个前景元素，将添加到前景组

[Pipeline] All steps completed successfully!
```

---

## 📐 尺寸处理说明

### **输入尺寸**
- 支持任意尺寸：512px ~ 4096px
- 宽度和高度不限制

### **自动缩放规则**
```python
if max(width, height) > 2048:
    scale = 2048 / max(width, height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    # 对齐到 16 的倍数
    new_width = ((new_width + 15) // 16) * 16
    new_height = ((new_height + 15) // 16) * 16
```

### **示例**
| 输入尺寸 | 缩放后 | 说明 |
|---------|--------|------|
| 512×512 | 512×512 | 无需缩放 |
| 1024×768 | 1024×768 | 无需缩放 |
| 2048×1536 | 2048×1536 | 刚好 2K |
| 4096×3072 | 2048×1536 | 缩放 50% |
| 3840×2160 | 2048×1152 | 缩放 ~53% |
| 6000×4000 | 2048×1360 | 缩放 ~34% |

---

## 🔍 前景切割算法说明

### **连通域分析**
使用 OpenCV 的 `cv2.connectedComponentsWithStats`：

1. **提取 Alpha 通道**
2. **二值化**（透明 = 0, 不透明 > 0）
3. **连通域标记**（8-连通）
4. **统计信息**：
   - 边界框 (x, y, width, height)
   - 面积 (像素数)
   - 质心坐标
5. **过滤**：面积 < 100px 的噪点
6. **排序**：按面积从大到小
7. **提取**：每个元素保持原画布尺寸和原位置

### **适用场景**
✅ 适合：
- 元素清晰分离
- 元素之间有空隙
- 背景已透明

❌ 不适合：
- 元素粘连（会合并成一个）
- 元素重叠（会分离不完全）
- 需要语义识别（无法区分"Logo"和"人物"）

---

## 📚 相关文档

- [SKILL.md](SKILL.md) - Skill 使用说明
- [CHANGELOG.md](CHANGELOG.md) - 版本更新日志
- [README-v5.0.md](README-v5.0.md) - v5.0 详细文档

---

## 🎊 v5.1 改进总结

| 功能 | v5.0 | v5.1 |
|------|------|------|
| **图片尺寸** | 固定 4K | 自动 2K |
| **前景层** | 合并层 | 自动切割成多个元素 |
| **PSD 结构** | 原图+背景+前景 | 原图+背景+前景组（文件夹） |
| **元素数量** | 1 个前景 | N 个独立元素 |
| **可编辑性** | 整体调整 | 每个元素独立调整 |

**v5.1 = v5.0 + 智能尺寸 + 自动切割 + 更好的 PSD 结构** ✨
