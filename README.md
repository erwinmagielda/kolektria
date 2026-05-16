# WinShield+ Collector

**Portable Windows patch-state collection and WinShield+ dataset acquisition.**

[Companion Project: WinShield+](https://github.com/erwinmagielda/winshield_plus)

WinShield+ Collector is a portable Windows host-scanning utility that gathers patch-state telemetry and exports compatible WinShield+ runtime scan JSON. It is designed to safely collect authorised endpoint data for offline analysis, dataset growth, and vulnerability assessment workflows.

The collector reuses the same PowerShell collection logic used by WinShield+, allowing harvested scan data to be imported directly into the main prioritisation pipeline without schema conversion or manual restructuring.

WinShield+ Collector is intended for controlled lab and authorised assessment environments. It is not designed for stealth collection, persistence, or enterprise endpoint management.

---

## Overview

The collector separates host acquisition from analysis. Instead of running the full WinShield+ platform directly on every endpoint, the collector can be distributed independently to gather compatible scan artefacts from authorised Windows systems.

The project demonstrates:

- Portable Windows patch-state collection.
- PowerShell-based host baseline and KB inventory extraction.
- MSRC advisory alignment through reusable collector modules.
- Runtime and archive scan management.
- Compatible JSON export for WinShield+ ingestion.
- EXE compilation through PyInstaller.
- Automatic elevation handling and dependency validation.
- Python source fallback when the executable is unavailable.
- Structured runtime artefacts for repeatable analysis workflows.

---

## Features

| Area | Implementation |
|---|---|
| Portable Collection | The collector can be executed independently from removable storage or standalone directories. |
| Windows Assessment | The workflow gathers host baseline, installed KB inventory, LCU context, and servicing metadata. |
| MSRC Correlation | Advisory mapping aligns installed and expected KB state against Microsoft Security Response Center data. |
| Compatible Export | Exported runtime JSON follows the same contract used by WinShield+ runtime ingestion. |
| Runtime Management | The latest runtime workspace is refreshed automatically while historical scans remain archived. |
| EXE Distribution | The collector supports standalone executable generation through PyInstaller. |
| Fallback Execution | When the executable is unavailable, the launcher automatically falls back to readable Python source execution. |
| Operational Safety | The workflow uses explicit elevation checks, dependency validation, and reviewable output artefacts. |

---

## Screenshots

The screenshots below show the collector build process, privilege validation, executable execution, and Python fallback workflow.

### EXE Build

![EXE build](assets/collection_build.png)

The build helper validates Python and PyInstaller availability before generating a standalone collector executable.

### Elevation Handling

![Elevation handling](assets/collection_priviledges.png)

The launcher validates administrator privileges before collection begins and requests elevation when required.

### Executable Collection

![Executable collection](assets/collection_executable.png)

When the compiled executable is available, the launcher runs the portable collector directly and exports runtime scan JSON.

### Python Fallback

![Python fallback](assets/collection_fallback.png)

If the executable is unavailable, the launcher automatically falls back to the readable Python source implementation.

---

## Architecture

The collector separates launcher logic, PowerShell acquisition, runtime export, and archive management into modular stages.

```text
winshield_collector.bat
│   Launches the collector workflow, validates dependencies,
│   checks elevation state, and selects EXE or Python execution.
│
build/
└── build_exe.bat
    Builds the standalone collector executable through PyInstaller.
│
src/
├── core/
│   └── winshield_collector.py
│       Runs host collection, MSRC correlation, supersedence logic,
│       runtime export, and archive management.
│
└── powershell/
    ├── winshield_baseline.ps1
    │   Collects OS baseline, architecture, and LCU context.
    │
    ├── winshield_inventory.ps1
    │   Enumerates installed KB inventory from the host.
    │
    └── winshield_adapter.ps1
        Queries MSRC advisory data and maps KB updates to CVEs.
│
data/
├── runtime/
│   Stores the latest generated runtime scan.
│
└── collected/
    Stores persistent archived scan history.
```

Each stage communicates through structured JSON artefacts so collected endpoint data can later be imported into WinShield+ without additional transformation.

---

## Collection Workflow

The collector is designed to support lightweight distributed acquisition for authorised hosts.

```text
Portable USB
    -> Run WinShield+ Collector
    -> Scan Authorised Windows Host
    -> Export Compatible Scan JSON
    -> Store Archived Runtime Copy
    -> Import Into WinShield+ Dataset
    -> Increase Training Data Coverage
```

This workflow allows scan acquisition and vulnerability analysis to remain operationally separated while preserving dataset consistency.

---

## Operation

Run the launcher from the repository root:

```bat
winshield_collector.bat
```

The launcher performs pre-flight validation before collection begins.

| Step | Action | Purpose |
|---|---|---|
| 1 | Windows Check | Verifies the collector is running on a supported Windows host. |
| 2 | Elevation Check | Requests administrator privileges required for servicing-state collection. |
| 3 | Dependency Validation | Confirms PowerShell and the MSRC module are available. |
| 4 | EXE Detection | Attempts to launch the standalone executable when present. |
| 5 | Python Fallback | Falls back to readable Python source execution if the executable is unavailable. |
| 6 | Runtime Export | Saves the latest runtime scan and archives a persistent copy. |

To build the standalone executable:

```bat
build\build_exe.bat
```

Runtime behaviour:

```text
data/runtime
    Latest scan workspace, refreshed each run.

data/collected
    Persistent scan archive, never cleared automatically.
```

---

## Security Controls

The collector is designed around controlled acquisition and transparent execution.

| Control | Implementation |
|---|---|
| Authorised Usage | The workflow is intended for approved Windows hosts and controlled assessment environments. |
| No Remediation | The collector performs assessment only and does not install, modify, or remove updates. |
| No Persistence | The project does not establish persistence, scheduled tasks, or resident services. |
| Reviewable Output | All collected results are exported as readable JSON artefacts. |
| Explicit Execution | Elevation, dependency handling, and execution paths remain visible to the operator. |
| Modular Design | Collection, export, and archive logic remain separated for easier inspection and maintenance. |

---

## Project Status

Current status: **complete portable collector implementation**.

Implemented functionality includes:

- Portable runtime scan collection for authorised Windows hosts.
- Host baseline and KB inventory extraction through PowerShell.
- MSRC advisory alignment and supersedence-aware collection logic.
- Compatible JSON export for direct WinShield+ ingestion.
- Automatic runtime workspace refresh and persistent archive storage.
- Standalone executable generation through PyInstaller.
- Automatic Python fallback support.
- Elevation handling and dependency validation through the launcher.

Future development under the wider WinShield ecosystem could include:

- Signed executable releases for stronger integrity assurance.
- Export compression for large-scale scan collection.
- Extended metadata collection for asset-aware prioritisation.
- Offline advisory snapshot support for isolated environments.
- Broader legacy Windows servicing compatibility.

---

## Limitations

The collector gathers Windows servicing and patch-state evidence, but it does not perform vulnerability exploitation, remediation validation, or threat simulation.

Collection quality depends on Windows servicing state, MSRC advisory consistency, and PowerShell execution availability on the target system.

The exported JSON is intended for WinShield+ compatibility and may require adaptation before integration into unrelated tooling.

---

## Licence

MIT License. See `LICENSE`.
