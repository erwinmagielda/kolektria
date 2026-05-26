"""
Kolektria Markdown reporter.

Builds a human-readable Markdown report from Kolektria scan JSON.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


# ------------------------------------------------------------
# REPORT HELPERS
# ------------------------------------------------------------

def format_list(values: list[str], empty_value: str = "None") -> str:
    """Return a comma-separated list or a fallback value."""

    if not values:
        return empty_value

    return ", ".join(values)


def format_value(value: Any, empty_value: str = "Unknown") -> str:
    """Return a readable value for Markdown output."""

    if value is None or value == "":
        return empty_value

    return str(value)


# ------------------------------------------------------------
# TABLE BUILDING
# ------------------------------------------------------------

def build_kb_table(
    kb_entries: list[dict[str, Any]],
    missing_kbs: list[str],
) -> list[str]:
    """Build a Markdown table for KB advisory entries."""

    missing_set = set(missing_kbs)

    lines = [
        "| KB | Status | Months | CVEs | Supersedes | Update type |",
        "|---|---|---|---:|---|---|",
    ]

    for entry in kb_entries:
        kb_id = format_value(entry.get("KB"))
        status = "Missing" if kb_id in missing_set else "Present or superseded"
        months = format_list(entry.get("Months") or [])
        cve_count = len(entry.get("Cves") or [])
        supersedes = format_list(entry.get("Supersedes") or [])
        update_type = format_value(entry.get("UpdateType"))

        lines.append(
            f"| {kb_id} | {status} | {months} | {cve_count} | {supersedes} | {update_type} |"
        )

    return lines


# ------------------------------------------------------------
# REPORT BUILDING
# ------------------------------------------------------------

def build_markdown_report(scan_result: dict[str, Any]) -> str:
    """Build a structured Markdown report from a Kolektria scan result."""

    baseline = scan_result.get("Baseline") or {}
    installed_kbs = scan_result.get("InstalledKbs") or []
    months_requested = scan_result.get("MonthsRequested") or []
    months_with_entries = scan_result.get("MonthsWithEntries") or []
    kb_entries = scan_result.get("KbEntries") or []
    missing_kbs = scan_result.get("MissingKbs") or []

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# Kolektria Scan Report",
        "",
        "## Summary",
        "",
        f"- Generated: {generated_at}",
        f"- OS: {format_value(baseline.get('OsName'))}",
        f"- Build: {format_value(baseline.get('Build'))}",
        f"- Architecture: {format_value(baseline.get('Architecture'))}",
        f"- Product hint: {format_value(baseline.get('ProductNameHint'))}",
        f"- Installed KBs collected: {len(installed_kbs)}",
        f"- MSRC months requested: {len(months_requested)}",
        f"- MSRC months with entries: {len(months_with_entries)}",
        f"- KB advisory entries: {len(kb_entries)}",
        f"- Missing KBs identified: {len(missing_kbs)}",
        "",
        "## Baseline",
        "",
        f"- OS name: {format_value(baseline.get('OsName'))}",
        f"- OS edition: {format_value(baseline.get('OsEdition'))}",
        f"- Display version: {format_value(baseline.get('DisplayVersion'))}",
        f"- Build: {format_value(baseline.get('Build'))}",
        f"- Architecture: {format_value(baseline.get('Architecture'))}",
        f"- Administrator context: {format_value(baseline.get('IsAdmin'))}",
        f"- LCU MonthId: {format_value(baseline.get('LcuMonthId'))}",
        f"- LCU package name: {format_value(baseline.get('LcuPackageName'))}",
        f"- LCU install time: {format_value(baseline.get('LcuInstallTime'))}",
        f"- MSRC latest MonthId: {format_value(baseline.get('MsrcLatestMonthId'))}",
        f"- Resolved product MonthId: {format_value(baseline.get('ResolvedProductMonthId'))}",
        f"- Product hint: {format_value(baseline.get('ProductNameHint'))}",
        "",
        "## Installed KB Inventory",
        "",
        format_list(installed_kbs, "No installed KBs collected"),
        "",
        "## MSRC Correlation",
        "",
        f"- Months requested: {format_list(months_requested)}",
        f"- Months with product rows: {format_list(months_with_entries)}",
        "",
        "## Missing KBs",
        "",
        format_list(missing_kbs, "No missing KBs identified"),
        "",
        "## KB Advisory Map",
        "",
    ]

    lines.extend(build_kb_table(kb_entries, missing_kbs))

    lines.extend(
        [
            "",
            "## Method",
            "",
            "Kolektria collects Windows baseline context, installed KB inventory, MSRC advisory mappings, and supersedence relationships. Missing KBs are calculated after expanding installed KB presence through supersedence evidence.",
            "",
            "## Notes",
            "",
            "This report is generated from local authorised host evidence and is intended for downstream Remetria analysis.",
            "",
        ]
    )

    return "\n".join(lines)


# ------------------------------------------------------------
# REPORT EXPORT
# ------------------------------------------------------------

def export_markdown_report(scan_result: dict[str, Any], report_path: Path) -> Path:
    """Write a Markdown report to disk."""

    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_content = build_markdown_report(scan_result)

    with report_path.open("w", encoding="utf-8") as file:
        file.write(report_content)

    return report_path