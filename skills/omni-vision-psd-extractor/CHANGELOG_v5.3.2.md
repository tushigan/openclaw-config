# Changelog v5.3.2 - 智能兜底机制

## 发布日期
2026-06-16

## 版本号
v5.3.2-gpt-image2-gen-fallback

## 核心特性

### 🔥 智能兜底机制（Intelligent Fallback）

当 PSD skill 的自有 API 配置请求失败后，自动切换到海报 skill 的 `gpt-image2-gen` 共享配置，实现双保险生成。

#### 工作流程

```
┌─────────────────────────────────────┐
│  主 API 调用                        │
│  (OPENCLAW_BOUND_* 配置)           │
│  n.lconai.com/gpt-image-2-pro      │
└──────────┬──────────────────────────┘
           │
           ├─ ✅ 成功 → 继续后续流程
           │
           └─ ❌ 失败
              │
              ↓
┌─────────────────────────────────────┐
│  🔄 自动切换到兜底配置              │
│  gpt-image2-gen (海报 skill)       │
│  继承 workspace-design 配置         │
└──────────┬──────────────────────────┘
           │
           ├─ ✅ 兜底成功 → 继续后续流程
           │                记录 fallback_success: true
           │
           └─ ❌ 兜底失败 → 任务终止
                            记录双重失败原因
```

#### 关键特性

1. **参数一致性**
   - 使用相同的 prompt（提示词）
   - 保持相同的尺寸（suggested_size）
   - 传递相同的底图（--ref-base）

2. **状态追溯**
   ```json
   {
     "tasks": {
       "bg": {
         "fallback_used": "gpt-image2-gen",
         "fallback_success": true,
         "status": "completed"
       }
     }
   }
   ```

3. **日志可见性**
   ```
   ⚠️ Generation failed for 'bg' after primary API attempts: [错误]
   🔄 [兜底机制] 切换到 gpt-image2-gen 共享 skill（海报 skill 配置）
   📍 找到 gpt-image2-gen: /Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py
   🚀 [兜底] 执行 gpt-image2-gen 调用...
   ✅ [兜底成功] gpt-image2-gen 生成成功
   ```

## 技术实现

### 修改的文件

1. **scripts/extract_layers.py** (核心修改)
   - 位置：第 723-731 行（原失败处理逻辑）
   - 新增：兜底调用逻辑（约 80 行代码）
   - 功能：检测失败 → 查找 gpt-image2-gen → 执行兜底 → 记录结果

2. **SKILL.md** (文档更新)
   - 版本号：5.3.1 → 5.3.2
   - 描述：新增智能兜底机制说明
   - 新增：兜底机制工作原理章节

3. **TEST_FALLBACK.md** (新增测试文档)
   - 功能说明
   - 兜底流程图
   - 测试方法
   - 失败场景处理

4. **CHANGELOG_v5.3.2.md** (本文件)
   - 变更记录
   - 技术细节
   - 使用指南

### 代码逻辑

```python
if not generation_success:
    # 1. 记录主 API 失败
    safe_log(f"⚠️ Generation failed for '{key}': {error_msg}")
    
    # 2. 查找 gpt-image2-gen
    gpt_image2_gen_path = resolve_gpt_image_generator()
    
    if gpt_image2_gen_path and gpt_image2_gen_path.exists():
        # 3. 准备兜底参数（与主 API 相同）
        fallback_args = [
            sys.executable,
            str(gpt_image2_gen_path),
            "--prompt-file", str(prompt_file),
            "-s", suggested_size,
            "-o", str(raw_out),
            "--ref-base", source_path
        ]
        
        # 4. 执行兜底调用
        fallback_res = run_with_spinner(fallback_args, env=env)
        
        # 5. 检查兜底结果
        if fallback_res.returncode == 0 and raw_out.exists():
            generation_success = True  # 兜底成功，继续流程
            # 记录状态
            task_state["fallback_used"] = "gpt-image2-gen"
            task_state["fallback_success"] = True
        else:
            # 记录双重失败
            task_state["status"] = "failed"
            task_state["error"] = f"Primary: {error_msg}; Fallback: {fallback_error}"
            return False
```

## API 配置对比

### 主 API 配置（PSD Skill 独立配置）
```bash
# /Users/a123/.openclaw/skills/omni-vision-psd-extractor/.env
OPENCLAW_BOUND_API_KEY=sk-xxx
OPENCLAW_BOUND_BASE_URL=https://n.lconai.com/
OPENCLAW_BOUND_MODEL_ID=gpt-image-2-pro
OPENCLAW_BOUND_PROTOCOL=openai
```

