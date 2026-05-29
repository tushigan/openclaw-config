# 视频提交优化设计

## 需求背景

### 需求 1：视频生成前的通道选择确认
**问题**：
- 当前直接使用 brief.json 中的 `quality_tier` 提交，用户无法在提交前选择
- 不同通道消耗的积分不同，用户无法理性选择

**需求**：
- 在提交视频生成前，询问用户选择通道
- 显示每个通道的特点和积分消耗
- 用户确认后再提交

### 需求 2：自动轮询生成进度
**问题**：
- 提交后 agent 没有反应，需要用户主动询问进度
- 用户体验差，需要手动检查

**需求**：
- 提交后自动轮询任务状态
- 定期汇报进度
- 生成完成后自动下载并发送给用户

## 技术调研

### 即梦通道配置

根据 dreamina CLI 文档和代码分析：

| 通道 | 模型版本 | 分辨率 | 速度 | 质量 | 适用场景 | 积分消耗（估算） |
|------|---------|--------|------|------|---------|-----------------|
| **draft** | seedance2.0fast | 720p | 快 | 中 | 打样、快速验证 | ~50-100 积分 |
| **standard** | seedance2.0 | 720p | 中 | 高 | 平衡选择、日常使用 | ~75-150 积分 |
| **fast_vip** | seedance2.0fast_vip | 720p | 快 | 高 | 快速高质量、时间紧迫 | ~100-200 积分 |
| **final** | seedance2.0_vip | 1080p | 慢 | 最高 | 正式交付、高质量 | ~150-300 积分 |

**注意**：积分消耗是估算值，实际消耗取决于视频时长、复杂度等因素。

### 即梦 CLI 轮询支持

即梦 CLI 已内置轮询功能：
```bash
dreamina multimodal2video --poll 600  # 轮询 600 秒（10 分钟）
```

- `--poll N`：提交后自动轮询 N 秒，每秒检查一次
- 返回值包含任务状态和结果

## 设计方案

### 方案 1：通道选择确认（推荐）

#### 实现位置
在 `submit-video` 步骤之前，增加一个 `confirm-submission` 步骤。

#### 工作流程
```
... → review-run → confirm-submission → submit-video → fetch-result
```

#### 实现细节

**1. 在 run_workflow.py 中增加 `confirm-submission` 命令**

```python
def confirm_submission(run_dir: Path, brief: dict[str, Any]) -> dict[str, Any]:
    """
    确认视频提交配置
    
    返回用户选择的配置
    """
    current_tier = brief.get("quality_tier", "draft")
    duration = brief.get("duration", 5)
    
    # 计算预估积分消耗
    estimated_credits = estimate_credit_cost(current_tier, duration)
    
    # 显示当前配置
    print("\n" + "=" * 60)
    print("视频生成配置确认")
    print("=" * 60)
    print(f"\n当前配置：")
    print(f"  - 质量档：{current_tier}")
    print(f"  - 时长：{duration} 秒")
    print(f"  - 预估积分消耗：{estimated_credits} 积分")
    print(f"\n可用通道：")
    
    # 显示所有通道选项
    options = get_quality_tier_options(duration)
    for i, option in enumerate(options, 1):
        print(f"\n{i}. {option['name']} ({option['tier']})")
        print(f"   - 模型：{option['model']}")
        print(f"   - 分辨率：{option['resolution']}")
        print(f"   - 速度：{option['speed']}")
        print(f"   - 质量：{option['quality']}")
        print(f"   - 预估积分：{option['estimated_credits']} 积分")
        print(f"   - 适用场景：{option['use_case']}")
    
    print("\n" + "=" * 60)
    
    # 返回配置，等待 agent 调用 AskUserQuestion 让用户选择
    return {
        "current_tier": current_tier,
        "options": options,
        "estimated_credits": estimated_credits
    }

def get_quality_tier_options(duration: int) -> list[dict]:
    """获取所有质量档选项"""
    base_cost_per_second = {
        "draft": 10,      # seedance2.0fast, 720p
        "standard": 15,   # seedance2.0, 720p
        "fast_vip": 20,   # seedance2.0fast_vip, 720p
        "final": 30,      # seedance2.0_vip, 1080p
    }
    
    options = [
        {
            "name": "快速打样",
            "tier": "draft",
            "model": "seedance2.0fast",
            "resolution": "720p",
            "speed": "快（~2-3分钟）",
            "quality": "中等",
            "estimated_credits": base_cost_per_second["draft"] * duration,
            "use_case": "快速验证创意、打样测试"
        },
        {
            "name": "标准质量",
            "tier": "standard",
            "model": "seedance2.0",
            "resolution": "720p",
            "speed": "中等（~5-8分钟）",
            "quality": "高",
            "estimated_credits": base_cost_per_second["standard"] * duration,
            "use_case": "平衡速度和质量"
        },
        {
            "name": "快速高质量",
            "tier": "fast_vip",
            "model": "seedance2.0fast_vip",
            "resolution": "720p",
            "speed": "快（~3-5分钟）",
            "quality": "高",
            "estimated_credits": base_cost_per_second["fast_vip"] * duration,
            "use_case": "需要快速出高质量结果"
        },
        {
            "name": "正式交付",
            "tier": "final",
            "model": "seedance2.0_vip",
            "resolution": "1080p",
            "speed": "慢（~10-15分钟）",
            "quality": "最高",
            "estimated_credits": base_cost_per_second["final"] * duration,
            "use_case": "正式交付、客户展示"
        }
    ]
    
    return options

def estimate_credit_cost(tier: str, duration: int) -> int:
    """估算积分消耗"""
    base_cost_per_second = {
        "draft": 10,
        "standard": 15,
        "fast_vip": 20,
        "final": 30,
    }
    return base_cost_per_second.get(tier, 10) * duration
```

