#!/usr/bin/env python3
"""Workflow helpers for the dreamina-reference-video skill."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    Image = None

from .state_manager import StateManager, ProjectConfig, RunState, Constraint

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = Path.cwd()
DEFAULT_OUTPUT_SUBDIR = Path("outputs") / "dreamina-reference-video"
PROJECTS_SUBDIR = Path("projects")
PROJECT_FILE_NAME = "project.json"
PROJECT_SUMMARY_NAME = "project-summary.md"
RUNS_SUBDIR_NAME = "runs"
CANONICAL_SUBDIR_NAME = "canonical"

REFERENCE_FILE_MAP = {
    "original": "original.png",
    "identity_source": "identity-source.png",
    "identity_board": "identity-board.png",
    "storyboard": "storyboard.png",
}

REQUIRED_PATHS = [
    "prompts",
    "refs",
    "dreamina",
    "dreamina/downloads",
]

DEFAULTS = {
    "project_name": "",
    "project_slug": "",
    "ratio": "16:9",
    "duration": 5,
    "quality_tier": "draft",
    "language": "zh-CN",
    "storyboard_strategy": "auto_beats",
    "storyboard_panel_count_override": None,
    "storyboard_beats_override": [],
    "identity_strategy": None,
    "identity_anchor_rules": [],
    "identity_structure": [],
    "identity_forbidden": [],
    "has_existing_references": False,
    "anchor_elements": [],
    "notes": "",
    "normalize_references": True,
}

RATIO_IMAGE_SIZES = {
    "1:1": "2048x2048",
    "3:4": "1536x2048",
    "4:3": "2048x1536",
    "16:9": "2560x1440",
    "9:16": "1440x2560",
    "21:9": "2688x1152",
}


def first_existing_path(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_gpt_image_script() -> Path:
    env_value = os.getenv("GPT_IMAGE2_GEN_SCRIPT")
    if env_value:
        return Path(env_value).expanduser()

    candidates = [
        SKILL_ROOT.parents[1] / "workspace-design" / "skills" / "gpt-image2-gen" / "scripts" / "generate.py",
        SKILL_ROOT.parents[1] / "workspace" / "skills" / "gpt-image2-gen" / "scripts" / "generate.py",
        SKILL_ROOT.parents[1] / "gpt-image2-gen" / "scripts" / "generate.py",
        Path.home() / ".codex" / "skills" / "gpt-image2-gen" / "scripts" / "generate.py",
    ]
    return first_existing_path(candidates)


def resolve_gpt_image_config() -> Path:
    env_value = os.getenv("GPT_IMAGE2_GEN_ENV_FILE")
    if env_value:
        return Path(env_value).expanduser()

    script_path = resolve_gpt_image_script()
    candidates = [
        script_path.parents[1] / ".env.local",
        SKILL_ROOT.parents[1] / "workspace-design" / "skills" / "gpt-image2-gen" / ".env.local",
        SKILL_ROOT.parents[1] / "workspace" / "skills" / "gpt-image2-gen" / ".env.local",
        Path.home() / ".codex" / "skills" / "gpt-image2-gen" / ".env.local",
    ]
    return first_existing_path(candidates)


def resolve_dreamina_bin() -> str:
    env_value = os.getenv("DREAMINA_BIN")
    if env_value:
        return str(Path(env_value).expanduser())
    return shutil.which("dreamina") or str(Path.home() / ".local" / "bin" / "dreamina")


GTP_IMAGE_SCRIPT = resolve_gpt_image_script()
DREAMINA_BIN = resolve_dreamina_bin()


@dataclass
class PreflightResult:
    ok: bool
    checks: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": self.checks}


def slugify(value: str) -> str:
    raw = value.strip()
    value = raw.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    value = re.sub(r"-{2,}", "-", value)
    if value:
        return value
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    return f"brief-{digest}"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_run_layout(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    for relative in REQUIRED_PATHS:
        (run_dir / relative).mkdir(parents=True, exist_ok=True)


def ensure_project_layout(project_dir: Path) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / RUNS_SUBDIR_NAME).mkdir(parents=True, exist_ok=True)
    (project_dir / CANONICAL_SUBDIR_NAME).mkdir(parents=True, exist_ok=True)


def normalize_reference_image(
    source: Path, target: Path, max_edge: int = 1920, max_size_mb: float = 3.0
) -> dict[str, Any]:
    """
    归一化参考图到安全工作尺寸

    Args:
        source: 源图片路径
        target: 目标图片路径
        max_edge: 最大边长（像素）
        max_size_mb: 最大文件大小（MB）

    Returns:
        manifest: 归一化信息字典
    """
    if Image is None:
        raise ImportError("需要安装 Pillow: pip install Pillow")

    if not source.exists():
        raise FileNotFoundError(f"源图片不存在: {source}")

    original_size = source.stat().st_size
    img = Image.open(source)
    original_width, original_height = img.size
    original_format = img.format or source.suffix[1:].upper()

    # 计算目标尺寸
    width, height = img.size
    changed = False

    if max(width, height) > max_edge:
        ratio = max_edge / max(width, height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        changed = True

    # 处理透明通道
    alpha_flattened = False
    if img.mode in ('RGBA', 'LA', 'P'):
        if img.mode == 'P' and 'transparency' in img.info:
            img = img.convert('RGBA')
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'LA':
                background.paste(img, mask=img.split()[1])
            else:
                background.paste(img, mask=img.split()[3])
            img = background
            alpha_flattened = True
            changed = True

    # 转换为 RGB（如果还不是）
    if img.mode != 'RGB':
        img = img.convert('RGB')
        changed = True

    # 保存
    target.parent.mkdir(parents=True, exist_ok=True)

    # 决定输出格式
    max_bytes = int(max_size_mb * 1024 * 1024)
    if source.suffix.lower() == '.png' and original_size <= max_bytes and not changed:
        # 小 PNG 保持原样
        img.save(target, 'PNG', optimize=True)
        output_format = 'PNG'
    else:
        # 其他情况输出 JPEG
        img.save(target, 'JPEG', quality=90, optimize=True, progressive=True)
        output_format = 'JPEG'
        changed = True

    normalized_size = target.stat().st_size
    normalized_width, normalized_height = img.size

    return {
        "source_path": str(source),
        "source_format": original_format,
        "source_width": original_width,
        "source_height": original_height,
        "source_bytes": original_size,
        "normalized_path": str(target),
        "normalized_format": output_format,
        "normalized_width": normalized_width,
        "normalized_height": normalized_height,
        "normalized_bytes": normalized_size,
        "alpha_flattened": alpha_flattened,
        "changed": changed,
    }


def parse_list_value(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[，,\n]", value) if item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def convert_constraints_to_structured(brief: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """
    将 brief 中的约束转换为结构化格式

    Args:
        brief: 归一化后的 brief

    Returns:
        结构化的约束字典
    """
    constraints: dict[str, list[dict[str, Any]]] = {
        "must_have": [],
        "must_not_have": [],
        "prefer": []
    }

    identity_structure = brief.get("identity_structure") or []
    identity_forbidden = brief.get("identity_forbidden") or []

    for idx, desc in enumerate(identity_structure):
        constraint = Constraint(
            id=f"structure-{idx}",
            type="must_have",
            description=desc,
            strength=0.9,
            applies_to=["identity_board", "storyboard", "video"],
            validation_mode="manual"
        )
        constraints["must_have"].append(constraint.to_dict())

    for idx, desc in enumerate(identity_forbidden):
        constraint = Constraint(
            id=f"forbidden-{idx}",
            type="must_not_have",
            description=desc,
            strength=0.9,
            applies_to=["identity_board", "storyboard", "video"],
            validation_mode="manual"
        )
        constraints["must_not_have"].append(constraint.to_dict())

    return constraints


def normalize_existing_reference_key(key: str) -> str:
    key = key.strip().lower().replace("-", "_")
    aliases = {
        "identity_source": "identity_source",
        "identitysource": "identity_source",
        "source": "identity_source",
        "identity": "identity_board",
        "identityboard": "identity_board",
        "identity_board": "identity_board",
        "story": "storyboard",
    }
    return aliases.get(key, key)


def target_storyboard_max_panels(duration: int, notes: str) -> int:
    if duration <= 3:
        max_panels = 4
    elif duration <= 5:
        max_panels = 5
    elif duration <= 7:
        max_panels = 6
    elif duration <= 10:
        max_panels = 8
    else:
        max_panels = 10

    notes = notes.strip()
    if any(keyword in notes for keyword in ("少一点", "别太碎", "简单", "简洁", "轻一些")):
        max_panels = max(3, max_panels - 1)
    if any(keyword in notes for keyword in ("细一点", "丰富一点", "多一些", "更细")):
        max_panels = min(10, max_panels + 1)
    return max_panels


def normalize_action_clause(clause: str) -> str:
    clause = clause.strip()
    clause = re.sub(r"^(先|再|然后|接着|随后|之后|最后|并且|并|同时)\s*", "", clause)
    return clause.strip("，,。；; ")


def split_action_clauses(action: str) -> list[str]:
    text = action
    for connector in ("然后", "接着", "随后", "之后", "最后", "并且", "同时", "再"):
        text = text.replace(connector, "|")
    text = re.sub(r"[，,。；;\n]+", "|", text)
    clauses = [normalize_action_clause(part) for part in text.split("|")]
    return [clause for clause in clauses if clause]


def classify_action_clause(clause: str, index: int) -> str:
    if any(keyword in clause for keyword in ("定格", "定版", "海报", "收尾", "结束", "停住", "落版")):
        return "final_pose"
    if any(keyword in clause for keyword in ("咕", "一声", "张嘴", "喊", "说", "亮相", "完成", "打开")):
        return "payoff"
    if any(keyword in clause for keyword in ("看", "望", "转向", "转头", "回头", "停顿", "注视", "看向")):
        return "attention_shift"
    if index == 0 and any(keyword in clause for keyword in ("出现", "进入", "走来", "站在", "坐着", "起身")):
        return "entry_or_idle"
    return "progression"


def describe_storyboard_beat(label: str, content: str) -> str:
    mapping = {
        "establishing": "建立空间",
        "entry_or_idle": "主体起始状态",
        "progression": "动作推进",
        "attention_shift": "注意力转移",
        "payoff": "关键动作落点",
        "final_pose": "收束定格",
    }
    prefix = mapping.get(label, "关键帧")
    return f"{prefix}：{content}"


def compress_storyboard_beats(beats: list[str], target_count: int) -> list[str]:
    if len(beats) <= target_count:
        return beats
    if target_count <= 1:
        return beats[:1]
    if target_count == 2:
        return [beats[0], beats[-1]]

    middle = beats[1:-1]
    needed_middle = target_count - 2
    if not middle:
        return beats[:target_count]
    if needed_middle == 1:
        return [beats[0], middle[len(middle) // 2], beats[-1]]

    indexes = []
    for i in range(needed_middle):
        idx = round(i * (len(middle) - 1) / (needed_middle - 1))
        indexes.append(idx)
    selected_middle = [middle[idx] for idx in sorted(set(indexes))]
    while len(selected_middle) < needed_middle:
        selected_middle.append(middle[-1])
    return [beats[0], *selected_middle[:needed_middle], beats[-1]]


def expand_storyboard_beats(beats: list[str], target_count: int) -> list[str]:
    expanded = list(beats)
    filler = "动作推进：延续上一格动作，并为下一格做过渡"
    while len(expanded) < target_count:
        expanded.insert(max(1, len(expanded) - 1), filler)
    return expanded


def apply_storyboard_panel_override(beats: list[str], panel_count: int) -> list[str]:
    panel_count = max(3, min(10, int(panel_count)))
    if len(beats) > panel_count:
        return compress_storyboard_beats(beats, panel_count)
    if len(beats) < panel_count:
        return expand_storyboard_beats(beats, panel_count)
    return beats


def build_auto_storyboard_beats(brief: dict[str, Any]) -> list[str]:
    beats = [describe_storyboard_beat("establishing", brief["scene"])]
    clauses = split_action_clauses(brief["action"])
    for index, clause in enumerate(clauses):
        beats.append(describe_storyboard_beat(classify_action_clause(clause, index), clause))

    if len(beats) == 1:
        beats.append(describe_storyboard_beat("progression", brief["action"]))

    if not any(beat.startswith("收束定格：") for beat in beats):
        beats.append(describe_storyboard_beat("final_pose", "主体收束到最终定格或关键落版"))

    max_panels = target_storyboard_max_panels(brief["duration"], str(brief.get("notes", "")))
    beats = compress_storyboard_beats(beats, max_panels)
    if len(beats) < 3:
        beats = expand_storyboard_beats(beats, 3)
    return beats


def resolve_storyboard_plan(brief: dict[str, Any]) -> tuple[list[str], int]:
    override_beats = parse_list_value(brief.get("storyboard_beats_override"))
    if override_beats:
        beats = override_beats
    else:
        beats = build_auto_storyboard_beats(brief)

    override_count = brief.get("storyboard_panel_count_override")
    if override_count not in (None, "") and not override_beats:
        beats = apply_storyboard_panel_override(beats, int(override_count))

    beats = beats[:10]
    if len(beats) < 3:
        beats = expand_storyboard_beats(beats, 3)
    return beats, len(beats)


def choose_identity_strategy(brief: dict[str, Any]) -> str | None:
    raw = brief.get("identity_strategy")
    if raw in (None, ""):
        return "reuse_exact" if brief.get("existing_references", {}).get("identity_source") else None
    strategy = str(raw).strip().lower()
    if strategy not in {"reuse_exact", "extend_from_source"}:
        raise ValueError("identity_strategy 只支持 reuse_exact 或 extend_from_source")
    return strategy


def normalize_brief(raw: dict[str, Any], project_defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    归一化 brief，支持从项目配置继承默认值

    Args:
        raw: 原始 brief 数据
        project_defaults: 项目级默认配置（可选）

    Returns:
        归一化后的 brief
    """
    # 三层继承：skill 默认 → project 默认 → run 级覆盖
    brief = deepcopy(DEFAULTS)
    if project_defaults:
        brief.update(project_defaults)
    brief.update(raw)

    required = ["subject", "action", "scene", "style"]
    missing = [key for key in required if not str(brief.get(key, "")).strip()]
    if missing:
        raise ValueError(f"缺少必填字段: {', '.join(missing)}")

    brief["duration"] = int(brief["duration"])
    brief["quality_tier"] = str(brief["quality_tier"]).strip().lower() or "draft"
    if brief["quality_tier"] not in {"draft", "final"}:
        raise ValueError("quality_tier 只支持 draft 或 final")

    if brief["ratio"] not in {"1:1", "3:4", "16:9", "4:3", "9:16", "21:9"}:
        brief["ratio"] = DEFAULTS["ratio"]

    brief["anchor_elements"] = parse_list_value(brief.get("anchor_elements"))
    brief["identity_anchor_rules"] = parse_list_value(brief.get("identity_anchor_rules"))
    brief["identity_structure"] = parse_list_value(brief.get("identity_structure"))
    brief["identity_forbidden"] = parse_list_value(brief.get("identity_forbidden"))

    # 向后兼容：自动迁移 identity_anchor_rules 到新字段
    if brief["identity_anchor_rules"] and not (brief["identity_structure"] or brief["identity_forbidden"]):
        for rule in brief["identity_anchor_rules"]:
            if any(keyword in rule for keyword in ("禁止", "不要", "不能", "不可", "避免")):
                brief["identity_forbidden"].append(rule)
            else:
                brief["identity_structure"].append(rule)

    brief["storyboard_beats_override"] = parse_list_value(brief.get("storyboard_beats_override"))
    brief["storyboard_strategy"] = str(brief.get("storyboard_strategy") or "auto_beats").strip().lower() or "auto_beats"
    if brief["storyboard_strategy"] not in {"auto_beats"}:
        raise ValueError("storyboard_strategy 第一版只支持 auto_beats")
    panel_override = brief.get("storyboard_panel_count_override")
    if panel_override not in (None, ""):
        brief["storyboard_panel_count_override"] = int(panel_override)
    else:
        brief["storyboard_panel_count_override"] = None

    existing = {}
    for key, value in (brief.get("existing_references") or {}).items():
        norm_key = normalize_existing_reference_key(key)
        if norm_key in REFERENCE_FILE_MAP and value:
            existing[norm_key] = str(Path(value).expanduser())
    brief["existing_references"] = existing
    brief["has_existing_references"] = bool(existing)
    brief["identity_strategy"] = choose_identity_strategy(brief)

    storyboard_beats, storyboard_panel_count = resolve_storyboard_plan(brief)
    brief["storyboard_beats"] = storyboard_beats
    brief["storyboard_panel_count"] = storyboard_panel_count

    project_name = str(brief.get("project_name") or "").strip() or str(brief["subject"]).strip()
    brief["project_name"] = project_name
    brief["project_slug"] = slugify(str(brief.get("project_slug") or project_name))

    slug_seed = str(brief.get("slug") or brief["subject"])
    brief["slug"] = slugify(slug_seed)

    # 归一化开关
    if "normalize_references" not in brief:
        brief["normalize_references"] = DEFAULTS["normalize_references"]

    return brief


