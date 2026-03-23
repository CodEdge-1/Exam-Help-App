#!/bin/bash

# LAN LLM Proxy System - Start Server (macOS / Linux)

# ============================================================
#  EDIT THIS LINE - Replace with your OpenAI API Key
#  Get one at: https://platform.openai.com/api-keys
# ============================================================
export OPENAI_API_KEY=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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ---- Validate API Key ----
if [ "$OPENAI_API_KEY" = "your-api-key-here" ]; then
    echo ""
    echo -e "${RED}!! API KEY NOT CONFIGURED !!${RESET}"
    echo ""
    echo "Please edit this file and replace:"
    echo "  your-api-key-here"
    echo "with your actual OpenAI API key."
    echo ""
    echo "Get your key at: https://platform.openai.com/api-keys"
    echo ""
    exit 1
fi

clear

echo ""
echo "============================================================"
echo -e "${BOLD}${CYAN}   LAN LLM PROXY SYSTEM - Server${RESET}"
echo "============================================================"
echo ""

# Get local IP
if [[ "$(uname)" == "Darwin" ]]; then
    MY_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "unknown")
else
    MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "unknown")
fi

echo -e "  ${GREEN}API Key:   Configured${RESET}"
echo -e "  ${GREEN}Server IP: ${MY_IP}${RESET}"
echo -e "  ${GREEN}Dashboard: http://localhost:8000${RESET}"
echo -e "  ${GREEN}Hotkey:    Ctrl+Shift+C${RESET}"
echo ""
echo "  Share this IP with clients: ${CYAN}${MY_IP}${RESET}"
echo ""
echo "  Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Detect Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

# Run server (try sudo for hotkey support, fallback to normal)
if [ "$(id -u)" -ne 0 ]; then
    echo "Note: Running without sudo - hotkey may not work."
    echo "For hotkey support, run: sudo ./start_server.sh"
    echo ""
fi

$PYTHON server.py
