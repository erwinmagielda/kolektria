"""
Kolektria Markdown reporter.

Builds a human-readable Markdown evidence report from Kolektria scan JSON.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


# ------------------------------------------------------------
# REPORT HELPERS
# ------------------------------------------------------------

def format_value(value: Any, empty_value: str = "Unknown") -> str:
    """Return a readable value for Markdown output."""

    if value is None or value == "":
        return empty_value

    return str(value)


def format_identifier(value: Any, empty_value: str = "None") -> str:
    """Return a Markdown inline-code identifier."""

    if value is None or value == "":
        return empty_value

    return f"`{value}`"


def format_identifier_list(values: list[str], empty_value: str = "None") -> str:
    """Return a comma-separated Markdown inline-code identifier list."""

    if not values:
        return empty_value

    return ", ".join(f"`{value}`" for value in values)


def format_month_list(values: list[str], empty_value: str = "None") -> str:
    """Return a comma-separated Markdown inline-code MonthId list."""

    return format_identifier_list(values, empty_value=empty_value)


def get_expected_kbs(kb_entries: list[dict[str, Any]]) -> list[str]:
    """Return sorted KBs expected from the advisory map."""

    return sorted(
        {
            entry.get("KB")
            for entry in kb_entries
            if entry.get("KB")
        }
    )


def get_missing_entries(
    kb_entries: list[dict[str, Any]],
    missing_kbs: list[str],
) -> list[dict[str, Any]]:
    """Return KB advisory entries matching missing KBs."""

    missing_set = set(missing_kbs)

    return [
        entry
        for entry in kb_entries
        if entry.get("KB") in missing_set
    ]


def get_superseded_kbs(kb_entries: list[dict[str, Any]]) -> list[str]:
    """Return sorted KBs referenced as superseded by advisory entries."""

    superseded_kbs: set[str] = set()

    for entry in kb_entries:
        for superseded_kb in entry.get("Supersedes") or []:
            superseded_kbs.add(superseded_kb)

    return sorted(superseded_kbs)


# ------------------------------------------------------------
# TABLE BUILDING
# ------------------------------------------------------------

def build_scan_outcome_table(
    generated_at: str,
    baseline: dict[str, Any],
    months_requested: list[str],
    missing_kbs: list[str],
) -> list[str]:
    """Build the scan outcome table with fields as columns."""

    return [
        "| Date Generated | Operating System | Months Requested | Missing KBs |",
        "|:---|:---|:---|:---|",
        (
            f"| {generated_at} "
            f"| {format_value(baseline.get('OsName'))} "
            f"| {format_month_list(months_requested)} "
            f"| {len(missing_kbs)} |"
        ),
    ]


def build_kb_state_table(
    kb_entries: list[dict[str, Any]],
    installed_kbs: list[str],
    missing_kbs: list[str],
) -> list[str]:
    """Build a KB state table with counts, KBs, and explanations."""

    expected_kbs = get_expected_kbs(kb_entries)
    superseded_kbs = get_superseded_kbs(kb_entries)

    rows = [
        (
            "Expected",
            len(expected_kbs),
            format_identifier_list(expected_kbs),
            "KBs identified from MSRC advisory mappings for the requested product and month range.",
        ),
        (
            "Installed",
            len(installed_kbs),
            format_identifier_list(installed_kbs),
            "KBs detected directly from the local Windows update inventory.",
        ),
        (
            "Superseded",
            len(superseded_kbs),
            format_identifier_list(superseded_kbs),
            "Older KBs referenced as superseded by advisory entries.",
        ),
        (
            "Missing",
            len(missing_kbs),
            format_identifier_list(missing_kbs, "None"),
            "Expected KBs not found directly and not covered by the supersedence calculation.",
        ),
    ]

    lines = [
        "| KB State | Count | KBs | Explanation |",
        "|:---|:---|:---|:---|",
    ]

    for state, count, kbs, explanation in rows:
        lines.append(f"| {state} | {count} | {kbs} | {explanation} |")

    return lines


def build_missing_kb_summary_table(entry: dict[str, Any]) -> list[str]:
    """Build a compact one-row table for one missing KB."""

    kb_id = format_identifier(entry.get("KB"))
    months = format_month_list(entry.get("Months") or [])
    cves = entry.get("Cves") or []
    supersedes = format_identifier_list(entry.get("Supersedes") or [])
    update_type = format_value(entry.get("UpdateType"))

    return [
        "| KB | Status | Months | CVE Count | Supersedes | Update Type |",
        "|:---|:---|:---|:---|:---|:---|",
        f"| {kb_id} | Missing | {months} | {len(cves)} | {supersedes} | {update_type} |",
    ]


def build_baseline_evidence_table(baseline: dict[str, Any]) -> list[str]:
    """Build the baseline evidence table."""

    rows = [
        ("OS Name", format_value(baseline.get("OsName"))),
        ("OS Edition", format_value(baseline.get("OsEdition"))),
        ("Display Version", format_value(baseline.get("DisplayVersion"))),
        ("Build", format_value(baseline.get("Build"))),
        ("Architecture", format_value(baseline.get("Architecture"))),
        ("LCU MonthId", format_identifier(baseline.get("LcuMonthId"))),
        ("LCU Install Month", format_identifier(baseline.get("LcuInstallMonth"))),
        ("Patch Age Days", format_value(baseline.get("PatchAgeDays"))),
        ("MSRC Latest MonthId", format_identifier(baseline.get("MsrcLatestMonthId"))),
        ("Resolved Product MonthId", format_identifier(baseline.get("ResolvedProductMonthId"))),
        ("Product Hint", format_value(baseline.get("ProductNameHint"))),
    ]

    lines = [
        "| Field | Value |",
        "|:---|:---|",
    ]

    for field, value in rows:
        lines.append(f"| {field} | {value} |")

    return lines


# ------------------------------------------------------------
# REPORT SECTIONS
# ------------------------------------------------------------

def build_scan_outcome_section(
    generated_at: str,
    baseline: dict[str, Any],
    months_requested: list[str],
    missing_kbs: list[str],
) -> list[str]:
    """Build the scan outcome section."""

    lines = [
        "# Kolektria Scan Report",
        "",
        "Kolektria is a Windows patch-state collector for authorised hosts. It gathers update, KB, MSRC, and supersedence evidence, then exports structured JSON and a readable Markdown report for downstream Remetria analysis.",
        "",
        "## Scan Outcome",
        "",
        "High-level result from this collection run.",
        "",
    ]

    lines.extend(
        build_scan_outcome_table(
            generated_at=generated_at,
            baseline=baseline,
            months_requested=months_requested,
            missing_kbs=missing_kbs,
        )
    )

    lines.append("")

    return lines


def build_missing_update_state_section(
    kb_entries: list[dict[str, Any]],
    installed_kbs: list[str],
    missing_kbs: list[str],
) -> list[str]:
    """Build the missing update state section."""

    lines = [
        "## Missing Update State",
        "",
        "Breakdown of the KB sets used to decide whether expected updates are installed, superseded, or missing.",
        "",
    ]

    lines.extend(
        build_kb_state_table(
            kb_entries=kb_entries,
            installed_kbs=installed_kbs,
            missing_kbs=missing_kbs,
        )
    )

    lines.append("")

    return lines


def build_missing_kb_evidence_section(
    kb_entries: list[dict[str, Any]],
    missing_kbs: list[str],
) -> list[str]:
    """Build the missing KB evidence section."""

    lines = [
        "## Missing KB Evidence",
        "",
        "Each missing KB is shown as a separate evidence block. CVEs are listed outside the table so long advisory mappings stay readable.",
        "",
    ]

    missing_entries = get_missing_entries(
        kb_entries=kb_entries,
        missing_kbs=missing_kbs,
    )

    if not missing_entries:
        lines.extend(
            [
                "No missing KB evidence was identified.",
                "",
            ]
        )

        return lines

    for index, entry in enumerate(missing_entries, start=1):
        kb_id = format_identifier(entry.get("KB"))
        cves = entry.get("Cves") or []

        lines.extend(
            [
                f"### {index}. {kb_id}",
                "",
            ]
        )

        lines.extend(build_missing_kb_summary_table(entry))

        lines.extend(
            [
                "",
                "**Mapped CVEs:**",
                "",
                format_identifier_list(cves),
                "",
            ]
        )

    return lines


def build_baseline_evidence_section(baseline: dict[str, Any]) -> list[str]:
    """Build the baseline evidence section."""

    lines = [
        "## Baseline Evidence",
        "",
        "Non-identifying Windows update-state fields used to resolve the MSRC product context.",
        "",
    ]

    lines.extend(build_baseline_evidence_table(baseline))
    lines.append("")

    return lines


def build_method_section() -> list[str]:
    """Build the method and scope section."""

    return [
        "## Method",
        "",
        "Kolektria collects Windows update-state evidence, installed KB inventory, MSRC advisory mappings, and supersedence relationships. Missing KBs are calculated by comparing expected advisory KBs against installed KBs after expanding logical presence through supersedence evidence.",
        "",
        "## Scope Notes",
        "",
        "The report is generated from authorised local host evidence and is intended for downstream Remetria analysis.",
        "",
        "Kolektria does not collect hostname, username, device name, serial number, IP address, MAC address, domain, local file paths, installed applications, or user activity. The scan is limited to Windows update-state and MSRC advisory-mapping evidence.",
        "",
    ]


# ------------------------------------------------------------
# REPORT BUILDING
# ------------------------------------------------------------

def build_markdown_report(scan_result: dict[str, Any]) -> str:
    """Build a structured Markdown report from a Kolektria scan result."""

    baseline = scan_result.get("Baseline") or {}
    installed_kbs = scan_result.get("InstalledKbs") or []
    months_requested = scan_result.get("MonthsRequested") or []
    kb_entries = scan_result.get("KbEntries") or []
    missing_kbs = scan_result.get("MissingKbs") or []

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []

    lines.extend(
        build_scan_outcome_section(
            generated_at=generated_at,
            baseline=baseline,
            months_requested=months_requested,
            missing_kbs=missing_kbs,
        )
    )

    lines.extend(
        build_missing_update_state_section(
            kb_entries=kb_entries,
            installed_kbs=installed_kbs,
            missing_kbs=missing_kbs,
        )
    )

    lines.extend(
        build_missing_kb_evidence_section(
            kb_entries=kb_entries,
            missing_kbs=missing_kbs,
        )
    )

    lines.extend(build_baseline_evidence_section(baseline=baseline))
    lines.extend(build_method_section())

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