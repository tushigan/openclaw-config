# Darwin 闭环报告：brand-poster-creator

时间：2026-06-09 00:11 CST
Skill：`/Users/a123/.openclaw/skills/brand-poster-creator`
分支：`auto-optimize/20260608-2342`
Baseline commit：`07c97b86`
Keep commit：`d6835de2`

## 结论

本轮 Darwin 闭环完成，结论为 **keep**。

本轮不是继续大改生图逻辑，而是补齐 Darwin full_test 发现的两个规整缺口：

- Step 2 显式写明：蒸馏卡存在但 `layout_analysis.elements` 为空、缺失或无效时，记录 `layout_status="empty_elements"` 并降级为自由构图，不得伪造坐标。
- `test-prompts.json` 新增第 4 条，覆盖固定版式坐标与自由构图 fallback 不能混用的关键场景。

## Full Test

测试集：`test-prompts.json` 4 条。

执行方式：

- baseline runner：不读取 skill，只按通用 agent 模拟 3 条原始 prompt，整体分 `5/10`。
- with-skill runner：读取当前 skill 后模拟执行，dim8 分 `8/10`。
- independent judge：对比 baseline / with-skill / 本轮补丁，结论 `keep`。

限制标记：

- `eval_mode=full_test`
- `no_image_render`：未真实调用生图模型生成图片。

## 评分

| 维度 | Before | After |
|---|---:|---:|
| Frontmatter | 9.0 | 9.0 |
| 工作流清晰度 | 8.8 | 9.1 |
| 失败模式编码 | 8.4 | 9.2 |
| 检查点设计 | 9.0 | 9.0 |
| 可执行具体性 | 8.5 | 9.0 |
| 资源整合度 | 9.0 | 9.0 |
| 整体架构 | 8.6 | 8.7 |
| 实测表现 | 8.0 | 8.8 |
| 反例与黑名单 | 9.0 | 9.1 |

总分：`84.5 -> 88.7`，增量 `+4.2`。

## 验证

- `python3 -m json.tool /Users/a123/.openclaw/skills/brand-poster-creator/test-prompts.json`
- `python3 -m unittest discover -s /Users/a123/.openclaw/skills/brand-poster-creator/tests`
- runtime 红灯扫描：空结果

验证结果：`21 tests OK`。

## Results 记录

已写入：

`/Users/a123/.codex/skills/darwin-skill/results.tsv`

新增记录：

- `07c97b86`：full_test 重新基线，`84.5`
- `d6835de2`：keep 本轮改进，`84.5 -> 88.7`
