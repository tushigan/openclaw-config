#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    PRODUCT_ROLE_ORDER,
    STYLE_ROLE_ORDER,
    append_audit,
    asset_entries_by_role,
    load_task_state,
    read_json,
    resolve_project_dir,
    resolve_task_dir,
    size_for_ratio,
    task_asset_entries_by_role,
    update_state,
    update_task_manifest_entry,
    update_task_state,
    utc_now,
    write_json,
)

DEFAULT_GPT_IMAGE2_SCRIPT = Path("/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py")


def dedupe_entries(entries: list[dict], limit: int) -> list[dict]:
    seen: set[str] = set()
    kept: list[dict] = []
    for entry in entries:
        key = entry.get("absolute_path", "")
        if not key or key in seen:
            continue
        seen.add(key)
        kept.append(entry)
        if len(kept) >= limit:
            break
    return kept


def latest_unique_entries(entries: list[dict], limit: int) -> list[dict]:
    seen: set[str] = set()
    kept: list[dict] = []
    for entry in reversed(entries):
        key = entry.get("absolute_path", "")
        if not key or key in seen:
            continue
        seen.add(key)
        kept.append(entry)
        if len(kept) >= limit:
            break
    kept.reverse()
    return kept


def build_command(
    *,
    gpt_script: Path,
    prompt_path: Path,
    output_path: Path,
    size: str,
    model: str,
    count: int,
    base_refs: list[dict],
    product_refs: list[dict],
    layout_refs: list[dict],
    style_refs: list[dict],
    background_refs: list[dict],
    generic_refs: list[dict],
) -> list[str]:
    cmd = [
        "python3",
        str(gpt_script),
        "--prompt-file",
        str(prompt_path),
        "--size",
        size,
        "--output",
        str(output_path),
        "--model",
        model,
        "--count",
        str(count),
    ]
    for entry in base_refs:
        cmd.extend(["--ref-base", entry["absolute_path"]])
    for entry in product_refs:
        cmd.extend(["--ref-product", entry["absolute_path"]])
    for entry in layout_refs:
        cmd.extend(["--ref-layout", entry["absolute_path"]])
    for entry in style_refs:
        cmd.extend(["--ref-style", entry["absolute_path"]])
    for entry in background_refs:
        cmd.extend(["--ref-background", entry["absolute_path"]])
    for entry in generic_refs:
        cmd.extend(["--reference", entry["absolute_path"]])
    return cmd


