#!/usr/bin/env python3
"""
项目进度汇报工具

用途：当用户询问"公司项目进度"、"有哪些项目"、"某品牌的任务"时，
      agent 调用此工具生成结构化的进度汇报
"""

import sys
import json
from pathlib import Path

# 添加 lib 路径
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from utils import get_projects_root, read_json

def get_all_clients_brands_projects():
    """获取所有客户、品牌、项目的概览"""

    projects_root = get_projects_root()
    result = {
        "clients": [],
        "total_clients": 0,
        "total_brands": 0,
        "total_projects": 0,
        "total_active_projects": 0
    }

    for client_dir in sorted(projects_root.iterdir()):
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue

        client_profile_path = client_dir / "_client-profile.json"
        if not client_profile_path.exists():
            continue

        client_profile = read_json(client_profile_path)
        client_name = client_profile.get("name", client_dir.name)

        client_data = {
            "name": client_name,
            "client_id": client_profile.get("client_id", ""),
            "brands": []
        }

        # 遍历品牌
        for brand_dir in sorted(client_dir.iterdir()):
            if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                continue

            brand_profile_path = brand_dir / "_brand-profile.json"
            if not brand_profile_path.exists():
                continue

            brand_profile = read_json(brand_profile_path)
            brand_name = brand_profile.get("name", brand_dir.name)

            brand_data = {
                "name": brand_name,
                "brand_id": brand_profile.get("brand_id", ""),
                "brand_tone": brand_profile.get("brand_tone", ""),
                "positioning": brand_profile.get("positioning", ""),
                "projects": []
            }

            # 遍历项目
            for project_dir in sorted(brand_dir.iterdir()):
                if not project_dir.is_dir() or project_dir.name.startswith("_"):
                    continue

                project_json_path = project_dir / "project.json"
                if not project_json_path.exists():
                    continue

                project_data = read_json(project_json_path)

                # 统计任务
                tasks_dir = project_dir / "tasks"
                task_count = 0
                active_tasks = 0
                completed_tasks = 0

                if tasks_dir.exists():
                    for task_dir in tasks_dir.iterdir():
                        if task_dir.is_dir() and not task_dir.name.startswith("_"):
                            task_json = task_dir / "task.json"
                            if task_json.exists():
                                task_count += 1
                                task_info = read_json(task_json)
                                status = task_info.get("status", "")
                                if status == "completed":
                                    completed_tasks += 1
                                elif status in ["pending", "in-progress"]:
                                    active_tasks += 1

                project_info = {
                    "name": project_data.get("campaign_name", project_dir.name),
                    "project_id": project_data.get("project_id", ""),
                    "campaign_type": project_data.get("campaign_type", ""),
                    "status": project_data.get("status", ""),
                    "lifecycle_stage": project_data.get("lifecycle_stage", ""),
                    "task_count": task_count,
                    "active_tasks": active_tasks,
                    "completed_tasks": completed_tasks,
                    "created_at": project_data.get("created_at", ""),
                    "latest_work_stage": project_data.get("latest_work_stage", "")
                }

                brand_data["projects"].append(project_info)
                result["total_projects"] += 1

                if project_data.get("status") == "active":
                    result["total_active_projects"] += 1

            if brand_data["projects"]:
                client_data["brands"].append(brand_data)
                result["total_brands"] += 1

        if client_data["brands"]:
            result["clients"].append(client_data)
            result["total_clients"] += 1

    return result