def resolve_output_base(output_root: Path) -> Path:
    root = output_root.expanduser()
    if root.parts[-2:] == DEFAULT_OUTPUT_SUBDIR.parts:
        return root
    return root / DEFAULT_OUTPUT_SUBDIR


def build_project_dir(output_root: Path, brief: dict[str, Any]) -> Path:
    base = resolve_output_base(output_root)
    return base / PROJECTS_SUBDIR / brief["project_slug"]


def build_run_dir(output_root: Path, brief: dict[str, Any]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    project_dir = build_project_dir(output_root, brief)
    candidate = project_dir / RUNS_SUBDIR_NAME / f"{stamp}-{brief['slug']}"
    if not candidate.exists():
        return candidate

    suffix = 2
    while True:
        alternative = project_dir / RUNS_SUBDIR_NAME / f"{stamp}-{brief['slug']}-{suffix:02d}"
        if not alternative.exists():
            return alternative
        suffix += 1


def resolve_project_dir_for_run(run_dir: Path, brief: dict[str, Any]) -> Path:
    if run_dir.parent.name == RUNS_SUBDIR_NAME:
        return run_dir.parent.parent
    return build_project_dir(run_dir.parent, brief)


def materialize_existing_references(brief: dict[str, Any], run_dir: Path) -> dict[str, str]:
    resolved = {}
    normalized_dir = run_dir / "refs" / "normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    manifests = []

    for key, source in brief.get("existing_references", {}).items():
        src = Path(source).expanduser()
        if not src.exists():
            raise FileNotFoundError(f"现成参考图不存在: {src}")
        target = run_dir / "refs" / REFERENCE_FILE_MAP[key]

        # 如果启用归一化
        if brief.get("normalize_references", True):
            normalized_target = normalized_dir / REFERENCE_FILE_MAP[key]
            manifest = normalize_reference_image(src, normalized_target)
            manifests.append({"role": key, **manifest})
            # 复制归一化后的图片到 refs/ 目录
            shutil.copyfile(normalized_target, target)
        else:
            # 不归一化，直接复制
            shutil.copyfile(src, target)

        resolved[key] = str(target)

    # 保存归一化清单
    if manifests:
        manifest_file = normalized_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifests, ensure_ascii=False, indent=2), encoding="utf-8")

    if brief.get("identity_strategy") == "reuse_exact" and "identity_source" in resolved and "identity_board" not in resolved:
        source_path = Path(resolved["identity_source"])
        target = run_dir / "refs" / REFERENCE_FILE_MAP["identity_board"]
        shutil.copyfile(source_path, target)
        resolved["identity_board"] = str(target)
    return resolved


