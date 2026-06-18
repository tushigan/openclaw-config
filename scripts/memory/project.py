#!/usr/bin/env python3
"""
项目管理脚本 - OpenClaw 顶层记忆系统（第3层）

功能：
- 创建/查询/更新项目档案
- 项目生命周期管理
- 项目里程碑跟踪
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加 lib 目录到 Python 路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

from schema import ProjectProfile
from utils import (
    ensure_dir,
    get_timestamp,
    generate_id,
    load_json,
    save_json,
    get_projects_root,
    get_registry_path
)


def get_or_create_project(client_name: str, brand_name: str, project_name: str,
                          campaign_type: str = "", auto_create: bool = True) -> dict:
    """查询或创建项目（核心接口）"""
    projects_root = get_projects_root()
    registry_path = get_registry_path()

    # 加载注册表
    registry = load_json(registry_path)
    if not registry:
        registry = {"version": "2.0", "clients": [], "brands": [], "projects": [], "tasks": []}

    # 兼容旧格式（clients 是 dict）和新格式（clients 是 list）
    if isinstance(registry.get("clients"), list):
        # 新格式：转换为查找逻辑
        client_exists = any(c.get("name") == client_name for c in registry.get("clients", []))
        if not client_exists:
            if not auto_create:
                return {"error": f"客户不存在: {client_name}"}
            # 自动创建客户
            from client import create_client
            result = create_client(client_name)
            if result is None or "error" in result:
                return {"error": "客户创建失败"}
            # 重新加载注册表
            registry = load_json(registry_path)

        # 查找品牌
        brand_exists = any(b.get("name") == brand_name for b in registry.get("brands", []))
        if not brand_exists:
            if not auto_create:
                return {"error": f"品牌不存在: {brand_name}"}
            # 自动创建品牌
            from brand import create_brand
            result = create_brand(client_name, brand_name)
            if result is None or "error" in result:
                return {"error": "品牌创建失败"}
            # 重新加载注册表
            registry = load_json(registry_path)

    else:
        # 旧格式（保持兼容）
        if client_name not in registry.get("clients", {}):
            if not auto_create:
                return {"error": f"客户不存在: {client_name}"}
            from client import create_client
            result = create_client(client_name)
            if result is None or "error" in result:
                return {"error": "客户创建失败"}

        client_data = registry["clients"].get(client_name, {})
        if brand_name not in client_data.get("brands", {}):
            if not auto_create:
                return {"error": f"品牌不存在: {brand_name}"}
            from brand import create_brand
            result = create_brand(client_name, brand_name)
            if result is None or "error" in result:
                return {"error": "品牌创建失败"}
            registry = load_json(registry_path)

    # 查找项目路径（实际文件系统）
    project_path = projects_root / client_name / brand_name / project_name
    project_json_path = project_path / "project.json"

    if project_json_path.exists():
        # 项目已存在，返回
        project_data = load_json(project_json_path)
        return {
            "status": "existing",
            "project_id": project_data["project_id"],
            "project_path": str(project_path),
            "project_data": project_data
        }

    if not auto_create:
        return {"error": f"项目不存在: {project_name}"}

    # 获取客户ID和品牌ID（从文件系统读取）
    client_profile_path = projects_root / client_name / "_client-profile.json"
    brand_profile_path = projects_root / client_name / brand_name / "_brand-profile.json"

    if not client_profile_path.exists() or not brand_profile_path.exists():
        return {"error": "客户或品牌档案文件不存在"}

    client_profile = load_json(client_profile_path)
    brand_profile = load_json(brand_profile_path)

    # 创建新项目
    project_id = generate_id("PROJECT")
    timestamp = get_timestamp()

    profile = ProjectProfile(
        project_id=project_id,
        brand_id=brand_profile["brand_id"],
        client_id=client_profile["client_id"],
        campaign_name=project_name,
        campaign_type=campaign_type,
        status="active",
        lifecycle_stage="需求收集",
        created_at=timestamp,
        updated_at=timestamp,
        _last_modified_by="system"
    )

    # 创建项目目录结构
    ensure_dir(project_path)
    ensure_dir(project_path / "materials")
    ensure_dir(project_path / "materials" / "research")
    ensure_dir(project_path / "materials" / "reference")
    ensure_dir(project_path / "materials" / "client-assets")
    ensure_dir(project_path / "outputs")
    ensure_dir(project_path / "outputs" / "copy")
    ensure_dir(project_path / "outputs" / "design")
    ensure_dir(project_path / "outputs" / "final")
    ensure_dir(project_path / "tasks")

    # 保存项目档案
    save_json(project_json_path, profile.to_dict())

    # 创建任务注册表
    tasks_registry_path = project_path / "tasks" / "_tasks-registry.json"
    save_json(tasks_registry_path, {
        "project_id": project_id,
        "tasks": {},
        "created_at": timestamp,
        "updated_at": timestamp
    })

    # 更新全局注册表（新格式）
    registry = load_json(registry_path)
    if "projects" not in registry:
        registry["projects"] = []

    # 检查项目是否已在注册表中
    existing_proj = next((p for p in registry["projects"] if p.get("id") == project_id), None)
    if not existing_proj:
        registry["projects"].append({
            "id": project_id,
            "name": project_name,
            "brand_name": brand_name,
            "client_name": client_name,
            "status": "active",
            "created_at": timestamp
        })
        registry["last_updated"] = timestamp
        save_json(registry_path, registry)

    return {
        "status": "created",
        "project_id": project_id,
        "project_path": str(project_path),
        "project_data": profile.to_dict()
    }


def update_project(project_id: str, updates: dict) -> dict:
    """更新项目信息"""
    projects_root = get_projects_root()
    registry_path = get_registry_path()
    registry = load_json(registry_path)

    # 查找项目路径（遍历文件系统）
    project_path = None
    if isinstance(registry.get("clients"), list):
        # 新格式：遍历文件系统
        for client_dir in projects_root.iterdir():
            if not client_dir.is_dir() or client_dir.name.startswith("_"):
                continue
            for brand_dir in client_dir.iterdir():
                if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                    continue
                for proj_dir in brand_dir.iterdir():
                    if not proj_dir.is_dir():
                        continue
                    project_json = proj_dir / "project.json"
                    if project_json.exists():
                        proj_data = load_json(project_json)
                        if proj_data and proj_data.get("project_id") == project_id:
                            project_path = proj_dir
                            break
                if project_path:
                    break
            if project_path:
                break
    else:
        # 旧格式
        for client_name, client_data in registry.get("clients", {}).items():
            for brand_name, brand_data in client_data.get("brands", {}).items():
                for proj_name, proj_data in brand_data.get("projects", {}).items():
                    if proj_data.get("project_id") == project_id:
                        project_path = projects_root / client_name / brand_name / proj_name
                        break

    if not project_path or not project_path.exists():
        return {"error": f"项目不存在: {project_id}"}

    project_json_path = project_path / "project.json"
    project_data = load_json(project_json_path)

    # 更新字段
    for key, value in updates.items():
        if key in project_data and value is not None:
            project_data[key] = value

    project_data["updated_at"] = get_timestamp()
    save_json(project_json_path, project_data)

    return {
        "status": "updated",
        "project_id": project_id,
        "project_data": project_data
    }


def get_project(project_id: str = None, client_name: str = None,
                brand_name: str = None, project_name: str = None) -> dict:
    """查询项目信息"""
    projects_root = get_projects_root()
    registry_path = get_registry_path()
    registry = load_json(registry_path)

    if project_id:
        # 通过 project_id 查找
        # 兼容新格式（list）和旧格式（dict）
        if isinstance(registry.get("clients"), list):
            # 新格式：遍历文件系统查找
            for client_dir in projects_root.iterdir():
                if not client_dir.is_dir() or client_dir.name.startswith("_"):
                    continue
                for brand_dir in client_dir.iterdir():
                    if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                        continue
                    for proj_dir in brand_dir.iterdir():
                        if not proj_dir.is_dir():
                            continue
                        project_json = proj_dir / "project.json"
                        if project_json.exists():
                            proj_data = load_json(project_json)
                            if proj_data and proj_data.get("project_id") == project_id:
                                return proj_data
        else:
            # 旧格式（保持兼容）
            for c_name, client_data in registry.get("clients", {}).items():
                for b_name, brand_data in client_data.get("brands", {}).items():
                    for proj_name, proj_data in brand_data.get("projects", {}).items():
                        if proj_data.get("project_id") == project_id:
                            project_path = projects_root / c_name / b_name / proj_name
                            project_json = project_path / "project.json"
                            if project_json.exists():
                                return load_json(project_json)
        return {"error": f"项目不存在: {project_id}"}

    elif client_name and brand_name and project_name:
        # 通过名称查找
        project_path = projects_root / client_name / brand_name / project_name
        project_json = project_path / "project.json"
        if project_json.exists():
            return load_json(project_json)
        return {"error": f"项目不存在: {client_name}/{brand_name}/{project_name}"}

    else:
        return {"error": "必须提供 project_id 或 (client_name, brand_name, project_name)"}


def list_projects(client_name: str = None, brand_name: str = None,
                  active_only: bool = False) -> list:
    """列出项目"""
    projects_root = get_projects_root()
    registry_path = get_registry_path()
    registry = load_json(registry_path)

    projects = []

    # 兼容新格式（list）和旧格式（dict）
    if isinstance(registry.get("clients"), list):
        # 新格式：遍历文件系统
        for client_dir in projects_root.iterdir():
            if not client_dir.is_dir() or client_dir.name.startswith("_"):
                continue

            c_name = client_dir.name
            if client_name and c_name != client_name:
                continue

            for brand_dir in client_dir.iterdir():
                if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                    continue

                b_name = brand_dir.name
                if brand_name and b_name != brand_name:
                    continue

                for proj_dir in brand_dir.iterdir():
                    if not proj_dir.is_dir():
                        continue

                    project_json = proj_dir / "project.json"
                    if project_json.exists():
                        project_info = load_json(project_json)
                        if project_info:
                            if active_only and project_info.get("status") != "active":
                                continue

                            projects.append({
                                "client": c_name,
                                "brand": b_name,
                                "project": proj_dir.name,
                                "project_id": project_info["project_id"],
                                "campaign_type": project_info.get("campaign_type", ""),
                                "status": project_info.get("status", ""),
                                "lifecycle_stage": project_info.get("lifecycle_stage", ""),
                                "created_at": project_info.get("created_at", ""),
                                "path": str(proj_dir)
                            })
    else:
        # 旧格式（保持兼容）
        for c_name, client_data in registry.get("clients", {}).items():
            if client_name and c_name != client_name:
                continue

            for b_name, brand_data in client_data.get("brands", {}).items():
                if brand_name and b_name != brand_name:
                    continue

                for proj_name, proj_data in brand_data.get("projects", {}).items():
                    if active_only and proj_data.get("status") != "active":
                        continue

                    project_path = projects_root / c_name / b_name / proj_name
                    project_json = project_path / "project.json"

                    if project_json.exists():
                        project_info = load_json(project_json)
                        projects.append({
                            "client": c_name,
                            "brand": b_name,
                            "project": proj_name,
                            "project_id": project_info["project_id"],
                            "campaign_type": project_info.get("campaign_type", ""),
                            "status": project_info.get("status", ""),
                            "lifecycle_stage": project_info.get("lifecycle_stage", ""),
                            "created_at": project_info.get("created_at", ""),
                            "path": str(project_path)
                        })

    return projects


def update_lifecycle_stage(project_id: str, new_stage: str) -> dict:
    """更新项目生命周期阶段"""
    return update_project(project_id, {
        "lifecycle_stage": new_stage,
        "milestones": None  # 保持原有 milestones，只更新 stage
    })


def update_execution_workspace(project_id: str, execution_workspace: str,
                               work_stage: str = "", index_path: str = "",
                               readme_path: str = "") -> dict:
    """更新项目的执行目录索引

    Args:
        project_id: 项目ID
        execution_workspace: 实际执行工作目录路径
        work_stage: 当前工作阶段
        index_path: 执行索引文件路径
        readme_path: 执行索引说明文档路径
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

    return update_project(project_id, updates)


