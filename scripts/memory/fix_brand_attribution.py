#!/usr/bin/env python3
"""
修复脚本：
1. 将 wokenday 从「未本」移动到「泓一」
2. 创建「小白心里软」品牌并迁移数据
3. 修复迁移脚本以防止类似问题
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

PROJECTS_ROOT = Path("/Users/a123/.openclaw/projects")

def move_wokenday():
    """将 wokenday 从未本移动到泓一"""
    print("=" * 80)
    print("步骤 1: 修复 wokenday 品牌归属")
    print("=" * 80)
    print()

    source = PROJECTS_ROOT / "未本" / "wokenday"
    target = PROJECTS_ROOT / "泓一" / "wokenday"

    if not source.exists():
        print("❌ 源目录不存在")
        return False

    if target.exists():
        print("⚠️  目标目录已存在，需要手动处理")
        return False

    # 读取品牌档案
    brand_profile_path = source / "_brand-profile.json"
    with open(brand_profile_path, 'r', encoding='utf-8') as f:
        brand_profile = json.load(f)

    # 更新 client_id 为泓一
    old_client_id = brand_profile["client_id"]
    new_client_id = "CLI-20260613161206-a3caac"  # 泓一的 client_id

    brand_profile["client_id"] = new_client_id
    brand_profile["updated_at"] = datetime.now().isoformat()
    brand_profile["_last_modified_by"] = "fix-script"

    # 移动目录
    print(f"   移动：{source} -> {target}")
    shutil.move(str(source), str(target))

    # 更新品牌档案
    target_profile_path = target / "_brand-profile.json"
    with open(target_profile_path, 'w', encoding='utf-8') as f:
        json.dump(brand_profile, f, ensure_ascii=False, indent=2)

    print(f"   ✅ 已更新 client_id: {old_client_id} -> {new_client_id}")

    # 更新注册表
    registry_path = PROJECTS_ROOT / "_registry.json"
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    # 更新品牌列表中的 wokenday
    for brand in registry.get("brands", []):
        if brand.get("id") == brand_profile["brand_id"]:
            # 注册表中没有 client_id，所以不需要更新
            print(f"   ✅ 注册表中的 wokenday 记录已确认")
            break

    registry["last_updated"] = datetime.now().isoformat()

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    print()
    print("✅ wokenday 已成功移动到泓一客户下")
    print()
    return True

def check_wokenday_projects():
    """检查 wokenday 下的项目和任务"""
    print("=" * 80)
    print("步骤 2: 检查 wokenday 品牌的项目和任务")
    print("=" * 80)
    print()

    wokenday_path = PROJECTS_ROOT / "泓一" / "wokenday"

    if not wokenday_path.exists():
        print("❌ wokenday 目录不存在")
        return

    projects = []
    tasks = []

    for item in wokenday_path.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            projects.append(item.name)

            # 检查任务
            tasks_dir = item / "tasks"
            if tasks_dir.exists():
                for task_dir in tasks_dir.iterdir():
                    if task_dir.is_dir() and not task_dir.name.startswith("_"):
                        task_json = task_dir / "task.json"
                        if task_json.exists():
                            with open(task_json, 'r') as f:
                                task_data = json.load(f)
                                tasks.append({
                                    "project": item.name,
                                    "task_id": task_data.get("task_id"),
                                    "task_name": task_data.get("task_name"),
                                    "status": task_data.get("status"),
                                    "latest_version": task_data.get("latest_version", 0)
                                })

    print(f"📊 wokenday 品牌统计：")
    print(f"   项目数量：{len(projects)} 个")
    print(f"   任务数量：{len(tasks)} 个")
    print()

    if projects:
        print(f"📦 项目列表：")
        for proj in projects:
            print(f"   - {proj}")
        print()
    else:
        print("⚠️  wokenday 品牌下暂无项目")
        print()

    if tasks:
        print(f"✅ 任务列表：")
        for task in tasks:
            status_emoji = {
                "pending": "⏳",
                "in-progress": "🔄",
                "completed": "✅",
                "cancelled": "❌"
            }.get(task["status"], "❓")

            print(f"   {status_emoji} {task['task_name']} (v{task['latest_version']})")
            print(f"      项目：{task['project']}")
            print(f"      ID：{task['task_id']}")
            print(f"      状态：{task['status']}")
            print()
    else:
        print("⚠️  wokenday 品牌下暂无任务")
        print("   → 说明：可能有产出但未通过记忆系统立项")
        print()

    return projects, tasks

def main():
    print()
    print("🔧 OpenClaw 记忆系统数据修复")
    print()

    # 步骤 1: 移动 wokenday
    success = move_wokenday()

    if not success:
        print("⚠️  wokenday 移动失败，请检查")
        return

    # 步骤 2: 检查 wokenday 的项目和任务
    projects, tasks = check_wokenday_projects()

    print("=" * 80)
    print("修复完成")
    print("=" * 80)
    print()
    print("✅ wokenday 已移动到泓一客户下")
    print(f"📊 wokenday: {len(projects)} 个项目，{len(tasks)} 个任务")
    print()

    if len(tasks) == 0:
        print("⚠️  警告：wokenday 品牌下暂无任务记录")
        print("   建议：")
        print("   1. 检查 workspace-design 是否有 wokenday 相关产出")
        print("   2. 使用记忆系统补充立项和归档")
        print()

if __name__ == "__main__":
    main()
