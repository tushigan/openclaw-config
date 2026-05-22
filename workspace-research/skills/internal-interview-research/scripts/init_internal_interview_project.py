from __future__ import annotations

import argparse
import json
from pathlib import Path

from internal_interview_research.project import create_internal_interview_project


def _parse_participant(value: str) -> dict[str, str]:
    parts = value.split(":", 2)
    name = parts[0].strip()
    feishu_id = parts[1].strip() if len(parts) >= 2 else ""
    reason = parts[2].strip() if len(parts) >= 3 else ""
    return {"姓名": name, "飞书标识": feishu_id, "纳入原因": reason}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--initiator-name", required=True)
    parser.add_argument("--initiator-feishu-id", required=True)
    parser.add_argument("--research-goal", required=True)
    parser.add_argument("--research-scope", required=True)
    parser.add_argument("--participant-source-mode", required=True, choices=["直接名单", "范围建议"])
    parser.add_argument("--participant-scope-text", default="")
    parser.add_argument("--project-deadline-at", default="")
    parser.add_argument("--participant", action="append", default=[])
    args = parser.parse_args()

    project_dir = create_internal_interview_project(
        workspace_root=Path(args.workspace_root),
        project_name=args.project_name,
        initiator_name=args.initiator_name,
        initiator_feishu_id=args.initiator_feishu_id,
        research_goal=args.research_goal,
        research_scope=args.research_scope,
        participant_source_mode=args.participant_source_mode,
        participant_scope_text=args.participant_scope_text,
        project_deadline_at=args.project_deadline_at,
        participants=[_parse_participant(item) for item in args.participant],
    )
    print(json.dumps({"project_dir": str(project_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
