from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from quote_skill.catalog_pending import add_pending_items, resolve_pending_items
from quote_skill.catalog_sync import ensure_catalog_json
from quote_skill.project import record_outputs
from quote_skill.renderers import render_html, render_pdf, render_xlsx
from quote_skill.validators import validate_quote_content

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK = SKILL_ROOT / "assets" / "standards" / "service-catalog.xlsx"
DEFAULT_CATALOG_JSON = SKILL_ROOT / "data" / "service-catalog.json"
DEFAULT_PENDING_POOL = SKILL_ROOT / "data" / "catalog-pending-review.json"
DEFAULT_HTML_TEMPLATE = SKILL_ROOT / "assets" / "templates" / "quote.html"
DEFAULT_XLSX_TEMPLATE = SKILL_ROOT / "assets" / "templates" / "quote.xlsx"
DEFAULT_HTML_TO_PDF_SCRIPT = SKILL_ROOT / "scripts" / "render_html_to_pdf.mjs"

def _project_metadata(project_dir: Path) -> tuple[str, str]:
    project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
    return (
        str(project_payload.get("client_name", "")).strip(),
        str(project_payload.get("project_name", "")).strip(),
    )


def _build_pending_pool_items(
    pending_catalog_items: list[dict[str, Any]],
    project_dir: Path | None,
    version: str | None,
) -> list[dict[str, Any]]:
    if not pending_catalog_items:
        return []
    if project_dir is None or not version:
        raise ValueError("检测到待入库条目，但缺少 project-dir 或 version，无法写入公司总待入库池。")

    client_name, project_name = _project_metadata(project_dir)
    enriched_items: list[dict[str, Any]] = []
    for item in pending_catalog_items:
        enriched_items.append(
            {
                "client_name": client_name,
                "project_name": project_name,
                "version": version,
                **item,
            }
        )
    return enriched_items


def _validate_pending_context(
    pending_catalog_items: list[dict[str, Any]],
    project_dir: Path | None,
    version: str | None,
) -> None:
    if pending_catalog_items and (project_dir is None or not version):
        raise ValueError("检测到待入库条目，但缺少 project-dir 或 version，无法写入公司总待入库池。")


def _collect_catalog_refs_used(content: dict[str, Any]) -> list[str]:
    refs: set[str] = set()
    for stage in content.get("stages", []):
        for project in stage.get("projects", []):
            refs.update(str(ref).strip() for ref in project.get("service_catalog_refs", []) if str(ref).strip())
            for task in project.get("tasks", []):
                refs.update(
                    str(ref).strip() for ref in task.get("service_catalog_refs", []) if str(ref).strip()
                )
    return sorted(refs)


def _catalog_service_id_set(catalog_payload: dict[str, Any]) -> set[str]:
    services = catalog_payload.get("services")
    if not isinstance(services, list):
        raise ValueError("服务清单数据格式错误：services 必须是列表。")

    return {
        str(service.get("service_id")).strip()
        for service in services
        if isinstance(service, dict) and str(service.get("service_id", "")).strip()
    }


def _validate_catalog_refs_exist(content: dict[str, Any], catalog_payload: dict[str, Any]) -> list[str]:
    catalog_service_ids = _catalog_service_id_set(catalog_payload)
    used_refs = _collect_catalog_refs_used(content)
    missing_refs: list[str] = []

    for ref in used_refs:
        if ref not in catalog_service_ids:
            missing_refs.append(ref)

    if missing_refs:
        missing_text = "、".join(sorted(missing_refs))
        raise ValueError(f"存在不存在的服务清单引用：{missing_text}。请先改成当前服务清单里的有效 service_id。")

    return used_refs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--formats", nargs="+", required=True, choices=["html", "pdf", "xlsx"])
    parser.add_argument("--html-template", default=str(DEFAULT_HTML_TEMPLATE))
    parser.add_argument("--xlsx-template", default=str(DEFAULT_XLSX_TEMPLATE))
    parser.add_argument("--project-dir")
    parser.add_argument("--version")
    parser.add_argument("--service-catalog-workbook", default=str(DEFAULT_WORKBOOK))
    parser.add_argument("--service-catalog-json", default=str(DEFAULT_CATALOG_JSON))
    parser.add_argument("--pending-pool", default=str(DEFAULT_PENDING_POOL))
    parser.add_argument("--node-bin")
    parser.add_argument("--html-to-pdf-script", default=str(DEFAULT_HTML_TO_PDF_SCRIPT))
    args = parser.parse_args()

    workbook_path = Path(args.service_catalog_workbook)
    catalog_json_path = Path(args.service_catalog_json)
    pending_pool_path = Path(args.pending_pool)
    project_dir = Path(args.project_dir) if args.project_dir else None

    catalog_payload = ensure_catalog_json(workbook_path, catalog_json_path)

    content = json.loads(Path(args.content).read_text(encoding="utf-8"))
    content = validate_quote_content(content)
    catalog_refs_used = _validate_catalog_refs_exist(content, catalog_payload)
    pending_catalog_items = content.get("pending_catalog_items", [])
    _validate_pending_context(
        pending_catalog_items,
        project_dir=project_dir,
        version=args.version,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_outputs: list[str] = []
    html_path = output_dir / "quote.html"

    if "html" in args.formats:
        render_html(content, template_path=Path(args.html_template), output_path=html_path)
        generated_outputs.append(html_path.name)

    if "pdf" in args.formats:
        pdf_path = output_dir / "quote.pdf"
        render_pdf(content, pdf_path, template_path=Path(args.html_template))
        generated_outputs.append(pdf_path.name)

    if "xlsx" in args.formats:
        xlsx_path = output_dir / "quote.xlsx"
        render_xlsx(content, xlsx_path, template_path=Path(args.xlsx_template))
        generated_outputs.append(xlsx_path.name)

    created_pending: list[dict[str, Any]] = []
    pending_records_for_version: list[dict[str, Any]] = []
    pending_pool_item_ids: list[str] = []
    if pending_catalog_items:
        pending_pool_items = _build_pending_pool_items(
            pending_catalog_items,
            project_dir=project_dir,
            version=args.version,
        )
        created_pending = add_pending_items(pending_pool_path, pending_pool_items)
        pending_records_for_version = resolve_pending_items(pending_pool_path, pending_pool_items)
        pending_pool_item_ids = [item["pending_id"] for item in pending_records_for_version]

    if project_dir and args.version:
        relative_outputs = [f"versions/{args.version}/{name}" for name in generated_outputs]
        record_outputs(
            project_dir,
            args.version,
            relative_outputs,
            case_type=content.get("case_type", ""),
            detected_new_catalog_items=pending_records_for_version or created_pending,
            catalog_refs_used=catalog_refs_used,
            pending_pool_item_ids=pending_pool_item_ids,
        )


if __name__ == "__main__":
    main()
