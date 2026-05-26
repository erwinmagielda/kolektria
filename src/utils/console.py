"""
Kolektria console output helpers.

Keeps scanner output consistent across the launcher and Python workflow.
"""

from __future__ import annotations

import msvcrt
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
    print(KOLEKTRIA_LOGO.rstrip())
    print()
    print("Windows Patch-State Collector")
    print()


# ------------------------------------------------------------
# PROMPTS
# ------------------------------------------------------------

def confirm_scan() -> bool:
    """Ask the user whether to run a collection scan using one key press."""

    print("Run collection scan? [Y/n]: ", end="", flush=True)

    key = msvcrt.getwch().strip().lower()

    if key in ("", "\r", "\n", "y"):
        print("Y")
        print()
        return True

    if key == "n":
        print("n")
        print()
        return False

    print(key)
    print()
    print_warning("Invalid selection, defaulting to scan")
    return True


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