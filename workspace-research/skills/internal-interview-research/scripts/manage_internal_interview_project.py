from __future__ import annotations

import argparse
import json
from pathlib import Path

from internal_interview_research.project import (
    analyze_project,
    advance_project,
    build_manual_continue_worker_contract,
    build_chain_acceptance_test_plan,
    build_dispatch_plan,
    build_final_delivery_payload,
    build_parallel_chain_acceptance_test_plan,
    build_participant_outreach_plan,
    cleanup_prebuilt_shared_sessions,
    close_project,
    evaluate_project_actions,
    finalize_participant,
    finalize_project_on_deadline,
    ingest_participant_reply,
    mark_delivery_complete,
    prepare_feishu_delivery,
    repair_project_participants,
    recover_project_replies,
    register_project_check_job,
    run_project_batch_worker,
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
    participant_parser.add_argument("--business-status")
    participant_parser.add_argument("--link-status")
    participant_parser.add_argument("--timeout-reason")
    participant_parser.add_argument("--closure-method")
    participant_parser.add_argument("--count-as-effective-sample", choices=["true", "false"])
    participant_parser.add_argument("--collected-signal", action="append", default=[])
    participant_parser.add_argument("--sender-account")
    participant_parser.add_argument("--first-message-tool")
    participant_parser.add_argument("--conversation-account")
    participant_parser.add_argument("--execution-channel-truth-type")
    participant_parser.add_argument("--execution-agent")
    participant_parser.add_argument("--execution-session-id")
    participant_parser.add_argument("--execution-session-key")
    participant_parser.add_argument("--helper-execution-session-id")
    participant_parser.add_argument("--helper-execution-session-key")
    participant_parser.add_argument("--conversation-binding-id")
    participant_parser.add_argument("--conversation-binding-status")
    participant_parser.add_argument("--binding-confirmed-at")
    participant_parser.add_argument("--binding-confirmation-evidence")
    participant_parser.add_argument("--binding-target-session-key")
    participant_parser.add_argument("--binding-check-result")
    participant_parser.add_argument("--last-message-id")
    participant_parser.add_argument("--last-chat-id")
    participant_parser.add_argument("--send-confirmation-status")
    participant_parser.add_argument("--send-confirmation-time")
    participant_parser.add_argument("--send-confirmation-evidence")
    participant_parser.add_argument("--last-card-id")
    participant_parser.add_argument("--last-card-result")
    participant_parser.add_argument("--last-recovered-at")
    participant_parser.add_argument("--recovered-to-research", choices=["true", "false"])
    participant_parser.add_argument("--closure-reached", choices=["true", "false"])
    participant_parser.add_argument("--closure-reason")

    finalize_participant_parser = subparsers.add_parser("finalize-participant")
    finalize_participant_parser.add_argument("--project-dir", required=True)
    finalize_participant_parser.add_argument("--name", required=True)
    finalize_participant_parser.add_argument("--finalized-at")

    ingest_reply_parser = subparsers.add_parser("ingest-reply")
    ingest_reply_parser.add_argument("--project-dir", required=True)
    ingest_reply_parser.add_argument("--name", required=True)
    ingest_reply_parser.add_argument("--reply-text", required=True)
    ingest_reply_parser.add_argument("--reply-at")
    ingest_reply_parser.add_argument("--assistant-text")
    ingest_reply_parser.add_argument("--execution-session-key")
    ingest_reply_parser.add_argument("--participant-open-id")
    ingest_reply_parser.add_argument("--project-type")

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--project-dir", required=True)
    inspect_parser.add_argument("--now-at")
    inspect_parser.add_argument("--cron-jobs-path")

    advance_parser = subparsers.add_parser("advance")
    advance_parser.add_argument("--project-dir", required=True)
    advance_parser.add_argument("--now-at")
    advance_parser.add_argument("--config-path", default="/Users/a123/.openclaw/openclaw.json")
    advance_parser.add_argument("--requester-session-key")
    advance_parser.add_argument("--requester-session-root")
    advance_parser.add_argument("--cron-jobs-path")

    worker_contract_parser = subparsers.add_parser("manual-continue-contract")
    worker_contract_parser.add_argument("--project-dir", required=True)
    worker_contract_parser.add_argument("--trigger", default="manual")
    worker_contract_parser.add_argument("--now-at")
    worker_contract_parser.add_argument("--config-path", default="/Users/a123/.openclaw/openclaw.json")
    worker_contract_parser.add_argument("--requester-session-key")
    worker_contract_parser.add_argument("--requester-session-root")
    worker_contract_parser.add_argument("--cron-jobs-path")

    run_batch_worker_parser = subparsers.add_parser("run-batch-worker")
    run_batch_worker_parser.add_argument("--project-dir", required=True)
    run_batch_worker_parser.add_argument("--trigger", default="manual")
    run_batch_worker_parser.add_argument("--status", choices=["prepare", "started", "heartbeat", "finished"], default="prepare")
    run_batch_worker_parser.add_argument("--worker-run-id")
    run_batch_worker_parser.add_argument("--worker-session-key")
    run_batch_worker_parser.add_argument("--summary")
    run_batch_worker_parser.add_argument("--now-at")
    run_batch_worker_parser.add_argument("--config-path", default="/Users/a123/.openclaw/openclaw.json")
    run_batch_worker_parser.add_argument("--requester-session-key")
    run_batch_worker_parser.add_argument("--requester-session-root")
    run_batch_worker_parser.add_argument("--cron-jobs-path")

    dispatch_parser = subparsers.add_parser("dispatch-plan")
    dispatch_parser.add_argument("--project-dir", required=True)
    dispatch_parser.add_argument("--batch-size", type=int)
    dispatch_parser.add_argument("--batch-interval-minutes", type=int, default=10)
    dispatch_parser.add_argument("--config-path", default="/Users/a123/.openclaw/openclaw.json")
    dispatch_parser.add_argument("--requester-session-key")
    dispatch_parser.add_argument("--requester-session-root")

    outreach_parser = subparsers.add_parser("outreach-plan")
    outreach_parser.add_argument("--project-dir", required=True)
    outreach_parser.add_argument("--name", required=True)
    outreach_parser.add_argument("--research-account-ready", choices=["true", "false"], default="true")
    outreach_parser.add_argument("--card-supported", choices=["true", "false"], default="true")
    outreach_parser.add_argument("--config-path", default="/Users/a123/.openclaw/openclaw.json")
    outreach_parser.add_argument("--requester-session-key")
    outreach_parser.add_argument("--requester-session-root")

    acceptance_parser = subparsers.add_parser("acceptance-plan")
    acceptance_parser.add_argument("--project-dir", required=True)
    acceptance_parser.add_argument("--name", required=True, action="append")
    acceptance_parser.add_argument("--config-path", default="/Users/a123/.openclaw/openclaw.json")
    acceptance_parser.add_argument("--requester-session-key")
    acceptance_parser.add_argument("--requester-session-root")

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--project-dir", required=True)
    finalize_parser.add_argument("--now-at")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--project-dir", required=True)
    analyze_parser.add_argument("--now-at")
    analyze_parser.add_argument("--group-by-org-info", choices=["true", "false"], default="false")

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

    delivery_complete_parser = subparsers.add_parser("delivery-complete")
    delivery_complete_parser.add_argument("--project-dir", required=True)
    delivery_complete_parser.add_argument("--delivered-at")
    delivery_complete_parser.add_argument("--doc-url")
    delivery_complete_parser.add_argument("--summary-message-id")
    delivery_complete_parser.add_argument("--cron-jobs-path")

    recover_parser = subparsers.add_parser("recover-replies")
    recover_parser.add_argument("--project-dir", required=True)
    recover_parser.add_argument("--gateway-log-path")
    recover_parser.add_argument("--session-root")
    recover_parser.add_argument("--research-session-root")

    repair_parser = subparsers.add_parser("repair-participants")
    repair_parser.add_argument("--project-dir", required=True)

    cleanup_prebuilt_parser = subparsers.add_parser("cleanup-prebuilt-shared")
    cleanup_prebuilt_parser.add_argument("--project-dir", required=True)
    cleanup_prebuilt_parser.add_argument("--session-root")
    cleanup_prebuilt_parser.add_argument("--name", action="append", default=[])

    close_parser = subparsers.add_parser("close-project")
    close_parser.add_argument("--project-dir", required=True)
    close_parser.add_argument("--now-at")

    cron_parser = subparsers.add_parser("register-cron")
    cron_parser.add_argument("--project-dir", required=True)
    cron_parser.add_argument("--cron-jobs-path", required=True)
    cron_parser.add_argument("--interval-minutes", type=int, default=180)
    cron_parser.add_argument("--report-mode", choices=["changed-only", "every-round"], default="every-round")
    cron_parser.add_argument("--auto-created", choices=["true", "false"], default="false")
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
        recovered_to_research = None
        if args.recovered_to_research is not None:
            recovered_to_research = args.recovered_to_research == "true"
        count_as_effective_sample = None
        if args.count_as_effective_sample is not None:
            count_as_effective_sample = args.count_as_effective_sample == "true"
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
            business_status=args.business_status,
            link_status=args.link_status,
            timeout_reason=args.timeout_reason,
            closure_method=args.closure_method,
            count_as_effective_sample=count_as_effective_sample,
            collected_signals=args.collected_signal,
            sender_account=args.sender_account,
            first_message_tool=args.first_message_tool,
            conversation_account=args.conversation_account,
            execution_channel_truth_type=args.execution_channel_truth_type,
            execution_agent=args.execution_agent,
            execution_session_id=args.execution_session_id,
            execution_session_key=args.execution_session_key,
            helper_execution_session_id=args.helper_execution_session_id,
            helper_execution_session_key=args.helper_execution_session_key,
            conversation_binding_id=args.conversation_binding_id,
            conversation_binding_status=args.conversation_binding_status,
            binding_confirmed_at=args.binding_confirmed_at,
            binding_confirmation_evidence=args.binding_confirmation_evidence,
            binding_target_session_key=args.binding_target_session_key,
            binding_check_result=args.binding_check_result,
            last_message_id=args.last_message_id,
            last_chat_id=args.last_chat_id,
            send_confirmation_status=args.send_confirmation_status,
            send_confirmation_time=args.send_confirmation_time,
            send_confirmation_evidence=args.send_confirmation_evidence,
            last_card_id=args.last_card_id,
            last_card_result=args.last_card_result,
            last_recovered_at=args.last_recovered_at,
            recovered_to_research=recovered_to_research,
            closure_reached=closure_reached,
            closure_reason=args.closure_reason,
        )
    elif args.command == "inspect":
        result = evaluate_project_actions(
            project_dir=Path(args.project_dir),
            now_at=args.now_at,
            cron_jobs_path=Path(args.cron_jobs_path) if args.cron_jobs_path else None,
        )
    elif args.command == "finalize-participant":
        result = finalize_participant(
            project_dir=Path(args.project_dir),
            participant_name=args.name,
            finalized_at=args.finalized_at,
        )
    elif args.command == "ingest-reply":
        result = ingest_participant_reply(
            project_dir=Path(args.project_dir),
            participant_name=args.name,
            reply_text=args.reply_text,
            reply_at=args.reply_at,
            assistant_text=args.assistant_text,
            execution_session_key=args.execution_session_key,
            participant_open_id=args.participant_open_id,
            project_type=args.project_type,
        )
    elif args.command == "advance":
        result = advance_project(
            project_dir=Path(args.project_dir),
            now_at=args.now_at,
            config_path=Path(args.config_path),
            requester_session_key=args.requester_session_key,
            requester_session_root=Path(args.requester_session_root) if args.requester_session_root else Path("/Users/a123/.openclaw/agents/research/sessions"),
            cron_jobs_path=Path(args.cron_jobs_path) if args.cron_jobs_path else None,
        )
    elif args.command == "manual-continue-contract":
        result = build_manual_continue_worker_contract(
            project_dir=Path(args.project_dir),
            trigger=args.trigger,
            now_at=args.now_at,
            config_path=Path(args.config_path),
            requester_session_key=args.requester_session_key,
            requester_session_root=Path(args.requester_session_root) if args.requester_session_root else Path("/Users/a123/.openclaw/agents/research/sessions"),
            cron_jobs_path=Path(args.cron_jobs_path) if args.cron_jobs_path else None,
        )
    elif args.command == "run-batch-worker":
        result = run_project_batch_worker(
            project_dir=Path(args.project_dir),
            trigger=args.trigger,
            status=args.status,
            worker_run_id=args.worker_run_id,
            worker_session_key=args.worker_session_key,
            summary=args.summary,
            now_at=args.now_at,
            config_path=Path(args.config_path),
            requester_session_key=args.requester_session_key,
            requester_session_root=Path(args.requester_session_root) if args.requester_session_root else Path("/Users/a123/.openclaw/agents/research/sessions"),
            cron_jobs_path=Path(args.cron_jobs_path) if args.cron_jobs_path else None,
        )
    elif args.command == "dispatch-plan":
        result = build_dispatch_plan(
            project_dir=Path(args.project_dir),
            batch_size=args.batch_size,
            batch_interval_minutes=args.batch_interval_minutes,
            config_path=Path(args.config_path),
            requester_session_key=args.requester_session_key,
            requester_session_root=Path(args.requester_session_root) if args.requester_session_root else Path("/Users/a123/.openclaw/agents/research/sessions"),
        )
    elif args.command == "outreach-plan":
        result = build_participant_outreach_plan(
            project_dir=Path(args.project_dir),
            participant_name=args.name,
            research_account_ready=args.research_account_ready == "true",
            card_supported=args.card_supported == "true",
            config_path=Path(args.config_path),
            requester_session_key=args.requester_session_key,
            requester_session_root=Path(args.requester_session_root) if args.requester_session_root else Path("/Users/a123/.openclaw/agents/research/sessions"),
        )
    elif args.command == "acceptance-plan":
        if len(args.name) == 1:
            result = build_chain_acceptance_test_plan(
                project_dir=Path(args.project_dir),
                participant_name=args.name[0],
                config_path=Path(args.config_path),
                requester_session_key=args.requester_session_key,
                requester_session_root=Path(args.requester_session_root) if args.requester_session_root else Path("/Users/a123/.openclaw/agents/research/sessions"),
            )
        else:
            result = build_parallel_chain_acceptance_test_plan(
                project_dir=Path(args.project_dir),
                participant_names=args.name,
                config_path=Path(args.config_path),
                requester_session_key=args.requester_session_key,
                requester_session_root=Path(args.requester_session_root) if args.requester_session_root else Path("/Users/a123/.openclaw/agents/research/sessions"),
            )
    elif args.command == "finalize":
        result = finalize_project_on_deadline(project_dir=Path(args.project_dir), now_at=args.now_at)
    elif args.command == "analyze":
        result = analyze_project(
            project_dir=Path(args.project_dir),
            now_at=args.now_at,
            group_by_org_info=args.group_by_org_info == "true",
        )
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
    elif args.command == "delivery-complete":
        result = mark_delivery_complete(
            project_dir=Path(args.project_dir),
            delivered_at=args.delivered_at,
            doc_url=args.doc_url,
            summary_message_id=args.summary_message_id,
            cron_jobs_path=Path(args.cron_jobs_path) if args.cron_jobs_path else None,
        )
    elif args.command == "recover-replies":
        kwargs = {"project_dir": Path(args.project_dir)}
        if args.gateway_log_path:
            kwargs["gateway_log_path"] = Path(args.gateway_log_path)
        if args.session_root:
            kwargs["session_root"] = Path(args.session_root)
        if args.research_session_root:
            kwargs["research_session_root"] = Path(args.research_session_root)
        result = recover_project_replies(**kwargs)
    elif args.command == "repair-participants":
        result = repair_project_participants(project_dir=Path(args.project_dir))
    elif args.command == "cleanup-prebuilt-shared":
        kwargs = {"project_dir": Path(args.project_dir)}
        if args.session_root:
            kwargs["session_root"] = Path(args.session_root)
        if args.name:
            kwargs["participant_names"] = args.name
        result = cleanup_prebuilt_shared_sessions(**kwargs)
    elif args.command == "close-project":
        result = close_project(project_dir=Path(args.project_dir), now_at=args.now_at)
    else:
        result = register_project_check_job(
            project_dir=Path(args.project_dir),
            cron_jobs_path=Path(args.cron_jobs_path),
            interval_minutes=args.interval_minutes,
            report_mode=args.report_mode,
            auto_created=args.auto_created == "true",
            agent_id=args.agent_id,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
