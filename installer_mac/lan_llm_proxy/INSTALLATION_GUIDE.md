# LAN LLM Proxy - Complete Installation Guide for Beginners

**No technical knowledge required! Just follow the pictures and steps.**

---

## 🪟 WINDOWS INSTALLATION

### Step 1: Install Python (5 minutes)

**What is Python?** It's free software that lets this program run on your computer.

1. **Go to:** https://www.python.org/downloads/
2. **Click** the big yellow button that says **"Download Python 3.x.x"**
3. **Run** the downloaded file (it's in your Downloads folder)
4. **VERY IMPORTANT:** Check the box that says **"Add Python to PATH"**
   - This box is at the BOTTOM of the first screen
   - If you don't check it, nothing will work!
note you may not see the box and it's fine.
5. Click **"Install Now"**
6. Wait for it to finish (takes 2-3 minutes)
7. Click **"Close"**

**How to check if it worked:**
1. Press **Windows key + R** on your keyboard
2. Type `cmd` and press Enter
3. A black window opens — type: `python --version` and press Enter
4. You should see something like: `Python 3.12.0`
5. If you see that, Python is installed! ✅

---

### Step 2: Get the Software (1 minute)

1. **Unzip** the `lan_llm_proxy_v2.zip` file someone sent you
   - Right-click the ZIP file
   - Click **"Extract All"**
   - Click **"Extract"**
2. You now have a folder called **`lan_llm_proxy`**
3. **Remember where this folder is!** You'll need it.

---

### Step 3: Install Required Packages (2 minutes)

1. **Open** the `lan_llm_proxy` folder
2. **Click** on the address bar at the top (where it shows the folder path)
3. **Type** `cmd` and press Enter
   - A black window opens — this is called "Command Prompt"
4. **Type** this exactly: `INSTALL.bat` and press Enter
5. **Wait** — you'll see text scrolling. This is normal!
6. When you see "INSTALLATION COMPLETE" — you're done! ✅

**If you see errors:**
- Right-click the file with the name 'INSTALL' in capital letters. instead
- Click **"Run as administrator"**
- Click **"Yes"** when Windows asks
- Try again

---

### Step 4: Start the Program! (1 minute)

1. **Find** `START_SERVER` in your folder
2. **Right-click** it → Click **"Run as administrator"**
   - Click **"Yes"** when Windows asks
3. A black window opens with green text — this is good!
4. You should see: `System ready!`
5. **Leave this window open!** Don't close it.

---

### Step 7: Open the Dashboard (30 seconds)

1. **Open** your web browser (Chrome, Edge, Firefox)
2. **Type** this in the address bar: `http://localhost:8000`
3. **Press** Enter
4. You should see a beautiful purple dashboard! 🎉

---

### Step 8: Try It! (30 seconds)

1. **Open** Notepad or any program
2. **Type** a question like: "What is 2+2?"
3. **Press** ctrl+shift+x
4. **Look** at the dashboard — the AI answer appears!

---

## 🍎 MAC INSTALLATION

### Step 1: Install Python (5 minutes)

**Option A — Using Homebrew (recommended if you have it):**
1. Open **Terminal** (press Cmd+Space, type "Terminal", press Enter)
2. Type: `brew install python`
3. Press Enter and wait

**Option B — Direct Download:**
1. Go to: https://www.python.org/downloads/
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the downloaded file
4. Follow the installer — just click "Continue" and "Install"
5. Enter your Mac password when asked
6. Click "Close" when done

**Check if it worked:**
1. Open Terminal (Cmd+Space → type "Terminal" → Enter)
2. Type: `python3 --version`
3. You should see: `Python 3.12.0` or similar ✅

---

### Step 2: Get the Software (1 minute)

1. **Unzip** the `lan_llm_proxy_v2.zip` file
   - Double-click it — Mac unzips automatically
2. You now have a folder called **`lan_llm_proxy`**
3. Move it to your **Desktop** or **Documents** for easy access

---

### Step 3: Install Required Packages (2 minutes)

1. Open **Terminal** (Cmd+Space → type "Terminal" → Enter)
2. Type: `cd ` (that's "cd" followed by a space)
3. **Drag** the `lan_llm_proxy` folder into the Terminal window
   - The path appears automatically!
4. Press Enter
5. Type: `bash install.sh` and press Enter
6. Enter your Mac password if asked
7. Wait for "INSTALLATION COMPLETE" ✅

---

### Step 4: Grant Screen Recording Permission (Mac only!)

**⚠️ IMPORTANT:** Mac blocks screen recording by default.

1. Open **System Preferences**
2. Click **Security & Privacy**
3. Click the **Privacy** tab
4. Select **Screen Recording** from the list on the left
5. Click the **lock icon** at the bottom left
6. Enter your Mac password
7. Check the box next to **Terminal**
8. Restart Terminal if it was already open

---

### Step 5: Start the Program (1 minute)

1. In Terminal, type: `bash start_server.sh`
2. Press Enter
3. You should see: `System ready!`
4. Leave Terminal open!

---

### Step 8: Open the Dashboard (30 seconds)

1. Open Safari, Chrome, or Firefox
2. Go to: `http://localhost:8000`
3. You should see the dashboard! 🎉

---

### Step 9: Try It! (30 seconds)

1. Open TextEdit or any app
2. Type a question
3. Press command+shift+x
4. Watch the answer appear in the dashboard!

---

## CONNECT YOUR PHONE (Any Platform)

### Step 1: Find Your Computer's IP Address

**Windows:**
1. Press **Windows key + R**
2. Type `cmd` and press Enter
3. Type `ipconfig` and press Enter
4. Look for "IPv4 Address" — it looks like: `192.168.1.100`
5. Write this down!

**Mac:**
1. Click the  menu → **System Preferences** → **Network**
2. Look for "IP Address" — it looks like: `192.168.1.100`
3. Write this down!

**OR:** Just look at the dashboard — the IP is shown in the purple banner at the top!

---

### Step 2: Open on Your Phone

1. Make sure your phone is on the **same WiFi** as your computer
2. Open your phone's web browser (Safari, Chrome, etc.)
3. Type: `http://YOUR_IP_HERE:8000/mobile`
   - Replace `YOUR_IP_HERE` with the IP you wrote down
   - Example: `http://192.168.1.100:8000/mobile`
4. Press Go
5. You should see the mobile interface! 🎉

**Now when you press Ctrl+shift+x on your computer, the answer appears on your phone instantly!**

---

## ❓ TROUBLESHOOTING

### "Python not found"
→ **Fix:** Reinstall Python and make sure you check "Add Python to PATH"

### "Hotkey not working"
→ **Fix:** Run `START_SERVER.bat` as administrator (right-click → Run as administrator)

### "Phone can't connect"
→ **Fix:**
- Check both devices are on the same WiFi
- Try turning Windows Firewall off temporarily to test
- Make sure the server is running (black window is open)

### "Screen capture fails" (Mac)
→ **Fix:** Grant screen recording permission (see Step 5 above)

### "Can't open dashboard"
→ **Fix:**
- Make sure the server is running (black window says "System ready")
- Try typing the IP address instead: `http://192.168.1.100:8000`

---

## 🎓 WHAT EACH FILE DOES

| File | What it does | Do you edit it? |
|------|--------------|-----------------|
| `START_SERVER.bat` (Win) | Starts the program 
| `start_server.sh` (Mac) | Starts the program 
| `INSTALL.bat` (Win) | Installs everything | NO - just run it once |
| `install.sh` (Mac) | Installs everything | NO - just run it once |
| `server.py` | The actual program | NO - unless you know Python |
| `requirements.txt` | List of needed software | NO - don't touch |
| `data/` folder | Where captures are saved | NO - but you can look inside |

---

## 💡 TIPS FOR BEGINNERS

1. **Always run as administrator on Windows** — this makes the hotkey work
2. **Keep the black window open** — that's the server running
3. **Bookmark the dashboard** — `http://localhost:8000`
4. **The phone URL changes** if you connect to different WiFi
5. **Press ctrl+shift+x** — to capture current screen.

---

## 📞 WHAT TO DO IF YOU'RE STUCK

1. **Close everything** — close the black window, close the browser
2. **Start fresh** — run `START_SERVER.bat` as administrator again
3. **Check the basics:**
   - Is Python installed? (type `python --version` in cmd)
   - Is the server running? (is the black window open?)
4. **Read the error messages** — they usually tell you what's wrong
5. **Try the troubleshooting section above**

---

## 🎉 YOU'RE DONE!

If you see the dashboard and can press ctrl+shift+x to get answers, **you've successfully installed everything!**

Enjoy your AI-powered screen analysis system! 🚀

**Next:** Learn how to use Custom Prompts (see CUSTOM_PROMPTS_GUIDE.md)
