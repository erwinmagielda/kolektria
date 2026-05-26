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

def build_key_value_table(rows: list[tuple[str, Any]]) -> list[str]:
    """Build a two-column Markdown key-value table."""

    lines = [
        "| Field | Value |",
        "|---|---|",
    ]

    for field, value in rows:
        lines.append(f"| {field} | {format_value(value)} |")

    return lines


def build_kb_state_table(
    kb_entries: list[dict[str, Any]],
    installed_kbs: list[str],
    missing_kbs: list[str],
) -> list[str]:
    """Build a KB state table with counts and actual KB values."""

    expected_kbs = get_expected_kbs(kb_entries)
    superseded_kbs = get_superseded_kbs(kb_entries)

    rows = [
        (
            "Expected",
            len(expected_kbs),
            format_list(expected_kbs),
        ),
        (
            "Installed",
            len(installed_kbs),
            format_list(installed_kbs),
        ),
        (
            "Superseded",
            len(superseded_kbs),
            format_list(superseded_kbs),
        ),
        (
            "Missing",
            len(missing_kbs),
            format_list(missing_kbs, "None"),
        ),
    ]

    lines = [
        "| KB State | Count | KBs |",
        "|---|---|---|",
    ]

    for state, count, kbs in rows:
        lines.append(f"| {state} | {count} | {kbs} |")

    return lines


def build_missing_kb_evidence_table(
    kb_entries: list[dict[str, Any]],
    missing_kbs: list[str],
) -> list[str]:
    """Build a Markdown table for missing KB evidence and related CVEs."""

    lines = [
        "| ID | KB | Status | Months | CVE Count | CVEs | Supersedes | Update Type |",
        "|---|---|---|---|---|---|---|---|",
    ]

    missing_entries = get_missing_entries(
        kb_entries=kb_entries,
        missing_kbs=missing_kbs,
    )

    if not missing_entries:
        lines.append("| 0 | None | Not Missing | None | 0 | None | None | None |")
        return lines

    for index, entry in enumerate(missing_entries, start=1):
        kb_id = format_value(entry.get("KB"))
        months = format_list(entry.get("Months") or [])
        cves = entry.get("Cves") or []
        cve_count = len(cves)
        cve_list = format_list(cves)
        supersedes = format_list(entry.get("Supersedes") or [])
        update_type = format_value(entry.get("UpdateType"))

        lines.append(
            f"| {index} | {kb_id} | Missing | {months} | {cve_count} | {cve_list} | {supersedes} | {update_type} |"
        )

    return lines


def build_baseline_evidence_table(baseline: dict[str, Any]) -> list[str]:
    """Build the baseline evidence table."""

    rows = [
        ("OS Name", baseline.get("OsName")),
        ("OS Edition", baseline.get("OsEdition")),
        ("Display Version", baseline.get("DisplayVersion")),
        ("Build", baseline.get("Build")),
        ("Architecture", baseline.get("Architecture")),
        ("LCU MonthId", baseline.get("LcuMonthId")),
        ("LCU Install Month", baseline.get("LcuInstallMonth")),
        ("Patch Age Days", baseline.get("PatchAgeDays")),
        ("MSRC Latest MonthId", baseline.get("MsrcLatestMonthId")),
        ("Resolved Product MonthId", baseline.get("ResolvedProductMonthId")),
        ("Product Hint", baseline.get("ProductNameHint")),
    ]

    return build_key_value_table(rows)


# ------------------------------------------------------------
# REPORT SECTIONS
# ------------------------------------------------------------

def build_scan_outcome_section(
    generated_at: str,
    baseline: dict[str, Any],
    months_requested: list[str],
    supersedence_summary: dict[str, Any],
) -> list[str]:
    """Build the scan outcome section."""

    lines = [
        "# Kolektria Scan Report",
        "",
        "Kolektria is a Windows patch-state collector that gathers update, KB, MSRC, and supersedence evidence from authorised hosts. The generated JSON and Markdown report are intended for downstream Remetria analysis.",
        "",
        "## Scan Outcome",
        "",
        "High-level scan result and Windows advisory context.",
        "",
    ]

    lines.extend(
        build_key_value_table(
            [
                ("Date Generated", generated_at),
                ("Operating System", baseline.get("OsName")),
                ("Months Requested", format_list(months_requested)),
                ("Missing KBs", supersedence_summary.get("MissingKbs")),
            ]
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
        "Summary of the KB states used to decide whether expected updates are present, superseded, or missing.",
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
        "Evidence chain for each missing KB, including affected CVEs and supersedence data.",
        "",
    ]

    lines.extend(
        build_missing_kb_evidence_table(
            kb_entries=kb_entries,
            missing_kbs=missing_kbs,
        )
    )

    lines.append("")

    return lines


def build_baseline_evidence_section(baseline: dict[str, Any]) -> list[str]:
    """Build the baseline evidence section."""

    lines = [
        "## Baseline Evidence",
        "",
        "Non-identifying Windows update-state fields used to resolve the correct MSRC product context.",
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
    supersedence_summary = scan_result.get("SupersedenceSummary") or {}
    missing_kbs = scan_result.get("MissingKbs") or []

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []

    lines.extend(
        build_scan_outcome_section(
            generated_at=generated_at,
            baseline=baseline,
            months_requested=months_requested,
            supersedence_summary=supersedence_summary,
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