#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260519-005"
EXEC_SCRIPT="/Users/a123/.openclaw/workspace/skills/brand-poster-creator/scripts/execute_generation.py"

python3 "${EXEC_SCRIPT}" \
  --project-dir "${PROJECT_DIR}" \
  --size 2160x3840 \
  --aspect 9:16 \
  --model gpt-image-2-pro
