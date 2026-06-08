# 提示词模板说明

## 最小输入字段

- `subject`: 主体是谁
- `action`: 主体要做什么
- `scene`: 场景 / 世界观
- `style`: 风格 / 气质
- `ratio`: 比例，默认 `16:9`
- `duration`: 时长，默认 `5`
- `quality_tier`: `draft` 或 `final`
- `storyboard_strategy`: 第一版固定 `auto_beats`
- `storyboard_panel_count_override`: 强制指定格数，可选
- `storyboard_beats_override`: 用户自定义关键帧提纲，可选
- `identity_strategy`: `reuse_exact` 或 `extend_from_source`
- `identity_anchor_rules`: 角色结构硬规则，可选
- `anchor_elements`: 空间锚点，可选
- `existing_references`: 已有参考图路径，可选
- `notes`: 额外说明，可选

## 原图模板关注点

- 世界观完整
- 风格稳定
- 主体与环境关系清晰
- 不要进入分镜思维

## 身份板模板关注点

- 大主视角 + 多辅助视角
- 锁脸、锁衣服、锁比例、锁手部、锁表情
- 浅底、少背景、不要叙事
- 如果有 `identity_source`，它才是结构最高依据
- `extend_from_source` 时，身份板只是延展展示板，不能改结构真相

## 故事板模板关注点

- 固定 `16:9`
- 固定黑白导演分镜感
- 按关键帧自动规划格数，不按一秒一格
- 简单故事优先少格数，复杂故事再增加格数
- 每格都要有明确镜头语言
- 空间锚点要持续出现
- 如果有 `identity_source`，角色优先服从它，不服从漂移版身份板
- 会把 `storyboard_beats` 直接写进 prompt

## 视频模板关注点

- 重申三张参考图各自职责
- 按本次关键帧顺序压缩成连贯短视频
- 不允许新世界、新角色设定、新风格冲突
- 如果有 `identity_source`，视频阶段仍以它为最高角色依据

## 默认模型档位

### draft
- 模型：`seedance2.0fast`
- 分辨率：`720p`

### final
- 模型：`seedance2.0_vip`
- 分辨率：优先 `1080p`
