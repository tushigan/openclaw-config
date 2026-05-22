from __future__ import annotations

import argparse
import json
from pathlib import Path

from internal_interview_research.project import (
    build_final_delivery_payload,
    build_participant_outreach_plan,
    evaluate_project_actions,
    finalize_project_on_deadline,
    prepare_feishu_delivery,
    register_project_check_job,
    stop_project_and_cleanup,
    update_participant,
    update_project_deadline,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    deadline_parser = subparsers.add_parser("deadline")
    deadline_parser.add_argument("--project-dir", required=True)
    deadline_parser.add_argument("--new-deadline-at", required=True)
    deadline_parser.add_argument("--changed-by", required=True)
    deadline_parser.add_argument("--reason", required=True)

    participant_parser = subparsers.add_parser("participant")
    participant_parser.add_argument("--project-dir", required=True)
    participant_parser.add_argument("--name", required=True)
    participant_parser.add_argument("--status")
    participant_parser.add_argument("--feishu-id")
    participant_parser.add_argument("--note-path")
    participant_parser.add_argument("--summary")
    participant_parser.add_argument("--last-outbound-at")
    participant_parser.add_argument("--last-inbound-at")
    participant_parser.add_argument("--followup-count", type=int)
    participant_parser.add_argument("--inclusion-reason")
    participant_parser.add_argument("--deadline-reminder-sent", choices=["true", "false"])
    participant_parser.add_argument("--confirm-suggested-list", action="store_true")
    participant_parser.add_argument("--question-mode")
    participant_parser.add_argument("--card-type")
    participant_parser.add_argument("--button-question-count", type=int)
    participant_parser.add_argument("--choice-question-count", type=int)
    participant_parser.add_argument("--open-question-count", type=int)
    participant_parser.add_argument("--effective-question-count", type=int)
    participant_parser.add_argument("--collected-signal", action="append", default=[])
    participant_parser.add_argument("--sender-account")
    participant_parser.add_argument("--first-message-tool")
    participant_parser.add_argument("--conversation-account")
    participant_parser.add_argument("--closure-reached", choices=["true", "false"])
    participant_parser.add_argument("--closure-reason")

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--project-dir", required=True)
    inspect_parser.add_argument("--now-at")

    outreach_parser = subparsers.add_parser("outreach-plan")
    outreach_parser.add_argument("--project-dir", required=True)
    outreach_parser.add_argument("--name", required=True)
    outreach_parser.add_argument("--research-account-ready", choices=["true", "false"], default="true")
    outreach_parser.add_argument("--card-supported", choices=["true", "false"], default="true")

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--project-dir", required=True)
    finalize_parser.add_argument("--now-at")

    stop_parser = subparsers.add_parser("stop")
    stop_parser.add_argument("--project-dir", required=True)
    stop_parser.add_argument("--stopped-by", required=True)
    stop_parser.add_argument("--stop-reason", required=True)
    stop_parser.add_argument("--cron-jobs-path")
    stop_parser.add_argument("--now-at")

    delivery_parser = subparsers.add_parser("delivery")
    delivery_parser.add_argument("--project-dir", required=True)

    prepare_delivery_parser = subparsers.add_parser("prepare-delivery")
    prepare_delivery_parser.add_argument("--project-dir", required=True)

    cron_parser = subparsers.add_parser("register-cron")
    cron_parser.add_argument("--project-dir", required=True)
    cron_parser.add_argument("--cron-jobs-path", required=True)
    cron_parser.add_argument("--interval-minutes", type=int, default=30)
    cron_parser.add_argument("--agent-id", default="research")

    args = parser.parse_args()

    if args.command == "deadline":
        result = update_project_deadline(
            project_dir=Path(args.project_dir),
            new_deadline_at=args.new_deadline_at,
            changed_by=args.changed_by,
            reason=args.reason,
        )
    elif args.command == "participant":
        reminder_sent = None
        if args.deadline_reminder_sent is not None:
            reminder_sent = args.deadline_reminder_sent == "true"
        closure_reached = None
        if args.closure_reached is not None:
            closure_reached = args.closure_reached == "true"
        result = update_participant(
            project_dir=Path(args.project_dir),
            participant_name=args.name,
            status=args.status,
            feishu_id=args.feishu_id,
            note_path=args.note_path,
            summary=args.summary,
            last_outbound_at=args.last_outbound_at,
            last_inbound_at=args.last_inbound_at,
            followup_count=args.followup_count,
            inclusion_reason=args.inclusion_reason,
            deadline_reminder_sent=reminder_sent,
            confirm_suggested_list=args.confirm_suggested_list,
            question_mode=args.question_mode,
            card_type=args.card_type,
            button_question_count=args.button_question_count,
            choice_question_count=args.choice_question_count,
            open_question_count=args.open_question_count,
            effective_question_count=args.effective_question_count,
            collected_signals=args.collected_signal,
            sender_account=args.sender_account,
            first_message_tool=args.first_message_tool,
            conversation_account=args.conversation_account,
            closure_reached=closure_reached,
            closure_reason=args.closure_reason,
        )
    elif args.command == "inspect":
        result = evaluate_project_actions(project_dir=Path(args.project_dir), now_at=args.now_at)
    elif args.command == "outreach-plan":
        result = build_participant_outreach_plan(
            project_dir=Path(args.project_dir),
            participant_name=args.name,
            research_account_ready=args.research_account_ready == "true",
            card_supported=args.card_supported == "true",
        )
    elif args.command == "finalize":
        result = finalize_project_on_deadline(project_dir=Path(args.project_dir), now_at=args.now_at)
    elif args.command == "stop":
        cron_jobs_path = Path(args.cron_jobs_path) if args.cron_jobs_path else None
        result = stop_project_and_cleanup(
            project_dir=Path(args.project_dir),
            stopped_by=args.stopped_by,
            stop_reason=args.stop_reason,
            cron_jobs_path=cron_jobs_path,
            now_at=args.now_at,
        )
    elif args.command == "delivery":
        result = build_final_delivery_payload(project_dir=Path(args.project_dir))
    elif args.command == "prepare-delivery":
        result = prepare_feishu_delivery(project_dir=Path(args.project_dir))
    else:
        result = register_project_check_job(
            project_dir=Path(args.project_dir),
            cron_jobs_path=Path(args.cron_jobs_path),
            interval_minutes=args.interval_minutes,
            agent_id=args.agent_id,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
