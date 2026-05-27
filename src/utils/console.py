"""
Kolektria console output helpers.

Keeps scanner output consistent across the launcher and Python workflow.
"""

from __future__ import annotations

import ctypes
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


def print_menu_title() -> None:
    """Print the compact menu title used after actions complete."""

    print()
    print("Kolektria")
    print("-" * len("Kolektria"))


# ------------------------------------------------------------
# CONSOLE MODE
# ------------------------------------------------------------

def disable_quick_edit_mode() -> None:
    """
    Disable QuickEdit mode for the current Windows console.

    QuickEdit can pause console applications when text is selected.
    This is best-effort and only applies to classic Windows console hosts.
    """

    if sys.platform != "win32":
        return

    kernel32 = ctypes.windll.kernel32
    std_input_handle = kernel32.GetStdHandle(-10)

    if std_input_handle == -1:
        return

    mode = ctypes.c_uint()

    if not kernel32.GetConsoleMode(std_input_handle, ctypes.byref(mode)):
        return

    enable_quick_edit_mode = 0x0040
    enable_extended_flags = 0x0080

    new_mode = mode.value
    new_mode &= ~enable_quick_edit_mode
    new_mode |= enable_extended_flags

    kernel32.SetConsoleMode(std_input_handle, new_mode)


# ------------------------------------------------------------
# PROMPTS
# ------------------------------------------------------------

def clear_pending_keys() -> None:
    """Clear buffered key presses after a single-key prompt."""

    while msvcrt.kbhit():
        msvcrt.getwch()


def prompt_main_menu() -> str:
    """Print the main menu and return a single-key selection."""

    print("1. Run Scan")
    print("2. Clear Artefacts")
    print("3. Exit")
    print()
    print("Select option [1-3]: ", end="", flush=True)

    key = msvcrt.getwch().strip().lower()
    clear_pending_keys()

    print(key)
    return key


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