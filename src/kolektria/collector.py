"""
Kolektria collector.

Portable Windows patch-state collector for authorised hosts.

Runtime behaviour:
    data/runtime    = latest scan workspace
    data/collected  = persistent scan archive
    results/reports = generated Markdown reports

Output purpose:
    Produces structured JSON and Markdown evidence reports for downstream Remetria analysis.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kolektria.cleaner import clear_generated_artefacts
from kolektria.reporter import export_markdown_report
from utils.console import (
    print_banner,
    print_detail,
    print_error,
    print_info,
    print_menu_title,
    print_result,
    print_section,
    print_step,
    print_success,
    print_warning,
    prompt_main_menu,
)
from utils.dependencies import (
    MSRC_MODULE_NAME,
    install_msrc_module,
    is_msrc_module_available,
)
from utils.paths import (
    ADAPTER_SCRIPT_PATH,
    BASELINE_SCRIPT_PATH,
    COLLECTED_DIR,
    INVENTORY_SCRIPT_PATH,
    POWERSHELL_DIR,
    REPORTS_DIR,
    RUNTIME_DIR,
    ensure_output_directories,
    ensure_required_files,
    relative_path,
)
from utils.runner import run_powershell_script


# ------------------------------------------------------------
# DISPLAY HELPERS
# ------------------------------------------------------------

def format_months(month_ids: list[str]) -> str:
    """Return a readable MonthId list."""

    if not month_ids:
        return "None"

    return ", ".join(month_ids)


# ------------------------------------------------------------
# RUNTIME CLEANUP
# ------------------------------------------------------------

def clear_runtime_directory() -> None:
    """
    Clear generated files from data/runtime.

    The .gitkeep placeholder is preserved so the folder remains tracked in Git.
    """

    ensure_output_directories()

    for item in RUNTIME_DIR.iterdir():
        if item.name == ".gitkeep":
            continue

        if item.is_dir():
            shutil.rmtree(item)
            continue

        item.unlink()


# ------------------------------------------------------------
# MONTH RANGE HANDLING
# ------------------------------------------------------------

def parse_month_id(month_id: str) -> datetime:
    """Parse an MSRC MonthId value into a UTC datetime."""

    try:
        return datetime.strptime(month_id, "%Y-%b").replace(day=1, tzinfo=UTC)
    except ValueError as exc:
        raise RuntimeError(f"Invalid MonthId value: {month_id}") from exc


def build_month_ids_from_lcu(
    baseline: dict[str, Any],
    max_months: int = 48,
) -> list[str]:
    """Build a MonthId range from installed LCU month to latest MSRC month."""

    if not baseline.get("IsAdmin"):
        raise RuntimeError("Baseline was collected without administrative privileges")

    start_id = baseline.get("LcuMonthId")
    end_id = baseline.get("MsrcLatestMonthId")

    if not start_id:
        raise RuntimeError("Baseline did not provide LcuMonthId")

    start_date = parse_month_id(str(start_id))

    if end_id:
        end_date = parse_month_id(str(end_id))
    else:
        end_date = datetime.now(UTC).replace(day=1)

    if start_date > end_date:
        print_warning("LCU month is newer than latest MSRC month. Using latest MSRC month only")
        start_date = end_date

    month_ids: list[str] = []
    year = start_date.year
    month = start_date.month

    while True:
        current_date = datetime(year, month, 1, tzinfo=UTC)

        if current_date > end_date:
            break

        if len(month_ids) >= max_months:
            print_warning(f"Month range reached max-months limit: {max_months}")
            break

        month_ids.append(current_date.strftime("%Y-%b"))

        if current_date == end_date:
            break

        month += 1

        if month == 13:
            month = 1
            year += 1

    if not month_ids:
        raise RuntimeError("No MSRC MonthIds were generated from baseline context")

    return month_ids


def chunk_list(items: list[str], size: int) -> list[list[str]]:
    """Split a list into fixed-size chunks."""

    return [items[index:index + size] for index in range(0, len(items), size)]


# ------------------------------------------------------------
# KB ENTRY MERGING
# ------------------------------------------------------------

def merge_kb_entries(
    existing: dict[str, dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> None:
    """Merge MSRC adapter KB entries into an indexed KB map."""

    for entry in incoming:
        kb_id = entry.get("KB")

        if not kb_id:
            continue

        target = existing.setdefault(
            kb_id,
            {
                "KB": kb_id,
                "Months": [],
                "Cves": [],
                "Supersedes": [],
            },
        )

        for field in ("Months", "Cves", "Supersedes"):
            for value in entry.get(field) or []:
                if value and value not in target[field]:
                    target[field].append(value)


def normalise_kb_entries(kb_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort and normalise merged KB entries."""

    normalised_entries: list[dict[str, Any]] = []

    for entry in kb_entries:
        months = sorted(set(entry.get("Months") or []))
        cves = sorted(set(entry.get("Cves") or []))
        supersedes = sorted(set(entry.get("Supersedes") or []))

        normalised_entries.append(
            {
                "KB": entry["KB"],
                "Months": months,
                "Cves": cves,
                "Supersedes": supersedes,
                "UpdateType": "Superseding" if supersedes else "Standalone",
            }
        )

    return sorted(normalised_entries, key=lambda item: item["KB"])


