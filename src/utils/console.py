"""
Kolektria console output helpers.

Keeps scanner output consistent across the launcher and Python workflow.
"""

from __future__ import annotations

import sys


# ------------------------------------------------------------
# BANNER
# ------------------------------------------------------------

KOLEKTRIA_LOGO = r"""
 /██   /██  /██████  /██       /████████ /██   /██ /████████ /███████  /██████  /██████ 
| ██  /██/ /██__  ██| ██      | ██_____/| ██  /██/|__  ██__/| ██__  ██|_  ██_/ /██__  ██
| ██ /██/ | ██  \ ██| ██      | ██      | ██ /██/    | ██   | ██  \ ██  | ██  | ██  \ ██
| █████/  | ██  | ██| ██      | █████   | █████/     | ██   | ███████/  | ██  | ████████
| ██  ██  | ██  | ██| ██      | ██__/   | ██  ██     | ██   | ██__  ██  | ██  | ██__  ██
| ██\  ██ | ██  | ██| ██      | ██      | ██\  ██    | ██   | ██  \ ██  | ██  | ██  | ██
| ██ \  ██|  ██████/| ████████| ████████| ██ \  ██   | ██   | ██  | ██ /██████| ██  | ██
|__/  \__/ \______/ |________/|________/|__/  \__/   |__/   |__/  |__/|______/|__/  |__/
"""


def print_banner() -> None:
    """Print the Kolektria startup banner."""

    print()
    print("============================================================")
    print()
    print(KOLEKTRIA_LOGO.rstrip())
    print("Kolektria")
    print()
    print("============================================================")
    print()


# ------------------------------------------------------------
# SECTION HEADERS
# ------------------------------------------------------------

def print_section(title: str) -> None:
    """Print an internal workflow section header."""

    print()
    print(title)
    print("-" * len(title))


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