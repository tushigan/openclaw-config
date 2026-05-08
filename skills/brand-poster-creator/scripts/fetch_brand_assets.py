#!/usr/bin/env python3
"""
飞书云盘品牌素材检索与下载脚本

根据品牌名在指定飞书云盘文件夹中搜索品牌子文件夹，
获取 Logo、IP 等品牌资产图并下载到本地项目目录。

使用示例:
  python3 fetch_brand_assets.py \
    --brand "小白心里软" \
    --folder-token "HrvvfbL8clefhAdSLtUcb7G3nYg" \
    --project-dir "/Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260507-001" \
    --verbose

环境变量:
  FEISHU_APP_ID     - 飞书应用 ID
  FEISHU_APP_SECRET - 飞书应用密钥
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from difflib import SequenceMatcher


FEISHU_BASE = "https://open.feishu.cn/open-apis"

# 默认品牌素材云盘 folder_token
DEFAULT_FOLDER_TOKEN = "HrvvfbL8clefhAdSLtUcb7G3nYg"

# 图片扩展名白名单
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}

# 文件名智能分类关键词
CLASSIFY_RULES = {
    "logo": ["logo", "Logo", "LOGO", "标志", "商标"],
    "ip": ["ip", "IP", "形象", "角色", "吉祥物", "IP形象"],
    "product": ["产品", "product", "商品", "实物"],
}


def get_feishu_token() -> str:
    """获取飞书 tenant_access_token"""
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        raise ValueError("FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量未设置")

    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"app_id": app_id, "app_secret": app_secret})
        ],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        raise Exception(f"获取飞书 token 失败: {result.stderr}")

    data = json.loads(result.stdout)
    if data.get("code") != 0:
        raise Exception(f"飞书 API 错误: {data.get('msg')}")

    return data["tenant_access_token"]


def feishu_api_get(path: str, token: str, params: dict = None) -> dict:
    """调用飞书 GET API"""
    url = f"{FEISHU_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        if query:
            url = f"{url}?{query}"

    cmd = ["curl", "-s", "-X", "GET", url, "-H", f"Authorization: Bearer {token}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"飞书 API 请求失败: {result.stderr}")

    data = json.loads(result.stdout)
    if data.get("code") != 0:
        raise Exception(f"飞书 API 错误 (path={path}): {data.get('msg')}")

    return data


def list_folder_items(folder_token: str, token: str) -> list:
    """列出飞书文件夹下的所有项目"""
    items = []
    page_token = None

    while True:
        params = {"folder_token": folder_token}
        if page_token:
            params["page_token"] = page_token

        data = feishu_api_get("/drive/v1/files", token, params)
        files = data.get("data", {}).get("files", [])
        items.extend(files)

        page_token = data.get("data", {}).get("page_token")
        if not page_token:
            break

    return items


def download_file(file_token: str, save_path: str, token: str) -> bool:
    """从飞书云盘下载文件到本地"""
    url = f"{FEISHU_BASE}/drive/v1/medias/{file_token}/download"
    result = subprocess.run(
        ["curl", "-s", "-o", save_path, url, "-H", f"Authorization: Bearer {token}"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        return False

    # 验证文件已下载且非空
    return os.path.exists(save_path) and os.path.getsize(save_path) > 0


def match_brand_folder(items: list, brand_name: str) -> dict | None:
    """在文件夹列表中模糊匹配品牌名，返回最佳匹配的文件夹"""
    candidates = [item for item in items if item.get("type") == "folder"]

    if not candidates:
        return None

    best_match = None
    best_score = 0.0

    for folder in candidates:
        folder_name = folder.get("name", "")
        # 计算双向相似度：品牌名包含在文件夹名中，或反过来
        score = max(
            SequenceMatcher(None, brand_name.lower(), folder_name.lower()).ratio(),
            SequenceMatcher(None, folder_name.lower(), brand_name.lower()).ratio()
        )
        # 精确包含关系加分
        if brand_name in folder_name or folder_name in brand_name:
            score = max(score, 0.8)

        if score > best_score:
            best_score = score
            best_match = folder

    # 阈值：至少 0.5 的相似度
    if best_score >= 0.5:
        return best_match

    return None


def classify_asset(filename: str) -> str:
    """根据文件名智能分类素材类型"""
    name_lower = filename.lower()

    for asset_type, keywords in CLASSIFY_RULES.items():
        for keyword in keywords:
            if keyword.lower() in name_lower:
                return asset_type

    return "other"


def is_image_file(filename: str) -> bool:
    """判断文件是否为图片"""
    ext = Path(filename).suffix.lower()
    return ext in IMAGE_EXTENSIONS


def fetch_brand_assets(brand_name: str, folder_token: str, project_dir: str, token: str) -> dict:
    """
    核心逻辑：搜索品牌文件夹并下载素材

    Returns:
        {
            "status": "success|not_found|error",
            "brand_folder": "文件夹名 或 null",
            "assets": [...],
            "message": "描述信息"
        }
    """
    images_dir = os.path.join(project_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    try:
        # 1. 列出根文件夹下的项目
        items = list_folder_items(folder_token, token)

        # 2. 匹配品牌文件夹
        brand_folder = match_brand_folder(items, brand_name)

        if not brand_folder:
            return {
                "status": "not_found",
                "brand_folder": None,
                "assets": [],
                "message": f"在云盘中未找到品牌「{brand_name}」的文件夹"
            }

        # 3. 列出品牌文件夹内的图片
        brand_items = list_folder_items(brand_folder["token"], token)
        image_files = [item for item in brand_items if is_image_file(item.get("name", ""))]

        if not image_files:
            return {
                "status": "not_found",
                "brand_folder": brand_folder["name"],
                "assets": [],
                "message": f"品牌「{brand_name}」的文件夹中没有图片文件"
            }

        # 4. 下载并分类
        assets = []
        type_counters = {}  # 用于同类型多文件的命名

        for image_file in image_files:
            original_name = image_file.get("name", "unknown")
            file_token = image_file.get("token")
            asset_type = classify_asset(original_name)

            # 确定保存文件名
            ext = Path(original_name).suffix
            if asset_type == "other":
                idx = type_counters.get("other", 0) + 1
                type_counters["other"] = idx
                save_name = f"brand_asset_{idx}{ext}"
            else:
                # 同类型多文件时追加序号
                existing_count = sum(1 for a in assets if a["type"] == asset_type)
                if existing_count > 0:
                    save_name = f"{asset_type}_{existing_count + 1}{ext}"
                else:
                    save_name = f"{asset_type}{ext}"

            save_path = os.path.join(images_dir, save_name)

            # 下载文件
            success = download_file(file_token, save_path, token)

            relative_path = f"images/{save_name}"
            assets.append({
                "type": asset_type,
                "filename": save_name,
                "path": relative_path,
                "original_name": original_name,
                "downloaded": success
            })

        # 5. 更新 brief.json 的 assets 字段
        brief_path = os.path.join(project_dir, "brief.json")
        if os.path.exists(brief_path):
            with open(brief_path, "r", encoding="utf-8") as f:
                brief = json.load(f)

            downloaded_assets = [a for a in assets if a["downloaded"]]
            for asset in downloaded_assets:
                if asset["type"] == "logo" and not brief.get("assets", {}).get("logo"):
                    brief.setdefault("assets", {})["logo"] = asset["path"]
                elif asset["type"] == "ip" and not brief.get("assets", {}).get("ip"):
                    brief.setdefault("assets", {})["ip"] = asset["path"]
                elif asset["type"] == "product" and not brief.get("assets", {}).get("product"):
                    brief.setdefault("assets", {})["product"] = asset["path"]
                else:
                    brief.setdefault("assets", {}).setdefault("brand_assets", []).append(asset["path"])

            brief.setdefault("assets", {})["source"] = "feishu_drive"

            with open(brief_path, "w", encoding="utf-8") as f:
                json.dump(brief, f, ensure_ascii=False, indent=2)

        downloaded_count = sum(1 for a in assets if a["downloaded"])
        return {
            "status": "success",
            "brand_folder": brand_folder["name"],
            "assets": assets,
            "message": f"从品牌「{brand_name}」文件夹中获取了 {downloaded_count}/{len(assets)} 个素材"
        }

    except Exception as e:
        return {
            "status": "error",
            "brand_folder": None,
            "assets": [],
            "message": f"检索品牌素材时出错: {str(e)}"
        }


def main():
    parser = argparse.ArgumentParser(
        description="飞书云盘品牌素材检索与下载",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 fetch_brand_assets.py \\
    --brand "小白心里软" \\
    --folder-token "HrvvfbL8clefhAdSLtUcb7G3nYg" \\
    --project-dir "/Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260507-001" \\
    --verbose

环境变量:
  FEISHU_APP_ID     - 飞书应用 ID
  FEISHU_APP_SECRET - 飞书应用密钥
        """
    )

    parser.add_argument("--brand", "-b", type=str, required=True, help="品牌名称")
    parser.add_argument("--folder-token", "-f", type=str, default=DEFAULT_FOLDER_TOKEN,
                        help=f"飞书云盘根文件夹 token（默认: {DEFAULT_FOLDER_TOKEN}）")
    parser.add_argument("--project-dir", "-d", type=str, required=True, help="项目目录绝对路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 获取 token
    try:
        token = get_feishu_token()
    except Exception as e:
        result = {"status": "error", "brand_folder": None, "assets": [], "message": str(e)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 执行检索
    result = fetch_brand_assets(args.brand, args.folder_token, args.project_dir, token)

    if args.verbose:
        if result["status"] == "success":
            print(f"✅ {result['message']}")
            print(f"📁 品牌文件夹: {result['brand_folder']}")
            for asset in result["assets"]:
                status = "✅" if asset["downloaded"] else "❌"
                print(f"  {status} {asset['type']}: {asset['original_name']} → {asset['path']}")
        elif result["status"] == "not_found":
            print(f"⚠️ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
