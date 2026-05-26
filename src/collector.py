"""
Kolektria collector.

Portable Windows patch-state collector for authorised hosts.

Runtime behaviour:
    data/runtime   = latest scan workspace
    data/collected = persistent scan archive

Output purpose:
    Produces structured JSON for downstream Remetria analysis.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from utils.console import (
    print_banner,
    print_error,
    print_info,
    print_step,
    print_success,
    print_warning,
)
from utils.paths import (
    ADAPTER_SCRIPT_PATH,
    BASELINE_SCRIPT_PATH,
    COLLECTED_DIR,
    INVENTORY_SCRIPT_PATH,
    RUNTIME_DIR,
    ensure_data_directories,
    ensure_required_files,
    relative_path,
)
from utils.runner import run_powershell_script


# ------------------------------------------------------------
# RUNTIME CLEANUP
# ------------------------------------------------------------

def clear_runtime_directory() -> None:
    """
    Clear generated files from data/runtime.

    The .gitkeep placeholder is preserved so the folder remains tracked in Git.
    """

    ensure_data_directories()

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
        print_warning("LCU month is newer than latest MSRC month. Using latest MSRC month only.")
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
# SCAN COLLECTION
# ------------------------------------------------------------

def collect_scan(max_months: int = 48) -> dict[str, Any]:
    """Run the Kolektria collection workflow and return scan JSON."""

    print_step("Collecting Windows baseline context")
    baseline = run_powershell_script(BASELINE_SCRIPT_PATH)

    product_name_hint = baseline.get("ProductNameHint")

    if not product_name_hint:
        raise RuntimeError("ProductNameHint could not be resolved")

    print_success("Baseline context collected")
    print_info(f"OS: {baseline.get('OsName', 'Unknown')}")
    print_info(f"Build: {baseline.get('Build', 'Unknown')}")
    print_info(f"Product hint: {product_name_hint}")

    print_step("Collecting installed KB inventory")
    inventory = run_powershell_script(INVENTORY_SCRIPT_PATH)
    installed_kbs = set(inventory.get("AllInstalledKbs") or [])

    print_success(f"Installed KB inventory collected: {len(installed_kbs)} KBs")

    print_step("Building MSRC MonthId range from LCU context")
    month_ids = build_month_ids_from_lcu(
        baseline=baseline,
        max_months=max_months,
    )

    print_success(f"Month range built: {len(month_ids)} month(s)")
    print_info(f"Months requested: {', '.join(month_ids)}")

    merged_entries: dict[str, dict[str, Any]] = {}
    months_with_entries: list[str] = []

    print_step("Querying MSRC advisory data")

    for month_chunk in chunk_list(month_ids, 3):
        chunk_text = ", ".join(month_chunk)
        print_info(f"Processing MonthId chunk: {chunk_text}")

        msrc_data = run_powershell_script(
            ADAPTER_SCRIPT_PATH,
            extra_args=[
                "-MonthIds",
                ",".join(month_chunk),
                "-ProductNameHint",
                product_name_hint,
            ],
        )

        entries = msrc_data.get("KbEntries") or []
        adapter_months = msrc_data.get("MonthsWithProductRows") or []

        if entries:
            merge_kb_entries(merged_entries, entries)
            months_with_entries.extend(adapter_months or month_chunk)

        print_info(f"KB entries returned: {len(entries)}")

    kb_entries = normalise_kb_entries(list(merged_entries.values()))

    print_success(f"MSRC advisory mapping collected: {len(kb_entries)} KB entries")

    print_step("Calculating supersedence and missing KBs")

    logical_present_kbs, superseded_by = compute_supersedence(
        kb_entries=kb_entries,
        installed_kbs=installed_kbs,
    )

    expected_kbs = {
        entry["KB"]
        for entry in kb_entries
        if entry.get("KB")
    }

    missing_kbs = sorted(expected_kbs - logical_present_kbs)

    print_info(f"Expected KBs from advisory map: {len(expected_kbs)}")
    print_info(f"Installed or superseded KBs: {len(logical_present_kbs)}")
    print_info(f"Supersedence relationships resolved: {len(superseded_by)}")
    print_success(f"Missing KBs identified: {len(missing_kbs)}")

    return {
        "Baseline": baseline,
        "InstalledKbs": sorted(installed_kbs),
        "MonthsRequested": month_ids,
        "MonthsWithEntries": sorted(set(months_with_entries)),
        "KbEntries": kb_entries,
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
        print_banner()

        print_step("Validating required collector files")
        ensure_required_files()
        print_success("Required collector files found")

        print_step("Preparing runtime workspace")
        clear_runtime_directory()
        print_success(f"Runtime workspace ready: {relative_path(RUNTIME_DIR)}")

        scan_result = collect_scan(max_months=args.max_months)

        print_step("Writing scan JSON")
        runtime_scan_path = export_runtime_scan(scan_result)
        collected_scan_path = COLLECTED_DIR / runtime_scan_path.name

        print_success(f"Runtime scan saved: {relative_path(runtime_scan_path)}")
        print_success(f"Archived scan saved: {relative_path(collected_scan_path)}")
        print_success("Kolektria collection completed")

        return 0

    except Exception as exc:
        print_error(f"Collector failed: {exc}")
        return 1


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())