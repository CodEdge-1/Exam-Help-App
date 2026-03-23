"""
LAN LLM Proxy System - Phase 2
Version: 2.0.0
New: Mobile client, multiple prompts, history + search,
     voice readout, scheduled captures
"""

import asyncio
import base64
import io
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from pydantic import BaseModel
from PIL import ImageGrab
import keyboard
from openai import OpenAI

def get_local_ip():
    """Get the actual LAN IP address"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "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")
    OPENAI_MODEL    = "gpt-4o"
    MAX_TOKENS      = 1500
    API_TIMEOUT     = 30
    SERVER_HOST     = "0.0.0.0"
    SERVER_PORT     = 8000
    HOTKEY          = "ctrl+shift+x"
    IMAGE_FORMAT    = "PNG"
    SAVE_CAPTURES   = True
    SAVE_RESULTS    = True
    CAPTURES_DIR    = "./data/captures"
    RESULTS_DIR     = "./data/results"
    LOGS_DIR        = "./data/logs"
    PROMPTS_FILE    = "./data/prompts.json"
    MAX_RETRIES     = 3
    RETRY_DELAY     = 2
    LOG_LEVEL       = "INFO"
    LOG_TO_FILE     = True

config = Config()

# ============================================================================
# DEFAULT PROMPT LIBRARY
# ============================================================================

DEFAULT_PROMPTS = [
    {
        "id": "qa",
        "name": "Answer Question",
        "icon": "?",
        "description": "Finds and answers any question on screen",
        "prompt": """You are a smart assistant. Look at this screen and:
1. If there is a QUESTION on screen, answer it directly and clearly.
2. If there is a TASK or INSTRUCTION, complete it directly.
3. If there is TEXT to analyze, analyze it directly.
4. If no clear question, summarize the main content.
IMPORTANT: Plain conversational text only. No headers like ###, no labels like Model: or Tokens:. No mention of the screen, app, file name, taskbar, or UI. Just answer naturally."""
    },
    {
        "id": "summarize",
        "name": "Summarize",
        "icon": "S",
        "description": "Summarizes all text on screen into key points",
        "prompt": """Summarize the main content visible on this screen into clear, concise bullet points. Focus only on the actual content — ignore the taskbar, clock, system tray, or any UI chrome. Do not mention the application or file name. Plain text only, no markdown headers."""
    },
    {
        "id": "translate",
        "name": "Translate to English",
        "icon": "T",
        "description": "Translates any foreign text on screen to English",
        "prompt": """Translate all non-English text visible on this screen to English. If the text is already in English, just return it as-is. Only return the translated text — no explanations, no descriptions of the screen."""
    },
    {
        "id": "explain",
        "name": "Explain Simply",
        "icon": "E",
        "description": "Explains complex content in simple terms",
        "prompt": """Look at the content on this screen and explain it in very simple, easy-to-understand language as if explaining to someone with no background knowledge. Focus only on the content, not the application or interface. Keep it conversational and clear."""
    },
    {
        "id": "extract",
        "name": "Extract Data",
        "icon": "D",
        "description": "Extracts key data, numbers, and facts",
        "prompt": """Extract all important data, numbers, facts, names, and dates visible on this screen. Present them in a clean, organized list. Ignore UI elements like taskbar, title bar, and system tray. Focus only on the actual content data."""
    },
    {
        "id": "proofread",
        "name": "Proofread",
        "icon": "P",
        "description": "Checks text for grammar and spelling errors",
        "prompt": """Proofread the text visible on this screen. List any grammar, spelling, or punctuation errors you find, and provide the corrected version. If the text is correct, say so. Focus only on the document content, not the application UI."""
    }
]

# ============================================================================
# LOGGING
# ============================================================================

def setup_logging():
    Path(config.LOGS_DIR).mkdir(parents=True, exist_ok=True)
    fmt_file    = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fmt_console = logging.Formatter('%(levelname)s: %(message)s')
    root = logging.getLogger()
    root.setLevel(getattr(logging, config.LOG_LEVEL))
    try:
        utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                errors='replace', line_buffering=True)
        ch = logging.StreamHandler(utf8)
    except Exception:
        ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt_console)
    root.addHandler(ch)
    if config.LOG_TO_FILE:
        fh = logging.FileHandler(
            os.path.join(config.LOGS_DIR,
                         f"llm_proxy_{datetime.now().strftime('%Y%m%d')}.log"),
            encoding='utf-8')
        fh.setFormatter(fmt_file)
        root.addHandler(fh)
    return root

logger = setup_logging()

# ============================================================================
# MODELS
# ============================================================================

class CaptureRequest(BaseModel):
    prompt: Optional[str] = None
    prompt_id: Optional[str] = None

class CaptureResult(BaseModel):
    status: str
    analysis: Optional[str]  = None
    error: Optional[str]     = None
    model: Optional[str]     = None
    tokens_used: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    timestamp: str
    capture_id: Optional[str] = None
    prompt_name: Optional[str] = None

class PromptCreate(BaseModel):
    name: str
    icon: Optional[str] = "+"
    description: Optional[str] = ""
    prompt: str

class ScheduleRequest(BaseModel):
    enabled: bool
    interval_minutes: int = 5
    prompt_id: Optional[str] = "qa"

# ============================================================================
# PROMPT MANAGER
# ============================================================================

