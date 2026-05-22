from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = REPO_ROOT / "python"
REQUIRED_PACKAGES = ["reportlab", "pypdf"]


def _missing_packages() -> list[str]:
    sys.path.insert(0, str(VENDOR_DIR))
    missing: list[str] = []
    for name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(name)
        except ModuleNotFoundError:
            missing.append(name)
    return missing


def main() -> None:
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    missing = _missing_packages()
    if not missing:
        print(f"Runtime already ready: {VENDOR_DIR}")
        return

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--only-binary=:all:",
        "--progress-bar",
        "off",
        "--target",
        str(VENDOR_DIR),
        *missing,
    ]
    subprocess.run(command, check=True)
    print(f"Installed runtime dependencies into: {VENDOR_DIR}")


if __name__ == "__main__":
    main()
