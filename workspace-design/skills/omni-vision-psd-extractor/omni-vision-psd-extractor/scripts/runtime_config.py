#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


def find_openclaw_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if (candidate / "openclaw.json").exists():
            return candidate

    return Path.home() / ".openclaw"


OPENCLAW_ROOT = find_openclaw_root()
WORKSPACE_DESIGN = OPENCLAW_ROOT / "workspace-design"
WORKSPACE_MAIN = OPENCLAW_ROOT / "workspace"


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    for dotenv in [
        OPENCLAW_ROOT / ".env",
        WORKSPACE_DESIGN / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]:
        for key, value in _read_dotenv(dotenv).items():
            env.setdefault(key, value)

    extra_path = [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/opt/local/bin",
        str(WORKSPACE_DESIGN / "node_modules" / ".bin"),
    ]
    env["PATH"] = os.pathsep.join([*extra_path, env.get("PATH", "")])
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def candidate_workspaces() -> list[Path]:
    return [WORKSPACE_DESIGN, WORKSPACE_MAIN, OPENCLAW_ROOT]


def resolve_gpt_image_generator() -> Path | None:
    relative_candidates = [
        "skills/gpt-image2-gen/scripts/generate_failover.py",
        "skills/gpt-image2-gen/scripts/generate.py",
        "PSD-SKILL/gpt-image2-gen/gpt-image2-gen/scripts/generate_failover.py",
        "PSD-SKILL/gpt-image2-gen/gpt-image2-gen/scripts/generate.py",
    ]
    for workspace in candidate_workspaces():
        for rel in relative_candidates:
            candidate = workspace / rel
            if candidate.exists():
                return candidate
    return None


def resolve_nano_banana_generator() -> Path | None:
    relative_candidates = [
        "skills/nano-banana-image-gen/scripts/generate.mjs",
        ".agents/skills/nano-banana-image-gen/scripts/generate.mjs",
    ]
    for workspace in candidate_workspaces():
        for rel in relative_candidates:
            candidate = workspace / rel
            if candidate.exists():
                return candidate
    return None


def default_output_base() -> Path:
    return WORKSPACE_DESIGN / "outputs" / "omni-vision-psd-extractor"
