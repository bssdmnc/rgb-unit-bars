# AGENTS.md — RGB Unit Bars

Guide for AI agents (and humans) who need to maintain this project or reproduce it for another game client, keyboard or firmware.

## What the project does

World of Warcraft health, power (mana / rage / energy / focus / runic power) and combo points are shown live as bars on an RGB keyboard.

```
WoW client ──(addon draws a pixel strip)──▶ screen ──(desktop app grabs a 24×1 px row per corner)──▶ renderer ──(USB HID)──▶ keyboard LEDs
```

No game memory is read and no input is sent to the game. The addon only draws a few pixels; the desktop app only reads those pixels. This is the same model as official RGB integrations, and it keeps the project inside Blizzard's addon rules.

## Repository layout

| Path | Purpose |
|---|---|
| `addon/RGBUnitBars/` | WoW addon (Lua). Encodes unit state into a pixel strip at a corner of the game window. |
| `app/rgbunitbars/` | Desktop app (Python 3.11+). `wow_link.py` decodes the strip, `render.py` maps state to per-key colors, `devices/` talks to keyboards. |
| `app/rgbunitbars/devices/via.py` | Generic QMK/VIA raw HID transport (usage page `0xFF60`, usage `0x61`, 32-byte reports). |
| `app/rgbunitbars/devices/k3max.py` | Keychron K3 Max driver for the custom firmware in `firmware/keychron_k3_max/`. |
| `app/rgbunitbars/devices/openrgb_sdk.py` | OpenRGB SDK client driver (any keyboard OpenRGB drives per key). Used unless a K3 Max is plugged in (`--device auto`). |
| `firmware/keychron_k3_max/` | QMK keymap that adds a host-controlled RGB effect (`MUSIC_DIRECT`) + Fn-lock (Fn+Esc). `build.sh` builds it in WSL/Linux. |
| `extras/` | Non-WoW demos for the same firmware: `music_eq.py` (16-band audio spectrum), `music_rgb.py` (beat-reactive global color). |
| `app/rgbunitbars/engine.py` | Background thread: picks the backend, opens the keyboard, runs the read → render → send loop, publishes a status for the tray. Polls gently while waiting (WoW absent: every 2 s, strip not visible: every 0.5 s). |
| `app/rgbunitbars/tray.py`, `autostart.py`, `paths.py` | Tray icon + menu (status, keyboard, *Start with Windows*, log, update notice from GitHub Releases), HKCU `Run` autostart, `%LOCALAPPDATA%\RGBUnitBars` (log, config). |
| `app/rgbunitbars/openrgb_server.py` | Starts a hidden OpenRGB SDK server when none is listening: bundled copy (unpacked to `%LOCALAPPDATA%\RGBUnitBars\openrgb`) or the system install; isolated `--config` dir; stopped on exit. |
| `packaging/` | `build.ps1` (PyInstaller one-file exe with OpenRGB bundled + addon zip into `dist/`), `entry.py`, `icon.ico`, `THIRD_PARTY_NOTICES.md`. |
| `run.bat` | Starts the desktop app from source (`python -m rgbunitbars`, tray; add `--console` for a console run). |

## Pixel protocol (addon → app), version 3

One row of **24 physical pixels, 1 px tall**, drawn by a parent-less frame (strata `TOOLTIP`, `768 / physicalHeight` UI units per pixel, frame scale 1) at a screen corner chosen in the addon (default top-left). Every value is the **brightness of one pixel**: `encode(f) = A * (0.3 + 0.7 * f)`, amplitude `A` = 0.25 ("Dark", default, nearly invisible) or 1.0 ("Bright"). The 0.3 floor exists because the client crushes dark output: inputs below ~15 % of `A` were captured as pure black on the user's setup.

| Pixel | Content |
|---|---|
| 0 | signature `(A, 0, A)` (raw, no floor) |
| 1 | signature `(0, A, 0)` (raw) |
| 2–6 | reference ladder `encode(1), encode(0), encode(0.25), encode(0.5), encode(0.75)` |
| 7 | health fraction (grey) |
| 8 | power fraction |
| 9 | combo points / 10 |
| 10 | power type / 10 (Enum.PowerType: 0 mana, 1 rage, 2 focus, 3 energy, 6 runic power) |
| 11 | cast progress (elapsed for casts, remaining for channels) |
| 12 | casting flag (1 or 0) |
| 13–19 | colours per channel: health full, health low, mana, rage, energy, combo, cast |
| 20 | rows (combo, health, power) / 12 |
| 21 | (dim, low-health, flags pulse=1 comboFlash=2) / 12 |
| 22 | (cast mode, cast rows, row order) / 12 |
| 23 | (cast flags invert=1 mirror=2, 0, 0) / 12 |

