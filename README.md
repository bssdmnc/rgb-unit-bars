# RGB Unit Bars

Your World of Warcraft health, power and combo points — live on your RGB keyboard.

The Keychron K3 Max currently connects by USB cable; Bluetooth support is planned.

| Class / resource | Keyboard layout (top → bottom) |
|---|---|
| Class | Default rows |
|---|---|
| Rogue | 2 combo · 2 health · 2 energy |
| Warrior, Hunter | 3 health · 3 power |
| Druid | 2 health · 2 power · 2 cast; power colour follows form |
| Other classes | 2 health · 2 power · 2 cast |

* Health uses your class colour (green when it would clash with your resource) and fades to red, pulsing below 25 %. Health and resource colours can be changed per class in `/rub`.
* Combo points are enabled by default for rogues only; they light up in five groups and flash at 5 — finisher time.
* Level-ups fill the keyboard with a hot-orange disk expanding from the center, keeping passed keys dimly shimmering until the return phase contracts a vertical orange band with two fading sparks; lighting stays off after death until you release your spirit, then a neutral gray-white wave continues until resurrection.
* Test these effects in-game with `/rub dev levelup` or `/rub dev dead`; run `/rub dev clear` afterward to restore your actual alive/dead state. `/rub dev` lists these commands.
* Empty parts of a bar stay faintly lit so you always see the full scale.
* Optional cast bar: its own rows, or taking over the health / power rows while you cast. Row order, fill direction and colour are set in `/rub`.

Works on WoW Forever / Classic beta (`Interface 16001`) and Classic Era (`11509`). No memory reading, no input automation: the addon draws one row of 24 dark pixels at the edge of the game window and the desktop app reads it.

## Supported keyboards

| Keyboard | Status |
|---|---|
| Any per-key RGB keyboard supported by [OpenRGB](https://openrgb.org) (Razer, Corsair, Logitech, SteelSeries, ASUS, HyperX, MSI, …) | ✅ via the OpenRGB SDK server |
| Keychron K3 Max (ANSI, RGB) | ✅ directly, with the custom firmware in `firmware/keychron_k3_max/` |
| Other QMK keyboards with VIA | 🛠 port the firmware block (see `AGENTS.md`) |

Keyboards that OpenRGB only exposes as a single zone (no per-key matrix) get one row instead of bars.

## Install (Windows)

1. **Addon** — install *RGB Unit Bars* from CurseForge (or copy `addon/RGBUnitBars` into `World of Warcraft\_classic_beta_\Interface\AddOns\` / `_classic_era_`). On your first login it shows a link to the desktop app; `/rub app` shows it again.
2. **Desktop app** — download `RGBUnitBars-<version>.exe` from [GitHub Releases](https://github.com/bssdmnc/rgb-unit-bars/releases) and run it once. It lives in the system tray, starts with Windows (untick *Start with Windows* in the tray menu to stop that) and wakes up by itself when WoW is open. No Python, no setup.
3. **Game settings** — use *Windowed* or *Windowed (Fullscreen)* mode.

The app ships with [OpenRGB](https://openrgb.org) 1.0 inside: if no OpenRGB server is running, it starts its own copy in the background (no window) and stops it on exit. If you already use OpenRGB, enable its **SDK Server** and the app uses that instead. If the keyboard does not react, close vendor RGB apps (Synapse, iCUE, G HUB…) — they fight over the lighting.

The tray menu shows the current status and the keyboard in use, opens the log (`%LOCALAPPDATA%\RGBUnitBars\log.txt`) and tells you when a new release is out. When the game is minimized or loading, the keyboard returns to its previous lighting after 1.5 s.

### Running from source

Python 3.11+: `pip install -r app/requirements.txt`, then `run.bat` (tray) or `run.bat --console`. Options: `--keyboard huntsman` picks an OpenRGB keyboard by name, `--device k3max|openrgb` forces a backend. Build the `.exe` and the addon zip with `packaging\build.ps1`.

## Install (Keychron K3 Max, Windows)

1. **Firmware** — flash `firmware/keychron_k3_max/rgb_unit_bars_k3_max_ansi_rgb.bin` with [QMK Toolbox](https://github.com/qmk/qmk_toolbox): unplug the keyboard, set the side switch to cable mode, hold **Esc** while plugging it in, then click *Flash*. To go back, flash `keychron_k3_max_ansi_rgb_via_official.bin` the same way.
2. **Addon** — copy `addon/RGBUnitBars` into `World of Warcraft\_classic_beta_\Interface\AddOns\` (or `_classic_era_`), restart the game and enable *RGB Unit Bars*.
3. **Game settings** — use *Windowed* or *Windowed (Fullscreen)* mode.
4. **App** — run `RGBUnitBars.exe` with the K3 Max connected **by USB cable**; a plugged-in K3 Max is picked automatically. Bluetooth support is planned.

When WoW is minimized or on a loading screen the keyboard returns to its normal effect within 1.5 s.

### Streaming

The addon draws one row of 24 dark pixels (1 px tall) at the edge of the game window — practically invisible. Pick the corner or switch to bright pixels in `/rub`. It cannot disappear completely because the app reads it from the screen; crop the edge in OBS if you want it gone from the stream too.

## Bonus: music modes (K3 Max firmware)

* `python extras/music_eq.py [classic|fire|ocean|sunset|neon|toxic|rainbow|pastel] [--drift]` — 16-band spectrum analyzer of whatever is playing.
* `python extras/music_rgb.py` — whole keyboard pulses and shifts colour to the beat.

## Firmware extras

The custom K3 Max firmware also adds an **Fn-lock**: `Fn+Esc` swaps the top row between F1–F12 and media keys (Windows mode).

## Roadmap

- [x] Pixel protocol, K3 Max firmware, desktop app, rogue / mana / rage layouts
- [x] In-game settings panel (`/rub`): colours, row split, low-health threshold, preview mode
- [x] OpenRGB backend for non-QMK keyboards (tested against OpenRGB 1.0 debug devices)
- [x] Single-file `.exe` (tray, autostart, bundled OpenRGB, update notice) and CurseForge zip
- [ ] Dedicated Druid mode

## For developers and AI agents

See [`AGENTS.md`](AGENTS.md) — architecture, both protocols, how to port to another keyboard, and every pitfall hit while building this.

## License

GPL-3.0-or-later. The firmware is derived from QMK / Keychron QMK (GPL-2.0-or-later).