**2. Agent 在 submit-video 前调用确认**

在 SKILL.md 中更新流程：

```markdown
### 步骤 7：confirm-submission - 确认视频提交配置

在提交视频生成前，让用户确认通道选择：

```bash
python3 scripts/run_workflow.py confirm-submission --run-dir /path/to/run
```

这会显示：
- 当前配置（质量档、时长、预估积分）
- 所有可用通道及其特点
- 每个通道的预估积分消耗

**Agent 必须使用 AskUserQuestion 让用户选择通道**，然后更新 brief.json 中的 `quality_tier`。

### 步骤 8：submit-video - 提交视频生成

确认通道后，提交视频生成任务。
```

**3. Agent 使用 AskUserQuestion 让用户选择**

Agent 在调用 `confirm-submission` 后，应该：

```python
# 1. 调用 confirm-submission 获取选项
result = exec("python3 scripts/run_workflow.py confirm-submission --run-dir ...")

# 2. 使用 AskUserQuestion 让用户选择
AskUserQuestion({
    "questions": [{
        "question": "请选择视频生成通道",
        "header": "通道选择",
        "options": [
            {
                "label": "快速打样 (draft)",
                "description": "seedance2.0fast, 720p, ~2-3分钟, 预估 50 积分, 适合快速验证"
            },
            {
                "label": "标准质量 (standard)",
                "description": "seedance2.0, 720p, ~5-8分钟, 预估 75 积分, 平衡速度和质量"
            },
            {
                "label": "快速高质量 (fast_vip)",
                "description": "seedance2.0fast_vip, 720p, ~3-5分钟, 预估 100 积分, 快速高质量"
            },
            {
                "label": "正式交付 (final)",
                "description": "seedance2.0_vip, 1080p, ~10-15分钟, 预估 150 积分, 最高质量"
            }
        ],
        "multiSelect": false
    }]
})

# 3. 根据用户选择更新 brief.json
# 4. 提交视频生成
```

### 方案 2：自动轮询机制（推荐）

#### 实现方式

**方式 1：使用即梦 CLI 内置轮询（推荐）**

修改 `build_dreamina_command()` 函数，添加 `--poll` 参数：

