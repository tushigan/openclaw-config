# Step 4：文案策划

## 概述

本步骤负责派发 `strategy` 和 `copywriter` 两个子代理，分两段完成文案策划工作。`strategy` 负责传播策略和文案框架，`copywriter` 负责最终可上画面的文案撰写。

---

## 4.1 派发 strategy：产出文案策略

### 4.1.1 spawn 参数约束（严格遵守）

**重要**：以下参数规则必须严格遵守，避免报错和重试浪费。

| 参数 | 规则 | 说明 |
|------|------|------|
| `thinking` | 只能填 `"low"` / `"medium"` / `"high"` / `"adaptive"` 之一 | **绝对禁止**把思考内容写进此字段，否则报 `Invalid thinking level` 错误 |
| `model` | 留空 `""` 或填白名单内模型 | 白名单：`huoshan/kimi-k2.5`、`huoshan/kimi-k2.6`、`newapi_channel_conn/gpt-5.4`、`newapi_channel_conn/gpt-5.5`、`zhichuang/claude-opus-4-6`。留空则由目标 agent 使用自身默认模型。**禁止**使用非白名单 provider（如 `aliyun-bailian/kimi-k2.5`） |
| `attachments` | **不要传** | 附件通道未开启（`sessions_spawn.attachments.enabled` 默认 false），传 attachments 会报 `forbidden` 错误。改为在 task 描述中指定文件绝对路径，让子 agent 自行读取 |

### 4.1.2 派发 strategy subagent

```json
{
  "runtime": "subagent",
  "agentId": "strategy-shared",
  "task": "海报文案策略任务（见下方模板）",
  "mode": "run",
  "timeoutSeconds": 600,
  "runTimeoutSeconds": 600,
  "lightContext": true,
  "thinking": "low",
  "model": ""
}
```

⚠️ **注意**：共享 agent 必须使用 `-shared` 后缀（如 `strategy-shared`、`copywriter-shared`），否则会报 `forbidden` 错误。

### 4.1.2b 保持流式卡片活跃（重要）

派发 subagent 后，**立即使用 `sessions_yield` 告知用户进度**，避免长时间无响应导致用户误以为卡住：

```json
{
  "tool": "sessions_yield",
  "message": "文案策略专家已启动，预计 30-60 秒完成策略文件..."
}
```

**等待期间的进度提示规则**：
- Strategy 预计耗时：30-60 秒
- Copywriter 预计耗时：30-60 秒
- 如果超过预计时间，每隔 30 秒 yield 一次进度更新
- 完成后立即读取结果文件并继续下一步

**禁止行为**：
- ❌ 不要 yield 之后就静默等待 3 分钟
- ❌ 不要只回复 "done" 就不管了
- ✅ 要让用户知道任务正在进行中

### 4.1.3 给 strategy 的任务描述模板

```
你是品牌策略专家，需要为以下海报制定文案策略。不要写最终文案。

**先读取以下项目文件获取完整上下文，不要凭空编造：**
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/brief.json
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copy_brief_for_strategy.json（如存在）

## 任务信息
- 海报目的：[产品推广 / 品牌发声 / 年节海报]
- 品牌：[品牌名]
- 行业：[行业]
- 营销节点：[节点]

## 版式约束（来自蒸馏卡）
[如果有蒸馏卡，将 copy_planning_guide 完整内容附在这里]
[每个文案区域的类型、排版方向、尺寸占比、字数建议]

## 品牌信息
- 必露元素：[清单]
- 禁忌：[清单]

## 产品信息（如适用）
- 产品名：[产品名]
- 卖点：[卖点列表]

## 输出要求
输出文案策略，不写最终文案。必须包含：
1. 核心传播主张
2. 卖点优先级
3. 标题/副标题/辅助文案的语气和长度建议
4. 每个蒸馏卡文案区域的表达任务
5. 禁止使用的表达方向

将结果写入：/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copy_strategy.json

格式：
{
  "core_message": "核心传播主张",
  "selling_points_priority": ["卖点1", "卖点2"],
  "tone": "语气",
  "area_guidance": {
    "el-5": { "role": "主标题", "task": "表达任务", "length_hint": "8-12字" },
    "el-7": { "role": "副标题", "task": "表达任务", "length_hint": "12-18字" }
  },
  "must_avoid": ["禁止表达1", "禁止表达2"]
}

完成后只回传：`copy_strategy.json` 路径 + 一句话策略摘要。
```

---

## 4.2 派发 copywriter：产出最终文案

### 4.2.1 前置检查

strategy 完成后，main 必须**确认 `copy_strategy.json` 存在**，再派发 `copywriter` 子代理。

**禁止**：不得在 `copy_strategy.json` 缺失时进入此步骤。

### 4.2.2 派发 copywriter subagent

```json
{
  "runtime": "subagent",
  "agentId": "copywriter-shared",
  "task": "海报最终文案撰写任务（见下方模板）",
  "mode": "run",
  "timeoutSeconds": 600,
  "runTimeoutSeconds": 600,
  "lightContext": true,
  "thinking": "low",
  "model": ""
}
```

