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
    client_name: str = "",
    brand_name_en: str = "",
    industry: str = "",
    category: str = "",
    positioning: str = "",
    core_values: list[str] | None = None,
    brand_tone: str = "",
    target_audience: str = "",
) -> Path:
    """
    Create brand profile or return existing brand directory.

    Args:
        workspace_root: OpenClaw root directory
        brand_name: Brand name
        client_name: Client name (optional, defaults to brand_name if not provided)
        brand_name_en: English brand name
        industry: Industry
        category: Category
        positioning: Brand positioning
        core_values: Core values
        brand_tone: Brand tone
        target_audience: Target audience

    Returns:
        Path to brand directory (client_name/brand_name/)
    """
    # 如果没有指定客户名，使用品牌名作为客户名（向后兼容）
    if not client_name:
        client_name = brand_name

    # 使用"客户→品牌"两层结构
    brand_dir = workspace_root / "projects" / client_name / brand_name
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
        client_name=brand_info.get("client_name", ""),
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
    """
    Find brand profile by brand name.

    This function is compatible with both old structure (brand_name/)
    and new structure (client_name/brand_name/).
    """
    projects_root = workspace_root / "projects"

    # Method 1: Try registry (preferred)
    registry_path = projects_root / "_registry.json"
    if registry_path.exists():
        registry = _read_json(registry_path)
        if brand_name in registry.get("brands", {}):
            brand_relative_path = registry["brands"][brand_name]
            profile_path = projects_root / brand_relative_path / "_brand-profile.json"
            if profile_path.exists():
                return profile_path

    # Method 2: Search all client directories (fallback for unregistered brands)
    for client_dir in projects_root.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue

        # Try client_name/brand_name/
        profile_path = client_dir / brand_name / "_brand-profile.json"
        if profile_path.exists():
            return profile_path

        # Try brand_name/ (old structure compatibility)
        if client_dir.name == brand_name:
            profile_path = client_dir / "_brand-profile.json"
            if profile_path.exists():
                return profile_path

    return None


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


def detect_conflicts(
    workspace_root: Path,
    brand_name: str,
    new_info: dict[str, Any],
) -> dict[str, Any]:
    """Detect conflicts between brand profile and new information.

    Args:
        workspace_root: Workspace root directory
        brand_name: Brand name
        new_info: New brand information to check

    Returns:
        {
            "has_conflict": bool,
            "conflicts": [{"field": str, "archived": Any, "new_input": Any, "severity": str}],
            "supplements": [{"field": str, "archived": Any, "new_input": Any}]
        }
    """
    profile_path = find_brand_profile(workspace_root, brand_name)

    if not profile_path:
        return {"has_conflict": False, "conflicts": [], "supplements": []}

    profile = _read_json(profile_path)

    # Define field severity
    HIGH_SEVERITY_FIELDS = {
        "industry",
        "positioning",
        "brand_tone",
    }

    # vi_guidelines is a nested object, needs special handling
    VI_GUIDELINE_FIELDS = {
        "primary_colors",
        "secondary_colors",
        "fonts",
        "logo_usage_notes",
    }

    conflicts = []
    supplements = []

    # Check scalar fields
    for field, new_value in new_info.items():
        if field == "vi_guidelines":
            # Handle nested vi_guidelines
            archived_vi = profile.get("vi_guidelines", {})
            new_vi = new_value if isinstance(new_value, dict) else {}

            for vi_field, vi_new_value in new_vi.items():
                if vi_field in VI_GUIDELINE_FIELDS:
                    vi_archived_value = archived_vi.get(vi_field)

                    # Skip if new value is empty or None
                    if not vi_new_value or (isinstance(vi_new_value, list) and len(vi_new_value) == 0):
                        continue

                    # Check if archived value exists and is non-empty
                    if vi_archived_value and (
                        (isinstance(vi_archived_value, list) and len(vi_archived_value) > 0) or
                        (isinstance(vi_archived_value, str) and vi_archived_value.strip())
                    ):
                        # Compare values
                        if vi_archived_value != vi_new_value:
                            conflicts.append({
                                "field": f"vi_guidelines.{vi_field}",
                                "archived": vi_archived_value,
                                "new_input": vi_new_value,
                                "severity": "high"
                            })
                    else:
                        # Supplement: archived is empty, new has value
                        supplements.append({
                            "field": f"vi_guidelines.{vi_field}",
                            "archived": vi_archived_value,
                            "new_input": vi_new_value
                        })
            continue

        # Skip if new value is empty or None
        if not new_value or (isinstance(new_value, str) and not new_value.strip()):
            continue

        archived_value = profile.get(field)

        # For list fields (core_values, competitors, etc.)
        if isinstance(new_value, list):
            archived_list = archived_value if isinstance(archived_value, list) else []

            # Skip if new list is empty
            if len(new_value) == 0:
                continue

            # Check if archived list is non-empty
            if len(archived_list) > 0:
                # Check if new items are truly new (not just reordering)
                new_items = [item for item in new_value if item not in archived_list]

                if new_items:
                    # New items exist - supplement
                    supplements.append({
                        "field": field,
                        "archived": archived_list,
                        "new_input": new_value
                    })
            else:
                # Archived is empty - supplement
                supplements.append({
                    "field": field,
                    "archived": archived_list,
                    "new_input": new_value
                })
        else:
            # Scalar field (string, etc.)
            # Check if archived value exists and is non-empty
            if archived_value and (isinstance(archived_value, str) and archived_value.strip()):
                # Compare values
                if archived_value.strip() != str(new_value).strip():
                    severity = "high" if field in HIGH_SEVERITY_FIELDS else "low"
                    conflicts.append({
                        "field": field,
                        "archived": archived_value,
                        "new_input": new_value,
                        "severity": severity
                    })
            else:
                # Archived is empty - supplement
                supplements.append({
                    "field": field,
                    "archived": archived_value,
                    "new_input": new_value
                })

    has_conflict = any(c["severity"] == "high" for c in conflicts)

    return {
        "has_conflict": has_conflict,
        "conflicts": conflicts,
        "supplements": supplements
    }


