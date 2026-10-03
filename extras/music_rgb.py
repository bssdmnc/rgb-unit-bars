import sys, os, time, warnings
import numpy as np
import soundcard as sc

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from rgbunitbars.devices.via import ViaDevice, ViaError, find_raw_hid
from rgbunitbars.devices.k3max import KEYCHRON_VID

warnings.filterwarnings("ignore", category=sc.SoundcardRuntimeWarning)

RATE = 48000
FPS = 40
BLOCK = RATE // FPS
CH_RGB = 3
ID_BRIGHTNESS, ID_EFFECT, ID_SPEED, ID_COLOR = 1, 2, 3, 4
SOLID_COLOR = 1
MIN_BRIGHT = 25


class Keyboard:
    def __init__(self):
        self.h = None
        self.saved = None

    def _cmd(self, data):
        try:
            return self.h.command(data)
        except ViaError:
            raise OSError("no response")

    def connect(self):
        info = find_raw_hid(KEYCHRON_VID, exclude_product="Link")
        if info is None:
            self.h = None
            return False
        self.h = ViaDevice(info)
        try:
            if self.saved is None:
                self.saved = {i: self._cmd([0x08, CH_RGB, i])[3:5] for i in (ID_BRIGHTNESS, ID_EFFECT, ID_SPEED, ID_COLOR)}
            self._cmd([0x07, CH_RGB, ID_EFFECT, SOLID_COLOR])
        except OSError:
            self.h = None
            return False
        return True

    def set(self, value_id, *vals):
        try:
            self._cmd([0x07, CH_RGB, value_id, *vals])
            return True
        except (OSError, ValueError):
            self.h = None
            return False

    def restore(self):
        if self.h is None or self.saved is None:
            return
        s = self.saved
        self.set(ID_EFFECT, s[ID_EFFECT][0])
        self.set(ID_SPEED, s[ID_SPEED][0])
        self.set(ID_COLOR, s[ID_COLOR][0], s[ID_COLOR][1])
        self.set(ID_BRIGHTNESS, s[ID_BRIGHTNESS][0])


def main():
    kb = Keyboard()
    while not kb.connect():
        print("Waiting for wired K3 Max...")
        time.sleep(2)
    print("Connected. Music RGB running, Ctrl+C to stop.")

    speaker = sc.default_speaker()
    mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
    freqs = np.fft.rfftfreq(BLOCK, 1 / RATE)
    bass = (freqs >= 30) & (freqs <= 160)
    window = np.hanning(BLOCK)

    hue = 0.0
    level = 0.0
    peak = 1e-3
    bass_avg = 1e-6
    last_beat = 0.0
    last_sent = (None, None)
    stop_at = time.monotonic() + float(sys.argv[1]) if len(sys.argv) > 1 else None

    try:
        with mic.recorder(samplerate=RATE, channels=2, blocksize=BLOCK) as rec:
            while stop_at is None or time.monotonic() < stop_at:
                data = rec.record(numframes=BLOCK).mean(axis=1)
                rms = float(np.sqrt(np.mean(data ** 2)))
                peak = max(rms, peak * 0.998, 1e-3)
                target = min(rms / peak, 1.0)
                level = target if target > level else level * 0.85 + target * 0.15

                spec = np.abs(np.fft.rfft(data * window))
                b = float(spec[bass].sum())
                now = time.monotonic()
                if b > bass_avg * 1.6 and b > 0.5 and now - last_beat > 0.18:
                    hue += 35
                    level = 1.0
                    last_beat = now
                bass_avg = bass_avg * 0.95 + b * 0.05

                hue = (hue + 0.4 + level * 1.5) % 256
                bright = int(MIN_BRIGHT + (255 - MIN_BRIGHT) * level ** 1.5) if rms > 1e-4 else MIN_BRIGHT
                color = (int(hue), 255)

                if kb.h is None:
                    if not kb.connect():
                        time.sleep(1)
                        continue
                if color != last_sent[0]:
                    kb.set(ID_COLOR, *color)
                if bright != last_sent[1]:
                    kb.set(ID_BRIGHTNESS, bright)
                last_sent = (color, bright)
    except KeyboardInterrupt:
        pass
    finally:
        kb.restore()
        print("Stopped, lighting restored.")


if __name__ == "__main__":
    main()
