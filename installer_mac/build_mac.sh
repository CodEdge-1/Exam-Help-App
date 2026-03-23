#!/bin/bash
# ============================================================
#  LAN LLM Proxy — Build macOS Installer
#  Self-contained: end users need NOTHING pre-installed
#  Run this script on a Mac (the build machine only)
# ============================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "===================================================="
echo "  Building LAN LLM Proxy Installer for macOS"
echo "  (Self-contained — end users need NOTHING installed)"
echo "===================================================="
echo ""

# ── Detect Python on the BUILD machine ────────────────────────────────────────
# Tries multiple locations so it works regardless of how Python was installed
PYTHON_CMD=""

try_python() {
    if command -v "$1" &>/dev/null; then
        VER=$("$1" -c "import sys; print(sys.version_info[:2])" 2>/dev/null)
        if [ -n "$VER" ]; then
            PYTHON_CMD="$1"
            return 0
        fi
    fi
    return 1
}

# Check in priority order: python3, python, then common install paths
try_python python3      && echo "Build machine: $(python3 --version)  (using: python3)" ||
try_python python       && echo "Build machine: $(python --version)  (using: python)"  ||
try_python /usr/local/bin/python3                    ||   # Homebrew (Intel)
try_python /opt/homebrew/bin/python3                 ||   # Homebrew (Apple Silicon)
try_python /usr/local/opt/python@3.11/bin/python3    ||   # Homebrew pinned
try_python /usr/local/opt/python@3.10/bin/python3    ||
try_python "$HOME/.pyenv/shims/python3"              ||   # pyenv
try_python "$HOME/Library/Python/3.11/bin/python3"   ||   # user install
try_python "$HOME/Library/Python/3.10/bin/python3"   ||
try_python /usr/bin/python3                               # system Python (Xcode CLT)

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "ERROR: Python not found on THIS machine (the build machine)."
    echo "You only need Python here to build. End users will NOT need it."
    echo ""
    echo "Try one of these fixes:"
    echo "  1. Install via Homebrew:  brew install python"
    echo "  2. Or download from:      https://python.org/downloads"
    echo "  3. Then re-run this script"
    exit 1
fi

echo "Build machine: $($PYTHON_CMD --version)  (using: $PYTHON_CMD)"

# ── Ensure pip is available (auto-bootstrap if missing) ───────────────────────
echo ""
echo "[1/5] Checking pip..."
"$PYTHON_CMD" -m pip --version &>/dev/null
if [ $? -ne 0 ]; then
    echo "      pip not found — bootstrapping via ensurepip..."
    "$PYTHON_CMD" -m ensurepip --upgrade 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "      ensurepip failed, trying get-pip.py..."
        curl -L -s -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
        "$PYTHON_CMD" /tmp/get-pip.py
    fi
fi

"$PYTHON_CMD" -m pip --version &>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Could not install pip."
    echo "Try reinstalling Python via: brew install python"
    echo "Or download from: https://python.org/downloads"
    exit 1
fi
echo "      pip ready."

# ── Install PyInstaller ────────────────────────────────────────────────────────
echo ""
echo "      Installing PyInstaller..."
"$PYTHON_CMD" -m pip install pyinstaller --quiet --upgrade
echo "      Done."

# ── Copy source files if needed ───────────────────────────────────────────────
echo ""
echo "[2/5] Preparing source files..."
if [ ! -d "$SCRIPT_DIR/lan_llm_proxy" ]; then
    if [ -d "$SCRIPT_DIR/../lan_llm_proxy" ]; then
        cp -r "$SCRIPT_DIR/../lan_llm_proxy" "$SCRIPT_DIR/lan_llm_proxy"
        echo "      Copied lan_llm_proxy folder."
    else
        echo "WARNING: lan_llm_proxy folder not found."
    fi
else
    echo "      lan_llm_proxy folder already present."
fi