# ------------------------------------------------------------
# SUPERSEDENCE RESOLUTION
# ------------------------------------------------------------

def compute_supersedence(
    kb_entries: list[dict[str, Any]],
    installed_kbs: set[str],
) -> tuple[set[str], dict[str, list[str]]]:
    """Expand logical KB presence using supersedence relationships."""

    supersedes_map: dict[str, set[str]] = {}

    for entry in kb_entries:
        kb_id = entry.get("KB")

        if not kb_id:
            continue

        for superseded_kb in entry.get("Supersedes") or []:
            supersedes_map.setdefault(kb_id, set()).add(superseded_kb)

    logical_present_kbs = set(installed_kbs)
    superseded_by: dict[str, set[str]] = {}

    for root_kb in installed_kbs:
        stack = [root_kb]
        seen = {root_kb}

        while stack:
            current_kb = stack.pop()

            for superseded_kb in supersedes_map.get(current_kb, set()):
                logical_present_kbs.add(superseded_kb)
                superseded_by.setdefault(superseded_kb, set()).add(root_kb)

                if superseded_kb not in seen:
                    seen.add(superseded_kb)
                    stack.append(superseded_kb)

    return logical_present_kbs, {
        kb_id: sorted(replacing_kbs)
        for kb_id, replacing_kbs in superseded_by.items()
    }


# ------------------------------------------------------------
# ENVIRONMENT PREPARATION
# ------------------------------------------------------------

def ensure_msrc_dependency() -> None:
    """Check and install the MSRC PowerShell module when required."""

    print_step("Checking MSRC PowerShell module")

    if is_msrc_module_available():
        print_result("MSRC PowerShell module found")
        print_detail(f"Module: {MSRC_MODULE_NAME}")
        return

    print_warning("MSRC PowerShell module missing")
    print_detail(f"Module: {MSRC_MODULE_NAME}")

    print()
    print_step("Installing MSRC PowerShell module")
    install_msrc_module()
    print_result("MSRC PowerShell module installed")
    print_detail("Scope: CurrentUser")


def prepare_environment() -> None:
    """Validate files, dependencies, and runtime workspace."""

    print_section("Environment Preparation")

    print_step("Validating collector files")
    ensure_required_files()
    print_result("Collector files found")
    print_detail(f"Path: {relative_path(POWERSHELL_DIR)}")

    print()
    ensure_msrc_dependency()

    print()
    print_step("Preparing runtime workspace")
    clear_runtime_directory()
    print_result("Runtime workspace prepared")
    print_detail(f"Path: {relative_path(RUNTIME_DIR)}")


# ------------------------------------------------------------
# HOST EVIDENCE
# ------------------------------------------------------------

