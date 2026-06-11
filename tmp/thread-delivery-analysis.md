# 话题投送错位问题 - 方案对比分析

## 问题核心
OpenClaw 在 `deliveryContext` 中正确保存了 `threadId`，但 `message` 工具实际投送时没有使用这个参数。

## 三种修改方案对比

### 方案 1：修改 OpenClaw 源码中的 message 工具
**位置**：`/opt/homebrew/lib/node_modules/openclaw/dist/*.js`

**修改内容**：
- 让 `message` 工具在投送时自动从当前 session 的 `deliveryContext.threadId` 读取 threadId
- 如果存在 threadId，自动传递给飞书 API 的 `reply_in_thread` 参数

**优点**：
- ✅ 最根本的解决方案，从源头修复
- ✅ 对所有 agent 生效，无需逐个配置
- ✅ 不需要修改现有脚本和配置

**缺点**：
- ❌ **高风险**：修改 npm 包源码，下次 `npm update openclaw` 会被覆盖
- ❌ **无法验证**：源码是编译后的 JS，难以调试
- ❌ **维护困难**：每次更新 OpenClaw 都要重新打补丁
- ❌ **可能引入 bug**：不了解 OpenClaw 内部实现，可能破坏其他功能

**安全性评分**：⭐⭐ (2/5) - 高风险，不推荐

---

### 方案 2：修改 feishu-route-guard.py 增加 threadId 支持
**位置**：`/Users/a123/.openclaw/scripts/feishu-route-guard.py`

**修改内容**：
```python
def write_route_sidecar(
    media_path: Path,
    *,
    target: str,
    account_id: str = '',
    source: str = '',
    source_manifest: str = '',
    thread_id: str = '',  # 新增参数
) -> Path:
    sidecar = route_sidecar_path(media_path)
    payload = {
        'schema': 'openclaw.feishu.media-route.v1',
        'media': str(media_path),
        'delivery_target': {
            'target': normalize_feishu_target(target),
            'account_id': str(account_id or '').strip(),
            'target_source': str(source or '').strip() or 'route_sidecar',
        },
        'source_manifest': str(source_manifest or '').strip(),
    }
    if thread_id:
        payload['delivery_target']['threadId'] = thread_id  # 新增字段
    write_json(sidecar, payload)
    return sidecar
```

**优点**：
- ✅ 只修改本地脚本，不影响 OpenClaw 核心
- ✅ 可以逐步测试，验证效果
- ✅ 不会影响现有的私聊和普通群聊投送

**缺点**：
- ❌ **不完整**：只是记录了 threadId，但 message 工具仍然不会读取它
- ❌ 需要配合 OpenClaw 的后续更新才能真正生效
- ❌ 治标不治本

**安全性评分**：⭐⭐⭐ (3/5) - 安全但不完整

---

### 方案 3：在 AGENTS.md 中增加话题投送规则（推荐）
**位置**：`/Users/a123/.openclaw/workspace-design/AGENTS.md`

**修改内容**：
```markdown
### 2.1.1 话题群投送处理（新增）

**问题**：在话题群（threadSession）中直接使用 message 工具投送会导致消息发送到主群，而不是原话题。

**解决方案**：
1. **检测话题环境**：
   - 读取当前工作区的 `memory/YYYY-MM-DD-HHMM.md`
   - 查找 `Session Key` 字段
   - 如果包含 `:thread:omt_`，说明在话题群中

2. **话题群投送策略**：
   - ✅ **推荐**：把生成的图片路径回传给 `main` agent，由 `main` 统一投送
   - ✅ **备选**：等待 OpenClaw 修复 message 工具的 threadId 支持
   - ❌ **禁止**：直接在 design agent 中调用 message 工具投送（会发错位置）

3. **回传格式**：
```json
{
  "status": "success",
  "image_path": "/Users/a123/.openclaw/workspace-design/images/xxx.png",
  "delivery_note": "请在原话题中投送",
  "session_context": "thread"
}
```

**临时措施**（在 OpenClaw 修复前）：
- 所有话题群任务，图片生成完成后回传给 main，不自行投送
- 在日常记忆中标注当前 session 类型（thread/group/direct）
```

**优点**：
- ✅ **最安全**：不修改任何代码，只改执行规则
- ✅ **零风险**：不会影响现有功能
- ✅ **立即生效**：agent 下次启动就会遵守新规则
- ✅ **可回滚**：如果有问题，删除这段规则即可
- ✅ **符合架构**：main 本来就是统一投送的协调者

**缺点**：
- ⚠️ 需要一次额外的 agent 交互（design → main → user）
- ⚠️ 用户会多等几秒钟

**安全性评分**：⭐⭐⭐⭐⭐ (5/5) - 最安全，强烈推荐

---

## 最终推荐：方案 3 + 方案 2 组合

### 短期（立即实施）：方案 3
修改 `workspace-design/AGENTS.md`，让 design agent 在话题群中不直接投送，而是回传给 main。

### 中期（观察验证）：方案 2
修改 `feishu-route-guard.py`，为未来的 threadId 支持做准备。

### 长期（等待官方）：
向 OpenClaw 提 issue，请求在 message 工具中增加 threadId 参数支持。

---

## 实施步骤（方案 3）

1. **备份现有配置**
```bash
cp workspace-design/AGENTS.md workspace-design/AGENTS.md.backup-$(date +%Y%m%d)
```

2. **修改 AGENTS.md**
在 `## 2. 文件与交付` 章节的 `### 2.1 图片发送规范` 后面增加 `### 2.1.1 话题群投送处理`

3. **测试验证**
- 在话题群中测试图片生成任务
- 确认 design agent 回传路径而不是直接投送
- 确认 main agent 正确在话题中投送

4. **git 备份**
```bash
cd ~/.openclaw
git add workspace-design/AGENTS.md
git commit -m "修复：话题群图片投送错位问题 - design agent 回传路径由 main 统一投送"
git push
```

---

## 风险评估

| 方案 | 影响私聊 | 影响普通群聊 | 影响话题群 | 可回滚性 | 总体风险 |
|------|---------|-------------|-----------|---------|---------|
| 方案 1 | ⚠️ 可能 | ⚠️ 可能 | ✅ 修复 | ❌ 难 | 高 |
| 方案 2 | ✅ 不影响 | ✅ 不影响 | ⚠️ 部分 | ✅ 容易 | 低 |
| 方案 3 | ✅ 不影响 | ✅ 不影响 | ✅ 修复 | ✅ 容易 | 极低 |

---

## 附加观察

从 `delivery.json` 中看到 `target_candidates` 有多个候选目标，说明 OpenClaw 的路由决策机制可能还需要优化。建议后续深入分析 `target_conflict_reason: "conflict_in_recent_session_scan"` 的触发条件。
