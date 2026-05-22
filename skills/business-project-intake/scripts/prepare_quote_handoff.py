from __future__ import annotations

import argparse
import json
from pathlib import Path

from business_project.project import prepare_quote_handoff


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--trigger-reason", required=True)
    parser.add_argument("--recommended-case-type", required=True)
    parser.add_argument("--confirmed-scope", action="append", default=[])
    parser.add_argument("--excluded-scope", action="append", default=[])
    args = parser.parse_args()

    payload = prepare_quote_handoff(
        project_dir=Path(args.project_dir),
        trigger_reason=args.trigger_reason,
        recommended_case_type=args.recommended_case_type,
        confirmed_scope=args.confirmed_scope,
        excluded_scope=args.excluded_scope,
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
