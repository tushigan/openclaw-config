#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import (  # noqa: E402
    STAGE_TRANSITIONS,
    append_task_confirmation,
    append_audit,
    load_task_state,
    read_json,
    resolve_project_dir,
    resolve_task_dir,
    update_state,
    update_task_manifest_entry,
    update_task_state,
    utc_now,
    write_json,
)


APPROVE_DECISIONS = {"approve", "approved", "confirmed", "yes"}
TASK_KINDS = {"task_brief", "task_generation_review"}


def is_approved(decision: str) -> bool:
    return (decision or "").strip().lower() in APPROVE_DECISIONS


def main() -> None:
    parser = argparse.ArgumentParser(description="记录用户确认阀门")
    parser.add_argument("--project-dir", required=True, help="项目目录")
    parser.add_argument("--task-id", default="", help="任务 ID 或任务目录")
    parser.add_argument(
        "--kind",
        required=True,
        choices=["risk_continue", "creative_direction", "generation_review", "task_brief", "task_generation_review"],
        help="确认类型",
    )
    parser.add_argument("--decision", required=True, help="确认结果")
    parser.add_argument("--note", default="", help="用户说明")
    parser.add_argument("--selected-output", default="", help="选中的输出文件")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project_dir)

    if args.kind in TASK_KINDS:
        if not args.task_id:
            raise SystemExit("任务级确认必须传入 --task-id。")
        task_dir = resolve_task_dir(project_dir, args.task_id)
        task_state = load_task_state(task_dir)
        approved = is_approved(args.decision)

        if args.kind == "task_brief":
            brief_path = task_dir / "task_brief.json"
            brief = read_json(brief_path, {})
            brief["confirmation"] = {
                "recorded_at": utc_now(),
                "decision": args.decision,
                "note": args.note,
            }
            brief["status"] = "confirmed" if approved else "revision_requested"
            write_json(brief_path, brief)

            update_task_state(
                task_dir,
                current_stage="task_brief_confirmed" if approved else "task_brief_waiting_confirm",
                stage_status="ready" if approved else "waiting_user",
                workflow_flag_updates={
                    "brief_confirmed": approved,
                    "generation_allowed": approved,
                },
            )
            update_task_manifest_entry(
                project_dir,
                task_state["task_id"],
                {
                    "status": "brief_confirmed" if approved else "brief_revision_requested",
                },
            )
            update_state(
                project_dir,
                current_stage="task_brief_confirmed" if approved else "task_brief_waiting_confirm",
                stage_status="ready" if approved else "waiting_user",
                active_task_id=task_state["task_id"],
            )
        else:
            generation_path = task_dir / "generation_manifest.json"
            generation = read_json(generation_path, {})
            version_id = task_state.get("selected_version_id", "") or generation.get("latest_version_id", "")
            review = {
                "recorded_at": utc_now(),
                "decision": args.decision,
                "note": args.note,
                "selected_output": args.selected_output,
                "version_id": version_id,
            }
            generation["review"] = review
            generation["latest_status"] = "approved" if approved else "revision_requested"
            if args.selected_output:
                generation["latest_output"] = args.selected_output
            for item in generation.get("versions", []):
                if item.get("version_id") == version_id:
                    item["status"] = generation["latest_status"]
                    if args.selected_output:
                        item["output"] = args.selected_output
                    item["review"] = review
            write_json(generation_path, generation)

            latest_output = args.selected_output or task_state.get("latest_output", "")
            update_task_state(
                task_dir,
                current_stage="task_generation_approved" if approved else "task_generation_revision_requested",
                stage_status="ready" if approved else "waiting_user",
                workflow_flag_updates={
                    "result_approved": approved,
                    "generation_allowed": approved,
                },
                field_updates={
                    "latest_output": latest_output,
                },
            )
            update_task_manifest_entry(
                project_dir,
                task_state["task_id"],
                {
                    "status": "approved" if approved else "revision_requested",
                    "latest_output": latest_output,
                },
            )
            update_state(
                project_dir,
                current_stage="task_generation_approved" if approved else "task_generation_revision_requested",
                stage_status="ready" if approved else "waiting_user",
                active_task_id=task_state["task_id"],
                workflow_flag_updates={
                    "delivery_ready": approved,
                },
            )

        confirmation_payload = {
            "recorded_at": utc_now(),
            "kind": args.kind,
            "decision": args.decision,
            "note": args.note,
            "selected_output": args.selected_output,
        }
        append_task_confirmation(task_dir, confirmation_payload)
        append_audit(
            project_dir,
            "task_confirmation_recorded",
            {
                "task_id": task_state["task_id"],
                **confirmation_payload,
            },
        )
        print(f"task_id={task_state['task_id']}")
        print(f"kind={args.kind}")
        print(f"decision={args.decision}")
        return

    state_updates = {}
    current_stage = STAGE_TRANSITIONS[args.kind]
    stage_status = "ready"

    if args.kind == "risk_continue":
        intake = read_json(project_dir / "intake_manifest.json", {})
        intake["risk_confirmation"] = {
            "recorded_at": utc_now(),
            "decision": args.decision,
            "note": args.note,
        }
        write_json(project_dir / "intake_manifest.json", intake)
        state_updates = {
            "risk_accepted": args.decision in {"approve", "approved", "continue_with_risk", "yes"},
        }
        if state_updates["risk_accepted"]:
            current_stage = "product_profile_ready"
    elif args.kind == "creative_direction":
        direction = read_json(project_dir / "creative_direction.json", {})
        direction["confirmation"] = {
            "recorded_at": utc_now(),
            "decision": args.decision,
            "note": args.note,
        }
        direction["status"] = "confirmed" if is_approved(args.decision) else "revision_requested"
        write_json(project_dir / "creative_direction.json", direction)
        approved = direction["status"] == "confirmed"
        state_updates = {
            "creative_confirmed": approved,
            "generation_allowed": approved,
        }
        current_stage = "creative_direction_confirmed" if approved else "creative_direction_waiting_confirm"
        stage_status = "ready" if approved else "waiting_user"
    else:
        generation = read_json(project_dir / "generation_manifest.json", {})
        generation["review"] = {
            "recorded_at": utc_now(),
            "decision": args.decision,
            "note": args.note,
            "selected_output": args.selected_output,
        }
        generation["latest_status"] = "approved" if is_approved(args.decision) else "revision_requested"
        write_json(project_dir / "generation_manifest.json", generation)
        approved = generation["latest_status"] == "approved"
        state_updates = {
            "delivery_ready": approved,
        }
        current_stage = "generation_approved" if approved else "generation_revision_requested"
        stage_status = "ready" if approved else "waiting_user"

    update_state(
        project_dir,
        current_stage=current_stage,
        stage_status=stage_status,
        workflow_flag_updates=state_updates,
    )
    append_audit(
        project_dir,
        "confirmation_recorded",
        {
            "kind": args.kind,
            "decision": args.decision,
            "note": args.note,
            "selected_output": args.selected_output,
        },
    )
    print(f"kind={args.kind}")
    print(f"decision={args.decision}")


if __name__ == "__main__":
    main()
