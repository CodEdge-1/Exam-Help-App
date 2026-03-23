@echo off
title LAN LLM Proxy - Installer
color 0A

echo.
echo ============================================================
echo    LAN LLM PROXY SYSTEM - Windows Installer
echo ============================================================
echo.

REM ---- Check Python ----
echo [1/7] Checking Python...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Python not found!
    echo  Please install Python from: https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during install!
    pause
    start https://www.python.org/downloads/
    exit /b 1
)
python --version
echo  Python found!

REM ---- Upgrade pip ----
echo.
echo [2/7] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo  pip upgraded!

REM ---- Upgrade setuptools and wheel first (fixes Python 3.14 build issues) ----
echo.
echo [3/7] Upgrading build tools (fixes Python 3.14 compatibility)...
python -m pip install --upgrade setuptools wheel --quiet
echo  Build tools upgraded!

REM ---- Install requirements ----
echo.
echo [4/7] Installing packages (this may take 1-2 minutes)...
python -m pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo.
    echo  Standard install failed. Trying alternative method...
    echo.
    python -m pip install --upgrade setuptools wheel build --quiet
    python -m pip install fastapi "uvicorn[standard]" websockets pydantic openai python-multipart colorama keyboard --quiet
    python -m pip install --upgrade Pillow
    IF ERRORLEVEL 1 (
        echo.
        echo  ERROR: Could not install all packages.
        echo  Please run this window as Administrator and try again.
        echo  Right-click INSTALL.bat and select "Run as administrator"
        pause
        exit /b 1
    )
)
echo  All packages installed!

REM ---- Open Windows Firewall for port 8000 ----
echo.
echo [5/7] Opening Windows Firewall on port 8000...
netsh advfirewall firewall show rule name="LAN LLM Proxy" >nul 2>&1
IF ERRORLEVEL 1 (
    netsh advfirewall firewall add rule name="LAN LLM Proxy" protocol=TCP dir=in localport=8000 action=allow >nul 2>&1
    IF ERRORLEVEL 1 (
        echo  WARNING: Could not add firewall rule. Run as Administrator to fix mobile access.
    ) ELSE (
        echo  Firewall rule added - port 8000 is now open!
    )
) ELSE (
    echo  Firewall rule already exists - OK!
)

REM ---- Create data directories ----
echo.
echo [6/7] Creating folders...
if not exist "data\captures" mkdir "data\captures"
if not exist "data\results"  mkdir "data\results"
if not exist "data\logs"     mkdir "data\logs"
echo  Folders created!

REM ---- Get network IP ----
echo.
echo [7/7] Your network IP address:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    goto :found_ip
)
:found_ip
echo  %ip%

REM ---- Done ----
echo.
echo ============================================================
echo   INSTALLATION COMPLETE!
echo ============================================================
echo.
echo  NEXT STEPS:
echo.
echo  1. Edit START_SERVER.bat and add your OpenAI API key
echo  2. Double-click START_SERVER.bat to start
echo  3. Open browser: http://localhost:8000
echo  4. Press Ctrl+Shift+C to capture!
echo.
echo ============================================================
echo.
pause
