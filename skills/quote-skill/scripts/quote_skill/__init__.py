"""Helpers for the internal quote skill."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
_VENDOR_DIR = _PACKAGE_ROOT / "python"
if _VENDOR_DIR.exists():
    vendor_path = str(_VENDOR_DIR)
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)

__all__ = ["catalog", "layout", "validators", "project", "renderers"]
