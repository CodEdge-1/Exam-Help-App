# ⚡ QUICK START - One Page Reference

## 🚀 5-Minute Setup

### Windows:
```
1. Install Python from python.org (check "Add to PATH"!)
2. Run INSTALL.bat
3. Edit START_SERVER.bat → add your API key
4. Right-click START_SERVER.bat → Run as administrator
5. Open browser: http://localhost:8000
```

### Mac:
```
1. Install Python: brew install python
2. Run: bash install.sh
3. Edit start_server.sh → add your API key
4. Run: bash start_server.sh
5. Open browser: http://localhost:8000
```

---

## ⌨️ How to Use

| Action | How |
|--------|-----|
| **Capture screen** | Press **Ctrl+shift+x**
| **View results** | Open `http://localhost:8000` in browser |
| **Use on phone** | Open `http://YOUR_IP:8000/mobile` |
| **Change prompt** | Click a different prompt in Prompts page |
| **Stop server** | Close the black window or press Ctrl+C |

---

## 📱 Phone Setup

1. Find your IP: Look at the purple banner on the dashboard OR run `ipconfig` (Win) / `ifconfig` (Mac)
2. Make sure phone is on **same WiFi**
3. Open phone browser: `http://YOUR_IP:8000/mobile`
4. Done! Now Ctrl+shift+x on computer → answer appears on phone

---

## ✏️ Custom Prompts in 30 Seconds

1. Go to **Prompts** page
2. Scroll to bottom form
3. Fill in:
   - **Name:** What you want to call it
   - **Icon:** A letter or emoji
   - **Prompt:** Tell the AI what to do
4. Click **Save Prompt**
5. Click your new prompt to activate it
6. Press Ctrl+shift+x — AI uses your instructions!

**Example Prompt:**
```
Extract all email addresses and phone numbers from this screen.
List them in a clean format.
```

---

## 🎯 Built-In Prompts

| Prompt | Press Ctrl+shift+x to... |
|--------|----------------|
| **Answer Question** | Answer any question written on screen |
| **Summarize** | Get bullet point summary |
| **Translate** | Translate foreign text to English |
| **Explain Simply** | Get simple explanation of complex stuff |
| **Extract Data** | Pull out numbers, facts, dates |
| **Proofread** | Check grammar and spelling |

---

## 🛠️ Common Issues

| Problem | Fix |
|---------|-----|
| Ctrl+shift+x not working | Run as administrator |
| Phone can't connect | Same WiFi? Firewall off? Server running? |
| "Python not found" | Reinstall Python, check "Add to PATH" |

---

## 💰 Costs

- **Software:** Free
- **Per capture:** ~$0.01-0.05
- **Typical monthly:** $5-20 for moderate use

Monitor at: https://platform.openai.com/account/usage

---

## 📂 File Locations

```
data/
├── captures/   → Your screen captures (PNG files)
├── results/    → AI answers (JSON files)
└── logs/       → System logs
```

---

## 🎓 Power Tips

1. **History Search:** Go to History page → search for past captures
2. **Voice Readout:** Toggle voice switch on dashboard → AI reads answers aloud
3. **Scheduler:** Schedule page → auto-capture every X minutes
4. **Multiple Devices:** Run client.py on other PCs to receive broadcasts

---

## 📞 Get Help

1. Read **INSTALLATION_GUIDE.md** for detailed steps
2. Read **CUSTOM_PROMPTS_GUIDE.md** for prompt examples
3. Check `data/logs/` for error details
4. Google the error message

---

## 🔗 Important URLs

| Page | URL |
|------|-----|
| Dashboard | `http://localhost:8000` |
| Mobile | `http://YOUR_IP:8000/mobile` |
| Prompts | Dashboard → Prompts tab |
| History | Dashboard → History tab |
| Schedule | Dashboard → Schedule tab |

---

**That's it! Press Ctrl+shift+x to start capturing. 🚀**
