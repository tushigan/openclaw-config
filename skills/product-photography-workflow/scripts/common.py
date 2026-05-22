#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/Users/a123/.openclaw")
WORKSPACE = ROOT / "workspace"
DEFAULT_OUTPUT_ROOT = WORKSPACE / "outputs"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
STATE_FILE = "project_state.json"

PROJECT_SCHEMA_VERSION = "2.0"
PROJECT_MODE = "multi_task_v2"
TASKS_MANIFEST_FILE = "tasks_manifest.json"
PROJECT_RECALL_FILE = "project_recall.json"
TASKS_DIR = "tasks"
TASK_STATE_FILE = "task_state.json"
TASK_ASSETS_FILE = "task_assets.json"
TASK_BRIEF_FILE = "task_brief.json"
TASK_GENERATION_FILE = "generation_manifest.json"
TASK_CONFIRMATION_LOG = "confirmation_log.jsonl"

RATIO_TO_SIZE = {
    "1:1": "2880x2880",
    "4:5": "2560x3200",
    "3:4": "2448x3264",
    "9:16": "2160x3840",
    "16:9": "3840x2160",
}

PRODUCT_ROLE_ORDER = [
    "product_front",
    "product_side",
    "product_top",
    "product_back",
    "product_open",
    "product_cross_section",
    "product_detail",
]

STYLE_ROLE_ORDER = [
    "reference_style",
    "reference_lighting",
    "reference_background",
    "reference_layout",
    "reference_other",
]

TASK_ROLE_ORDER = [
    "page_draft",
    "composition_reference",
    "scene_reference",
    "style_reference",
    "lighting_reference",
    "product_state_reference",
    "other_reference",
]

