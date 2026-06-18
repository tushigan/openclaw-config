#!/usr/bin/env python3
"""从旧版 candidates 响应 JSON 中提取 inlineData.data。"""

import json
import sys


def main() -> None:
    data = json.load(sys.stdin)
    print(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])


if __name__ == "__main__":
    main()
