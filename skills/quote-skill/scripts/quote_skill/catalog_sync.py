from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quote_skill.catalog import build_catalog, parse_summary_sheet


def _normalize_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve(strict=False))


def _load_catalog_payload(output_path: Path) -> dict[str, Any] | None:
    if not output_path.exists():
        return None

    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def _has_minimum_catalog_shape(
    payload: dict[str, Any] | None, workbook_path: Path, sheet_name: str
) -> bool:
    if payload is None:
        return False
    if not payload.get("source_file"):
        return False
    if payload.get("source_sheet") != sheet_name:
        return False
    if not isinstance(payload.get("services"), list):
        return False
    return _normalize_path(payload["source_file"]) == _normalize_path(workbook_path)


def needs_catalog_rebuild(
    workbook_path: Path, output_path: Path, sheet_name: str = "汇总表"
) -> bool:
    if not output_path.exists():
        return True

    if workbook_path.stat().st_mtime > output_path.stat().st_mtime:
        return True

    payload = _load_catalog_payload(output_path)
    if not _has_minimum_catalog_shape(payload, workbook_path, sheet_name):
        return True

    parse_summary_sheet(workbook_path, sheet_name=sheet_name)
    return False


def ensure_catalog_json(
    workbook_path: Path, output_path: Path, sheet_name: str = "汇总表"
) -> dict[str, Any]:
    if needs_catalog_rebuild(workbook_path, output_path, sheet_name=sheet_name):
        return build_catalog(workbook_path, output_path, sheet_name=sheet_name)
    payload = _load_catalog_payload(output_path)
    if not _has_minimum_catalog_shape(payload, workbook_path, sheet_name):
        return build_catalog(workbook_path, output_path, sheet_name=sheet_name)
    return payload
