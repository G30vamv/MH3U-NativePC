# Corresponding source of `mh3u-tools.exe` (AGPL-3.0)

`mh3u-tools.exe` in the Releases is built from [glinesbdev/mh3u-port](https://github.com/glinesbdev/mh3u-port) (AGPL-3.0) plus the changes in these patches. The patches are under **AGPL-3.0**, like the original project.

- **Base:** commit `41d3a9b` of `glinesbdev/mh3u-port` (26 Oct 2026, *Merge pull request #34*).
- **Order:** `0001` and `0002` are independent of each other; `0003` goes after `0002`, `0004` after `0003`, `0005` after `0004`, `0006` after `0005`, `0007` after `0006`, `0008` after `0007`, `0009` after `0008`, `0010` after `0009`, `0011` after `0010`, `0012` after `0011` `0013` after `0012`, `0014` after `0013`, `0015` after `0014` `0016` after `0015`, `0017` after `0016`, `0018` after `0017`, `0019` after `0018` and `0020` after `0019`.

| Patch | Contents |
|---|---|
| `0001-gfx-and-build-performance.patch` | Release profile with fat LTO, fast hasher (`fxmap.rs`), GPU queue on its own thread (`queue.rs`; `MH3U_GFX_THREAD=off` disables it), **AMD FidelityFX Super Resolution 1.0** (`fsr.rs`: EASU + RCAS ported to WGSL from AMD's MIT-licensed `ffx_fsr1.h`; used when `MH3U_UPSCALER=fsr`, the default) and other `mh3u-gfx` adjustments. |
| `0002-runtime-online-and-translator.patch` | Online networking of the runtime (`net.rs`: server redirection, NAT, local IP), changes in `game.rs`, `cafe.rs`, `sync.rs`, `kernel.rs`, `guest.rs` and the translator's function discovery (`discover.rs`). |
| `0003-gamepad-hid-support.patch` | DualSense, DualShock 4 and generic HID gamepads read straight from the device (`hidpad.rs`; `MH3U_HID_PADS=0` disables it). |
| `0004-ingame-settings.patch` | The in-game settings window (F1 / F2) in the overlay (`settings.rs`, `overlay.rs`, `gx2.rs`): resolution, upscaler, sharpness, present mode, FPS counter, language and camera sensitivity; text for the game's keyboard prompts (`swkbd.rs`); right-stick sensitivity (`input.rs`). |
| `0005-low-memory-gpus-and-gpu-report.patch` | Smaller buffer caches on integrated GPUs and recovery when the device runs out of memory (`draw.rs`); the graphics API picked with `WGPU_BACKEND` is honoured, an optional DXC shader compiler for DX12 (`dxcompiler.dll` beside the exe) and the adapter / features lines in the log (`lib.rs`). |
| `0006-gpu-error-reporting.patch` | Says in the log why the graphics device was lost and no longer floods it with repeated graphics errors (`lib.rs`). |
| `0007-fix-character-colours.patch` | Fixes the colours of characters (a cold blue-green tint): in a group of dot products the output modifier (times 2, times 4, divided by 2) and clamp of the instructions after the first were skipped, and pixel shaders that ask for the fragment position now receive it (the fog depth of characters) (`translate.rs`, with tests; `draw.rs`). Also renews the on-disk shader translation cache. |
| `0008-fix-stale-colour-buffers.patch` | Fixes textures drawn with the picture of an old render target: the game's colour buffers (such as the screenshot kept at a monster's last hit for the results screen) were remembered by memory address for ever and were drawn over any texture the game later put in that memory. A buffer is now only used when the texture read there has the buffer's size (`draw.rs`, `gx2.rs`, with a test); the log says once when one is skipped. |
| `0009-gpu-queue-thread-by-vendor.patch` | The GPU queue's own thread (from `0001`) is now on by default only on NVIDIA cards: on AMD cards it made the driver hold on to gigabytes of memory in screens with many draws (the item box) until the device was lost, and cards that share the system's memory (Intel's) are kept on the game's thread too. `MH3U_GFX_THREAD=on` or `off` decides for any card (`queue.rs`, `lib.rs`). |
| `0010-device-lost-closes-the-game.patch` | When the driver takes the graphics device away (a GPU reset or crash) the game shows a message (English or Spanish) and closes, instead of going on with a frozen picture; the log says on which card, in which scene and at which frame (`lost.rs`, `lib.rs`, `error_box` in `mh3u-rt`). `MH3U_DEVICE_LOST_EXIT=off` keeps the old behaviour. |
| `0011-caches-survive-updates-and-thread-times.patch` | The on-disk caches of translated shaders and pipelines are now named after a hash of the translator's sources only (`build.rs`, `translations.rs`, `docs/translator.md`), so a release that changes just the rest of the graphics code no longer throws them away. Two new lines in the timing report: `[gfx threads]` (the CPU each thread used, `thread_cpu_times` in `mh3u-rt`) and `[gfx gpu]` (how long the GPU takes to finish a frame once the queue has all its work; `perf.rs`, `queue.rs`). |
| `0012-graphics-in-parallel.patch` | The game's graphics work moves off the game's thread: the calls are copied in order (with what each draw reads from the game's memory, copied once) to a thread of its own that works out the draws (`front.rs`, `mirror.rs`), each draw sets only the pass state that changed, the scene is read every 8 frames, and the caches' translator-only key. On by default only on NVIDIA cards (`MH3U_GFX_RESOLVER=thread\|off`). |
| `0013-geometry-batches-and-threads-on-amd.patch` | A batch of draws is handed to the GPU after every 32 draws with a geometry shader (`MH3U_GFX_GS_BATCH=<n>` changes it, `0` turns the limit off): hundreds of them in one batch (the interface of the equipment screens) made the driver of a Radeon RX 6600 lose the device and, with the GPU queue on its own thread, made AMD cards hold on to gigabytes of memory. With that fixed, the two graphics threads (`0009`, `0012`) are on by default on AMD cards as well as NVIDIA (`queue.rs`, `front.rs`); Intel stays on the game's thread. |
| `0014-cheats.patch` | The launcher's Cheats section (opt-in, `MH3U_CHEATS`): One Hit Kill, infinite sharpness, more zenny, infinite items, and two read-only helpers drawn over the game: life bars for the monsters (with the game's own monster names, in English or Spanish) and a damage meter with DPS (`cheats.rs`, `combat.rs`, the overlay; with tests). Off unless the player turns it on in the launcher. |
| `0015-guest-threads-end-for-real.patch` | When a game thread ends by calling the system's exit, its host thread now really ends (on Windows) instead of sleeping for ever: the process used to gather about 30 sleeping threads a minute, thousands in a long online session (`kernel.rs`). The `[gfx mirror]` lines of `0012` are now printed once per report window (10 s) instead of every 120 frames, which was three quarters of a long session's log (`front.rs`). |
| `0016-remove-glinesbdevs-mods.patch` | Takes out the blacksmith wishlist, the forge status line in the item menu, the Mods page of the pause menu and the crate and hooks they used (`mh3u-mods`, `events.rs`, `native_menu.rs`, `native_text.rs`, `menu_probe.rs`, the wishlist and events windows of `overlay.rs`, and the extra entries of `mods/hooks.txt`), which are not part of this project. The overlay keeps its Settings and Controls windows, the on-screen panels and the keyboard window; `mods/hooks.txt` keeps the five hooks the cheats and the life and damage panels use. The game's text buffer constant moved to `cafe.rs` (same address). |
| `0017-log-time-and-graphics-card-choice.patch` | Every line of the game's log now starts with the local time (`[14:03:22.481] [gfx frames] ...`), so it can be set beside the room server's log (`logstamp.rs`; `MH3U_LOG_TIME=off` leaves the log as it was). `MH3U_GFX_ADAPTER=<part of a card's name>` makes the game draw with that graphics card (the launcher's Graphics card list); if none matches, the log lists the cards and the usual choice is used (`lib.rs` of `mh3u-gfx`). |
| `0018-geometry-draws-in-one-compute-pass.patch` | The compute work of the draws with a geometry shader (hundreds in the equipment screens) is recorded when the batch goes to the GPU: one clear of what they write and one compute pass for all of them, instead of two passes and two clears for each draw (`geometry.rs`, `draw.rs`). On an integrated Radeon the equipment screen runs about 7 % faster and the game's peak memory fell by some 1.7 GB. `MH3U_GFX_GS_GROUP=off` goes back to the old way. |
| `0019-damage-meter-and-camera-stick-fixes.patch` | Several fixes in one. **Damage meter:** a monster's fall of life is counted as the damage of the hunters whose hits came in the last second (by the hits' base damage) instead of in the last 3 frames, so a player in a room, who gets the monsters' life from the host a moment late, sees their own damage and DPS; the panel also lists every hunter whose hits this machine sees; the monsters' kind is told by the byte at `+3` of their state; each monster is told once in the log, which also gets the first hits and falls of life (`combat.rs`, `cheats.rs`, the damage panel of `overlay.rs`). **Camera stick:** the right stick is scaled as a vector that keeps its angle, its dead zone is applied to its pushed length and its direction buttons follow the stick as pushed, so a low or a high sensitivity no longer loses looking up and down (and aiming) (`input.rs`; `MH3U_TRACE_STICK=1` writes what the game gets). |
| `0020-gamepad-button-remapper.patch` | The button remapper: `MH3U_PAD_MAP` (`B>A,A>B,ZL>`: what each button of a pad counts as, or none) is applied to the GamePad buttons after every pad reader (gilrs, XInput, HID) has made them with the layout, except for the combination that opens the overlay and the buttons of the sticks (`padmap.rs`, `input.rs`, with tests); `mh3u-tools pad-listen` writes `down NAME` / `up NAME` for each button pressed on the connected pads, which is how the launcher asks the player to press the button to map (`mh3u-tools/src/main.rs`). |
| `0021-bowgun-aim-with-the-stick.patch` | The bowgun's vertical aim: the game moves the aim with orders that nothing sets on this port, so the aim never went up or down. A hook on the per-frame update of a ranged weapon's aim (`aim_pitch`, listed in `mods/hooks.txt`) moves the target pitch from the right stick, scaled by the camera sensitivity, with the game's own limits, both aiming through the sight and in third person (`cheats.rs`, `input.rs`); the diagnostic of the bowgun's aim is removed (`combat.rs`, `cafe.rs`). |

## Reproducing the binary

```powershell
git clone https://github.com/glinesbdev/mh3u-port.git
cd mh3u-port
git checkout 41d3a9b
git apply --ignore-whitespace <path>/0001-gfx-and-build-performance.patch
git apply --ignore-whitespace <path>/0002-runtime-online-and-translator.patch
git apply --ignore-whitespace <path>/0003-gamepad-hid-support.patch
git apply --ignore-whitespace <path>/0004-ingame-settings.patch
git apply --ignore-whitespace <path>/0005-low-memory-gpus-and-gpu-report.patch
git apply --ignore-whitespace <path>/0006-gpu-error-reporting.patch
git apply --ignore-whitespace <path>/0007-fix-character-colours.patch
git apply --ignore-whitespace <path>/0008-fix-stale-colour-buffers.patch
git apply --ignore-whitespace <path>/0009-gpu-queue-thread-by-vendor.patch
git apply --ignore-whitespace <path>/0010-device-lost-closes-the-game.patch
git apply --ignore-whitespace <path>/0011-caches-survive-updates-and-thread-times.patch
git apply --ignore-whitespace <path>/0012-graphics-in-parallel.patch
git apply --ignore-whitespace <path>/0013-geometry-batches-and-threads-on-amd.patch
git apply --ignore-whitespace <path>/0014-cheats.patch
git apply --ignore-whitespace <path>/0015-guest-threads-end-for-real.patch
git apply --ignore-whitespace <path>/0016-remove-glinesbdevs-mods.patch
git apply --ignore-whitespace <path>/0017-log-time-and-graphics-card-choice.patch
git apply --ignore-whitespace <path>/0018-geometry-draws-in-one-compute-pass.patch
git apply --ignore-whitespace <path>/0019-damage-meter-and-camera-stick-fixes.patch
git apply --ignore-whitespace <path>/0020-gamepad-button-remapper.patch
git apply --ignore-whitespace <path>/0021-bowgun-aim-with-the-stick.patch
cargo build --release -p mh3u-tools
```

Verified: the twenty patches apply cleanly on `41d3a9b` in that order, `mh3u-latte` tests (including the two added by 0007) pass, and the `mh3u-gfx` tests (including the FSR shader checks) pass on that tree. The original project's own checks (`fmt`, `clippy -D warnings`) were not run on the patched tree as a whole.
