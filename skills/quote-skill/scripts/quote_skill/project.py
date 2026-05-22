from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat()


def slugify(text: str) -> str:
    compact = re.sub(r"\s+", "-", text.strip())
    compact = re.sub(r"[^\w\-一-龥]+", "-", compact)
    compact = re.sub(r"-{2,}", "-", compact).strip("-")
    return compact.lower() or "untitled"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _empty_quote_content(project_name: str) -> dict[str, Any]:
    return {
        "title": project_name,
        "subtitle": "",
        "case_type": "",
        "annual_context": {},
        "overview_paragraphs": [],
        "pricing_summary": {"label": "当前报价结构", "details": "", "total": ""},
        "stage_plan": [],
        "stages": [],
        "pending_catalog_items": [],
        "service_sections": [],
        "closing_notes": [],
    }


def create_project(
    projects_root: Path | None,
    client_name: str,
    project_name: str,
    output_mode: str,
    project_dir: Path | None = None,
) -> Path:
    if project_dir is None:
        if projects_root is None:
            raise ValueError("projects_root or project_dir is required")
        project_dir = projects_root / client_name / project_name
    project_path = project_dir / "project.json"
    version_dir = project_dir / "versions" / "v1"

    if project_dir.exists():
        if not project_dir.is_dir() or any(project_dir.iterdir()):
            raise FileExistsError(f"Project directory already exists: {project_dir}")

    (project_dir / "source-materials").mkdir(parents=True, exist_ok=True)
    (project_dir / "working-notes").mkdir(parents=True, exist_ok=True)
    version_dir.mkdir(parents=True, exist_ok=True)

    timestamp = _timestamp()
    project_payload = {
        "project_id": f"{slugify(client_name)}-{slugify(project_name)}-001",
        "client_name": client_name,
        "project_name": project_name,
        "project_slug": slugify(project_name),
        "status": "collecting-info",
        "current_version": "v1",
        "created_at": timestamp,
        "updated_at": timestamp,
        "project_summary": "",
        "output_mode": output_mode,
        "pricing_owner": "human",
        "suggested_case_type": "",
        "confirmed_case_type": "",
        "business_goal": "",
        "service_scope": [],
        "excluded_scope": [],
        "catalog_pending_summary": [],
        "missing_info": [],
        "open_questions": [],
        "key_decisions": [],
        "source_materials": [],
        "versions": ["v1"],
    }
    version_payload = {
        "version": "v1",
        "based_on": None,
        "created_at": timestamp,
        "change_reason": "initial draft",
        "input_summary": "",
        "changes": [],
        "user_feedback": [],
        "outputs": [],
        "case_type": "",
        "catalog_refs_used": [],
        "detected_new_catalog_items": [],
        "pending_pool_item_ids": [],
        "notes": "",
    }

    _write_json(project_path, project_payload)
    _write_json(version_dir / "version.json", version_payload)
    _write_json(version_dir / "quote-content.json", _empty_quote_content(project_name))
    return project_dir


def create_version(project_dir: Path, change_reason: str) -> Path:
    project_path = project_dir / "project.json"
    project_payload = json.loads(project_path.read_text(encoding="utf-8"))

    last_version = project_payload["versions"][-1]
    next_number = int(last_version.removeprefix("v")) + 1
    next_version = f"v{next_number}"
    version_dir = project_dir / "versions" / next_version
    version_dir.mkdir(parents=True, exist_ok=True)
    previous_quote_content_path = project_dir / "versions" / last_version / "quote-content.json"
    previous_quote_content = json.loads(previous_quote_content_path.read_text(encoding="utf-8"))

    version_payload = {
        "version": next_version,
        "based_on": last_version,
        "created_at": _timestamp(),
        "change_reason": change_reason,
        "input_summary": "",
        "changes": [],
        "user_feedback": [],
        "outputs": [],
        "case_type": previous_quote_content.get("case_type", ""),
        "catalog_refs_used": [],
        "detected_new_catalog_items": [],
        "pending_pool_item_ids": [],
        "notes": "",
    }

    project_payload["current_version"] = next_version
    project_payload["status"] = "revising"
    project_payload["updated_at"] = _timestamp()
    project_payload["versions"].append(next_version)

    _write_json(version_dir / "version.json", version_payload)
    _write_json(version_dir / "quote-content.json", previous_quote_content)
    _write_json(project_path, project_payload)
    return version_dir


def record_outputs(
    project_dir: Path,
    version_name: str,
    outputs: list[str],
    case_type: str | None = None,
    detected_new_catalog_items: list[dict[str, Any]] | None = None,
    catalog_refs_used: list[str] | None = None,
    pending_pool_item_ids: list[str] | None = None,
) -> None:
    project_path = project_dir / "project.json"
    version_path = project_dir / "versions" / version_name / "version.json"

    project_payload = json.loads(project_path.read_text(encoding="utf-8"))
    version_payload = json.loads(version_path.read_text(encoding="utf-8"))

    if version_name != project_payload["current_version"]:
        raise ValueError(f"Cannot record outputs for non-current version: {version_name}")

    version_payload["outputs"] = outputs
    if case_type is not None:
        version_payload["case_type"] = case_type
        project_payload["confirmed_case_type"] = case_type
    if catalog_refs_used is not None:
        version_payload["catalog_refs_used"] = catalog_refs_used
    if detected_new_catalog_items is not None:
        version_payload["detected_new_catalog_items"] = detected_new_catalog_items
        project_payload["catalog_pending_summary"] = detected_new_catalog_items
    if pending_pool_item_ids is not None:
        version_payload["pending_pool_item_ids"] = pending_pool_item_ids
    version_payload["notes"] = version_payload.get("notes", "")
    project_payload["status"] = "pending-review"
    project_payload["updated_at"] = _timestamp()

    _write_json(version_path, version_payload)
    _write_json(project_path, project_payload)