def add_milestone(project_id: str, milestone_name: str,
                  milestone_status: str = "pending") -> dict:
    """添加项目里程碑"""
    project_data = get_project(project_id=project_id)
    if "error" in project_data:
        return project_data

    milestones = project_data.get("milestones", [])
    milestones.append({
        "name": milestone_name,
        "status": milestone_status,
        "timestamp": get_timestamp()
    })

    return update_project(project_id, {"milestones": milestones})


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 项目管理")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # get-or-create 命令
    create_parser = subparsers.add_parser("get-or-create", help="查询或创建项目")
    create_parser.add_argument("--client", required=True, help="客户名称")
    create_parser.add_argument("--brand", required=True, help="品牌名称")
    create_parser.add_argument("--project", required=True, help="项目名称")
    create_parser.add_argument("--campaign-type", default="", help="项目类型")
    create_parser.add_argument("--no-auto-create", action="store_true",
                              help="禁止自动创建（仅查询）")
    create_parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    # get 命令
    get_parser = subparsers.add_parser("get", help="查询项目信息")
    get_parser.add_argument("--project-id", help="项目 ID")
    get_parser.add_argument("--client", help="客户名称")
    get_parser.add_argument("--brand", help="品牌名称")
    get_parser.add_argument("--project", help="项目名称")
    get_parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出项目")
    list_parser.add_argument("--client", help="筛选客户")
    list_parser.add_argument("--brand", help="筛选品牌")
    list_parser.add_argument("--active", action="store_true", help="仅显示活跃项目")
    list_parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    # update-stage 命令
    stage_parser = subparsers.add_parser("update-stage", help="更新生命周期阶段")
    stage_parser.add_argument("--project-id", required=True, help="项目 ID")
    stage_parser.add_argument("--stage", required=True, help="新阶段")
    stage_parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    # add-milestone 命令
    milestone_parser = subparsers.add_parser("add-milestone", help="添加里程碑")
    milestone_parser.add_argument("--project-id", required=True, help="项目 ID")
    milestone_parser.add_argument("--name", required=True, help="里程碑名称")
    milestone_parser.add_argument("--status", default="pending", help="状态")
    milestone_parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    # update-execution 命令
    execution_parser = subparsers.add_parser("update-execution", help="更新执行目录索引")
    execution_parser.add_argument("--project-id", required=True, help="项目 ID")
    execution_parser.add_argument("--execution-workspace", required=True, help="执行工作目录路径")
    execution_parser.add_argument("--work-stage", default="", help="当前工作阶段")
    execution_parser.add_argument("--index-path", default="", help="索引文件路径")
    execution_parser.add_argument("--readme-path", default="", help="README 路径")
    execution_parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    if args.command == "get-or-create":
        result = get_or_create_project(
            args.client,
            args.brand,
            args.project,
            args.campaign_type,
            not args.no_auto_create
        )

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)

            status_emoji = "✅" if result["status"] == "created" else "📁"
            status_text = "已创建" if result["status"] == "created" else "已存在"

            print(f"{status_emoji} 项目{status_text}: {result['project_id']}")
            print(f"路径: {result['project_path']}")

    elif args.command == "get":
        result = get_project(
            project_id=args.project_id,
            client_name=args.client,
            brand_name=args.brand,
            project_name=args.project
        )

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)

            print(f"项目 ID: {result['project_id']}")
            print(f"项目名称: {result['campaign_name']}")
            print(f"项目类型: {result.get('campaign_type', '')}")
            print(f"状态: {result.get('status', '')}")
            print(f"阶段: {result.get('lifecycle_stage', '')}")

    elif args.command == "list":
        projects = list_projects(
            client_name=args.client,
            brand_name=args.brand,
            active_only=args.active
        )

        if args.json:
            print(json.dumps(projects, ensure_ascii=False, indent=2))
        else:
            print(f"共找到 {len(projects)} 个项目:\n")
            for proj in projects:
                status_emoji = "🟢" if proj["status"] == "active" else "⚪"
                print(f"{status_emoji} {proj['client']} / {proj['brand']} / {proj['project']}")
                print(f"   ID: {proj['project_id']} | 类型: {proj['campaign_type']} | 阶段: {proj['lifecycle_stage']}")
                print()

    elif args.command == "update-stage":
        result = update_lifecycle_stage(args.project_id, args.stage)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)
            print(f"✅ 项目阶段已更新: {args.stage}")

    elif args.command == "add-milestone":
        result = add_milestone(args.project_id, args.name, args.status)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "error" in result:
                print(f"❌ {result['error']}")
                sys.exit(1)
            print(f"✅ 里程碑已添加: {args.name}")

    elif args.command == "update-execution":
        result = update_execution_workspace(
            args.project_id,
            args.execution_workspace,
            args.work_stage,
            args.index_path,
            args.readme_path
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

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
