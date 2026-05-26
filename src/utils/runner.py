"""
Kolektria PowerShell runner.

Provides a small wrapper around non-interactive PowerShell script execution
and JSON parsing.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


# ------------------------------------------------------------
# POWERSHELL EXECUTION
# ------------------------------------------------------------

def run_powershell_script(
    script_path: Path,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """Execute a PowerShell script and return parsed JSON output."""

    args = extra_args or []

    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        *args,
    ]

    result = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        error_output = result.stderr.strip() or result.stdout.strip()

        if error_output:
            raise RuntimeError(f"{script_path.name} failed: {error_output}")

        raise RuntimeError(f"{script_path.name} failed with exit code {result.returncode}")

    stdout = result.stdout.strip()

    if not stdout:
        raise RuntimeError(f"{script_path.name} returned no output")

    try:
        parsed_output = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{script_path.name} returned invalid JSON") from exc

    if not isinstance(parsed_output, dict):
        raise RuntimeError(f"{script_path.name} returned unexpected JSON structure")

    return parsed_output