def update_brand_profile_field(
    workspace_root: Path,
    brand_name: str,
    field: str,
    value: Any,
    operation: str = "replace",  # "replace" or "append"
) -> dict[str, Any]:
    """Update a field in brand profile.

    Args:
        workspace_root: Workspace root directory
        brand_name: Brand name
        field: Field name (supports nested fields like "vi_guidelines.primary_colors")
        value: New value
        operation: "replace" to replace value, "append" to append to list

    Returns:
        {"success": bool, "message": str, "updated_at": str}
    """
    profile_path = find_brand_profile(workspace_root, brand_name)

    if not profile_path:
        return {
            "success": False,
            "message": f"Brand profile not found: {brand_name}",
            "updated_at": ""
        }

    profile = _read_json(profile_path)

    # Handle nested fields (e.g., "vi_guidelines.primary_colors")
    if "." in field:
        parts = field.split(".", 1)
        parent_field = parts[0]
        child_field = parts[1]

        if parent_field not in profile:
            profile[parent_field] = {}

        parent_obj = profile[parent_field]

        if operation == "append" and isinstance(value, list):
            # Append to list
            existing = parent_obj.get(child_field, [])
            if not isinstance(existing, list):
                existing = []

            # Merge: add new items that don't exist
            for item in value:
                if item not in existing:
                    existing.append(item)

            parent_obj[child_field] = existing
        else:
            # Replace
            parent_obj[child_field] = value
    else:
        # Top-level field
        if operation == "append" and isinstance(value, list):
            # Append to list
            existing = profile.get(field, [])
            if not isinstance(existing, list):
                existing = []

            # Merge: add new items that don't exist
            for item in value:
                if item not in existing:
                    existing.append(item)

            profile[field] = existing
        else:
            # Replace
            profile[field] = value

    # Update timestamp
    profile["updated_at"] = _timestamp()

    # Write back
    _write_json(profile_path, profile)

    return {
        "success": True,
        "message": f"Updated field '{field}' with operation '{operation}'",
        "updated_at": profile["updated_at"]
    }
