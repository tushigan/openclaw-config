#!/usr/bin/env python3
"""CLI entrypoint for the dreamina-reference-video skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.workflow import (
    DREAMINA_BIN,
    DEFAULT_OUTPUT_ROOT,
    REFERENCE_FILE_MAP,
    build_project_dir,
    build_dreamina_command,
    build_gpt_image_jobs,
    build_prompts,
    build_run_dir,
    collect_prompt_files,
    collect_reference_files,
    default_validation_stage,
    ensure_run_layout,
    ensure_project_layout,
    load_validation_report,
    materialize_existing_references,
    normalize_brief,
    prepare_validation_references,
    resolve_reference_path,
    resolve_project_dir_for_run,
    run_command,
    run_preflight,
    save_result_json,
    save_submit_id,
    summarize_reusable_fields,
    sync_project_canonical_files,
    update_project_state,
    write_validation_report,
    write_brief,
    write_prompts,
    write_summary,
)
from scripts.state_manager import RunState, StateManager, now_iso
from scripts.validator import validate_run
from scripts.iteration_engine import IterationEngine
from scripts.prompt_risk_analyzer import analyze_prompts


def load_brief(args: argparse.Namespace) -> dict:
    if args.brief_file:
        return json.loads(Path(args.brief_file).read_text(encoding="utf-8"))
    payload = {
        "project_name": args.project_name,
        "project_slug": args.project_slug,
        "video_mode": args.video_mode,
        "subject": args.subject,
        "action": args.action,
        "scene": args.scene,
        "style": args.style,
        "ratio": args.ratio,
        "duration": args.duration,
        "quality_tier": args.quality_tier,
        "notes": args.notes,
        "storyboard_strategy": args.storyboard_strategy,
        "storyboard_panel_count_override": args.storyboard_panel_count_override,
        "storyboard_beats_override": args.storyboard_beats_override,
        "identity_strategy": args.identity_strategy,
        "identity_anchor_rules": args.identity_anchor_rules,
    }
    return {k: v for k, v in payload.items() if v not in (None, "")}


def load_run_state_or_error(state_manager: StateManager, run_dir: Path):
    run_state = state_manager.load_run_state(run_dir)
    if run_state is None:
        raise ValueError(f"运行状态不存在: {run_dir}")
    return run_state


def prompt_text_for_stage(stage: str, prompts: dict[str, str]) -> str:
    if stage == "reference_system":
        ordered = ("original", "identity_board", "storyboard", "video")
        return "\n\n".join(prompts[name] for name in ordered if name in prompts)
    if stage == "storyboard":
        return prompts.get("storyboard", "")
    if stage == "video":
        return prompts.get("video", "")
    return ""


def parse_check_assignment(raw: str) -> tuple[str, bool]:
    if "=" not in raw:
        raise ValueError(f"检查项参数格式错误: {raw}")
    check_id, raw_value = raw.split("=", 1)
    value = raw_value.strip().lower()
    if value in {"true", "1", "yes", "y", "checked"}:
        return check_id.strip(), True
    if value in {"false", "0", "no", "n", "unchecked"}:
        return check_id.strip(), False
    raise ValueError(f"检查项布尔值无法识别: {raw}")


def load_manual_check_updates(args: argparse.Namespace) -> dict[str, bool]:
    updates: dict[str, bool] = {}

    # 如果指定了 --all-passed，标记所有检查项为通过
    if getattr(args, 'all_passed', False):
        # 这个标记会在 cmd_complete_manual_checks 中处理
        return {}

    if args.file:
        payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "manual_checks" in payload:
            payload = payload["manual_checks"]
        if isinstance(payload, dict):
            for check_id, checked in payload.items():
                updates[str(check_id)] = bool(checked)
        elif isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict) or "id" not in item:
                    raise ValueError("manual checks JSON 列表里的每一项都必须包含 id")
                updates[str(item["id"])] = bool(item.get("checked", False))
        else:
            raise ValueError("manual checks JSON 必须是对象、列表，或包含 manual_checks 的对象")

    for raw in args.check or []:
        check_id, checked = parse_check_assignment(raw)
        updates[check_id] = checked

    if not updates and not getattr(args, 'all_passed', False):
        raise ValueError("请通过 --file、--check 或 --all-passed 提供至少一个人工检查更新")
    return updates


def persist_validation_report(run_dir: Path, validation_report: dict[str, Any]) -> Path:
    report_files = write_validation_report(run_dir, validation_report)
    return report_files[0]


def infer_run_stage_and_status(
    run_dir: Path,
    project_config: Any | None,
) -> tuple[str, str]:
    if project_config is not None:
        for record in project_config.runs:
            if record.get("run_id") == run_dir.name:
                return record.get("stage", "prepare"), record.get("status", "pending")

    if (run_dir / "dreamina" / "result.json").exists() or (run_dir / "dreamina" / "submit_id.txt").exists():
        return "submit_video", "video_submitted"
    if collect_reference_files(run_dir):
        return "generate_refs", "references_generated"
    return "prepare", "ready_for_ref_generation"


def build_artifact_map(run_dir: Path) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    result_file = run_dir / "dreamina" / "result.json"
    submit_id_file = run_dir / "dreamina" / "submit_id.txt"
    downloads_dir = run_dir / "dreamina" / "downloads"
    if result_file.exists():
        artifacts["result_file"] = str(result_file)
    if submit_id_file.exists():
        artifacts["submit_id_file"] = str(submit_id_file)
    if downloads_dir.exists():
        artifacts["downloads_dir"] = str(downloads_dir)
    return artifacts


def refresh_project_canonical_manifest(
    state_manager: StateManager,
) -> list[dict[str, Any]]:
    recovery_actions: list[dict[str, Any]] = []
    project_config = state_manager.load_project()
    if project_config is None:
        return recovery_actions

    canonical_changed = False
    for key, filename in REFERENCE_FILE_MAP.items():
        canonical_path = Path(project_config.project_dir) / "canonical" / filename
        if canonical_path.exists() and project_config.canonical_files.get(key) != str(canonical_path):
            project_config.canonical_files[key] = str(canonical_path)
            canonical_changed = True

    if canonical_changed:
        state_manager.save_project(project_config)
        recovery_actions.append(
            {
                "action": "refresh_project_canonical_manifest",
                "target": str(Path(project_config.project_dir) / "project.json"),
            }
        )

    return recovery_actions


def load_or_recover_run_state(
    state_manager: StateManager,
    run_dir: Path,
    brief: dict[str, Any],
) -> tuple[RunState, list[dict[str, Any]]]:
    recovery_actions: list[dict[str, Any]] = []
    run_state = state_manager.load_run_state(run_dir)
    project_config = state_manager.load_project()
    recovery_actions.extend(refresh_project_canonical_manifest(state_manager))

    if run_state is None:
        stage, status = infer_run_stage_and_status(run_dir, project_config)
        run_state = RunState(
            run_id=run_dir.name,
            project_id=brief.get("project_slug", ""),
            stage=stage,
            status=status,
            created_at=now_iso(),
            updated_at=now_iso(),
            config_snapshot=brief,
            prompt_files=collect_prompt_files(run_dir),
            reference_files=collect_reference_files(run_dir),
            artifacts=build_artifact_map(run_dir),
        )
        validation_report, report_path = load_validation_report(run_dir)
        if validation_report:
            run_state.validation_report = validation_report
            recovery_actions.append(
                {
                    "action": "recover_validation_report",
                    "source": str(report_path),
                }
            )
        state_manager.save_run_state(run_dir, run_state)
        recovery_actions.append(
            {
                "action": "rebuild_run_state",
                "target": str(run_dir / "run_state.json"),
                "stage": stage,
                "status": status,
            }
        )
        return run_state, recovery_actions

    changed = False
    if not run_state.config_snapshot:
        run_state.config_snapshot = brief
        changed = True
    if not run_state.prompt_files:
        run_state.prompt_files = collect_prompt_files(run_dir)
        changed = True
    current_references = collect_reference_files(run_dir)
    if current_references and current_references != run_state.reference_files:
        run_state.reference_files.update(current_references)
        changed = True
    current_artifacts = build_artifact_map(run_dir)
    if current_artifacts:
        for key, value in current_artifacts.items():
            if run_state.artifacts.get(key) != value:
                run_state.artifacts[key] = value
                changed = True
    if not run_state.validation_report:
        validation_report, report_path = load_validation_report(run_dir)
        if validation_report:
            run_state.validation_report = validation_report
            changed = True
            recovery_actions.append(
                {
                    "action": "recover_validation_report",
                    "source": str(report_path),
                }
            )

    if changed:
        state_manager.save_run_state(run_dir, run_state)
        recovery_actions.append(
            {
                "action": "refresh_run_state",
                "target": str(run_dir / "run_state.json"),
            }
        )

    return run_state, recovery_actions


def build_validation_gate_status(run_state: RunState) -> dict[str, Any]:
    next_action = run_state.next_action or {}
    decision = next_action.get("decision")
    can_submit = bool(run_state.validation_report) and bool(next_action.get("reviewed_at")) and decision in {"proceed", "continue"}
    return {
        "has_validation_report": bool(run_state.validation_report),
        "has_review": bool(next_action.get("reviewed_at")),
        "review_decision": decision or "",
        "can_submit": bool(can_submit),
    }


def cmd_preflight(_: argparse.Namespace) -> int:
    result = run_preflight()
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def cmd_prepare(args: argparse.Namespace) -> int:
    # 加载项目配置（如果存在）
    brief_raw = load_brief(args)
    output_root = Path(args.output_root or DEFAULT_OUTPUT_ROOT)

    # 先做一次简单的归一化来获取 project_slug
    temp_brief = normalize_brief(brief_raw)
    project_dir = build_project_dir(output_root, temp_brief)

    # 加载项目默认配置
    state_manager = StateManager(project_dir)
    project_config = state_manager.load_project()
    project_defaults = project_config.defaults if project_config else None

    # 使用项目默认配置进行完整归一化
    brief = normalize_brief(brief_raw, project_defaults)

    run_dir = build_run_dir(output_root, brief)
    ensure_project_layout(project_dir)
    ensure_run_layout(run_dir)
    materialize_existing_references(brief, run_dir)
    prompts = build_prompts(brief)
    write_brief(run_dir, brief)
    write_prompts(run_dir, prompts)

    # 执行 prompt 风险分析
    risk_reports = analyze_prompts(prompts)
    risk_report_dict = {name: report.to_dict() for name, report in risk_reports.items()}

    # 保存风险分析报告
    risk_report_file = run_dir / "prompts" / "risk_report.json"
    risk_report_file.write_text(json.dumps(risk_report_dict, ensure_ascii=False, indent=2), encoding="utf-8")

    write_summary(run_dir, brief, prompts)
    prompt_files = collect_prompt_files(run_dir)
    reference_files = collect_reference_files(run_dir)
    canonical_files = sync_project_canonical_files(project_dir, run_dir, tuple(reference_files.keys()))

    # 创建 run_state.json
    run_state = state_manager.create_run_state(
        run_dir=run_dir,
        run_id=run_dir.name,
        project_id=brief["project_slug"],
        config_snapshot=brief,
    )
    run_state.prompt_files = prompt_files
    run_state.reference_files = reference_files
    run_state.prompt_risk_report = risk_report_dict
    run_state.stage = "prepare"
    run_state.status = "ready_for_ref_generation"
    state_manager.save_run_state(run_dir, run_state)

    # 更新项目状态
    update_project_state(
        project_dir,
        brief,
        run_dir,
        stage="prepare",
        status="ready_for_ref_generation",
        prompt_files=prompt_files,
        reference_files=reference_files,
        canonical_files=canonical_files,
    )

    # 统计风险
    total_risks = sum(len(report.risks) for report in risk_reports.values())
    high_severity_risks = sum(
        1 for report in risk_reports.values()
        for risk in report.risks
        if risk.severity == "high"
    )

    # 提取前 3 条高风险
    all_high_risks = [
        {"prompt": name, "risk_type": risk.risk_type, "message": risk.reason}
        for name, report in risk_reports.items()
        for risk in report.risks
        if risk.severity == "high"
    ]
    top_risks = all_high_risks[:3]

    # 检查参考图复用策略
    reference_reuse_plan = {}
    existing_refs = brief.get("existing_references", {})
    if "final_frame_poster" in existing_refs:
        reference_reuse_plan["final_frame_poster_reuse"] = "会自动复用为 original，避免生成冲突原图"
    if "identity_source" in existing_refs:
        identity_strategy = brief.get("identity_strategy", "reuse_exact")
        reference_reuse_plan["identity_strategy"] = identity_strategy
        if identity_strategy == "reuse_exact":
            reference_reuse_plan["identity_note"] = "直接使用 identity_source，不额外生成 AI 身份板"

    print(
        json.dumps(
            {
                "project_dir": str(project_dir),
                "project_file": str(project_dir / "project.json"),
                "project_summary_file": str(project_dir / "project-summary.md"),
                "run_dir": str(run_dir),
                "run_state_file": str(run_dir / "run_state.json"),
                "brief_file": str(run_dir / "brief.json"),
                "prompt_files": prompt_files,
                "risk_report_file": str(risk_report_file),
                "risk_summary": {
                    "total_risks": total_risks,
                    "high_severity_risks": high_severity_risks,
                    "top_risks": top_risks,
                },
                "reference_reuse_plan": reference_reuse_plan,
                "next_step": "generate-refs",
                "summary": summarize_reusable_fields(brief),
            },
            ensure_ascii=False,
        )
    )
    return 0


def read_brief_and_prompts(run_dir: Path) -> tuple[dict, dict]:
    brief = json.loads((run_dir / "brief.json").read_text(encoding="utf-8"))
    prompts = {
        "original": (run_dir / "prompts" / "original.txt").read_text(encoding="utf-8"),
        "identity_board": (run_dir / "prompts" / "identity-board.txt").read_text(encoding="utf-8"),
        "storyboard": (run_dir / "prompts" / "storyboard.txt").read_text(encoding="utf-8"),
        "video": (run_dir / "prompts" / "video.txt").read_text(encoding="utf-8"),
    }
    return brief, prompts


def cmd_generate_refs(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    brief, prompts = read_brief_and_prompts(run_dir)
    project_dir = resolve_project_dir_for_run(run_dir, brief)
    state_manager = StateManager(project_dir)
    jobs = build_gpt_image_jobs(brief, run_dir, prompts)

    if args.dry_run:
        print(json.dumps({"jobs": jobs}, ensure_ascii=False, indent=2))
        return 0

    results = []
    for job in jobs:
        proc = run_command(job["command"])
        results.append({"name": job["name"], "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
        if proc.returncode != 0:
            # 更新 run_state.json
            state_manager.update_run_state(
                run_dir,
                stage="generate_refs",
                status="ref_generation_failed",
                reference_files=collect_reference_files(run_dir),
            )
            update_project_state(
                project_dir,
                brief,
                run_dir,
                stage="generate_refs",
                status="ref_generation_failed",
                prompt_files=collect_prompt_files(run_dir),
                reference_files=collect_reference_files(run_dir),
                extra={"last_error": proc.stderr or proc.stdout or f"{job['name']} failed"},
            )
            print(json.dumps({"ok": False, "results": results}, ensure_ascii=False, indent=2))
            return proc.returncode

    reference_files = collect_reference_files(run_dir)
    canonical_files = sync_project_canonical_files(project_dir, run_dir, ("original", "identity_source", "identity_board", "storyboard"))

    # 更新 run_state.json
    state_manager.update_run_state(
        run_dir,
        stage="generate_refs",
        status="references_generated",
        reference_files=reference_files,
    )

    update_project_state(
        project_dir,
        brief,
        run_dir,
        stage="generate_refs",
        status="references_generated",
        prompt_files=collect_prompt_files(run_dir),
        reference_files=reference_files,
        canonical_files=canonical_files,
    )

    # 构建结构化输出
    generated_refs = []
    preview_candidates = []
    for name, path in reference_files.items():
        generated_refs.append({"name": name, "path": path})
        # 只有这三张图需要发送给用户确认
        if name in ("original", "identity_board", "identity_source", "storyboard"):
            preview_candidates.append({"name": name, "path": path})

    # 提取关键帧信息
    storyboard_prompt = prompts.get("storyboard", "")
    beats_count = brief.get("storyboard_strategy", {}).get("beats_count", 0) if isinstance(brief.get("storyboard_strategy"), dict) else 0

    validation_stage = default_validation_stage(brief)
    print(json.dumps({
        "ok": True,
        "results": results,
        "generated_refs": generated_refs,
        "preview_candidates": preview_candidates,
        "requires_user_confirmation": True,
        "next_step": f"validate-run --stage {validation_stage}",
        "keyframe_info": {
            "beats_count": beats_count or len(brief.get("storyboard_beats", [])),
            "ratio": brief.get("ratio", "16:9"),
            "duration": brief.get("duration", 5),
            "video_mode": brief.get("video_mode", "ip_poster"),
        },
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_submit_video(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    brief, prompts = read_brief_and_prompts(run_dir)
    project_dir = resolve_project_dir_for_run(run_dir, brief)
    state_manager = StateManager(project_dir)
    run_state, recovery_actions = load_or_recover_run_state(state_manager, run_dir, brief)

    if not args.dry_run:
        validation_report = run_state.validation_report or {}
        next_action = run_state.next_action or {}
        if not validation_report:
            print(json.dumps({"error": "提交视频前请先执行 validate-run"}, ensure_ascii=False, indent=2))
            return 1
        if not next_action.get("reviewed_at"):
            print(json.dumps({"error": "提交视频前请先执行 review-run"}, ensure_ascii=False, indent=2))
            return 1
        if next_action.get("decision") not in {"proceed", "continue"}:
            print(
                json.dumps(
                    {
                        "error": "当前 review-run 尚未放行提交视频",
                        "next_action": next_action,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

    command_recovery_actions = list(recovery_actions)
    cmd = build_dreamina_command(
        run_dir,
        brief,
        prompts,
        project_dir=project_dir,
        recovery_actions=command_recovery_actions,
    )
    command_recovery_actions.extend(refresh_project_canonical_manifest(state_manager))
    video_mode = brief.get("video_mode", "ip_poster")
    resolved_references = {
        "original": str(
            resolve_reference_path(
                run_dir,
                "original",
                project_dir=project_dir,
            )
        ),
    }
    if video_mode == "ip_poster":
        resolved_identity_source = resolve_reference_path(run_dir, "identity_source", project_dir=project_dir)
        resolved_identity = (
            resolved_identity_source
            if resolved_identity_source.exists()
            else resolve_reference_path(run_dir, "identity_board", project_dir=project_dir)
        )
        resolved_references["identity"] = str(resolved_identity)
    elif video_mode == "shot_clip":
        identity_source = resolve_reference_path(run_dir, "identity_source", project_dir=project_dir)
        if identity_source.exists():
            resolved_references["identity"] = str(identity_source)
    if video_mode in {"ip_poster", "non_ip_poster"}:
        resolved_references["storyboard"] = str(
            resolve_reference_path(
                run_dir,
                "storyboard",
                project_dir=project_dir,
                purpose="submit",
            )
        )

    if args.dry_run:
        print(
            json.dumps(
                {
                    "command": cmd,
                    "resolved_references": resolved_references,
                    "recovery_actions": command_recovery_actions,
                    "validation_gate_status": build_validation_gate_status(run_state),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    proc = run_command(cmd)
    submit_id = save_submit_id(run_dir, proc.stdout)
    save_result_json(run_dir, proc.stdout or proc.stderr)
    write_summary(run_dir, brief, prompts, submit_id=submit_id)

    # 更新 run_state.json
    state_manager.update_run_state(
        run_dir,
        stage="submit_video",
        status="video_submitted" if proc.returncode == 0 else "video_submit_failed",
        artifacts={"result_file": str(run_dir / "dreamina" / "result.json")},
    )

    update_project_state(
        project_dir,
        brief,
        run_dir,
        stage="submit_video",
        status="video_submitted" if proc.returncode == 0 else "video_submit_failed",
        prompt_files=collect_prompt_files(run_dir),
        reference_files=collect_reference_files(run_dir),
        submit_id=submit_id,
        extra={"result_file": str(run_dir / "dreamina" / "result.json")},
    )

    payload = {"returncode": proc.returncode, "submit_id": submit_id, "stdout": proc.stdout, "stderr": proc.stderr}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return proc.returncode


def cmd_fetch_result(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    brief, _ = read_brief_and_prompts(run_dir)
    project_dir = resolve_project_dir_for_run(run_dir, brief)
    state_manager = StateManager(project_dir)
    _, _ = load_or_recover_run_state(state_manager, run_dir, brief)
    submit_id_path = run_dir / "dreamina" / "submit_id.txt"
    submit_id = args.submit_id or submit_id_path.read_text(encoding="utf-8").strip()
    downloads = run_dir / "dreamina" / "downloads"
    proc = run_command(
        [
            args.dreamina_bin,
            "query_result",
            f"--submit_id={submit_id}",
            f"--download_dir={downloads}",
        ]
    )
    save_result_json(run_dir, proc.stdout or proc.stderr)

    # 更新 run_state.json
    state_manager.update_run_state(
        run_dir,
        stage="fetch_result",
        status="video_result_fetched" if proc.returncode == 0 else "video_result_fetch_failed",
        artifacts={
            "result_file": str(run_dir / "dreamina" / "result.json"),
            "downloads_dir": str(downloads),
        },
    )

    update_project_state(
        project_dir,
        brief,
        run_dir,
        stage="fetch_result",
        status="video_result_fetched" if proc.returncode == 0 else "video_result_fetch_failed",
        prompt_files=collect_prompt_files(run_dir),
        reference_files=collect_reference_files(run_dir),
        submit_id=submit_id,
        extra={
            "result_file": str(run_dir / "dreamina" / "result.json"),
            "downloads_dir": str(downloads),
        },
    )
    print(json.dumps({"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}, ensure_ascii=False, indent=2))
    return proc.returncode


def cmd_validate_run(args: argparse.Namespace) -> int:
    """验证运行结果"""
    run_dir = Path(args.run_dir)
    brief, prompts = read_brief_and_prompts(run_dir)
    project_dir = resolve_project_dir_for_run(run_dir, brief)
    state_manager = StateManager(project_dir)
    run_state, recovery_actions = load_or_recover_run_state(state_manager, run_dir, brief)

    # 默认验证阶段按视频类型决定：尾帧模式验证故事板，单镜头素材验证参考系统
    stage = args.stage or default_validation_stage(brief)
    prepare_validation_references(
        run_dir,
        brief,
        stage,
        project_dir=project_dir,
        recovery_actions=recovery_actions,
    )
    recovery_actions.extend(refresh_project_canonical_manifest(state_manager))
    report = validate_run(run_dir, brief, stage)
    report_dict = report.to_dict()
    if recovery_actions:
        report_dict["recovery_actions"] = recovery_actions

    # 保留已有的人工检查状态（如果存在）
    if run_state.validation_report and "manual_checks" in run_state.validation_report:
        old_checks = run_state.validation_report["manual_checks"]
        new_checks = report_dict.get("manual_checks", [])

        # 构建旧检查项的索引
        old_check_index = {check.get("id"): check for check in old_checks}

        # 合并：保留旧的 checked 状态
        for new_check in new_checks:
            check_id = new_check.get("id")
            if check_id in old_check_index:
                new_check["checked"] = old_check_index[check_id].get("checked", False)

    run_state.reference_files = collect_reference_files(run_dir)
    run_state.validation_report = report_dict
    run_state.add_iteration(
        artifact_type=stage,
        prompt=prompt_text_for_stage(stage, prompts),
        issues=report_dict.get("issues", []),
        validation_score=report_dict.get("score", 0.0),
    )
    state_manager.save_run_state(run_dir, run_state)

    persist_validation_report(run_dir, report_dict)

    print(json.dumps(report_dict, ensure_ascii=False, indent=2))
    return 0 if report.passed else 1


def cmd_complete_manual_checks(args: argparse.Namespace) -> int:
    """回写人工检查清单"""
    run_dir = Path(args.run_dir)
    brief, _ = read_brief_and_prompts(run_dir)
    project_dir = resolve_project_dir_for_run(run_dir, brief)
    state_manager = StateManager(project_dir)
    run_state, _ = load_or_recover_run_state(state_manager, run_dir, brief)

    validation_report = run_state.validation_report or {}
    manual_checks = validation_report.get("manual_checks", [])
    if not manual_checks:
        print(json.dumps({"error": "当前 run 没有可回写的人工检查清单"}, ensure_ascii=False, indent=2))
        return 1

    # 如果指定了 --all-passed，标记所有检查项为通过
    if getattr(args, 'all_passed', False):
        for check in manual_checks:
            check["checked"] = True
        updates = {check.get("id"): True for check in manual_checks}
    else:
        try:
            updates = load_manual_check_updates(args)
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
            return 1

        check_index = {check.get("id"): check for check in manual_checks}
        unknown_ids = sorted(check_id for check_id in updates if check_id not in check_index)
        if unknown_ids:
            print(
                json.dumps(
                    {
                        "error": "存在未知的人工检查项",
                        "unknown_ids": unknown_ids,
                        "known_ids": sorted(check_index.keys()),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

        for check_id, checked in updates.items():
            check_index[check_id]["checked"] = checked

    run_state.validation_report = validation_report
    state_manager.save_run_state(run_dir, run_state)
    report_file = persist_validation_report(run_dir, validation_report)

    print(
        json.dumps(
            {
                "ok": True,
                "run_dir": str(run_dir),
                "report_file": str(report_file),
                "manual_checks": manual_checks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_review_run(args: argparse.Namespace) -> int:
    """审查运行结果并决定下一步动作"""
    run_dir = Path(args.run_dir)
    brief, _ = read_brief_and_prompts(run_dir)
    project_dir = resolve_project_dir_for_run(run_dir, brief)
    state_manager = StateManager(project_dir)

    # 加载 run_state
    run_state, recovery_actions = load_or_recover_run_state(state_manager, run_dir, brief)
    if not run_state.validation_report:
        print(json.dumps({"error": "还没有验证报告，请先执行 validate-run"}, ensure_ascii=False, indent=2))
        return 1

    # 加载项目配置
    project_config = state_manager.load_project()
    if project_config is None:
        print(json.dumps({"error": "项目配置不存在"}, ensure_ascii=False, indent=2))
        return 1

    # 创建迭代引擎
    engine = IterationEngine(project_config.iteration_strategy)

    # 决定下一步动作
    decision = engine.decide_next_action(
        validation_report=run_state.validation_report,
        iterations=run_state.iterations,
        stage=run_state.stage,
    )
    decision_payload = decision.to_dict()
    decision_payload["reviewed_at"] = now_iso()
    decision_payload["validation_stage"] = run_state.validation_report.get("stage", "")
    if recovery_actions:
        decision_payload["recovery_actions"] = recovery_actions

    # 更新 run_state.json
    state_manager.update_run_state(
        run_dir,
        next_action=decision_payload,
    )

    print(json.dumps(decision_payload, ensure_ascii=False, indent=2))
    return 0


def cmd_adjust_beats(args: argparse.Namespace) -> int:
    """调整关键帧规划"""
    run_dir = Path(args.run_dir)
    brief_file = run_dir / "brief.json"

    if not brief_file.exists():
        print(json.dumps({"error": "brief.json 不存在"}, ensure_ascii=False, indent=2))
        return 1

    brief = json.loads(brief_file.read_text(encoding="utf-8"))

    # 如果指定了新的 beats
    if args.beats:
        new_beats = args.beats
    elif args.beats_file:
        beats_file = Path(args.beats_file)
        if not beats_file.exists():
            print(json.dumps({"error": f"beats 文件不存在: {args.beats_file}"}, ensure_ascii=False, indent=2))
            return 1
        beats_data = json.loads(beats_file.read_text(encoding="utf-8"))
        if isinstance(beats_data, list):
            new_beats = beats_data
        elif isinstance(beats_data, dict) and "storyboard_beats" in beats_data:
            new_beats = beats_data["storyboard_beats"]
        else:
            print(json.dumps({"error": "beats 文件格式错误，应该是数组或包含 storyboard_beats 的对象"}, ensure_ascii=False, indent=2))
            return 1
    elif args.panel_count:
        # 调整格数
        from scripts.workflow import apply_storyboard_panel_override
        current_beats = brief.get("storyboard_beats", [])
        new_beats = apply_storyboard_panel_override(current_beats, args.panel_count)
    else:
        print(json.dumps({"error": "请通过 --beats、--beats-file 或 --panel-count 指定新的关键帧规划"}, ensure_ascii=False, indent=2))
        return 1

    # 更新 brief
    brief["storyboard_beats"] = new_beats
    if args.panel_count:
        if "storyboard_strategy" not in brief or not isinstance(brief["storyboard_strategy"], dict):
            brief["storyboard_strategy"] = {}
        brief["storyboard_strategy"]["beats_count"] = len(new_beats)

    # 保存 brief
    brief_file.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    # 重新生成 prompts 和 summary
    from scripts.workflow import build_prompts, write_prompts, write_summary
    prompts = build_prompts(brief)
    write_prompts(run_dir, prompts)
    write_summary(run_dir, brief, prompts)

    print(json.dumps({
        "ok": True,
        "run_dir": str(run_dir),
        "new_beats": new_beats,
        "beats_count": len(new_beats),
        "next_step": "generate-refs（需要重新生成故事板）",
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_project_status(args: argparse.Namespace) -> int:
    """显示项目状态"""
    project_dir = Path(args.project_dir)
    state_manager = StateManager(project_dir)

    project_config = state_manager.load_project()
    if project_config is None:
        print(json.dumps({"error": "项目不存在"}, ensure_ascii=False, indent=2))
        return 1

    # 构建输出
    output = {
        "project_name": project_config.project_name,
        "project_id": project_config.project_id,
        "project_dir": project_config.project_dir,
        "state": project_config.state,
        "defaults": project_config.defaults,
        "constraints": {
            "must_have_count": len(project_config.constraints.get("must_have", [])),
            "must_not_have_count": len(project_config.constraints.get("must_not_have", [])),
            "prefer_count": len(project_config.constraints.get("prefer", [])),
        },
        "canonical_files": project_config.canonical_files,
        "recent_runs": project_config.runs[-5:] if project_config.runs else [],
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="dreamina reference video workflow CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="检查 dreamina 与 gpt-image2-gen 是否可用")
    preflight.set_defaults(func=cmd_preflight)

    prepare = subparsers.add_parser("prepare", help="生成运行目录、brief.json 和 4 段提示词")
    prepare.add_argument("--brief-file", help="输入 brief.json")
    prepare.add_argument("--project-name")
    prepare.add_argument("--project-slug")
    prepare.add_argument("--video-mode", choices=["auto", "ip_poster", "non_ip_poster", "shot_clip"])
    prepare.add_argument("--subject")
    prepare.add_argument("--action")
    prepare.add_argument("--scene")
    prepare.add_argument("--style")
    prepare.add_argument("--ratio")
    prepare.add_argument("--duration", type=int)
    prepare.add_argument("--quality-tier")
    prepare.add_argument("--notes")
    prepare.add_argument("--storyboard-strategy")
    prepare.add_argument("--storyboard-panel-count-override", type=int)
    prepare.add_argument("--storyboard-beats-override", action="append")
    prepare.add_argument("--identity-strategy")
    prepare.add_argument("--identity-anchor-rules", action="append")
    prepare.add_argument("--output-root", help="项目根目录，或直接传 outputs/dreamina-reference-video 目录")
    prepare.set_defaults(func=cmd_prepare)

    generate_refs = subparsers.add_parser("generate-refs", help="调用 gpt-image2-gen 生成原图、身份板、故事板")
    generate_refs.add_argument("--run-dir", required=True)
    generate_refs.add_argument("--dry-run", action="store_true")
    generate_refs.set_defaults(func=cmd_generate_refs)

    submit_video = subparsers.add_parser("submit-video", help="调用 dreamina multimodal2video 提交视频任务")
    submit_video.add_argument("--run-dir", required=True)
    submit_video.add_argument("--dry-run", action="store_true")
    submit_video.set_defaults(func=cmd_submit_video)

    fetch = subparsers.add_parser("fetch-result", help="按 submit_id 查询并下载即梦结果")
    fetch.add_argument("--run-dir", required=True)
    fetch.add_argument("--submit-id")
    fetch.add_argument("--dreamina-bin", default=DREAMINA_BIN)
    fetch.set_defaults(func=cmd_fetch_result)

    validate = subparsers.add_parser("validate-run", help="验证运行结果（默认验证 storyboard 阶段）")
    validate.add_argument("--run-dir", required=True)
    validate.add_argument("--stage", choices=["reference_system", "storyboard", "video"],
                         help="验证阶段（默认：storyboard，包含人工检查清单）")
    validate.set_defaults(func=cmd_validate_run)

    complete_manual = subparsers.add_parser("complete-manual-checks", help="回写人工检查清单")
    complete_manual.add_argument("--run-dir", required=True)
    complete_manual.add_argument("--file", help="包含人工检查结果的 JSON 文件")
    complete_manual.add_argument("--check", action="append", help="单项更新，格式为 check_id=true/false")
    complete_manual.add_argument("--all-passed", action="store_true", help="标记所有检查项为通过")
    complete_manual.set_defaults(func=cmd_complete_manual_checks)

    review = subparsers.add_parser("review-run", help="审查运行结果并决定下一步动作")
    review.add_argument("--run-dir", required=True)
    review.set_defaults(func=cmd_review_run)

    adjust_beats = subparsers.add_parser("adjust-beats", help="调整关键帧规划")
    adjust_beats.add_argument("--run-dir", required=True)
    adjust_beats.add_argument("--beats", nargs="+", help="新的关键帧列表")
    adjust_beats.add_argument("--beats-file", help="包含关键帧列表的 JSON 文件")
    adjust_beats.add_argument("--panel-count", type=int, help="调整格数（3-10）")
    adjust_beats.set_defaults(func=cmd_adjust_beats)

    status = subparsers.add_parser("project-status", help="显示项目状态")
    status.add_argument("--project-dir", required=True)
    status.set_defaults(func=cmd_project_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
