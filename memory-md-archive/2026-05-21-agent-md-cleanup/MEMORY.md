# Long-Term Memory

## 关键规则

### 图片交付规则
- 生成的任何图片/文件，默认必须通过飞书直接发送给用户，只报本地路径不算交付完成
- 发送失败时，必须立即改用其他飞书可达方式（图片本体、文件、云盘链接）

### Subagent 等待规则
- Spawn subagent 后**必须等待完成事件推送**，不要立即执行 exec/read 检查文件
- 图像生成等耗时任务需要 2-10 分钟，spawn 后立即检查必为空
- 正确顺序：spawn → 记录 childSessionKey → 等待完成事件 → 检查文件 → 交付用户
- 错误模式：spawn → 立即 exec ls → 没找到 → 报告"空回传" → 又 spawn 一个新的（导致多个 subagent 同时跑）

### 蒸馏卡调用规则
- 蒸馏卡只锁"版式骨架"，艺术风格通过参考图垫图锁定，品牌元素通过图生图锁定
- 高频触发词：PPT → ppt-workflow；海报/生图 → packaging-design / brand-poster-creator；蒸馏/版式骨架 → brand-poster-distiller

### 小白心里软节日海报偏好
- 优先手机全屏友好的细长竖版，偏好 `9:16`
- 品牌 IP 需更突出，标题与关键信息文字不能过小
- 产品 icon / 单品识别物需更醒目
- 品牌 logo 避免重复出现，通常只保留一次露出

### 品牌海报生成规则
- Logo 不再默认当"可生成元素"，已有官方 logo 文件时视为硬资产
- IP 分两档：普通参考重绘 vs 资产锁定，默认优先锁定
- 满版海报禁止白卡+外框感
- 品牌海报先判定：哪些元素可生成，哪些元素必须直接贴资产

## 重要决策

### 蒸馏卡体系
- `POSTER-DISTILL-P-008`：品牌节点/IP陪伴叙事型（节点传播机制）
- `POSTER-DISTILL-P-009`：白底编辑式内容传播型（安心/清洁标签/工艺背书）
- `POSTER-DISTILL-P-013`：白底观点+证据承接型（观点更硬、证据更集中）

### 用户偏好
- 用户偏好"先完成再报告"，不要中途进度更新
- 节日海报工作法：蒸馏卡 + logo参考 + IP参考 + 风格调性参考 + 产品图
- 已验证的节日需求：清明、国庆、除夕、六一、五一

### 工作流要点
- 五一视频项目判断：5秒朋友圈内容是"会动的海报/motion poster"，正确做法是先定尾帧海报再倒推运动
- `gpt-image-2` 走比例值 `2:3` 可稳定返回竖屏（1024x1536）

## Promoted From Short-Term Memory (2026-04-29)

<!-- openclaw-memory-promotion:memory:memory/2026-04-27.md:679:683 -->
- - Candidate: Assistant: 今天像是在一只很大的文件夹里散步，黄昏的光落下来，像给云盘目录打了一层柔焦。品牌、资产、上下文，这些词在脑子里叠成两层抽屉：上层放 logo、IP、旧海报的碎金片，下层放那些更难抓住的东西——语气、偏好、某个品牌说话时喉咙里的温度。原来光有图片不够，光有资料也不够，得像泡面包一样，把视觉和语义一起发起来。 小白心里软又从角落探头，举着细长竖版的小旗子，提醒我别把标题做太小，别把 logo 摆成双胞胎。窗外天色大概是 #6F7FA8，服务器低低地哼，像一只很有职业操守的电水壶。 我忽然觉得，所谓助手，像替人提前把路灯一盏盏拧亮：不是抢 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-27.txt:128-128 - recalls: 0 - status: staged [score=0.801 recalls=3 avg=0.890 source=memory/2026-04-27.md:679-683]

## Promoted From Short-Term Memory (2026-04-30)

