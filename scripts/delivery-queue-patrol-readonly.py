#!/usr/bin/env python3
"""
Delivery Queue 定时巡检脚本（只读版本）
功能：
1. 检查 delivery-queue 中积压的消息
2. 对于超过一定时间的消息，只报告不删除
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

# 时间阈值（秒）
WARNING_THRESHOLD = 30 * 60  # 30 分钟
EXPIRE_THRESHOLD = 2 * 60 * 60  # 2 小时
DELETE_THRESHOLD = 24 * 60 * 60  # 24 小时

def load_delivery_item(file_path: Path) -> Dict[str, Any]:
    """加载 delivery queue 项目"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
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
    """巡检 delivery queue（只读）"""
    print("=" * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Delivery Queue Patrol (Read-Only)")
    print("=" * 60)

    # 统计
    stats = {
        "total_pending": 0,
        "total_failed": 0,
        "warnings": [],
        "expired": [],
        "to_delete": []
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

        # 根据年龄分类
        if age >= DELETE_THRESHOLD:
            stats["to_delete"].append({
                "id": item_id,
                "age": format_age(age),
                "target": target,
                "error": last_error
            })
        elif age >= EXPIRE_THRESHOLD:
            stats["expired"].append({
                "id": item_id,
                "age": format_age(age),
                "target": target,
                "error": last_error
            })
        elif age >= WARNING_THRESHOLD:
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

    # 输出报告
    print(f"\n📊 统计:")
    print(f"  待发送消息: {stats['total_pending']}")
    print(f"  失败消息: {stats['total_failed']}")
    print(f"  ⚠️  警告 (>30分钟): {len(stats['warnings'])}")
    print(f"  ⏰ 过期 (>2小时): {len(stats['expired'])}")
    print(f"  🗑️  建议删除 (>24小时): {len(stats['to_delete'])}")

    # 详细信息
    if stats['warnings']:
        print(f"\n⚠️  警告消息 (超过30分钟未发送):")
        for w in stats['warnings']:
            print(f"  - {w['id'][:8]}... | {w['age']} | 重试{w['retry_count']}次 | {w['target']}")
            if w['error']:
                print(f"    错误: {w['error'][:80]}")

    if stats['expired']:
        print(f"\n⏰ 过期消息 (超过2小时):")
        for e in stats['expired']:
            print(f"  - {e['id'][:8]}... | {e['age']} | {e['target']}")
            if e['error']:
                print(f"    错误: {e['error'][:80]}")

    if stats['to_delete']:
        print(f"\n🗑️  建议删除 (超过24小时):")
        for d in stats['to_delete']:
            print(f"  - {d['id'][:8]}... | {d['age']} | {d['target']}")

    print("\n" + "=" * 60)

    # 返回是否需要通知
    return len(stats['warnings']) > 0 or len(stats['expired']) > 0

if __name__ == "__main__":
    try:
        needs_notification = patrol_queue()
        sys.exit(0 if not needs_notification else 1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)
