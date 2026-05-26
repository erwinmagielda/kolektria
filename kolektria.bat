@echo off
setlocal

title Kolektria Launcher

REM ------------------------------------------------------------
REM Kolektria Launcher
REM ------------------------------------------------------------
REM Runs the collector executable by default.
REM Falls back to Python source mode when the executable is unavailable.
REM
REM Output:
REM     data\runtime    - latest scan workspace
REM     data\collected  - persistent scan archive
REM     results\reports - generated Markdown reports
REM ------------------------------------------------------------

cd /d "%~dp0"

set "EXE_PATH=dist\kolektria.exe"
set "PY_PATH=src\collector.py"
set "POWERSHELL_DIR=src\powershell"
set "RUNTIME_DIR=data\runtime"
set "COLLECTED_DIR=data\collected"
set "REPORTS_DIR=results\reports"

REM ------------------------------------------------------------
REM PAUSE HELPER
REM ------------------------------------------------------------

goto main

:wait_to_close
echo Press any key to close
pause >nul
exit /b 0


REM ------------------------------------------------------------
REM MAIN WORKFLOW
REM ------------------------------------------------------------

:main

REM ------------------------------------------------------------
REM WINDOWS CHECK
REM ------------------------------------------------------------

if /i not "%OS%"=="Windows_NT" (
    echo [X] This collector must be run on Windows
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM ADMIN ELEVATION
REM ------------------------------------------------------------

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Administrator privileges are required
    echo [*] Requesting elevation
    echo.

    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"

    exit /b
)

REM ------------------------------------------------------------
REM POWERSHELL CHECK
REM ------------------------------------------------------------

where powershell.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] PowerShell was not found on this system
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM MSRC MODULE BOOTSTRAP
REM ------------------------------------------------------------

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "if (Get-Module -ListAvailable -Name MsrcSecurityUpdates) { exit 0 } else { exit 1 }" >nul 2>&1

if %errorlevel% neq 0 (
    echo.
    echo Dependency Bootstrap
    echo --------------------
    echo [*] Installing MSRC PowerShell module
    echo     [i] Module: MsrcSecurityUpdates
    echo     [i] Scope: CurrentUser
    echo.

    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ErrorActionPreference = 'Stop';" ^
        "Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Scope CurrentUser -Force;" ^
        "Set-PSRepository -Name PSGallery -InstallationPolicy Trusted;" ^
        "Install-Module -Name MsrcSecurityUpdates -Scope CurrentUser -Force -AllowClobber"

    if %errorlevel% neq 0 (
        echo.
        echo [X] Failed to install MSRC PowerShell module
        echo.
        pause
        exit /b 1
    )

    echo.
    echo     [+] MSRC PowerShell module installed
    echo.
)

REM ------------------------------------------------------------
REM REQUIRED FILE CHECKS
REM ------------------------------------------------------------

if not exist "%POWERSHELL_DIR%\baseline.ps1" (
    echo [X] Missing PowerShell script:
    echo %POWERSHELL_DIR%\baseline.ps1
    echo.
    pause
    exit /b 1
)

if not exist "%POWERSHELL_DIR%\inventory.ps1" (
    echo [X] Missing PowerShell script:
    echo %POWERSHELL_DIR%\inventory.ps1
    echo.
    pause
    exit /b 1
)

if not exist "%POWERSHELL_DIR%\adapter.ps1" (
    echo [X] Missing PowerShell script:
    echo %POWERSHELL_DIR%\adapter.ps1
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM OUTPUT DIRECTORIES
REM ------------------------------------------------------------

if not exist "%RUNTIME_DIR%" (
    mkdir "%RUNTIME_DIR%" >nul 2>&1
)

if not exist "%COLLECTED_DIR%" (
    mkdir "%COLLECTED_DIR%" >nul 2>&1
)

if not exist "%REPORTS_DIR%" (
    mkdir "%REPORTS_DIR%" >nul 2>&1
)

REM ------------------------------------------------------------
REM COLLECTOR EXECUTION
REM ------------------------------------------------------------

if exist "%EXE_PATH%" (
    "%EXE_PATH%"

    if %errorlevel% neq 0 (
        echo.
        echo [X] Kolektria failed
        echo.
        pause
        exit /b 1
    )

    call :wait_to_close
)

where python.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Kolektria executable was not found:
    echo     %EXE_PATH%
    echo.
    echo [X] Python fallback is unavailable because Python was not found
    echo.
    echo Build the executable first using:
    echo build\build_exe.bat
    echo.
    pause
    exit /b 1
)

if not exist "%PY_PATH%" (
    echo [X] Kolektria executable was not found:
    echo     %EXE_PATH%
    echo.
    echo [X] Python collector source was not found:
    echo     %PY_PATH%
    echo.
    pause
    exit /b 1
)

python "%PY_PATH%"

if %errorlevel% neq 0 (
    echo.
    echo [X] Kolektria failed
    echo.
    pause
    exit /b 1
)

call :wait_to_close