#!/usr/bin/env python3
"""从 OpenAI 兼容图片响应 JSON 中提取 b64_json。"""

import json
import sys


def main() -> None:
    data = json.load(sys.stdin)
    print(((data.get("data") or [{}])[0].get("b64_json", "")))


if __name__ == "__main__":
    main()
