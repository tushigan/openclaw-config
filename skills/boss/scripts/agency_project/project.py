"""Agency project management utilities."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from .schemas import (
    _slugify,
    _timestamp,
    build_brand_profile,
    build_brief,
    build_creative_direction,
    build_problem_alignment,
    build_project,
    build_registry,
    build_research_request,
    build_strategy,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON file with proper formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    """Read JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_project_dirs(project_dir: Path) -> None:
    """Create project directory structure."""
    for relative in (
        "materials/research",
        "materials/reference",
        "materials/client-assets",
        "outputs/copy",
        "outputs/design",
        "outputs/final",
    ):
        (project_dir / relative).mkdir(parents=True, exist_ok=True)


def _ensure_brand_dirs(brand_dir: Path) -> None:
    """Create brand directory structure."""
    for relative in (
        "_brand-assets/logos",
        "_brand-assets/vi-manual",
        "_brand-assets/reference-images",
    ):
        (brand_dir / relative).mkdir(parents=True, exist_ok=True)


def _update_registry(
    workspace_root: Path,
    brand_name: str,
    brand_dir: Path,
    project_id: str,
    project_dir: Path,
    campaign_name: str,
) -> None:
    """Update project registry."""
    registry_path = workspace_root / "projects" / "_registry.json"

    if registry_path.exists():
        registry = _read_json(registry_path)
    else:
        registry = build_registry()

    # Update brands index
    registry["brands"][brand_name] = str(brand_dir.relative_to(workspace_root / "projects"))

    # Update projects index
    registry["projects"][project_id] = {
        "brand_name": brand_name,
        "campaign_name": campaign_name,
        "project_path": str(project_dir.relative_to(workspace_root / "projects")),
        "created_at": _timestamp(),
        "status": "active",
    }

    _write_json(registry_path, registry)


def create_or_get_brand(
    workspace_root: Path,
    brand_name: str,
    brand_name_en: str = "",
    industry: str = "",
    category: str = "",
    positioning: str = "",
    core_values: list[str] | None = None,
    brand_tone: str = "",
    target_audience: str = "",
) -> Path:
    """Create brand profile or return existing brand directory."""
    brand_dir = workspace_root / "projects" / brand_name
    profile_path = brand_dir / "_brand-profile.json"

    if profile_path.exists():
        # Brand already exists, return directory
        return brand_dir

    # Create new brand
    _ensure_brand_dirs(brand_dir)

    profile = build_brand_profile(
        brand_name=brand_name,
        brand_name_en=brand_name_en,
        industry=industry,
        category=category,
        positioning=positioning,
        core_values=core_values,
        brand_tone=brand_tone,
        target_audience=target_audience,
    )

    _write_json(profile_path, profile)
    return brand_dir


def create_agency_project(
    workspace_root: Path,
    brand_name: str,
    campaign_name: str,
    campaign_type: str = "integrated_marketing",
    brand_info: dict[str, Any] | None = None,
) -> Path:
    """Create a new agency project with brand profile if needed."""
    # Create or get brand
    brand_info = brand_info or {}
    brand_dir = create_or_get_brand(
        workspace_root=workspace_root,
        brand_name=brand_name,
        brand_name_en=brand_info.get("brand_name_en", ""),
        industry=brand_info.get("industry", ""),
        category=brand_info.get("category", ""),
        positioning=brand_info.get("positioning", ""),
        core_values=brand_info.get("core_values"),
        brand_tone=brand_info.get("brand_tone", ""),
        target_audience=brand_info.get("target_audience", ""),
    )

    # Create project directory
    project_dir = brand_dir / campaign_name
    if project_dir.exists():
        raise FileExistsError(f"Project already exists: {project_dir}")

    _ensure_project_dirs(project_dir)

    # Create project files
    brand_profile_exists = (brand_dir / "_brand-profile.json").exists()
    project_payload = build_project(
        project_dir=project_dir,
        brand_name=brand_name,
        campaign_name=campaign_name,
        campaign_type=campaign_type,
        brand_profile_exists=brand_profile_exists,
    )

    _write_json(project_dir / "project.json", project_payload)
    _write_json(project_dir / "brief.json", build_brief())
    _write_json(project_dir / "problem-alignment.json", build_problem_alignment())
    _write_json(project_dir / "research-request.json", build_research_request())
    _write_json(project_dir / "strategy.json", build_strategy())
    _write_json(project_dir / "creative-direction.json", build_creative_direction())

    # Update registry
    _update_registry(
        workspace_root=workspace_root,
        brand_name=brand_name,
        brand_dir=brand_dir,
        project_id=project_payload["project_id"],
        project_dir=project_dir,
        campaign_name=campaign_name,
    )

    return project_dir


def find_brand_profile(workspace_root: Path, brand_name: str) -> Path | None:
    """Find brand profile by brand name."""
    registry_path = workspace_root / "projects" / "_registry.json"

    if not registry_path.exists():
        return None

    registry = _read_json(registry_path)

    if brand_name not in registry["brands"]:
        return None

    brand_relative_path = registry["brands"][brand_name]
    brand_dir = workspace_root / "projects" / brand_relative_path
    profile_path = brand_dir / "_brand-profile.json"

    if not profile_path.exists():
        return None

    return profile_path


def find_active_project(workspace_root: Path, brand_name: str) -> Path | None:
    """Find the most recent active project for a brand."""
    registry_path = workspace_root / "projects" / "_registry.json"

    if not registry_path.exists():
        return None

    registry = _read_json(registry_path)

    # Find all active projects for this brand
    active_projects = [
        (pid, pdata)
        for pid, pdata in registry["projects"].items()
        if pdata["brand_name"] == brand_name and pdata["status"] == "active"
    ]

    if not active_projects:
        return None

    # Return the most recent one
    active_projects.sort(key=lambda x: x[1]["created_at"], reverse=True)
    project_relative_path = active_projects[0][1]["project_path"]

    return workspace_root / "projects" / project_relative_path


def archive_material(
    project_dir: Path,
    source_path: Path,
    material_type: str,  # "research", "reference", "client-assets"
    notes: str = "",
) -> Path:
    """Archive material into project directory."""
    destination = project_dir / "materials" / material_type / source_path.name

    if destination.exists():
        destination = destination.with_name(f"{uuid4().hex[:8]}-{source_path.name}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)

    return destination


def update_stage_checkpoint(
    project_dir: Path,
    stage: str,
    status: str,
    user_confirmed: bool = False,
) -> None:
    """Update project stage checkpoint."""
    project_path = project_dir / "project.json"
    project_payload = _read_json(project_path)

    if stage not in project_payload["stage_checkpoints"]:
        raise ValueError(f"Invalid stage: {stage}")

    checkpoint = project_payload["stage_checkpoints"][stage]
    checkpoint["status"] = status
    checkpoint["user_confirmed"] = user_confirmed

    if status == "completed":
        checkpoint["completed_at"] = _timestamp()

    project_payload["current_stage"] = stage
    project_payload["updated_at"] = _timestamp()
    project_payload["last_activity_at"] = project_payload["updated_at"]

    _write_json(project_path, project_payload)