STAGE_TRANSITIONS = {
    "risk_continue": "intake_risk_waiting_confirm",
    "creative_direction": "creative_direction_waiting_confirm",
    "generation_review": "generation_review_waiting_confirm",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def slugify(text: str) -> str:
    ascii_only = re.sub(r"[^A-Za-z0-9]+", "-", text or "").strip("-").lower()
    return ascii_only[:32] or "project"


def build_project_id(name: str) -> str:
    now = datetime.now()
    return f"PP-{now.strftime('%Y%m%d-%H%M%S')}-{slugify(name)}"


def build_task_id(task_name: str, index: int) -> str:
    return f"TASK-{index:03d}-{slugify(task_name)}"


def build_version_id(index: int) -> str:
    return f"V{index:03d}"


def ensure_project_tree(project_dir: Path) -> None:
    for rel in [
        "images/product_sources",
        "images/reference_sources",
        "images/generated_drafts",
        "images/final_delivery",
        "prompts",
        "reports",
        "deliveries",
        "logs",
        TASKS_DIR,
    ]:
        (project_dir / rel).mkdir(parents=True, exist_ok=True)


def ensure_task_tree(task_dir: Path) -> None:
    for rel in [
        "references/page_draft",
        "references/composition_reference",
        "references/scene_reference",
        "references/style_reference",
        "references/lighting_reference",
        "references/product_state_reference",
        "references/other_reference",
        "prompts",
        "reports",
        "versions",
    ]:
        (task_dir / rel).mkdir(parents=True, exist_ok=True)


def blank_tasks_manifest(project_id: str, project_name: str) -> dict[str, Any]:
    return {
        "version": PROJECT_SCHEMA_VERSION,
        "project_id": project_id,
        "project_name": project_name,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "tasks": [],
        "summary": {
            "task_count": 0,
            "approved_task_count": 0,
            "revision_count": 0,
        },
    }


def blank_project_recall(project_id: str, project_name: str) -> dict[str, Any]:
    return {
        "version": "1.0",
        "project_id": project_id,
        "project_name": project_name,
        "aliases": [project_name],
        "last_recalled_at": "",
        "last_query": "",
        "last_summary": {},
    }


def initialize_project_files(
    project_dir: Path,
    project_name: str,
    project_id: str,
    scene_mode: str,
    scope_level: str,
) -> None:
    ensure_project_tree(project_dir)
    state = {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "project_mode": PROJECT_MODE,
        "project_id": project_id,
        "project_name": project_name,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "current_stage": "intake_collecting",
        "stage_status": "ready",
        "active_task_id": "",
        "project_recall": {
            "aliases": [project_name],
            "last_recalled_at": "",
            "last_query": "",
        },
        "workflow_flags": {
            "assets_sufficient": False,
            "risk_accepted": False,
            "creative_confirmed": False,
            "generation_allowed": False,
            "delivery_ready": False,
        },
        "mode": {
            "scene_mode": scene_mode,
            "scope_level": scope_level,
        },
        "attempts": {
            "generation_round": 0,
            "revision_round": 0,
        },
        "last_error_stage": "",
        "last_error": "",
        "artifacts": {
            "intake_manifest": "intake_manifest.json",
            "assets_manifest": "assets_manifest.json",
            "product_profile": "product_profile.json",
            "reference_analysis": "reference_analysis.json",
            "creative_direction": "creative_direction.json",
            "generation_manifest": "generation_manifest.json",
            "delivery_manifest": "delivery_manifest.json",
            "tasks_manifest": TASKS_MANIFEST_FILE,
            "project_recall": PROJECT_RECALL_FILE,
        },
    }
    intake = {
        "version": "1.0",
        "project_id": project_id,
        "project_name": project_name,
        "created_at": utc_now(),
        "status": "collecting",
        "requested_output_kind": "",
        "requested_ratio": "",
        "requested_variants": 1,
        "user_notes": [],
        "gap_report": {},
        "risk_confirmation": {},
    }
    assets = {
        "version": "1.0",
        "project_id": project_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "product_assets": [],
        "reference_assets": [],
        "summary": {
            "product_asset_count": 0,
            "reference_asset_count": 0,
            "distinct_product_roles": [],
            "distinct_reference_roles": [],
        },
    }
    generation = {
        "version": "1.0",
        "project_id": project_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "rounds": [],
        "latest_status": "not_started",
        "latest_output": "",
        "latest_task_id": "",
        "review": {},
    }
    delivery = {
        "version": "1.0",
        "project_id": project_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "status": "not_started",
        "delivered_files": [],
    }
    write_json(project_dir / STATE_FILE, state)
    write_json(project_dir / "intake_manifest.json", intake)
    write_json(project_dir / "assets_manifest.json", assets)
    write_json(project_dir / "generation_manifest.json", generation)
    write_json(project_dir / "delivery_manifest.json", delivery)
    write_json(project_dir / TASKS_MANIFEST_FILE, blank_tasks_manifest(project_id, project_name))
    write_json(project_dir / PROJECT_RECALL_FILE, blank_project_recall(project_id, project_name))
    (project_dir / "audit_log.jsonl").touch(exist_ok=True)


def load_state(project_dir: Path) -> dict[str, Any]:
    path = project_dir / STATE_FILE
    if not path.exists():
        raise SystemExit(f"项目状态文件不存在: {path}")
    return read_json(path, {})


def save_state(project_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    write_json(project_dir / STATE_FILE, state)


def update_state(
    project_dir: Path,
    *,
    current_stage: str | None = None,
    stage_status: str | None = None,
    workflow_flag_updates: dict[str, Any] | None = None,
    artifact_updates: dict[str, str] | None = None,
    attempts_update: dict[str, Any] | None = None,
    active_task_id: str | None = None,
    last_error_stage: str | None = None,
    last_error: str | None = None,
) -> dict[str, Any]:
    state = load_state(project_dir)
    if current_stage is not None:
        state["current_stage"] = current_stage
    if stage_status is not None:
        state["stage_status"] = stage_status
    if workflow_flag_updates:
        state.setdefault("workflow_flags", {}).update(workflow_flag_updates)
    if artifact_updates:
        state.setdefault("artifacts", {}).update(artifact_updates)
    if attempts_update:
        state.setdefault("attempts", {}).update(attempts_update)
    if active_task_id is not None:
        state["active_task_id"] = active_task_id
    if last_error_stage is not None:
        state["last_error_stage"] = last_error_stage
    if last_error is not None:
        state["last_error"] = last_error
    save_state(project_dir, state)
    return state


def append_audit(project_dir: Path, event: str, payload: dict[str, Any]) -> None:
    append_jsonl(
        project_dir / "audit_log.jsonl",
        {
            "ts": utc_now(),
            "event": event,
            "payload": payload,
        },
    )


def resolve_project_dir(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def resolve_asset_input(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def copy_asset(source: Path, dest_dir: Path, stem_prefix: str, index: int) -> Path:
    if not source.exists():
        raise SystemExit(f"素材不存在: {source}")
    suffix = source.suffix.lower() or ".png"
    dest_name = f"{stem_prefix}_{index:02d}{suffix}"
    dest = dest_dir / dest_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest


def copy_asset_to_project(source: Path, dest_dir: Path, stem_prefix: str, index: int) -> Path:
    return copy_asset(source, dest_dir, stem_prefix, index)


def copy_asset_to_task(source: Path, task_dir: Path, role: str, index: int) -> Path:
    return copy_asset(source, task_dir / "references" / role, role, index)


def summarize_assets(assets_manifest: dict[str, Any]) -> dict[str, Any]:
    product_assets = assets_manifest.get("product_assets", [])
    reference_assets = assets_manifest.get("reference_assets", [])
    return {
        "product_asset_count": len(product_assets),
        "reference_asset_count": len(reference_assets),
        "distinct_product_roles": sorted({item.get("role", "") for item in product_assets if item.get("role")}),
        "distinct_reference_roles": sorted({item.get("role", "") for item in reference_assets if item.get("role")}),
    }


def summarize_task_assets(task_assets: dict[str, Any]) -> dict[str, Any]:
    payload = {f"{role}_count": 0 for role in TASK_ROLE_ORDER}
    payload["distinct_roles"] = []
    roles = []
    for role in TASK_ROLE_ORDER:
        count = len(task_assets.get("assets", {}).get(role, []))
        payload[f"{role}_count"] = count
        if count:
            roles.append(role)
    payload["distinct_roles"] = roles
    return payload


def size_for_ratio(ratio: str) -> str:
    return RATIO_TO_SIZE.get((ratio or "").strip(), "2880x2880")


def asset_entries_by_role(assets_manifest: dict[str, Any], roles: list[str]) -> list[dict[str, Any]]:
    all_entries = assets_manifest.get("product_assets", []) + assets_manifest.get("reference_assets", [])
    wanted = []
    for role in roles:
        wanted.extend([entry for entry in all_entries if entry.get("role") == role])
    return wanted


def task_asset_entries_by_role(task_assets: dict[str, Any], roles: list[str]) -> list[dict[str, Any]]:
    wanted = []
    asset_map = task_assets.get("assets", {})
    for role in roles:
        wanted.extend(asset_map.get(role, []))
    return wanted


def relative_to_project(project_dir: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project_dir))
    except ValueError:
        return str(path)


def load_tasks_manifest(project_dir: Path) -> dict[str, Any]:
    state = load_state(project_dir)
    project_id = state.get("project_id", "")
    project_name = state.get("project_name", project_dir.name)
    manifest_path = project_dir / TASKS_MANIFEST_FILE
    manifest = read_json(manifest_path)
    if manifest is None:
        manifest = blank_tasks_manifest(project_id, project_name)
        write_json(manifest_path, manifest)
    return manifest


def summarize_tasks(tasks_manifest: dict[str, Any]) -> dict[str, Any]:
    tasks = tasks_manifest.get("tasks", [])
    return {
        "task_count": len(tasks),
        "approved_task_count": sum(1 for item in tasks if item.get("status") == "approved"),
        "revision_count": sum(max(0, int(item.get("version_count", 1)) - 1) for item in tasks),
    }


def save_tasks_manifest(project_dir: Path, tasks_manifest: dict[str, Any]) -> None:
    tasks_manifest["updated_at"] = utc_now()
    tasks_manifest["summary"] = summarize_tasks(tasks_manifest)
    write_json(project_dir / TASKS_MANIFEST_FILE, tasks_manifest)


def blank_task_assets(project_id: str, task_id: str) -> dict[str, Any]:
    return {
        "version": "1.0",
        "project_id": project_id,
        "task_id": task_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "assets": {role: [] for role in TASK_ROLE_ORDER},
        "summary": summarize_task_assets({"assets": {role: [] for role in TASK_ROLE_ORDER}}),
    }


def blank_task_brief(project_id: str, task_id: str, task_name: str, task_type: str, output_ratio: str, goal: str) -> dict[str, Any]:
    return {
        "version": "1.1",
        "project_id": project_id,
        "task_id": task_id,
        "task_name": task_name,
        "task_type": task_type,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "status": "draft",
        "goal": goal,
        "output_ratio": output_ratio,
        "page_draft_note": "",
        "composition_note": "",
        "scene_note": "",
        "product_state_note": "",
        "placement_note": "",
        "execution_mode": "whole_image",
        "base_image": {},
        "edit_scope": {
            "editable_targets": [],
            "immutable_elements": [],
            "anchor_objects": [],
            "spatial_relations": [],
        },
        "must_show": [],
        "must_avoid": [],
        "references_summary": {},
        "product_constraints_snapshot": {},
        "confirmation": {},
    }


def blank_task_generation_manifest(project_id: str, task_id: str, initial_version_id: str) -> dict[str, Any]:
    return {
        "version": "2.0",
        "project_id": project_id,
        "task_id": task_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "latest_status": "not_started",
        "latest_output": "",
        "latest_version_id": initial_version_id,
        "review": {},
        "versions": [
            {
                "version_id": initial_version_id,
                "created_at": utc_now(),
                "status": "draft",
                "note": "initial version scaffold",
            }
        ],
    }


def blank_task_state(
    project_id: str,
    task_id: str,
    task_name: str,
    task_type: str,
    output_ratio: str,
    goal: str,
    selected_version_id: str,
) -> dict[str, Any]:
    return {
        "version": "2.0",
        "project_id": project_id,
        "task_id": task_id,
        "task_name": task_name,
        "task_type": task_type,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "current_stage": "task_collecting",
        "stage_status": "ready",
        "goal": goal,
        "output_ratio": output_ratio,
        "selected_version_id": selected_version_id,
        "latest_version_id": selected_version_id,
        "latest_output": "",
        "workflow_flags": {
            "references_classified": False,
            "brief_confirmed": False,
            "generation_allowed": False,
            "result_approved": False,
        },
        "history": {
            "revision_round": 0,
        },
    }


def initialize_task_files(
    project_dir: Path,
    task_name: str,
    task_type: str,
    output_ratio: str = "",
    goal: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    tags = tags or []
    state = load_state(project_dir)
    tasks_manifest = load_tasks_manifest(project_dir)
    existing_ids = {item.get("task_id", "") for item in tasks_manifest.get("tasks", [])}
    index = len(tasks_manifest.get("tasks", [])) + 1
    task_id = build_task_id(task_name, index)
    while task_id in existing_ids or (project_dir / TASKS_DIR / task_id).exists():
        index += 1
        task_id = build_task_id(task_name, index)

    task_dir = project_dir / TASKS_DIR / task_id
    ensure_task_tree(task_dir)
    version_id = build_version_id(1)
    (task_dir / "versions" / version_id).mkdir(parents=True, exist_ok=True)

    task_state = blank_task_state(
        state.get("project_id", ""),
        task_id,
        task_name,
        task_type,
        output_ratio,
        goal,
        version_id,
    )
    task_assets = blank_task_assets(state.get("project_id", ""), task_id)
    task_brief = blank_task_brief(
        state.get("project_id", ""),
        task_id,
        task_name,
        task_type,
        output_ratio,
        goal,
    )
    generation_manifest = blank_task_generation_manifest(state.get("project_id", ""), task_id, version_id)

    write_json(task_dir / TASK_STATE_FILE, task_state)
    write_json(task_dir / TASK_ASSETS_FILE, task_assets)
    write_json(task_dir / TASK_BRIEF_FILE, task_brief)
    write_json(task_dir / TASK_GENERATION_FILE, generation_manifest)
    (task_dir / TASK_CONFIRMATION_LOG).touch(exist_ok=True)

    tasks_manifest.setdefault("tasks", []).append(
        {
            "task_id": task_id,
            "task_name": task_name,
            "task_slug": slugify(task_name),
            "task_type": task_type,
            "task_dir": relative_to_project(project_dir, task_dir),
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "status": "collecting",
            "selected_version_id": version_id,
            "latest_version_id": version_id,
            "version_count": 1,
            "latest_output": "",
            "output_ratio": output_ratio,
            "tags": tags,
        }
    )
    save_tasks_manifest(project_dir, tasks_manifest)
    update_state(
        project_dir,
        current_stage="task_collecting",
        stage_status="ready",
        active_task_id=task_id,
    )
    append_audit(
        project_dir,
        "task_initialized",
        {
            "task_id": task_id,
            "task_name": task_name,
            "task_type": task_type,
            "output_ratio": output_ratio,
        },
    )
    return {
        "task_id": task_id,
        "task_dir": task_dir,
        "version_id": version_id,
    }


def load_task_state(task_dir: Path) -> dict[str, Any]:
    state_path = task_dir / TASK_STATE_FILE
    if not state_path.exists():
        raise SystemExit(f"任务状态文件不存在: {state_path}")
    return read_json(state_path, {})


def save_task_state(task_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    write_json(task_dir / TASK_STATE_FILE, state)


def update_task_state(
    task_dir: Path,
    *,
    current_stage: str | None = None,
    stage_status: str | None = None,
    workflow_flag_updates: dict[str, Any] | None = None,
    field_updates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = load_task_state(task_dir)
    if current_stage is not None:
        state["current_stage"] = current_stage
    if stage_status is not None:
        state["stage_status"] = stage_status
    if workflow_flag_updates:
        state.setdefault("workflow_flags", {}).update(workflow_flag_updates)
    if field_updates:
        state.update(field_updates)
    save_task_state(task_dir, state)
    return state


def update_task_manifest_entry(project_dir: Path, task_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    manifest = load_tasks_manifest(project_dir)
    for entry in manifest.get("tasks", []):
        if entry.get("task_id") == task_id:
            entry.update(updates)
            entry["updated_at"] = utc_now()
            save_tasks_manifest(project_dir, manifest)
            return entry
    raise SystemExit(f"未找到任务: {task_id}")


def find_task_entry(project_dir: Path, task_ref: str) -> dict[str, Any] | None:
    ref = (task_ref or "").strip()
    if not ref:
        return None
    manifest = load_tasks_manifest(project_dir)
    for entry in manifest.get("tasks", []):
        if ref in {entry.get("task_id", ""), entry.get("task_name", ""), entry.get("task_slug", "")}:
            return entry
    return None


def resolve_task_dir(project_dir: Path, task_ref: str) -> Path:
    task_path = Path(task_ref)
    if task_path.exists() and task_path.is_dir():
        if (task_path / TASK_STATE_FILE).exists():
            return task_path.resolve()
    entry = find_task_entry(project_dir, task_ref)
    if not entry:
        raise SystemExit(f"未找到任务: {task_ref}")
    return (project_dir / entry["task_dir"]).resolve()


def next_task_version_id(task_dir: Path) -> str:
    generation = read_json(task_dir / TASK_GENERATION_FILE, {})
    existing = generation.get("versions", [])
    return build_version_id(len(existing) + 1)


def append_task_confirmation(task_dir: Path, payload: dict[str, Any]) -> None:
    append_jsonl(task_dir / TASK_CONFIRMATION_LOG, payload)


def tokenize_simple(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", (text or "").strip().lower())
    if not normalized:
        return []
    tokens = [part for part in re.split(r"[\s\-_]+", normalized) if part]
    if tokens:
        return tokens
    return [normalized]


def project_aliases(project_dir: Path) -> list[str]:
    state = load_state(project_dir)
    recall = read_json(project_dir / PROJECT_RECALL_FILE, {})
    profile = read_json(project_dir / "product_profile.json", {})
    values = [
        state.get("project_name", ""),
        profile.get("product_name", ""),
        profile.get("brand_name", ""),
    ]
    values.extend(recall.get("aliases", []))
    unique = []
    for value in values:
        normalized = (value or "").strip()
        if normalized and normalized not in unique:
            unique.append(normalized)
    return unique


def score_project_match(query: str, aliases: list[str]) -> int:
    normalized_query = (query or "").strip().lower()
    if not normalized_query:
        return 0
    best = 0
    query_tokens = tokenize_simple(normalized_query)
    for alias in aliases:
        normalized_alias = alias.strip().lower()
        if not normalized_alias:
            continue
        score = 0
        if normalized_query == normalized_alias:
            score += 100
        elif normalized_query in normalized_alias or normalized_alias in normalized_query:
            score += 70
        alias_tokens = tokenize_simple(normalized_alias)
        shared_tokens = len(set(query_tokens) & set(alias_tokens))
        score += shared_tokens * 10
        shared_chars = len(set(normalized_query) & set(normalized_alias))
        score += min(shared_chars, 8)
        best = max(best, score)
    return best


def iter_project_dirs(output_root: Path) -> list[Path]:
    if not output_root.exists():
        return []
    return sorted({path.parent for path in output_root.rglob(STATE_FILE)})


def project_summary(project_dir: Path) -> dict[str, Any]:
    state = load_state(project_dir)
    profile = read_json(project_dir / "product_profile.json", {})
    tasks_manifest = load_tasks_manifest(project_dir)
    tasks = tasks_manifest.get("tasks", [])
    latest_task = tasks[-1] if tasks else {}
    return {
        "project_dir": str(project_dir),
        "project_id": state.get("project_id", ""),
        "project_name": state.get("project_name", project_dir.name),
        "product_name": profile.get("product_name", ""),
        "brand_name": profile.get("brand_name", ""),
        "task_count": len(tasks),
        "active_task_id": state.get("active_task_id", ""),
        "latest_task_id": latest_task.get("task_id", ""),
        "latest_task_name": latest_task.get("task_name", ""),
        "aliases": project_aliases(project_dir),
    }


def find_project_candidates(query: str, output_root: Path, limit: int = 3) -> list[dict[str, Any]]:
    candidates = []
    for project_dir in iter_project_dirs(output_root):
        aliases = project_aliases(project_dir)
        score = score_project_match(query, aliases)
        if score <= 0:
            continue
        summary = project_summary(project_dir)
        summary["score"] = score
        candidates.append(summary)
    candidates.sort(key=lambda item: (-int(item.get("score", 0)), item.get("project_name", "")))
    return candidates[:limit]


def update_project_recall(project_dir: Path, query: str, summary: dict[str, Any]) -> dict[str, Any]:
    recall_path = project_dir / PROJECT_RECALL_FILE
    recall = read_json(recall_path, blank_project_recall(summary.get("project_id", ""), summary.get("project_name", "")))
    recall["last_recalled_at"] = utc_now()
    recall["last_query"] = query
    recall["last_summary"] = summary
    aliases = recall.get("aliases", [])
    project_name = summary.get("project_name", "")
    product_name = summary.get("product_name", "")
    for value in [project_name, product_name, query]:
        normalized = (value or "").strip()
        if normalized and normalized not in aliases:
            aliases.append(normalized)
    recall["aliases"] = aliases
    write_json(recall_path, recall)

    state = load_state(project_dir)
    state.setdefault("project_recall", {})
    state["project_recall"]["aliases"] = aliases
    state["project_recall"]["last_recalled_at"] = recall["last_recalled_at"]
    state["project_recall"]["last_query"] = query
    save_state(project_dir, state)
    return recall
