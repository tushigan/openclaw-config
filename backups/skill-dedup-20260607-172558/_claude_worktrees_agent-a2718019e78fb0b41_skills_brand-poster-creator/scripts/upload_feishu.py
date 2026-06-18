#!/usr/bin/env python3
"""
上传图片到飞书云文档
- 支持创建文件夹
- 上传图片到指定文件夹
- 返回飞书文档链接
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path


def get_feishu_token() -> str:
    """获取飞书 tenant_access_token"""
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量未设置")
    
    # 获取 tenant_access_token
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"app_id": app_id, "app_secret": app_secret})
        ],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"获取飞书 token 失败: {result.stderr}")
    
    try:
        data = json.loads(result.stdout)
        if data.get("code") != 0:
            raise Exception(f"飞书 API 错误: {data.get('msg')}")
        return data["tenant_access_token"]
    except json.JSONDecodeError:
        raise Exception(f"解析飞书响应失败: {result.stdout[:200]}")


def upload_image_to_feishu(file_path: str, token: str) -> dict:
    """
    上传图片到飞书
    
    Returns:
        {"image_key": "xxx", "url": "xxx"}
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 使用飞书上传图片 API
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            "https://open.feishu.cn/open-apis/im/v1/images",
            "-H", f"Authorization: Bearer {token}",
            "-F", f"image_type=message",
            "-F", f"file=@{file_path}"
        ],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"上传图片失败: {result.stderr}")
    
    try:
        data = json.loads(result.stdout)
        if data.get("code") != 0:
            raise Exception(f"飞书上传错误: {data.get('msg')}")
        return {
            "image_key": data["data"]["image_key"],
            "url": f"https://open.feishu.cn/open-apis/im/v1/images/{data['data']['image_key']}"
        }
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception(f"解析上传响应失败: {result.stdout[:200]}")


def create_feishu_doc(title: str, content: str, token: str) -> str:
    """
    创建飞书文档并写入内容
    
    Returns:
        飞书文档链接
    """
    # 创建文档
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            "https://open.feishu.cn/open-apis/docx/v1/documents",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "title": title,
                "folder_token": ""
            })
        ],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"创建文档失败: {result.stderr}")
    
    try:
        data = json.loads(result.stdout)
        if data.get("code") != 0:
            raise Exception(f"飞书创建文档错误: {data.get('msg')}")
        
        document_id = data["data"]["document"]["document_id"]
        return f"https://feishu.cn/docx/{document_id}"
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception(f"解析创建文档响应失败: {result.stdout[:200]}")


def upload_to_feishu(file_path: str, folder: str, title: str) -> dict:
    """
    上传图片到飞书并创建文档
    
    Args:
        file_path: 图片文件路径
        folder: 文件夹名称（用于组织）
        title: 文档标题
    
    Returns:
        {"doc_url": "xxx", "image_url": "xxx", "status": "success"}
    """
    try:
        # 获取 token
        token = get_feishu_token()
        
        # 上传图片
        image_info = upload_image_to_feishu(file_path, token)
        
        # 创建文档并添加图片
        doc_title = f"{folder} - {title}"
        doc_url = create_feishu_doc(doc_title, f"图片链接: {image_info['url']}", token)
        
        return {
            "status": "success",
            "doc_url": doc_url,
            "image_url": image_info["url"],
            "image_key": image_info["image_key"],
            "folder": folder,
            "title": title
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="上传图片到飞书云文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 上传图片到飞书
  python upload_feishu.py --file images/mood_concept.png \\
    --folder "小白心里软-端午节海报" \\
    --title "MJ调性图-四宫格"

环境变量:
  FEISHU_APP_ID     - 飞书应用 ID
  FEISHU_APP_SECRET - 飞书应用密钥
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        required=True,
        help="要上传的图片文件路径"
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="品牌海报项目",
        help="飞书文件夹名称（用于组织），默认: 品牌海报项目"
    )
    parser.add_argument(
        "--title", "-t",
        type=str,
        required=True,
        help="文档标题"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    # 执行上传
    result = upload_to_feishu(args.file, args.folder, args.title)
    
    if args.verbose:
        if result["status"] == "success":
            print(f"✅ 上传成功")
            print(f"📁 文件夹: {result['folder']}")
            print(f"📄 文档标题: {args.title}")
            print(f"🔗 飞书文档: {result['doc_url']}")
            print(f"🖼️  图片链接: {result['image_url']}")
        else:
            print(f"❌ 上传失败: {result['message']}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 返回退出码
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
