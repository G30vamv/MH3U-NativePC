# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). While the project is below 1.0, every release raises the last number of the version (`0.MINOR.PATCH`), whether it brings fixes or new things; see "Versions and releases" in the [README](README.md). A published version is never replaced: a fix comes as a new version.

Every entry is also published as the notes of its [GitHub Release](../../releases). From 0.9.14 the launcher comes in English and Spanish.

## [0.9.16] - 2026-11-10

### Added
- **A smooth camera with the right stick.** The camera now turns and goes up or down by how far you push the stick: a little to move it slowly, all the way to move it fast, in any direction. Before, it moved in steps, as if the stick were buttons. If you prefer the game's original camera, turn off "Smooth camera with the right stick" in the Controls tab. The game is built again the first time you press PLAY.
- **The bowgun's aim follows the stick too.** With the smooth camera on, the sight goes up and down by how far you push the stick, slowly or fast, and at the same speed whatever your FPS.
- **Hold to gather.** Keep the button held on a carcass, a gathering spot or a mining point and the hunter keeps carving, gathering or mining until the spot is used up, instead of one press for each item.
- **An FPS limit.** A new list under the resolution in the Graphics tab (and in the game's F2 window) lets you cap the game at 30, 60, 90... up to 240 FPS, or leave it without a limit as before. With a cap your PC works less, and online everyone runs at a similar pace.
- **The server relay can be chosen in the Online tab** (Auto, On, Off) when you create a room. Auto is still the default.

### Fixed
- **The bowgun keeps its aim when you shoot.** The sight used to drop back to the middle with every shot.
- **Old update backups no longer pile up** next to the launcher (about 60 MB each). Only the last one is kept, and the old ones are cleared when the launcher opens.
- **The launcher opens in the middle of your main screen**, and its messages open over it, instead of wherever the mouse was.

### Changed
- The LTO build option moved to the gear's menu (it is still off by default).
- Leftovers of an old way of connecting online that was no longer used were removed from the game's program.

## [0.9.15] - 2026-11-09

### Fixed
- **Aiming the bowgun up and down** works now, both through the sight and in third person: the aim follows the right stick (and its sensitivity setting). It never did before in this port.
- **Looking up and down with the camera stick** no longer stops when the camera sensitivity is set very low or very high (and aiming with the bowgun with it). The sensitivity now only changes how far the stick is pushed, not where it points.
- **The damage meter now counts your damage in a room.** When you join a friend's room the monsters' life reaches you a moment late, and the meter, which only looked at the last few frames after your hit, left your damage and DPS out. It now looks at the last second.

### Added
- **Button remapper for gamepads.** The Controls tab now remaps buttons for real: pick an action, press the button of your gamepad that you want to use for it (Xbox, PlayStation, Nintendo or generic pads; the picture shows what you press as you press it), and the game uses it from then on. Buttons can be turned off, the map can be reset, exported and imported as a file, and the two default profiles (Xbox and Nintendo layouts) are one click away. The Back + R combination that opens the game's panels is never remapped, so a wrong map cannot lock you out.
- **Damage of every hunter in the meter.** In a room the damage panel also lists each hunter whose hits your game sees, with their share and DPS (you first, marked *You*).
- The game's log now writes the first hits and falls of a monster's life, to see what a room looks like from your side.

## [0.9.14] - 2026-11-08

### Added
- **The launcher in English.** Every text of the launcher (menus, tabs, tips, messages, the log of the build window) and the guides come in English and Spanish. The language follows Windows' on its own (English if Windows is in neither language) and can be changed in the new **Language** selector of the gear menu; the launcher offers to restart to apply it. The game's own panels (F1 / F2, the keyboard window, the life and damage panels) use the same language, so there is one setting for everything; the monsters' names stay as they are. New guides: `README.txt` and `MULTIPLAYER_INSTRUCTIONS.txt`.
- **Choose the graphics card.** The Graphics tab has a "Graphics card" list (Automatic by default) so a PC with an integrated and a dedicated card, or a hybrid laptop, can pick which one draws the game. If the chosen card is not found the game uses the automatic choice.
- **DirectX 12 helper download.** With DirectX 12 selected, a button downloads Microsoft's shader compiler (two DLLs) so the game prepares its shaders in seconds instead of tens of seconds. You read and accept Microsoft's license terms in a window first; the button only shows with DirectX 12 and disappears once installed.
- **Time on every line of the game's log**, to match it with the room server's log when something goes wrong online.
- **Saved games apart (Online tab).** An option to keep this launcher's saved games in a folder of their own, so the port and Cemu on the same PC can have hunters with different names and not clash in a room. Your usual saved game is not touched.

### Changed
- **The language selector moved** from the Graphics tab to the gear menu and now sets the language of the launcher and of the game together.
- **The equipment and item box screens run smoother.** Their many small graphics jobs are now handed to the graphics card together: about 7 % more frames on an integrated Radeon, fewer sudden stutters and about 1.7 GB less memory at its peak.

### Fixed
- **Updates retry on their own** when GitHub answers "504 Gateway Time-out" or the connection drops, instead of failing the first time.
- **A heads-up before playing with DirectX 12 without Microsoft's helper files.** On some graphics cards the game draws wrongly (black shadows and objects) without them; the launcher now says so once and offers to install them (you read and accept Microsoft's terms first), or lets you carry on.
- **Joining a friend's room now stops a room server of yours** that was still running from an earlier try.