class PromptManager:
    def __init__(self):
        Path("./data").mkdir(parents=True, exist_ok=True)
        if not os.path.exists(config.PROMPTS_FILE):
            self._save(DEFAULT_PROMPTS)
        self.prompts = self._load()

    def _load(self):
        with open(config.PROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self, data):
        with open(config.PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all(self):
        return self.prompts

    def get_by_id(self, pid: str):
        return next((p for p in self.prompts if p['id'] == pid), None)

    def get_prompt_text(self, pid: str):
        p = self.get_by_id(pid)
        return p['prompt'] if p else DEFAULT_PROMPTS[0]['prompt']

    def add(self, data: dict):
        data['id'] = f"custom_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.prompts.append(data)
        self._save(self.prompts)
        return data

    def delete(self, pid: str):
        self.prompts = [p for p in self.prompts if p['id'] != pid]
        self._save(self.prompts)

# ============================================================================
# HISTORY MANAGER
# ============================================================================

class HistoryManager:
    def __init__(self):
        Path(config.RESULTS_DIR).mkdir(parents=True, exist_ok=True)

    def save(self, result: dict):
        filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        filepath = os.path.join(config.RESULTS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def get_all(self, limit=50):
        files = sorted(
            Path(config.RESULTS_DIR).glob("*.json"),
            key=lambda x: x.stat().st_mtime, reverse=True
        )[:limit]
        results = []
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    results.append(json.load(fp))
            except Exception:
                pass
        return results

    def search(self, query: str, limit=50):
        all_results = self.get_all(limit=200)
        q = query.lower()
        return [r for r in all_results
                if q in (r.get('analysis') or '').lower()
                or q in (r.get('prompt_name') or '').lower()
                ][:limit]

    def clear(self):
        for f in Path(config.RESULTS_DIR).glob("*.json"):
            f.unlink()

# ============================================================================
# SCHEDULER
# ============================================================================

class Scheduler:
    def __init__(self):
        self.enabled   = False
        self.interval  = 5
        self.prompt_id = "qa"
        self._task: Optional[asyncio.Task] = None

    def configure(self, enabled: bool, interval: int, prompt_id: str):
        self.enabled   = enabled
        self.interval  = max(1, interval)
        self.prompt_id = prompt_id

    async def _loop(self):
        logger.info(f"Scheduler started: every {self.interval} minute(s)")
        while self.enabled:
            await asyncio.sleep(self.interval * 60)
            if self.enabled:
                logger.info("Scheduler: triggering capture...")
                await trigger_capture_handler(self.prompt_id)

    def start(self, loop):
        if self._task:
            self._task.cancel()
        self._task = asyncio.run_coroutine_threadsafe(self._loop(), loop)

    def stop(self):
        self.enabled = False
        if self._task:
            try:
                self._task.cancel()
            except Exception:
                pass

# ============================================================================
# SCREEN CAPTURE SYSTEM
# ============================================================================

class ScreenCaptureSystem:
    def __init__(self):
        self.is_processing    = False
        self.capture_count    = 0
        self.start_time       = datetime.now()
        self.last_capture_time = None
        self.client           = OpenAI(api_key=config.OPENAI_API_KEY)
        Path(config.CAPTURES_DIR).mkdir(parents=True, exist_ok=True)

    def capture_screen(self) -> bytes:
        logger.info("Capturing screen...")
        screenshot = ImageGrab.grab()
        buf = io.BytesIO()
        screenshot.save(buf, format=config.IMAGE_FORMAT)
        buf.seek(0)
        image_bytes = buf.getvalue()
        if config.SAVE_CAPTURES:
            self.capture_count += 1
            fname = f"capture_{self.capture_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(os.path.join(config.CAPTURES_DIR, fname), 'wb') as f:
                f.write(image_bytes)
        return image_bytes

    async def process_with_openai(self, image_bytes: bytes, prompt: str,
                                   prompt_name: str = "") -> CaptureResult:
        retries, last_error = 0, None
        while retries <= config.MAX_RETRIES:
            try:
                logger.info(f"Sending to OpenAI (attempt {retries+1})...")
                b64 = base64.b64encode(image_bytes).decode('utf-8')
                resp = self.client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/png;base64,{b64}"}}
                    ]}],
                    max_tokens=config.MAX_TOKENS,
                    timeout=config.API_TIMEOUT
                )
                result = CaptureResult(
                    status="success",
                    analysis=resp.choices[0].message.content,
                    model=resp.model,
                    tokens_used=resp.usage.total_tokens,
                    prompt_tokens=resp.usage.prompt_tokens,
                    completion_tokens=resp.usage.completion_tokens,
                    timestamp=datetime.now().isoformat(),
                    capture_id=f"cap_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    prompt_name=prompt_name
                )
                logger.info(f"Done. Tokens: {resp.usage.total_tokens}")
                history_manager.save(result.dict())
                return result
            except Exception as e:
                last_error = str(e)
                retries += 1
                logger.error(f"OpenAI error: {e}")
                if retries <= config.MAX_RETRIES:
                    await asyncio.sleep(config.RETRY_DELAY)
        return CaptureResult(status="error", error=last_error,
                             timestamp=datetime.now().isoformat())

    async def process_capture(self, prompt_id="qa",
                               custom_prompt=None) -> CaptureResult:
        if self.is_processing:
            return CaptureResult(status="error",
                                 error="Already processing, please wait",
                                 timestamp=datetime.now().isoformat())
        self.is_processing = True
        try:
            p_obj = prompt_manager.get_by_id(prompt_id)
            prompt_text = custom_prompt or \
                          (p_obj['prompt'] if p_obj else DEFAULT_PROMPTS[0]['prompt'])
            prompt_name = p_obj['name'] if p_obj else "Custom"
            image_bytes = self.capture_screen()
            result = await self.process_with_openai(image_bytes, prompt_text, prompt_name)
            self.last_capture_time = datetime.now()
            return result
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return CaptureResult(status="error", error=str(e),
                                 timestamp=datetime.now().isoformat())
        finally:
            self.is_processing = False

    def get_stats(self):
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            "total_captures": self.capture_count,
            "connected_clients": len(connected_clients),
            "is_processing": self.is_processing,
            "uptime_seconds": uptime,
            "scheduler_enabled": scheduler.enabled,
            "scheduler_interval": scheduler.interval,
	    "server_ip": get_local_ip(), 
            "last_capture": self.last_capture_time.isoformat()
                            if self.last_capture_time else None
        }

# ============================================================================
# APP + GLOBAL STATE
# ============================================================================

app = FastAPI(title="LAN LLM Proxy System", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

prompt_manager  = PromptManager()
history_manager = HistoryManager()
scheduler       = Scheduler()
capture_system  = ScreenCaptureSystem()
connected_clients: List[WebSocket] = []
latest_result: Optional[CaptureResult] = None
active_prompt_id = "qa"
main_event_loop  = None

# ============================================================================
# BROADCAST + HOTKEY
# ============================================================================

async def broadcast(data: dict):
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)

