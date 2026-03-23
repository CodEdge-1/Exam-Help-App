#!/bin/bash

# LAN LLM Proxy System - Start Client (macOS / Linux)

# ============================================================
#  EDIT THIS LINE - Replace with the SERVER's IP address
#  Ask the person running the server for their IP
# ============================================================
SERVER_IP="192.168.1.136"

# Colors
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

clear

echo ""
echo "============================================================"
echo -e "${BOLD}${CYAN}   LAN LLM PROXY SYSTEM - Client${RESET}"
echo "============================================================"
echo ""
echo -e "  Connecting to: ${CYAN}${SERVER_IP}:8000${RESET}"
echo ""
echo "  Press Ctrl+C to disconnect"
echo "============================================================"
echo ""

# Pass IP to client
export LAN_PROXY_SERVER_IP=$SERVER_IP

# Detect Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

$PYTHON client.py