def canonical_target(project_dir: Path, key: str) -> Path:
    return project_dir / CANONICAL_SUBDIR_NAME / REFERENCE_FILE_MAP[key]


def sync_project_canonical_files(project_dir: Path, run_dir: Path, keys: list[str] | tuple[str, ...] | None = None) -> dict[str, str]:
    ensure_project_layout(project_dir)
    selected_keys = list(keys) if keys else list(REFERENCE_FILE_MAP.keys())
    synced: dict[str, str] = {}
    for key in selected_keys:
        if key not in REFERENCE_FILE_MAP:
            continue
        source = run_dir / "refs" / REFERENCE_FILE_MAP[key]
        if not source.exists():
            continue
        target = canonical_target(project_dir, key)
        shutil.copyfile(source, target)
        synced[key] = str(target)
    return synced


def build_prompts(brief: dict[str, Any]) -> dict[str, str]:
    anchor_text = "、".join(brief["anchor_elements"]) if brief["anchor_elements"] else "保留能稳定识别空间关系的地标"
    subject = brief["subject"]
    action = brief["action"]
    scene = brief["scene"]
    style = brief["style"]
    ratio = brief["ratio"]
    notes = str(brief.get("notes", "")).strip()
    notes_block = f"\n补充说明：{notes}" if notes else ""
    panel_count = brief["storyboard_panel_count"]
    storyboard_beats = brief["storyboard_beats"]
    storyboard_beats_block = "\n".join(f"{idx}. {beat}" for idx, beat in enumerate(storyboard_beats, start=1))

    # 使用新的 IP 约束字段
    identity_structure = brief.get("identity_structure") or []
    identity_forbidden = brief.get("identity_forbidden") or []

    # 向后兼容：如果新字段为空但旧字段有值，使用旧字段
    if not identity_structure and not identity_forbidden:
        identity_anchor_rules = brief.get("identity_anchor_rules") or []
        identity_structure_text = "；".join(identity_anchor_rules) if identity_anchor_rules else "保持主体的核心识别点稳定不漂"
        identity_forbidden_text = ""
    else:
        identity_structure_text = "；".join(identity_structure) if identity_structure else "保持主体的核心识别点稳定不漂"
        identity_forbidden_text = "；".join(identity_forbidden) if identity_forbidden else ""

    has_identity_source = bool(brief.get("existing_references", {}).get("identity_source"))
    identity_strategy = brief.get("identity_strategy")
    identity_source_block = ""
    if has_identity_source:
        identity_source_block = "\n7. 用户提供的 identity-source 是角色结构最高依据，任何延展版身份板都不能推翻它。"
    identity_board_goal = f"生成一张适合 {ratio} 项目的角色身份板 / 角色设定板。"
    identity_board_mode_block = ""
    if identity_strategy == "extend_from_source":
        identity_board_mode_block = (
            "\n这次模式：基于准确三视图 / 定稿图延展一张更正式的身份展示板。"
            "\n重点：这是延展展示板，不允许改动角色结构真相。"
        )
    elif identity_strategy == "reuse_exact":
        identity_board_mode_block = "\n这次模式：已有准确三视图 / 定稿图，身份板主要作为复用说明，不允许改动角色结构真相。"

    original = f"""原图任务：只负责风格与世界，不负责镜头顺序。
主体：{subject}
主体行为：{action}
场景 / 世界观：{scene}
风格 / 气质：{style}
空间锚点：{anchor_text}
要求：
1. 先建立完整世界观和主画面气质。
2. 让主体与环境关系清晰，能作为后续身份板和故事板的世界基准。
3. 保持电影感、真实感、可继续扩展成视频的空间信息。
4. 不要做分镜拼贴，不要出现分镜网格，不要用设定板版式。{notes_block}
""".strip()

    identity_board_forbidden_block = ""
    if identity_forbidden_text:
        identity_board_forbidden_block = f"\n7. 禁止变形：{identity_forbidden_text}。"

    identity_board = f"""身份板任务：只负责角色一致性，不负责背景叙事。
主体：{subject}
主体行为线索：{action}
目标：{identity_board_goal}{identity_board_mode_block}
要求：
1. 严格锁定主体的脸、发型、服装、身体比例、手部、表情和姿态语言。
2. 使用纯净浅底，不要复杂背景，不要重新讲故事。
3. 版式偏高端工作室设定板：大主视角 + 多个辅助角度 + 局部细节。
4. 只负责角色一致性，不出现 12 格分镜，不重新定义世界观。
5. 如果主体是动物或非人角色，也要把毛发、肢体比例、表情范围和关键特征锁住。
6. 结构真相：{identity_structure_text}。{identity_board_forbidden_block}{identity_source_block}{notes_block}
""".strip()

    storyboard_forbidden_block = ""
    if identity_forbidden_text:
        storyboard_forbidden_block = f"\n10. 禁止变形：{identity_forbidden_text}。"

    storyboard = f"""故事板任务：只负责镜头与动作节奏，不负责重新定义角色。
主体：{subject}
主体行为主线：{action}
场景 / 世界观：{scene}
空间锚点：{anchor_text}
要求：
1. 根据本次关键帧规划，做成 {panel_count} 格黑白导演分镜稿。
2. **每一格都必须是独立的 {ratio} 成片画幅**。不要做横向长条单格，不要把多格画成电影条带。整张看板怎么排版都可以，但每格内部画幅必须服从 {ratio} 成片比例。
3. 强调连续空间，同一世界内完成镜头推进，不要每格重造世界。
4. 主体身份必须保持和身份板一致，不要变脸、变衣服、变体型。
5. 每格都给明确镜头语言：景别、视角、运镜、动作节拍。
6. 让故事从建立空间，到动作推进，到结尾收束，形成清晰视频节奏。
7. 默认保留关键锚点：{anchor_text}。
8. 故事板里的角色首先要读成身份板里的核心轮廓，不能被画成一个新的普通角色。
9. 如果存在 identity-source，角色首先服从 identity-source，不服从任何漂移版身份板。{storyboard_forbidden_block}
11. 结构真相：{identity_structure_text}。
12. 如果动作设计和角色结构发生冲突，优先保住角色结构，宁可简化动作，不要改形。
13. 分镜允许用简化线稿表达动作，但外轮廓、体块关系和关键识别点必须忠于身份板。
14. 格数服务于关键帧，不追求平均切段。关键帧规划如下：
{storyboard_beats_block}{notes_block}
""".strip()

    video_forbidden_block = ""
    if identity_forbidden_text:
        video_forbidden_block = f"\n10. 禁止变形：{identity_forbidden_text}。"

    video = f"""视频提示词任务：必须引用前三张图的职责，不能重新发明一个冲突的新世界。
使用三张参考图：
- 原图：负责风格与世界
- 身份板：负责角色一致性
- 故事板：负责镜头与动作节奏

视频目标：
主体：{subject}
主体行为：{action}
场景 / 世界观：{scene}
风格 / 气质：{style}
比例：{brief['ratio']}
时长：{brief['duration']} 秒

要求：
1. 严格沿用故事板的镜头顺序和动作推进。
2. 严格沿用身份板的主体身份，不要漂角色。
3. 如果存在 identity-source，角色身份以原始三视图 / 定稿图为最高依据。
4. 严格沿用原图的世界与色调，不要把背景改成另一套体系。
5. 用自然流畅的镜头连接，按本次 {panel_count} 格关键帧顺序压成连贯短视频。
6. 保留明确的空间锚点：{anchor_text}。
7. 不要重新发明新的世界观、角色设定或冲突风格。
8. 本次关键帧规划如下：
{storyboard_beats_block}
9. 结构真相：{identity_structure_text}。{video_forbidden_block}{notes_block}
""".strip()

    return {
        "original": original,
        "identity_board": identity_board,
        "storyboard": storyboard,
        "video": video,
    }


