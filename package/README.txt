============================================================
  MH3U NativePC - MONSTER HUNTER 3 ULTIMATE, NATIVE PC PORT (v0.9.15)
  Launcher developed by: g30wolff99
============================================================

(La versión en español de este archivo es LEEME.txt)

Welcome to the official launcher of Monster Hunter 3 Ultimate for PC!

This package is 100% PORTABLE and SELF-CONTAINED (it works straight after unzipping):
- Portable Clang/LLD: the launcher downloads it once (~90 MB) with one click when you need it.
- Real AMD FidelityFX FSR 1.0 upscaling (EASU + RCAS) and AMD CAS built into Vulkan/DirectX 12.
- Glass interface with a live summary of your settings; optional Acrylic effect (Windows 11 only).
- Support for link-time optimisation ThinLTO (-flto=thin + -O3).
- The native engine 'mh3u-tools.exe', tuned, with an FPS counter and a smooth interface.
- Official graphical launcher v0.9.15 with a scrollable real-time log.
- The launcher and the game's panels (F1 / F2) come in English and Spanish: the language follows
  Windows (English if it is neither) and can be changed with the gear button in the title bar.

------------------------------------------------------------
QUICK STEPS TO PLAY (FIRST TIME ONLY):
------------------------------------------------------------
1. Open "MH3U.exe".
2. Go to the "Install & Dump" tab:
   - If you have your folder with the base game (0005000010118300) and the
     v32 update (0005000e10118300), press "Browse..." and select it.
     (The launcher detects both dumps by itself and marks them in green.)
   - If Clang shows in red, press 'Download Portable Clang' (or accept the download when building).
   - You can turn on "LTO optimisation" for the best CPU
     performance and frame stability on your processor.
3. Click the orange button:
   "Translate and Build Port (Create game.dll)"
   - The launcher translates the game and builds the native files
     in parallel on your processor.
   - You will see the progress bar and the file counter move in real time.
   - (This step takes about 1 to 2 minutes and is done only ONCE.)
4. In "Graphics Settings":
   - You can set the native resolution (1x, 2x 1440p, 4K),
     the AMD FSR 1.0 or AMD CAS upscaler, and the sharpness level.
   - The "Controls & Gamepads" tab has the button remapper (pick an action and press the button
     of your gamepad that you want to use), the gamepad layout and the camera sensitivity.
   - Inside the game, F2 opens quick settings (resolution, upscaling, sharpness, VSync,
     FPS counter, camera sensitivity and language); F1 opens the full panel. The gamepad's B button closes them.
5. Done! Press "PLAY".

MODS AND CHEATS (settings tab):
- «Mods»: monsters' life and damage meter on screen. They only read the game and change nothing: they are safe
  and also recommended in online games. With F1 open you can drag them with the mouse.
- «Cheats» (off by default): One Hit Kill, infinite sharpness, more zenny and infinite items (bowgun ammo
  included). They change the game and can alter or corrupt your saved game: make a copy first.
  In online games they are NOT recommended (they are not blocked, but they can affect your save and other players').

------------------------------------------------------------
IMPORTANT TIP:
------------------------------------------------------------
- To play the Tanzia tavern quests (High and G Rank) on your own,
  talk to the sailor and choose:
  "Tanzia Port -> Single -> Harbor or Tavern".
  Do not choose "Multiplayer" if you are not connected to a network room.

Happy hunting!

- Gamepad or keyboard: on the main screen, in 'Frequent Actions', choose
  'Do you play with a gamepad or keyboard?'. 'Keyboard and mouse' turns keyboard and mouse on (the default);
  'Gamepad' turns them off so the window does not capture the cursor.
- Supported gamepads: Xbox and XInput-compatible (2.4 GHz receivers and GameSir included),
  DualSense (PS5) and DualShock 4 (PS4) wired or over Bluetooth, and most generic HID
  gamepads. You do not need Steam or DS4Windows. If your gamepad does not respond, close them (or
  turn off the emulation) and restart the game.
  If you use HidHide (DSX, DS4Windows) and the gamepad is hidden, the launcher offers to let MH3U
  read it when you press PLAY (it asks for administrator permission); with DSX or DS4Windows
  open it is not needed.
