---
name: omni-vision-psd-extractor
version: 4.0.0-mac-openclaw (111omni original logic)
description: Mac/OpenClaw adapter for the original 111omni PSD extractor. Use the top-level scripts/run_omni_delivery.py wrapper by default.
triggers:
  - "原图提取分层"
  - "物理拆解PSD"
  - "无损提取PSD"
  - "语义抠图PSD"
  - "全息万物提取"
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - node
        - npm
        - zip
    emoji: "🔪"
---

# Omni-Vision PSD Extractor

This nested skill file is intentionally minimal. The OpenClaw entrypoint and execution rules live in the parent `SKILL.md`.

Use:

```bash
python3 {baseDir}/../scripts/run_omni_delivery.py \
  --source "/absolute/path/to/source.png" \
  --source-session-key "agent:design:feishu:direct:ou_xxx"
```

The original 111omni extraction logic is preserved in `omni-vision-psd-extractor/scripts/`.
Read the parent `SKILL.md` for the Feishu target and split-package delivery rules.
