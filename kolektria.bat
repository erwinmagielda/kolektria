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
REM     data\runtime   - latest scan workspace
REM     data\collected - persistent scan archive
REM ------------------------------------------------------------

cd /d "%~dp0"

set "APP_NAME=Kolektria"
set "EXE_PATH=dist\kolektria.exe"
set "PY_PATH=src\collector.py"
set "POWERSHELL_DIR=src\powershell"
set "RUNTIME_DIR=data\runtime"
set "COLLECTED_DIR=data\collected"

echo.
echo ============================================================
echo  Kolektria
echo  Windows Patch-State Collector
echo ============================================================
echo.

REM ------------------------------------------------------------
REM WINDOWS CHECK
REM ------------------------------------------------------------

if /i not "%OS%"=="Windows_NT" (
    echo [X] This collector must be run on Windows.
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM ADMIN ELEVATION
REM ------------------------------------------------------------

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Administrator privileges are required.
    echo [*] Requesting elevation...
    echo.

    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"

    exit /b
)

REM ------------------------------------------------------------
REM POWERSHELL CHECK
REM ------------------------------------------------------------

where powershell.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] PowerShell was not found on this system.
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM MSRC MODULE CHECK
REM ------------------------------------------------------------

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "if (Get-Module -ListAvailable -Name MsrcSecurityUpdates) { exit 0 } else { exit 1 }" >nul 2>&1

if %errorlevel% neq 0 (
    echo [X] Required PowerShell module is missing:
    echo     MsrcSecurityUpdates
    echo.
    echo Kolektria requires this module to query Microsoft Security Response Center data.
    echo.
    echo Install it manually with:
    echo powershell -NoProfile -Command "Install-Module MsrcSecurityUpdates -Scope CurrentUser"
    echo.
    pause
    exit /b 1
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
REM DATA DIRECTORIES
REM ------------------------------------------------------------

if not exist "%RUNTIME_DIR%" (
    mkdir "%RUNTIME_DIR%" >nul 2>&1
)

if not exist "%COLLECTED_DIR%" (
    mkdir "%COLLECTED_DIR%" >nul 2>&1
)

REM ------------------------------------------------------------
REM COLLECTOR EXECUTION - EXE FIRST
REM ------------------------------------------------------------

if exist "%EXE_PATH%" (
    echo [*] Running Kolektria executable...
    echo.

    "%EXE_PATH%"

    if %errorlevel% neq 0 (
        echo.
        echo [X] Kolektria failed.
        echo.
        pause
        exit /b 1
    )

    echo.
    echo [+] Scan completed successfully.
    echo [+] Runtime JSON saved in: %RUNTIME_DIR%
    echo [+] Archived copy saved in: %COLLECTED_DIR%
    echo.
    pause
    exit /b 0
)

REM ------------------------------------------------------------
REM SOURCE FALLBACK
REM ------------------------------------------------------------

echo [!] Kolektria executable was not found:
echo     %EXE_PATH%
echo.
echo [*] Falling back to Python source mode...
echo.

where python.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python was not found.
    echo.
    echo Build the executable first using:
    echo build\build_exe.bat
    echo.
    pause
    exit /b 1
)

if not exist "%PY_PATH%" (
    echo [X] Python collector source was not found:
    echo %PY_PATH%
    echo.
    pause
    exit /b 1
)

python "%PY_PATH%"

if %errorlevel% neq 0 (
    echo.
    echo [X] Kolektria failed.
    echo.
    pause
    exit /b 1
)

echo.
echo [+] Scan completed successfully.
echo [+] Runtime JSON saved in: %RUNTIME_DIR%
echo [+] Archived copy saved in: %COLLECTED_DIR%
echo.
pause
exit /b 0