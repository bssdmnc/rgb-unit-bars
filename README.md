# RGB Unit Bars

Your World of Warcraft health, power and combo points — live on your RGB keyboard.

| Class / resource | Keyboard layout (top → bottom) |
|---|---|
| Rogue, Druid in Cat Form (energy) | combo points · health · energy |
| Warrior, Druid in Bear Form (rage) | health · rage |
| Mana users | health · mana |

* Health uses your class colour (green when it would clash with your resource) and fades to red, pulsing below 25 %. Health and resource colours can be changed per class in `/rub`.
* Combo points light up in five groups and flash at 5 — finisher time.
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

## Install with OpenRGB (most keyboards, Windows)

1. Install [OpenRGB](https://openrgb.org/releases.html) and check that it shows your keyboard. If the keyboard does not react, close vendor RGB apps (Synapse, iCUE, G HUB…) — they fight over the lighting.
2. In OpenRGB open **SDK Server** and click **Start Server** (or start OpenRGB with `--server`). Leave OpenRGB running.
3. Copy `addon/RGBUnitBars` into `World of Warcraft\_classic_beta_\Interface\AddOns\` (or `_classic_era_`), restart the game and enable *RGB Unit Bars*.
4. Use *Windowed* or *Windowed (Fullscreen)* mode in the game.
5. Install Python 3.11+, run `pip install -r app/requirements.txt`, then start `run.bat`. With several keyboards pick one by name: `run.bat --keyboard huntsman`.

When the game is minimized or loading, the keyboard returns to its previous OpenRGB mode after 1.5 s.

## Install (Keychron K3 Max, Windows)

1. **Firmware** — flash `firmware/keychron_k3_max/rgb_unit_bars_k3_max_ansi_rgb.bin` with [QMK Toolbox](https://github.com/qmk/qmk_toolbox): unplug the keyboard, set the side switch to cable mode, hold **Esc** while plugging it in, then click *Flash*. To go back, flash `keychron_k3_max_ansi_rgb_via_official.bin` the same way.
2. **Addon** — copy `addon/RGBUnitBars` into `World of Warcraft\_classic_beta_\Interface\AddOns\` (or `_classic_era_`), restart the game and enable *RGB Unit Bars*.
3. **Game settings** — use *Windowed* or *Windowed (Fullscreen)* mode.
4. **App** — install Python 3.11+, run `pip install -r app/requirements.txt`, connect the keyboard **by cable**, then start `run.bat` (a plugged-in K3 Max is picked automatically; force it with `run.bat --device k3max`).

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
- [ ] Single-file `.exe` and CurseForge package
- [ ] Dedicated Druid mode

## For developers and AI agents

See [`AGENTS.md`](AGENTS.md) — architecture, both protocols, how to port to another keyboard, and every pitfall hit while building this.

## License

GPL-3.0-or-later. The firmware is derived from QMK / Keychron QMK (GPL-2.0-or-later).
