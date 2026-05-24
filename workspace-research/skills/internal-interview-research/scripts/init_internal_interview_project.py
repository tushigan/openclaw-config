from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from internal_interview_research.project import create_internal_interview_project


飞书用户目标正则 = re.compile(r"^(user:ou_[A-Za-z0-9]+)(?::(.*))?$")
飞书open_id正则 = re.compile(r"^(ou_[A-Za-z0-9]+)(?::(.*))?$")


def _parse_participant(value: str) -> dict[str, str]:
    name, separator, remainder = value.partition(":")
    name = name.strip()
    if not name or not separator:
        raise ValueError(f"受访对象格式不合法：{value}")
    remainder = remainder.strip()
    matched_user = 飞书用户目标正则.match(remainder)
    if matched_user:
        return {
            "姓名": name,
            "飞书标识": matched_user.group(1),
            "纳入原因": str(matched_user.group(2) or "").strip(),
        }
    matched_open_id = 飞书open_id正则.match(remainder)
    if matched_open_id:
        return {
            "姓名": name,
            "飞书标识": f"user:{matched_open_id.group(1)}",
            "纳入原因": str(matched_open_id.group(2) or "").strip(),
        }
    raise ValueError(f"受访对象格式不合法：{value}")


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
    parser.add_argument("--project-type", default="真实调研", choices=["真实调研", "链路验收"])
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
        project_type=args.project_type,
    )
    print(json.dumps({"project_dir": str(project_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
