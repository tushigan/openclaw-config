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

    # This skill has its own model binding. Keep it local to omni and let it
    # override generic OpenClaw env values without touching global config.
    for dotenv in [
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]:
        for key, value in _read_dotenv(dotenv).items():
            if key.startswith("OPENCLAW_BOUND_"):
                env[key] = value

    env.setdefault("OMNI_FORCE_BOUND_GEMINI", "1")

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


def resolve_bound_gemini_config(env: dict[str, str] | None = None) -> dict[str, str]:
    runtime_env = env or load_runtime_env()
    base_url = runtime_env.get("OPENCLAW_BOUND_BASE_URL", "https://s.lconai.com/").rstrip("/")
    model = (
        runtime_env.get("OPENCLAW_BOUND_MODEL_ID")
        or runtime_env.get("OPENCLAW_BOUND_MODEL")
        or runtime_env.get("OPENCLAW_BOUND_MODEL_NAME")
        or "gemini-3.1-flash-image-preview"
    )
    api_key = runtime_env.get("OPENCLAW_BOUND_API_KEY", "")
    return {
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
        "endpoint": f"{base_url}/v1beta/models/{model}:generateContent",
        "provider": "s.lconai",
    }


def default_output_base() -> Path:
    return WORKSPACE_DESIGN / "outputs" / "omni-vision-psd-extractor"
