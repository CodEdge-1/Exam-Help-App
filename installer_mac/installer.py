#!/usr/bin/env python3
"""
LAN LLM Proxy System — Installation Wizard
Cross-platform GUI installer (Windows & macOS)
Build with PyInstaller — see build_windows.bat or build_mac.sh
"""

import os
import sys
import platform
import subprocess
import threading
import shutil
import socket
import zipfile
import tarfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


# ─── Colour Scheme (matches the proxy dashboard purple theme) ─────────────────
BG         = "#1E1B2E"
CARD       = "#2D2B45"
ACCENT     = "#7C3AED"
ACCENT_LT  = "#9F67FF"
SUCCESS    = "#10B981"
ERROR      = "#EF4444"
WARNING    = "#F59E0B"
FG         = "#F3F4F6"
FG_MUTED   = "#9CA3AF"
WHITE      = "#FFFFFF"

SYSTEM     = platform.system()   # "Windows" or "Darwin"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_bundle_dir() -> Path:
    """Return the directory containing bundled data (works frozen or unfrozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)          # PyInstaller temp dir
    return Path(__file__).parent           # dev mode: same folder as script


def default_install_path() -> Path:
    if SYSTEM == "Windows":
        return Path.home() / "AppData" / "Local" / "LAN_LLM_Proxy"
    else:
        return Path.home() / "Applications" / "LAN_LLM_Proxy"


# ─── Main Application ─────────────────────────────────────────────────────────

class InstallerApp(tk.Tk):

    STEPS = [
        "Welcome",
        "System Check",
        "Install Location",
        "Installing",
        "API Key",
        "Done",
    ]

    def __init__(self):
        super().__init__()

        self.title("LAN LLM Proxy — Setup Wizard")
        self.geometry("640x520")
        self.resizable(False, False)
        self.configure(bg=BG)

        # Centre on screen
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-640)//2}+{(sh-520)//2}")

        # Shared state
        self.step_index       = 0
        self.install_dir      = tk.StringVar(value=str(default_install_path()))
        self.api_key_var      = tk.StringVar()
        self.install_success  = False
        self._syscheck_ok     = False

        self._build_chrome()
        self._show_step(0)

    # ── Chrome (persistent header + button bar) ───────────────────────────────

    def _build_chrome(self):
        # Header bar
        hdr = tk.Frame(self, bg=ACCENT, height=68)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⚡  LAN LLM Proxy",
                 font=("Helvetica", 17, "bold"),
                 fg=WHITE, bg=ACCENT).pack(side="left", padx=22, pady=14)

        self._step_lbl = tk.Label(hdr, text="", font=("Helvetica", 10),
                                   fg="#D1C4E9", bg=ACCENT)
        self._step_lbl.pack(side="right", padx=22)

        # Thin progress strip
        strip = tk.Frame(self, bg=BG, height=4)
        strip.pack(fill="x")
        self._prog_fill = tk.Frame(strip, bg=ACCENT_LT, height=4)
        self._prog_fill.place(x=0, y=0, height=4, width=1)

        # Content area
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True)

        # Button bar
        btnbar = tk.Frame(self, bg=CARD, height=58)
        btnbar.pack(fill="x", side="bottom")
        btnbar.pack_propagate(False)

        self._btn_cancel = tk.Button(btnbar, text="Cancel",
                                      font=("Helvetica", 11),
                                      fg=FG_MUTED, bg=CARD, relief="flat",
                                      cursor="hand2", command=self._on_cancel)
        self._btn_cancel.pack(side="left", padx=20, pady=10)

        self._btn_next = tk.Button(btnbar, text="Next →",
                                    font=("Helvetica", 11, "bold"),
                                    fg=WHITE, bg=ACCENT, relief="flat",
                                    cursor="hand2", padx=18, pady=5,
                                    command=self._on_next)
        self._btn_next.pack(side="right", padx=20, pady=10)

        self._btn_back = tk.Button(btnbar, text="← Back",
                                    font=("Helvetica", 11),
                                    fg=FG_MUTED, bg=CARD, relief="flat",
                                    cursor="hand2", command=self._on_back)
        self._btn_back.pack(side="right", padx=4, pady=10)

    def _update_chrome(self):
        idx   = self.step_index
        total = len(self.STEPS)
        pct   = (idx + 1) / total
        self.update_idletasks()
        w = max(int(self.winfo_width() * pct), 4)
        self._prog_fill.configure(width=w)
        self._step_lbl.configure(text=f"Step {idx+1} of {total}  —  {self.STEPS[idx]}")

        # Back button
        self._btn_back.configure(state="normal" if idx > 0 else "disabled")

        # Next / Finish
        if idx == total - 1:
            self._btn_next.configure(text="Finish", command=self._on_finish,
                                      state="normal")
            self._btn_cancel.configure(state="disabled")
        elif idx == 3:                          # installing — lock navigation
            self._btn_next.configure(state="disabled")
            self._btn_back.configure(state="disabled")
            self._btn_cancel.configure(state="disabled")
        else:
            self._btn_next.configure(text="Next →", command=self._on_next,
                                      state="normal")
            self._btn_cancel.configure(state="normal")

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show_step(self, idx: int):
        for w in self.content.winfo_children():
            w.destroy()
        self.step_index = idx
        self._update_chrome()
        [self._page_welcome,
         self._page_syscheck,
         self._page_location,
         self._page_installing,
         self._page_apikey,
         self._page_done][idx]()

    def _on_next(self):
        i = self.step_index
        if i == 1 and not self._syscheck_ok:
            messagebox.showerror("Prerequisites Missing",
                                 "Python 3.8+ is required.\n"
                                 "Please install it from python.org and re-run this wizard.")
            return
        if i == 2 and not self.install_dir.get().strip():
            messagebox.showerror("No Location", "Please choose an install directory.")
            return
        self._show_step(i + 1)
        if self.step_index == 3:
            self.after(200, self._start_install_thread)

    def _on_back(self):
        if self.step_index > 0:
            self._show_step(self.step_index - 1)

    def _on_cancel(self):
        if messagebox.askyesno("Cancel", "Cancel the installation?"):
            self.destroy()

    def _on_finish(self):
        self.destroy()

    # =========================================================================
    # PAGE 1 — WELCOME
    # =========================================================================

    def _page_welcome(self):
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=44, pady=18)

        tk.Label(f, text="🚀", font=("Helvetica", 44), bg=BG).pack(pady=(4, 4))
        tk.Label(f, text="Welcome to LAN LLM Proxy",
                 font=("Helvetica", 20, "bold"), fg=FG, bg=BG).pack()
        tk.Label(f, text="AI-Powered Screen Analysis over your Local Network",
                 font=("Helvetica", 11), fg=FG_MUTED, bg=BG).pack(pady=(3, 18))

        card = tk.Frame(f, bg=CARD, padx=20, pady=14)
        card.pack(fill="x")

        for icon, text in [
            ("⚡", "Hotkey-triggered screen capture  (Ctrl+Shift+X)"),
            ("🌐", "LAN-accessible web dashboard at http://localhost:8000"),
            ("📱", "Mobile device support on the same WiFi"),
            ("🤖", "OpenAI-powered analysis of any screen content"),
        ]:
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=icon, bg=CARD, font=("Helvetica", 13)).pack(side="left")
            tk.Label(row, text=f"  {text}", fg=FG, bg=CARD,
                     font=("Helvetica", 11)).pack(side="left")

        tk.Label(f,
                 text="This wizard installs all files and dependencies automatically.\n"
                      "Click  Next →  to begin.",
                 font=("Helvetica", 11), fg=FG_MUTED, bg=BG,
                 justify="center").pack(pady=(18, 0))

    # =========================================================================
    # PAGE 2 — SYSTEM CHECK
    # =========================================================================

    def _page_syscheck(self):
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=44, pady=18)

        tk.Label(f, text="System Requirements", font=("Helvetica", 16, "bold"),
                 fg=FG, bg=BG).pack(anchor="w")
        tk.Label(f, text="Checking your system before installation…",
                 font=("Helvetica", 11), fg=FG_MUTED, bg=BG).pack(anchor="w", pady=(3, 14))

        card = tk.Frame(f, bg=CARD, padx=20, pady=14)
        card.pack(fill="x")

        self._check_labels = {}
        for name in ["Python Runtime", "Port 8000", "Disk Space"]:
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=name, fg=FG, bg=CARD,
                     font=("Helvetica", 11), width=16, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="Checking…", fg=FG_MUTED, bg=CARD,
                           font=("Helvetica", 11))
            lbl.pack(side="left")
            self._check_labels[name] = lbl

        self._syscheck_note = tk.Label(f, text="", fg=FG_MUTED, bg=BG,
                                        font=("Helvetica", 10),
                                        wraplength=530, justify="left")
        self._syscheck_note.pack(anchor="w", pady=(14, 0))

        self.after(300, self._run_syscheck)

    def _run_syscheck(self):
        results = {}

        # Python runtime — always bundled inside the installer, no install needed
        results["Python Runtime"] = (True, "Bundled inside installer  ✅  (no install needed)")

        # Port 8000
        try:
            s = socket.socket()
            s.bind(("0.0.0.0", 8000))
            s.close()
            port_ok = True
        except Exception:
            port_ok = False
        results["Port 8000"] = (port_ok,
            "Available" if port_ok
            else "In use — another service is using port 8000")

        # Disk space — need ~500 MB (proxy files + bundled Python + packages)
        try:
            free = shutil.disk_usage(Path.home()).free
            space_ok = free > 500 * 1024 * 1024
            gb = free / 1024**3
            results["Disk Space"] = (space_ok,
                f"{gb:.1f} GB free" if space_ok
                else f"Low — only {gb:.1f} GB free (need ~500 MB)")
        except Exception:
            results["Disk Space"] = (True, "Unknown")

        # Update labels — Port and Disk are warnings only, never blockers
        for name, (ok, msg) in results.items():
            color = SUCCESS if ok else WARNING
            icon  = "✅" if ok else "⚠️"
            self._check_labels[name].configure(text=f"{icon}  {msg}", fg=color)

        # Always allow proceeding — nothing can block since Python is bundled
        self._syscheck_ok = True

        if not results["Port 8000"][0]:
            self._syscheck_note.configure(
                text="⚠️  Port 8000 is in use. The proxy server may not start until "
                     "the other service is stopped. You can still install now.",
                fg=WARNING)
        else:
            self._syscheck_note.configure(
                text="✅  Everything looks good. Click Next → to continue.",
                fg=SUCCESS)

    # =========================================================================
    # PAGE 3 — INSTALL LOCATION
    # =========================================================================

    def _page_location(self):
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=44, pady=18)

        tk.Label(f, text="Choose Install Location",
                 font=("Helvetica", 16, "bold"), fg=FG, bg=BG).pack(anchor="w")
        tk.Label(f, text="Select the folder where LAN LLM Proxy will be installed.",
                 font=("Helvetica", 11), fg=FG_MUTED, bg=BG).pack(anchor="w", pady=(3, 18))

        row = tk.Frame(f, bg=BG)
        row.pack(fill="x")

        entry = tk.Entry(row, textvariable=self.install_dir,
                         font=("Helvetica", 11), fg=FG, bg=CARD,
                         insertbackground=FG, relief="flat", bd=0)
        entry.pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 8))

        tk.Button(row, text="Browse…",
                  font=("Helvetica", 10), fg=WHITE, bg=ACCENT,
                  relief="flat", cursor="hand2", padx=10, pady=4,
                  command=self._browse_dir).pack(side="right")

        card = tk.Frame(f, bg=CARD, padx=18, pady=12)
        card.pack(fill="x", pady=(22, 0))

        if SYSTEM == "Windows":
            notes = [
                "📁  Program files are copied to the folder above.",
                "📦  Approx. 50 MB of disk space required.",
                "🔗  A Desktop shortcut is created automatically.",
                "🔑  Right-click the shortcut → Run as Administrator for hotkey support.",
            ]
        else:
            notes = [
                "📁  Program files are copied to the folder above.",
                "📦  Approx. 50 MB of disk space required.",
                "🖥️  A launcher script is created in the install folder.",
                "🔐  Grant Screen Recording permission after first launch (System Preferences).",
            ]

        for note in notes:
            tk.Label(card, text=note, fg=FG_MUTED, bg=CARD,
                     font=("Helvetica", 10), anchor="w").pack(fill="x", pady=2)

    def _browse_dir(self):
        chosen = filedialog.askdirectory(title="Choose Install Location",
                                         initialdir=Path.home())
        if chosen:
            self.install_dir.set(str(Path(chosen) / "LAN_LLM_Proxy"))

    # =========================================================================
    # PAGE 4 — INSTALLING  (background thread)
    # =========================================================================

    def _page_installing(self):
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=44, pady=18)

        tk.Label(f, text="Installing…", font=("Helvetica", 16, "bold"),
                 fg=FG, bg=BG).pack(anchor="w")

        self._install_status = tk.Label(f, text="Preparing…",
                                         font=("Helvetica", 11), fg=FG_MUTED, bg=BG)
        self._install_status.pack(anchor="w", pady=(3, 10))

        # Progress bar
        sty = ttk.Style()
        sty.theme_use("clam")
        sty.configure("P.Horizontal.TProgressbar",
                       background=ACCENT, troughcolor=CARD, thickness=14)

        self._pb = ttk.Progressbar(f, style="P.Horizontal.TProgressbar",
                                    mode="indeterminate", length=540)
        self._pb.pack(fill="x", pady=(0, 12))
        self._pb.start(12)

        # Log box
        log_outer = tk.Frame(f, bg=CARD, padx=2, pady=2)
        log_outer.pack(fill="both", expand=True)

        self._log_box = tk.Text(log_outer, font=("Courier", 9),
                                 fg="#A0E0A0", bg="#161425",
                                 relief="flat", bd=0, state="disabled", wrap="word")
        self._log_box.pack(fill="both", expand=True, padx=8, pady=8)

    def _log(self, msg: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
        self.update_idletasks()

    def _status(self, msg: str):
        self._install_status.configure(text=msg)
        self.update_idletasks()

    def _start_install_thread(self):
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        dest   = Path(self.install_dir.get())
        bundle = get_bundle_dir()
        src    = bundle / "lan_llm_proxy"

        try:
            # 1 ── Create destination directory
            self._status("Creating install directory…")
            self._log(f"→ Target: {dest}")
            dest.mkdir(parents=True, exist_ok=True)
            self._log("  ✓ Directory ready")

            # 2 ── Copy proxy source files
            self._status("Copying program files…")
            self._log("→ Copying proxy files…")
            if src.exists():
                for item in src.iterdir():
                    dst_item = dest / item.name
                    if item.is_dir():
                        shutil.copytree(str(item), str(dst_item), dirs_exist_ok=True)
                    else:
                        shutil.copy2(str(item), str(dst_item))
                    self._log(f"  ✓ {item.name}")
            else:
                self._log("  ⚠ Source bundle not found (dev mode) — skipping file copy.")

            # 3 ── Extract bundled Python runtime (no system Python needed)
            python_dir = dest / "python"
            python_exe = None

            if SYSTEM == "Windows":
                py_zip = bundle / "python_embed.zip"
                if py_zip.exists():
                    self._status("Extracting Python runtime…")
                    self._log("\n→ Extracting bundled Python runtime…")
                    python_dir.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(py_zip) as z:
                        z.extractall(python_dir)
                    self._log("  ✓ Python runtime extracted")

                    # Enable site-packages so pip works in embeddable Python
                    for pth_file in python_dir.glob("python*._pth"):
                        txt = pth_file.read_text(encoding="utf-8")
                        txt = txt.replace("#import site", "import site")
                        pth_file.write_text(txt, encoding="utf-8")
                    self._log("  ✓ Python runtime configured")

                    python_exe = python_dir / "python.exe"

                    # Bootstrap pip into the embeddable Python
                    get_pip = bundle / "get-pip.py"
                    if get_pip.exists():
                        self._status("Setting up pip…")
                        self._log("→ Installing pip into bundled Python…")
                        subprocess.run(
                            [str(python_exe), str(get_pip), "--quiet"],
                            capture_output=True, cwd=str(dest)
                        )
                        self._log("  ✓ pip ready")
                else:
                    self._log("  ⚠ python_embed.zip not found in bundle (dev mode)")
                    python_exe = Path(sys.executable)

            else:  # macOS
                py_tar = bundle / "python_mac.tar.gz"
                if py_tar.exists():
                    self._status("Extracting Python runtime…")
                    self._log("\n→ Extracting bundled Python runtime…")
                    python_dir.mkdir(parents=True, exist_ok=True)
                    with tarfile.open(py_tar, "r:gz") as t:
                        t.extractall(python_dir)
                    self._log("  ✓ Python runtime extracted")

                    # python-build-standalone puts the binary at python/bin/python3
                    python_exe = python_dir / "bin" / "python3"
                    if python_exe.exists():
                        python_exe.chmod(0o755)
                        self._log("  ✓ Python runtime configured")
                    else:
                        # Fallback: search for the binary
                        candidates = list(python_dir.glob("**/python3"))
                        if candidates:
                            python_exe = candidates[0]
                            python_exe.chmod(0o755)
                        else:
                            python_exe = Path(sys.executable)
                else:
                    self._log("  ⚠ python_mac.tar.gz not found in bundle (dev mode)")
                    python_exe = Path(sys.executable)

            # 4 ── Install pip packages using the bundled Python
            self._status("Installing packages (this takes a minute)…")
            self._log("\n→ Installing required packages…")
            req = dest / "requirements.txt"
            if req.exists() and python_exe:
                result = subprocess.run(
                    [str(python_exe), "-m", "pip", "install",
                     "-r", str(req), "--quiet", "--no-warn-script-location"],
                    capture_output=True, text=True, cwd=str(dest)
                )
                if result.returncode == 0:
                    self._log("  ✓ All packages installed")
                else:
                    self._log("  ⚠ pip completed with warnings:")
                    for line in result.stderr.splitlines()[-10:]:
                        if line.strip():
                            self._log(f"    {line}")
            else:
                self._log("  ⚠ requirements.txt not found — skipping")

            # 5 ── Create data directories
            self._status("Creating data directories…")
            for d in ["data/captures", "data/results", "data/logs"]:
                (dest / d).mkdir(parents=True, exist_ok=True)
            self._log("  ✓ Data folders created")

            # 6 ── Create launcher (points to bundled Python)
            self._status("Creating launcher…")
            self._log("\n→ Creating launcher…")
            self._create_launcher(dest, python_exe)

            # Done
            self._pb.stop()
            self._pb.configure(mode="determinate", value=100)
            self._status("✅  Installation complete!")
            self._log(f"\n✅  Installed to:\n   {dest}")
            self.install_success = True
            self.after(600, lambda: self._show_step(4))

        except Exception as exc:
            self._pb.stop()
            self._status(f"❌  Error: {exc}")
            self._log(f"\n❌  Installation error:\n   {exc}")
            self.after(100, lambda: self._btn_next.configure(
                state="normal", text="Continue →",
                command=lambda: self._show_step(4)))

    def _create_launcher(self, dest: Path, python_exe: Path):
        if SYSTEM == "Windows":
            # Use bundled python.exe — relative path so the install folder is portable
            py_rel = python_exe.relative_to(dest) if python_exe.is_relative_to(dest) \
                     else python_exe

            bat = dest / "Launch_LAN_LLM_Proxy.bat"
            bat.write_text(
                f'@echo off\r\n'
                f'title LAN LLM Proxy Server\r\n'
                f'cd /d "{dest}"\r\n'
                f'echo Starting LAN LLM Proxy...\r\n'
                f'"{py_rel}" server.py\r\n'
                f'pause\r\n'
            )
            self._log("  ✓ Launch_LAN_LLM_Proxy.bat")

            # Desktop shortcut via VBScript
            try:
                desktop = Path.home() / "Desktop"
                lnk     = desktop / "LAN LLM Proxy.lnk"
                vbs     = dest / "_mk_shortcut.vbs"
                vbs.write_text(
                    f'Set sh = WScript.CreateObject("WScript.Shell")\r\n'
                    f'Set lnk = sh.CreateShortcut("{lnk}")\r\n'
                    f'lnk.TargetPath = "{bat}"\r\n'
                    f'lnk.WorkingDirectory = "{dest}"\r\n'
                    f'lnk.Description = "LAN LLM Proxy"\r\n'
                    f'lnk.Save\r\n'
                )
                subprocess.run(["cscript", "//Nologo", str(vbs)],
                               capture_output=True, timeout=10)
                vbs.unlink(missing_ok=True)
                self._log("  ✓ Desktop shortcut created")
            except Exception:
                self._log("  ⚠ Desktop shortcut skipped (run as admin to create it)")
        else:
            # macOS — use bundled Python binary
            py_rel = python_exe.relative_to(dest) if python_exe.is_relative_to(dest) \
                     else python_exe

            sh_file = dest / "Launch_LAN_LLM_Proxy.sh"
            sh_file.write_text(
                f'#!/bin/bash\n'
                f'cd "{dest}"\n'
                f'echo "Starting LAN LLM Proxy..."\n'
                f'"{py_rel}" server.py\n'
            )
            sh_file.chmod(0o755)
            self._log("  ✓ Launch_LAN_LLM_Proxy.sh")

    # =========================================================================
    # PAGE 5 — API KEY
    # =========================================================================

    # Placeholder value used in server.py when no key has been set
    _KEY_PLACEHOLDER = "your-api-key-here"

    def _read_existing_key(self) -> str:
        """
        Read server.py from the install directory and return the current API
        key value.  Returns the placeholder string if no real key is set, or
        an empty string if server.py cannot be read.
        """
        server_py = Path(self.install_dir.get()) / "server.py"
        try:
            content = server_py.read_text(encoding="utf-8", errors="replace")
            # Match both storage patterns used in server.py
            import re
            # Pattern 1:  OPENAI_API_KEY = "sk-..."
            m = re.search(r'OPENAI_API_KEY\s*=\s*["\']([^"\']+)["\']', content)
            if m:
                return m.group(1)
            # Pattern 2:  os.getenv('OPENAI_API_KEY', 'sk-...')
            m = re.search(r"os\.getenv\(['\"]OPENAI_API_KEY['\"],\s*['\"]([^'\"]+)['\"]\)",
                          content)
            if m:
                return m.group(1)
        except Exception:
            pass
        return ""

    def _page_apikey(self):
        existing_key = self._read_existing_key()
        key_is_set   = bool(existing_key) and existing_key != self._KEY_PLACEHOLDER

        # Key is already baked in — jump straight to Done, no page shown
        if key_is_set:
            self.after(50, lambda: self._show_step(5))
            return

        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=44, pady=18)

        tk.Label(f, text="Configure OpenAI API Key",
                 font=("Helvetica", 16, "bold"), fg=FG, bg=BG).pack(anchor="w")

        if key_is_set:
            # ── Key already present — show confirmation, offer optional update ──
            tk.Label(f,
                     text="An API key is already configured in server.py.",
                     font=("Helvetica", 11), fg=FG_MUTED, bg=BG,
                     justify="left").pack(anchor="w", pady=(3, 18))

            confirmed = tk.Frame(f, bg=CARD, padx=18, pady=16)
            confirmed.pack(fill="x")

            # Masked key preview  (show first 8 chars + dots)
            masked = existing_key[:8] + "•" * max(0, len(existing_key) - 8)
            tk.Label(confirmed, text="✅  Key already set", fg=SUCCESS, bg=CARD,
                     font=("Helvetica", 12, "bold")).pack(anchor="w")
            tk.Label(confirmed, text=masked, fg=FG_MUTED, bg=CARD,
                     font=("Courier", 10)).pack(anchor="w", pady=(4, 0))

            tk.Label(f, text="You can click  Next →  to continue, or enter a different key below to replace it.",
                     font=("Helvetica", 10), fg=FG_MUTED, bg=BG,
                     wraplength=530, justify="left").pack(anchor="w", pady=(14, 10))

            # Optional replacement entry (collapsed until user types)
            replace_card = tk.Frame(f, bg=CARD, padx=18, pady=14)
            replace_card.pack(fill="x")

            tk.Label(replace_card, text="Replace with a different key (optional):",
                     fg=FG_MUTED, bg=CARD, font=("Helvetica", 10)).pack(anchor="w", pady=(0, 6))

            key_entry = tk.Entry(replace_card, textvariable=self.api_key_var,
                                 font=("Courier", 11), fg=FG, bg="#161425",
                                 insertbackground=FG, relief="flat", bd=0, show="•")
            key_entry.pack(fill="x", ipady=9, padx=2)

            self._show_key = False
            def _toggle():
                self._show_key = not self._show_key
                key_entry.configure(show="" if self._show_key else "•")
                btn_show.configure(text="🙈 Hide" if self._show_key else "👁 Show")

            btn_show = tk.Button(replace_card, text="👁 Show", font=("Helvetica", 9),
                                 fg=FG_MUTED, bg=CARD, relief="flat",
                                 cursor="hand2", command=_toggle)
            btn_show.pack(anchor="e", pady=(4, 0))

            btn_row = tk.Frame(f, bg=BG)
            btn_row.pack(anchor="w", pady=(12, 0))

            tk.Button(btn_row, text="Update Key",
                      font=("Helvetica", 11, "bold"), fg=WHITE, bg=ACCENT,
                      relief="flat", cursor="hand2", padx=16, pady=7,
                      command=self._save_api_key).pack(side="left")

            self._api_status = tk.Label(btn_row, text="", fg=FG_MUTED, bg=BG,
                                         font=("Helvetica", 10))
            self._api_status.pack(side="left", padx=(12, 0))

        else:
            # ── No key set — prompt the user to add one ────────────────────────
            tk.Label(f,
                     text="LAN LLM Proxy uses OpenAI to analyse screen captures.\n"
                          "Paste your API key below — or skip and add it later.",
                     font=("Helvetica", 11), fg=FG_MUTED, bg=BG,
                     justify="left").pack(anchor="w", pady=(3, 18))

            card = tk.Frame(f, bg=CARD, padx=18, pady=16)
            card.pack(fill="x")

            tk.Label(card, text="OpenAI API Key", fg=FG, bg=CARD,
                     font=("Helvetica", 11, "bold")).pack(anchor="w")
            tk.Label(card, text="Starts with  sk-…", fg=FG_MUTED, bg=CARD,
                     font=("Helvetica", 9)).pack(anchor="w", pady=(1, 7))

            key_entry = tk.Entry(card, textvariable=self.api_key_var,
                                 font=("Courier", 11), fg=FG, bg="#161425",
                                 insertbackground=FG, relief="flat", bd=0, show="•")
            key_entry.pack(fill="x", ipady=10, padx=2)

            self._show_key = False
            def _toggle():
                self._show_key = not self._show_key
                key_entry.configure(show="" if self._show_key else "•")
                btn_show.configure(text="🙈 Hide" if self._show_key else "👁 Show")

            btn_show = tk.Button(card, text="👁 Show", font=("Helvetica", 9),
                                 fg=FG_MUTED, bg=CARD, relief="flat",
                                 cursor="hand2", command=_toggle)
            btn_show.pack(anchor="e", pady=(5, 0))

            tip = tk.Frame(f, bg=CARD, padx=16, pady=10)
            tip.pack(fill="x", pady=(14, 0))
            tk.Label(tip,
                     text="💡 Get a key:\n"
                          "   1. Visit  platform.openai.com\n"
                          "   2. Click  API Keys  →  Create new secret key\n"
                          "   3. Paste it above and click  Save Key\n\n"
                          "⏭  Skip for now — edit  server.py  later to add it.",
                     fg=FG_MUTED, bg=CARD, font=("Helvetica", 10),
                     justify="left").pack(anchor="w")

            btn_row = tk.Frame(f, bg=BG)
            btn_row.pack(anchor="w", pady=(14, 0))

            tk.Button(btn_row, text="Save Key",
                      font=("Helvetica", 11, "bold"), fg=WHITE, bg=ACCENT,
                      relief="flat", cursor="hand2", padx=16, pady=7,
                      command=self._save_api_key).pack(side="left")

            tk.Button(btn_row, text="Skip →",
                      font=("Helvetica", 11), fg=FG_MUTED, bg=BG,
                      relief="flat", cursor="hand2", padx=12, pady=7,
                      command=lambda: self._show_step(5)).pack(side="left", padx=(10, 0))

            self._api_status = tk.Label(btn_row, text="", fg=FG_MUTED, bg=BG,
                                         font=("Helvetica", 10))
            self._api_status.pack(side="left", padx=(12, 0))

    def _save_api_key(self):
        key  = self.api_key_var.get().strip()
        dest = Path(self.install_dir.get())

        if not key:
            self._api_status.configure(text="⚠  No key entered — nothing changed.", fg=WARNING)
            return

        if key == self._KEY_PLACEHOLDER:
            self._api_status.configure(text="⚠  That's the placeholder, not a real key.", fg=WARNING)
            return

        if not key.startswith("sk-"):
            self._api_status.configure(
                text="⚠  Key should start with 'sk-'. Double-check and try again.",
                fg=WARNING)
            return

        server_py = dest / "server.py"
        try:
            if server_py.exists():
                content = server_py.read_text(encoding="utf-8", errors="replace")
                # Handle both common patterns in server.py
                content = content.replace(
                    'OPENAI_API_KEY = "your-api-key-here"',
                    f'OPENAI_API_KEY = "{key}"')
                content = content.replace(
                    "os.getenv('OPENAI_API_KEY', 'your-api-key-here')",
                    f"os.getenv('OPENAI_API_KEY', '{key}')")
                content = content.replace(
                    'os.getenv("OPENAI_API_KEY", "your-api-key-here")',
                    f'os.getenv("OPENAI_API_KEY", "{key}")')
                server_py.write_text(content, encoding="utf-8")
            else:
                # Fallback: write a plain config file
                (dest / "api_key.txt").write_text(key, encoding="utf-8")

            # Show success then auto-advance to the final step
            self._api_status.configure(text="✅  Key saved! Continuing…", fg=SUCCESS)
            self.update_idletasks()
            self.after(1200, lambda: self._show_step(5))
            # Fallback: also enable Next → so user can proceed manually if after() misfires
            self._btn_next.configure(state="normal", text="Next →",
                                     command=lambda: self._show_step(5))

        except Exception as e:
            self._api_status.configure(text=f"❌  Save failed: {e}", fg=ERROR)

    # =========================================================================
    # PAGE 6 — DONE
    # =========================================================================

    def _page_done(self):
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=44, pady=12)

        tk.Label(f, text="🎉", font=("Helvetica", 36), bg=BG).pack(pady=(0, 4))

        if self.install_success:
            tk.Label(f, text="Installation Complete!",
                     font=("Helvetica", 18, "bold"), fg=SUCCESS, bg=BG).pack()
            tk.Label(f, text=f"Installed to:  {self.install_dir.get()}",
                     font=("Helvetica", 10), fg=FG_MUTED, bg=BG).pack(pady=(2, 14))
        else:
            tk.Label(f, text="Setup Wizard Complete",
                     font=("Helvetica", 18, "bold"), fg=FG, bg=BG).pack(pady=(0, 14))

        card = tk.Frame(f, bg=CARD, padx=18, pady=12)
        card.pack(fill="x")

        tk.Label(card, text="Next Steps", fg=ACCENT_LT, bg=CARD,
                 font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 6))

        if SYSTEM == "Windows":
            steps = [
                "1. Double-click  'LAN LLM Proxy'  on your Desktop to start the server",
                "   → Right-click → Run as Administrator for hotkey support",
                "2. Open your browser:  http://localhost:8000",
                "3. Press  Ctrl+Shift+X  to capture your screen",
                "4. Connect phone (same WiFi):  http://YOUR_IP:8000/mobile",
                "",
                "✅  No Python installation needed — everything is self-contained.",
            ]
        else:
            steps = [
                "1. Double-click  Launch_LAN_LLM_Proxy.sh  to start the server",
                "2. Grant Screen Recording permission:",
                "   System Preferences → Security & Privacy → Screen Recording",
                "3. Open your browser:  http://localhost:8000",
                "4. Press  Cmd+Shift+X  to capture your screen",
                "",
                "✅  No Python installation needed — everything is self-contained.",
            ]

        for s in steps:
            tk.Label(card, text=s, fg=FG_MUTED, bg=CARD,
                     font=("Helvetica", 10), anchor="w",
                     justify="left").pack(fill="x", pady=1)

        def _launch():
            path = Path(self.install_dir.get())
            if SYSTEM == "Windows":
                bat = path / "Launch_LAN_LLM_Proxy.bat"
                if bat.exists():
                    subprocess.Popen(["cmd", "/c", "start", "", str(bat)],
                                     shell=True)
            else:
                sh_file = path / "Launch_LAN_LLM_Proxy.sh"
                if sh_file.exists():
                    subprocess.Popen(["open", "-a", "Terminal", str(sh_file)])

        tk.Button(f, text="🚀  Launch Now",
                  font=("Helvetica", 12, "bold"), fg=WHITE, bg=ACCENT,
                  relief="flat", cursor="hand2", padx=20, pady=8,
                  command=_launch).pack(pady=(16, 0))

        tk.Label(f, text="Click  Finish  to close the installer.",
                 font=("Helvetica", 10), fg=FG_MUTED, bg=BG).pack(pady=(6, 0))


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        app = InstallerApp()
        app.mainloop()
    except KeyboardInterrupt:
        pass
