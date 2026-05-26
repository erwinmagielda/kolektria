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


# ------------------------------------------------------------
# TABLE BUILDING
# ------------------------------------------------------------

def build_key_value_table(rows: list[tuple[str, Any]]) -> list[str]:
    """Build a two-column Markdown key-value table."""

    lines = [
        "| Field | Value |",
        "|---|---|",
    ]

    for field, value in rows:
        lines.append(f"| {field} | {format_value(value)} |")

    return lines


def build_metric_table(rows: list[tuple[str, Any]]) -> list[str]:
    """Build a two-column Markdown metric table."""

    lines = [
        "| Metric | Value |",
        "|---|---:|",
    ]

    for metric, value in rows:
        lines.append(f"| {metric} | {format_value(value, '0')} |")

    return lines


def build_missing_kb_table(
    kb_entries: list[dict[str, Any]],
    missing_kbs: list[str],
) -> list[str]:
    """Build a Markdown table for missing KB evidence and related CVEs."""

    lines = [
        "| KB | Months | CVE count | CVEs | Supersedes |",
        "|---|---|---:|---|---|",
    ]

    missing_entries = get_missing_entries(
        kb_entries=kb_entries,
        missing_kbs=missing_kbs,
    )

    if not missing_entries:
        lines.append("| None | None | 0 | None | None |")
        return lines

    for entry in missing_entries:
        kb_id = format_value(entry.get("KB"))
        months = format_list(entry.get("Months") or [])
        cves = entry.get("Cves") or []
        cve_count = len(cves)
        cve_list = format_list(cves)
        supersedes = format_list(entry.get("Supersedes") or [])

        lines.append(
            f"| {kb_id} | {months} | {cve_count} | {cve_list} | {supersedes} |"
        )

    return lines


def build_advisory_table(
    kb_entries: list[dict[str, Any]],
    missing_kbs: list[str],
) -> list[str]:
    """Build a compact Markdown table for all KB advisory entries."""

    missing_set = set(missing_kbs)

    lines = [
        "| KB | Status | Months | CVE count | Supersedes | Update type |",
        "|---|---|---|---:|---|---|",
    ]

    if not kb_entries:
        lines.append("| None | None | None | 0 | None | None |")
        return lines

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
# REPORT SECTIONS
# ------------------------------------------------------------

def build_scan_outcome_section(
    generated_at: str,
    baseline: dict[str, Any],
    months_requested: list[str],
    kb_entries: list[dict[str, Any]],
    supersedence_summary: dict[str, Any],
) -> list[str]:
    """Build the scan outcome section."""

    return [
        "# Kolektria Scan Report",
        "",
        "## Scan Outcome",
        "",
        *build_key_value_table(
            [
                ("Generated", generated_at),
                ("Product hint", baseline.get("ProductNameHint")),
                ("LCU MonthId", baseline.get("LcuMonthId")),
                ("MSRC latest MonthId", baseline.get("MsrcLatestMonthId")),
                ("Months requested", format_list(months_requested)),
                ("Advisory KB entries", len(kb_entries)),
                ("Missing KBs", supersedence_summary.get("MissingKbs")),
            ]
        ),
    ]


def build_missing_state_section(
    kb_entries: list[dict[str, Any]],
    missing_kbs: list[str],
    supersedence_summary: dict[str, Any],
) -> list[str]:
    """Build missing update state and missing KB evidence sections."""

    lines = [
        "",
        "## Missing Update State",
        "",
    ]

    lines.extend(
        build_metric_table(
            [
                ("Expected KBs", supersedence_summary.get("ExpectedKbs")),
                ("Installed KBs", supersedence_summary.get("InstalledKbs")),
                ("Installed or superseded KBs", supersedence_summary.get("InstalledOrSupersededKbs")),
                ("Supersedence relationships", supersedence_summary.get("RelationshipsResolved")),
                ("Missing KBs", supersedence_summary.get("MissingKbs")),
            ]
        )
    )

    lines.extend(
        [
            "",
            "## Missing KB Evidence",
            "",
        ]
    )

    lines.extend(build_missing_kb_table(kb_entries, missing_kbs))

    return lines


def build_advisory_evidence_section(
    kb_entries: list[dict[str, Any]],
    missing_kbs: list[str],
) -> list[str]:
    """Build the advisory evidence section."""

    lines = [
        "",
        "## Advisory Evidence",
        "",
    ]

    lines.extend(build_advisory_table(kb_entries, missing_kbs))

    return lines


def build_baseline_evidence_section(baseline: dict[str, Any]) -> list[str]:
    """Build the baseline evidence section."""

    lines = [
        "",
        "## Baseline Evidence",
        "",
    ]

    lines.extend(
        build_key_value_table(
            [
                ("OS name", baseline.get("OsName")),
                ("OS edition", baseline.get("OsEdition")),
                ("Display version", baseline.get("DisplayVersion")),
                ("Build", baseline.get("Build")),
                ("Architecture", baseline.get("Architecture")),
                ("LCU MonthId", baseline.get("LcuMonthId")),
                ("LCU package name", baseline.get("LcuPackageName")),
                ("LCU install month", baseline.get("LcuInstallMonth")),
                ("Patch age days", baseline.get("PatchAgeDays")),
                ("MSRC latest MonthId", baseline.get("MsrcLatestMonthId")),
                ("Resolved product MonthId", baseline.get("ResolvedProductMonthId")),
                ("Product hint", baseline.get("ProductNameHint")),
            ]
        )
    )

    return lines


def build_method_section() -> list[str]:
    """Build the report method section."""

    return [
        "",
        "## Method",
        "",
        "Kolektria collects Windows update-state evidence, installed KB inventory, MSRC advisory mappings, and supersedence relationships. Missing KBs are calculated by comparing expected advisory KBs against installed KBs after expanding logical presence through supersedence evidence.",
        "",
        "## Scope Notes",
        "",
        "This report is generated from authorised local host evidence and is intended for downstream Remetria analysis.",
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
    months_requested = scan_result.get("MonthsRequested") or []
    kb_entries = scan_result.get("KbEntries") or []
    supersedence_summary = scan_result.get("SupersedenceSummary") or {}
    missing_kbs = scan_result.get("MissingKbs") or []

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []

    lines.extend(
        build_scan_outcome_section(
            generated_at=generated_at,
            baseline=baseline,
            months_requested=months_requested,
            kb_entries=kb_entries,
            supersedence_summary=supersedence_summary,
        )
    )

    lines.extend(
        build_missing_state_section(
            kb_entries=kb_entries,
            missing_kbs=missing_kbs,
            supersedence_summary=supersedence_summary,
        )
    )

    lines.extend(
        build_advisory_evidence_section(
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