### 兜底配置（继承海报 Skill）
```bash
# /Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/
# 继承该 skill 的完整配置
# 包括：
# - API endpoints (n.lconai.com, direct.aixor.org)
# - API keys (BANANA_API_KEY, BANANA_API_KEY_AIXOR)
# - Failover 机制
# - 模型自动选择（gpt-image-2 / gpt-image-2-pro）
```

## 使用场景

### 场景 1：主 API 配额耗尽
```
主 API: 401 Unauthorized (配额不足)
    ↓
兜底: 切换到 gpt-image2-gen（使用不同的 API key）
    ↓
结果: ✅ 任务成功完成
```

### 场景 2：主 API 端点故障
```
主 API: Connection timeout (n.lconai.com 不可达)
    ↓
兜底: gpt-image2-gen 自动 failover 到 direct.aixor.org
    ↓
结果: ✅ 任务成功完成
```

### 场景 3：双重失败
```
主 API: 403 Forbidden
    ↓
兜底: 429 Rate Limit Exceeded
    ↓
结果: ❌ 记录双重失败，任务终止
状态: {
  "error": "Primary: 403 Forbidden; Fallback: 429 Rate Limit"
}
```

## 性能影响

### 成功路径（主 API 正常）
- **延迟**：无变化
- **请求数**：无变化
- **成本**：无变化

### 兜底路径（主 API 失败）
- **额外延迟**：+10-30 秒（1 次兜底请求）
- **额外请求**：+1 次 API 调用
- **额外成本**：1 次图像生成费用

### 成功率提升
- **单一 API**：假设成功率 95%
- **双保险**：成功率 ~99.75%（95% + 5% × 95%）
- **改善**：失败率从 5% 降至 0.25%（降低 20 倍）

## 兼容性

### 向后兼容
- ✅ 保持所有现有参数不变
- ✅ 不影响主 API 的正常工作
- ✅ 兜底机制自动生效，无需配置

### 依赖要求
- ✅ 需要 `gpt-image2-gen` skill 存在于 workspace-design
- ✅ 需要 `runtime_config.py` 中的 `resolve_gpt_image_generator()` 函数
- ✅ 环境变量继承自 `gpt-image2-gen` 的配置

## 测试建议

### 自动化测试
```bash
# 临时破坏主配置以触发兜底
export OPENCLAW_BOUND_API_KEY="invalid-key-for-testing"

# 运行 PSD skill
python3 scripts/run_omni_delivery.py \
  --source "/path/to/test.png" \
  --target-size "2K" \
  --feishu-user-id "ou_xxx"

# 检查是否自动兜底成功
cat outputs/*/state.json | jq '.tasks | .[] | .fallback_success'
```

### 监控指标
- `fallback_used` 字段：兜底使用次数
- `fallback_success` 字段：兜底成功率
- 主 API 失败率 vs 总体失败率

## 后续优化方向

### 短期
1. ⏰ **超时配置**：为兜底调用设置独立超时
2. 📊 **统计上报**：收集兜底使用率和成功率数据
3. 🔔 **告警机制**：主 API 失败率超过阈值时告警

### 中期
4. 🔄 **多级兜底**：gpt-image2-gen 失败后再兜底到其他 provider
5. 🧠 **智能路由**：根据历史成功率自动选择最佳 endpoint
6. 💰 **成本优化**：根据任务优先级选择不同兜底策略

### 长期
7. 🌐 **全局兜底池**：建立跨 skill 的统一兜底资源池
8. 📈 **预测性切换**：在检测到 API 不稳定时提前切换
9. 🤖 **自适应策略**：根据时间段、负载自动调整兜底策略

## 发布清单

- [x] 修改 `extract_layers.py` 添加兜底逻辑
- [x] 更新 `SKILL.md` 版本和说明
- [x] 创建 `TEST_FALLBACK.md` 测试文档
- [x] 创建 `CHANGELOG_v5.3.2.md` 变更日志
- [ ] 更新 `.gitignore`（如需要）
- [ ] 提交到 git 仓库
- [ ] 通知相关用户和开发者
- [ ] 监控兜底机制运行情况

## 参考文档

- [SKILL.md](SKILL.md) - 完整功能说明
- [TEST_FALLBACK.md](TEST_FALLBACK.md) - 测试方法和场景
- [runtime_config.py](scripts/runtime_config.py) - 配置解析函数
- [extract_layers.py](scripts/extract_layers.py) - 核心实现逻辑

---

**贡献者**: Claude (Kiro AI Assistant)  
**审核状态**: 待测试  
**部署状态**: 开发完成，待生产验证
