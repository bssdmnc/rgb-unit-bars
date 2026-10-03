import sys, os, time, warnings, colorsys
import numpy as np
import soundcard as sc

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from rgbunitbars.devices import KeychronK3Max, DeviceUnavailable
from rgbunitbars.devices.k3max import LED_POINTS

warnings.filterwarnings("ignore", category=sc.SoundcardRuntimeWarning)

RATE = 48000
FPS = 60
BLOCK = RATE // FPS
FFT_SIZE = 4096
BANDS = 16
ROWS = 6
F_LOW, F_HIGH = 35, 16000
RANGE_DB = 42
FALL = 0.82

GRADIENT_THEMES = {
    "classic": (85, -17),
    "fire": (0, 8),
    "ocean": (170, -12),
    "sunset": (200, 11),
    "neon": (128, 20),
    "toxic": (64, 6),
}
COLUMN_THEMES = ("rainbow", "pastel")

LED_BAND = np.array([min(x * BANDS // 224, BANDS - 1) for x, _ in LED_POINTS])
LED_CELL = np.array([(70 - y) // 13 for _, y in LED_POINTS])


def band_edges():
    edges = np.geomspace(F_LOW, F_HIGH, BANDS + 1)
    freqs = np.fft.rfftfreq(FFT_SIZE, 1 / RATE)
    idx = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = np.where((freqs >= lo) & (freqs < hi))[0]
        if len(sel) == 0:
            sel = np.array([np.argmin(np.abs(freqs - (lo + hi) / 2))])
        idx.append(sel)
    centers = np.sqrt(edges[:-1] * edges[1:])
    tilt = 3.0 * np.log2(centers / 100.0)
    return idx, tilt


def send_gradient(kb, bars, hue_bottom, hue_step):
    kb.send_bars(int(hue_bottom), hue_step, bars)


def send_columns(kb, bars, theme, shift):
    levels = np.clip(np.array(bars)[LED_BAND] * ROWS - LED_CELL * 255, 0, 255) / 255
    sat = 0.45 if theme == "pastel" else 1.0
    colors = []
    for band, v in zip(LED_BAND, levels):
        r, g, b = colorsys.hsv_to_rgb(((band * 15 + shift) % 256) / 256, sat, v)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    kb.send(colors)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    theme = args[0] if args else "classic"
    if theme not in GRADIENT_THEMES and theme not in COLUMN_THEMES:
        sys.exit("Unknown theme. Available: " + ", ".join([*GRADIENT_THEMES, *COLUMN_THEMES]))
    drift = "--drift" in sys.argv

    idx, tilt = band_edges()
    window = np.hanning(FFT_SIZE)
    ring = np.zeros(FFT_SIZE)
    levels = np.zeros(BANDS)
    ref = -60.0
    shift = 0.0

    kb = KeychronK3Max()
    print(f"Equalizer theme '{theme}'{' with drift' if drift else ''}, Ctrl+C to stop.")
    speaker = sc.default_speaker()
    mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)

    block = BLOCK if theme in GRADIENT_THEMES else RATE // 25
    fall = FALL ** (block / BLOCK)

    try:
        with mic.recorder(samplerate=RATE, channels=2, blocksize=block) as rec:
            while True:
                data = rec.record(numframes=block).mean(axis=1)
                ring = np.concatenate((ring[len(data):], data))

                if np.sqrt(np.mean(data ** 2)) < 1e-4:
                    target = np.zeros(BANDS)
                else:
                    spec = np.abs(np.fft.rfft(ring * window))
                    mags = np.array([spec[i].max() for i in idx])
                    db = 20 * np.log10(mags + 1e-9) + tilt
                    ref = max(db.max(), ref - 0.08)
                    target = np.clip((db - (ref - RANGE_DB)) / RANGE_DB, 0, 1)

                levels = np.maximum(target, levels * fall)
                bars = (levels * 255).astype(int).tolist()

                if drift:
                    shift = (shift + 0.4) % 256

                try:
                    if theme in GRADIENT_THEMES:
                        hue_bottom, hue_step = GRADIENT_THEMES[theme]
                        send_gradient(kb, bars, hue_bottom + shift, hue_step)
                    else:
                        send_columns(kb, bars, theme, shift)
                except DeviceUnavailable:
                    time.sleep(1)
    except KeyboardInterrupt:
        pass
    print("Stopped. Lighting returns to normal in ~1.5 s.")


if __name__ == "__main__":
    main()
