# 然利品牌升级视频｜严格版故事板生图提示词记录

整理对象：本轮已发送的 4 张“严格版”四宫格故事板。

说明：以下是生成这 4 张故事板时，实际发给生图模型的提示词与参考素材。前面因包装虚拟化而撤回的不合格版本不收录。

---

## 1. 第一段｜为什么升级｜0–6 秒

### 实际提示词

```text
Storyboard sheet, four panels, each panel 16:9, for segment 1 of Ranli brand upgrade video, 0-6s. Use ONLY the provided old Ranli logo and real old packaging references. Panel 1: old Ranli logo centered on clean red brand background. Panel 2: slow push-in on old logo with subtle design analysis lines, respectful heritage mood. Panel 3: real old packaging close-up from references, show old logo application; keep packaging shape and design faithful, no invented package. Panel 4: old logo and real old packaging details together, showing need for clearer professional brand system. No soup dumpling, no fake product, no extra subtitles.
```

### 参考素材

- `01_old_logo.jpg`：旧 Logo，作为 brand LOGO 参考
- `06_packaging_A_old_logo.jpg`：旧包装 A，作为 product reference
- `08_packaging_B_old_logo.jpg`：旧包装 B，作为 product reference

### 模型参考约束

```text
Reference images (by role — obey each role strictly, do not swap them):
- Image 1: brand LOGO — must be reproduced precisely, do not redraw, do not distort, do not invent new marks
- Image 2: product reference — keep packaging shape, real materials and color identity faithful
- Image 3: product reference — keep packaging shape, real materials and color identity faithful
```

---

## 2. 第二段｜升级了哪些东西｜6–13 秒

### 实际提示词

```text
Storyboard sheet, four panels, each panel 16:9, for segment 2 of Ranli brand upgrade video, 6-13s. Logo upgrade explanation only, no product packaging. Use provided old and new Ranli logo references. Panel 1: full old logo appears with clean technical breakdown guides. Panel 2: old logo separates into layers: Ranli brand name, 手工 label, rolling-pin symbol, outer frame, English Ranli. Panel 3: 手工 label fades backward, Ranli main name grows in visual weight; rolling-pin, outer frame and brand colors remain. Panel 4: elements recombine into new logo structure prototype. Show what is kept, weakened and strengthened. No packaging, no fake products, no subtitles.
```

### 参考素材

- `01_old_logo.jpg`：旧 Logo，作为 brand LOGO 参考
- `02_new_logo.jpg`：新 Logo，作为 brand LOGO 参考

### 模型参考约束

```text
Reference images (by role — obey each role strictly, do not swap them):
- Image 1: brand LOGO — must be reproduced precisely, do not redraw, do not distort, do not invent new marks
- Image 2: brand LOGO — must be reproduced precisely, do not redraw, do not distort, do not invent new marks
```

---

## 3. 第三段｜做了哪些提升 / 关键点｜13–20 秒

### 实际提示词

```text
Storyboard sheet, four 16:9 panels, segment 3 of Ranli logo upgrade video, 13-20s. No packaging. Use only new Ranli logo reference. Panel 1: logo forms on technical grid. Panel 2: outer frame aligns, Ranli wordmark becomes focused. Panel 3: rolling-pin symbol is highlighted as brand memory. Panel 4: new logo locks in stable final position, premium brand design release style. No fake product, no extra subtitles.
```

### 参考素材

- `02_new_logo.jpg`：新 Logo，作为 brand LOGO 参考

### 模型参考约束

```text
Reference images (by role — obey each role strictly, do not swap them):
- Image 1: brand LOGO — must be reproduced precisely, do not redraw, do not distort, do not invent new marks
```

---

## 4. 第四段｜应用展示 + 定版收束｜20–30 秒

### 实际提示词

```text
Storyboard sheet, four panels, each panel 16:9, for segment 4 of Ranli brand upgrade video, 20-30s. Product packaging must be real from provided references, do not invent packaging. Panel 1: real packaging A transition old to new, use references 06 to 05 faithfully. Panel 2: real packaging B transition old to new, use references 08 to 09 faithfully. Panel 3: brand system matrix with the two real new packaging designs as core; optional paper bag, card, uniform, vehicle only as secondary mockups, never replace packaging. Panel 4: materials fade back, red brand background returns, provided new logo plus slogan centered as final lockup. No soup dumpling, no fake product, no extra subtitles.
```

### 参考素材

- `06_packaging_A_old_logo.jpg`：包装 A 旧 Logo 版本，作为 product reference
- `05_packaging_A_new_logo.jpg`：包装 A 新 Logo 版本，作为 product reference
- `08_packaging_B_old_logo.jpg`：包装 B 旧 Logo 版本，作为 product reference
- `09_packaging_B_new_logo.jpg`：包装 B 新 Logo 版本，作为 product reference
- `03_logo_slogan_final.jpg`：新 Logo + 广告语，作为 brand LOGO 参考

### 模型参考约束

```text
Reference images (by role — obey each role strictly, do not swap them):
- Image 1: product reference — keep packaging shape, real materials and color identity faithful
- Image 2: product reference — keep packaging shape, real materials and color identity faithful
- Image 3: product reference — keep packaging shape, real materials and color identity faithful
- Image 4: product reference — keep packaging shape, real materials and color identity faithful
- Image 5: brand LOGO — must be reproduced precisely, do not redraw, do not distort, do not invent new marks
```

---

## 生成参数记录

- 模型：`gpt-image-2-pro`
- 请求尺寸：`2560x1440`
- 实际返回尺寸：`1672x941`
- 输出类型：每段 1 张四宫格故事板图片
- 重要限制：凡是出现包装，必须使用用户提供的真实包装参考，不允许虚构包装。

## 项目素材目录

```text
/Users/a123/.openclaw/projects/然利客户/然利/品牌升级视频/assets/
```
