============================================================
   LAN LLM Proxy — Your AI Screen Assistant
   Mac Edition
============================================================

Welcome! This guide will help you get started in just a
few simple steps. No technical knowledge required.

------------------------------------------------------------
WHAT IS THIS APP?
------------------------------------------------------------

LAN LLM Proxy is your personal AI assistant that can:

  - Look at your screen and explain what it sees
  - Answer questions about anything on your screen
  - Work from your phone or tablet on the same WiFi
  - Run privately on your own computer (nothing is stored
    in the cloud — only sent to OpenAI for analysis)


------------------------------------------------------------
HOW TO INSTALL
------------------------------------------------------------

1. Double-click  LAN_LLM_Proxy.dmg  to open the installer.

2. A window will appear. Double-click the
   LAN_LLM_Proxy_Setup  icon inside it.

3. If Mac shows a warning saying "unidentified developer":
   - Right-click the icon instead of double-clicking
   - Choose  "Open"  from the menu
   - Click  "Open"  again on the popup

4. The Setup Wizard will open. Click  Next  on each screen.
   It will install everything automatically — no extra
   downloads or technical steps needed.

5. When you see "Installation Complete!", click
   "Launch Now" to start the app right away.

That's it! The app is now installed on your Mac.


------------------------------------------------------------
HOW TO USE IT EVERY DAY
------------------------------------------------------------

STARTING THE APP:
  - Open your install folder (shown at the end of setup)
  - Double-click  Launch_LAN_LLM_Proxy.sh  to start.
  - A Terminal window will open in the background — this
    is normal. Do NOT close it while using the app.

GIVING SCREEN PERMISSION (first time only):
  - Mac will ask for Screen Recording permission.
  - Go to:  System Preferences → Security & Privacy
            → Privacy → Screen Recording
  - Turn on the switch next to Terminal.
  - Restart the app after granting permission.

OPENING THE DASHBOARD:
  - Open any web browser (Safari, Chrome, Firefox, etc.)
  - Go to:  http://localhost:8000
  - The dashboard will appear with all the controls.

CAPTURING YOUR SCREEN:
  - Press  Cmd + Shift + X  on your keyboard at any time
    to take a screenshot and get an instant AI analysis.
  - The result will appear on your dashboard automatically.

USING IT ON YOUR PHONE OR TABLET (same WiFi only):
  - On your mobile device, open the browser and go to:
    http://YOUR_COMPUTER_IP:8000/mobile
  - Your Mac's IP address is shown on the dashboard.


------------------------------------------------------------
TIPS
------------------------------------------------------------

  - Make sure your Mac stays on while using the app
    from a phone or tablet.

  - The app only works on your local network (your home
    or office WiFi). It does not work over the internet.

  - To stop the app, close the Terminal window or
    press  Ctrl + C  inside it.

  - If the hotkey (Cmd+Shift+X) does not respond, try
    starting the app with:  sudo ./start_server.sh
    in Terminal for full system access.


------------------------------------------------------------
SOMETHING NOT WORKING?
------------------------------------------------------------

  - Make sure the Terminal window is open and running.
  - Try restarting the server by double-clicking the
    Launch file again.
  - Make sure your phone and computer are on the SAME WiFi.
  - If Screen Recording permission was not granted, the
    capture feature will not work — see the permission
    steps above.
  - If your company WiFi blocks device-to-device traffic,
    the mobile feature will not work — this is a network
    restriction, not an app problem.

============================================================
