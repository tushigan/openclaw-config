from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

REQUIRED_PENDING_FIELDS = (
    "client_name",
    "project_name",
    "version",
    "proposed_level_1_module",
    "proposed_level_2_module",
    "proposed_project",
    "proposed_task",
    "description",
    "reason",
)
PENDING_DEDUPE_FIELDS = tuple(field for field in REQUIRED_PENDING_FIELDS if field != "version")


def _write_pending_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _clean_required_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _validate_pending_item(item: dict[str, Any]) -> None:
    missing_fields = [
        field for field in REQUIRED_PENDING_FIELDS if not _clean_required_text(item.get(field))
    ]
    if missing_fields:
        raise ValueError(f"待入库项缺少必要字段: {', '.join(missing_fields)}")


def _pending_dedupe_key(item: dict[str, Any]) -> tuple[str, ...]:
    return tuple(_clean_required_text(item.get(field)) for field in PENDING_DEDUPE_FIELDS)


def load_pending_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("待入库池格式错误：items 必须是列表。")
    return items


def add_pending_items(path: Path, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current = load_pending_items(path)
    now = datetime.now().astimezone().isoformat()
    created: list[dict[str, Any]] = []
    existing_keys = {_pending_dedupe_key(item) for item in current}

    for item in items:
        _validate_pending_item(item)
        dedupe_key = _pending_dedupe_key(item)
        if dedupe_key in existing_keys:
            continue

        pending_item = dict(item)
        pending_item["pending_id"] = pending_item.get("pending_id") or str(uuid4())
        pending_item["discovered_at"] = pending_item.get("discovered_at") or now
        pending_item["status"] = "pending-review"
        current.append(pending_item)
        created.append(pending_item)
        existing_keys.add(dedupe_key)

    _write_pending_payload(path, {"items": current})
    return created


def resolve_pending_items(path: Path, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current = load_pending_items(path)
    current_by_key = {_pending_dedupe_key(item): item for item in current}
    resolved: list[dict[str, Any]] = []
    seen_pending_ids: set[str] = set()

    for item in items:
        _validate_pending_item(item)
        matched = current_by_key.get(_pending_dedupe_key(item))
        if matched is None:
            raise ValueError("待入库项未能在公司总待入库池中找到对应记录。")

        pending_id = _clean_required_text(matched.get("pending_id"))
        if pending_id and pending_id in seen_pending_ids:
            continue

        resolved.append(matched)
        if pending_id:
            seen_pending_ids.add(pending_id)

    return resolved


def remove_pending_item(path: Path, pending_id: str) -> None:
    remaining = [item for item in load_pending_items(path) if item.get("pending_id") != pending_id]
    _write_pending_payload(path, {"items": remaining})
