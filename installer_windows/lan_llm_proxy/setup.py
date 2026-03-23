#!/usr/bin/env python3
"""
LAN LLM Proxy System - Setup & Verification Script
Automated setup and testing for the MVP
"""

import os
import sys
import subprocess
import socket
from pathlib import Path


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN} {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED} {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}  {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}  {text}{Colors.END}")


def check_python_version():
    """Check Python version"""
    print_info("Checking Python version...")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} detected")
        print_warning("Python 3.8 or higher required")
        return False


def check_pip():
    """Check if pip is available"""
    print_info("Checking pip...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("pip is installed")
            return True
        else:
            print_error("pip not found")
            return False
    except Exception as e:
        print_error(f"pip check failed: {e}")
        return False


def install_requirements():
    """Install required packages"""
    print_info("Installing requirements...")
    
    if not os.path.exists("requirements.txt"):
        print_error("requirements.txt not found")
        return False
    
    try:
        print_info("This may take a few minutes...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("All packages installed")
            return True
        else:
            print_error("Installation failed")
            print(result.stderr)
            return False
    except Exception as e:
        print_error(f"Installation error: {e}")
        return False


def check_imports():
    """Verify all required imports work"""
    print_info("Verifying package imports...")
    
    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "PIL": "Pillow",
        "keyboard": "keyboard",
        "openai": "OpenAI SDK",
        "websockets": "websockets",
        "pydantic": "Pydantic"
    }
    
    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print_success(f"{name}")
        except ImportError:
            print_error(f"{name} - IMPORT FAILED")
            all_ok = False
    
    return all_ok


def check_openai_key():
    """Check OpenAI API key"""
    print_info("Checking OpenAI API key...")
    
    # Check environment variable
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key and env_key != "your-api-key-here":
        print_success("Found in environment variable")
        return True
    
    # Check if server.py has key configured
    if os.path.exists("server.py"):
        with open("server.py", "r") as f:
            content = f.read()
            if 'OPENAI_API_KEY = "your-api-key-here"' in content:
                print_warning("API key not configured in server.py")
                print_info("Set OPENAI_API_KEY environment variable or edit server.py")
                return False
    
    print_warning("Could not verify API key configuration")
    return False


def test_screen_capture():
    """Test screen capture capability"""
    print_info("Testing screen capture...")
    
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        
        if screenshot:
            width, height = screenshot.size
            print_success(f"Screen capture working ({width}x{height})")
            return True
        else:
            print_error("Screen capture failed")
            return False
    except Exception as e:
        print_error(f"Screen capture error: {e}")
        print_info("On Linux, try: sudo apt-get install python3-tk scrot")
        print_info("On Mac, grant screen recording permissions")
        return False


def get_network_info():
    """Get network information"""
    print_info("Getting network information...")
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print_success(f"Hostname: {hostname}")
        print_success(f"Local IP: {local_ip}")
        print()
        print_info(f"Use this IP in client.py: SERVER_IP = \"{local_ip}\"")
        
        return local_ip
    except Exception as e:
        print_error(f"Network check failed: {e}")
        return None


def create_directories():
    """Create necessary directories"""
    print_info("Creating directories...")
    
    dirs = ["data/captures", "data/results", "data/logs"]
    
    for directory in dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {directory}")
    
    return True


def check_firewall():
    """Check firewall configuration"""
    print_info("Checking port availability...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 8000))
        sock.close()
        print_success("Port 8000 is available")
        return True
    except Exception as e:
        print_error(f"Port 8000 check failed: {e}")
        print_warning("Firewall may be blocking port 8000")
        return False


def generate_config():
    """Generate startup instructions"""
    print_header("🎉 SETUP COMPLETE!")
    
    print(f"{Colors.BOLD}Next Steps:{Colors.END}\n")
    
    print(f"{Colors.CYAN}1. Configure OpenAI API Key:{Colors.END}")
    print(f"   Option A: Set environment variable")
    print(f"     export OPENAI_API_KEY='sk-your-key-here'")
    print(f"   Option B: Edit server.py")
    print(f"     OPENAI_API_KEY = 'sk-your-key-here'")
    print()
    
    print(f"{Colors.CYAN}2. Start the Server:{Colors.END}")
    print(f"   python server.py")
    print(f"   (May need: sudo python server.py for hotkey support)")
    print()
    
    print(f"{Colors.CYAN}3. Access the Dashboard:{Colors.END}")
    print(f"   Open browser: http://localhost:8000")
    print()
    
    print(f"{Colors.CYAN}4. Setup Client on Another Device:{Colors.END}")
    print(f"   • Copy client.py and requirements.txt to Device 2")
    print(f"   • Edit client.py: SERVER_IP = \"YOUR_SERVER_IP\"")
    print(f"   • Install requirements: pip install -r requirements.txt")
    print(f"   • Run: python client.py")
    print()
    
    print(f"{Colors.CYAN}5. Test the System:{Colors.END}")
    print(f"   • Press Ctrl+Shift+C to capture screen")
    print(f"   • Or use the dashboard 'Capture Now' button")
    print(f"   • Watch results appear on client device")
    print()
    
    print(f"{Colors.BOLD}Documentation:{Colors.END}")
    print(f"   • Full docs: README.md")
    print(f"   • Quick start: QUICKSTART.md")
    print()


def main():
    """Main setup function"""
    print_header("LAN LLM PROXY SYSTEM - SETUP")
    
    results = {}
    
    # Run checks
    results['python'] = check_python_version()
    results['pip'] = check_pip()
    
    if not results['python'] or not results['pip']:
        print_error("\n Prerequisites not met")
        sys.exit(1)
    
    # Install requirements
    install = input("\nInstall requirements? (Y/n): ").strip().lower()
    if install != 'n':
        results['install'] = install_requirements()
    
    # Verify imports
    results['imports'] = check_imports()
    
    # Create directories
    results['directories'] = create_directories()
    
    # Additional checks
    results['screen'] = test_screen_capture()
    results['network'] = get_network_info() is not None
    results['firewall'] = check_firewall()
    results['api_key'] = check_openai_key()
    
    # Summary
    print_header("SETUP SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = print_success if result else print_error
        status(f"{check.replace('_', ' ').title()}")
    
    print(f"\n{Colors.BOLD}Score: {passed}/{total} checks passed{Colors.END}\n")
    
    if passed >= total - 1:  # Allow one optional failure
        generate_config()
    else:
        print_error("Setup incomplete. Please fix the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nSetup error: {e}")
        sys.exit(1)
