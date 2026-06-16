# RunningHub Custom Workflows (用户的专属工作流)

When the user triggers the "创作中心" (Creation Center) via the Feishu bot menu (`runninghub_draw`), you MUST present this specific list of custom workflows. DO NOT use `--list` to fetch public apps.

## Custom Workflow List:

1. **素描 (Sketch)**
   - **WebappId**: `2000785565266083842`
   - **Inputs**: 
     - `image` (上传参考图)
     - `每次出几张图` (生成数量，默认可不填或设为4)

2. **版画 (Printmaking)**
   - **WebappId**: `2000775904060207106`
   - **Inputs**: 
     - `image` (上传参考图)
     - `每次出几张图` (生成数量)

3. **草稿 (Draft)**
   - **WebappId**: `2000774473844486146`
   - **Inputs**: 
     - `image` (上传参考图)
     - `每次出几张图` (生成数量)

4. **【GGUF版】SeedVR2/视频放大/超清放大**
   - **WebappId**: `2054744810652741633`
   - **Inputs**: 
     - `image` (上传需要放大的媒体)
     - `value` (分辨率数值，例如2048)

5. **光影融合V31208**
   - **WebappId**: `2054748651523715074`
   - **Inputs**: 
     - `image` (上传源图片)

6. **质感提升kontext工作流万物提升**
   - **WebappId**: `2054755676718673922`
   - **Inputs**: 
     - `image` (上传需要提升质感的图片)

7. **扩图-自定义尺寸 (Qwen Image 扩图)**
   - **WebappId**: `2001848803948937217`
   - **Tags**: 写实, 图生图, 扩图
   - **Description**: 极速稳定扩图工作流，可自定义尺寸
   - **Inputs**: 
     - `image` (上传需要扩图的图片)
     - `左扩充像素` (INT, 默认400)
     - `右扩充像素` (INT, 默认400)
     - `上扩充像素` (INT, 默认0)
     - `下扩充像素` (INT, 默认0)

8. **Klein_亚秒级渲染精修 (渲染级产品精修 V4)**
   - **WebappId**: `2017525136844394497`
   - **Tags**: 精修
   - **Description**: Klein 4步2K直出，渲染级产品精修 V4，亚秒级速度
   - **Inputs**: 
     - `image` (上传需要精修的产品图片)
     - `strength_model` (FLOAT, 模型强度, 默认0.85)

9. **Leo工作流：室内写实渲染V3 (FLUX2-Klein)**
   - **WebappId**: `2013570680079523842`
   - **Tags**: 其它建筑及空间设计, 图生图, 手稿到渲染
   - **Description**: 照片级写实室内渲染 V3，双图参考/全风格通用/直出高清
   - **Inputs**: 
     - `输入图片1` (IMAGE, 任何底图都可以)
     - `输入参考图2` (IMAGE, 可选参考图，下方按钮控制开关)
     - `是否参考图2` (BOOLEAN, 默认关闭)
     - `输入中文提示词` (TEXT, 按需填写可提升效果, 例如"照片级写实摄影效果")
     - `提示词优化` (BOOLEAN, 关闭更稳定-开启更丰富)

10. **Qwen-edit 万物重打光**
    - **WebappId**: `1964753754237095937`
    - **Tags**: 重新打光, 打光, 角色一致性
    - **Description**: 万物重打光，光影重塑/超强一致性/自定光源位置。用于真实人物/CG角色/动物/雕塑/IP形象等光影优化重塑。
    - **Inputs**: 
      - `图片替换` (IMAGE, 上传需要重打光的图片)
      - `提示词输入` (TEXT, 修改最后两个字即可, 例如"将主光源移动到角色的左侧")
      - `效果不好可以改` (SELECT, 默认"默认效果比较稳定")
      - `LORA模型强度` (FLOAT, 默认1.0)

11. **放大0723**
    - **WebappId**: `2061369927923232769`
    - **Inputs**: 
      - `image` (上传参考图)

## Execution Flow for Custom Workflows
1. **List Presentation**: When asked for "创作中心" or custom workflows, you MUST reply with a beautiful Markdown table. Do not use plain text lists.
   - **Reply EXACTLY with this structure**:
   
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
2. **User Selection & Parameter Request**: When the user selects one, tell them exactly what inputs are needed.
   - Example: "好的，准备运行【素描】工作流。请上传一张需要转换的图片，并告诉我需要生成几张（默认4张）。"
3. **Execution**: Once the user uploads the image and gives the parameters:
   - **CRITICAL STEP**: You MUST first send a message to the user saying something like: "✨ 收到！正在呼叫云端 GPU 为您生成画面，大概需要 1-3 分钟，请稍等片刻..." (Use the `message` tool). 
   - **ONLY AFTER** sending that notification message, you execute `runninghub_app.py --run {WebappId}`.
   - Map the uploaded image to the `image` node (e.g. `--file "1:image=/tmp/..."`). If you aren't sure of the exact nodeId, run `runninghub_app.py --info {WebappId}` silently first.
