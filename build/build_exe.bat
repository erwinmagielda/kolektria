@echo off
setlocal

title Kolektria EXE Builder

REM ------------------------------------------------------------
REM Kolektria EXE Builder
REM ------------------------------------------------------------
REM Builds:
REM     src\kolektria\collector.py
REM
REM Into:
REM     dist\kolektria.exe
REM ------------------------------------------------------------

cd /d "%~dp0\.."

set "SOURCE_FILE=src\kolektria\collector.py"
set "EXE_NAME=kolektria"
set "DIST_DIR=dist"
set "WORK_DIR=build\pyinstaller"
set "SPEC_DIR=build\pyinstaller"

echo.
echo Build Kolektria EXE
echo ===================
echo.

REM ------------------------------------------------------------
REM SOURCE CHECK
REM ------------------------------------------------------------

if not exist "%SOURCE_FILE%" (
    echo [X] Source file not found
    echo     %SOURCE_FILE%
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM PYTHON CHECK
REM ------------------------------------------------------------

where python.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python was not found
    echo.
    echo Install Python, then rerun:
    echo build\build_exe.bat
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM PYINSTALLER CHECK
REM ------------------------------------------------------------

python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] PyInstaller is not installed
    echo [*] Installing PyInstaller
    echo.

    python -m pip install -r requirements.txt

    if %errorlevel% neq 0 (
        echo.
        echo [X] Failed to install build dependencies
        echo.
        pause
        exit /b 1
    )
)

REM ------------------------------------------------------------
REM CLEAN PREVIOUS BUILD FILES
REM ------------------------------------------------------------

if exist "%DIST_DIR%\%EXE_NAME%.exe" (
    del /f /q "%DIST_DIR%\%EXE_NAME%.exe" >nul 2>&1
)

if exist "%WORK_DIR%" (
    rmdir /s /q "%WORK_DIR%" >nul 2>&1
)

if exist "%SPEC_DIR%\%EXE_NAME%.spec" (
    del /f /q "%SPEC_DIR%\%EXE_NAME%.spec" >nul 2>&1
)

REM ------------------------------------------------------------
REM BUILD EXE
REM ------------------------------------------------------------

echo [*] Building Kolektria executable
echo     [i] Source: %SOURCE_FILE%
echo     [i] Output: %DIST_DIR%\%EXE_NAME%.exe
echo.

python -m PyInstaller ^
    --onefile ^
    --clean ^
    --name "%EXE_NAME%" ^
    --paths "src" ^
    --distpath "%DIST_DIR%" ^
    --workpath "%WORK_DIR%" ^
    --specpath "%SPEC_DIR%" ^
    "%SOURCE_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo [X] Build failed
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM VERIFY OUTPUT
REM ------------------------------------------------------------

if not exist "%DIST_DIR%\%EXE_NAME%.exe" (
    echo.
    echo [X] Build completed, but executable was not found
    echo     %DIST_DIR%\%EXE_NAME%.exe
    echo.
    pause
    exit /b 1
)

echo.
echo [+] Build completed
echo     [i] Executable: %DIST_DIR%\%EXE_NAME%.exe
echo.
pause
exit /b 0