from __future__ import annotations

from copy import deepcopy
from typing import Any


class QuoteValidationError(ValueError):
    """Raised when quote content is not ready for formal output generation."""


ALLOWED_CASE_TYPES = {"散案", "项目案", "全案"}
ALLOWED_CATALOG_STATUSES = {"matched", "pending_review"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _list_of_text(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, list):
        return [_text(value) for value in values if _text(value)]
    text = _text(values)
    return [text] if text else []


def _case_type(value: Any) -> str:
    text = _text(value)
    if not text:
        return "项目案"
    if text not in ALLOWED_CASE_TYPES:
        allowed = "、".join(sorted(ALLOWED_CASE_TYPES))
        raise QuoteValidationError(f"不支持的案子类型：{text}。只允许：{allowed}。")
    return text


def _normalized_annual_context(value: Any) -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    return {
        "business_goal": _text(source.get("business_goal")),
        "service_period": _text(source.get("service_period")),
        "service_boundary": _text(source.get("service_boundary")),
        "core_service_modules": _list_of_text(source.get("core_service_modules")),
        "priority": _text(source.get("priority")),
    }


def _normalized_catalog_candidate(
    candidate: Any,
    stage_name: str,
    project_name: str,
    task_name: str,
    descriptions: list[str],
) -> dict[str, Any]:
    source = candidate if isinstance(candidate, dict) else {}
    return {
        "proposed_level_1_module": _text(source.get("proposed_level_1_module")),
        "proposed_level_2_module": _text(source.get("proposed_level_2_module")),
        "proposed_project": _text(source.get("proposed_project")),
        "proposed_task": _text(source.get("proposed_task")) or task_name,
        "description": _text(source.get("description")) or "；".join(descriptions),
        "reason": _text(source.get("reason")),
        "source_stage_name": stage_name,
        "source_project_name": project_name,
        "source_task_name": task_name,
    }


def _required_stage_count(case_type: str) -> int:
    if case_type == "项目案":
        return 2
    return 1


def _required_project_count(case_type: str) -> int:
    if case_type in {"散案", "项目案"}:
        return 2
    return 1


def _required_task_count(case_type: str) -> int:
    if case_type in {"散案", "项目案"}:
        return 2
    return 1


def validate_quote_content(content: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(content)
    case_type = _case_type(normalized.get("case_type"))
    annual_context = _normalized_annual_context(normalized.get("annual_context"))
    pending_catalog_items: list[dict[str, Any]] = []
    stages = normalized.get("stages") or []

    if not stages:
        raise QuoteValidationError("当前报价还没有按“阶段 > 项目 > 任务”整理，不能直接生成正式报价。")

    if case_type == "全案":
        required_keys = [
            "business_goal",
            "service_period",
            "service_boundary",
            "priority",
        ]
        missing = [key for key in required_keys if not annual_context.get(key)]
        if not annual_context["core_service_modules"]:
            missing.append("core_service_modules")
        if missing:
            missing_text = "、".join(missing)
            raise QuoteValidationError(f"全案缺少完整年度上下文：{missing_text}。")

    required_stage_count = _required_stage_count(case_type)
    if len(stages) < required_stage_count:
        if case_type == "项目案":
            raise QuoteValidationError("项目案至少需要 2 个阶段，拆分不够，请先确认。")
        raise QuoteValidationError("当前报价结构拆分不够，请先确认。")

    for stage in stages:
        stage_name = _text(stage.get("stage_name")) or "未命名阶段"
        projects = stage.get("projects") or []
        required_project_count = _required_project_count(case_type)
        if len(projects) < required_project_count:
            if case_type == "全案":
                raise QuoteValidationError(
                    f"服务模块“{stage_name}”至少需要 1 个项目，不能是空壳。"
                )
            raise QuoteValidationError(
                f"阶段“{stage_name}”至少需要 {required_project_count} 个项目，拆分不够，请先确认。"
            )

        stage["stage_name"] = stage_name
        stage["stage_price"] = _text(stage.get("stage_price"))
        stage["stage_duration"] = _text(stage.get("stage_duration"))
        stage["stage_deliverables"] = _list_of_text(stage.get("stage_deliverables"))

        for project in projects:
            project_name = _text(project.get("project_name")) or "未命名项目"
            tasks = project.get("tasks") or []
            required_task_count = _required_task_count(case_type)
            if len(tasks) < required_task_count:
                if case_type == "全案":
                    raise QuoteValidationError(
                        f"项目“{project_name}”至少需要 1 个任务，不能是空壳。"
                    )
                raise QuoteValidationError(
                    f"项目“{project_name}”至少需要 {required_task_count} 个任务，拆分不够，请先确认。"
                )

            project["project_name"] = project_name
            project["project_deliverables"] = _list_of_text(project.get("project_deliverables"))
            project["service_catalog_refs"] = _list_of_text(project.get("service_catalog_refs"))

            for task in tasks:
                task_name = _text(task.get("task_name")) or "未命名任务"
                descriptions = _list_of_text(task.get("description_bullets"))
                if not descriptions:
                    raise QuoteValidationError(f"任务“{task_name}”缺少按任务颗粒度撰写的说明。")

                catalog_status = _text(task.get("catalog_status")) or "matched"
                if catalog_status not in ALLOWED_CATALOG_STATUSES:
                    allowed = "、".join(sorted(ALLOWED_CATALOG_STATUSES))
                    raise QuoteValidationError(
                        f"任务“{task_name}”的 catalog_status 非法：{catalog_status}。只允许：{allowed}。"
                    )
                task_refs = _list_of_text(task.get("service_catalog_refs"))
                catalog_candidate = _normalized_catalog_candidate(
                    task.get("catalog_candidate"),
                    stage_name=stage_name,
                    project_name=project_name,
                    task_name=task_name,
                    descriptions=descriptions,
                )

                if catalog_status == "pending_review":
                    required_candidate_fields = [
                        "proposed_level_1_module",
                        "proposed_level_2_module",
                        "proposed_project",
                        "proposed_task",
                        "description",
                        "reason",
                    ]
                    missing_candidate = [
                        key for key in required_candidate_fields if not _text(catalog_candidate.get(key))
                    ]
                    if missing_candidate:
                        missing_text = "、".join(missing_candidate)
                        raise QuoteValidationError(
                            f"任务“{task_name}”缺少待入库候选信息：{missing_text}。"
                        )
                    pending_catalog_items.append(catalog_candidate)
                elif not task_refs:
                    raise QuoteValidationError(f"任务“{task_name}”缺少服务清单引用。")

                task["task_name"] = task_name
                task["description_bullets"] = descriptions
                task["catalog_status"] = catalog_status
                task["service_catalog_refs"] = task_refs
                if catalog_status == "pending_review":
                    task["catalog_candidate"] = catalog_candidate

    normalized["case_type"] = case_type
    normalized["annual_context"] = annual_context
    normalized["pending_catalog_items"] = pending_catalog_items
    return normalized
