# Step 2：品牌档案查询

## 概述

本步骤负责查询品牌档案和品牌资产，获取品牌调性、定位、Logo、VI 手册等信息，为后续流程提供品牌一致性保障。

⚠️ **生成品牌海报前，必须先查询品牌档案和资产**

---

## 2.1 查询品牌信息

根据 `brief.json` 中的 `brand_name`，查询是否已建立品牌档案。

### 执行查询

```bash
# 1. 查询品牌档案（获取调性、定位、目标受众）
python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "品牌名" --json

# 2. 查询品牌资产（获取 Logo、VI 手册、参考图）
python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "品牌名" --json
```

### 查询结果示例

品牌档案返回格式：

```json
{
  "found": true,
  "brand_name": "品牌名称",
  "brand_tone": "品牌调性描述",
  "positioning": "品牌定位",
  "target_audience": "目标受众",
  "core_values": ["价值观1", "价值观2"],
  "visual_guidelines": {
    "primary_colors": ["#色值1", "#色值2"],
    "fonts": ["字体1", "字体2"]
  }
}
```

品牌资产返回格式：

```json
{
  "found": true,
  "logos": [
    {"path": "/path/to/logo.png", "type": "标准Logo"}
  ],
  "vi_manual": [
    {"path": "/path/to/vi.pdf", "description": "VI 手册"}
  ],
  "reference_images": [
    {"path": "/path/to/ref.jpg", "category": "产品摄影"}
  ]
}
```

---

## 2.2 关键信息提取

### 从品牌档案中提取：
- **品牌调性** (`brand_tone`) - 决定画面氛围和色彩情绪
- **定位** (`positioning`) - 决定视觉语言和风格层级
- **目标受众** (`target_audience`) - 决定画面语境和表达方式
- **核心价值观** (`core_values`) - 用于文案创意方向

### 从品牌资产中提取：
- **Logo 路径** (`logos[]`) - 用于 ref_order.json 的 logo 角色
- **VI 手册** (`vi_manual[]`) - 参考标准色、字体规范
- **参考图** (`reference_images[]`) - 风格参考或产品参考

---

## 2.3 结果处理

### 情况 A：找到品牌档案（found = true）

1. 记录品牌档案信息到项目状态：
   - 将 `profile` 写入项目目录的 `brand_profile_cache.json`
   - 在 `project_state.json` 中标记 `"brand_profile_found": true`

2. 提取关键信息用于后续流程：
   - **视觉规范**：`visual_guidelines.primary_colors`（用于 prompt 生成的色彩约束）
   - **品牌素材路径**：`brand_assets_path`（用于 Step 3 素材检索优先路径）
   - **品牌价值观**：`core_values`（用于 Step 3 文案创意方向）
   - **品牌语气**：`tone_of_voice`（用于文案风格）

3. 向用户告知：
   ```
   ✅ 已找到品牌档案
   - 品牌主色：[列出 primary_colors]
   - 品牌素材路径：[brand_assets_path]
   - 将优先使用品牌档案中的视觉规范和素材路径
   ```

### 情况 B：未找到品牌档案（found = false）

**自动建档流程**

1. 从 `brief.json` 提取可用的品牌信息：

```bash
# 提取品牌信息
brand_info=$(jq '{
  brand_name: .brand_name,
  industry: .industry,
  target_audience: (.target_audience // ""),
  core_values: (if .core_message then [.core_message] else [] end),
  brand_tone: (.brand_tone // "")
}' brief.json)
```

2. **暂停任务，询问用户是否创建品牌档案**：

向用户展示提取的信息，提供两个选项：

```markdown
🆕 检测到新品牌"XX"，是否创建品牌档案？

当前已知信息：
- 品牌名称：XX
- 行业/品类：[从 brief.json.industry 提取]
- 目标受众：[从 brief.json.target_audience 提取]
- 核心信息：[从 brief.json.core_message 提取]

创建品牌档案的好处：
✅ 后续项目可复用品牌信息（视觉规范、品牌调性、素材路径）
✅ 确保品牌输出物的一致性
✅ 减少重复填写信息的工作量

选项：
1. **创建档案并继续**（推荐：适合长期合作品牌）
2. **仅本次使用，不建档**（适合一次性项目或测试）
```

3. **用户选择"创建档案并继续"**：

调用创建脚本：

```bash
# 解析 brand_info 中的各字段
brand_name=$(echo "$brand_info" | jq -r '.brand_name')
industry=$(echo "$brand_info" | jq -r '.industry // ""')
target_audience=$(echo "$brand_info" | jq -r '.target_audience // ""')
core_values=$(echo "$brand_info" | jq -r '.core_values | join(",")')

# 创建品牌档案
python3 /Users/a123/.openclaw/scripts/memory/brand.py \
  create \
  --name "$brand_name" \
  --industry "$industry" \
  --target-audience "$target_audience" \
  --core-values "$core_values"
```

