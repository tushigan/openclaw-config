"""Schema definitions for agency projects."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def _timestamp() -> str:
    """Generate ISO 8601 timestamp with timezone."""
    return datetime.now().astimezone().isoformat()


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    compact = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in text.strip())
    compact = "-".join(part for part in compact.split("-") if part)
    return compact.lower() or "untitled"


def build_brand_profile(
    brand_name: str,
    brand_name_en: str = "",
    industry: str = "",
    category: str = "",
    positioning: str = "",
    core_values: list[str] | None = None,
    brand_tone: str = "",
    target_audience: str = "",
) -> dict[str, Any]:
    """Build brand profile schema."""
    timestamp = _timestamp()
    return {
        "schema_version": "1.0",
        "brand_id": _slugify(brand_name),
        "brand_name": brand_name,
        "brand_name_en": brand_name_en,
        "industry": industry,
        "category": category,
        "positioning": positioning,
        "core_values": core_values or [],
        "brand_tone": brand_tone,
        "target_audience": target_audience,
        "vi_guidelines": {
            "primary_colors": [],
            "secondary_colors": [],
            "fonts": [],
            "logo_usage_notes": "",
        },
        "brand_assets_dir": "_brand-assets/",
        "historical_campaigns": [],
        "key_contacts": [],
        "notes": "",
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def build_project(
    project_dir: Path,
    brand_name: str,
    campaign_name: str,
    campaign_type: str = "integrated_marketing",
    brand_profile_exists: bool = False,
) -> dict[str, Any]:
    """Build project metadata schema."""
    timestamp = _timestamp()
    project_id = f"{_slugify(brand_name)}-{_slugify(campaign_name)}"

    return {
        "schema_version": "1.0",
        "project_id": project_id,
        "brand_name": brand_name,
        "campaign_name": campaign_name,
        "campaign_type": campaign_type,
        "current_stage": "brief_intake",
        "lifecycle_status": "active",
        "project_summary": "",
        "business_objective": "",
        "communication_objective": "",
        "target_audience": "",
        "budget_range": "",
        "timeline": {
            "start_date": "",
            "launch_date": "",
            "end_date": "",
        },
        "brand_profile_path": "../_brand-profile.json" if brand_profile_exists else "",
        "stage_checkpoints": {
            "brief_intake": {"status": "in_progress", "completed_at": "", "user_confirmed": False},
            "problem_alignment": {"status": "pending", "completed_at": "", "user_confirmed": False},
            "research": {"status": "pending", "completed_at": "", "user_confirmed": False},
            "strategy": {"status": "pending", "completed_at": "", "user_confirmed": False},
            "creative_direction": {"status": "pending", "completed_at": "", "user_confirmed": False},
            "direction_confirmation": {"status": "pending", "completed_at": "", "user_confirmed": False},
            "execution": {"status": "pending", "completed_at": "", "user_confirmed": False},
        },
        "created_at": timestamp,
        "updated_at": timestamp,
        "last_activity_at": timestamp,
    }


def build_brief() -> dict[str, Any]:
    """Build AE brief schema."""
    timestamp = _timestamp()
    return {
        "schema_version": "1.0",
        "brief_version": "1.0",
        "collected_by": "Account Executive",
        "collected_at": timestamp,
        "updated_at": timestamp,
        "client_need": "",
        "background": "",
        "business_challenge": "",
        "target_audience": "",
        "deliverables": [],
        "timeline_requirements": "",
        "budget_constraints": "",
        "mandatories": [],
        "known_information": [],
        "missing_information": [],
        "questions_to_confirm": [],
    }


def build_problem_alignment() -> dict[str, Any]:
    """Build problem and objective alignment schema."""
    timestamp = _timestamp()
    return {
        "schema_version": "1.0",
        "alignment_version": "1.0",
        "drafted_by": "Account Executive",
        "drafted_at": timestamp,
        "confirmed_at": "",
        "confirmed_by": [],  # ["AE", "Strategy Director", "Creative Director"]
        "problem_statement": "",
        "core_problem": "",
        "business_objective": "",
        "communication_objective": "",
        "target_audience": "",
        "success_criteria": [],
        "constraints": [],
        "risks": [],
    }


def build_research_request() -> dict[str, Any]:
    """Build research and material collection schema."""
    timestamp = _timestamp()
    return {
        "schema_version": "1.0",
        "request_version": "1.0",
        "requested_by": "Account Executive",
        "requested_at": timestamp,
        "updated_at": timestamp,
        "research_needs": {
            "industry_research": {"needed": False, "status": "pending", "notes": ""},
            "competitor_analysis": {"needed": False, "status": "pending", "notes": ""},
            "consumer_insights": {"needed": False, "status": "pending", "notes": ""},
            "brand_materials": {"needed": False, "status": "pending", "notes": ""},
            "product_materials": {"needed": False, "status": "pending", "notes": ""},
            "channel_context": {"needed": False, "status": "pending", "notes": ""},
            "historical_campaigns": {"needed": False, "status": "pending", "notes": ""},
        },
        "materials_available": [],
        "materials_missing": [],
    }


def build_strategy() -> dict[str, Any]:
    """Build strategy schema."""
    timestamp = _timestamp()
    return {
        "schema_version": "1.0",
        "strategy_version": "1.0",
        "created_by": "Strategy Director",
        "created_at": timestamp,
        "updated_at": timestamp,
        "problem_diagnosis": "",
        "audience_insight": "",
        "category_judgment": "",
        "competitor_judgment": "",
        "core_proposition": "",
        "communication_task": "",
        "campaign_strategy": "",
        "channel_roles": [],
        "creative_mandatories": [],
    }


def build_creative_direction() -> dict[str, Any]:
    """Build creative direction schema."""
    timestamp = _timestamp()
    return {
        "schema_version": "1.0",
        "direction_version": "1.0",
        "created_by": "Creative Director",
        "created_at": timestamp,
        "updated_at": timestamp,
        "directions": [],  # List of direction options
        "confirmed_direction": {},
        "confirmed_at": "",
        "confirmed_by": [],  # ["AE", "Strategy Director", "Creative Director"]
        "rejected_directions": [],
        "execution_boundaries": [],
        "copy_tasks": [],
        "design_tasks": [],
    }


def build_direction_option(
    direction_name: str,
    core_idea: str = "",
    creative_mechanism: str = "",
    key_message: str = "",
    visual_extensions: list[str] | None = None,
    content_extensions: list[str] | None = None,
    risks: list[str] | None = None,
) -> dict[str, Any]:
    """Build a single creative direction option."""
    return {
        "direction_name": direction_name,
        "core_idea": core_idea,
        "creative_mechanism": creative_mechanism,
        "key_message": key_message,
        "visual_extensions": visual_extensions or [],
        "content_extensions": content_extensions or [],
        "channel_adaptability": "",
        "production_feasibility": "",
        "risks": risks or [],
        "tradeoffs": "",
    }


def build_registry() -> dict[str, Any]:
    """Build project registry schema."""
    return {
        "schema_version": "1.0",
        "projects": {},  # {project_id: project_metadata}
        "brands": {},    # {brand_name: brand_directory}
    }
