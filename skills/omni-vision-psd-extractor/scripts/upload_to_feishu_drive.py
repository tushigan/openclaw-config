#!/usr/bin/env python3
"""
上传 PSD 文件到飞书云盘并获取访问链接

使用 OpenClaw 的 feishu_drive_file 工具上传文件
"""

import json
import subprocess
import sys
from pathlib import Path


def upload_to_feishu_drive(file_path: str, parent_folder_token: str = None) -> dict:
    """
    上传文件到飞书云盘
    
    Args:
        file_path: 本地文件路径
        parent_folder_token: 目标文件夹 token（可选，默认上传到根目录）
    
    Returns:
        {
            "success": True/False,
            "file_token": "xxx",
            "file_name": "xxx.psd",
            "size": 12345,
            "url": "https://example.feishu.cn/drive/folder/xxx",
            "error": "error message" (如果失败)
        }
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {
            "success": False,
            "error": f"文件不存在: {file_path}"
        }
    
    file_size = file_path.stat().st_size
    file_name = file_path.name
    
    print(f"[飞书云盘上传] 文件: {file_name}")
    print(f"[飞书云盘上传] 大小: {file_size / (1024 * 1024):.2f} MB")
    
    # 构建 OpenClaw tool 调用参数
    tool_params = {
        "action": "upload",
        "file_path": str(file_path.absolute()),
    }
    
    if parent_folder_token:
        tool_params["parent_node"] = parent_folder_token
    
    # 调用 OpenClaw feishu_drive_file 工具
    # 注意：这里需要通过 OpenClaw 的 tool 调用机制
    # 实际使用时应该由 OpenClaw agent 调用，而不是直接从 Python 调用
    
    print(f"[飞书云盘上传] 准备上传...")
    print(f"[飞书云盘上传] 参数: {json.dumps(tool_params, ensure_ascii=False)}")
    
    # 返回工具调用参数，由 OpenClaw agent 执行
    return {
        "success": True,
        "tool": "feishu_drive_file",
        "params": tool_params,
        "file_name": file_name,
        "size": file_size,
    }


def generate_feishu_file_url(file_token: str) -> str:
    """
    生成飞书文件访问链接
    
    Args:
        file_token: 文件 token
    
    Returns:
        飞书文件 URL
    """
    # 飞书云盘文件的标准 URL 格式
    # 注意：实际 URL 可能因组织配置而异
    return f"https://bytedance.larkoffice.com/file/{file_token}"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 upload_to_feishu_drive.py <file_path> [parent_folder_token]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    parent_folder_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = upload_to_feishu_drive(file_path, parent_folder_token)
    
    print("\n" + "=" * 60)
    print("上传结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 60)
    
    if result.get("success"):
        print("\n✅ 准备完成！")
        print(f"📋 工具: {result['tool']}")
        print(f"📦 文件: {result['file_name']} ({result['size'] / (1024 * 1024):.2f} MB)")
        print("\n💡 提示：请通过 OpenClaw agent 调用 feishu_drive_file 工具完成上传")
    else:
        print(f"\n❌ 错误: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
