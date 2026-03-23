#!/bin/bash

# LAN LLM Proxy System - Unix Installer (macOS / Linux)

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

clear

echo ""
echo "============================================================"
echo -e "${BOLD}${CYAN}   LAN LLM PROXY SYSTEM - Installer${RESET}"
echo -e "${CYAN}   macOS / Linux${RESET}"
echo "============================================================"
echo ""

# ---- Detect OS ----
OS="$(uname -s)"
case "${OS}" in
    Linux*)  PLATFORM="Linux";;
    Darwin*) PLATFORM="Mac";;
    *)       PLATFORM="Unknown";;
esac
echo -e "${CYAN}Platform: ${PLATFORM}${RESET}"
echo ""

# ---- Check Python ----
echo -e "${BOLD}[1/5] Checking Python...${RESET}"

if command -v python3 &>/dev/null; then
    PYTHON=python3
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ ${PYTHON_VERSION}${RESET}"
elif command -v python &>/dev/null; then
    PYTHON=python
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✅ ${PYTHON_VERSION}${RESET}"
else
    echo -e "${RED}❌ Python not found!${RESET}"
    echo ""
    echo "Please install Python 3.8+:"
    if [ "$PLATFORM" = "Mac" ]; then
        echo "  brew install python"
        echo "  or: https://www.python.org/downloads/"
    else
        echo "  sudo apt-get install python3 python3-pip  # Ubuntu/Debian"
        echo "  sudo yum install python3 python3-pip      # CentOS/RHEL"
    fi
    exit 1
fi

# ---- Check pip ----
echo ""
echo -e "${BOLD}[2/5] Upgrading pip...${RESET}"
$PYTHON -m pip install --upgrade pip --quiet
echo -e "${GREEN}✅ pip ready${RESET}"

# ---- Linux dependencies ----
if [ "$PLATFORM" = "Linux" ]; then
    echo ""
    echo -e "${BOLD}[3/5] Installing Linux dependencies...${RESET}"
    echo -e "${YELLOW}This may require your sudo password${RESET}"
    
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3-tk python3-dev scrot xclip 2>/dev/null || \
            echo -e "${YELLOW}⚠️  Some system packages may need manual installation${RESET}"
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3-tkinter python3-devel scrot xclip 2>/dev/null || \
            echo -e "${YELLOW}⚠️  Some system packages may need manual installation${RESET}"
    fi
    echo -e "${GREEN}✅ System dependencies handled${RESET}"
else
    echo ""
    echo -e "${BOLD}[3/5] Checking macOS dependencies...${RESET}"
    echo -e "${GREEN}✅ macOS dependencies OK${RESET}"
fi

# ---- Install Python packages ----
echo ""
echo -e "${BOLD}[4/5] Installing Python packages (1-2 minutes)...${RESET}"
$PYTHON -m pip install -r requirements.txt
echo -e "${GREEN}✅ All packages installed${RESET}"

# ---- Create directories ----
echo ""
echo -e "${BOLD}[5/5] Creating folders...${RESET}"
mkdir -p data/captures data/results data/logs
echo -e "${GREEN}✅ Folders created${RESET}"

# ---- Make scripts executable ----
chmod +x install.sh start_server.sh start_client.sh 2>/dev/null || true

# ---- Get network IP ----
echo ""
if [ "$PLATFORM" = "Mac" ]; then
    MY_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "Check with: ifconfig")
else
    MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "Check with: ip addr")
fi

# ---- macOS screen permissions notice ----
if [ "$PLATFORM" = "Mac" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  macOS Screen Recording Permission Required:${RESET}"
    echo "   System Preferences → Security & Privacy → Privacy"
    echo "   → Screen Recording → Enable for Terminal"
    echo ""
fi

# ---- Done ----
echo ""
echo "============================================================"
echo -e "${BOLD}${GREEN}  INSTALLATION COMPLETE!${RESET}"
echo "============================================================"
echo ""
echo -e "${BOLD}Your IP address: ${CYAN}${MY_IP}${RESET}"
echo ""
echo -e "${BOLD}NEXT STEPS:${RESET}"
echo ""
echo "  1. Set your OpenAI API key:"
echo "     Edit start_server.sh"
echo "     Replace: your-api-key-here"
echo "     Get key from: platform.openai.com/api-keys"
echo ""
echo "  2. Start the server:"
echo "     ./start_server.sh"
echo ""
echo "  3. Open dashboard:"
echo "     http://localhost:8000"
echo ""
echo "  4. Press Ctrl+Shift+C to capture!"
echo ""
echo "============================================================"
echo ""