⚠️ **注意**：共享 agent 必须使用 `-shared` 后缀。

### 4.2.2b 保持流式卡片活跃

派发 copywriter 后，立即使用 `sessions_yield` 告知进度：

```json
{
  "tool": "sessions_yield",
  "message": "文案专家已启动，基于策略撰写最终上画文案，预计 30-60 秒..."
}
```

### 4.2.3 给 copywriter 的任务描述模板

```
你是文案策划专家，需要基于策略文件为海报写最终可上画面的文案。

**先读取以下项目文件，不要凭空编造：**
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/brief.json
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copy_strategy.json
- /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copy_brief_for_strategy.json（如存在）

## 输出要求
按蒸馏卡文案区域逐一输出最终文案。每个区域必须包含：
1. 文案内容（具体中文文字，可直接上画面）
2. 字体风格建议
3. 对应蒸馏卡元素 ID

将结果写入：/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/copywriting.json

格式：
{
  "el-5": { "文案": "把团圆装进礼盒", "字体风格": "大气端庄" },
  "el-7": { "文案": "新年·心意到家", "字体风格": "细体" }
}

完成后只回传：`copywriting.json` 路径 + 一句话文案策略说明。
```

---

## 4.3 文案结果统一落盘

copywriter 子代理写完 `copywriting.json` 后，main 必须继续运行：

```bash
python3 {baseDir}/scripts/process_copywriting.py \
  --project-dir "[项目目录绝对路径]"
```

### 4.3.1 脚本自动完成

- 校验 `copywriting.json` 是否存在且结构有效
- 规范化每个区域的 `文案` / `字体风格` 字段
- 写入 `copywriting_manifest.json`、`project_state.json`、`audit_log.jsonl`
- 将阶段推进到 `style_profile` / `creative_direction` 前的可续跑状态

---

## 4.4 文案数据结构示例

### copy_strategy.json 示例

```json
{
  "core_message": "新春团圆，心意到家",
  "selling_points_priority": [
    "匠心烘焙",
    "五谷为养",
    "送礼自用"
  ],
  "tone": "温暖、节庆、亲切",
  "area_guidance": {
    "el-5": {
      "role": "主标题",
      "task": "直击新春送礼场景，传递团圆心意",
      "length_hint": "8-12字"
    },
    "el-7": {
      "role": "副标题",
      "task": "强化节庆氛围和品牌联想",
      "length_hint": "12-18字"
    }
  },
  "must_avoid": [
    "过于商业化的促销话术",
    "与节庆氛围不符的冷硬表达"
  ]
}
```

### copywriting.json 示例

```json
{
  "el-5": {
    "文案": "把团圆装进礼盒",
    "字体风格": "大气端庄"
  },
  "el-7": {
    "文案": "新年·心意到家",
    "字体风格": "细体"
  },
  "el-8": {
    "文案": "五谷为养 匠心烘焙",
    "字体风格": "竖排宋体"
  }
}
```

### copywriting_manifest.json 示例

```json
{
  "status": "success",
  "copywriting_file": "copywriting.json",
  "regions_count": 6,
  "validated": true,
  "timestamp": "2026-06-13T11:00:00Z"
}
```

---

## 4.5 关键硬规则

### ✅ 必须遵守

1. **文案阶段必须分两段执行**：先 strategy，后 copywriter
2. **strategy 不写最终文案**：只输出策略框架到 `copy_strategy.json`
3. **copywriter 不凭空编造**：必须基于 `copy_strategy.json` 撰写
4. **文案结果必须落盘**：运行 `process_copywriting.py` 校验和归档
5. **spawn 参数必须正确**：`thinking` 只填枚举值，`attachments` 不传

### ❌ 禁止行为

1. **不得跳过 strategy 直接让 copywriter 凭空写**
2. **不得让 strategy 直接写最终 `copywriting.json`**
3. **不得让 main 手写最终文案顶替 copywriter**
4. **不得在 `copy_strategy.json` 缺失时进入 Step 5**
5. **不得把思考内容写进 `thinking` 参数**
6. **不得传递 `attachments` 参数**
7. **不得使用非 `-shared` 后缀的 agentId**（共享 agent 场景）
8. **不得派发 subagent 后长时间静默**（必须用 `sessions_yield` 保持进度提示）

---

## 4.6 品牌档案信息的使用

如果 Step 2 已查询到品牌档案，在派发 strategy 时应包含以下信息：

```
## 品牌档案信息（已查询）
- 品牌调性：[brand_tone]
- 品牌定位：[positioning]
- 目标受众：[target_audience]
- 核心价值观：[core_values]
- 品牌语气：[tone_of_voice]

请确保文案策略符合品牌调性和目标受众特征。
```

---

## 完成后执行下一步

文案策划完成并落盘后，进入 **Step 5：文案审批**。
