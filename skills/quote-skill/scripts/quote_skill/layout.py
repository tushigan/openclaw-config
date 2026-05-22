from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "；".join(_text(item) for item in value if item is not None)
    return str(value)


def build_stage_table_sections(content: dict[str, Any]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []

    for stage in content.get("stages", []):
        rows: list[dict[str, Any]] = []
        for project in stage.get("projects", []):
            tasks = project.get("tasks", [])
            project_rowspan = len(tasks)
            project_deliverables = _text(project.get("project_deliverables"))

            for index, task in enumerate(tasks):
                rows.append(
                    {
                        "stage_name": _text(stage.get("stage_name")),
                        "stage_rowspan": 0,
                        "show_stage": False,
                        "project_name": _text(project.get("project_name")),
                        "project_rowspan": project_rowspan if index == 0 else 0,
                        "show_project": index == 0,
                        "task_name": _text(task.get("task_name")),
                        "description_text": _text(task.get("description_bullets")),
                        "deliverables_text": project_deliverables,
                        "show_deliverables": index == 0,
                        "department_text": _text(
                            task.get("department")
                            or task.get("service_department")
                            or project.get("department")
                            or project.get("service_department")
                        ),
                        "owner_text": _text(task.get("owner") or project.get("owner")),
                    }
                )

        if rows:
            rows[0]["show_stage"] = True
            rows[0]["stage_rowspan"] = len(rows)

        sections.append(
            {
                "stage_name": _text(stage.get("stage_name")),
                "stage_price": _text(stage.get("stage_price")),
                "stage_duration": _text(stage.get("stage_duration")),
                "stage_deliverables_text": _text(stage.get("stage_deliverables")),
                "rows": rows,
            }
        )

    return sections