def get_brand_projects(brand_name: str):
    """获取指定品牌的所有项目和任务"""

    projects_root = get_projects_root()

    for client_dir in projects_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue

        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                continue

            brand_profile_path = brand_dir / "_brand-profile.json"
            if not brand_profile_path.exists():
                continue

            brand_profile = read_json(brand_profile_path)
            current_brand_name = brand_profile.get("name", brand_dir.name)

            if current_brand_name.lower() == brand_name.lower() or brand_dir.name.lower() == brand_name.lower():
                # 找到品牌
                result = {
                    "client": client_dir.name,
                    "brand": current_brand_name,
                    "brand_id": brand_profile.get("brand_id", ""),
                    "brand_tone": brand_profile.get("brand_tone", ""),
                    "positioning": brand_profile.get("positioning", ""),
                    "target_audience": brand_profile.get("target_audience", ""),
                    "projects": []
                }

                # 获取所有项目
                for project_dir in sorted(brand_dir.iterdir()):
                    if not project_dir.is_dir() or project_dir.name.startswith("_"):
                        continue

                    project_json_path = project_dir / "project.json"
                    if not project_json_path.exists():
                        continue

                    project_data = read_json(project_json_path)

                    # 获取所有任务
                    tasks = []
                    tasks_dir = project_dir / "tasks"

                    if tasks_dir.exists():
                        for task_dir in sorted(tasks_dir.iterdir()):
                            if task_dir.is_dir() and not task_dir.name.startswith("_"):
                                task_json = task_dir / "task.json"
                                if task_json.exists():
                                    task_info = read_json(task_json)
                                    tasks.append({
                                        "task_id": task_info.get("task_id", ""),
                                        "task_name": task_info.get("task_name", ""),
                                        "task_type": task_info.get("task_type", ""),
                                        "status": task_info.get("status", ""),
                                        "assigned_agent": task_info.get("assigned_agent", ""),
                                        "assigned_skill": task_info.get("assigned_skill", ""),
                                        "latest_version": task_info.get("latest_version", 0),
                                        "latest_work_stage": task_info.get("latest_work_stage", ""),
                                        "created_at": task_info.get("created_at", ""),
                                        "updated_at": task_info.get("updated_at", "")
                                    })

                    project_info = {
                        "project_name": project_data.get("campaign_name", project_dir.name),
                        "project_id": project_data.get("project_id", ""),
                        "campaign_type": project_data.get("campaign_type", ""),
                        "status": project_data.get("status", ""),
                        "lifecycle_stage": project_data.get("lifecycle_stage", ""),
                        "latest_work_stage": project_data.get("latest_work_stage", ""),
                        "created_at": project_data.get("created_at", ""),
                        "tasks": tasks
                    }

                    result["projects"].append(project_info)

                return result

    return {"error": f"品牌不存在: {brand_name}"}


