from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = "1.0"


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat()


def _slugify(text: str) -> str:
    compact = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in text.strip())
    compact = "-".join(part for part in compact.split("-") if part)
    return compact.lower() or "untitled"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_project_dirs(project_dir: Path) -> None:
    if project_dir.exists():
        raise FileExistsError(f"Project directory already exists: {project_dir}")

    for relative in (
        "materials/audio",
        "materials/images",
        "materials/docs",
        "materials/chat",
        "notes/meeting-notes",
        "notes/briefs",
        "notes/summaries",
        "outputs/handoff",
        "outputs/reports",
        "quote",
    ):
        (project_dir / relative).mkdir(parents=True, exist_ok=True)


def build_project_payload(
    project_dir: Path,
    client_name: str,
    project_name: str,
    current_goal: str,
) -> dict[str, Any]:
    timestamp = _timestamp()
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": f"{_slugify(client_name)}-{_slugify(project_name)}",
        "client_name": client_name,
        "project_name": project_name,
        "project_slug": _slugify(project_name),
        "current_stage": "线索",
        "lifecycle_status": "active",
        "current_goal": current_goal,
        "project_summary": "",
        "background_summary": "",
        "requirement_summary": "",
        "recommended_case_type": "",
        "quote_status": "not-ready",
        "created_at": timestamp,
        "updated_at": timestamp,
        "last_activity_at": timestamp,
        "next_action_summary": "",
        "primary_contact": "",
        "source_channels": [],
        "tags": [],
        "material_count": 0,
        "latest_material_id": "",
        "latest_progress_id": "",
        "current_quote_version": "",
        "quote_project_dir": str(project_dir / "quote"),
    }


def build_materials_payload(project_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_dir.name,
        "items": [],
    }


def build_progress_payload(
    project_dir: Path,
    current_goal: str,
    source_materials: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_dir.name,
        "entries": [
            {
                "progress_id": "",
                "recorded_at": "",
                "event_type": "intake",
                "stage_before": "",
                "stage_after": "线索",
                "summary": "项目已立项",
                "details": current_goal,
                "key_decisions": [],
                "open_questions": [],
                "blockers": [],
                "next_actions": [],
                "source_material_ids": [],
                "note_path": "",
                "recorded_by": "business-project-intake",
                "source_material_count": len(source_materials),
            }
        ],
    }


def build_tasks_payload(project_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_dir.name,
        "tasks": [],
    }


def build_quote_handoff_payload(
    project_dir: Path,
    client_name: str,
    project_name: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_dir.name,
        "handoff_status": "draft",
        "prepared_at": "",
        "prepared_by": "",
        "trigger_reason": "",
        "client_name": client_name,
        "project_name": project_name,
        "current_stage": "线索",
        "business_goal": "",
        "recommended_case_type": "",
        "confirmed_scope": [],
        "excluded_scope": [],
        "key_requirements": [],
        "key_decisions": [],
        "open_questions": [],
        "material_refs": [],
        "meeting_note_refs": [],
        "quote_project_dir": str(project_dir / "quote"),
        "current_quote_version": "",
        "quote_output_refs": [],
        "last_quote_generated_at": "",
        "quote_followup_summary": "",
    }


def build_material_record(
    project_dir: Path,
    destination: Path,
    material_type: str,
    title: str,
    source_channel: str,
    captured_at: str | None = None,
) -> dict[str, Any]:
    return {
        "material_id": f"mat-{uuid4().hex[:10]}",
        "type": material_type,
        "title": title,
        "source_channel": source_channel,
        "original_name": destination.name,
        "stored_path": str(destination),
        "copied_at": _timestamp(),
        "captured_at": captured_at or "",
        "mime_type": "",
        "tags": [],
        "summary": "",
        "transcript_path": "",
        "note_path": "",
        "processing_status": "copied",
        "related_progress_ids": [],
        "related_task_ids": [],
    }


