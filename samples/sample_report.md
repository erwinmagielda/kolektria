# Kolektria Scan Report

Kolektria is a Windows patch-state collector for authorised hosts. It gathers update, KB, MSRC, and supersedence evidence, then exports structured JSON and a readable Markdown report for downstream Remetria analysis.

## Scan Outcome

High-level result from this collection run.

| Date Generated | Operating System | Product Hint | Months Requested | Missing KBs |
|:---|:---|:---|:---|:---|
| 2026-05-27 11:40:13 UTC | Microsoft Windows 11 Home | `Windows 11 Version 25H2 for x64-based Systems` | `2026-May` | 1 |

## Missing Update State

Breakdown of the KB sets used to decide whether expected updates are installed, superseded, or missing.

| KB State | Count | KBs | Explanation |
|:---|:---|:---|:---|
| Expected | 2 | `KB5089466`, `KB5089549` | KBs identified from MSRC advisory mappings for the requested product and month range. |
| Installed | 4 | `KB5054156`, `KB5087051`, `KB5089549`, `KB5092762` | KBs detected directly from the local Windows update inventory. |
| Superseded | 1 | `KB5083769` | Older KBs referenced as superseded by advisory entries. |
| Missing | 1 | `KB5089466` | Expected KBs not found directly and not covered by the supersedence calculation. |

## Missing KB Evidence

Each missing KB is shown as a separate evidence block. CVEs are listed outside the table so long advisory mappings stay readable.

### 1. KB5089466

| KB | Status | Months | CVE Count | Supersedes | Update Type |
|:---|:---|:---|:---|:---|:---|
| `KB5089466` | Missing | `2026-May` | 60 | `KB5083769` | Superseding |

**Mapped CVEs:**

`CVE-2025-54518`, `CVE-2026-21530`, `CVE-2026-32161`, `CVE-2026-32170`, `CVE-2026-32209`, `CVE-2026-33834`, `CVE-2026-33835`, `CVE-2026-33837`, `CVE-2026-33838`, `CVE-2026-33839`, `CVE-2026-33840`, `CVE-2026-33841`, `CVE-2026-34329`, `CVE-2026-34330`, `CVE-2026-34331`, `CVE-2026-34333`, `CVE-2026-34334`, `CVE-2026-34336`, `CVE-2026-34337`, `CVE-2026-34338`, `CVE-2026-34339`, `CVE-2026-34340`, `CVE-2026-34341`, `CVE-2026-34342`, `CVE-2026-34343`, `CVE-2026-34344`, `CVE-2026-34345`, `CVE-2026-34347`, `CVE-2026-34351`, `CVE-2026-35415`, `CVE-2026-35416`, `CVE-2026-35417`, `CVE-2026-35418`, `CVE-2026-35419`, `CVE-2026-35421`, `CVE-2026-35422`, `CVE-2026-35423`, `CVE-2026-35424`, `CVE-2026-40369`, `CVE-2026-40377`, `CVE-2026-40380`, `CVE-2026-40382`, `CVE-2026-40397`, `CVE-2026-40398`, `CVE-2026-40399`, `CVE-2026-40401`, `CVE-2026-40403`, `CVE-2026-40405`, `CVE-2026-40406`, `CVE-2026-40407`, `CVE-2026-40408`, `CVE-2026-40410`, `CVE-2026-40413`, `CVE-2026-40414`, `CVE-2026-40415`, `CVE-2026-41088`, `CVE-2026-41096`, `CVE-2026-41097`, `CVE-2026-42825`, `CVE-2026-42896`

## Baseline Evidence

Non-identifying Windows update-state fields used to resolve the MSRC product context.

| Baseline Evidence | Recorded Value |
|:---|:---|
| Operating System | Microsoft Windows 11 Home |
| OS Edition | Core |
| Display Version | `25H2` |
| Build | `26200.8457` |
| Architecture | x64 |
| LCU MonthId | `2026-May` |
| LCU Install Month | `2026-May` |
| Patch Age Days | 14 |
| MSRC Latest MonthId | `2026-May` |
| Resolved Product MonthId | `2026-May` |
| Product Hint | `Windows 11 Version 25H2 for x64-based Systems` |

## Method

Kolektria collects Windows update-state evidence, installed KB inventory, MSRC advisory mappings, and supersedence relationships. Missing KBs are calculated by comparing expected advisory KBs against installed KBs after expanding logical presence through supersedence evidence.

## Scope Notes

The report is generated from authorised local host evidence and is intended for downstream Remetria analysis.

Kolektria does not collect hostname, username, device name, serial number, IP address, MAC address, domain, local file paths, installed applications, or user activity. The scan is limited to Windows update-state and MSRC advisory-mapping evidence.