# ── Download standalone Python runtime for end users ──────────────────────────
echo ""
echo "[3/5] Downloading standalone Python runtime for end users..."
echo "      (Bundled inside the installer — end users won't see this step)"
echo ""

ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    PY_URL="https://github.com/indygreg/python-build-standalone/releases/download/20240814/cpython-3.11.9%2B20240814-aarch64-apple-darwin-install_only.tar.gz"
    echo "      Detected: Apple Silicon (arm64)"
else
    PY_URL="https://github.com/indygreg/python-build-standalone/releases/download/20240814/cpython-3.11.9%2B20240814-x86_64-apple-darwin-install_only.tar.gz"
    echo "      Detected: Intel Mac (x86_64)"
fi

if [ ! -f "python_mac.tar.gz" ]; then
    echo "      Downloading Python 3.11.9 standalone runtime..."
    curl -L --progress-bar -o python_mac.tar.gz "$PY_URL"
    if [ $? -ne 0 ]; then
        echo "ERROR: Download failed. Check your internet connection."
        exit 1
    fi
    echo "      Downloaded python_mac.tar.gz"
else
    echo "      python_mac.tar.gz already present — skipping download."
fi

# ── Set up output folder ──────────────────────────────────────────────────────
OUTPUT_DIR="$SCRIPT_DIR/../packaged/mac"
mkdir -p "$OUTPUT_DIR"

# ── Clean previous build ──────────────────────────────────────────────────────
echo ""
echo "[4/5] Cleaning previous build output..."
rm -rf dist build LAN_LLM_Proxy_Setup.spec 2>/dev/null || true

# ── Run PyInstaller ───────────────────────────────────────────────────────────
echo ""
echo "[5/5] Building self-contained installer app..."
echo "      (Bundles Python + all proxy files — takes 2-3 minutes)"
echo ""

"$PYTHON_CMD" -m PyInstaller --onefile --windowed \
    --name "LAN_LLM_Proxy_Setup" \
    --add-data "lan_llm_proxy:lan_llm_proxy" \
    --add-data "python_mac.tar.gz:." \
    installer.py

if [ $? -ne 0 ]; then
    echo ""
    echo "====================================================="
    echo " BUILD FAILED. Common fixes:"
    echo "   - Make sure Xcode Command Line Tools are installed:"
    echo "       xcode-select --install"
    echo "   - Try upgrading PyInstaller:"
    echo "       $PYTHON_CMD -m pip install pyinstaller --upgrade"
    echo "====================================================="
    exit 1
fi

# ── Wrap in .dmg and move to packaged folder ──────────────────────────────────
echo ""
echo "      Wrapping into LAN_LLM_Proxy.dmg..."
hdiutil create \
    -volname "LAN LLM Proxy" \
    -srcfolder dist \
    -ov -format UDZO \
    "$OUTPUT_DIR/LAN_LLM_Proxy.dmg"

if [ $? -ne 0 ]; then
    echo "WARNING: DMG creation failed. Copying .app directly instead..."
    cp -r "dist/LAN_LLM_Proxy_Setup" "$OUTPUT_DIR/LAN_LLM_Proxy_Setup.app"
fi

# ── Copy README to packaged folder ───────────────────────────────────────────
cp "$SCRIPT_DIR/README.txt" "$OUTPUT_DIR/README.txt" 2>/dev/null || true

# ── Clean up build temp files ─────────────────────────────────────────────────
rm -rf dist build LAN_LLM_Proxy_Setup.spec 2>/dev/null || true

echo ""
echo "===================================================="
echo "  BUILD SUCCESSFUL!"
echo ""
echo "  Your installer is ready to send:"
echo "  packaged/mac/LAN_LLM_Proxy.dmg"
echo ""
echo "  Share this single .dmg with your client."
echo "  They just double-click it."
echo "  No Python. No dependencies. Nothing to pre-install."
echo "===================================================="
echo ""
