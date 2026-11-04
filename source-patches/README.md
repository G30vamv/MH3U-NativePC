# Corresponding source of `mh3u-tools.exe` (AGPL-3.0)

`mh3u-tools.exe` in the Releases is built from [glinesbdev/mh3u-port](https://github.com/glinesbdev/mh3u-port) (AGPL-3.0) plus the changes in these patches. The patches are under **AGPL-3.0**, like the original project.

- **Base:** commit `41d3a9b` of `glinesbdev/mh3u-port` (26 Oct 2026, *Merge pull request #34*).
- **Order:** `0001` and `0002` are independent of each other; `0003` goes after `0002`, `0004` after `0003`, `0005` after `0004`, `0006` after `0005`, `0007` after `0006`, `0008` after `0007`, `0009` after `0008`, `0010` after `0009`, `0011` after `0010`, `0012` after `0011` and `0013` after `0012`.

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
| `0012-graphics-in-parallel.patch` | The game's graphics work moves off the game's thread: the calls are copied in order (with what each draw reads from the game's memory, copied once) to a thread of its own that works out the draws (`front.rs`, `mirror.rs`), each draw sets only the pass state that changed, the scene is read every 8 frames, and the caches' translator-only key. On by default only on NVIDIA cards (`MH3U_GFX_RESOLVER=thread\|off`). This work-in-progress version still carries the test switches (`MH3U_GFX_ADAPTER`, `MH3U_WINDOW_ACTIVE`, `MH3U_GFX_FRONT_TIMES`, `MH3U_GFX_FRAMES_AHEAD`, `MH3U_GFX_BATCH`), which go before it is published. |
| `0013-cheats.patch` | The launcher's Cheats section (opt-in, `MH3U_CHEATS`): One Hit Kill, infinite sharpness, invincible (the hits on the hunter), more zenny, infinite items, and two read-only helpers drawn over the game: life bars for the monsters and a damage meter with DPS (`cheats.rs`, `combat.rs`, the overlay; with tests). Off unless the player turns it on in the launcher. |

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
git apply --ignore-whitespace <path>/0013-cheats.patch
cargo build --release -p mh3u-tools
```

Verified: the twelve patches apply cleanly on `41d3a9b`, `mh3u-latte` tests (including the two added by 0007) pass, and the `mh3u-gfx` tests (including the FSR shader checks) pass on that tree. The original project's own checks (`fmt`, `clippy -D warnings`) were not run on the patched tree as a whole.
