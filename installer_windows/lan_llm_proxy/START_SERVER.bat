@echo off
title LAN LLM Proxy - Server
color 0B

REM ---- Always run from the folder this .bat file is in ----
cd /d "%~dp0"

REM ---- Set UTF-8 mode so special characters don't crash the terminal ----
chcp 65001 >nul 2>&1

REM ============================================================
REM  EDIT THIS LINE - Replace with your OpenAI API Key
REM  Get one at: https://platform.openai.com/api-keys
REM ============================================================
set OPENAI_API_KEY=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

REM ---- Validate API Key ----
if "%OPENAI_API_KEY%"=="your-api-key-here" (
    echo.
    echo  !! API KEY NOT CONFIGURED !!
    echo.
    echo  Please edit this file and replace:
    echo    your-api-key-here
    echo  with your actual OpenAI API key.
    echo.
    echo  Get your API key at:
    echo    https://platform.openai.com/api-keys
    echo.
    pause
    exit /b 1
)

REM ---- Ensure firewall port 8000 is open for mobile access ----
netsh advfirewall firewall show rule name="LAN LLM Proxy" >nul 2>&1
IF ERRORLEVEL 1 (
    netsh advfirewall firewall add rule name="LAN LLM Proxy" protocol=TCP dir=in localport=8000 action=allow >nul 2>&1
)

echo.
echo ============================================================
echo    LAN LLM PROXY SYSTEM - Starting Server
echo ============================================================
echo.
echo  API Key  : Configured
echo  Dashboard: http://localhost:8000
echo  Hotkey   : Ctrl+Shift+X
echo.
echo  NOTE: For the hotkey to work, this window must be
echo        running as Administrator (right-click - Run as admin)
echo.
echo  Press Ctrl+C to stop the server
echo ============================================================
echo.

python server.py

IF ERRORLEVEL 1 (
    echo.
    echo  Server stopped with an error.
    echo  Check the output above for details.
    echo.
    pause
)