def build_quote_progress_entry(
    project_payload: dict[str, Any],
    quote_version: str,
    output_refs: list[str],
) -> dict[str, Any]:
    return {
        "progress_id": f"prog-{uuid4().hex[:10]}",
        "recorded_at": _timestamp(),
        "event_type": "quote-sent",
        "stage_before": project_payload.get("current_stage", ""),
        "stage_after": "报价中",
        "summary": f"已生成并同步报价版本 {quote_version}",
        "details": "报价文件已写回业务项目。",
        "key_decisions": [],
        "open_questions": [],
        "blockers": [],
        "next_actions": ["跟进客户对本轮报价的反馈"],
        "source_material_ids": [],
        "note_path": "",
        "recorded_by": "business-project-intake",
        "quote_output_refs": output_refs,
    }


def build_quote_followup_task(quote_version: str, title: str) -> dict[str, Any]:
    timestamp = _timestamp()
    return {
        "task_id": f"task-{uuid4().hex[:10]}",
        "title": title,
        "description": f"跟进 {quote_version} 的客户反馈和修改意见。",
        "status": "todo",
        "priority": "high",
        "owner": "",
        "due_at": "",
        "created_at": timestamp,
        "updated_at": timestamp,
        "source_progress_id": "",
        "related_material_ids": [],
        "related_quote_version": quote_version,
        "completion_note": "",
    }


def _material_folder_name(material_type: str) -> str:
    mapping = {
        "audio": "audio",
        "image": "images",
        "doc": "docs",
        "chat": "chat",
    }
    return mapping.get(material_type, "docs")


def create_business_project(
    workspace_root: Path,
    client_name: str,
    project_name: str,
    current_goal: str,
    source_materials: list[dict[str, Any]],
) -> Path:
    project_dir = workspace_root / "projects" / client_name / project_name
    _ensure_project_dirs(project_dir)
    _write_json(project_dir / "project.json", build_project_payload(project_dir, client_name, project_name, current_goal))
    _write_json(project_dir / "materials.json", build_materials_payload(project_dir))
    _write_json(project_dir / "progress.json", build_progress_payload(project_dir, current_goal, source_materials))
    _write_json(project_dir / "tasks.json", build_tasks_payload(project_dir))
    _write_json(
        project_dir / "quote-handoff.json",
        build_quote_handoff_payload(project_dir, client_name, project_name),
    )

    material_ids: list[str] = []
    for source_material in source_materials:
        record = archive_material(
            project_dir=project_dir,
            source_path=Path(source_material["path"]),
            material_type=str(source_material.get("type", "doc")),
            title=str(source_material.get("title", Path(source_material["path"]).name)),
            source_channel=str(source_material.get("source_channel", "")),
        )
        material_ids.append(record["material_id"])

    progress_payload = _read_json(project_dir / "progress.json")
    progress_payload["entries"][0]["progress_id"] = f"prog-{uuid4().hex[:10]}"
    progress_payload["entries"][0]["recorded_at"] = _timestamp()
    progress_payload["entries"][0]["source_material_ids"] = material_ids
    _write_json(project_dir / "progress.json", progress_payload)

    project_payload = _read_json(project_dir / "project.json")
    project_payload["latest_progress_id"] = progress_payload["entries"][0]["progress_id"]
    project_payload["source_channels"] = sorted(
        {
            str(source_material.get("source_channel", "")).strip()
            for source_material in source_materials
            if str(source_material.get("source_channel", "")).strip()
        }
    )
    _write_json(project_dir / "project.json", project_payload)

    return project_dir