* The app grabs four 24×1 regions (top / bottom row of the client area, left- and right-aligned), last good corner first, accepts a row only if the signatures match and the reference ladder is strictly increasing, then inverts values by piecewise-linear interpolation over the ladder — no gamma model needed.
* Cast modes: 0 off, 1 own rows, 2 instead of health, 3 instead of power, 4 instead of health + power (replacement only while casting). Row orders are the six permutations in `ORDERS` in both the addon and `wow_link.py` — keep them in sync.

* Colours 13 (health full) and 15–17 (mana, rage, energy) are resolved **per class** before they are drawn: `settings.classColors[CLASS]` override, else automatic — health = `RAID_CLASS_COLORS[class]` unless its hue is within 40° of the class's base resource colour (rogue/energy, warrior/rage, others/mana), then green; resources use the built-in mana/rage/energy colours. Old global colours are migrated into the current class on load. The app is unaware of classes.

### Secret values → colour curves (important)

Clients built on the Midnight-era engine (WoW Forever / classic beta `Interface: 16001`, retail 12.x) return **secret values** from `UnitHealth`, `UnitHealthPercent`, `UnitPowerPercent`, etc. Addons cannot do arithmetic, comparisons, `tostring` or `table.concat` with them; they can only hand them to widget setters or to curves. The addon builds a linear `C_CurveUtil.CreateColorCurve()` from `encode(0)` to `encode(1)` and calls `UnitHealthPercent("player", false, curve)` / `UnitPowerPercent("player", type, false, curve)`, which return a colour the engine computed; that goes straight into `texture:SetVertexColor(color:GetRGB())`. Combo points use plain arithmetic, falling back to `UnitPowerPercent(..., ComboPoints, false, halfCurve)` if secret. Cast progress uses `UnitCastingInfo`/`UnitChannelInfo` times, falling back to `UnitCastingDuration(...):EvaluateElapsedPercent(curve)` (channels: `UnitChannelDuration` + `EvaluateRemainingPercent`) if those times are secret. Older clients (Classic Era `11509`) have no curves and no secrets, so plain arithmetic is used. Reader errors are stored in `RGBUnitBarsDB.errors`.

## Keyboard protocol (app → K3 Max custom firmware)

VIA "custom value" command on channel 0 (`id_custom_channel`), handled by `via_custom_value_command_kb` in `firmware/keychron_k3_max/keymap.c`:

| Bytes | Meaning |
|---|---|
| `07 00 01 hueBottom hueStep b0..b15` | Spectrum bars: 16 band levels (0–255); firmware lights 6 rows bottom-up, hue = `hueBottom + hueStep * row`. One packet per frame (≈300 fps capacity). |
| `07 00 02 start count r g b …` | Raw per-LED RGB, up to 9 LEDs per packet (84 LEDs → 10 packets ≈ 30 ms). |

Any frame switches the matrix to the `MUSIC_DIRECT` effect (non-EEPROM). If no frame arrives for 1.5 s the previous effect is restored, so a crashed app never leaves the keyboard stuck. Global brightness still comes from the keyboard's own brightness keys (`rgb_matrix_get_val()`).

The standard VIA lighting channel 3 (effect / brightness / speed / colour, ids 1–4) also works and does not write EEPROM.

## Reproducing on another keyboard

1. **Desktop side** — implement a class in `app/rgbunitbars/devices/` with `name`, `leds` (list of `(x, y)` LED centres in any units, LED-index order), `send(colors)` (list of `(r, g, b)` in the same order) and `close()`; raise `DeviceUnavailable` on disconnect. Register it in `devices/__init__.py`. `KeyboardGeometry` derives rows (y clustering) and key width (median x gap), so layouts adapt automatically.
2. **QMK keyboard** — copy `rgb_matrix_user.inc`, the `music_*` block and `via_custom_value_command_kb` from `firmware/keychron_k3_max/keymap.c` into the keyboard's VIA keymap, add `RGB_MATRIX_CUSTOM_USER = yes` to `rules.mk`. Check first that the vendor code does not already define `via_custom_value_command_kb` or `housekeeping_task_user`. LED coordinates come from `g_led_config.point` in the keyboard's `.c` file.
3. **Non-QMK keyboards** — handled by `openrgb_sdk.py`: it takes the largest `MATRIX` zone of the first OpenRGB keyboard, uses `(column, row)` from `matrix_map` as LED positions (`row_tolerance = 0`), switches to the per-LED `Direct` mode while the game is visible and restores the previous mode in `idle()` 1.5 s after the strip disappears.

### Device driver contract

`name`, `leds`, `row_tolerance`, `prepare()` (connect and fill `leds`; raise `DeviceUnavailable` to make the app wait and retry), `send(colors)`, `idle()` (game not visible: hand the lighting back), `close()`.

### Testing OpenRGB without hardware

Run OpenRGB with an isolated config that defines a debug keyboard, on a spare port:

Run the automated OpenRGB selection checks from the repository root first:

```
$env:PYTHONPATH = "app"
python -m unittest discover -s app/tests -v
```

```json
{"DebugDevices": {"devices": [{"type": "keyboard", "name": "Debug Keyboard", "keyboard": true, "underglow": true}]}}
```

