"""
Kolektria console output helpers.

Keeps scanner output consistent across the launcher and Python workflow.
"""

from __future__ import annotations

import sys


# ------------------------------------------------------------
# BANNER
# ------------------------------------------------------------

def print_banner() -> None:
    """Print the Kolektria banner."""

    print()
    print("============================================================")
    print(" Kolektria")
    print(" Windows Patch-State Collector")
    print("============================================================")
    print()


# ------------------------------------------------------------
# STATUS LINES
# ------------------------------------------------------------

def print_step(message: str) -> None:
    """Print an active workflow step."""

    print(f"[*] {message}")


def print_success(message: str) -> None:
    """Print a successful workflow step."""

    print(f"[+] {message}")


def print_info(message: str) -> None:
    """Print an informational message."""

    print(f"[i] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""

    print(f"[!] {message}")


def print_error(message: str) -> None:
    """Print an error message to stderr."""

    print(f"[X] {message}", file=sys.stderr)