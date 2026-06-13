#!/usr/bin/env python3
"""
OpenClaw 顶层记忆系统 - 数据结构定义
5层架构：客户 → 品牌 → 项目 → 任务 → 迭代版本
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json


@dataclass
class ContactInfo:
    """联系人信息"""
    name: str
    role: str = ""
    phone: str = ""
    email: str = ""
    wechat: str = ""
    feishu_user_id: str = ""
    notes: str = ""


@dataclass
class ContractInfo:
    """合同信息"""
    contract_id: str
    contract_name: str
    signed_date: str
    amount: float = 0.0
    currency: str = "CNY"
    status: str = "active"  # active/completed/cancelled
    file_path: str = ""
    notes: str = ""


@dataclass
class ClientProfile:
    """客户档案（第1层）"""
    client_id: str
    name: str
    name_en: str = ""
    industry: str = ""
    company_type: str = ""  # 甲方/代理商/渠道商
    contacts: List[ContactInfo] = field(default_factory=list)
    contracts: List[ContractInfo] = field(default_factory=list)
    business_notes: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    _last_modified_by: str = ""  # agent ID

    def to_dict(self) -> Dict:
        data = asdict(self)
        return data


@dataclass
class HistoryEntry:
    """变更历史记录"""
    timestamp: str
    field: str
    old_value: Any
    new_value: Any
    changed_by: str  # agent ID
    user_confirmed: bool = False
    reason: str = ""


@dataclass
class BrandProfile:
    """品牌档案（第2层）"""
    brand_id: str
    client_id: str  # 关联客户
    name: str
    name_en: str = ""
    industry: str = ""
    category: str = ""
    positioning: str = ""
    brand_tone: str = ""  # 品牌调性
    target_audience: str = ""  # 目标受众
    core_values: List[str] = field(default_factory=list)  # 核心价值观
    brand_story: str = ""
    competitive_advantages: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    assets_path: str = ""  # 品牌资产库路径
    created_at: str = ""
    updated_at: str = ""
    _history: List[HistoryEntry] = field(default_factory=list)  # 变更历史
    _last_modified_by: str = ""

    def to_dict(self) -> Dict:
        data = asdict(self)
        return data


@dataclass
class ProjectProfile:
    """项目档案（第3层）"""
    project_id: str
    brand_id: str
    client_id: str
    campaign_name: str
    campaign_type: str = ""  # 品牌全案/产品发布/营销战役/TVC制作/海报设计等
    start_date: str = ""
    deadline_date: str = ""
    status: str = "active"  # active/on-hold/completed/cancelled
    lifecycle_stage: str = ""  # 需求收集/策略制定/创意执行/交付等
    milestones: List[Dict] = field(default_factory=list)
    project_summary: str = ""
    current_goal: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    _last_modified_by: str = ""

    # 关键文档路径
    brief_path: str = ""
    strategy_path: str = ""
    creative_direction_path: str = ""

    def to_dict(self) -> Dict:
        data = asdict(self)
        return data


@dataclass
class TaskProfile:
    """任务档案（第4层）"""
    task_id: str
    project_id: str
    task_name: str
    task_type: str = ""  # poster/copy/video/tvc/design/research等
    assigned_agent: str = ""  # main/design/copywriter/strategy/research
    assigned_skill: str = ""  # 调用的 skill 名称
    status: str = "pending"  # pending/in-progress/completed/cancelled
    priority: str = "normal"  # low/normal/high/urgent
    brief: str = ""
    requirements: Dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    completed_at: str = ""
    latest_version: int = 0  # 当前最新版本号
    _last_modified_by: str = ""

    def to_dict(self) -> Dict:
        data = asdict(self)
        return data


@dataclass
class IterationMetadata:
    """迭代版本元信息（第5层）"""
    iteration_id: str
    task_id: str
    version: int
    output_file_path: str
    output_file_type: str  # image/video/document/psd/audio等
    file_size_bytes: int = 0
    created_at: str = ""
    created_by: str = ""  # agent ID
    expire_at: str = ""  # 过期时间（图片/视频30天后）
    is_expired: bool = False
    prompt: str = ""  # 生成时使用的 prompt
    model_used: str = ""  # 使用的模型
    generation_params: Dict = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict:
        data = asdict(self)
        return data


@dataclass
class ConflictReport:
    """冲突检测报告"""
    entity_type: str  # client/brand/project/task
    entity_id: str
    field: str
    old_value: Any
    new_value: Any
    diff: str
    impact_summary: str
    requires_confirmation: bool = True
    suggested_action: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_user_message(self) -> str:
        """生成用户确认消息"""
        return f"""⚠️ 检测到{self.entity_type}档案变更

字段：{self.field}
原值：{self.old_value}
新值：{self.new_value}

{self.diff}

影响范围：
{self.impact_summary}

是否确认此变更？
回复"确认"继续 / "取消"放弃"""


# 文件过期策略配置
EXPIRY_RULES = {
    "image": 30,      # 图片：30天
    "video": 30,      # 视频：30天
    "psd": 60,        # PSD：60天
    "audio": 30,      # 音频：30天
    "document": None, # 文档：永久保留（md/txt/json/pdf等）
}

# 文件类型映射
FILE_TYPE_MAPPING = {
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".svg": "image",
    ".mp4": "video",
    ".mov": "video",
    ".avi": "video",
    ".mkv": "video",
    ".psd": "psd",
    ".ai": "psd",
    ".sketch": "psd",
    ".mp3": "audio",
    ".wav": "audio",
    ".m4a": "audio",
    ".md": "document",
    ".txt": "document",
    ".json": "document",
    ".pdf": "document",
    ".docx": "document",
    ".xlsx": "document",
}


def get_file_type(file_path: str) -> str:
    """根据文件扩展名获取文件类型"""
    import os
    ext = os.path.splitext(file_path)[1].lower()
    return FILE_TYPE_MAPPING.get(ext, "document")


def get_expiry_days(file_type: str) -> Optional[int]:
    """获取文件过期天数"""
    return EXPIRY_RULES.get(file_type)


def calculate_expire_date(created_at: str, file_type: str) -> Optional[str]:
    """计算文件过期日期"""
    expiry_days = get_expiry_days(file_type)
    if expiry_days is None:
        return None

    from datetime import datetime, timedelta
    created = datetime.fromisoformat(created_at)
    expire = created + timedelta(days=expiry_days)
    return expire.isoformat()