```
OpenRGB.exe --config <dir containing that OpenRGB.json> --server --server-port 6743 --noautoconnect
python -m rgbunitbars --device openrgb --openrgb-port 6743
```

Read back `client.devices[0].colors` through `matrix_map` to assert which keys are lit. The debug keyboard has a 21×6 ANSI key matrix plus a 10×3 underglow matrix — a good check that only the key matrix is driven.

When OpenRGB exposes several keyboard candidates, the app prefers a per-key Direct mode and then the candidate with the largest MATRIX zone. Use `--keyboard <name>` to select a specific device by name.

## Releasing

1. Bump `app/rgbunitbars/__init__.py` `__version__` **and** `## Version` in `RGBUnitBars.toc` — they must match (the pixel protocol changes in lock-step; `build.ps1` refuses mismatches).
2. `powershell packaging\build.ps1` (needs Python with `app/requirements.txt` + `pyinstaller`, and OpenRGB installed in `C:\Program Files\OpenRGB` or `OPENRGB_DIR`). Output: `dist/RGBUnitBars-<v>.exe` (~50 MB) and `dist/RGBUnitBars-<v>.zip` (addon, `RGBUnitBars/` at the zip root).
3. GitHub Release `v<v>` on `bssdmnc/rgb-unit-bars` with the exe attached — the tray's update check reads `releases/latest`, the addon's first-login popup links to the releases page (`APP_URL` in the Lua, `GITHUB_REPO` in `tray.py`).
4. Upload the zip to CurseForge. CurseForge rejects executables and external file links, so the exe never goes there.

Packaged-app behaviour: single instance (named mutex `Local\RGBUnitBarsSingleInstance`), the first packaged run enables *Start with Windows* once (`config.json: autostart_initialized`), the tray toggles it. When testing a packaged build on a dev machine set `autostart_initialized` first so the Run key does not point at `build/out`.

## Building the K3 Max firmware

`firmware/keychron_k3_max/build.sh` (run inside WSL Ubuntu or Linux, no sudo needed): clones Keychron's `wireless_playground` branch, downloads ARM GNU toolchain 13.3 into `$WORK`, installs the `qmk` Python package into a venv, copies the keymap as `rgbunitbars` and builds `keychron/k3_max/ansi/rgb:rgbunitbars`.

Flashing (user does this): QMK Toolbox → open the `.bin` → unplug keyboard, switch to cable mode, hold **Esc** while plugging in (STM32 ROM DFU) → Flash. The ROM bootloader cannot be erased, so the official `.bin` can always be re-flashed. VIA keymap/EEPROM resets on every new build, which is why Fn-lock is compiled into the default keymap.

## Gotchas found the hard way

* **2.4 GHz dongle (Keychron Link) does not forward VIA raw HID** — everything needs the USB cable in cable mode.
* **hidapi `read(n, 0)` blocks forever** (timeout 0 = blocking). Use `set_nonblocking(1)` to drain the queue. `read(n, 1)` costs ~15 ms on Windows (timer resolution) — that made every command 15 ms instead of 3 ms.
* **Match replies to requests**: another process talking to the keyboard (or a late reply) shifts responses by one. `ViaDevice.command` compares the echoed command bytes.
* **`dfu-suffix: not found`** at the end of the QMK build is harmless; the `.bin` is already produced. `build.sh` tolerates it.
* **Stock older Keychron firmware** answers `0xFF` (unhandled) to Keychron per-key RGB commands (`0xA8`), and Keychron's newer per-key mode cannot switch individual LEDs off (brightness is global) — hence the custom effect.
* **Lua errors are written to `<WoW>/_classic_beta_/Logs/General.log`** (`[E][Lua] Lua Error: …`) — read this instead of asking the user to enable script errors.
* **K3 Max LEDs face north**: each key's light shows in the gap *above* it, so adjacent rows visually bleed into the row above. Group colours in pairs of rows (combo points use F-row + number row) to keep borders clean.
* **Exclusive fullscreen** breaks GDI screen capture; use windowed or borderless.
* `soundcard` loopback capture works on Python 3.14; `mss.mss()` is deprecated — use `mss.MSS()`.
* **openrgb-python hangs inside `OpenRGBClient()`** on `requestPluginList` against OpenRGB 1.0 (blocking socket read). Connect with `protocol_version=3` (no plugin query) under a temporary `socket.setdefaulttimeout`.
* OpenRGB may describe underglow / logo LEDs as extra `MATRIX` zones; merging them corrupts the row geometry. Drive only the largest matrix zone and send black to the rest.

## Conventions

* No inline code comments (project owner preference); docstrings only where they add real value.
* Keep the addon dependency-free and taint-safe: no secure frames, no combat-lockdown APIs, only `pcall`-guarded reads.
* Everything that touches the keyboard must fail soft (`DeviceUnavailable`) and retry; the firmware timeout restores lighting on its own.
