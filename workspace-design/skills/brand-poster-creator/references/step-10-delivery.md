# Step 10：交付

## 概述

本步骤负责最终交付确认和复盘报告生成。所有审批流程完成后，向用户确认项目完成，并生成项目复盘报告。

---

## 10.1 前置条件

所有必需的审批节点均已通过：
- **B级项目**：文案审批 + 设计审批
- **A级项目**：文案审批 + 设计审批 + 创意总监审核
- **S级项目**：文案审批 + 设计审批 + 创意总监审核 + 老板最终决策

---

## 10.2 生成复盘报告

无论用户是否清理文件，都生成复盘报告：

```bash
# 生成复盘报告
python3 {baseDir}/scripts/time_tracking.py \
  retrospective \
  --project-dir "[项目目录绝对路径]" \
  --output "[项目目录绝对路径]/project_retrospective.md"
```

### 10.2.1 复盘报告内容

复盘报告包含以下信息：

#### 项目基本信息
- 项目 ID
- 品牌名称
- 项目等级（B/A/S）
- 海报类型（产品推广/品牌发声/年节海报）

#### 时间统计
- 总耗时（从立项到交付）
- AI 处理时间（占比）
- 人工审核时间（占比）
- 各阶段耗时明细：
  - 需求收集
  - 品牌档案查询
  - 蒸馏卡处理
  - 素材检索
  - 文案策划
  - 创意方向
  - Prompt 组装
  - 生图执行
  - 审批流程

#### 审批流程统计
- 审批节点数量
- 各节点审批者
- 各节点响应时长
- 审批通过率
- 超时次数

#### 资源消耗
- 生图次数
- 参考图数量
- 文案修改次数
- 设计修改次数

#### 关键里程碑
- 立项时间
- 文案确认时间
- 创意确认时间
- 生图完成时间
- 最终交付时间

---

## 10.3 向用户展示项目完成信息

```markdown
🎉 **项目审批流程已完成**

- 项目等级：[B/A/S]
- 审批通过节点：
  ✅ 文案策划审核
  ✅ 设计初稿审核
  [如果是 A/S 级] ✅ 创意总监审核
  [如果是 S 级] ✅ 老板最终决策

📊 **项目数据摘要**：
- 总耗时：XX 分钟
- AI 处理时间：XX 分钟（XX%）
- 人工审核时间：XX 分钟（XX%）
- 审批响应平均时长：XX 分钟

详细复盘报告已生成：project_retrospective.md

请选择：
- 回复「完成」→ 清理项目中间文件
- 回复「保留」→ 保留所有文件，不清理
```

---

## 10.4 发送原图 zip 包（如适用）

如果之前发送的是预览图（`delivery_mode=preview_and_zip`），用户确认定稿后，发送原图 zip 包：

```bash
# 读取 delivery_manifest.json
delivery_mode=$(jq -r '.delivery_mode' "[项目目录]/delivery_manifest.json")

if [ "$delivery_mode" = "preview_and_zip" ]; then
  # 发送原图 zip 包
  zip_path=$(jq -r '.deliverables.original_zip.path' "[项目目录]/delivery_manifest.json")
  
  # 调用 message 工具发送 zip 文件
  # message(action=send, channel=feishu, media="$zip_path", mimeType="application/zip")
fi
```

向用户说明：

```markdown
📦 **原图交付包**

已发送原始高清图 zip 包，包含：
- 原始分辨率海报图片
- 项目元数据文件

请下载保存备用。
```

---

## 10.5 最终交付验证

确认以下交付物已完成：

### 必需交付物

- ✅ 成品海报图片已发送（通过 message 工具，有 messageId 记录）
- ✅ 复盘报告已生成（`project_retrospective.md`）
- ✅ 所有审批节点已通过
- ✅ 交付记录已落盘（`delivery_manifest.json`）

### 可选交付物

- 原图 zip 包（大图项目）
- 多版本备选图（用户要求多张时）

---

## 10.6 交付清单示例

### delivery_manifest.json 结构

