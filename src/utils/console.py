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


def get_logo_width() -> int:
    """Return the maximum printable logo line width."""

    return max(len(line.rstrip()) for line in KOLEKTRIA_LOGO.splitlines() if line.strip())


def print_banner() -> None:
    """Print the Kolektria startup banner."""

    print()
    print(KOLEKTRIA_LOGO.rstrip())
    print()
    print("Windows Patch-State Collector")
    print()
    print("=" * get_logo_width())
    print()


# ------------------------------------------------------------
# PROMPTS
# ------------------------------------------------------------

def clear_pending_keys() -> None:
    """Clear buffered key presses after a single-key prompt."""

    while msvcrt.kbhit():
        msvcrt.getwch()


def confirm_scan() -> bool:
    """Ask the user whether to run a collection scan using one key press."""

    print("Run collection scan? [Y/n]: ", end="", flush=True)

    key = msvcrt.getwch().strip().lower()
    clear_pending_keys()

    if key in ("", "\r", "\n", "y"):
        print("Y")
        return True

    if key == "n":
        print("n")
        return False

    print(key)
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
    """Print a primary workflow action."""

    print(f"[*] {message}")


def print_result(message: str) -> None:
    """Print an indented workflow result."""

    print(f"    [+] {message}")


def print_detail(message: str) -> None:
    """Print an indented workflow detail."""

    print(f"    [i] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""

    print(f"[!] {message}")


def print_error(message: str) -> None:
    """Print an error message to stderr."""

    print(f"[X] {message}", file=sys.stderr)


def print_info(message: str) -> None:
    """Print a standalone informational message."""

    print(f"[i] {message}")


def print_success(message: str) -> None:
    """Print a standalone success message."""

    print(f"[+] {message}")