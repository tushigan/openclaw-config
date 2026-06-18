#!/usr/bin/env python3
"""
Delivery Queue 定时巡检脚本
功能：
1. 检查 delivery-queue 中积压的消息
2. 对于超过一定时间的消息，根据策略处理：
   - 超过 30 分钟但小于 2 小时：记录警告
   - 超过 2 小时：标记为过期，移到 expired 目录
   - 超过 24 小时：直接删除
3. 输出巡检报告
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# 配置
QUEUE_DIR = Path("/Users/a123/.openclaw/delivery-queue")
FAILED_DIR = QUEUE_DIR / "failed"
EXPIRED_DIR = QUEUE_DIR / "expired"
LOG_FILE = Path("/Users/a123/.openclaw/logs/delivery-patrol.log")

# 时间阈值（秒）
WARNING_THRESHOLD = 30 * 60  # 30 分钟
EXPIRE_THRESHOLD = 2 * 60 * 60  # 2 小时
DELETE_THRESHOLD = 24 * 60 * 60  # 24 小时

def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)

    # 写入日志文件
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

def load_delivery_item(file_path: Path) -> Dict[str, Any]:
    """加载 delivery queue 项目"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading {file_path}: {e}")
        return {}

def get_age_seconds(item: Dict[str, Any]) -> int:
    """获取消息的年龄（秒）"""
    enqueued_at = item.get("enqueuedAt", 0)
    if not enqueued_at:
        return 0

    # enqueuedAt 是毫秒时间戳
    enqueued_time = enqueued_at / 1000
    current_time = time.time()
    return int(current_time - enqueued_time)

def format_age(seconds: int) -> str:
    """格式化年龄显示"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        return f"{seconds // 60}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分钟"

def patrol_queue():
    """巡检 delivery queue"""
    log("=" * 60)
    log("Starting delivery queue patrol")

    # 确保目录存在
    EXPIRED_DIR.mkdir(parents=True, exist_ok=True)

    # 统计
    stats = {
        "total_pending": 0,
        "total_failed": 0,
        "warnings": [],
        "expired": [],
        "deleted": []
    }

    # 检查待发送的消息
    pending_files = list(QUEUE_DIR.glob("*.json"))
    stats["total_pending"] = len(pending_files)

    for file_path in pending_files:
        item = load_delivery_item(file_path)
        if not item:
            continue

        age = get_age_seconds(item)
        item_id = item.get("id", "unknown")
        target = item.get("to", "unknown")
        retry_count = item.get("retryCount", 0)
        last_error = item.get("lastError", "")

        # 根据年龄采取不同策略
        if age >= DELETE_THRESHOLD:
            # 超过 24 小时，直接删除
            log(f"Deleting expired message {item_id} (age: {format_age(age)}, target: {target})")
            file_path.unlink()
            stats["deleted"].append({
                "id": item_id,
                "age": format_age(age),
                "target": target,
                "error": last_error
            })

        elif age >= EXPIRE_THRESHOLD:
            # 超过 2 小时，移到 expired 目录
            log(f"Moving to expired: {item_id} (age: {format_age(age)}, target: {target})")
            expired_path = EXPIRED_DIR / file_path.name
            file_path.rename(expired_path)
            stats["expired"].append({
                "id": item_id,
                "age": format_age(age),
                "target": target,
                "error": last_error
            })

        elif age >= WARNING_THRESHOLD:
            # 超过 30 分钟，记录警告
            log(f"Warning: message {item_id} pending for {format_age(age)} (target: {target}, retries: {retry_count})")
            stats["warnings"].append({
                "id": item_id,
                "age": format_age(age),
                "target": target,
                "retry_count": retry_count,
                "error": last_error
            })

    # 检查失败的消息
    if FAILED_DIR.exists():
        failed_files = list(FAILED_DIR.glob("*.json"))
        stats["total_failed"] = len(failed_files)

        # 清理超过 7 天的失败消息
        for file_path in failed_files:
            item = load_delivery_item(file_path)
            if not item:
                continue

            age = get_age_seconds(item)
            if age >= 7 * 24 * 60 * 60:  # 7 天
                item_id = item.get("id", "unknown")
                log(f"Deleting old failed message {item_id} (age: {format_age(age)})")
                file_path.unlink()

    # 输出报告
    log("-" * 60)
    log(f"Patrol summary:")
    log(f"  Total pending: {stats['total_pending']}")
    log(f"  Total failed: {stats['total_failed']}")
    log(f"  Warnings: {len(stats['warnings'])}")
    log(f"  Expired: {len(stats['expired'])}")
    log(f"  Deleted: {len(stats['deleted'])}")

    # 如果有需要关注的问题，输出详细信息
    if stats['warnings'] or stats['expired'] or stats['deleted']:
        log("-" * 60)
        log("Details:")

        for warning in stats['warnings']:
            log(f"  ⚠️  {warning['id']}: {warning['age']} (retries: {warning['retry_count']})")
            if warning['error']:
                log(f"      Error: {warning['error']}")

        for expired in stats['expired']:
            log(f"  ⏰ {expired['id']}: {expired['age']} -> moved to expired/")

        for deleted in stats['deleted']:
            log(f"  🗑️  {deleted['id']}: {deleted['age']} -> deleted")

    log("Patrol complete")
    log("=" * 60)

    # 返回是否需要通知用户
    return len(stats['warnings']) > 0 or len(stats['expired']) > 0

if __name__ == "__main__":
    try:
        needs_notification = patrol_queue()
        sys.exit(0 if not needs_notification else 1)
    except Exception as e:
        log(f"Error during patrol: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(2)
