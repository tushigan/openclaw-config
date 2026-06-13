# Step 7：生图

## 概述

本步骤负责组装 prompt 并派发 design subagent 执行生图任务。main 完成全部策划和脚本编写，design 子代理只负责执行脚本并等待结果。

---

## 7.1 运行 assemble_prompt.py 脚本组装 prompt

**必须通过脚本生成 prompt，禁止手写。**

```bash
python3 {baseDir}/scripts/assemble_prompt.py \
  --brief "[项目目录]/brief.json" \
  --distill "[项目目录]/distill_card.json" \
  --copywriting "[项目目录]/copywriting.json" \
  --style-profile "[项目目录]/style_profile.json" \
  --creative-direction "[项目目录]/creative_direction.json" \
  --output "[项目目录]/prompt_draft.md"
```

**注意**：
- `--style-profile` 为可选参数。有 `style_profile.json` 时传入，无则省略（脚本会使用中性回退描述）
- `--creative-direction` 在用户已确认画面创意表达方案后为必传参数，不得跳过

### 7.1.1 脚本自动完成

1. 读取 brief.json + distill_card.json + copywriting.json + creative_direction.json（如有）
2. 按规则程序化组装 prompt（参考图排序：风格→骨架→产品→IP→Logo）
3. 内置校验：
   - 检查无工作流术语
   - 坐标覆盖率
   - 文案覆盖率
   - 参考图角色挂载是否冲突
   - 创意表达是否缺失主视觉锚点
4. 输出 `prompt_draft.md` 与 `ref_order.json`

---

## 7.2 Prompt 版式模式

`assemble_prompt.py` 必须根据是否存在有效版式元素选择不同 layout adapter：

### A. 固定版式坐标模式

**触发条件**：`distill_card.json.layout_analysis.elements` 存在有效元素

**特征**：
- prompt 中使用 `== 画面布局（固定版式坐标） ==`
- 每个区域必须输出 `x / y / 宽 / 高 / z`，并绑定区域角色、文案或素材
- 用户确认的文案必须落到对应区域；缺失则阻塞
- 模型只在固定区域内做视觉表达，不得自行重排

### B. 自由构图与阅读动线模式

**触发条件**：没有有效版式元素

**特征**：
- prompt 中使用 `== 画面布局（自由构图与阅读动线） ==`
- 不得生成 `x:`、`y:`、坐标框、占位框或"放置在适当位置"
- 使用相对区域约束：顶部信息区、中部主视觉区、底部信息区、前中后景层次
- 锁定第一视觉、辅助视觉、禁忌主角和阅读顺序
- 允许模型在相对区域内自然构图
- 产品、礼盒、包装、食品等静物主视觉使用"陈列姿态、光影承托、场景关系"，不要套用人物动作或站姿语言

---

## 7.3 脚本执行结果处理

### 7.3.1 脚本成功（退出码 0）

向用户展示 prompt 摘要：

```markdown
📝 **生图 Prompt 已组装完成**

- 参考图数量：N 张
- 区域数量：N 个
- 负面约束：N 条
- 分辨率：默认低于 2K；用户明确要求高清/4K/打印时才升高

请确认本次抽卡几张：
- 回复「确认生图」或「确认」→ 按默认 1 张执行
- 回复「抽 2 张 / 2 张 / 3 张」→ 按对应张数执行
- 最多 10 张；如果用户回复超过 10 张，一律按 10 张执行
```

### 7.3.2 脚本失败（退出码 ≠ 0）

展示校验错误，修复后重新运行。不得手补或绕过校验。

---

## 7.4 🔴 CHECKPOINT · STOP：进入生图前必须满足的条件

在派发 design subagent 之前，必须确认以下所有条件：

### 文件存在性检查

- ✅ `prompt_draft.md` 已生成
- ✅ `ref_order.json` 已生成，且其中所有 `path` 都必须是**绝对路径**
- ✅ `ref_order.json` 中每个参考图路径对应的文件都必须真实存在，缺任意一个都不得进入生图

### 创意确认检查

- ✅ 已确认本次抽卡张数：
  - 若用户只回复「确认生图 / 确认 / OK / 可以」，视为默认 `1` 张
  - 若用户回复大于 `10`，必须截断为 `10`
- ✅ 若已执行 Step 6，则 `creative_direction.json` 必须存在，且其中至少包含 `summary`、`hero_focus`、`composition_plan`

### 素材完整性检查

- ✅ 若 `hero_priority.hero_1` 明确为"产品"，则 `brief.json.assets.product` 必须存在且不可为空
- ✅ 若是低清烘焙产品，必须满足二选一：
  - 已有 `assets.product_texture_refs`，或
  - 已生成 `product_reference_manifest.json`
  - **不得用手写/临时生成的 `product_realized.png` 绕过 Step 3.5**
- ✅ 若同时存在 `assets.product` 与 `assets.ip`，两者路径不得相同

### 参考图角色检查