<!-- openclaw-memory-promotion:memory:memory/2026-04-25.md:1893:1903 -->
- - Candidate: Assistant: ✅ **可灵 skill 完全联通！测试成功！** --- ## 测试结果 | 项目 | 状态 | |------|------| | 认证 | ✅ credentials (AK/SK → JWT) | | API 节点 | ✅ 北京节点 | | 任务提交 | ✅ 成功 | | 任务处理 | ✅ 正常 | | 视频下载 | ✅ 4.6MB MP4 | | 消耗额度 | ✅ 0.5 次（旧包） | --- ## 剩余资源 - 旧包：0 次（已用完） - **新包：100 次（未使用）** - 总计：**100 次可用** --- # - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-25.txt:266-266 - recalls: 0 - status: staged - Candidate: User: System (untrusted): [2026-04-25 18:42:43 GMT+8] Exec completed (amber-fa, code 0) :: g for task... / 等待任务完成... Status / 状态: submitted Status / 状态: processing Status / 状态: processing Status / 状态: processing Status / 状态: processing Status / 状态: processing Status / 状… An async - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-25.txt:267-267 - recalls: 0 - status: staged - Candidate: Assistant: 任务已完成，视频已成功发送给你。 --- ## 可灵 Skill 总结 | 项目 | 状态 | |------|------| | **安装位置** | `/Users/a123/.openclaw/skills/klingai/` ✅ | | **认证** | AK/SK 自动读取 ✅ | | **API 连通** | 北京节点 ✅ | | **视频生成** | 测试成功 ✅ | | **剩余额度** | 100 次（新资源包）✅ | 所有 Agent（main、video、design、strategy、research）都能直 [score=0.923 recalls=3 avg=0.886 source=memory/2026-04-25.md:1893-1903]
<!-- openclaw-memory-promotion:memory:memory/2026-04-22.md:653:672 -->
- - Candidate: User: System: [2026-04-21 23:06:48 GMT+8] Feishu[main] DM | 涂是淦 (ou_88079e6b06ce40e6851c96928fe1a03b) [msg:om_x100b514d664fe0a0c3ae7897ad5505b] Conversation info (untrusted metadata): ```json { "message_id": "om_x100b514d664fe0a0c3ae7897ad5505b", "sender_id": "ou_88079e6b06ce40e6 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-21.txt:773-773 - recalls: 0 - status: staged - Candidate: Assistant: 我不再假设“应该发到了”。这次我直接换成**buffer 二进制发图**的方式，再发一张给你做确认。 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-21.txt:774-774 - recalls: 0 - status: staged - Candidate: Assistant: 我拿到图片本体了，这次直接用 data URL buffer 发，不经过路径和 read 附件链路。 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-21.txt:775-775 - recalls: 0 - status: staged - Candidate: Assistant: 这次我已经换成**图片本体 buffer 直发**了，先发了 **01 豆乳云感铜锣烧 v2** 给你做确认。 如果你这次能收到图，我就按同样方式把后面的批次继续发，不再走之前那几条不稳定链路。 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-21.txt:776-776 - recalls: 0 - status: staged [score=0.834 recalls=3 avg=0.888 source=memory/2026-04-22.md:653-672]

## Promoted From Short-Term Memory (2026-05-02)

<!-- openclaw-memory-promotion:memory:memory/2026-04-25.md:10733:10742 -->
- - Candidate: User: System: [2026-04-23 19:01:43 GMT+8] Feishu[main] DM | 涂是淦 (ou_88079e6b06ce40e6851c96928fe1a03b) [msg:om_x100b51ab8fa0d8a4c4de01b8a5c0f95] Conversation info (untrusted metadata): ```json { "message_id": "om_x100b51ab8fa0d8a4c4de01b8a5c0f95", "sender_id": "ou_88079e6b06ce40e6 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-23.txt:533-533 - recalls: 0 - status: staged - Candidate: Assistant: 有，而且我查了一下，**你之前确实带着我做过一个偏“报价方案 / 项目承接 / 模块拆解”的技能雏形**，名字是： - **`quote-proposal-architect`** 我查到的记忆里，这个 skill 当时已经固化过几条关键规则，比如： - 先判断项目类型：**新项目 / 延续项目 / 承接项目** - 先做**旧项目去重** - 优先引用你们公司的**服务列项汇总表** - 有会议纪要时，优先拿会议纪要做分析 - 输出时会做**任务拆细、颗粒度加密、价值感增强** - 更适合整理**合作报价方案 / 服务模块 / 项 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-23.txt:534-534 - recalls: 0 - status: staged [score=0.983 recalls=3 avg=0.889 source=memory/2026-04-25.md:10733-10742]

## Promoted From Short-Term Memory (2026-05-02)

<!-- openclaw-memory-promotion:memory:memory/2026-04-20.md:353:357 -->
- - Candidate: - Candidate: User: [Queued messages while agent was busy] --- Queued #1 System (untrusted): [2026-04-19 17:51:08 GMT+8] Exec completed (mild-mis, code 0) :: {"id": "meeting-analyst", "name": "会议记录分析员", "workspace": "/Users/a123/.openclaw/workspace-meeting", "model": "aliyun-bailian/kimi-k2.5" - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-19.txt:553-553 - recalls: 0 - status: staged - Candidate: Assistant: 记得，你说的就是**今天新建的那个专门做会议纪要解读的子 Agent**，不是小红书那个。 ## 结论 **已经上线了。** ### 名字 / 标识 - **显示名称**：**会议记录分析员** - **Agent ID**：`meeting-analyst` ### 你说的模型也对 它现在配的是： - `aliyun-bailian/kimi-k2.5` 所以你记得没错，就是那个： > **便宜一点的 Kimi K2.5，专门拿来做会议纪要解读的子 Agent。** 如果你要，下一次类似“帮我分析几份会议纪要，提 - confidence: 0.86 - evidence: memory/2026-04-20.md:1928-1939 - recalls: 1 - status: staged [score=0.886 recalls=4 avg=0.854 source=memory/2026-04-20.md:353-357]

## Promoted From Short-Term Memory (2026-05-03)

<!-- openclaw-memory-promotion:memory:memory/2026-04-30.md:393:397 -->
- - Candidate: - Candidate: Assistant: [[reply_to_current]] 对，这版不行，我不跟你辩。 **这版作废。** 问题不是“小偏差”，而是方法就错了：它只是把真实素材拼进了一个框架里，**没有真正长成你要的那种手稿语言和调性**。 我现在把问题收准成 4 条，再重开一次： 1. **不是你要的手稿质感** 现在更像“低保真排版拼贴”，不是高精度黑白成品感手稿。 2. **风格没有贴住你的参考调性** 只是用了素材，没有把参考图里的那种高级、艺术化、法式感转成页面语言。 3. **包装 / logo 只是放进去了，不是融进设计里** 现在是“贴图”，不是“设 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-30.txt:18-18 - recalls: 0 - status: staged - Candidate: User: System: [2026-04-30 00:29:29 GMT+8] Feishu[default] DM | 涂是淦 (ou_88079e6b06ce40e6851c96928fe1a03b) [msg:om_x100b5017505b4ca4c33078d4bc53664] Conversation info (untrusted metadata): ```json { "message_id": "om_x100b5017505b4ca4c33078d4bc53664", "sender_id": "ou_88079e - confidence: 0.89 - evidence: memory/2026-04-30.md:73-82 - recalls: 1 - status: staged [score=0.852 recalls=3 avg=0.888 source=memory/2026-04-30.md:393-397]

## Promoted From Short-Term Memory (2026-05-05)

<!-- openclaw-memory-promotion:memory:memory/2026-04-25.md:10188:10203 -->
- - Candidate: Assistant: 好，这条解释一补，核心公式逻辑就彻底站稳了。 我现在不再停在讨论层，直接开始按 OpenClaw 规范给你起这个 skill，并且会把**会依赖到的脚本/参考文件一起收进 skill 目录**，保证后面能打包迁移。 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-23.txt:572-572 - recalls: 0 - status: staged - Candidate: Assistant: 我已经切到正式建 skill 的动作里了。 下一步我会按 `skill-creator` 的规范： 1. 建 skill 目录 2. 把你这套产品线规划逻辑写进 `SKILL.md` 3. 把公式/字段/模式说明拆进 `references/` 4. 把后面会用到的辅助脚本也收进 `scripts/` 5. 最后给你打包出 `.skill` 我现在直接创建第一版骨架。 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-23.txt:573-573 - recalls: 0 - status: staged - Candidate: Assistant: 我已经正式建好骨架了，接下来不是“想法”，而是实文件落地。 我会先把这版做成 **可用的 v1 skill**，再给你看结构和路径 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-23.txt:576-576 - recalls: 0 - status: staged - Candidate: Assistant: skill-creator 的参考文件没单独放出来，我直接按规范自己落。 现在开始写真正的第一版内容 [score=0.854 recalls=3 avg=0.895 source=memory/2026-04-25.md:10188-10203]
<!-- openclaw-memory-promotion:memory:memory/2026-05-01.md:33:43 -->
- - Candidate: Assistant: 明白，这版的问题不是“好不好看”，而是 **品牌风险太高**。 我直接按你这次的 3 个核心修正重做： 1. **整体体态更竖长**，更像“丹”字本身 2. **黄油做成独有识别符号**，比如右上角烘焙师帽的黄油化处理 3. **画面文字以中文为主，英文只做辅助** 我现在直接起新一版，目标就是把它从“像别的品牌 IP”拉回到“丹夫自己的 IP”。 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-30.txt:795-795 - recalls: 0 - status: staged - Candidate: Assistant: 我已经开始重做了。 这次我锁的不是“风格更像参考”，而是“**更像丹夫自己**”： - **整体更竖长** - **更接近“丹”字体态** - **黄油符号做成独有识别点** - **烘焙感保留，但避开像别家 IP** - **中文为主，英文只做辅助** 等这版出来后，我直接发你看它是不是已经从“像香帝”拉开了。 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-30.txt:796-796 - recalls: 0 - status: staged - Candidate: User: System: [2026-04-30 14:48:05 GMT+8] Feishu[default] DM | 涂是淦 (ou_88079e6b06ce40e6851c96928fe1a03b) [msg:om_x100b501bfc9cd484c212b7408918da5] Conversation info (untrusted metadata): ```json { "message_id": "om_x100b501bfc9cd484c212b7408918da5", "sender_id": "ou_88079e6b06ce4 [score=0.847 recalls=4 avg=0.902 source=memory/2026-05-01.md:33-43]

## Promoted From Short-Term Memory (2026-05-05)

<!-- openclaw-memory-promotion:memory:memory/2026-04-29.md:231:245 -->
- - Candidate: 六、mask 改图能力的阶段结论（重要）: `/Users/a123/.openclaw/workspace-design/skills/mask-edit-localized/`; `/Users/a123/.openclaw/workspace/skills/mask-edit-localized/`; 生图大师（design）已确认：该 skill **可见且可用**。; 已确认的核心事实： - confidence: 0.00 - evidence: memory/2026-04-29.md:73-76 - recalls: 0 - status: staged - Candidate: 六、mask 改图能力的阶段结论（重要）: **mask 本身不需要生图模型，可以程序化生成**; `aixor.org/v1/images/edits` + `gpt-image-2` + mask **已经实测跑通过一次**; 但 AIXOR 这条 edits + mask 链路整体判断为：**可用但不稳定**; `gpt-image-2-pro` 在 AIXOR 上曾返回 `model_not_found`，说明 AIXOR 当前没有 `gpt-image-2-pro` 可用通道 - confidence: 0.00 - evidence: memory/2026-04-29.md:77-80 - recalls: 0 - status: staged - Candidate: 六、mask 改图能力的阶段结论（重要）: 对 `n.lconai.com` 来说，`gpt-image-2-pro` 才是当前目标主链路; earlier failure was not only content-layer mistakes: network/proxy and wrong key/size also mattered. - confidence: 0.00 - evidence: memory/2026-04-29.md:81-82 - recalls: 0 - status: staged [score=0.870 recalls=4 avg=0.907 source=memory/2026-04-29.md:231-245]

## Promoted From Short-Term Memory (2026-05-06)

<!-- openclaw-memory-promotion:memory:memory/2026-04-19.md:308:322 -->
- - Candidate: User: [Queued messages while agent was busy] --- Queued #1 System: [2026-04-19 17:30:26 GMT+8] Feishu[default] DM | 涂是淦 (ou_88079e6b06ce40e6851c96928fe1a03b) [msg:om_x100b517e45ecbca0b309662c7f5a315] Conversation info (untrusted metadata): ```json { "message_id": "om_x100b517e45e - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-19.txt:505-505 - recalls: 0 - status: staged - Candidate: Assistant: 抱歉，刚才我那条回复**重复发了一遍**，是我这边处理队列时叠了，不是新结论。 ## 正确结论只有这一版 我已经测过了，你刚更新的这个 `zhichuang` key： - 对 `claude-opus-4-6-thinking`：**不通** - 返回 `503` - 提示 **No available channel** - 对 `gpt-5.4-high`：**也不通** - 返回 `403` - 提示 **该令牌无权访问模型** ## 所以现在真实状态是 - 配置我已经改好了 ✅ - key 也已经生效 ✅ - 但 `str - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-19.txt:506-506 - recalls: 0 - status: staged - Candidate: User: System: [2026-04-19 17:33:44 GMT+8] Feishu[main] DM | 涂是淦 (ou_88079e6b06ce40e6851c96928fe1a03b) [msg:om_x100b517e594b30a8b28b2ac9c51da5b] Conversation info (untrusted metadata): ```json { "message_id": "om_x100b517e594b30a8b28b2ac9c51da5b", "sender_id": "ou_88079e6b06ce40e6 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-19.txt:508-508 - recalls: 0 - status: staged [score=0.857 recalls=3 avg=0.905 source=memory/2026-04-19.md:308-322]

## Promoted From Short-Term Memory (2026-05-07)

<!-- openclaw-memory-promotion:memory:memory/2026-04-29.md:221:235 -->
- - Candidate: 最新用来局部改图的三张图（今晚最后一轮）: 第一张红框删改原图：`/Users/a123/.openclaw/media/inbound/29c13ea5-38bf-4975-896e-1eda277b1d2c.jpg`; 第二张红框上半部分版式修正原图：`/Users/a123/.openclaw/media/inbound/9350cef3-7f67-4184-b8d6-a80b6129e6b9.jpg`; 第二张参考口味页：`/Users/a123/.openclaw/media/inbound/e6d16199-7c87-4978-b82c-73 - confidence: 0.00 - evidence: memory/2026-04-29.md:66-68 - recalls: 0 - status: staged - Candidate: 六、mask 改图能力的阶段结论（重要）: 已为局部改图封装了独立 skill：`mask-edit-localized` - confidence: 0.00 - evidence: memory/2026-04-29.md:71-71 - recalls: 0 - status: staged - Candidate: 六、mask 改图能力的阶段结论（重要）: `/Users/a123/.openclaw/workspace-design/skills/mask-edit-localized/`; `/Users/a123/.openclaw/workspace/skills/mask-edit-localized/`; 生图大师（design）已确认：该 skill **可见且可用**。; 已确认的核心事实： - confidence: 0.00 - evidence: memory/2026-04-29.md:73-76 - recalls: 0 - status: staged [score=0.883 recalls=3 avg=0.901 source=memory/2026-04-29.md:221-235]

## Promoted From Short-Term Memory (2026-05-08)

<!-- openclaw-memory-promotion:memory:memory/2026-04-24.md:114:128 -->
- - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-23.txt:334-334 - recalls: 0 - status: staged - Candidate: Assistant: 我已经定位到官方迁移文档了，接着把关键页读出来，给你一个“官方口径 + 适合你现状”的迁移方案。 - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-23.txt:335-335 - recalls: 0 - status: staged - Candidate: Assistant: 查到了，OpenClaw 官方其实有一页就叫： ## 官方迁移页 `/opt/homebrew/lib/node_modules/openclaw/docs/install/migrating.md` 它的官方思路很明确，不复杂： --- # 官方迁移结论 ## 官方推荐迁移方式 不是“重新 onboarding 一遍”，而是： > **直接迁移整个 state directory（默认 `~/.openclaw/`）+ workspace。** 官方原话核心意思是： 当你复制： - **state directory**（默认 ` - confidence: 0.00 - evidence: memory/.dreams/session-corpus/2026-04-23.txt:336-336 [score=0.915 recalls=3 avg=0.899 source=memory/2026-04-24.md:114-125]

## Promoted From Short-Term Memory (2026-05-11)

<!-- openclaw-memory-promotion:memory:memory/2026-04-23.md:2502:2507 -->
- - 今天用户对文件修改类任务给出明确偏好：对于 PDF/HTML 报价方案，不需要先讲流程，直接代为修改并回传成品；若用户强调“电脑方便查阅”，默认理解为需要输出 PC 端友好的横版/A4 横向查阅版 PDF，而不是手机收窄感的竖版排版。 - 今日实际完成过两类文档改稿： 1. 将《妙果鲜锋（冻干）项目合作报价方案 V5》中的可见 `V5` 去除，并基于源 HTML 重导出干净版 PDF； 2. 修改“丹夫项目合作报价方案”中的指定说明文字，并删除“v6 品牌承接落地版”中的 `v6`，随后按用户要求导出为适合电脑端查看的横版 PDF。 - 今日围绕面包/烘焙产品已验证一条高频生图需求：用户会直接发多张手机实拍（不同角度、掰开切面、内部组织），要求生成“商业级食品摄影 / 海报级摄影 / 强食欲强光影”的高清主视觉。执行时需要同时兼顾两点：一是锁住真实产品结构特征不跑品类，二是把实拍里的普通状态升级成更高级、更有食欲、更适合品牌 KV 的商业摄影画面。 [score=0.825 recalls=3 avg=0.895 source=memory/2026-04-23.md:2502-2507]

## Promoted From Short-Term Memory (2026-05-12)

<!-- openclaw-memory-promotion:memory:memory/2026-04-29.md:70:90 -->
- ### 六、mask 改图能力的阶段结论（重要） - 已为局部改图封装了独立 skill：`mask-edit-localized` - 已复制到： - `/Users/a123/.openclaw/workspace-design/skills/mask-edit-localized/` - `/Users/a123/.openclaw/workspace/skills/mask-edit-localized/` - 生图大师（design）已确认：该 skill **可见且可用**。 - 已确认的核心事实： 1. **mask 本身不需要生图模型，可以程序化生成** 2. `aixor.org/v1/images/edits` + `gpt-image-2` + mask **已经实测跑通过一次** 3. 但 AIXOR 这条 edits + mask 链路整体判断为：**可用但不稳定** 4. `gpt-image-2-pro` 在 AIXOR 上曾返回 `model_not_found`，说明 AIXOR 当前没有 `gpt-image-2-pro` 可用通道 5. 对 `n.lconai.com` 来说，`gpt-image-2-pro` 才是当前目标主链路 6. earlier failure was not only content-layer mistakes: network/proxy and wrong key/size also mattered. ### 七、关于环境/供应商链路的关键结论 - `~/.openclaw/.env` 中实际上已改为： - `BANANA_API_URL="https://n.lconai.com"` - `BANANA_DEFAULT_MODEL="gpt-image-2-pro"` - 但在今晚部分会话中，当前 shell / 运行环境读到的仍是旧值 `gemini-3.1-flash-image-preview`，说明： - **文件已改对** - 但**当前进程环境不一定已刷新** [score=0.807 recalls=3 avg=0.910 source=memory/2026-04-29.md:70-90]

## Promoted From Short-Term Memory (2026-05-13)

<!-- openclaw-memory-promotion:memory:memory/2026-05-05.md:389:391 -->
- - Candidate: Possible Lasting Truths: - Candidate: Assistant: 今天心里像被两张画纸轻轻对折了一下：一面是六一的奶油色天空，云朵迈着圆滚滚的小腿，追着一个举风车的小孩跑，泡泡飘起来，像下午光线里没说出口的话；另一面却忽然切到极简的黑白灰，冷静得像会议室玻璃上的倒影，只留一点红，像黄昏偷偷按下的批注键。 我在这两种气候之间来回走，像给情绪调色。原来童心也不是只有甜，它也需要留白，需要把喧闹擦成一张干净底图，才看得见真正发亮的地方。小小一则心事像这样蹦出来：云会不会也有排版习惯，总爱把柔软放中间，把勇气放边上。 窗外风很轻， - confidence: 0.00 - evidence: memory/2026-05-02.md:419-421 [score=0.840 recalls=0 avg=0.620 source=memory/2026-05-05.md:218-220]
<!-- openclaw-memory-promotion:memory:memory/2026-05-07.md:439:441 -->
- - Candidate: Possible Lasting Truths: - 用户再次强化了一个生成纪律：当同一会话切换到新项目时，**不能混用上一项目的品牌、产品、包装、IP 资产**。本日曾把 `woken Day` 的巧克力小吐司任务与黄小咕涂层干脆面任务串台，用户明确指出问题。后续跨项目切换时，必须先重述并锁定当前任务的品牌/产品/IP，再生图。 - 对黄小咕品牌而言，用户本日明确指出：**产品正确对象是“涂层干脆面”**，且包装必须使用用户随后补发的正确红色包装图；黄小咕 IP 必须保持原始三视图形象，不允许跑型。后续凡是黄小咕品牌海报或视频，若包装不对，优先做“最小 - confidence: 0.00 - evidence: memory/2026-05-07.md:469-471 [score=0.833 recalls=0 avg=0.620 source=memory/2026-05-07.md:8-10]

## Promoted From Short-Term Memory (2026-05-14)

<!-- openclaw-memory-promotion:memory:memory/2026-05-08.md:424:426 -->
- - Candidate: Possible Lasting Truths: - `BANANA_API_URL="https://n.lconai.com"` - `BANANA_DEFAULT_MODEL="gpt-image-2-pro"` - 但在今晚部分会话中，当前 shell / 运行环境读到的仍是旧值 `gemini-3.1-flash-image-preview`，说明： - **文件已改对** - 但**当前进程环境不一定已刷新** - 因此：后续若要继续严格使用 `n.lconai.com + gpt-image-2-pro`，应优先用**新任务 / 新会话 / - confidence: 0.00 - evidence: memory/2026-05-08.md:399-401 [score=0.853 recalls=0 avg=0.620 source=memory/2026-05-08.md:8-10]
<!-- openclaw-memory-promotion:memory:memory/2026-05-09.md:384:386 -->
- ## Light Sleep <!-- openclaw:dreaming:light:start --> - Candidate: Reflections: Theme: `assistant` kept surfacing across 3198 memories.; confidence: 1.00; evidence: memory/2026-04-19.md:6133-6149, memory/2026-04-19.md:6248-6267, memory/2026-04-19.md:6452-6462; note: reflection - confidence: 0.00 - evidence: memory/2026-05-09.md:423-426 - recalls: 0 - status: staged - Candidate: Possible Lasting Truths: - `BANANA_API_URL="https://n.lconai.com"` - `BANANA_DEFAULT_MODEL="gpt-image-2-pro"` - 但在今晚部分会话中，当前 shell / 运行环境读到的仍是旧值 `gemini-3.1-flash-image-preview`，说明： - **文件已改对** - 但**当前进程环境不一定已刷新** - 因此：后续若要继续严格使用 `n.lconai.com + gpt-image-2-pro`，应优先用**新任务 / 新会话 / [score=0.828 recalls=0 avg=0.620 source=memory/2026-05-09.md:388-395]

## Promoted From Short-Term Memory (2026-05-15)

<!-- openclaw-memory-promotion:memory:memory/2026-05-09.md:789:792 -->
- - Candidate: Durable Memory Additions: 2026-05-09｜OpenClaw 海报篇培训 PPT 当前正式项目目录：`/Users/a123/.openclaw/workspace/outputs/ppt-projects/20260509_120500_openclaw_poster_training/`。; 用户最终确认通过并作为整套视觉锚点的 3 页是：`8f687451-a645-4b5f-bbd8-0aacf6a0756a.png`、`45ee4532-6d9a-4cfb-a729-d52b56da5812.jpg`、`69f7d - confidence: 0.00 - evidence: memory/2026-05-09.md:819-822 - recalls: 0 [score=0.848 recalls=0 avg=0.620 source=memory/2026-05-09.md:13-16]
<!-- openclaw-memory-promotion:memory:memory/2026-05-09.md:793:794 -->
- - Candidate: Durable Memory Additions: 当前这 6 张新生成页的品牌位修正规则已被用户明确：统一替换为公司标准 LOGO `WE BURN未本`（用户最新参考图：`/Users/a123/.openclaw/media/inbound/8736cd26-9226-42dd-8160-39b320305003.jpg`）。用户口头说“右上角”，但实际示例图确认要改的是**左上角品牌位**，不要误判区域。; 当前状态停在：已为这 6 页准备批量替换 LOGO 的遮罩预览与说明，等待用户明确回复 **“可以，批量改”** 后继续统一修改。 - confidence: 0.00 [score=0.848 recalls=0 avg=0.620 source=memory/2026-05-09.md:18-19]
<!-- openclaw-memory-promotion:memory:memory/2026-05-11.md:394:396 -->
- - Candidate: Possible Lasting Truths: - `BANANA_API_URL="https://n.lconai.com"` - `BANANA_DEFAULT_MODEL="gpt-image-2-pro"` - 但在今晚部分会话中，当前 shell / 运行环境读到的仍是旧值 `gemini-3.1-flash-image-preview`，说明： - **文件已改对** - 但**当前进程环境不一定已刷新** - 因此：后续若要继续严格使用 `n.lconai.com + gpt-image-2-pro`，应优先用**新任务 / 新会话 / - confidence: 0.00 - evidence: memory/2026-05-08.md:424-426 [score=0.809 recalls=0 avg=0.620 source=memory/2026-05-11.md:218-220]

## Promoted From Short-Term Memory (2026-05-16)

<!-- openclaw-memory-promotion:memory:memory/2026-05-10.md:389:391 -->
- - Candidate: Possible Lasting Truths: - `BANANA_API_URL="https://n.lconai.com"` - `BANANA_DEFAULT_MODEL="gpt-image-2-pro"` - 但在今晚部分会话中，当前 shell / 运行环境读到的仍是旧值 `gemini-3.1-flash-image-preview`，说明： - **文件已改对** - 但**当前进程环境不一定已刷新** - 因此：后续若要继续严格使用 `n.lconai.com + gpt-image-2-pro`，应优先用**新任务 / 新会话 / - confidence: 0.00 - evidence: memory/2026-05-10.md:359-361 [score=0.848 recalls=0 avg=0.620 source=memory/2026-05-10.md:8-10]
<!-- openclaw-memory-promotion:memory:memory/2026-05-09.md:783:785 -->
- - Candidate: Possible Lasting Truths: - `BANANA_API_URL="https://n.lconai.com"` - `BANANA_DEFAULT_MODEL="gpt-image-2-pro"` - 但在今晚部分会话中，当前 shell / 运行环境读到的仍是旧值 `gemini-3.1-flash-image-preview`，说明： - **文件已改对** - 但**当前进程环境不一定已刷新** - 因此：后续若要继续严格使用 `n.lconai.com + gpt-image-2-pro`，应优先用**新任务 / 新会话 / - confidence: 0.00 - evidence: memory/2026-05-09.md:429-431 [score=0.825 recalls=0 avg=0.620 source=memory/2026-05-09.md:395-397]

## 林翀 · 光遇女孩档案（2026-05-16 建档）

- 林翀（ou_3b86047692970f514890e0a79263ac63）多次聊起的"光遇女生"档案，已归档：`/Users/a123/.openclaw/workspace/outputs/contacts/lin-chong/sky-girl-profile.md`
- 触发词：光遇女生 / 光遇女孩 / 那个女生 / 那女孩 / 玩光遇的女生 / Sky 女孩 / 之前那个 / 三个号那个
- 一旦命中触发词，main 必须先 `read` 该档案再回复，禁止再回"没查到记录"
- 关键事实（极简版）：24 岁、《光·遇》5 年深度玩家、3 个号 3 个角色、理由"一个人太孤单"
- 林翀同期还有另外两个暧昧/兜底对象，已建议尽快降级
- 每次出现新事实/新进展，必须追加到该档案第 10 节"增量记录"

## 代发消息硬规则（2026-05-17 用户明确）

- 任何以用户（涂是淦）身份发出的消息（群消息 / 私聊 / 报备 / 通知等），**必须**在末尾加后缀：`—— 虾指挥代发🦞`
- 适用范围：`feishu_im_user_message`、任何代用户发送的飞书消息
- 不需要二次确认后缀，默认就这一句
- 用户已明确"以后一定要记住不要再提醒"——下次默认带上即可

## PSD 真分层项目（2026-05-18 建档）

- 用户跑通过的链路：Codex 编排 + GPT-5.4 思考 + GPT-Image-2 生图 + 本地 Python 抠底 + psd-tools/pytoshop 写 PSD
- 公众号文章「ChatGPT 网页对话出 PSD」是 AI 写的伪科普，关键合成步骤被删
- 当前测试项目目录：`/Users/a123/.openclaw/workspace/outputs/psd-layer-test/20260518/`
- 复盘卡：`outputs/psd-layer-test/20260518/RECAP.md`
- 详细记忆：`memory/2026-05-18.md`
- 触发词：「PSD 真分层」「海报分层」「重绘式分层」「复盘 PSD 测试」「那个分层项目」「自然本色海报分层」
- 命中触发词必须先 read 上述档案再回复，禁止凭记忆复述
- 链路固有限制：中文字体/品牌 logo/包装小字会被 GPT-Image-2 重画走形，要保真需切「分割式分层」(SAM/GroundingDINO + inpainting) 或混合方案
