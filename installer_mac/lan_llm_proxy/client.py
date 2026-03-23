"""
LAN LLM Proxy System - Enhanced Client
Advanced client with colored console output and interactive features
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Optional

try:
    import websockets
except ImportError:
    print(" websockets not installed. Run: pip install websockets")
    sys.exit(1)

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    print("  colorama not installed. Install for colored output: pip install colorama")


# ============================================================================
# CONFIGURATION
# ============================================================================

import os
# Reads SERVER_IP from launcher scripts (START_CLIENT.bat / start_client.sh)
# or falls back to manual setting below
SERVER_IP = os.getenv("LAN_PROXY_SERVER_IP", "192.168.1.100")
SERVER_PORT = int(os.getenv("LAN_PROXY_SERVER_PORT", "8000"))
WEBSOCKET_URL = f"ws://{SERVER_IP}:{SERVER_PORT}/ws"


# ============================================================================
# COLOR HELPERS
# ============================================================================

class Colors:
    """Color output helpers"""
    
    @staticmethod
    def success(text):
        if COLORS_AVAILABLE:
            return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
        return f" {text}"
    
    @staticmethod
    def error(text):
        if COLORS_AVAILABLE:
            return f"{Fore.RED}{text}{Style.RESET_ALL}"
        return f" {text}"
    
    @staticmethod
    def warning(text):
        if COLORS_AVAILABLE:
            return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
        return f"  {text}"
    
    @staticmethod
    def info(text):
        if COLORS_AVAILABLE:
            return f"{Fore.CYAN}{text}{Style.RESET_ALL}"
        return f"  {text}"
    
    @staticmethod
    def header(text):
        if COLORS_AVAILABLE:
            return f"{Fore.MAGENTA}{Style.BRIGHT}{text}{Style.RESET_ALL}"
        return text
    
    @staticmethod
    def data(text):
        if COLORS_AVAILABLE:
            return f"{Fore.WHITE}{Style.BRIGHT}{text}{Style.RESET_ALL}"
        return text


# ============================================================================
# CLIENT CLASS
# ============================================================================

class LLMProxyClient:
    """Enhanced client for receiving LLM analysis results"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.message_count = 0
    
    def print_banner(self):
        """Print startup banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║             LAN LLM PROXY CLIENT                           ║
║                                                               ║
║           Real-time Screen Analysis Receiver                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        print(Colors.header(banner))
        print(Colors.info(f"Server: {self.server_url}"))
        print(Colors.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
        print("─" * 67)
    
    async def connect(self) -> bool:
        """Connect to server"""
        print(Colors.info(f"Connecting to {self.server_url}..."))
        
        try:
            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True
            print(Colors.success("Connected to server!"))
            print()
            return True
            
        except Exception as e:
            print(Colors.error(f"Connection failed: {e}"))
            print()
            print(Colors.warning("Troubleshooting:"))
            print("  1. Check if server is running")
            print("  2. Verify SERVER_IP is correct")
            print("  3. Check firewall settings")
            print("  4. Ensure both devices are on same network")
            return False
    
    async def listen(self):
        """Listen for incoming messages"""
        print(Colors.info("Listening for messages..."))
        print(Colors.info("Press Ctrl+C to exit"))
        print("═" * 67)
        print()
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.message_count += 1
                    self.handle_message(data)
                    
                except json.JSONDecodeError:
                    print(Colors.warning(f"Invalid JSON received: {message[:100]}..."))
        
        except websockets.exceptions.ConnectionClosed:
            print()
            print(Colors.error("Connection to server closed"))
            self.connected = False
        
        except Exception as e:
            print()
            print(Colors.error(f"Error: {e}"))
            self.connected = False
    
    def handle_message(self, data: dict):
        """Handle received message"""
        
        message_type = data.get("type")
        status = data.get("status")
        
        # Connection message
        if message_type == "connection":
            self.handle_connection(data)
        
        # Success result
        elif status == "success":
            self.handle_result(data)
        
        # Error result
        elif status == "error":
            self.handle_error(data)
        
        # Stats update
        elif message_type == "stats":
            self.handle_stats(data)
        
        # Other messages
        else:
            self.handle_other(data)
    
    def handle_connection(self, data: dict):
        """Handle connection message"""
        print(Colors.success("═" * 67))
        print(Colors.success(f"MESSAGE #{self.message_count}: CONNECTION"))
        print(Colors.success("═" * 67))
        print(Colors.info(data.get("message", "Connected")))
        
        server_info = data.get("server_info", {})
        if server_info:
            print(Colors.data(f"\n📋 Server Info:"))
            print(f"   Model: {server_info.get('model', 'N/A')}")
            print(f"   Hotkey: {server_info.get('hotkey', 'N/A')}")
        
        # Display latest result if available
        latest = data.get("latest_result")
        if latest and latest.get("status") == "success":
            print(Colors.info("\n📊 Latest result available:"))
            self.display_result_compact(latest)
        
        print("═" * 67)
        print()
    
    def handle_result(self, data: dict):
        """Handle analysis result"""
        print()
        print(Colors.success("═" * 67))
        print(Colors.success(f"📨 NEW ANALYSIS RECEIVED"))
        print(Colors.success("═" * 67))
        
        self.display_result_full(data)
        
        print("═" * 67)
        print()
    
    def handle_error(self, data: dict):
        """Handle error message"""
        print()
        print(Colors.error("═" * 67))
        print(Colors.error(f" ERROR RECEIVED"))
        print(Colors.error("═" * 67))
        
        print(Colors.error(f"\n{data.get('error', 'Unknown error')}"))
        print(f"\n Time: {self.format_timestamp(data.get('timestamp'))}")
        
        print("═" * 67)
        print()
    
    def handle_stats(self, data: dict):
        """Handle stats update"""
        print(Colors.info("\n System Statistics:"))
        print(f"   Total Captures: {data.get('total_captures', 0)}")
        print(f"   Connected Clients: {data.get('connected_clients', 0)}")
        print(f"   Processing: {data.get('is_processing', False)}")
        print()
    
    def handle_other(self, data: dict):
        """Handle other messages"""
        print(Colors.info("\n Message received:"))
        print(json.dumps(data, indent=2))
        print()
    
    def display_result_full(self, result: dict):
        """Display full result details"""
        
        # Metadata
        print(Colors.data("\n Metadata:"))
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Model: {result.get('model', 'N/A')}")
        print(f"   Capture ID: {result.get('capture_id', 'N/A')}")
        print(f"   Time: {self.format_timestamp(result.get('timestamp'))}")
        
        # Token usage
        if result.get('tokens_used'):
            print(Colors.data("\n Token Usage:"))
            print(f"   Total: {result.get('tokens_used', 'N/A')}")
            print(f"   Prompt: {result.get('prompt_tokens', 'N/A')}")
            print(f"   Completion: {result.get('completion_tokens', 'N/A')}")
        
        # Analysis
        analysis = result.get('analysis')
        if analysis:
            print(Colors.data("\n Analysis:"))
            print("─" * 67)
            
            # Format and display analysis
            lines = analysis.split('\n')
            for line in lines:
                if line.strip():
                    print(f"   {line}")
                else:
                    print()
            
            print("─" * 67)
    
    def display_result_compact(self, result: dict):
        """Display compact result"""
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Model: {result.get('model', 'N/A')}")
        print(f"   Time: {self.format_timestamp(result.get('timestamp'))}")
        
        analysis = result.get('analysis', '')
        if analysis:
            preview = analysis[:150] + "..." if len(analysis) > 150 else analysis
            print(f"   Preview: {preview}")
    
    def format_timestamp(self, timestamp: Optional[str]) -> str:
        """Format timestamp for display"""
        if not timestamp:
            return "N/A"
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    
    async def send_command(self, command: dict):
        """Send command to server"""
        if not self.websocket or not self.connected:
            print(Colors.error("Not connected to server"))
            return
        
        try:
            await self.websocket.send(json.dumps(command))
            print(Colors.success(f"Sent command: {command.get('action')}"))
        except Exception as e:
            print(Colors.error(f"Failed to send command: {e}"))
    
    async def run(self):
        """Main run loop"""
        if await self.connect():
            await self.listen()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point"""
    
    client = LLMProxyClient(WEBSOCKET_URL)
    client.print_banner()
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print()
        print()
        print(Colors.info("═" * 67))
        print(Colors.info("Shutting down client..."))
        print(Colors.info(f"Total messages received: {client.message_count}"))
        print(Colors.info("═" * 67))
        print()
        print(Colors.success(" Goodbye!"))
        print()


if __name__ == "__main__":
    # Check if SERVER_IP is configured
    if SERVER_IP == "192.168.1.100":
        print()
        print(Colors.warning("  SERVER_IP not configured!"))
        print()
        print("Please edit client.py and set SERVER_IP to your server's IP address")
        print()
        print("To find your server's IP:")
        print("  Windows: ipconfig")
        print("  Linux/Mac: ifconfig or hostname -I")
        print()
        
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
        print()
    
    try:
        asyncio.run(main())
    except Exception as e:
        print()
        print(Colors.error(f"Fatal error: {e}"))
        sys.exit(1)
