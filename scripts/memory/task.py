#!/usr/bin/env python3
"""
任务管理脚本 - OpenClaw 顶层记忆系统（第4层+第5层）

功能：
- 创建/查询/更新任务档案（第4层）
- 保存任务产出（第5层迭代版本）
- 自动版本管理
- 文件过期管理
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# 添加 lib 目录到 Python 路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

from schema import TaskProfile, IterationMetadata, get_file_type, EXPIRY_RULES
from utils import (
    ensure_dir,
    get_timestamp,
    generate_id,
    load_json,
    save_json,
    get_projects_root,
)


def create_task(project_id: str, task_name: str, task_type: str = "",
                assigned_agent: str = "", assigned_skill: str = "",
                brief: str = "", requirements: dict = None) -> dict:
    """创建新任务"""
    projects_root = get_projects_root()

    # 查找项目路径
    from project import get_project
    project_data = get_project(project_id=project_id)
    if "error" in project_data:
        return project_data

    # 构建项目路径
    # 从 project_data 中获取路径信息
    client_id = project_data["client_id"]
    brand_id = project_data["brand_id"]
    campaign_name = project_data["campaign_name"]

    # 需要从注册表或文件系统找到实际的客户/品牌名称
    from utils import get_registry_path
    registry = load_json(get_registry_path())

    client_name = None
    brand_name = None

    # 兼容新格式（list）
    if isinstance(registry.get("clients"), list):
        # 遍历文件系统查找
        for client_dir in projects_root.iterdir():
            if not client_dir.is_dir() or client_dir.name.startswith("_"):
                continue
            client_profile_path = client_dir / "_client-profile.json"
            if client_profile_path.exists():
                client_profile = load_json(client_profile_path)
                if client_profile and client_profile.get("client_id") == client_id:
                    client_name = client_dir.name
                    # 查找品牌
                    for brand_dir in client_dir.iterdir():
                        if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                            continue
                        brand_profile_path = brand_dir / "_brand-profile.json"
                        if brand_profile_path.exists():
                            brand_profile = load_json(brand_profile_path)
                            if brand_profile and brand_profile.get("brand_id") == brand_id:
                                brand_name = brand_dir.name
                                break
                    break
    else:
        # 旧格式兼容
        for c_name, c_data in registry.get("clients", {}).items():
            if c_data.get("client_id") == client_id:
                client_name = c_name
                for b_name, b_data in c_data.get("brands", {}).items():
                    if b_data.get("brand_id") == brand_id:
                        brand_name = b_name
                        break
                break

    if not client_name or not brand_name:
        return {"error": f"无法找到项目的客户/品牌信息: {project_id}"}

    project_path = projects_root / client_name / brand_name / campaign_name
    tasks_dir = project_path / "tasks"
    tasks_registry_path = tasks_dir / "_tasks-registry.json"

    # 加载任务注册表
    tasks_registry = load_json(tasks_registry_path)
    if not tasks_registry:
        tasks_registry = {
            "project_id": project_id,
            "tasks": {},
            "created_at": get_timestamp(),
            "updated_at": get_timestamp()
        }

    # 生成任务 ID
    task_id = generate_id("TASK")
    timestamp = get_timestamp()

    # 创建任务档案
    task_profile = TaskProfile(
        task_id=task_id,
        project_id=project_id,
        task_name=task_name,
        task_type=task_type,
        assigned_agent=assigned_agent,
        assigned_skill=assigned_skill,
        status="pending",
        brief=brief,
        requirements=requirements or {},
        created_at=timestamp,
        updated_at=timestamp,
        latest_version=0,
        _last_modified_by=assigned_agent or "system"
    )

    # 创建任务目录
    task_dir = tasks_dir / task_id
    ensure_dir(task_dir)
    ensure_dir(task_dir / "iterations")

    # 保存任务档案
    task_json_path = task_dir / "task.json"
    save_json(task_json_path, task_profile.to_dict())

    # 更新任务注册表
    tasks_registry["tasks"][task_id] = {
        "task_name": task_name,
        "task_type": task_type,
        "status": "pending",
        "created_at": timestamp
    }
    tasks_registry["updated_at"] = timestamp
    save_json(tasks_registry_path, tasks_registry)

    return {
        "status": "created",
        "task_id": task_id,
        "task_path": str(task_dir),
        "task_data": task_profile.to_dict()
    }


def get_task(task_id: str) -> dict:
    """查询任务信息"""
    projects_root = get_projects_root()

    # 遍历所有项目查找任务
    for client_dir in projects_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue

        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                continue

            for project_dir in brand_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                task_dir = project_dir / "tasks" / task_id
                task_json = task_dir / "task.json"

                if task_json.exists():
                    return load_json(task_json)

    return {"error": f"任务不存在: {task_id}"}


def update_task(task_id: str, updates: dict) -> dict:
    """更新任务信息"""
    task_data = get_task(task_id)
    if "error" in task_data:
        return task_data

    # 找到任务路径
    projects_root = get_projects_root()
    task_json_path = None

    for client_dir in projects_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue

        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                continue

            for project_dir in brand_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                task_dir = project_dir / "tasks" / task_id
                task_json = task_dir / "task.json"

                if task_json.exists():
                    task_json_path = task_json
                    break

    if not task_json_path:
        return {"error": f"任务文件不存在: {task_id}"}

    # 更新字段
    for key, value in updates.items():
        if key in task_data and value is not None:
            task_data[key] = value
        elif key not in task_data and value is not None:
            # 允许添加新字段（如执行目录索引相关字段）
            task_data[key] = value

    task_data["updated_at"] = get_timestamp()
    save_json(task_json_path, task_data)

    return {
        "status": "updated",
        "task_id": task_id,
        "task_data": task_data
    }


def update_execution_workspace(task_id: str, execution_workspace: str,
                               work_stage: str = "", index_path: str = "",
                               readme_path: str = "", key_files: dict = None) -> dict:
    """更新任务的执行目录索引

    Args:
        task_id: 任务ID
        execution_workspace: 实际执行工作目录路径
        work_stage: 当前工作阶段
        index_path: 执行索引文件路径
        readme_path: 执行索引说明文档路径
        key_files: 关键文件路径字典 {name: path}
    """
    updates = {
        "execution_workspace": execution_workspace,
    }

    if work_stage:
        updates["latest_work_stage"] = work_stage

    if index_path:
        updates["execution_index_path"] = index_path

    if readme_path:
        updates["execution_readme_path"] = readme_path

    if key_files:
        updates["key_files"] = key_files

    return update_task(task_id, updates)


def save_output(task_id: str, output_file: str, version_note: str = "",
                expire_days: int = None, prompt: str = "", model_used: str = "",
                generation_params: dict = None) -> dict:
    """保存任务产出（自动创建新版本）"""
    task_data = get_task(task_id)
    if "error" in task_data:
        return task_data

    output_path = Path(output_file)
    if not output_path.exists():
        return {"error": f"产出文件不存在: {output_file}"}

    # 找到任务目录
    projects_root = get_projects_root()
    task_dir = None

    for client_dir in projects_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue

        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                continue

            for project_dir in brand_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                t_dir = project_dir / "tasks" / task_id
                if t_dir.exists():
                    task_dir = t_dir
                    break

    if not task_dir:
        return {"error": f"任务目录不存在: {task_id}"}

    # 获取下一个版本号
    next_version = task_data.get("latest_version", 0) + 1

    # 创建版本目录
    version_dir = task_dir / "iterations" / f"v{next_version}"
    ensure_dir(version_dir)

    # 复制产出文件到版本目录
    file_ext = output_path.suffix
    target_filename = f"{task_data['task_name']}_v{next_version}{file_ext}"
    target_path = version_dir / target_filename

    shutil.copy2(output_path, target_path)

    # 获取文件信息
    file_type = get_file_type(str(output_path))
    file_size = output_path.stat().st_size

    # 计算过期时间
    timestamp = get_timestamp()
    expire_at = ""

    if expire_days is not None:
        expiry_days = expire_days
    else:
        expiry_days = EXPIRY_RULES.get(file_type)

    if expiry_days:
        expire_date = datetime.now() + timedelta(days=expiry_days)
        expire_at = expire_date.isoformat()

    # 创建迭代元信息
    iteration_id = generate_id("ITER")
    iteration = IterationMetadata(
        iteration_id=iteration_id,
        task_id=task_id,
        version=next_version,
        output_file_path=str(target_path),
        output_file_type=file_type,
        file_size_bytes=file_size,
        created_at=timestamp,
        created_by=task_data.get("assigned_agent", "unknown"),
        expire_at=expire_at,
        is_expired=False,
        prompt=prompt,
        model_used=model_used,
        generation_params=generation_params or {},
        notes=version_note
    )

    # 保存迭代元信息
    iteration_json = version_dir / "metadata.json"
    save_json(iteration_json, iteration.to_dict())

    # 更新任务的最新版本号
    update_task(task_id, {
        "latest_version": next_version,
        "status": "completed"
    })

    return {
        "status": "saved",
        "task_id": task_id,
        "version": next_version,
        "file_path": str(target_path),
        "expire_at": expire_at,
        "iteration_data": iteration.to_dict()
    }


def list_tasks(project_id: str, status: str = None) -> list:
    """列出项目的所有任务"""
    from project import get_project
    project_data = get_project(project_id=project_id)
    if "error" in project_data:
        return []

    # 构建任务注册表路径
    projects_root = get_projects_root()
    from utils import get_registry_path
    registry = load_json(get_registry_path())

    client_name = None
    brand_name = None

    # 兼容新格式（list）
    if isinstance(registry.get("clients"), list):
        # 遍历文件系统查找
        for client_dir in projects_root.iterdir():
            if not client_dir.is_dir() or client_dir.name.startswith("_"):
                continue
            client_profile_path = client_dir / "_client-profile.json"
            if client_profile_path.exists():
                client_profile = load_json(client_profile_path)
                if client_profile and client_profile.get("client_id") == project_data["client_id"]:
                    client_name = client_dir.name
                    for brand_dir in client_dir.iterdir():
                        if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                            continue
                        brand_profile_path = brand_dir / "_brand-profile.json"
                        if brand_profile_path.exists():
                            brand_profile = load_json(brand_profile_path)
                            if brand_profile and brand_profile.get("brand_id") == project_data["brand_id"]:
                                brand_name = brand_dir.name
                                break
                    break
    else:
        # 旧格式兼容
        for c_name, c_data in registry.get("clients", {}).items():
            if c_data.get("client_id") == project_data["client_id"]:
                client_name = c_name
                for b_name, b_data in c_data.get("brands", {}).items():
                    if b_data.get("brand_id") == project_data["brand_id"]:
                        brand_name = b_name
                        break
                break

    if not client_name or not brand_name:
        return []

    project_path = projects_root / client_name / brand_name / project_data["campaign_name"]
    tasks_registry_path = project_path / "tasks" / "_tasks-registry.json"

    if not tasks_registry_path.exists():
        return []

    tasks_registry = load_json(tasks_registry_path)
    tasks = []

    for task_id, task_info in tasks_registry.get("tasks", {}).items():
        if status and task_info.get("status") != status:
            continue

        task_dir = project_path / "tasks" / task_id
        task_json = task_dir / "task.json"

        if task_json.exists():
            task_data = load_json(task_json)
            tasks.append(task_data)

    return tasks


def list_iterations(task_id: str) -> list:
    """列出任务的所有版本"""
    task_data = get_task(task_id)
    if "error" in task_data:
        return []

    # 找到任务目录
    projects_root = get_projects_root()
    task_dir = None

    for client_dir in projects_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue

        for brand_dir in client_dir.iterdir():
            if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                continue

            for project_dir in brand_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                t_dir = project_dir / "tasks" / task_id
                if t_dir.exists():
                    task_dir = t_dir
                    break

    if not task_dir:
        return []

    iterations_dir = task_dir / "iterations"
    if not iterations_dir.exists():
        return []

    iterations = []
    for version_dir in sorted(iterations_dir.iterdir()):
        if not version_dir.is_dir():
            continue

        metadata_json = version_dir / "metadata.json"
        if metadata_json.exists():
            iteration_data = load_json(metadata_json)
            iterations.append(iteration_data)

    return iterations


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 任务管理")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # create 命令
    create_parser = subparsers.add_parser("create", help="创建任务")
    create_parser.add_argument("--project-id", required=True, help="项目 ID")
    create_parser.add_argument("--name", required=True, help="任务名称")
    create_parser.add_argument("--type", default="", help="任务类型")
    create_parser.add_argument("--agent", default="", help="指派 agent")
    create_parser.add_argument("--skill", default="", help="调用的 skill")
    create_parser.add_argument("--brief", default="", help="任务简介")
    create_parser.add_argument("--json", action="store_true", help="输出 JSON")

    # get 命令
    get_parser = subparsers.add_parser("get", help="查询任务")
    get_parser.add_argument("--task-id", required=True, help="任务 ID")
    get_parser.add_argument("--json", action="store_true", help="输出 JSON")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出任务")
    list_parser.add_argument("--project-id", required=True, help="项目 ID")
    list_parser.add_argument("--status", help="筛选状态")
    list_parser.add_argument("--json", action="store_true", help="输出 JSON")

    # save-output 命令
    save_parser = subparsers.add_parser("save-output", help="保存产出")
    save_parser.add_argument("--task-id", required=True, help="任务 ID")
    save_parser.add_argument("--file", required=True, help="产出文件路径")
    save_parser.add_argument("--note", default="", help="版本说明")
    save_parser.add_argument("--expire-days", type=int, help="过期天数")
    save_parser.add_argument("--prompt", default="", help="生成 prompt")
    save_parser.add_argument("--model", default="", help="使用的模型")
    save_parser.add_argument("--json", action="store_true", help="输出 JSON")

    # list-iterations 命令
    iter_parser = subparsers.add_parser("list-iterations", help="列出版本")
    iter_parser.add_argument("--task-id", required=True, help="任务 ID")
    iter_parser.add_argument("--json", action="store_true", help="输出 JSON")

    # update-status 命令
    status_parser = subparsers.add_parser("update-status", help="更新任务状态")
    status_parser.add_argument("--task-id", required=True, help="任务 ID")
    status_parser.add_argument("--status", required=True,
                              choices=["pending", "in-progress", "completed", "cancelled"],
                              help="新状态")
    status_parser.add_argument("--json", action="store_true", help="输出 JSON")

    # update-execution 命令
    execution_parser = subparsers.add_parser("update-execution", help="更新执行目录索引")
    execution_parser.add_argument("--task-id", required=True, help="任务 ID")
    execution_parser.add_argument("--execution-workspace", required=True, help="执行工作目录路径")
    execution_parser.add_argument("--work-stage", default="", help="当前工作阶段")
    execution_parser.add_argument("--index-path", default="", help="索引文件路径")
    execution_parser.add_argument("--readme-path", default="", help="README 路径")
    execution_parser.add_argument("--key-file", action="append", nargs=2, metavar=("NAME", "PATH"),
                                 help="关键文件 (可多次使用)")
    execution_parser.add_argument("--json", action="store_true", help="输出 JSON")

    args = parser.parse_args()

    if args.command == "create":
        result = create_task(
            args.project_id,
            args.name,
            args.type,
            args.agent,
            args.skill,
            args.brief
        )

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)
            print(f"✅ 任务已创建: {result['task_id']}")
            print(f"路径: {result['task_path']}")

    elif args.command == "get":
        result = get_task(args.task_id)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)

            print(f"任务 ID: {result['task_id']}")
            print(f"任务名称: {result['task_name']}")
            print(f"任务类型: {result.get('task_type', '')}")
            print(f"状态: {result.get('status', '')}")
            print(f"当前版本: v{result.get('latest_version', 0)}")

    elif args.command == "list":
        tasks = list_tasks(args.project_id, args.status)

        if args.json:
            print(json.dumps(tasks, ensure_ascii=False, indent=2))
        else:
            print(f"共找到 {len(tasks)} 个任务:\n")
            for task in tasks:
                status_emoji = {
                    "pending": "⏳",
                    "in-progress": "🔄",
                    "completed": "✅",
                    "cancelled": "❌"
                }.get(task["status"], "❓")

                print(f"{status_emoji} {task['task_name']} ({task['task_id']})")
                print(f"   类型: {task.get('task_type', '')} | 版本: v{task.get('latest_version', 0)}")
                print()

    elif args.command == "save-output":
        result = save_output(
            args.task_id,
            args.file,
            args.note,
            args.expire_days,
            args.prompt,
            args.model
        )

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)

            print(f"✅ 产出已保存: v{result['version']}")
            print(f"文件路径: {result['file_path']}")
            if result['expire_at']:
                print(f"过期时间: {result['expire_at']}")

    elif args.command == "list-iterations":
        iterations = list_iterations(args.task_id)

        if args.json:
            print(json.dumps(iterations, ensure_ascii=False, indent=2))
        else:
            print(f"共找到 {len(iterations)} 个版本:\n")
            for it in iterations:
                print(f"v{it['version']} - {it['created_at']}")
                print(f"   文件: {it['output_file_path']}")
                if it.get('notes'):
                    print(f"   说明: {it['notes']}")
                print()

    elif args.command == "update-status":
        result = update_task(args.task_id, {"status": args.status})

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)
            print(f"✅ 任务状态已更新: {args.status}")

    elif args.command == "update-execution":
        # 处理关键文件参数
        key_files = {}
        if args.key_file:
            for name, path in args.key_file:
                key_files[name] = path

        result = update_execution_workspace(
            args.task_id,
            args.execution_workspace,
            args.work_stage,
            args.index_path,
            args.readme_path,
            key_files if key_files else None
        )

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)
            print(f"✅ 执行目录索引已更新")
            print(f"   执行目录: {args.execution_workspace}")
            if args.work_stage:
                print(f"   工作阶段: {args.work_stage}")
            if key_files:
                print(f"   关键文件: {len(key_files)} 个")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
