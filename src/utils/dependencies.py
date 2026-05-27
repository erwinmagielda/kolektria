"""
Kolektria dependency helpers.

Checks and bootstraps external PowerShell dependencies required by the
collector workflow.
"""

from __future__ import annotations

import subprocess


# ------------------------------------------------------------
# POWERSHELL MODULES
# ------------------------------------------------------------

MSRC_MODULE_NAME = "MsrcSecurityUpdates"


# ------------------------------------------------------------
# POWERSHELL EXECUTION
# ------------------------------------------------------------

def run_powershell_command(command: str, timeout_seconds: int = 240) -> subprocess.CompletedProcess[str]:
    """Run a non-interactive PowerShell command."""

    return subprocess.run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


# ------------------------------------------------------------
# MSRC MODULE CHECK
# ------------------------------------------------------------

def is_msrc_module_available() -> bool:
    """Return True when the MSRC PowerShell module is installed."""

    command = (
        f"if (Get-Module -ListAvailable -Name {MSRC_MODULE_NAME}) "
        "{ exit 0 } else { exit 1 }"
    )

    result = run_powershell_command(
        command=command,
        timeout_seconds=60,
    )

    return result.returncode == 0


def install_msrc_module() -> None:
    """Install the MSRC PowerShell module for the current user."""

    command = (
        "$ErrorActionPreference = 'Stop'; "
        "Install-PackageProvider "
        "-Name NuGet "
        "-MinimumVersion 2.8.5.201 "
        "-Scope CurrentUser "
        "-Force; "
        "Set-PSRepository "
        "-Name PSGallery "
        "-InstallationPolicy Trusted; "
        f"Install-Module "
        f"-Name {MSRC_MODULE_NAME} "
        "-Scope CurrentUser "
        "-Force "
        "-AllowClobber"
    )

    try:
        result = run_powershell_command(
            command=command,
            timeout_seconds=300,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("MSRC PowerShell module installation timed out") from exc

    if result.returncode != 0:
        error_output = result.stderr.strip() or result.stdout.strip()

        if error_output:
            raise RuntimeError(f"MSRC PowerShell module installation failed: {error_output}")

        raise RuntimeError("MSRC PowerShell module installation failed")