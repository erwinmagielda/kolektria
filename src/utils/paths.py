"""
Kolektria path helpers.

Centralises project paths used by the collector, cleaner, PowerShell runner,
reporter, and runtime export workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ------------------------------------------------------------
# SCRIPT NAMES
# ------------------------------------------------------------

BASELINE_SCRIPT = "baseline.ps1"
INVENTORY_SCRIPT = "inventory.ps1"
ADAPTER_SCRIPT = "adapter.ps1"


# ------------------------------------------------------------
# PROJECT ROOT
# ------------------------------------------------------------

def get_root_dir() -> Path:
    """
    Return the Kolektria project root directory.

    Source mode:
        src/kolektria/collector.py

    Executable mode:
        dist/kolektria.exe
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parents[1]

    return Path(__file__).resolve().parents[2]


ROOT_DIR = get_root_dir()


# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

SRC_DIR = ROOT_DIR / "src"
KOLEKTRIA_DIR = SRC_DIR / "kolektria"
UTILS_DIR = SRC_DIR / "utils"
POWERSHELL_DIR = SRC_DIR / "powershell"

DATA_DIR = ROOT_DIR / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
COLLECTED_DIR = DATA_DIR / "collected"

RESULTS_DIR = ROOT_DIR / "results"
REPORTS_DIR = RESULTS_DIR / "reports"

BUILD_DIR = ROOT_DIR / "build"
BUILD_PYINSTALLER_DIR = BUILD_DIR / "pyinstaller"

DIST_DIR = ROOT_DIR / "dist"

BASELINE_SCRIPT_PATH = POWERSHELL_DIR / BASELINE_SCRIPT
INVENTORY_SCRIPT_PATH = POWERSHELL_DIR / INVENTORY_SCRIPT
ADAPTER_SCRIPT_PATH = POWERSHELL_DIR / ADAPTER_SCRIPT


# ------------------------------------------------------------
# PATH DISPLAY
# ------------------------------------------------------------

def relative_path(path: Path) -> str:
    """Return a project-relative path for clean console output."""

    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


# ------------------------------------------------------------
# REQUIRED FILE VALIDATION
# ------------------------------------------------------------

def get_required_script_paths() -> list[Path]:
    """Return PowerShell scripts required by the collector workflow."""

    return [
        BASELINE_SCRIPT_PATH,
        INVENTORY_SCRIPT_PATH,
        ADAPTER_SCRIPT_PATH,
    ]


def ensure_required_files() -> None:
    """Validate that all required PowerShell scripts exist."""

    missing_files = [
        relative_path(script_path)
        for script_path in get_required_script_paths()
        if not script_path.exists()
    ]

    if missing_files:
        missing = ", ".join(missing_files)
        raise RuntimeError(f"Missing required PowerShell script(s): {missing}")


# ------------------------------------------------------------
# OUTPUT DIRECTORIES
# ------------------------------------------------------------

def ensure_output_directories() -> None:
    """Create required output directories if they do not exist."""

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    COLLECTED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)