- ✅ 若脚本报告参考图角色冲突，必须先回到素材确认/修正，不得继续生图
- ✅ 若 `must_include` 要求 Logo/IP，`ref_order.json` 必须分别包含 `logo` / `ip` 角色，且路径必须匹配 `brief.json.assets.logo` / `brief.json.assets.ip`
- ✅ `assets.style_refs` 只能放**真实风格参考图**；禁止把上一版 AI 成图、`current_base_ref.png`、`final_poster.png` 等项目输出图继续当 `style_ref`

---

## 7.5 禁止规则

### ❌ Prompt 修改禁令

- 脚本输出即为最终 prompt，main agent **不得手动追加、修改、拼接任何内容**到 `prompt_draft.md`
- 蒸馏卡的 `copy_planning_guide`、`notes`、`Distill ID` 等内部字段不得出现在 prompt 中
- 如果 prompt 不完整，必须修复脚本后重新运行，不得手补

### ❌ 参考图顺序禁令

- 脚本同时输出 `ref_order.json`，记录参考图传图顺序，`run.sh` 必须按此顺序传图
- role 到参数的映射固定为：
  - `style_ref → --ref-style`
  - `skeleton → --ref-layout`
  - `product → --ref-product`
  - `ip → --ref-ip`
  - `logo → --ref-logo`
- 底层生图器必须保持 `ref_order.json` 的参考图顺序；prompt 中的参考图编号采用 1-based 编号，必须与底层 stdout 的 `Reference list` 和 `Reference images` 顺序一致

### ❌ 生图入口禁令

- 不得绕过 `execute_generation.py` 直接调用 `gpt-image2-gen`
- 先固化 `prompt_draft.md`、`ref_order.json`、`run.sh`，再执行正式入口
- 当项目包含品牌 Logo/IP 时，禁止绕过 `execute_generation.py` 直接调用 `gpt-image2-gen`；否则无法校验 Logo/IP 是否被正确挂载

### ❌ 多张出图禁令

- 单 prompt 多张用 `execute_generation.py --count N`，由底层并行 fan-out
- 不得写多条 `generate.py` 顺序命令伪装并行

### ❌ 多方向出图禁令

- 用户明确"三个都要/每个方向各出"时，运行 `split_direction_projects.py` 拆成多个独立项目
- 不得手写 `prompt_A/B/C.txt` 或手动复制项目改状态

### ❌ 产品参考适配禁令

- 如果项目是面包/吐司/烘焙类产品，prompt 中必须显式约束"切面组织真实、湿润回弹、低局部对比、商业软吐司闭合细密组织、孔隙少量且柔和、不要酸面包/欧包/夏巴塔式大开孔、不要均匀蜂窝孔/干海绵/木屑感/网状雕刻/鳞片状/硬描边纹理"，避免把食品组织做成假锐化
- 如果产品参考图分辨率低、角度不完整，或目标姿态与产品参考差异很大，必须在 prompt 中明确"小尺寸产品参考图只锁定身份、轮廓、配色与基础材质，不把压缩像素放大成微观纹理"，不能强行重塑成不存在的完美正面产品
- 对面包/吐司等切面敏感产品，若产品图短边 < 900px，必须自动启用烘焙参考适配：优先使用原始产品图锁身份 + `product_texture_refs` 锁真实组织；没有质地参考时才运行低频软代理。默认不得生成中间 AI 产品 hero 参考；不得要求用户必须补高清图才继续

### ❌ 二维码区域禁令

- 如果二维码区域不需要二维码，prompt 必须写明"不要画二维码、边框、占位框、半透明矩形或按钮框"，防止模型生成空框

---

## 7.6 main 先写好生图脚本

在派发子 agent 之前，main 必须先写好 `run.sh` 到项目目录：

```bash
#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]"
EXEC_SCRIPT="{baseDir}/scripts/execute_generation.py"

python3 "${EXEC_SCRIPT}" --project-dir "${PROJECT_DIR}" --size 1080x1920 --aspect 9:16 --model gpt-image-2 --count 1
```

**注意**：
- 如果用户要求"一次多抽几张 / 给 N 个备选 / 多来几版"，main 必须把数量写进 `run.sh` 的 `--count N`（1-10）。底层 `gpt-image2-gen` 会并行生成，不要手写串行循环。
- 如果用户说"三个都要 / 每个方案各出"，必须先按 Step 5 的 `split_direction_projects.py` 拆成多个子项目；每个子项目分别生成自己的 `prompt_draft.md`、`ref_order.json`、`run.sh`，不得手写 `prompt_A/B/C.txt` 直接生图。
- **参考图顺序由 `assemble_prompt.py` 输出的 `ref_order.json` 决定**，不再手写。run.sh 从该文件动态读取，确保与 prompt 中的参考图编号严格对应
- 所有路径使用绝对路径，不用相对路径
- prompt 从 `prompt_draft.md` 读取，不内联
- 脚本执行后必须产出 `generation_result.json` 与 stdout/stderr 日志，作为唯一验收依据