创建成功后：
- 在 `project_state.json` 中标记 `"brand_profile_found": true`
- 将档案信息写入 `brand_profile_cache.json`
- 向用户确认：
  ```
  ✅ 品牌档案已创建
  - 档案位置：/Users/a123/.openclaw/projects/XX/_brand-profile.json
  - 已记录品牌信息，后续项目将自动复用
  ```

4. **用户选择"仅本次使用，不建档"**：

- 在 `project_state.json` 中标记 `"brand_profile_found": false`
- 继续执行后续流程（Step 3 飞书云盘素材搜索）
- 向用户告知：
  ```
  ℹ️ 品牌未建档，将使用通用流程
  - 将从飞书云盘搜索品牌素材
  - 下次执行相同品牌任务时，仍会提示是否建档
  ```

---

## 2.4 冲突检测流程（品牌档案已存在时）

在 **情况 A：找到品牌档案** 之后，新增以下步骤：

### 2.4.1 检测品牌信息冲突

```bash
# 从 brief.json 提取新信息
new_info=$(jq '{
  industry: .industry,
  target_audience: (.target_audience // ""),
  core_values: (if .core_message then [.core_message] else [] end),
  brand_tone: (.brand_tone // "")
}' brief.json)

# 检测冲突
conflicts=$(python3 /Users/a123/.openclaw/scripts/memory/brand.py \
  check-conflict \
  --name "$(jq -r '.brand_name' brief.json)" \
  --new-info "$new_info")

has_conflict=$(echo "$conflicts" | jq -r '.has_conflict')
```

### 2.4.2 处理高严重性冲突

如果 `has_conflict = true`，提取冲突详情并**暂停任务**：

```bash
high_conflicts=$(echo "$conflicts" | jq '[.conflicts[] | select(.severity == "high")]')
conflict_count=$(echo "$high_conflicts" | jq 'length')

if [ "$conflict_count" -gt 0 ]; then
  # 向用户展示冲突
  echo "$high_conflicts" | jq -r '.[] | "⚠️ 冲突字段：\(.field)\n档案记录：\(.archived)\n当前输入：\(.new_input)\n"'
fi
```

向用户展示冲突并提供选项：

```markdown
⚠️ 品牌信息冲突检测

检测到以下冲突：

**字段：行业**
- 档案记录：烘焙
- 当前输入：餐饮

如何处理？
1. **使用档案记录**（烘焙）- 保持品牌一致性
2. **更新档案为新信息**（餐饮）- 档案可能过时，需更新
3. **仅本次使用新信息，不更新档案** - 临时偏差，档案不变
```

根据用户选择执行：

**选项 1：使用档案记录**
- 使用档案中的值继续执行
- 不更新档案

**选项 2：更新档案为新信息**
```bash
# 更新档案
python3 /Users/a123/.openclaw/scripts/memory/brand.py \
  update \
  --name "$brand_name" \
  --field "industry" \
  --value "餐饮" \
  --operation replace
```

**选项 3：仅本次使用新信息**
- 使用新值继续执行
- 不更新档案

### 2.4.3 自动合并低严重性补充信息

```bash
supplements=$(echo "$conflicts" | jq -r '.supplements')
supplement_count=$(echo "$supplements" | jq 'length')

if [ "$supplement_count" -gt 0 ]; then
  # 自动合并补充信息
  echo "$supplements" | jq -c '.[]' | while read -r item; do
    field=$(echo "$item" | jq -r '.field')
    new_value=$(echo "$item" | jq -c '.new_input')
    
    # 调用更新脚本（append 操作）
    python3 /Users/a123/.openclaw/scripts/memory/brand.py \
      update \
      --name "$brand_name" \
      --field "$field" \
      --value "$new_value" \
      --operation append
  done
  
  # 记录补充信息，任务结束后通知用户
  echo "$supplements" | jq -r '.[] | "- \(.field): 新增 \(.new_input | tostring)"' > supplement_log.txt
fi
```

任务结束后，向用户通知补充信息：

```markdown
✅ 已补充品牌档案：
- 核心价值观：新增"用心品质"、"匠心传承"
- 目标受众：扩展为"25-45岁女性"
```

---

## 2.5 品牌一致性保障

海报生成流程必须遵守以下规则：
- 画面风格必须符合品牌调性
- Logo 使用品牌资产库中的官方文件
- 色彩参考品牌 VI 规范
- 视觉语言匹配目标受众审美

---

## 2.6 与 Step 3 的协作

- 若品牌档案中有 `brand_assets_path`（飞书云盘路径），Step 3 优先在该路径下搜索
- 若品牌档案中的路径无效或未找到素材，Step 3 回退到默认根目录搜索

---

## 完成后执行下一步

品牌档案查询完成后，进入 **Step 3：蒸馏卡检查** 或 **Step 3：飞书云盘品牌素材检索**。