def run_project_generation(args: argparse.Namespace, project_dir: Path) -> int:
    state = read_json(project_dir / "project_state.json", {})
    direction = read_json(project_dir / "creative_direction.json", {})
    assets_manifest = read_json(project_dir / "assets_manifest.json", {})
    generation_manifest_path = project_dir / "generation_manifest.json"
    generation_manifest = read_json(generation_manifest_path, {})

    if not args.force and not state.get("workflow_flags", {}).get("creative_confirmed", False):
        raise SystemExit("creative_direction 尚未确认，不能进入生图阶段。可先执行 record_confirmation.py。")

    prompt_path = project_dir / "prompts" / f"prompt_{args.prompt_version}.md"
    if not prompt_path.exists():
        raise SystemExit(f"Prompt 文件不存在: {prompt_path}")

    ratio = args.ratio or direction.get("output_ratio", "1:1")
    size = args.size or size_for_ratio(ratio)
    count = args.count or int(direction.get("draft_count", 1) or 1)

    product_refs = asset_entries_by_role(assets_manifest, PRODUCT_ROLE_ORDER)[: args.max_product_refs]
    style_refs = asset_entries_by_role(assets_manifest, ["reference_style"])[: args.max_style_refs]
    background_refs = asset_entries_by_role(assets_manifest, ["reference_background"])[:1]
    generic_refs: list[dict] = []

    round_no = len(generation_manifest.get("rounds", [])) + 1
    output_path = project_dir / "images" / "generated_drafts" / f"draft_round_{round_no:02d}.png"
    gpt_script = Path(args.gpt_image2_script)

    cmd = build_command(
        gpt_script=gpt_script,
        prompt_path=prompt_path,
        output_path=output_path,
        size=size,
        model=args.model,
        count=count,
        base_refs=[],
        product_refs=product_refs,
        layout_refs=[],
        style_refs=style_refs,
        background_refs=background_refs,
        generic_refs=generic_refs,
    )
    command_summary = " ".join(shlex.quote(part) for part in cmd)
    round_payload = {
        "round": round_no,
        "created_at": utc_now(),
        "prompt_file": str(prompt_path),
        "output": str(output_path),
        "size": size,
        "ratio": ratio,
        "count": count,
        "model": args.model,
        "product_refs": [item["absolute_path"] for item in product_refs],
        "style_refs": [item["absolute_path"] for item in style_refs],
        "background_refs": [item["absolute_path"] for item in background_refs],
        "command_summary": command_summary,
        "status": "dry_run" if args.dry_run else "queued",
    }

    logs_dir = project_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = logs_dir / f"generate.round-{round_no:02d}.stdout.log"
    stderr_log = logs_dir / f"generate.round-{round_no:02d}.stderr.log"
    round_payload["stdout_log"] = str(stdout_log)
    round_payload["stderr_log"] = str(stderr_log)

    if args.dry_run:
        generation_manifest.setdefault("rounds", []).append(round_payload)
        generation_manifest["latest_status"] = "dry_run"
        generation_manifest["latest_output"] = str(output_path)
        generation_manifest["updated_at"] = utc_now()
        write_json(generation_manifest_path, generation_manifest)
        update_state(
            project_dir,
            current_stage="generation_queued",
            stage_status="ready",
            attempts_update={"generation_round": round_no},
        )
        append_audit(project_dir, "generation_dry_run_prepared", round_payload)
        print(f"command_summary={command_summary}")
        return 0

    update_state(
        project_dir,
        current_stage="generation_running",
        stage_status="running",
        attempts_update={"generation_round": round_no},
    )
    with stdout_log.open("w", encoding="utf-8") as stdout_fh, stderr_log.open("w", encoding="utf-8") as stderr_fh:
        result = subprocess.run(cmd, text=True, stdout=stdout_fh, stderr=stderr_fh)

    round_payload["exit_code"] = result.returncode
    result_path = output_path.with_name(f"{output_path.stem}.result.json")
    round_payload["result_path"] = str(result_path)
    round_payload["status"] = "succeeded" if result.returncode == 0 else "failed"
    if result_path.exists():
        round_payload["result_summary"] = read_json(result_path, {})

    generation_manifest.setdefault("rounds", []).append(round_payload)
    generation_manifest["latest_status"] = round_payload["status"]
    generation_manifest["latest_output"] = str(output_path)
    generation_manifest["updated_at"] = utc_now()
    write_json(generation_manifest_path, generation_manifest)

    if result.returncode == 0:
        update_state(
            project_dir,
            current_stage="generation_review_waiting_confirm",
            stage_status="waiting_user",
        )
    else:
        update_state(
            project_dir,
            current_stage="generation_running",
            stage_status="error",
            last_error_stage="generation_running",
            last_error=f"gpt-image2-gen failed with exit code {result.returncode}",
        )

    append_audit(project_dir, "generation_executed", round_payload)
    return result.returncode