def collect_host_evidence() -> tuple[dict[str, Any], set[str], str]:
    """Collect Windows baseline context and installed KB inventory."""

    print_section("Host Evidence")

    print_step("Collecting Windows baseline context")
    baseline = run_powershell_script(BASELINE_SCRIPT_PATH)

    product_name_hint = baseline.get("ProductNameHint")

    if not product_name_hint:
        raise RuntimeError("ProductNameHint could not be resolved")

    print_result("Windows baseline collected")
    print_detail(f"Product hint: {product_name_hint}")

    print()
    print_step("Collecting installed KB inventory")
    inventory = run_powershell_script(INVENTORY_SCRIPT_PATH)
    installed_kbs = set(inventory.get("AllInstalledKbs") or [])

    print_result("Installed KB inventory collected")
    print_detail(f"Installed KBs: {len(installed_kbs)}")

    return baseline, installed_kbs, str(product_name_hint)


# ------------------------------------------------------------
# MSRC CORRELATION
# ------------------------------------------------------------

def collect_msrc_entries(
    baseline: dict[str, Any],
    product_name_hint: str,
    max_months: int,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Collect and merge MSRC advisory KB entries."""

    print_section("MSRC Correlation")

    print_step("Building MSRC MonthId range")
    month_ids = build_month_ids_from_lcu(
        baseline=baseline,
        max_months=max_months,
    )

    print_result("MSRC MonthId range built")
    print_detail(f"Months requested: {format_months(month_ids)}")

    print()
    print_step("Querying MSRC advisory data")

    merged_entries: dict[str, dict[str, Any]] = {}
    months_with_entries: list[str] = []

    for month_chunk in chunk_list(month_ids, 3):
        chunk_text = ", ".join(month_chunk)
        print_detail(f"Processing MonthId chunk: {chunk_text}")
        print_detail("Timeout: 240 seconds")

        msrc_data = run_powershell_script(
            ADAPTER_SCRIPT_PATH,
            extra_args=[
                "-MonthIds",
                ",".join(month_chunk),
                "-ProductNameHint",
                product_name_hint,
            ],
            timeout_seconds=240,
        )

        entries = msrc_data.get("KbEntries") or []
        adapter_months = msrc_data.get("MonthsWithProductRows") or []

        if entries:
            merge_kb_entries(merged_entries, entries)
            months_with_entries.extend(adapter_months or month_chunk)

        print_detail(f"Chunk KB entries: {len(entries)}")

    kb_entries = normalise_kb_entries(list(merged_entries.values()))

    print_result("MSRC advisory data collected")
    print_detail(f"KB entries collected: {len(kb_entries)}")

    return month_ids, sorted(set(months_with_entries)), kb_entries


# ------------------------------------------------------------
# SUPERSEDENCE ANALYSIS
# ------------------------------------------------------------

def calculate_supersedence_summary(
    kb_entries: list[dict[str, Any]],
    installed_kbs: set[str],
) -> tuple[list[str], dict[str, int]]:
    """Calculate missing KBs and return a supersedence summary."""

    print_section("Supersedence Analysis")

    print_step("Calculating supersedence relationships")
    logical_present_kbs, superseded_by = compute_supersedence(
        kb_entries=kb_entries,
        installed_kbs=installed_kbs,
    )

    print_result("Supersedence relationships calculated")
    print_detail(f"Relationships resolved: {len(superseded_by)}")

    print()
    print_step("Calculating missing update state")

    expected_kbs = {
        entry["KB"]
        for entry in kb_entries
        if entry.get("KB")
    }

    missing_kbs = sorted(expected_kbs - logical_present_kbs)

    supersedence_summary = {
        "ExpectedKbs": len(expected_kbs),
        "InstalledKbs": len(installed_kbs),
        "InstalledOrSupersededKbs": len(logical_present_kbs),
        "RelationshipsResolved": len(superseded_by),
        "MissingKbs": len(missing_kbs),
    }

    print_result("Missing update state calculated")
    print_detail(f"Expected KBs: {supersedence_summary['ExpectedKbs']}")
    print_detail(f"Installed or superseded KBs: {supersedence_summary['InstalledOrSupersededKbs']}")
    print_detail(f"Missing KBs: {supersedence_summary['MissingKbs']}")

    return missing_kbs, supersedence_summary


# ------------------------------------------------------------
# SCAN COLLECTION
# ------------------------------------------------------------

def collect_scan(max_months: int = 48) -> dict[str, Any]:
    """Run the Kolektria collection workflow and return scan JSON."""

    baseline, installed_kbs, product_name_hint = collect_host_evidence()

    month_ids, months_with_entries, kb_entries = collect_msrc_entries(
        baseline=baseline,
        product_name_hint=product_name_hint,
        max_months=max_months,
    )

    missing_kbs, supersedence_summary = calculate_supersedence_summary(
        kb_entries=kb_entries,
        installed_kbs=installed_kbs,
    )

    return {
        "Baseline": baseline,
        "InstalledKbs": sorted(installed_kbs),
        "MonthsRequested": month_ids,
        "MonthsWithEntries": months_with_entries,
        "KbEntries": kb_entries,
        "SupersedenceSummary": supersedence_summary,
        "MissingKbs": missing_kbs,
    }


# ------------------------------------------------------------
# RUNTIME EXPORT
# ------------------------------------------------------------

def export_runtime_scan(scan_result: dict[str, Any]) -> Path:
    """Write runtime scan output and archive a persistent copy."""

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    runtime_scan_path = RUNTIME_DIR / f"scan_{timestamp}.json"
    collected_scan_path = COLLECTED_DIR / runtime_scan_path.name

    with runtime_scan_path.open("w", encoding="utf-8") as file:
        json.dump(scan_result, file, indent=2)

    shutil.copy2(runtime_scan_path, collected_scan_path)

    return runtime_scan_path


def write_scan_output(scan_result: dict[str, Any]) -> None:
    """Write scan output and print generated artefact paths."""

    print_section("Runtime Export")

    print_step("Writing scan JSON")
    runtime_scan_path = export_runtime_scan(scan_result)
    collected_scan_path = COLLECTED_DIR / runtime_scan_path.name

    print_result("Scan JSON written")
    print_detail(f"Runtime JSON: {relative_path(runtime_scan_path)}")
    print_detail(f"Archived JSON: {relative_path(collected_scan_path)}")

    print()
    print_step("Writing Markdown report")
    report_path = REPORTS_DIR / runtime_scan_path.with_suffix(".md").name
    export_markdown_report(scan_result, report_path)

    print_result("Markdown report written")
    print_detail(f"Markdown report: {relative_path(report_path)}")


# ------------------------------------------------------------
# MENU ACTIONS
# ------------------------------------------------------------

def run_scan_action(args: argparse.Namespace) -> None:
    """Run the scan workflow from the interactive menu."""

    prepare_environment()
    scan_result = collect_scan(max_months=args.max_months)
    write_scan_output(scan_result)

    print()
    print_success("Run Scan completed")


def clear_artefacts_action() -> None:
    """Run the artefact cleanup workflow from the interactive menu."""

    clear_generated_artefacts()

    print()
    print_success("Clear Artefacts completed")


def run_menu(args: argparse.Namespace) -> int:
    """Run the Kolektria interactive menu."""

    print_banner()

    while True:
        choice = prompt_main_menu()

        if choice == "1":
            run_scan_action(args)
            print_menu_title()
            continue

        if choice == "2":
            clear_artefacts_action()
            print_menu_title()
            continue

        if choice == "3":
            print_info("Exit selected")
            print()
            return 0

        print_warning("Invalid menu selection")
        print_menu_title()


# ------------------------------------------------------------
# COMMAND LINE
# ------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Collect Windows patch-state data and export Kolektria JSON.",
    )

    parser.add_argument(
        "--max-months",
        type=int,
        default=48,
        help="Maximum number of MSRC months to query from the LCU month onward.",
    )

    return parser.parse_args()


# ------------------------------------------------------------
# MAIN WORKFLOW
# ------------------------------------------------------------

def main() -> int:
    """Run the Kolektria collector workflow."""

    args = parse_args()

    try:
        return run_menu(args)

    except KeyboardInterrupt:
        print()
        print_info("Exit selected")
        print()
        return 0

    except Exception as exc:
        print_error(f"Collector failed: {exc}")
        print()
        return 1


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())