```python
def build_dreamina_command(
    run_dir: Path,
    brief: dict[str, Any],
    prompts: dict[str, str],
    project_dir: Path | None = None,
    recovery_actions: list[dict[str, Any]] | None = None,
    enable_polling: bool = True,  # 新增参数
    poll_timeout: int = 900,      # 默认轮询 15 分钟
) -> list[str]:
    settings = model_settings(brief)
    cmd = [
        DREAMINA_BIN,
        "multimodal2video",
    ]
    
    # ... 现有代码 ...
    
    # 添加轮询参数
    if enable_polling:
        cmd.extend(["--poll", str(poll_timeout)])
    
    return cmd
```

**优点**：
- 简单，利用 CLI 内置功能
- 自动轮询，无需额外代码
- 轮询结束后直接返回结果

**缺点**：
- 轮询期间 agent 阻塞，无法做其他事情
- 无法中途汇报进度

**方式 2：Agent 主动轮询（更灵活）**

在 SKILL.md 中增加轮询指导：

```markdown
### 步骤 8：submit-video - 提交视频生成

提交后会返回 submit_id，agent 应该：

1. **立即告知用户任务已提交**：
   ```
   视频生成任务已提交
   - submit_id: xxx
   - 预估时间：5-8 分钟
   - 我会每 30 秒检查一次进度
   ```

2. **定期轮询任务状态**：
   ```bash
   # 每 30 秒执行一次
   dreamina query_result --submit_id=xxx
   ```

3. **根据状态汇报**：
   - `pending`: "任务排队中..."
   - `processing`: "正在生成中...（已用时 X 分钟）"
   - `success`: "生成完成！正在下载..."
   - `failed`: "生成失败：{reason}"

4. **生成完成后自动下载**：
   ```bash
   python3 scripts/run_workflow.py fetch-result --run-dir /path/to/run --submit-id xxx
   ```

5. **下载完成后发送给用户**：
   - 复制视频到 feishu-deliver 目录
   - 使用 message 工具发送
```

**优点**：
- 灵活，可以中途汇报进度
- 不阻塞 agent，可以响应用户其他请求
- 更好的用户体验

**缺点**：
- 需要 agent 主动轮询
- 实现稍复杂

#### 推荐方案

**结合两种方式**：

1. **默认使用 CLI 内置轮询**（`--poll 900`），适合大多数情况
2. **在 AGENTS.md 中指导 agent**：如果用户在轮询期间发消息，agent 应该响应并说明"视频生成中，预计还需 X 分钟"

## 实施计划

### 阶段 1：通道选择确认（高优先级）

1. 在 `workflow.py` 中实现：
   - `get_quality_tier_options()` - 获取通道选项
   - `estimate_credit_cost()` - 估算积分消耗
   - `confirm_submission()` - 显示确认信息

2. 在 `run_workflow.py` 中增加 `confirm-submission` 命令

3. 更新 SKILL.md，在 submit-video 前增加确认步骤

4. 在 AGENTS.md 中指导 agent 使用 AskUserQuestion 让用户选择

### 阶段 2：自动轮询机制（高优先级）

1. 修改 `build_dreamina_command()`，添加 `--poll` 参数

2. 更新 SKILL.md，说明轮询行为

3. 在 AGENTS.md 中指导 agent：
   - 提交后告知用户预估时间
   - 轮询期间如何响应用户

### 阶段 3：进度汇报优化（中优先级）

1. 实现主动轮询逻辑（如果需要更细粒度的进度汇报）

2. 在 AGENTS.md 中增加进度汇报模板

## 注意事项

1. **积分消耗是估算值**：实际消耗可能因视频复杂度、时长等因素有所不同

2. **轮询超时设置**：
   - draft: 建议 300 秒（5 分钟）
   - standard: 建议 600 秒（10 分钟）
   - fast_vip: 建议 600 秒（10 分钟）
   - final: 建议 900 秒（15 分钟）

3. **用户体验**：
   - 提交前明确告知预估时间和积分消耗
   - 轮询期间保持响应，不要让用户感觉 agent "卡住了"
   - 生成完成后立即通知用户

4. **错误处理**：
   - 轮询超时：告知用户可以手动查询
   - 生成失败：显示失败原因，建议重试或调整参数