def run_task_generation(args: argparse.Namespace, project_dir: Path) -> int:
    task_dir = resolve_task_dir(project_dir, args.task_id)
    task_state = load_task_state(task_dir)
    if not args.force and not task_state.get("workflow_flags", {}).get("generation_allowed", False):
        raise SystemExit("task brief 尚未确认，不能进入任务级生图。可先执行 record_confirmation.py --kind task_brief。")

    assets_manifest = read_json(project_dir / "assets_manifest.json", {})
    task_assets = read_json(task_dir / "task_assets.json", {})
    task_brief = read_json(task_dir / "task_brief.json", {})
    generation_manifest_path = task_dir / "generation_manifest.json"
    generation_manifest = read_json(generation_manifest_path, {})

    version_id = (
        args.prompt_version
        if args.prompt_version and args.prompt_version != "v1"
        else task_state.get("selected_version_id") or task_state.get("latest_version_id") or generation_manifest.get("latest_version_id") or "V001"
    )
    prompt_path = task_dir / "prompts" / f"prompt_{version_id}.md"
    if not prompt_path.exists():
        raise SystemExit(f"任务 Prompt 文件不存在: {prompt_path}")

    ratio = args.ratio or task_brief.get("output_ratio") or task_state.get("output_ratio", "") or "1:1"
    size = args.size or size_for_ratio(ratio)
    count = args.count or 1
    execution_mode = task_brief.get("execution_mode") or "whole_image"
    base_refs: list[dict] = []
    if execution_mode == "local_edit":
        base_info = task_brief.get("base_image") or {}
        base_path_text = base_info.get("absolute_path", "")
        if not base_path_text:
            raise SystemExit("local_edit 模式缺少 base_image.absolute_path。")
        base_path = Path(base_path_text)
        if not base_path.exists():
            raise SystemExit(f"local_edit 母版图不存在: {base_path}")
        base_refs = [{"absolute_path": str(base_path)}]

    base_product_refs = asset_entries_by_role(assets_manifest, PRODUCT_ROLE_ORDER)
    task_product_refs = task_asset_entries_by_role(task_assets, ["product_state_reference"])
    product_refs = dedupe_entries(base_product_refs + task_product_refs, args.max_product_refs)

    task_layout_refs = task_asset_entries_by_role(task_assets, ["composition_reference"])
    project_layout_refs = asset_entries_by_role(assets_manifest, ["reference_layout"])
    layout_source_refs = task_layout_refs if task_layout_refs else project_layout_refs
    layout_refs = latest_unique_entries(layout_source_refs, 1)

    style_refs = dedupe_entries(
        asset_entries_by_role(assets_manifest, ["reference_style", "reference_lighting"])
        + task_asset_entries_by_role(task_assets, ["style_reference", "lighting_reference"]),
        args.max_style_refs,
    )
    background_refs = dedupe_entries(
        asset_entries_by_role(assets_manifest, ["reference_background"]) + task_asset_entries_by_role(task_assets, ["scene_reference"]),
        max(1, args.max_style_refs),
    )
    generic_refs = dedupe_entries(
        task_asset_entries_by_role(task_assets, ["page_draft", "other_reference"]),
        12,
    )

    output_path = task_dir / "versions" / version_id / "generated.png"
    gpt_script = Path(args.gpt_image2_script)
    cmd = build_command(
        gpt_script=gpt_script,
        prompt_path=prompt_path,
        output_path=output_path,
        size=size,
        model=args.model,
        count=count,
        base_refs=base_refs,
        product_refs=product_refs,
        layout_refs=layout_refs,
        style_refs=style_refs,
        background_refs=background_refs,
        generic_refs=generic_refs,
    )
    command_summary = " ".join(shlex.quote(part) for part in cmd)

    task_round_payload = {
        "version_id": version_id,
        "created_at": utc_now(),
        "prompt_file": str(prompt_path),
        "output": str(output_path),
        "size": size,
        "ratio": ratio,
        "count": count,
        "model": args.model,
        "execution_mode": execution_mode,
        "base_refs": [item["absolute_path"] for item in base_refs],
        "product_refs": [item["absolute_path"] for item in product_refs],
        "layout_refs": [item["absolute_path"] for item in layout_refs],
        "style_refs": [item["absolute_path"] for item in style_refs],
        "background_refs": [item["absolute_path"] for item in background_refs],
        "generic_refs": [item["absolute_path"] for item in generic_refs],
        "command_summary": command_summary,
        "status": "dry_run" if args.dry_run else "queued",
    }

    logs_dir = task_dir / "reports"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = logs_dir / f"generate.{version_id}.stdout.log"
    stderr_log = logs_dir / f"generate.{version_id}.stderr.log"
    task_round_payload["stdout_log"] = str(stdout_log)
    task_round_payload["stderr_log"] = str(stderr_log)

    def sync_generation_manifest(status: str, exit_code: int | None = None) -> None:
        generation_manifest["latest_status"] = status
        generation_manifest["latest_output"] = str(output_path)
        generation_manifest["latest_version_id"] = version_id
        generation_manifest["updated_at"] = utc_now()
        versions = generation_manifest.setdefault("versions", [])
        matched = False
        for item in versions:
            if item.get("version_id") != version_id:
                continue
            item.update(task_round_payload)
            item["status"] = status
            if exit_code is not None:
                item["exit_code"] = exit_code
            matched = True
        if not matched:
            entry = dict(task_round_payload)
            entry["status"] = status
            if exit_code is not None:
                entry["exit_code"] = exit_code
            versions.append(entry)
        write_json(generation_manifest_path, generation_manifest)

    if args.dry_run:
        sync_generation_manifest("dry_run")
        update_task_state(
            task_dir,
            current_stage="task_generation_queued",
            stage_status="ready",
        )
        update_task_manifest_entry(
            project_dir,
            task_state["task_id"],
            {
                "status": "generation_dry_run",
                "latest_version_id": version_id,
                "selected_version_id": version_id,
            },
        )
        update_state(
            project_dir,
            current_stage="task_generation_queued",
            stage_status="ready",
            active_task_id=task_state["task_id"],
        )
        append_audit(
            project_dir,
            "task_generation_dry_run_prepared",
            {
                "task_id": task_state["task_id"],
                **task_round_payload,
            },
        )
        print(f"task_id={task_state['task_id']}")
        print(f"version_id={version_id}")
        print(f"command_summary={command_summary}")
        return 0

    update_task_state(
        task_dir,
        current_stage="task_generation_running",
        stage_status="running",
        field_updates={
            "selected_version_id": version_id,
            "latest_version_id": version_id,
        },
    )
    update_state(
        project_dir,
        current_stage="task_generation_running",
        stage_status="running",
        active_task_id=task_state["task_id"],
    )

    with stdout_log.open("w", encoding="utf-8") as stdout_fh, stderr_log.open("w", encoding="utf-8") as stderr_fh:
        result = subprocess.run(cmd, text=True, stdout=stdout_fh, stderr=stderr_fh)

    result_path = output_path.with_name(f"{output_path.stem}.result.json")
    task_round_payload["result_path"] = str(result_path)
    if result_path.exists():
        task_round_payload["result_summary"] = read_json(result_path, {})

    status = "succeeded" if result.returncode == 0 else "failed"
    sync_generation_manifest(status, result.returncode)

    latest_output = str(output_path)
    update_task_state(
        task_dir,
        current_stage="task_generation_review_waiting_confirm" if result.returncode == 0 else "task_generation_failed",
        stage_status="waiting_user" if result.returncode == 0 else "error",
        workflow_flag_updates={
            "result_approved": False,
        },
        field_updates={
            "selected_version_id": version_id,
            "latest_version_id": version_id,
            "latest_output": latest_output,
        },
    )
    update_task_manifest_entry(
        project_dir,
        task_state["task_id"],
        {
            "status": "generated" if result.returncode == 0 else "generation_failed",
            "selected_version_id": version_id,
            "latest_version_id": version_id,
            "latest_output": latest_output,
        },
    )
    update_state(
        project_dir,
        current_stage="task_generation_review_waiting_confirm" if result.returncode == 0 else "task_generation_failed",
        stage_status="waiting_user" if result.returncode == 0 else "error",
        active_task_id=task_state["task_id"],
        workflow_flag_updates={
            "delivery_ready": False,
        },
        last_error_stage="" if result.returncode == 0 else "task_generation_running",
        last_error="" if result.returncode == 0 else f"gpt-image2-gen failed with exit code {result.returncode}",
    )
    append_audit(
        project_dir,
        "task_generation_executed",
        {
            "task_id": task_state["task_id"],
            **task_round_payload,
            "exit_code": result.returncode,
            "status": status,
        },
    )
    print(f"task_id={task_state['task_id']}")
    print(f"version_id={version_id}")
    print(f"output={output_path}")
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="调用 gpt-image2-gen 执行产品摄影生图")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-id", default="", help="任务 ID 或任务目录；传入时走 V2 任务模式")
    parser.add_argument("--gpt-image2-script", default=str(DEFAULT_GPT_IMAGE2_SCRIPT), help="统一生图脚本")
    parser.add_argument("--prompt-version", default="v1", help="V1 prompt 版本；V2 默认读取当前任务版本")
    parser.add_argument("--ratio", default="", help="覆盖比例")
    parser.add_argument("--size", default="", help="覆盖像素尺寸")
    parser.add_argument("--count", type=int, default=0, help="覆盖首轮张数")
    parser.add_argument("--model", default="gpt-image-2-pro", help="逻辑模型名；命中 AIXOR 时会由底层脚本自动映射为其可用模型")
    parser.add_argument("--max-product-refs", type=int, default=6, help="最多产品参考图数量")
    parser.add_argument("--max-style-refs", type=int, default=3, help="最多风格参考图数量")
    parser.add_argument("--dry-run", action="store_true", help="只生成命令和 manifest，不真正调用模型")
    parser.add_argument("--force", action="store_true", help="忽略确认阀门检查")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)
    exit_code = run_task_generation(args, project_dir) if args.task_id else run_project_generation(args, project_dir)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