async def trigger_capture_handler(prompt_id=None):
    global latest_result
    pid = prompt_id or active_prompt_id
    result = await capture_system.process_capture(prompt_id=pid)
    latest_result = result
    await broadcast({**result.dict(), "active_prompt": pid})

def setup_hotkey():
    def on_hotkey():
        logger.info(f"Hotkey pressed! Capturing with prompt: {active_prompt_id}")
        if main_event_loop:
            asyncio.run_coroutine_threadsafe(
                trigger_capture_handler(), main_event_loop)
    try:
        keyboard.add_hotkey(config.HOTKEY, on_hotkey)
        logger.info(f"Hotkey '{config.HOTKEY}' registered")
        return True
    except Exception as e:
        logger.error(f"Hotkey failed: {e}")
        return False

# ============================================================================
# DESKTOP DASHBOARD HTML
# ============================================================================

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html>
<head>
<title>LAN LLM Proxy v2</title>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f0f1a;color:#e2e8f0;min-height:100vh}
.sidebar{position:fixed;left:0;top:0;width:220px;height:100vh;background:#1a1a2e;padding:20px 0;border-right:1px solid #2d2d44;overflow-y:auto}
.logo{padding:0 20px 20px;border-bottom:1px solid #2d2d44;margin-bottom:16px}
.logo h1{font-size:16px;font-weight:700;color:#fff}
.logo p{font-size:11px;color:#8892b0;margin-top:2px}
.nav-section{padding:0 12px;margin-bottom:8px}
.nav-label{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#4a5568;padding:0 8px;margin-bottom:6px}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;cursor:pointer;font-size:13px;color:#a0aec0;transition:.15s;border:none;background:none;width:100%;text-align:left}
.nav-item:hover{background:#2d2d44;color:#fff}
.nav-item.active{background:#4f46e5;color:#fff}
.nav-icon{width:20px;text-align:center;font-size:14px}
.main{margin-left:220px;padding:24px;min-height:100vh}
.page{display:none}.page.active{display:block}
.page-title{font-size:20px;font-weight:700;color:#fff;margin-bottom:6px}
.page-sub{font-size:13px;color:#8892b0;margin-bottom:24px}

/* Stats */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
.stat-card{background:#1a1a2e;border-radius:10px;padding:16px 20px;border:1px solid #2d2d44}
.stat-label{font-size:11px;color:#8892b0;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.stat-value{font-size:22px;font-weight:700;color:#fff}
.stat-sub{font-size:11px;color:#4a5568;margin-top:3px}

/* Answer card */
.answer-card{background:#1a1a2e;border-radius:12px;border:1px solid #2d2d44;overflow:hidden;margin-bottom:20px}
.answer-header{background:#16213e;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #2d2d44}
.answer-header h2{font-size:14px;font-weight:600;color:#fff}
.answer-meta{font-size:11px;color:#8892b0}
.answer-body{padding:22px}
.answer-text{font-size:14px;line-height:1.85;color:#e2e8f0}
.answer-text h1,.answer-text h2,.answer-text h3{color:#fff;margin:12px 0 6px}
.answer-text strong{color:#fff}
.answer-text ul,.answer-text ol{padding-left:20px;margin:6px 0}
.answer-text li{margin:3px 0}
.answer-text code{background:#0f0f1a;padding:2px 6px;border-radius:4px;font-size:12px;font-family:monospace;color:#a78bfa}
.empty-state{text-align:center;padding:50px 20px;color:#4a5568}
.empty-icon{font-size:40px;margin-bottom:12px}
.empty-state h3{color:#8892b0;font-size:15px;margin-bottom:6px}
.empty-state p{font-size:13px}
.spinner{width:32px;height:32px;border:3px solid #2d2d44;border-top-color:#4f46e5;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-state{text-align:center;padding:40px}
.error-box{background:#2d1515;border:1px solid #7f1d1d;border-radius:8px;padding:14px 18px;color:#fca5a5;font-size:13px}

/* Prompts */
.prompts-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.prompt-card{background:#1a1a2e;border:2px solid #2d2d44;border-radius:10px;padding:16px;cursor:pointer;transition:.15s;position:relative}
.prompt-card:hover{border-color:#4f46e5;background:#1e1e35}
.prompt-card.active{border-color:#4f46e5;background:#1e1e35}
.prompt-card.active::after{content:'ACTIVE';position:absolute;top:10px;right:10px;font-size:9px;background:#4f46e5;color:#fff;padding:2px 6px;border-radius:4px;font-weight:700}
.prompt-icon{font-size:22px;margin-bottom:8px;width:36px;height:36px;background:#2d2d44;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:700;color:#a78bfa}
.prompt-name{font-size:13px;font-weight:600;color:#fff;margin-bottom:4px}
.prompt-desc{font-size:11px;color:#8892b0;line-height:1.4}
.prompt-delete{position:absolute;bottom:8px;right:10px;background:none;border:none;color:#4a5568;cursor:pointer;font-size:16px;padding:2px 6px;border-radius:4px;transition:.15s}
.prompt-delete:hover{color:#fc8181;background:#2d2d44}

/* Add prompt form */
.form-card{background:#1a1a2e;border-radius:12px;border:1px solid #2d2d44;padding:20px;margin-bottom:20px}
.form-card h3{font-size:14px;font-weight:600;color:#fff;margin-bottom:14px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.form-group{display:flex;flex-direction:column;gap:6px}
.form-group label{font-size:11px;color:#8892b0;text-transform:uppercase;letter-spacing:.5px}
.form-group input,.form-group textarea{background:#0f0f1a;border:1px solid #2d2d44;border-radius:6px;padding:8px 12px;color:#e2e8f0;font-size:13px;font-family:inherit;outline:none;transition:.15s}
.form-group input:focus,.form-group textarea:focus{border-color:#4f46e5}
.form-group textarea{resize:vertical;min-height:100px}

/* History */
.search-bar{display:flex;gap:10px;margin-bottom:16px}
.search-bar input{flex:1;background:#1a1a2e;border:1px solid #2d2d44;border-radius:8px;padding:10px 16px;color:#e2e8f0;font-size:13px;outline:none}
.search-bar input:focus{border-color:#4f46e5}
.history-list{display:flex;flex-direction:column;gap:10px}
.history-item{background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:16px;cursor:pointer;transition:.15s}
.history-item:hover{border-color:#4f46e5}
.history-meta{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.history-badge{font-size:10px;background:#2d2d44;color:#a78bfa;padding:2px 8px;border-radius:4px;font-weight:600}
.history-time{font-size:11px;color:#4a5568}
.history-preview{font-size:13px;color:#8892b0;line-height:1.5;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.history-full{display:none;margin-top:10px;padding-top:10px;border-top:1px solid #2d2d44;font-size:13px;color:#e2e8f0;line-height:1.7}
.history-item.expanded .history-full{display:block}
.history-item.expanded .history-preview{display:none}

/* Schedule */
.schedule-card{background:#1a1a2e;border-radius:12px;border:1px solid #2d2d44;padding:22px;margin-bottom:16px}
.schedule-card h3{font-size:14px;font-weight:600;color:#fff;margin-bottom:16px}
.toggle-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.toggle-label{font-size:13px;color:#e2e8f0}
.toggle{position:relative;width:44px;height:24px}
.toggle input{opacity:0;width:0;height:0}
.slider{position:absolute;inset:0;background:#2d2d44;border-radius:24px;cursor:pointer;transition:.3s}
.slider:before{content:'';position:absolute;width:18px;height:18px;left:3px;top:3px;background:#8892b0;border-radius:50%;transition:.3s}
input:checked+.slider{background:#4f46e5}
input:checked+.slider:before{transform:translateX(20px);background:#fff}
.interval-row{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.interval-row label{font-size:13px;color:#8892b0;min-width:80px}
.interval-row input[type=number]{width:80px;background:#0f0f1a;border:1px solid #2d2d44;border-radius:6px;padding:7px 10px;color:#e2e8f0;font-size:13px;outline:none}
.interval-row span{font-size:13px;color:#8892b0}
.schedule-status{font-size:12px;padding:8px 14px;border-radius:6px;display:inline-block}
.schedule-status.on{background:#1a2e1a;color:#6ee7b7;border:1px solid #064e3b}
.schedule-status.off{background:#1a1a2e;color:#4a5568;border:1px solid #2d2d44}

/* Buttons */
.btn{padding:9px 18px;border:none;border-radius:7px;font-size:13px;font-weight:600;cursor:pointer;transition:.15s;display:inline-flex;align-items:center;gap:6px}
.btn-primary{background:#4f46e5;color:#fff}
.btn-primary:hover{background:#4338ca}
.btn-danger{background:#7f1d1d;color:#fca5a5}
.btn-danger:hover{background:#991b1b}
.btn-ghost{background:#2d2d44;color:#a0aec0}
.btn-ghost:hover{background:#3d3d54;color:#fff}
.btn:disabled{opacity:.4;cursor:not-allowed}

/* Voice toggle */
.voice-row{display:flex;align-items:center;gap:10px;margin-top:10px}
.voice-row label{font-size:12px;color:#8892b0}

/* Connection badge */
.conn-dot{width:8px;height:8px;border-radius:50%;background:#ef4444;display:inline-block;margin-right:6px}
.conn-dot.ok{background:#10b981}

/* Scrollbar */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:#0f0f1a}
::-webkit-scrollbar-thumb{background:#2d2d44;border-radius:3px}

/* Mobile link banner */
.mobile-banner{background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:14px 18px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
.mobile-banner p{font-size:13px;color:#8892b0}
.mobile-banner strong{color:#a78bfa}
.mobile-url{font-size:12px;color:#4f46e5;font-family:monospace;background:#0f0f1a;padding:4px 10px;border-radius:4px}
</style>
</head>
<body>

<!-- Sidebar -->
<div class="sidebar">
  <div class="logo">
    <h1>LAN LLM Proxy</h1>
    <p><span class="conn-dot" id="connDot"></span><span id="connText">Connecting...</span></p>
  </div>
  <div class="nav-section">
    <div class="nav-label">Main</div>
    <button class="nav-item active" onclick="showPage('dashboard',this)">
      <span class="nav-icon">&#x2302;</span> Dashboard
    </button>
    <button class="nav-item" onclick="showPage('prompts',this)">
      <span class="nav-icon">&#x270E;</span> Prompts
    </button>
    <button class="nav-item" onclick="showPage('history',this)">
      <span class="nav-icon">&#x23F3;</span> History
    </button>
    <button class="nav-item" onclick="showPage('schedule',this)">
      <span class="nav-icon">&#x23F0;</span> Schedule
    </button>
  </div>
  <div class="nav-section" style="margin-top:auto;padding-top:20px">
    <div class="nav-label">Active Prompt</div>
    <div id="sidebarPrompt" style="padding:8px 12px;font-size:12px;color:#a78bfa;background:#1e1e35;border-radius:8px;margin:0 0 8px">
      Answer Question
    </div>
    <div class="nav-label" style="margin-top:12px">Hotkey</div>
    <div style="padding:8px 12px;font-size:12px;color:#6b7280;font-family:monospace">
      Ctrl+Shift+X
    </div>
  </div>
</div>

<!-- Main content -->
<div class="main">

  <!-- DASHBOARD PAGE -->
  <div class="page active" id="page-dashboard">
    <div class="page-title">Dashboard</div>
    <div class="page-sub">Latest capture result and system status</div>

    <div class="mobile-banner">
      <p>Mobile client: open <strong id="mobileUrl">http://YOUR_IP:8000/mobile</strong> on your phone</p>
      <span class="mobile-url" id="mobileUrlBadge">loading...</span>
    </div>

    <div class="stats">
      <div class="stat-card">
        <div class="stat-label">Total Captures</div>
        <div class="stat-value" id="totalCaptures">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Clients Connected</div>
        <div class="stat-value" id="connClients">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Uptime</div>
        <div class="stat-value" id="uptime">0s</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Scheduler</div>
        <div class="stat-value" id="schedulerStat" style="font-size:14px">Off</div>
      </div>
    </div>

    <div class="answer-card">
      <div class="answer-header">
        <h2>Answer / Analysis</h2>
        <div style="display:flex;align-items:center;gap:12px">
          <div class="voice-row">
            <label style="color:#8892b0;font-size:12px">Voice</label>
            <label class="toggle" title="Read answer aloud">
              <input type="checkbox" id="voiceToggle" onchange="toggleVoice()">
              <span class="slider"></span>
            </label>
          </div>
          <span class="answer-meta" id="lastUpdate"></span>
        </div>
      </div>
      <div class="answer-body" id="answerBody">
        <div class="empty-state">
          <div class="empty-icon">&#x1F4F8;</div>
          <h3>No captures yet</h3>
          <p>Press <strong>Ctrl+Shift+X</strong> to capture your screen</p>
        </div>
      </div>
    </div>
  </div>

  <!-- PROMPTS PAGE -->
  <div class="page" id="page-prompts">
    <div class="page-title">Prompts</div>
    <div class="page-sub">Choose what the AI should do with your screen captures</div>

    <div class="prompts-grid" id="promptsGrid"></div>

    <div class="form-card">
      <h3>+ Add Custom Prompt</h3>
      <div class="form-row">
        <div class="form-group">
          <label>Name</label>
          <input type="text" id="newPromptName" placeholder="e.g. Code Review">
        </div>
        <div class="form-group">
          <label>Icon (letter or emoji)</label>
          <input type="text" id="newPromptIcon" placeholder="e.g. C" maxlength="2">
        </div>
      </div>
      <div class="form-group" style="margin-bottom:12px">
        <label>Description</label>
        <input type="text" id="newPromptDesc" placeholder="Short description of what this prompt does">
      </div>
      <div class="form-group" style="margin-bottom:14px">
        <label>Prompt Instructions</label>
        <textarea id="newPromptText" placeholder="Write your AI instructions here..."></textarea>
      </div>
      <button class="btn btn-primary" onclick="addPrompt()">Save Prompt</button>
    </div>
  </div>

  <!-- HISTORY PAGE -->
  <div class="page" id="page-history">
    <div class="page-title">History</div>
    <div class="page-sub">All past captures and answers — stored locally</div>

    <div class="search-bar">
      <input type="text" id="searchInput" placeholder="Search history..." oninput="searchHistory()">
      <button class="btn btn-ghost" onclick="loadHistory()">Refresh</button>
      <button class="btn btn-danger" onclick="clearHistory()">Clear All</button>
    </div>

    <div class="history-list" id="historyList">
      <div style="text-align:center;color:#4a5568;padding:40px">Loading history...</div>
    </div>
  </div>

  <!-- SCHEDULE PAGE -->
  <div class="page" id="page-schedule">
    <div class="page-title">Scheduler</div>
    <div class="page-sub">Automatically capture screen at set intervals</div>

    <div class="schedule-card">
      <h3>Automatic Capture</h3>

      <div class="toggle-row">
        <span class="toggle-label">Enable automatic captures</span>
        <label class="toggle">
          <input type="checkbox" id="scheduleToggle" onchange="saveSchedule()">
          <span class="slider"></span>
        </label>
      </div>

      <div class="interval-row">
        <label>Every</label>
        <input type="number" id="scheduleInterval" value="5" min="1" max="120"
               onchange="saveSchedule()">
        <span>minutes</span>
      </div>

      <div class="form-group" style="margin-bottom:16px">
        <label>Use Prompt</label>
        <select id="schedulePromptSelect"
                style="background:#0f0f1a;border:1px solid #2d2d44;border-radius:6px;padding:8px 12px;color:#e2e8f0;font-size:13px;outline:none"
                onchange="saveSchedule()">
        </select>
      </div>

      <div id="scheduleStatus" class="schedule-status off">Scheduler is OFF</div>
    </div>

    <div class="form-card">
      <h3>How it works</h3>
      <p style="font-size:13px;color:#8892b0;line-height:1.7">
        When enabled, the system automatically captures your screen at the chosen interval and sends it to the AI using the selected prompt. Results are broadcast to all connected devices and saved to history.<br><br>
        <strong style="color:#a78bfa">Tip:</strong> Use "Summarize" prompt for regular monitoring, or "Extract Data" for tracking numbers on a dashboard.
      </p>
    </div>
  </div>

</div>

<script>
let ws, voiceEnabled=false, activePromptId='qa', allPrompts=[];

// ---- Navigation ----
function showPage(id, btn) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.getElementById('page-'+id).classList.add('active');
  btn.classList.add('active');
  if(id==='history') loadHistory();
  if(id==='schedule') loadSchedulePrompts();
}

// ---- WebSocket ----
function connect() {
  ws = new WebSocket('ws://'+location.host+'/ws');
  ws.onopen = () => { setConn(true); refreshStats(); };
  ws.onmessage = e => handle(JSON.parse(e.data));
  ws.onclose = () => { setConn(false); setTimeout(connect,3000); };
}

function setConn(ok) {
  document.getElementById('connDot').className = 'conn-dot'+(ok?' ok':'');
  document.getElementById('connText').textContent = ok ? 'Connected' : 'Reconnecting...';
}

function handle(d) {
  if(d.type==='connection') {
    if(d.latest_result && d.latest_result.status==='success') showAnswer(d.latest_result);
  } else if(d.status==='success') {
    showAnswer(d);
    refreshStats();
  } else if(d.status==='error') {
    showError(d.error);
  } else if(d.type==='stats') {
    updateStats(d);
  }
}

// ---- Answer display ----
function showAnswer(r) {
  document.getElementById('lastUpdate').textContent =
    new Date(r.timestamp).toLocaleTimeString() + (r.prompt_name ? ' · '+r.prompt_name : '');
  document.getElementById('answerBody').innerHTML =
    '<div class="answer-text">'+renderMD(r.analysis||'')+'</div>';
  if(voiceEnabled && r.analysis) speak(r.analysis);
}
function showError(msg) {
  document.getElementById('answerBody').innerHTML =
    '<div class="error-box"><strong>Error:</strong> '+msg+'</div>';
}
function showLoading() {
  document.getElementById('answerBody').innerHTML =
    '<div class="loading-state"><div class="spinner"></div><p style="color:#8892b0;font-size:13px">Analyzing screen...</p></div>';
}
function renderMD(t) {
  return t
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/^### (.+)$/gm,'<h3>$1</h3>')
    .replace(/^## (.+)$/gm,'<h2>$1</h2>')
    .replace(/^# (.+)$/gm,'<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/^- (.+)$/gm,'<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm,'<li>$2</li>')
    .replace(/\n\n/g,'<br><br>').replace(/\n/g,'<br>');
}

// ---- Voice ----
function toggleVoice() {
  voiceEnabled = document.getElementById('voiceToggle').checked;
  if(!voiceEnabled) speechSynthesis.cancel();
}
function speak(text) {
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/<[^>]*>/g,''));
  u.rate = 0.95; u.pitch = 1;
  speechSynthesis.speak(u);
}

// ---- Stats ----
async function refreshStats() {
  try { updateStats(await (await fetch('/stats')).json()); } catch(e){}
}
function updateStats(s) {
  document.getElementById('totalCaptures').textContent = s.total_captures||0;
  document.getElementById('connClients').textContent   = s.connected_clients||0;
  const u=s.uptime_seconds||0;
  document.getElementById('uptime').textContent =
    Math.floor(u/3600)+'h '+Math.floor((u%3600)/60)+'m '+Math.floor(u%60)+'s';
  document.getElementById('schedulerStat').textContent =
    s.scheduler_enabled ? 'Every '+s.scheduler_interval+'m' : 'Off';
  document.getElementById('schedulerStat').style.color =
    s.scheduler_enabled ? '#6ee7b7' : '#4a5568';
}

// ---- Prompts ----
async function loadPrompts() {
  const r = await fetch('/prompts');
  allPrompts = await r.json();
  renderPrompts();
  loadSchedulePrompts();
}
function renderPrompts() {
  const grid = document.getElementById('promptsGrid');
  grid.innerHTML = allPrompts.map(p => `
    <div class="prompt-card${p.id===activePromptId?' active':''}" onclick="setPrompt('${p.id}',this)">
      <div class="prompt-icon">${p.icon||'?'}</div>
      <div class="prompt-name">${p.name}</div>
      <div class="prompt-desc">${p.description||''}</div>
      ${p.id.startsWith('custom_') ?
        `<button class="prompt-delete" onclick="event.stopPropagation();deletePrompt('${p.id}')">&#x2715;</button>` : ''}
    </div>`).join('');
}
async function setPrompt(id, card) {
  activePromptId = id;
  await fetch('/active-prompt', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({prompt_id:id})});
  document.querySelectorAll('.prompt-card').forEach(c=>c.classList.remove('active'));
  card.classList.add('active');
  const p = allPrompts.find(x=>x.id===id);
  if(p) document.getElementById('sidebarPrompt').textContent = p.name;
}
async function addPrompt() {
  const name  = document.getElementById('newPromptName').value.trim();
  const icon  = document.getElementById('newPromptIcon').value.trim() || '+';
  const desc  = document.getElementById('newPromptDesc').value.trim();
  const prompt= document.getElementById('newPromptText').value.trim();
  if(!name||!prompt){alert('Please fill in Name and Prompt fields');return;}
  await fetch('/prompts',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name,icon,description:desc,prompt})});
  document.getElementById('newPromptName').value='';
  document.getElementById('newPromptIcon').value='';
  document.getElementById('newPromptDesc').value='';
  document.getElementById('newPromptText').value='';
  await loadPrompts();
}
async function deletePrompt(id) {
  if(!confirm('Delete this prompt?')) return;
  await fetch('/prompts/'+id,{method:'DELETE'});
  await loadPrompts();
}

// ---- History ----
async function loadHistory() {
  const r = await fetch('/history?limit=50');
  const d = await r.json();
  renderHistory(d.results||[]);
}
async function searchHistory() {
  const q = document.getElementById('searchInput').value.trim();
  if(!q){loadHistory();return;}
  const r = await fetch('/history/search?q='+encodeURIComponent(q));
  const d = await r.json();
  renderHistory(d.results||[]);
}
function renderHistory(items) {
  const el = document.getElementById('historyList');
  if(!items.length){
    el.innerHTML='<div style="text-align:center;color:#4a5568;padding:40px">No results found</div>';
    return;
  }
  el.innerHTML = items.map(r=>`
    <div class="history-item" onclick="this.classList.toggle('expanded')">
      <div class="history-meta">
        <span class="history-badge">${r.prompt_name||'Answer'}</span>
        <span class="history-time">${r.timestamp ? new Date(r.timestamp).toLocaleString() : ''}</span>
      </div>
      <div class="history-preview">${(r.analysis||'').replace(/<[^>]*>/g,'').substring(0,150)}...</div>
      <div class="history-full">${renderMD(r.analysis||'')}</div>
    </div>`).join('');
}
async function clearHistory() {
  if(!confirm('Clear ALL history? This cannot be undone.')) return;
  await fetch('/history',{method:'DELETE'});
  loadHistory();
}

// ---- Schedule ----
function loadSchedulePrompts() {
  const sel = document.getElementById('schedulePromptSelect');
  if(!sel) return;
  sel.innerHTML = allPrompts.map(p=>
    `<option value="${p.id}">${p.name}</option>`).join('');
}
async function saveSchedule() {
  const enabled  = document.getElementById('scheduleToggle').checked;
  const interval = parseInt(document.getElementById('scheduleInterval').value)||5;
  const pid      = document.getElementById('schedulePromptSelect').value||'qa';
  await fetch('/schedule',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({enabled,interval_minutes:interval,prompt_id:pid})});
  const el = document.getElementById('scheduleStatus');
  el.className = 'schedule-status '+(enabled?'on':'off');
  el.textContent = enabled ?
    `Scheduler ON - capturing every ${interval} minute(s)` : 'Scheduler is OFF';
  refreshStats();
}

// ---- Mobile URL ----
async function setMobileUrl() {
  try {
    const s = await (await fetch('/stats')).json();
    if(s.server_ip) {
      const url = 'http://'+s.server_ip+':8000/mobile';
      document.getElementById('mobileUrl').textContent = url;
      document.getElementById('mobileUrlBadge').textContent = url;
    }
  } catch(e) {}
}
// ---- Init ----
connect();
loadPrompts();
setMobileUrl();
setInterval(refreshStats, 10000);
setInterval(setMobileUrl, 5000);
</script>
</body>
</html>"""


# ============================================================================
# MOBILE CLIENT HTML
# ============================================================================

MOBILE_HTML = r"""<!DOCTYPE html>
<html>
<head>
<title>LLM Proxy - Mobile</title>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0f0f1a">
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f0f1a;color:#e2e8f0;min-height:100vh;padding-bottom:80px}

.topbar{background:#1a1a2e;padding:14px 18px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10;border-bottom:1px solid #2d2d44}
.topbar h1{font-size:16px;font-weight:700;color:#fff}
.conn-pill{font-size:11px;padding:4px 10px;border-radius:20px;font-weight:600}
.conn-pill.ok{background:#064e3b;color:#6ee7b7}
.conn-pill.err{background:#7f1d1d;color:#fca5a5}

.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:14px}
.stat{background:#1a1a2e;border-radius:10px;padding:12px 10px;text-align:center;border:1px solid #2d2d44}
.stat-val{font-size:20px;font-weight:700;color:#fff}
.stat-lbl{font-size:10px;color:#8892b0;margin-top:3px;text-transform:uppercase}

.answer-wrap{padding:0 14px}
.answer-card{background:#1a1a2e;border-radius:12px;border:1px solid #2d2d44;overflow:hidden}
.card-hdr{background:#16213e;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #2d2d44}
.card-hdr h2{font-size:13px;font-weight:600;color:#fff}
.card-time{font-size:11px;color:#8892b0}
.card-body{padding:18px}
.answer-text{font-size:14px;line-height:1.85;color:#e2e8f0}
.answer-text h1,.answer-text h2,.answer-text h3{color:#fff;margin:10px 0 5px}
.answer-text strong{color:#fff}
.answer-text ul,.answer-text ol{padding-left:18px;margin:6px 0}
.answer-text li{margin:3px 0}
.answer-text code{background:#0f0f1a;padding:2px 5px;border-radius:3px;font-size:12px;color:#a78bfa}

.empty{text-align:center;padding:40px 16px;color:#4a5568}
.empty-icon{font-size:38px;margin-bottom:10px}
.empty h3{color:#8892b0;font-size:14px;margin-bottom:5px}
.empty p{font-size:12px}

.spinner{width:28px;height:28px;border:3px solid #2d2d44;border-top-color:#4f46e5;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 10px}
@keyframes spin{to{transform:rotate(360deg)}}
.loading{text-align:center;padding:32px}

.error-box{background:#2d1515;border:1px solid #7f1d1d;border-radius:8px;padding:12px 16px;color:#fca5a5;font-size:13px}

.bottom-bar{position:fixed;bottom:0;left:0;right:0;background:#1a1a2e;border-top:1px solid #2d2d44;padding:10px 14px;display:flex;gap:10px}
.btn{flex:1;padding:12px;border:none;border-radius:9px;font-size:14px;font-weight:600;cursor:pointer;transition:.15s}
.btn-primary{background:#4f46e5;color:#fff}
.btn-ghost{background:#2d2d44;color:#a0aec0}
.btn:active{opacity:.7;transform:scale(.98)}
.btn:disabled{opacity:.4}

.prompt-chips{display:flex;gap:8px;padding:10px 14px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.prompt-chips::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;padding:6px 14px;border-radius:20px;border:1px solid #2d2d44;background:#1a1a2e;color:#8892b0;font-size:12px;font-weight:600;cursor:pointer;transition:.15s}
.chip.active{background:#4f46e5;border-color:#4f46e5;color:#fff}

.notif{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#4f46e5;color:#fff;padding:8px 18px;border-radius:20px;font-size:13px;font-weight:600;opacity:0;transition:.3s;pointer-events:none;white-space:nowrap;z-index:100}
.notif.show{opacity:1}
</style>
</head>
<body>

<div class="topbar">
  <h1>LLM Proxy</h1>
  <span class="conn-pill err" id="connPill">Connecting</span>
</div>

<div class="stats-row">
  <div class="stat"><div class="stat-val" id="mCaptures">0</div><div class="stat-lbl">Captures</div></div>
  <div class="stat"><div class="stat-val" id="mClients">0</div><div class="stat-lbl">Devices</div></div>
  <div class="stat"><div class="stat-val" id="mUptime">0m</div><div class="stat-lbl">Uptime</div></div>
</div>

<div class="prompt-chips" id="promptChips"></div>

<div class="answer-wrap">
  <div class="answer-card">
    <div class="card-hdr">
      <h2>Answer</h2>
      <span class="card-time" id="mLastUpdate"></span>
    </div>
    <div class="card-body" id="mAnswerBody">
      <div class="empty">
        <div class="empty-icon">&#x1F4F8;</div>
        <h3>Waiting for capture</h3>
        <p>Results will appear here in real time</p>
      </div>
    </div>
  </div>
</div>

<div class="notif" id="notif"></div>

<div class="bottom-bar">
  <button class="btn btn-ghost" id="voiceBtn" onclick="toggleVoice()">Voice Off</button>
  <button class="btn btn-primary" onclick="requestCapture()">Request Capture</button>
</div>

<script>
let ws, voiceOn=false, activeChip='qa', allPrompts=[];

function connect() {
  ws = new WebSocket('ws://'+location.host+'/ws');
  ws.onopen = () => { setConn(true); loadPrompts(); refreshStats(); };
  ws.onmessage = e => handle(JSON.parse(e.data));
  ws.onclose = () => { setConn(false); setTimeout(connect,3000); };
}
function setConn(ok) {
  const el = document.getElementById('connPill');
  el.className = 'conn-pill '+(ok?'ok':'err');
  el.textContent = ok ? 'Live' : 'Offline';
}
function handle(d) {
  if(d.type==='connection') {
    if(d.latest_result && d.latest_result.status==='success') showAnswer(d.latest_result);
    loadPrompts();
  } else if(d.status==='success') {
    showAnswer(d); notify('New answer received!'); refreshStats();
  } else if(d.status==='error') {
    showError(d.error);
  }
}
function showAnswer(r) {
  document.getElementById('mLastUpdate').textContent =
    new Date(r.timestamp).toLocaleTimeString();
  document.getElementById('mAnswerBody').innerHTML =
    '<div class="answer-text">'+renderMD(r.analysis||'')+'</div>';
  if(voiceOn && r.analysis) speak(r.analysis);
}
function showError(msg) {
  document.getElementById('mAnswerBody').innerHTML =
    '<div class="error-box"><strong>Error:</strong> '+msg+'</div>';
}
function renderMD(t) {
  return t
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/^### (.+)$/gm,'<h3>$1</h3>')
    .replace(/^## (.+)$/gm,'<h2>$1</h2>')
    .replace(/^# (.+)$/gm,'<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/^- (.+)$/gm,'<li>$1</li>')
    .replace(/\n\n/g,'<br><br>').replace(/\n/g,'<br>');
}
async function loadPrompts() {
  try {
    const r = await fetch('/prompts');
    allPrompts = await r.json();
    const chips = document.getElementById('promptChips');
    chips.innerHTML = allPrompts.map(p=>
      `<div class="chip${p.id===activeChip?' active':''}"
            onclick="setChip('${p.id}',this)">${p.name}</div>`
    ).join('');
  } catch(e){}
}
function setChip(id, el) {
  activeChip = id;
  document.querySelectorAll('.chip').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
  fetch('/active-prompt',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({prompt_id:id})});
}
async function requestCapture() {
  document.getElementById('mAnswerBody').innerHTML =
    '<div class="loading"><div class="spinner"></div><p style="color:#8892b0;font-size:13px">Requesting capture...</p></div>';
  notify('Capture requested!');
  try {
    await fetch('/capture',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({prompt_id:activeChip})});
  } catch(e) { showError(e.message); }
}
function toggleVoice() {
  voiceOn = !voiceOn;
  const btn = document.getElementById('voiceBtn');
  btn.textContent = voiceOn ? 'Voice On' : 'Voice Off';
  btn.style.background = voiceOn ? '#065f46' : '';
  btn.style.color = voiceOn ? '#6ee7b7' : '';
  if(!voiceOn) speechSynthesis.cancel();
  notify(voiceOn ? 'Voice readout ON' : 'Voice readout OFF');
}
function speak(text) {
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/<[^>]*>/g,''));
  u.rate=0.95; u.pitch=1;
  speechSynthesis.speak(u);
}
function notify(msg) {
  const el = document.getElementById('notif');
  el.textContent = msg; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'), 2500);
}
async function refreshStats() {
  try {
    const s = await (await fetch('/stats')).json();
    document.getElementById('mCaptures').textContent = s.total_captures||0;
    document.getElementById('mClients').textContent  = s.connected_clients||0;
    const u=s.uptime_seconds||0;
    document.getElementById('mUptime').textContent =
      Math.floor(u/3600)>0 ? Math.floor(u/3600)+'h' :
      Math.floor(u/60)+'m';
  } catch(e){}
}

connect();
setInterval(refreshStats,15000);
</script>
</body>
</html>"""


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/mobile", response_class=HTMLResponse)
async def mobile():
    return MOBILE_HTML

@app.get("/prompts")
async def get_prompts():
    return JSONResponse(prompt_manager.get_all())

@app.post("/prompts")
async def add_prompt(data: PromptCreate):
    return prompt_manager.add(data.dict())

@app.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    prompt_manager.delete(prompt_id)
    return {"status": "deleted"}

@app.post("/active-prompt")
async def set_active_prompt(data: dict):
    global active_prompt_id
    active_prompt_id = data.get("prompt_id", "qa")
    return {"active_prompt": active_prompt_id}

@app.post("/capture")
async def trigger_capture(request: CaptureRequest):
    global latest_result
    pid = request.prompt_id or active_prompt_id
    result = await capture_system.process_capture(
        prompt_id=pid, custom_prompt=request.prompt)
    latest_result = result
    await broadcast({**result.dict(), "active_prompt": pid})
    return result

@app.get("/latest")
async def get_latest():
    if latest_result:
        return latest_result
    return {"status": "idle", "timestamp": datetime.now().isoformat()}

@app.get("/stats")
async def get_stats():
    return capture_system.get_stats()

@app.get("/history")
async def get_history(limit: int = 50):
    return {"results": history_manager.get_all(limit)}

@app.get("/history/search")
async def search_history(q: str = Query(""), limit: int = 50):
    return {"results": history_manager.search(q, limit)}

@app.delete("/history")
async def clear_history():
    history_manager.clear()
    return {"status": "cleared"}

@app.post("/schedule")
async def set_schedule(req: ScheduleRequest):
    scheduler.configure(req.enabled, req.interval_minutes, req.prompt_id)
    if req.enabled:
        scheduler.start(main_event_loop)
    else:
        scheduler.stop()
    return {"status": "ok", "enabled": req.enabled,
            "interval": req.interval_minutes}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"Client connected: {websocket.client.host} "
                f"(Total: {len(connected_clients)})")
    try:
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to LAN LLM Proxy v2",
            "server_info": {"model": config.OPENAI_MODEL,
                            "hotkey": config.HOTKEY},
            "latest_result": latest_result.dict() if latest_result else None
        })
        while True:
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                if cmd.get("action") == "capture":
                    await trigger_capture_handler(
                        cmd.get("prompt_id", active_prompt_id))
                elif cmd.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected: {websocket.client.host} "
                    f"(Total: {len(connected_clients)})")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    global main_event_loop
    main_event_loop = asyncio.get_event_loop()
    logger.info("=" * 60)
    logger.info("LAN LLM PROXY v2.0.0 STARTING")
    logger.info("=" * 60)
    logger.info(f"Desktop : http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    logger.info(f"Mobile  : http://{config.SERVER_HOST}:{config.SERVER_PORT}/mobile")
    logger.info(f"Hotkey  : {config.HOTKEY}")
    logger.info("=" * 60)
    if not setup_hotkey():
        logger.warning("Hotkey unavailable - use dashboard instead")
    logger.info("System ready!")

@app.on_event("shutdown")
async def shutdown():
    scheduler.stop()
    keyboard.unhook_all()
    logger.info("Shutdown complete")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    if config.OPENAI_API_KEY == "your-api-key-here":
        print("ERROR: OpenAI API key not configured!")
        sys.exit(1)
    uvicorn.run(app, host=config.SERVER_HOST,
                port=config.SERVER_PORT,
                log_level=config.LOG_LEVEL.lower())