def archive_material(
    project_dir: Path,
    source_path: Path,
    material_type: str,
    title: str,
    source_channel: str,
    captured_at: str | None = None,
) -> dict[str, Any]:
    folder_name = _material_folder_name(material_type)
    destination = project_dir / "materials" / folder_name / source_path.name
    if destination.exists():
        destination = destination.with_name(f"{uuid4().hex[:8]}-{source_path.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)

    materials_path = project_dir / "materials.json"
    materials_payload = _read_json(materials_path)
    material = build_material_record(
        project_dir=project_dir,
        destination=destination,
        material_type=material_type,
        title=title,
        source_channel=source_channel,
        captured_at=captured_at,
    )
    material["original_name"] = source_path.name
    materials_payload["items"].append(material)
    _write_json(materials_path, materials_payload)

    project_path = project_dir / "project.json"
    project_payload = _read_json(project_path)
    project_payload["material_count"] = len(materials_payload["items"])
    project_payload["latest_material_id"] = material["material_id"]
    project_payload["updated_at"] = _timestamp()
    project_payload["last_activity_at"] = project_payload["updated_at"]
    channels = set(project_payload.get("source_channels", []))
    if source_channel:
        channels.add(source_channel)
    project_payload["source_channels"] = sorted(channels)
    _write_json(project_path, project_payload)

    return material


def prepare_quote_handoff(
    project_dir: Path,
    trigger_reason: str,
    recommended_case_type: str,
    confirmed_scope: list[str] | None = None,
    excluded_scope: list[str] | None = None,
) -> dict[str, Any]:
    handoff_path = project_dir / "quote-handoff.json"
    handoff_payload = _read_json(handoff_path)
    handoff_payload["handoff_status"] = "ready"
    handoff_payload["prepared_at"] = _timestamp()
    handoff_payload["prepared_by"] = "business-project-intake"
    handoff_payload["trigger_reason"] = trigger_reason
    handoff_payload["recommended_case_type"] = recommended_case_type
    handoff_payload["confirmed_scope"] = confirmed_scope or []
    handoff_payload["excluded_scope"] = excluded_scope or []
    handoff_payload["current_stage"] = "待报价"
    _write_json(handoff_path, handoff_payload)

    project_path = project_dir / "project.json"
    project_payload = _read_json(project_path)
    project_payload["quote_status"] = "ready"
    project_payload["recommended_case_type"] = recommended_case_type
    project_payload["current_stage"] = "待报价"
    project_payload["quote_project_dir"] = str(project_dir / "quote")
    project_payload["updated_at"] = _timestamp()
    project_payload["last_activity_at"] = project_payload["updated_at"]
    _write_json(project_path, project_payload)

    return handoff_payload


def sync_quote_state(project_dir: Path, quote_version: str, output_refs: list[str]) -> None:
    project_path = project_dir / "project.json"
    handoff_path = project_dir / "quote-handoff.json"
    progress_path = project_dir / "progress.json"
    tasks_path = project_dir / "tasks.json"

    project_payload = _read_json(project_path)
    handoff_payload = _read_json(handoff_path)
    progress_payload = _read_json(progress_path)
    tasks_payload = _read_json(tasks_path)

    project_payload["quote_status"] = "quoted"
    project_payload["current_quote_version"] = quote_version
    project_payload["current_stage"] = "报价中"
    project_payload["updated_at"] = _timestamp()
    project_payload["last_activity_at"] = project_payload["updated_at"]

    handoff_payload["handoff_status"] = "quoted"
    handoff_payload["current_quote_version"] = quote_version
    handoff_payload["quote_output_refs"] = output_refs
    handoff_payload["last_quote_generated_at"] = _timestamp()
    handoff_payload["quote_followup_summary"] = "等待客户反馈本轮报价。"
    handoff_payload["current_stage"] = "报价中"

    progress_entry = build_quote_progress_entry(project_payload=project_payload, quote_version=quote_version, output_refs=output_refs)
    progress_payload["entries"].append(progress_entry)
    project_payload["latest_progress_id"] = progress_entry["progress_id"]

    tasks_payload["tasks"].append(
        build_quote_followup_task(
            quote_version=quote_version,
            title="跟进本轮报价反馈",
        )
    )

    _write_json(project_path, project_payload)
    _write_json(handoff_path, handoff_payload)
    _write_json(progress_path, progress_payload)
    _write_json(tasks_path, tasks_payload)
