"""
Kolektria console output helpers.

Keeps scanner output consistent across the launcher and Python workflow.
"""

from __future__ import annotations

import os
import sys


# ------------------------------------------------------------
# COLOUR SETTINGS
# ------------------------------------------------------------

USE_COLOUR = os.getenv("NO_COLOR") is None

RESET = "\033[0m"
BOLD = "\033[1m"

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"


def colour(text: str, code: str) -> str:
    """Return coloured text when terminal colour is enabled."""

    if not USE_COLOUR:
        return text

    return f"{code}{text}{RESET}"


# ------------------------------------------------------------
# BANNER
# ------------------------------------------------------------

def print_banner() -> None:
    """Print the Kolektria banner."""

    print()
    print(colour("============================================================", CYAN))
    print(colour(" Kolektria", BOLD))
    print(" Windows Patch-State Collector")
    print(colour("============================================================", CYAN))
    print()


# ------------------------------------------------------------
# STATUS LINES
# ------------------------------------------------------------

def print_step(message: str) -> None:
    """Print an active workflow step."""

    print(f"{colour('[*]', BLUE)} {message}")


def print_success(message: str) -> None:
    """Print a successful workflow step."""

    print(f"{colour('[+]', GREEN)} {message}")


def print_info(message: str) -> None:
    """Print an informational message."""

    print(f"{colour('[i]', CYAN)} {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""

    print(f"{colour('[!]', YELLOW)} {message}")


def print_error(message: str) -> None:
    """Print an error message to stderr."""

    print(f"{colour('[X]', RED)} {message}", file=sys.stderr)