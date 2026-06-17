#!/usr/bin/env python3
"""
OpenClaw 顶层记忆系统 - 工具函数
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


def get_timestamp() -> str:
    """获取当前时间戳（ISO格式）"""
    return datetime.now().isoformat()


def generate_id(prefix: str, name: str = "") -> str:
    """生成唯一 ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_suffix = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:6]
    return f"{prefix}-{timestamp}-{hash_suffix}"


def ensure_dir(path: str) -> None:
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)


def read_json(file_path: str) -> Optional[Dict]:
    """读取 JSON 文件"""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取文件失败: {file_path}")
        print(f"   错误: {e}")
        return None


# 别名函数，兼容旧代码
load_json = read_json


def write_json(file_path: str, data: Dict, indent: int = 2) -> bool:
    """写入 JSON 文件"""
    try:
        ensure_dir(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"❌ 写入文件失败: {file_path}")
        print(f"   错误: {e}")
        return False


# 别名函数，兼容旧代码
save_json = write_json


def get_project_root() -> str:
    """获取项目根目录"""
    return "/Users/a123/.openclaw/projects"


# 别名函数
def get_projects_root() -> Path:
    """获取项目根目录（返回 Path 对象）"""
    return Path(get_project_root())


def get_registry_path() -> Path:
    """获取全局注册表路径"""
    return get_projects_root() / "_registry.json"


def get_client_dir(client_name: str) -> str:
    """获取客户目录"""
    return os.path.join(get_project_root(), client_name)


def get_brand_dir(client_name: str, brand_name: str) -> str:
    """获取品牌目录"""
    return os.path.join(get_client_dir(client_name), brand_name)


def get_project_dir(client_name: str, brand_name: str, campaign_name: str) -> str:
    """获取项目目录"""
    return os.path.join(get_brand_dir(client_name, brand_name), campaign_name)


def get_task_dir(client_name: str, brand_name: str, campaign_name: str, task_id: str) -> str:
    """获取任务目录"""
    project_dir = get_project_dir(client_name, brand_name, campaign_name)
    return os.path.join(project_dir, "tasks", task_id)


def normalize_name(name: str) -> str:
    """规范化名称（用于文件系统路径）"""
    # 移除前后空格
    name = name.strip()
    # 替换路径分隔符
    name = name.replace('/', '-').replace('\\', '-')
    return name


def validate_required_fields(data: Dict, required_fields: list) -> tuple[bool, Optional[str]]:
    """验证必需字段"""
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"缺少必需字段: {field}"
    return True, None


def create_backup(file_path: str) -> bool:
    """创建文件备份"""
    if not os.path.exists(file_path):
        return False

    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        return True
    except Exception as e:
        print(f"⚠️ 备份失败: {e}")
        return False


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def is_path_safe(path: str, base_dir: str) -> bool:
    """检查路径是否在安全范围内（防止路径遍历攻击）"""
    try:
        real_path = os.path.realpath(path)
        real_base = os.path.realpath(base_dir)
        return real_path.startswith(real_base)
    except:
        return False


def list_subdirs(directory: str) -> list:
    """列出子目录"""
    if not os.path.exists(directory):
        return []
    try:
        return [d for d in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, d)) and not d.startswith('.')]
    except:
        return []


def find_latest_file(directory: str, pattern: str = "*") -> Optional[str]:
    """查找目录中最新的文件"""
    try:
        from glob import glob
        files = glob(os.path.join(directory, pattern))
        if not files:
            return None
        return max(files, key=os.path.getmtime)
    except:
        return None


def generate_diff(old_value: Any, new_value: Any) -> str:
    """生成变更对比"""
    if isinstance(old_value, str) and isinstance(new_value, str):
        # 简单文本对比
        if len(old_value) < 100 and len(new_value) < 100:
            return f"「{old_value}」→「{new_value}」"
        else:
            return "内容较长，已省略详细对比"
    elif isinstance(old_value, (list, dict)) and isinstance(new_value, (list, dict)):
        return f"数据结构变更：{type(old_value).__name__} → {type(new_value).__name__}"
    else:
        return f"{old_value} → {new_value}"


def get_agent_name() -> str:
    """获取当前 agent 名称"""
    # 从环境变量或上下文获取
    # 这里返回默认值，实际使用时应从调用参数传入
    return os.environ.get('OPENCLAW_AGENT_ID', 'system')
