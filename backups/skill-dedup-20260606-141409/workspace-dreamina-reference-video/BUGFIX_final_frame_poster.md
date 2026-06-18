# Bug 修复：final_frame_poster 污染问题

## 问题描述

**发现时间：** 2026-05-27 15:09

**问题现象：**
用户明确提供了尾帧定版图（`final_frame_poster`），但系统仍然会自己生成一个 `original.png`（风格与世界参考图）。这个自动生成的 `original.png` 可能与用户提供的定版图风格不一致，导致后续的 `storyboard` 参考了错误的风格，造成"污染"。

**用户反馈原文：**
> "我明明已经给了明确的尾帧定版图了，它还是会自己生成一个原图参考出来，这个环节是不是有一定的问题？这会对后续造成污染吧？"

## 根本原因

在 `workflow.py` 中：

1. **`build_prompts` 函数**（第638-771行）生成 `original` 的 prompt 时，完全没有考虑用户提供的 `final_frame_poster`，只是根据 brief 中的 subject、action、scene、style 自由生成。

2. **`build_gpt_image_jobs` 函数**（第1028-1075行）中，`original` 总是会被生成，没有任何逻辑判断是否应该复用 `final_frame_poster`。

3. **后续影响链：**
   - `storyboard` 生成时会参考 `original` 的风格（`--ref-style original`）
   - 如果 `original` 与 `final_frame_poster` 风格不一致，会导致故事板风格偏离
   - 最终视频也会受到影响

## 修复方案

### 1. 添加 `final_frame_poster` 到 `REFERENCE_FILE_MAP`

```python
REFERENCE_FILE_MAP = {
    "original": "original.png",
    "identity_source": "identity-source.png",
    "identity_board": "identity-board.png",
    "storyboard": "storyboard.png",
    "final_frame_poster": "final-frame-poster.png",  # 新增
}
```

### 2. 修改 `materialize_existing_references` 函数

在函数末尾添加逻辑：当用户提供了 `final_frame_poster` 且没有提供 `original` 时，自动将 `final_frame_poster` 复用为 `original`。

```python
# 如果提供了 final_frame_poster，且没有提供 original，则复用 final_frame_poster 作为 original
if "final_frame_poster" in resolved and "original" not in resolved:
    source_path = Path(resolved["final_frame_poster"])
    target = run_dir / "refs" / REFERENCE_FILE_MAP["original"]
    shutil.copyfile(source_path, target)
    resolved["original"] = str(target)
```

### 3. 更新文档

在 `SKILL.md` 中明确说明：

> **重要：当提供 `final_frame_poster` 时，系统会自动将其复用为 `original`（风格与世界参考），避免生成与定版不一致的原图。**

## 验证测试

创建测试 brief：
```json
{
  "existing_references": {
    "identity_source": "/path/to/identity.jpg",
    "final_frame_poster": "/path/to/final_poster.png"
  },
  "identity_strategy": "reuse_exact"
}
```

执行 `prepare` 命令后，验证：
1. `refs/final-frame-poster.png` 存在
2. `refs/original.png` 存在
3. 两个文件的 MD5 值相同

**测试结果：**
```bash
MD5 (original.png) = 08be0d52f60ca6b84deef37a465d69f2
MD5 (final-frame-poster.png) = 08be0d52f60ca6b84deef37a465d69f2
```

✅ 验证通过

## 影响范围

### 向后兼容性
- ✅ 不影响现有工作流
- ✅ 不提供 `final_frame_poster` 时，行为与之前完全一致
- ✅ 提供 `final_frame_poster` 时，自动优化，避免污染

### 使用场景
适用于以下场景：
1. 用户已有明确的品牌海报定版
2. 用户希望视频最终收束到特定的终帧构图
3. 用户希望整个视频的风格与终帧海报保持一致

### 不适用场景
如果用户希望：
1. 视频风格与终帧海报不同（例如：视频是动态风格，终帧是静态海报）
2. 需要单独生成一个不同风格的 `original`

在这些情况下，用户应该：
- 不提供 `final_frame_poster`，或
- 同时提供 `original` 和 `final_frame_poster`（此时不会自动复用）

## 相关文件

- `scripts/workflow.py` - 核心修复
- `SKILL.md` - 文档更新
- `tests/test_final_frame_poster_brief.json` - 测试用例

## 提交信息

```
修复 final_frame_poster 污染问题：自动复用为 original

- 当用户提供 final_frame_poster 时，自动将其复用为 original
- 避免生成与定版不一致的原图，防止风格污染
- 更新文档说明新的行为
- 添加测试验证
```