def get_project_detail(project_id: str = None, project_name: str = None, brand_name: str = None):
    """获取指定项目的详细信息"""

    projects_root = get_projects_root()

    for client_dir in projects_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue

        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                continue

            # 如果指定了品牌名，检查是否匹配
            if brand_name:
                brand_profile_path = brand_dir / "_brand-profile.json"
                if brand_profile_path.exists():
                    brand_profile = read_json(brand_profile_path)
                    current_brand_name = brand_profile.get("name", brand_dir.name)
                    if current_brand_name.lower() != brand_name.lower() and brand_dir.name.lower() != brand_name.lower():
                        continue
                else:
                    continue

            for project_dir in brand_dir.iterdir():
                if not project_dir.is_dir() or project_dir.name.startswith("_"):
                    continue

                project_json_path = project_dir / "project.json"
                if not project_json_path.exists():
                    continue

                project_data = read_json(project_json_path)

                # 匹配项目
                match = False
                if project_id and project_data.get("project_id") == project_id:
                    match = True
                elif project_name and (project_data.get("campaign_name", "").lower() == project_name.lower() or
                                      project_dir.name.lower() == project_name.lower()):
                    match = True

                if not match:
                    continue

                # 获取品牌信息
                brand_profile_path = brand_dir / "_brand-profile.json"
                brand_info = {}
                if brand_profile_path.exists():
                    brand_profile = read_json(brand_profile_path)
                    brand_info = {
                        "name": brand_profile.get("name", ""),
                        "brand_tone": brand_profile.get("brand_tone", ""),
                        "positioning": brand_profile.get("positioning", "")
                    }

                # 获取所有任务的详细信息
                tasks = []
                tasks_dir = project_dir / "tasks"

                if tasks_dir.exists():
                    for task_dir in sorted(tasks_dir.iterdir()):
                        if task_dir.is_dir() and not task_dir.name.startswith("_"):
                            task_json = task_dir / "task.json"
                            if task_json.exists():
                                task_info = read_json(task_json)

                                # 获取版本历史
                                iterations_dir = task_dir / "iterations"
                                iterations = []
                                if iterations_dir.exists():
                                    for version_dir in sorted(iterations_dir.iterdir()):
                                        if version_dir.is_dir() and version_dir.name.startswith("v"):
                                            iter_json = version_dir / "iteration.json"
                                            if iter_json.exists():
                                                iter_data = read_json(iter_json)
                                                iterations.append({
                                                    "version": iter_data.get("version", 0),
                                                    "output_file_path": iter_data.get("output_file_path", ""),
                                                    "created_at": iter_data.get("created_at", ""),
                                                    "notes": iter_data.get("notes", "")
                                                })

                                tasks.append({
                                    "task_id": task_info.get("task_id", ""),
                                    "task_name": task_info.get("task_name", ""),
                                    "task_type": task_info.get("task_type", ""),
                                    "status": task_info.get("status", ""),
                                    "assigned_agent": task_info.get("assigned_agent", ""),
                                    "assigned_skill": task_info.get("assigned_skill", ""),
                                    "brief": task_info.get("brief", ""),
                                    "latest_version": task_info.get("latest_version", 0),
                                    "latest_work_stage": task_info.get("latest_work_stage", ""),
                                    "execution_workspace": task_info.get("execution_workspace", ""),
                                    "key_files": task_info.get("key_files", {}),
                                    "created_at": task_info.get("created_at", ""),
                                    "updated_at": task_info.get("updated_at", ""),
                                    "iterations": iterations
                                })

                return {
                    "client": client_dir.name,
                    "brand": brand_info,
                    "project": {
                        "project_id": project_data.get("project_id", ""),
                        "project_name": project_data.get("campaign_name", ""),
                        "campaign_type": project_data.get("campaign_type", ""),
                        "status": project_data.get("status", ""),
                        "lifecycle_stage": project_data.get("lifecycle_stage", ""),
                        "project_summary": project_data.get("project_summary", ""),
                        "current_goal": project_data.get("current_goal", ""),
                        "latest_work_stage": project_data.get("latest_work_stage", ""),
                        "execution_workspace": project_data.get("execution_workspace", ""),
                        "created_at": project_data.get("created_at", ""),
                        "updated_at": project_data.get("updated_at", "")
                    },
                    "tasks": tasks
                }

    return {"error": f"项目不存在"}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="项目进度汇报工具")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # overview 命令
    overview_parser = subparsers.add_parser("overview", help="获取所有项目概览")
    overview_parser.add_argument("--json", action="store_true", help="输出 JSON")

    # brand 命令
    brand_parser = subparsers.add_parser("brand", help="获取指定品牌的项目")
    brand_parser.add_argument("--name", required=True, help="品牌名称")
    brand_parser.add_argument("--json", action="store_true", help="输出 JSON")

    # project 命令
    project_parser = subparsers.add_parser("project", help="获取项目详情")
    project_parser.add_argument("--project-id", help="项目 ID")
    project_parser.add_argument("--project-name", help="项目名称")
    project_parser.add_argument("--brand-name", help="品牌名称（配合项目名使用）")
    project_parser.add_argument("--json", action="store_true", help="输出 JSON")

    args = parser.parse_args()

    if args.command == "overview":
        result = get_all_clients_brands_projects()

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📊 公司项目进度概览")
            print()
            print(f"客户总数: {result['total_clients']}")
            print(f"品牌总数: {result['total_brands']}")
            print(f"项目总数: {result['total_projects']}")
            print(f"活跃项目: {result['total_active_projects']}")
            print()
            print("=" * 80)
            print("详细列表")
            print("=" * 80)
            print()

            for client in result["clients"]:
                print(f"📁 客户: {client['name']}")
                for brand in client["brands"]:
                    print(f"  🎨 品牌: {brand['name']}")
                    if brand.get("brand_tone"):
                        print(f"     调性: {brand['brand_tone']}")
                    for project in brand["projects"]:
                        status_emoji = "🟢" if project["status"] == "active" else "⚪"
                        print(f"    {status_emoji} 项目: {project['name']}")
                        print(f"       类型: {project['campaign_type']} | 阶段: {project['lifecycle_stage']}")
                        print(f"       任务: {project['task_count']} 个 (进行中: {project['active_tasks']}, 已完成: {project['completed_tasks']})")
                        if project.get("latest_work_stage"):
                            print(f"       最新状态: {project['latest_work_stage']}")
                        print()
                print()

    elif args.command == "brand":
        result = get_brand_projects(args.name)

        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"🎨 品牌: {result['brand']}")
            print(f"客户: {result['client']}")
            if result.get("brand_tone"):
                print(f"调性: {result['brand_tone']}")
            if result.get("positioning"):
                print(f"定位: {result['positioning']}")
            print()
            print(f"项目总数: {len(result['projects'])}")
            print()

            for project in result["projects"]:
                status_emoji = "🟢" if project["status"] == "active" else "⚪"
                print(f"{status_emoji} {project['project_name']}")
                print(f"   类型: {project['campaign_type']} | 阶段: {project['lifecycle_stage']}")
                print(f"   任务数: {len(project['tasks'])}")

                if project['tasks']:
                    print(f"   任务列表:")
                    for task in project['tasks']:
                        task_emoji = {
                            "pending": "⏳",
                            "in-progress": "🔄",
                            "completed": "✅",
                            "cancelled": "❌"
                        }.get(task["status"], "❓")
                        print(f"     {task_emoji} {task['task_name']} (v{task['latest_version']})")
                        if task.get("latest_work_stage"):
                            print(f"        状态: {task['latest_work_stage']}")
                print()

    elif args.command == "project":
        if not args.project_id and not args.project_name:
            print("❌ 必须指定 --project-id 或 --project-name")
            sys.exit(1)

        result = get_project_detail(
            project_id=args.project_id,
            project_name=args.project_name,
            brand_name=args.brand_name
        )

        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            proj = result["project"]
            print(f"📦 项目: {proj['project_name']}")
            print(f"客户: {result['client']}")
            print(f"品牌: {result['brand']['name']}")
            print(f"类型: {proj['campaign_type']}")
            print(f"状态: {proj['status']} | 阶段: {proj['lifecycle_stage']}")
            if proj.get("project_summary"):
                print(f"摘要: {proj['project_summary']}")
            if proj.get("current_goal"):
                print(f"当前目标: {proj['current_goal']}")
            if proj.get("latest_work_stage"):
                print(f"最新状态: {proj['latest_work_stage']}")
            print()
            print(f"任务总数: {len(result['tasks'])}")
            print()

            for task in result["tasks"]:
                task_emoji = {
                    "pending": "⏳",
                    "in-progress": "🔄",
                    "completed": "✅",
                    "cancelled": "❌"
                }.get(task["status"], "❓")
                print(f"{task_emoji} {task['task_name']}")
                print(f"   类型: {task['task_type']} | 状态: {task['status']} | 版本: v{task['latest_version']}")
                print(f"   负责: {task['assigned_agent']} / {task['assigned_skill']}")
                if task.get("brief"):
                    print(f"   需求: {task['brief']}")
                if task.get("latest_work_stage"):
                    print(f"   最新状态: {task['latest_work_stage']}")
                if task.get("execution_workspace"):
                    print(f"   执行目录: {task['execution_workspace']}")
                if task.get("key_files"):
                    print(f"   关键文件: {len(task['key_files'])} 个")
                if task.get("iterations"):
                    print(f"   版本历史: {len(task['iterations'])} 个")
                print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
