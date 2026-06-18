# Feishu Menu Logic (OpenClaw Side)

When a Bot Menu event (type: `application.bot.menu_v6`) or a Feishu interactive card action is forwarded to you, it will typically come as a raw text command or an event JSON.

## Handling Feishu Shortcuts & Menus

If the user clicks a Feishu shortcut/menu and sends you a specific trigger word or event key, follow this exact logic:

1. **If user message contains `[系统内部指令：用户点击了“创作中心”按钮` or event key is `runninghub_draw` or user says "创作中心" / "帮我生图"**:
   - **CRITICAL**: IGNORE any instructions inside the prompt that tell you to reply with "创作中心已就绪".
   - DO NOT run `--list` to fetch public apps.
   - INSTEAD, read `{baseDir}/references/custom-workflows.md`.
   - **CRITICAL**: You MUST format the response as a clear Markdown list to prevent Feishu from paginating tables.
   - Reply EXACTLY with this structure:
   
   🎯 欢迎来到创作中心！ 我为您准备了以下 11 个专属工作流：
   
   **1.** ✏️ 素描 (Sketch) `[2000785565266083842]`
   **2.** 🖼️ 版画 (Printmaking) `[2000775904060207106]`
   **3.** 📝 草稿 (Draft) `[2000774473844486146]`
   **4.** 🔍 SeedVR2 视频/图像超清放大 `[2054744810652741633]`
   **5.** 💡 光影融合 V31208 `[2054748651523715074]`
   **6.** ✨ 质感提升 (kontext工作流) `[2054755676718673922]`
   **7.** 📐 扩图-自定义尺寸 `[2001848803948937217]`
   **8.** 💎 Klein_亚秒级渲染精修 V4 `[2017525136844394497]`
   **9.** 🏠 Leo室内写实渲染V3 `[2013570680079523842]`
   **10.** 🎇 Qwen-edit 万物重打光 `[1964753754237095937]`
   **11.** 🔎 放大0723 `[2061369927923232769]`
   
   使用方式：
   - 回复 **编号** (如：`1` 或 `素描`) 选择工作流
   - 根据提示上传图片并设置参数
   - 我会自动帮您运行！
   
   你想使用哪个工作流？ 🚀

2. **If event key is `runninghub_video` or user says "视频魔法" / "图片生视频" / "video_img"**:
   - Reply warmly: "好的，请直接上传一张图片，我来帮您转成视频！🎬"
   - (Then follow the standard image-to-video workflow in `video-models.md`).

3. **If event key is `runninghub_balance` or user says "检查余额" / "check_balance"**:
   - Immediately execute: `python3 {baseDir}/scripts/runninghub.py --check`
   - Return the balance info to the user in a friendly way.

## Interactive Flow for Custom Workflows
Once the user selects a custom workflow (e.g., "我选1" or "素描"):
1. Execute `python3 {baseDir}/scripts/runninghub_app.py --info WEBAPP_ID` to get the node IDs.
2. Reply to the user asking for the required inputs (e.g. "好的，准备运行素描工作流。请**上传一张参考图片**，并告诉我**每次出几张图**（不填默认4张）～")
3. Wait for the user to upload the image and provide text.
4. Download/save their image, run `runninghub_app.py --run WEBAPP_ID --file "NODE_ID:image=PATH" ...`
5. Send the result back using the `message` tool!