def write_prompts(run_dir: Path, prompts: dict[str, str]) -> None:
    mapping = {
        "original": "original.txt",
        "identity_board": "identity-board.txt",
        "storyboard": "storyboard.txt",
        "video": "video.txt",
    }
    for key, filename in mapping.items():
        (run_dir / "prompts" / filename).write_text(prompts[key], encoding="utf-8")


def write_brief(run_dir: Path, brief: dict[str, Any]) -> None:
    (run_dir / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")


def project_file(project_dir: Path) -> Path:
    return project_dir / PROJECT_FILE_NAME


def project_summary_file(project_dir: Path) -> Path:
    return project_dir / PROJECT_SUMMARY_NAME


def load_project_state(project_dir: Path) -> dict[str, Any] | None:
    path = project_file(project_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def collect_prompt_files(run_dir: Path) -> dict[str, str]:
    return {
        "original": str(run_dir / "prompts" / "original.txt"),
        "identity_board": str(run_dir / "prompts" / "identity-board.txt"),
        "storyboard": str(run_dir / "prompts" / "storyboard.txt"),
        "video": str(run_dir / "prompts" / "video.txt"),
    }


def collect_reference_files(run_dir: Path) -> dict[str, str]:
    files = {}
    for key, filename in REFERENCE_FILE_MAP.items():
        path = run_dir / "refs" / filename
        if path.exists():
            files[key] = str(path)
    normalized_manifest = run_dir / "refs" / "normalized" / "manifest.json"
    if normalized_manifest.exists():
        files["normalized_manifest"] = str(normalized_manifest)
    return files


def build_run_record(
    run_dir: Path,
    stage: str,
    status: str,
    prompt_files: dict[str, str] | None = None,
    reference_files: dict[str, str] | None = None,
    submit_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "run_id": run_dir.name,
        "stage": stage,
        "status": status,
        "run_dir": str(run_dir),
        "brief_file": str(run_dir / "brief.json"),
        "summary_file": str(run_dir / "summary.md"),
    }
    if prompt_files:
        payload["prompt_files"] = prompt_files
    if reference_files:
        payload["reference_files"] = reference_files
    if submit_id:
        payload["submit_id"] = submit_id
    if extra:
        payload.update(extra)
    return payload


def write_project_summary(project_dir: Path, project_state: dict[str, Any]) -> None:
    """写入项目摘要文件"""
    state = project_state.get("state", {})
    defaults = project_state.get("defaults", {})
    constraints = project_state.get("constraints", {})

    lines = [
        "# 项目摘要",
        "",
        f"- 项目名：{project_state.get('project_name', '')}",
        f"- 项目标识：{project_state.get('project_id', '')}",
        f"- 当前阶段：{state.get('current_phase', '')}",
        f"- 当前状态：{state.get('status', '')}",
        f"- 最新运行：{state.get('latest_run_dir', '')}",
        "",
        "## 默认配置",
        f"- 比例：{defaults.get('ratio', '16:9')}",
        f"- 时长：{defaults.get('duration', 5)} 秒",
        f"- 质量档：{defaults.get('quality_tier', 'draft')}",
        f"- 故事板策略：{defaults.get('storyboard_strategy', 'auto_beats')}",
        f"- 参考图归一化：{'开启' if defaults.get('normalize_references', True) else '关闭'}",
        "",
    ]

    # 约束规则
    must_have = constraints.get("must_have", [])
    must_not_have = constraints.get("must_not_have", [])

    if must_have:
        lines.append("## 结构真相（必须成立）")
        for constraint in must_have:
            lines.append(f"- {constraint.get('description', '')}")
        lines.append("")

    if must_not_have:
        lines.append("## 禁止变形（不能出现）")
        for constraint in must_not_have:
            lines.append(f"- {constraint.get('description', '')}")
        lines.append("")

    canonical_files = project_state.get("canonical_files") or {}
    if canonical_files:
        lines.append("## 关键文件")
        for key, value in canonical_files.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    runs = project_state.get("runs") or []
    if runs:
        lines.append("## 最近运行")
        for run in runs[-5:]:
            lines.append(f"- {run['run_id']} | {run['stage']} | {run['status']}")
        lines.append("")

    project_summary_file(project_dir).write_text("\n".join(lines), encoding="utf-8")


def update_project_state(
    project_dir: Path,
    brief: dict[str, Any],
    run_dir: Path,
    stage: str,
    status: str,
    prompt_files: dict[str, str] | None = None,
    reference_files: dict[str, str] | None = None,
    canonical_files: dict[str, str] | None = None,
    submit_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    更新项目状态（使用新的 StateManager）

    保持向后兼容：返回的字典格式与旧版本一致
    """
    ensure_project_layout(project_dir)
    state_manager = StateManager(project_dir)
    now = now_iso()

    # 加载或创建项目配置
    project_config = state_manager.load_project()
    if project_config is None:
        # 创建新项目
        defaults = {
            "ratio": brief.get("ratio", "16:9"),
            "duration": brief.get("duration", 5),
            "quality_tier": brief.get("quality_tier", "draft"),
            "storyboard_strategy": brief.get("storyboard_strategy", "auto_beats"),
            "normalize_references": brief.get("normalize_references", True),
        }
        project_config = state_manager.create_project(
            project_id=brief["project_slug"],
            project_name=brief["project_name"],
            project_slug=brief["project_slug"],
            defaults=defaults,
        )

    # 更新项目核心信息
    project_config.project_name = brief["project_name"]
    project_config.project_slug = brief["project_slug"]
    project_config.project_dir = str(project_dir)

    # 只在 defaults 缺失时补齐，避免把单次 run 覆盖值污染成项目长期默认
    project_config.defaults.setdefault("ratio", brief["ratio"])
    project_config.defaults.setdefault("duration", brief["duration"])
    project_config.defaults.setdefault("quality_tier", brief["quality_tier"])
    if brief.get("identity_strategy") is not None:
        project_config.defaults.setdefault("identity_strategy", brief.get("identity_strategy"))
    project_config.defaults.setdefault(
        "storyboard_strategy",
        brief.get("storyboard_strategy", "auto_beats"),
    )
    project_config.defaults.setdefault(
        "normalize_references",
        brief.get("normalize_references", True),
    )

    # 更新约束
    project_config.constraints = convert_constraints_to_structured(brief)

    # 更新状态
    project_config.state.update({
        "status": status,
        "current_phase": stage,
        "latest_run_id": run_dir.name,
        "latest_run_dir": str(run_dir),
        "updated_at": now,
    })

    # 更新 canonical_files
    if canonical_files:
        project_config.canonical_files.update(canonical_files)

    # 构建运行记录
    run_record = build_run_record(
        run_dir,
        stage=stage,
        status=status,
        prompt_files=prompt_files,
        reference_files=reference_files,
        submit_id=submit_id,
        extra=extra,
    )
    run_record["updated_at"] = now

    # 添加或更新运行记录
    existing = next((r for r in project_config.runs if r.get("run_id") == run_dir.name), None)
    if existing is None:
        run_record["created_at"] = now
        project_config.runs.append(run_record)
    else:
        created_at = existing.get("created_at", now)
        existing.update(run_record)
        existing["created_at"] = created_at

    # 保存项目配置
    state_manager.save_project(project_config)

    # 写 project-summary.md
    write_project_summary(project_dir, project_config.to_dict())

    # 返回兼容格式的字典
    return project_config.to_dict()


def reference_target(run_dir: Path, name: str) -> Path:
    return run_dir / "refs" / REFERENCE_FILE_MAP[name]


def preferred_identity_reference(run_dir: Path) -> Path:
    identity_source = reference_target(run_dir, "identity_source")
    if identity_source.exists():
        return identity_source
    return reference_target(run_dir, "identity_board")


def build_gpt_image_jobs(brief: dict[str, Any], run_dir: Path, prompts: dict[str, str]) -> list[dict[str, Any]]:
    jobs = []
    preferred_identity_ref = preferred_identity_reference(run_dir)
    typed_refs = {
        "identity_board": [("--ref-style", str(reference_target(run_dir, "original")))],
        "storyboard": [
            ("--ref-style", str(reference_target(run_dir, "original"))),
            ("--ref-mascot", str(preferred_identity_ref)),
        ],
    }
    if brief.get("identity_strategy") == "extend_from_source" and preferred_identity_ref.exists():
        typed_refs["identity_board"].append(("--ref-mascot", str(preferred_identity_ref)))
    target_size = RATIO_IMAGE_SIZES.get(brief["ratio"], RATIO_IMAGE_SIZES["16:9"])
    sizes = {
        "original": target_size,
        "identity_board": target_size,
        "storyboard": target_size,
    }

    for name in ("original", "identity_board", "storyboard"):
        if name == "identity_board" and brief.get("identity_strategy") == "reuse_exact":
            continue
        target = reference_target(run_dir, name)
        if target.exists():
            continue

        command = [
            "python3",
            str(GTP_IMAGE_SCRIPT),
            "--prompt",
            prompts[name],
            "--size",
            sizes[name],
            "--output",
            str(target),
        ]
        for flag, value in typed_refs.get(name, []):
            command.extend([flag, value])

        jobs.append(
            {
                "name": name,
                "prompt": prompts[name],
                "output": str(target),
                "command": command,
            }
        )
    return jobs


def model_settings(brief: dict[str, Any]) -> dict[str, str]:
    if brief["quality_tier"] == "final":
        return {"model_version": "seedance2.0_vip", "video_resolution": "1080p"}
    return {"model_version": "seedance2.0fast", "video_resolution": "720p"}


def build_dreamina_command(run_dir: Path, brief: dict[str, Any], prompts: dict[str, str]) -> list[str]:
    settings = model_settings(brief)
    cmd = [
        DREAMINA_BIN,
        "multimodal2video",
    ]
    image_refs = [
        reference_target(run_dir, "original"),
        preferred_identity_reference(run_dir),
        reference_target(run_dir, "storyboard"),
    ]
    for path in image_refs:
        cmd.extend(["--image", str(path)])
    cmd.extend(
        [
            f"--prompt={prompts['video']}",
            f"--duration={brief['duration']}",
            f"--ratio={brief['ratio']}",
            f"--model_version={settings['model_version']}",
            f"--video_resolution={settings['video_resolution']}",
            "--poll=15",
        ]
    )
    return cmd


def summarize_reusable_fields(brief: dict[str, Any]) -> str:
    identity_strategy = brief.get("identity_strategy") or "auto"
    return "\n".join(
        [
            "## 下次复用重点",
            f"- 主体：{brief['subject']}",
            f"- 动作：{brief['action']}",
            f"- 场景：{brief['scene']}",
            f"- 风格：{brief['style']}",
            f"- 比例：{brief['ratio']}",
            f"- 时长：{brief['duration']} 秒",
            f"- 关键帧数：{brief['storyboard_panel_count']}",
            f"- 质量档：{brief['quality_tier']}",
            f"- 身份策略：{identity_strategy}",
        ]
    )


def write_summary(run_dir: Path, brief: dict[str, Any], prompts: dict[str, str], submit_id: str | None = None) -> None:
    identity_source = reference_target(run_dir, "identity_source")
    identity_reference = "refs/identity-source.png" if identity_source.exists() else "refs/identity-board.png"

    lines = [
        "# 本次运行摘要",
        "",
        summarize_reusable_fields(brief),
        "",
        "## 本次关键帧规划",
        *[f"- {beat}" for beat in brief["storyboard_beats"]],
        "",
    ]

    # 归一化结果
    normalized_manifest_file = run_dir / "refs" / "normalized" / "manifest.json"
    if normalized_manifest_file.exists():
        try:
            manifests = json.loads(normalized_manifest_file.read_text(encoding="utf-8"))
            lines.extend([
                "## 参考图归一化结果",
                "",
            ])
            for manifest in manifests:
                role = manifest.get("role", "unknown")
                role_name = {"original": "原图", "identity_source": "角色来源", "identity_board": "身份板", "storyboard": "故事板"}.get(role, role)
                src_w = manifest.get("source_width", 0)
                src_h = manifest.get("source_height", 0)
                src_kb = manifest.get("source_bytes", 0) // 1024
                norm_w = manifest.get("normalized_width", 0)
                norm_h = manifest.get("normalized_height", 0)
                norm_kb = manifest.get("normalized_bytes", 0) // 1024
                changed = manifest.get("changed", False)
                status = "已压缩" if changed else "未改动"
                lines.append(f"- **{role_name}**: {src_w}x{src_h} ({src_kb}KB) → {norm_w}x{norm_h} ({norm_kb}KB) [{status}]")
            lines.append("")
        except (json.JSONDecodeError, KeyError):
            pass

    lines.extend([
        "## 角色结构依据",
        f"- 最高依据：{identity_reference}",
        f"- 当前身份策略：{brief.get('identity_strategy') or 'auto'}",
        "",
    ])

    # IP 约束信息
    identity_structure = brief.get("identity_structure") or []
    identity_forbidden = brief.get("identity_forbidden") or []
    if identity_structure or identity_forbidden:
        lines.extend([
            "## IP 约束规则",
            "",
        ])
        if identity_structure:
            lines.append("**结构真相**（必须成立的）：")
            for item in identity_structure:
                lines.append(f"- {item}")
            lines.append("")
        if identity_forbidden:
            lines.append("**禁止变形**（不能出现的）：")
            for item in identity_forbidden:
                lines.append(f"- {item}")
            lines.append("")

    lines.extend([
        "## 人工检查清单",
        "",
        f"请在生成参考图和视频后，检查以下项目：",
        "",
        f"- [ ] 故事板每一格是否都是 **{brief['ratio']}** 画幅？（不是横向长条，不是电影条带）",
        f"- [ ] 角色身份是否和 {identity_reference} 一致？（脸、服装、比例、姿态）",
    ])

    if identity_structure:
        lines.append("- [ ] 以下结构真相是否都保持了？")
        for item in identity_structure:
            lines.append(f"  - [ ] {item}")

    if identity_forbidden:
        lines.append("- [ ] 是否出现了以下禁止变形？（应该全部没有出现）")
        for item in identity_forbidden:
            lines.append(f"  - [ ] {item}")

    lines.extend([
        "",
        "## 关键提示词文件",
        "- prompts/original.txt",
        "- prompts/identity-board.txt",
        "- prompts/storyboard.txt",
        "- prompts/video.txt",
    ])

    if submit_id:
        lines.extend(["", f"## 即梦任务", f"- submit_id: {submit_id}"])

    (run_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def parse_credit_output(stdout: str) -> dict[str, Any]:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"raw": stdout.strip()}


def check_readable_gpt_image_config() -> bool:
    env_file = resolve_gpt_image_config()
    return env_file.exists() or bool(os.getenv("BANANA_API_KEY"))


def run_preflight() -> PreflightResult:
    checks = []

    dreamina_ok = Path(DREAMINA_BIN).exists() if DREAMINA_BIN.startswith("/") else bool(shutil.which(DREAMINA_BIN))
    checks.append({"name": "dreamina_bin", "ok": dreamina_ok, "detail": DREAMINA_BIN})

    credit_ok = False
    credit_detail: dict[str, Any] | str = "未执行"
    if dreamina_ok:
        result = run_command([DREAMINA_BIN, "user_credit"])
        credit_detail = parse_credit_output(result.stdout or result.stderr or f"exit={result.returncode}")
        credit_ok = result.returncode == 0
    checks.append({"name": "dreamina_credit", "ok": credit_ok, "detail": credit_detail})

    gpt_script_ok = GTP_IMAGE_SCRIPT.exists()
    checks.append({"name": "gpt_image_script", "ok": gpt_script_ok, "detail": str(GTP_IMAGE_SCRIPT)})

    gpt_config_ok = check_readable_gpt_image_config()
    checks.append(
        {
            "name": "gpt_image_config",
            "ok": gpt_config_ok,
            "detail": f"{resolve_gpt_image_config()} 或 BANANA_API_KEY",
        }
    )

    ok = all(item["ok"] for item in checks)
    return PreflightResult(ok=ok, checks=checks)


def save_submit_id(run_dir: Path, stdout: str) -> str | None:
    match = re.search(r'"submit_id"\s*:\s*"([^"]+)"', stdout)
    if not match:
        match = re.search(r"submit_id[:=]\s*([A-Za-z0-9-]+)", stdout)
    if not match:
        return None
    submit_id = match.group(1)
    (run_dir / "dreamina" / "submit_id.txt").write_text(submit_id, encoding="utf-8")
    return submit_id


def save_result_json(run_dir: Path, stdout: str) -> None:
    path = run_dir / "dreamina" / "result.json"
    try:
        payload = json.loads(stdout)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except json.JSONDecodeError:
        path.write_text(stdout, encoding="utf-8")
