#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path


MAX_EDGE = 4096
MAX_PIXELS = 16777216
MIN_EDGE = 1024

GROUP_PRIORITY = {
    "05_SUBJECT": 0,
    "01_BG": 1,
    "03_TITLE": 2,
    "02_LOGO": 3,
    "04_DECOR": 4,
    "06_LEFT_SCENE": 5,
    "07_RIGHT_SCENE": 6,
    "08_FX": 7,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def round_up_16(value: int) -> int:
    return max(16, ((int(value) + 15) // 16) * 16)


def clamp_ratio(width: int, height: int) -> tuple[int, int, list[str]]:
    notes: list[str] = []
    ratio = width / height
    if ratio > 3:
        width = int(round(height * 3))
        notes.append("长宽比超过 3:1，已按 3:1 收敛")
    elif ratio < 1 / 3:
        height = int(round(width * 3))
        notes.append("长宽比超过 1:3，已按 1:3 收敛")
    return width, height, notes


def fit_limits(width: int, height: int) -> tuple[int, int]:
    scale = 1.0
    long_edge = max(width, height)
    if long_edge > MAX_EDGE:
        scale = min(scale, MAX_EDGE / long_edge)

    pixels = width * height
    if pixels > MAX_PIXELS:
        scale = min(scale, math.sqrt(MAX_PIXELS / pixels))

    if scale < 1.0:
        width = max(MIN_EDGE, int(width * scale))
        height = max(MIN_EDGE, int(height * scale))

    return round_up_16(width), round_up_16(height)


def _scaled_size(width: int, height: int, scale: float) -> tuple[int, int]:
    return max(MIN_EDGE, int(round(width * scale))), max(MIN_EDGE, int(round(height * scale)))


def maximize_supported_size(width: int, height: int) -> tuple[int, int, list[str]]:
    notes: list[str] = []
    width, height, ratio_notes = clamp_ratio(width, height)
    notes.extend(ratio_notes)
    ratio = width / height

    scale = min(MAX_EDGE / max(width, height), math.sqrt(MAX_PIXELS / (width * height)))
    raw_w, raw_h = _scaled_size(width, height, scale)
    base_w = max(16, (raw_w // 16) * 16)
    base_h = max(16, (raw_h // 16) * 16)

    candidates: list[tuple[float, int, int, int]] = []
    for dw in range(0, 48):
        cand_w = base_w - dw * 16
        if cand_w < 16:
            break
        for dh in range(0, 48):
            cand_h = base_h - dh * 16
            if cand_h < 16:
                break
            if max(cand_w, cand_h) > MAX_EDGE:
                continue
            if cand_w * cand_h > MAX_PIXELS:
                continue
            cand_ratio = cand_w / cand_h
            if cand_ratio > 3 or cand_ratio < 1 / 3:
                continue
            ratio_error = abs(cand_ratio - ratio)
            area = cand_w * cand_h
            candidates.append((ratio_error, area, cand_w, cand_h))

    if not candidates:
        fallback_w, fallback_h = fit_limits(raw_w, raw_h)
        return fallback_w, fallback_h, notes

    max_area = max(item[1] for item in candidates)
    filtered = [item for item in candidates if item[1] >= max_area * 0.92]
    best_error, _best_area, best_w, best_h = sorted(filtered, key=lambda item: (item[0], -item[1]))[0]

    if best_error > 0.003:
        notes.append("已尽量贴近原始长宽比，并控制在端点支持上限内")
    else:
        notes.append("已按端点支持上限尽量拉高分辨率，并贴近原始长宽比")

    return best_w, best_h, notes


def mode_scale(mode: str) -> float:
    if mode == "draft":
        return 0.68
    if mode == "final":
        return 0.88
    return 1.0


def suggest_size(layer: dict, canvas: dict, mode: str) -> dict:
    target_w = int(layer["width"])
    target_h = int(layer["height"])
    max_w, max_h, notes = maximize_supported_size(target_w, target_h)
    scale = mode_scale(mode)
    width, height = fit_limits(*_scaled_size(max_w, max_h, scale))

    if width != target_w or height != target_h:
        notes.append("建议先按安全尺寸生成，再缩回目标尺寸")

    return {
        "key": layer["key"],
        "group": layer["group"],
        "name": layer.get("name", layer["key"]),
        "target_size": f"{target_w}x{target_h}",
        "suggested_size": f"{width}x{height}",
        "max_supported_size": f"{max_w}x{max_h}",
        "mode": mode,
        "notes": notes,
    }


def background_task(manifest: dict) -> dict:
    canvas = manifest["canvas"]
    return {
        "key": "background",
        "group": "01_BG",
        "name": "Rebuilt Background",
        "prompt_spec": "纯环境大背景（没有任何前景、主体IP、文字、logo）",
        "left": 0,
        "top": 0,
        "width": canvas["width"],
        "height": canvas["height"],
        "ref_path": manifest.get("layout_ref") or manifest.get("source_path", ""),
        "raw_path": manifest.get("background_raw_path", ""),
        "layer_path": manifest.get("background_raw_path", ""),
        "hidden": False,
        "kind": "background",
    }


def layer_tasks(manifest: dict) -> list[dict]:
    return [
        {
            "key": layer["key"],
            "group": layer["group"],
            "name": layer.get("name", layer["key"]),
            "prompt_spec": layer.get("prompt", layer.get("name", layer["key"])),
            "left": int(layer["left"]),
            "top": int(layer["top"]),
            "width": int(layer["width"]),
            "height": int(layer["height"]),
            "ref_path": layer.get("ref_path", ""),
            "raw_path": layer.get("raw_path", ""),
            "layer_path": layer.get("layer_path", ""),
            "hidden": bool(layer.get("hidden", False)),
            "lossless_extract": bool(layer.get("lossless_extract", False)),
            "kind": "layer",
        }
        for layer in manifest.get("layers", [])
    ]


def build_size_plan(manifest: dict, mode: str) -> list[dict]:
    canvas = manifest["canvas"]
    tasks = [background_task(manifest), *layer_tasks(manifest)]
    return [suggest_size(task, canvas, mode) for task in tasks]


def choose_anchor_key(tasks: list[dict], preferred_key: str | None = None) -> str:
    if preferred_key:
        match = next((task for task in tasks if task["key"] == preferred_key), None)
        if match:
            return preferred_key

    subject_candidates = [task for task in tasks if task["group"] == "05_SUBJECT"]
    if subject_candidates:
        subject_candidates.sort(key=lambda task: task["width"] * task["height"], reverse=True)
        return subject_candidates[0]["key"]

    background = next((task for task in tasks if task["key"] == "background"), None)
    if background:
        return "background"

    tasks_sorted = sorted(tasks, key=lambda task: (GROUP_PRIORITY.get(task["group"], 99), -(task["width"] * task["height"])))
    return tasks_sorted[0]["key"] if tasks_sorted else "background"


EXTRACTION_MD_PATH = Path(__file__).parent.parent / "references" / "万物提取.md"
_EXTRACTION_MD_CACHE = None

def get_extraction_md() -> str:
    global _EXTRACTION_MD_CACHE
    if _EXTRACTION_MD_CACHE is not None:
        return _EXTRACTION_MD_CACHE
    try:
        path = EXTRACTION_MD_PATH
        if path.exists():
            _EXTRACTION_MD_CACHE = path.read_text(encoding="utf-8")
        else:
            _EXTRACTION_MD_CACHE = "【警告：万物提取.md 未找到，退化为基础要求：必须保证主体不变且背景填纯绿色#00ff00】"
    except Exception as e:
        print(f"Warning: Failed to load extraction MD: {e}")
        _EXTRACTION_MD_CACHE = "【警告：万物提取.md 读取失败】"
    return _EXTRACTION_MD_CACHE


def build_task_prompt(task: dict, anchor_task: dict, size_entry: dict, mode: str, anchor_key: str) -> str:
    # Prompt is now hardcoded in extract_layers.py to ensure 100% precision.
    return ""


def build_parallel_plan(manifest: dict, mode: str = "max", preferred_anchor_key: str | None = None) -> dict:
    size_plan = build_size_plan(manifest, mode)
    tasks = [background_task(manifest), *layer_tasks(manifest)]
    size_map = {entry["key"]: entry for entry in size_plan}
    anchor_key = choose_anchor_key(tasks, preferred_anchor_key)
    anchor_task = next(task for task in tasks if task["key"] == anchor_key)

    enriched_tasks: list[dict] = []
    for idx, task in enumerate(tasks):
        size_entry = size_map[task["key"]]
        task_status = "pending"
        role = "anchor" if task["key"] == anchor_key else "parallel"
        enriched_tasks.append(
            {
                **task,
                "role": role,
                "priority": GROUP_PRIORITY.get(task["group"], 99),
                "status": task_status,
                "depends_on": [] if task["key"] == anchor_key else [anchor_key],
                "size_plan": size_entry,
                "prompt_spec": task.get("prompt_spec", task.get("name", task["key"])),
                "prompt": build_task_prompt(task, anchor_task, size_entry, mode, anchor_key),
                "sequence": idx,
            }
        )

    parallel_tasks = [task for task in enriched_tasks if task["key"] != anchor_key]
    ready_queue = [anchor_key]

    return {
        "generated_at": utc_now(),
        "mode": mode,
        "anchor_key": anchor_key,
        "anchor_task": next(task for task in enriched_tasks if task["key"] == anchor_key),
        "ready_queue": ready_queue,
        "parallel_queue": [task["key"] for task in parallel_tasks],
        "tasks": enriched_tasks,
    }


def build_initial_state(plan: dict) -> dict:
    tasks = {}
    for task in plan["tasks"]:
        tasks[task["key"]] = {
            "status": "pending",
            "attempts": 0,
            "updated_at": plan["generated_at"],
            "error": "",
            "result_path": "",
        }

    return {
        "generated_at": plan["generated_at"],
        "mode": plan["mode"],
        "phase": "bootstrap",
        "anchor_key": plan["anchor_key"],
        "anchor_completed": False,
        "released_at": None,
        "tasks": tasks,
    }
