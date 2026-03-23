@echo off
title LAN LLM Proxy — Build Windows Installer
echo.
echo ====================================================
echo   Building LAN LLM Proxy Installer for Windows
echo   (Self-contained — end users need NOTHING installed)
echo ====================================================
echo.

:: ── Detect Python on the BUILD machine ───────────────────────────────────────
:: Try py launcher first (works even when running as Admin with user-PATH Python)
set PYTHON_CMD=
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto :python_found
)
:: Fallback: try python
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :python_found
)
:: Fallback: try python3
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :python_found
)
:: Last resort: check common install paths directly
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if exist %%P (
        set PYTHON_CMD=%%P
        goto :python_found
    )
)

echo ERROR: Python not found on THIS machine ^(the build machine^).
echo You only need Python here to build. End users will NOT need it.
echo.
echo Try one of these fixes:
echo   1. Open a NEW Command Prompt ^(not as Admin^) and run build_windows.bat from there
echo   2. Or reinstall Python and check "Install for all users" + "Add to PATH"
echo   3. Download from: https://python.org/downloads
pause
exit /b 1

:python_found
for /f "tokens=*" %%v in ('"%PYTHON_CMD%" --version 2^>^&1') do echo Build machine: %%v  ^(using: %PYTHON_CMD%^)

:: ── Ensure pip is available (auto-bootstrap if missing) ──────────────────────
echo.
echo [1/5] Checking pip...
"%PYTHON_CMD%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo       pip not found — bootstrapping via ensurepip...
    "%PYTHON_CMD%" -m ensurepip --upgrade
    if errorlevel 1 (
        echo       ensurepip failed, trying get-pip.py...
        curl -L -s -o "%TEMP%\get-pip.py" "https://bootstrap.pypa.io/get-pip.py"
        "%PYTHON_CMD%" "%TEMP%\get-pip.py"
    )
)
"%PYTHON_CMD%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not install pip. Try reinstalling Python and checking
    echo        "Add Python to PATH" and "pip" options during setup.
    pause
    exit /b 1
)
echo       pip ready.

:: ── Install PyInstaller ───────────────────────────────────────────────────────
echo.
echo       Installing PyInstaller...
"%PYTHON_CMD%" -m pip install pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller.
    pause
    exit /b 1
)
echo       Done.

:: ── Copy source files into this folder ───────────────────────────────────────
echo.
echo [2/5] Preparing source files...
if not exist "lan_llm_proxy" (
    if exist "..\lan_llm_proxy" (
        xcopy /E /I /Q /Y "..\lan_llm_proxy" "lan_llm_proxy" >nul
        echo       Copied lan_llm_proxy folder.
    ) else (
        echo WARNING: lan_llm_proxy folder not found.
    )
) else (
    echo       lan_llm_proxy folder already present.
)

:: ── Download Python embeddable runtime ───────────────────────────────────────
echo.
echo [3/5] Downloading Python embeddable runtime for end users...
echo       ^(This is bundled inside the installer — end users won't see this step^)
echo.

if not exist "python_embed.zip" (
    echo       Downloading Python 3.11.9 embeddable package...
    curl -L --progress-bar -o python_embed.zip ^
        "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    if errorlevel 1 (
        echo ERROR: Download failed. Check your internet connection.
        pause
        exit /b 1
    )
    echo       Downloaded python_embed.zip
) else (
    echo       python_embed.zip already present — skipping download.
)

if not exist "get-pip.py" (
    echo       Downloading get-pip.py...
    curl -L --progress-bar -o get-pip.py "https://bootstrap.pypa.io/get-pip.py"
    if errorlevel 1 (
        echo ERROR: Could not download get-pip.py.
        pause
        exit /b 1
    )
    echo       Downloaded get-pip.py
) else (
    echo       get-pip.py already present — skipping download.
)

:: ── Set up output folder ──────────────────────────────────────────────────────
set OUTPUT_DIR=%~dp0..\packaged\windows
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

:: ── Clean previous build ──────────────────────────────────────────────────────
echo.
echo [4/5] Cleaning previous build output...
if exist "dist"  rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "LAN_LLM_Proxy_Setup.spec" del /q "LAN_LLM_Proxy_Setup.spec"

:: ── Run PyInstaller ───────────────────────────────────────────────────────────
echo.
echo [5/5] Building self-contained installer EXE...
echo       ^(Bundles Python + all proxy files — takes 2-3 minutes^)
echo.

"%PYTHON_CMD%" -m PyInstaller --onefile --windowed ^
    --name "LAN_LLM_Proxy_Setup" ^
    --add-data "lan_llm_proxy;lan_llm_proxy" ^
    --add-data "python_embed.zip;." ^
    --add-data "get-pip.py;." ^
    installer.py

if errorlevel 1 (
    echo.
    echo =====================================================
    echo  BUILD FAILED. Common fixes:
    echo   - Run this script as Administrator
    echo   - Make sure antivirus isn't blocking PyInstaller
    echo   - Try:  pip install pyinstaller --upgrade
    echo =====================================================
    pause
    exit /b 1
)

:: ── Move final EXE and README to packaged folder ──────────────────────────────
echo.
echo       Moving installer to packaged\windows\...
copy /Y "dist\LAN_LLM_Proxy_Setup.exe" "%OUTPUT_DIR%\LAN_LLM_Proxy_Setup.exe" >nul
if errorlevel 1 (
    echo ERROR: Could not copy EXE to packaged folder.
    pause
    exit /b 1
)
copy /Y "%~dp0README.txt" "%OUTPUT_DIR%\README.txt" >nul

:: ── Clean up build temp files ─────────────────────────────────────────────────
rmdir /s /q dist
rmdir /s /q build
del /q "LAN_LLM_Proxy_Setup.spec" 2>nul

echo.
echo ====================================================
echo   BUILD SUCCESSFUL!
echo.
echo   Your installer is ready to send:
echo   packaged\windows\LAN_LLM_Proxy_Setup.exe
echo.
echo   Share this single .exe with your client.
echo   They just double-click it.
echo   No Python. No dependencies. Nothing to pre-install.
echo ====================================================
echo.
pause