```json
{
  "delivery_mode": "direct_image",
  "delivery_status": "success",
  "deliverables": {
    "original_copy": {
      "path": "/Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260613-001/images/final_poster.png",
      "size_bytes": 2048576,
      "size_mb": 1.95
    }
  },
  "delivery_evidence": {
    "message_id": "om_xxxxx",
    "chat_id": "oc_yyyyy",
    "delivery_method": "message(media)",
    "delivered_at": "2026-06-13T13:05:00Z"
  },
  "edit_source_image": "/Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260613-001/images/final_poster.png",
  "agent_delivery_contract": {
    "send_plan": {
      "message_tool_arguments": {
        "action": "send",
        "channel": "feishu",
        "media": "/Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260613-001/images/final_poster.png",
        "mimeType": "image/png"
      }
    }
  }
}
```

---

## 10.7 复盘报告示例

### project_retrospective.md 结构

```markdown
# 品牌海报项目复盘报告

## 项目基本信息

- **项目 ID**: BP-20260613-001
- **品牌名称**: 小白心里软
- **项目等级**: B级 - 日常项目
- **海报类型**: 产品推广
- **营销节点**: 春节

## 时间统计

### 总体时间
- **总耗时**: 95 分钟
- **AI 处理时间**: 45 分钟 (47%)
- **人工审核时间**: 50 分钟 (53%)

### 各阶段耗时
- 需求收集: 10 分钟
- 品牌档案查询: 2 分钟
- 蒸馏卡处理: 1 分钟
- 素材检索: 5 分钟
- 文案策划: 12 分钟 (AI: 8分钟, 人工: 4分钟)
- 文案审批: 15 分钟
- 创意方向: 8 分钟
- Prompt 组装: 3 分钟
- 生图执行: 25 分钟
- 设计审批: 20 分钟

## 审批流程统计

### 审批节点
1. **文案策划审核**
   - 审批者: 张三
   - 请求时间: 2026-06-13 11:00:00
   - 响应时间: 2026-06-13 11:15:00
   - 响应时长: 15 分钟
   - 决策: 通过
   - 反馈: 文案符合品牌调性

2. **设计初稿审核**
   - 审批者: 李四
   - 请求时间: 2026-06-13 12:00:00
   - 响应时间: 2026-06-13 12:20:00
   - 响应时长: 20 分钟
   - 决策: 通过
   - 反馈: 设计效果符合预期

### 审批统计
- 平均响应时长: 17.5 分钟
- 审批通过率: 100%
- 超时次数: 0

## 资源消耗

- 生图次数: 1
- 参考图数量: 4（风格1 + 骨架1 + 产品1 + Logo1）
- 文案修改次数: 0
- 设计修改次数: 0

## 关键里程碑

- 立项时间: 2026-06-13 10:00:00
- 文案确认时间: 2026-06-13 11:15:00
- 创意确认时间: 2026-06-13 11:45:00
- 生图完成时间: 2026-06-13 12:00:00
- 最终交付时间: 2026-06-13 12:20:00

## 效率分析

### 优势
- 审批响应及时，无超时情况
- 一次生图成功，无需返工
- 文案和设计均一次通过

### 改进建议
- 素材检索可以提前准备，节省 5 分钟
- 可以考虑文案和创意方向并行处理

## 项目评级

- **整体效率**: A （总耗时 95 分钟，优于平均水平）
- **协作效率**: A （审批响应及时，无阻塞）
- **成品质量**: A （一次通过，无返工）
```

---

## 10.8 关键硬规则

### ✅ 必须遵守

1. **所有审批通过后才能交付**：不得跳过审批节点
2. **必须生成复盘报告**：无论是否清理文件
3. **交付必须有记录**：`delivery_manifest.json` 中必须有 `message_id`
4. **原图 zip 包必须在用户确认后发送**：不得未经确认就发送

### ❌ 禁止行为

1. **不得在审批未完成时交付**
2. **不得跳过复盘报告生成**
3. **不得把本地路径当作交付**
4. **不得自动清理文件**：必须等待用户确认

---

## 完成后执行下一步

用户确认后，进入 **Step 11：清理**（可选）。
