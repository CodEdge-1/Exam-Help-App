@echo off
title LAN LLM Proxy - Client
color 0D

REM ============================================================
REM  EDIT THIS LINE - Replace with the SERVER's IP address
REM  Ask the person running the server for their IP
REM ============================================================
set SERVER_IP=192.168.1.136

echo.
echo ============================================================
echo    LAN LLM PROXY SYSTEM - Starting Client
echo ============================================================
echo.
echo  Connecting to server at: %SERVER_IP%:8000
echo.
echo  Press Ctrl+C to stop the client
echo ============================================================
echo.

REM Pass the IP to client.py via environment variable
set LAN_PROXY_SERVER_IP=%SERVER_IP%
python client.py

IF ERRORLEVEL 1 (
    echo.
    echo  Client stopped.
    echo  Check that the server IP is correct.
    echo.
    pause
)
