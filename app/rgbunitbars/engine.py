import logging
import threading
import time

from .devices import DEVICES, DeviceUnavailable
from .devices.k3max import KEYCHRON_VID
from .devices.via import find_raw_hid
from .openrgb_server import OpenRGBServer
from .render import KeyboardGeometry, render
from .wow_link import WowLink

log = logging.getLogger("RGBUnitBars")

FPS = 20
KEEPALIVE = 0.5
IDLE_AFTER = 1.5
NO_WOW_INTERVAL = 2.0
NO_ADDON_INTERVAL = 0.5
KEYBOARD_RETRY = 3.0

STATUS_TEXT = {
    "starting": "Starting…",
    "keyboard": "Looking for a keyboard…",
    "no-wow": "Waiting for World of Warcraft",
    "no-addon": "WoW found, addon not visible (loading screen, minimized or addon disabled)",
    "ok": "Showing your bars",
    "offline": "Keyboard disconnected — retrying",
}


class Engine(threading.Thread):
    def __init__(self, device="auto", openrgb_host="127.0.0.1", openrgb_port=6742, keyboard=""):
        super().__init__(name="engine", daemon=True)
        self.requested = device
        self.openrgb_host = openrgb_host
        self.openrgb_port = openrgb_port
        self.keyboard = keyboard
        self.server = OpenRGBServer(openrgb_host, openrgb_port)
        self.stop_event = threading.Event()
        self.status = "starting"
        self.detail = ""
        self.keyboard_name = ""
        self.listeners = []

    def set_status(self, status, detail=""):
        if (status, detail) != (self.status, self.detail):
            self.status, self.detail = status, detail
            log.info("%s%s", STATUS_TEXT[status], f" — {detail}" if detail else "")
            for listener in self.listeners:
                listener()

    def status_line(self):
        text = STATUS_TEXT[self.status]
        if self.status == "keyboard" and self.detail:
            text = f"{text} ({self.detail})"
        return text

    def stop(self):
        self.stop_event.set()

    def wait(self, seconds):
        return self.stop_event.wait(seconds)

    def pick_backend(self):
        if self.requested != "auto":
            return self.requested
        return "k3max" if find_raw_hid(KEYCHRON_VID, exclude_product="Link") else "openrgb"

    def open_device(self):
        while not self.stop_event.is_set():
            backend = self.pick_backend()
            if backend == "openrgb":
                self.server.ensure()
                device = DEVICES["openrgb"](self.openrgb_host, self.openrgb_port, self.keyboard)
            else:
                device = DEVICES[backend]()
            try:
                device.prepare()
                self.keyboard_name = device.name
                log.info("Keyboard: %s (%d LEDs)", device.name, len(device.leds))
                return device
            except DeviceUnavailable as error:
                self.set_status("keyboard", str(error))
                if self.wait(KEYBOARD_RETRY):
                    return None
        return None

    def run(self):
        try:
            self.loop()
        except Exception:
            log.exception("Engine crashed")
            raise
        finally:
            self.server.stop()

    def loop(self):
        device = self.open_device()
        if device is None:
            return
        geometry = KeyboardGeometry(device.leds, device.row_tolerance)
        link = WowLink()
        last_colors, last_sent = None, 0.0
        last_state_at, idle = 0.0, True
        try:
            while not self.stop_event.is_set():
                started = time.monotonic()
                reading, status = link.read()
                state, settings = reading if reading else (None, None)
                if state is None and not idle and started - last_state_at > IDLE_AFTER:
                    device.idle()
                    idle, last_colors = True, None
                if state is None:
                    self.set_status(status)
                    if self.wait(NO_WOW_INTERVAL if status == "no-wow" else NO_ADDON_INTERVAL):
                        break
                    continue
                last_state_at, idle = started, False
                colors = render(state, settings, geometry, started)
                if colors != last_colors or started - last_sent > KEEPALIVE:
                    try:
                        device.send(colors)
                        last_colors, last_sent = colors, started
                        self.set_status("ok")
                    except DeviceUnavailable as error:
                        self.set_status("offline", str(error))
                        if self.backend_is_openrgb(device):
                            self.server.ensure()
                        if self.wait(1):
                            break
                        continue
                self.wait(max(0.0, 1 / FPS - (time.monotonic() - started)))
        finally:
            device.close()
            link.close()

    @staticmethod
    def backend_is_openrgb(device):
        return device.__class__.__name__ == "OpenRGBKeyboard"
