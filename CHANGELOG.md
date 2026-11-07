# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). While the project is below 1.0, every release raises the last number of the version (`0.MINOR.PATCH`), whether it brings fixes or new things; see "Versions and releases" in the [README](README.md). A published version is never replaced: a fix comes as a new version.

Every entry is also published as the notes of its [GitHub Release](../../releases). The interface of the launcher is still in Spanish; a full English translation is planned.

## [Unreleased]

### Added
- **A logo for MH3U NativePC.** A new emblem (a great sword planted in a rock, with the moon and a volcano behind it) is now the icon of `MH3U.exe` and of its window.

### Changed
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