脚本写完后，main 确认文件存在且内容正确，再进入下一步。

---

## 7.7 派发 design subagent（执行型，不塞上下文）

### 7.7.1 🔴 CHECKPOINT · STOP：main 写完，子 agent 只跑

生图任务由 main 在主会话完成全部策划和脚本编写，子 agent 只负责执行脚本并等待结果。**不要把 prompt、参考图信息、蒸馏卡数据等塞进子 agent 任务描述。**

**强制约束**：
- main 先把生图所需决策全部固化到 `prompt_draft.md`、`ref_order.json`、`run.sh`、`generation_result.json` 约定结构中
- design subagent 视为**执行器**，不是策划者；不得自行补全需求、重写 prompt、调整参考图顺序、改动模型参数或解释项目背景
- 如执行中发现缺文件、参数冲突、输出异常，子 agent 只返回失败事实与结果文件路径，由 main 回到上一阶段修复后再重派，不得让子 agent 临场自行决策
- **绝对禁止** design subagent 在正式生图失败后自行改用 Python / PIL / Pillow / ImageMagick / 本地贴图 / 手工拼图生成"正式海报"
- 若正式生图报配额、权限、模型接口错误，只能保留失败记录并回报 main；除非用户明确要"临时示意图/降级草图"，否则不得产出任何本地合成海报

### 7.7.2 派发参数

```json
{
  "runtime": "subagent",
  "agentId": "design",
  "task": "海报生图：执行脚本",
  "mode": "run",
  "timeoutSeconds": 600,
  "runTimeoutSeconds": 600,
  "lightContext": true,
  "thinking": "low",
  "model": ""
}
```

**spawn 参数约束同 Step 4：**
- `thinking`：只填 `"low"` / `"medium"` / `"high"` / `"adaptive"`，禁止填思考内容
- `model`：留空或用白名单内模型，禁止用非白名单 provider
- `attachments`：不要传，附件通道未开启

### 7.7.3 给子 agent 的任务描述（固定模板，不改动）

```
你是品牌海报生图专家。按以下步骤执行，不要解释、不复述需求、不做方案：

1. 执行以下脚本：
   bash /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/run.sh

2. 读取并确认以下结果文件存在：
   /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/generation_result.json

3. 如果 `generation_result.json` 中 `ok=true`，再确认 `output_paths` 中的所有输出文件都存在。默认 1 张时至少存在：
   /Users/a123/.openclaw/workspace/brand-poster-projects/[任务ID]/images/final_poster.png

4. 完成后只回传：`generation_result.json` 路径；若成功，再附上 `output_paths` 中所有海报路径。

不要修改脚本内容，不要改变参数，不要读取其他无关文件。
不要自行编写任何 Python/PIL/Pillow/ImageMagick/HTML Canvas 拼图脚本，不要产出本地合成海报顶替正式生图结果。
```

---

## 7.8 回收结果

子 agent 完成后（遵守 AGENTS.md 0.7.1 等待完成事件规则）：

1. 先读取 `generation_result.json`，确认 `ok=true`
2. 再检查 `output_paths` 中所有图片是否真实存在；若缺少 `output_paths`，至少检查 `images/final_poster.png`
3. 确认文件大小合理（不应为 0 字节）
4. 对每张成品做视觉核验：
   - IP 必须来自 `brief.json.assets.ip`，不得变成风格参考图人物
   - Logo 必须看起来是官方 Logo，而不是模型临摹的相似文字
5. `ref_order.json` 中包含 `logo` / `ip` 只证明参考图已挂载，不得作为成品保真的结论
6. 若 Logo 需要文件级精确，优先重新生成并预留 Logo 区；仍不稳定时，允许在正式生图成功后做一次受控品牌安全修正：只把官方 Logo 文件放回预留区域，不得重画主体、文案或版式，并在 `generation_result.json` / `delivery_manifest.json` 记录该修正
7. 若任一条件不满足，视为执行失败或品牌保真风险，先查看 `stdout/stderr` 日志，不得向用户播报"已出图"
8. 只有全部通过后，才按 Step 8 流程发送成品图给用户

---

## 7.9 正式生图失败后的处理

如果 `generation_result.json` 中出现以下任一信号：
- `ok=false`
- `fallback_allowed=false`
- `error_category=quota_insufficient`
- `error_category=permission_denied`
- `error_category=provider_error`

则必须执行以下规则：

1. 停在 `generation failed`
2. 回报失败事实、错误摘要、日志路径、处理动作
3. 回报以下处理选项：
   - 充值 / 恢复配额
   - 切换可用 provider
   - 修复权限或路径
4. **不得**让 design subagent 自行改走本地拼图、本地贴图、PIL 合成、手工排字顶替正式结果
5. 只有用户明确接受"临时示意图/降级草图"时，才允许走非正式链路，并且必须先说明这不是正式海报交付

---

## 完成后执行下一步

生图成功且通过视觉核验后，进入 **Step 8：设计审批**。