## [0.9.13] - 2026-11-08

### Added
- **A menu for the launcher's own options.** The gear next to the window buttons opens a menu with the options that belong to the launcher itself: the animations, the Acrylic effect of the window, the Discord status and looking for updates when it opens. The Acrylic and Discord options moved there from the Graphics tab. The tabs stay where they were, now with just their names.
- **Soft animations you can notice.** The tabs and the selectors (resolution, graphics engine, VSync...) have a gold pill that slides to the choice you click and lights up under the mouse, pages rise into place when you change them, panels fold away and unfold when something changes (for example when you switch between joining a friend's room and creating your own in the Online tab), buttons glow softly under the mouse, switches slide, the launcher comes in piece by piece when it opens and the PLAY button gently glows in gold while the game is not running. They cost nothing when you are not clicking, they turn off by themselves if Windows has animations off, and there is a switch for them in the menu.
- **The launcher fades and sinks a little when you minimise it**, and comes back softly (it follows the same animations switch in the menu).
- **A logo for MH3U NativePC.** A new emblem (a great sword planted in a rock, with the moon and a volcano behind it) is now the icon of `MH3U.exe` and of its window.
- **A Mods section** for what only reads the game and draws over it: the **monsters' life** (a big bar and name for the main monsters, a thin bar for the small ones) and the **damage meter with DPS**. Each one is switched on by itself, they sit in the top-right corner (no longer tied to the FPS counter), you can drag each with the mouse while F1 is open and put them back from F2, and they use the launcher's colours, like the FPS counter.
- **Cheats section** in the launcher (Settings tab, off by default): One Hit Kill (your hits do xN damage), infinite sharpness, more zenny and infinite items used in a quest (potions, traps, whetstones and the ammo of bowguns). One Hit Kill never makes a hit above 10 000 base damage, so shots from bowguns and bows hurt too. A warning tells you that cheats can alter or corrupt your save before you turn them on.
- The first time you play after updating, the game is built again (the cheats need new hooks).

### Fixed
- **Long sessions stay light.** The game used to pile up about 30 idle background threads every minute (thousands after an hour or two, most of them in online rooms); they now end when they are done, so the game keeps a steady number of threads and a little less memory.
- **Much smaller game log.** `mh3u_latest.log` used to grow to several MB in a long session (three quarters of it was one repeated graphics line); it now stays about ten times smaller, so it is easier to send when you report a problem.
- **Rebuilding after an update now really starts over when it has to.** If an update changed the game's code (like the cheats do), the launcher used to build the old code again and leave the new parts out, so some new features did nothing. It now makes the code again whenever the build is out of date.
- **Cheats that cannot work now tell you.** If a cheat needs a part your compiled game does not have, the launcher says so when you press PLAY and offers to build the game again; the game also says it in its log. The build window warns when the launcher has no hooks list.

### Removed
- **The blacksmith wishlist, the forge line in the item menu and the Mods page of the pause menu.** They are gone, and so are the settings that turned them on. F1 still opens the settings and controls (and now lets you drag the life and damage panels), and F2 the quick settings.
- **The two boxes for the hunter's name.** Type the name of a new hunter in the game itself, with its own keyboard; with a saved game the launcher keeps using that hunter's name for Discord and the online rooms, as before.

### Changed
- **The explanations show when the mouse is over an option.** The little texts under the options are now tooltips, shown in a small panel with the colours of the launcher that fades in softly, and the options that have one start with a 💡.
- **The PLAY button is as wide as its text, with some room**, and sits in the middle instead of stretching across the whole window.
- **The program is now called MH3U NativePC.** The window title, the header, the footer, the file properties of `MH3U.exe` and the Discord status say so, and the project page on GitHub moved to `G30vamv/MH3U-NativePC` (the old address keeps working). Nothing changes in how it plays or updates.

## [0.9.12] - 2026-11-06

### Added
- **Faster graphics on NVIDIA and AMD cards.** The game now prepares each frame's drawing on a second thread, so the frame rate goes up by about a quarter in the village and a fifth indoors (measured on an RTX 4070 and on the Radeon inside a Ryzen) and it is smoother, with fewer hiccups. It is on by default (*Automatic*); Intel graphics stay as before until they can be tried. It uses roughly 1 GB more memory.

### Fixed
- **No more freezing when opening the item box or the equipment screens on AMD cards.** On a Radeon RX 6600 the picture could freeze or the game closed with a "graphics card stopped" message after opening the box and choosing "Change equipment", especially with decorations and jewels. It is fixed, at 1x and with 2x + FSR.
- **The graphics thread no longer eats memory on AMD cards.** The thread that had to be switched off on AMD (it made the card hold on to gigabytes of memory in those same screens) now works fine.

### Changed
- **One setting for the graphics threads.** "GPU queue on its own thread" in Graphics is now **"Graphics in parallel (more FPS)"** with two choices: *Automatic* (recommended) and *Off*. Try *Off* if you see flickering or things that disappear.

## [0.9.11] - 2026-11-03

### Fixed
- **Updates no longer throw away the graphics the game had saved.** Until now, after almost every update the game forgot the shaders and effects it had prepared, so the first scenes stuttered and some things were missing for a few seconds. They are now kept unless an update really changes how they are made. The first time after this update the game still rebuilds them once.

### Added
- **A bit more information in the log.** When the FPS counter is on, the log now also says how busy each part of the game is and how long the graphics card takes to finish each frame. It helps to find out why a PC is slow when you send a log.

## [0.9.10] - 2026-11-03

### Fixed
- **A clear message instead of a frozen picture.** If the graphics card stops answering (a driver crash or a reset of the card), the game now tells you what happened, suggests DirectX 12 or a lower resolution, and closes, instead of staying on a frozen picture with the sound still playing. This was meant to come with 0.9.9 and I forgot to put it in.

## [0.9.9] - 2026-11-03

### Fixed
- **The picture no longer freezes on AMD graphics cards.** On AMD cards the game could freeze (sound and network kept going) a few seconds after opening the item box or the equipment screen in your house. The game now splits its graphics work between two threads only on NVIDIA cards, where it makes the game faster. On AMD and Intel it keeps everything on one thread, so it is a little slower on a weak processor but no longer runs out of memory.

### Added
- **A setting for it.** Graphics now has "GPU queue on its own thread": *Automatic* (recommended, the choice above), *Always on* and *Off*. Hover over it for a short explanation.

## [0.9.8] - 2026-11-02

### Changed
- **"Your IP for friends" refreshes itself.** If Radmin VPN, Tailscale or ZeroTier connects after the launcher is open, its address now shows up when you open the Online tab or press the new refresh button. Home-network addresses are labelled as working only on the same network.
- **Joining your own address.** If you choose "Join a friend's room" but the address is your own PC, the launcher now warns you that it would create your own room instead of joining.
- The log of the previous game session is kept as `mh3u_anterior.log`, so a short session no longer wipes the log of a long one.

## [0.9.7] - 2026-11-02

### Fixed
- **Strange pictures on top of the scenery after a hunt.** When you finished a monster, the game keeps a picture of the last hit for the results screen. Later, some other texture (the bushes of the next quest, the title screen...) could end up drawn with that picture. Textures now always show their own image.

## [0.9.6] - 2026-11-01

### Fixed
- **Characters have their right colours again.** Your hunter, your Palico and the monsters were drawn with a cold blue-green tint, as if a cyan lamp was lighting them, and some looked plain green (the Great Jaggi, the fish...). Armour, skin and fur now look like they do on the console. Scenery was never affected.
- The first time you play after updating, the game rebuilds its graphics cache, so the first scenes may stutter a little. It happens only once.

## [0.9.5] - 2026-10-31

### Fixed
- **Firewall permissions never got created.** The launcher was meant to open Windows' firewall for the game and the room server when you switched online on, but the command it used was rejected by Windows without any message, so nothing was ever set up. That is why Windows' "Allow access" windows kept appearing, only for some of you, and why friends could be left out (Radmin VPN counts as a "public" network). It now works: when you press PLAY with online on, the launcher checks the firewall and, if the game is blocked or not allowed on every network, fixes it with a single administrator confirmation. It also removes the "Block" rules Windows creates when "Cancel" is pressed on its window.

### Changed
- **Easier room setup.** The room, address and name you type in the Online tab are used when you press PLAY; "Save" is no longer needed. The launcher warns you if you host a room without an address your friends can reach.
- **"Test connection"** now asks the room's server itself instead of sending a ping, so it shows whether your friend can really be reached.

### Added
- **Network diagnosis** button in the Online tab: checks the firewall, your addresses and the connection with your friend, and says what to fix.
- You can play in the same room as friends who use Cemu, through MH3U Revival.

## [0.9.4] - 2026-10-31

### Fixed
- The log no longer fills up with thousands of repeated graphics errors when the picture freezes, and it now says why the graphics card stopped working. This helps find the cause of the picture freezing for some players while the sound and the online session keep going.

## [0.9.3] - 2026-10-31

### Fixed
- **Joining a friend's room.** If you typed the host's address and pressed PLAY without saving it first, the launcher ignored it, started a room server of its own and you ended up alone in your own world. It now uses the address you typed.
- **Black or half-drawn screen on laptops with integrated graphics** when the game ran out of graphics memory: the game now keeps smaller caches on integrated GPUs and recovers on its own if memory runs out.
- The graphics API chosen in the launcher (Vulkan or DX12) is now really used.

### Added
- The log now lists the graphics card, its driver and the features it supports, to help with reports.

## [0.9.2] - 2026-10-31

### Added
- **In-game settings menu.** Press F2 while playing (or F1 for the full overlay) to change the internal resolution, upscaler, sharpness, V-Sync mode, FPS counter, camera sensitivity and language without leaving the game. The game's B button closes it. What you change is remembered and shows up in the launcher the next time you open it.
- **Camera sensitivity for the controller's right stick**, in the Controls tab and in the in-game menu.
- **Language setting for the in-game menu** (English or Spanish, Windows' language by default), in the Graphics tab.
- The in-game menu now uses the launcher's blue.

### Fixed
- **Room names and chat messages can be typed in game.** The keyboard used to fill in your hunter name every time it appeared; now it only does that when you create a new hunter. Enter accepts the text.
- **Dark patches in the shadows** after changing the internal resolution during a hunt.

## [0.9.1] - 2026-10-31

### Removed
- Old artwork.

## [0.9.0] - 2026-10-30

A big visual and graphics release.

### Added
- **AMD FidelityFX Super Resolution 1.0**, the real one: EASU upscaling followed by RCAS sharpening, ported to WGSL from AMD's MIT-licensed reference (`mh3u-gfx/src/fsr.rs`). It replaces the previous home-made "FSR" (a four-tap bilinear with a sharpening term). It is independent of the internal resolution; when the internal image is already as large as the window, only the RCAS sharpening is applied. FSR 2/3/4 are not an option for this port: they are temporal and need motion vectors, depth and jitter that a recompiled Wii U game does not provide (FSR 4 also needs an RDNA 4 GPU).
- **New glass interface** (PySide6 / Qt): frosted translucent panels over a soft backdrop in the Moga / Tanzia palette, the game banner fading into the header, an in-window title bar with palette-gold hover on the window buttons, and a footer drawn straight on the background.
- **Optional Windows Acrylic** (Graphics tab, restart required): lets the desktop show through the window. Leave it off on Windows 10.
- **Controls tab** with the interface for the upcoming universal button mapper (marked as coming soon). The controller layout and mouse camera sensitivity moved here from the Graphics tab.
- **Live "Active settings" summary** on the main tab: resolution, upscaler and sharpness, VSync, graphics API, window mode, FPS counter, input, controller layout, camera sensitivity, mods, audio, LTO and online status, updated as you change them.
- Link to this repository in the credits.

### Changed
- The launcher is now built with PySide6 instead of CustomTkinter. The launcher logic moved to `core.py` unchanged; the executable grows from about 22 MB to 34 MB, starts as fast as before, uses no CPU while idle and about 85 MB more RAM (around 160 MB in total).
- The Graphics tab no longer has the "FSR preset" selector: it silently changed the internal resolution and could not be combined with 4x. Resolution and upscaler are now independent settings.
- `mh3u-gfx`: the hasher no longer needs a deprecated slice iterator (same output, clean `clippy`).
- Repository documentation, release titles and notes are now in English.

### Fixed
- Visible square edges in the glass backdrop gradient.
- The update path was re-verified against the updater of the previous release (every manifest path and extension is accepted by it).

## [0.8.9] - 2026-10-30

### Fixed
- Auto-update was broken for every installed version because v0.8.8 shipped `assets/banner.jpg`, an extension the updater of older launchers rejects, and the update manifest is global. The banner is a PNG again and the updater now also accepts `.jpg`.

## [0.8.8] - 2026-10-30
### Changed
- Original launcher artwork replaces the official Capcom artwork that had been used by mistake; `logo.png` removed.

## [0.8.7] - 2026-10-30
### Added
- Detects a gamepad hidden by HidHide (for example by DSX) and offers to let `mh3u-tools.exe` use it (one UAC prompt).
### Changed
- The HID gamepad reader steps aside while an XInput pad is connected, to avoid double input.

## [0.8.6] - 2026-10-30
### Added
- Direct DualSense, DualShock 4 and generic HID gamepad support, read straight from the device (USB and Bluetooth). `MH3U_HID_PADS=0` turns it off.

## [0.8.5] - 2026-10-29
### Fixed
- The launcher relaunches cleanly after an update (it no longer inherits PyInstaller's environment, which caused "Failed to load Python DLL").

## [0.8.4] - 2026-10-29
### Changed
- The portable Clang download is partial (about 90 MB instead of 182 MB).
- Translating and compiling no longer opens a black console window.

## [0.8.3] - 2026-10-29
### Fixed
- The update script no longer dies silently (it was launched detached and its `tasklist | find` pipe failed); UTF-8 paths with accents work.

## [0.8.2] - 2026-10-29
### Changed
- The update button and status moved to the header badge.

## [0.8.1] - 2026-10-29
### Added
- Custom colour selector fix (GX2 tiling apertures), gamepad input while the window is unfocused, and a "gamepad or keyboard" selector, synced with upstream pull requests #31-#34.

## [0.8.0] - 2026-10-29
### Added
- Remote updates with SHA-256 verification, backup and rollback; full package in a single zip; AGPL-3.0 licensing with the corresponding source in `source-patches/`.

[0.9.0]: ../../releases/tag/v0.9.0
[0.8.9]: ../../releases/tag/v0.8.9
