import json
import logging
import os
import threading
import urllib.request
import webbrowser

import pystray
from PIL import Image, ImageDraw

from . import __version__, autostart
from .paths import DATA_DIR, LOG_FILE, frozen

log = logging.getLogger("RGBUnitBars")

GITHUB_REPO = "bssdmnc/rgb-unit-bars"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
LATEST_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def make_icon():
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, 62, 62), radius=12, fill=(24, 24, 28, 255))
    rows = [((242, 0, 255), 0.6), ((60, 220, 60), 0.85), ((255, 200, 0), 0.45)]
    for i, (color, fill) in enumerate(rows):
        top = 12 + i * 15
        draw.rounded_rectangle((10, top, 54, top + 10), radius=3, fill=(60, 60, 66, 255))
        draw.rounded_rectangle((10, top, 10 + int(44 * fill), top + 10), radius=3, fill=color + (255,))
    return image


def version_tuple(text):
    parts = []
    for piece in text.lstrip("vV").split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


class Tray:
    def __init__(self, engine, on_quit):
        self.engine = engine
        self.on_quit = on_quit
        self.update_version = None
        self.icon = pystray.Icon("RGBUnitBars", make_icon(), "RGB Unit Bars", self.build_menu())
        engine.listeners.append(self.refresh)

    def build_menu(self):
        items = [
            pystray.MenuItem(f"RGB Unit Bars {__version__}", None, enabled=False),
            pystray.MenuItem(lambda _: self.engine.status_line(), None, enabled=False),
            pystray.MenuItem(lambda _: self.engine.keyboard_name or "No keyboard yet", None, enabled=False),
            pystray.Menu.SEPARATOR,
        ]
        if frozen():
            items.append(pystray.MenuItem("Start with Windows", self.toggle_autostart, checked=lambda _: autostart.enabled()))
        items += [
            pystray.MenuItem(lambda _: f"Update available: {self.update_version}" if self.update_version else "Check releases", self.open_releases),
            pystray.MenuItem("Open log", self.open_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit),
        ]
        return pystray.Menu(*items)

    def refresh(self):
        self.icon.title = f"RGB Unit Bars — {self.engine.status_line()}"[:127]
        self.icon.update_menu()

    def toggle_autostart(self, _icon, _item):
        try:
            autostart.set_enabled(not autostart.enabled())
        except OSError:
            log.exception("Could not change autostart")
        self.refresh()

    def open_releases(self, _icon=None, _item=None):
        webbrowser.open(RELEASES_URL)

    def open_log(self, _icon=None, _item=None):
        target = LOG_FILE if os.path.isfile(LOG_FILE) else DATA_DIR
        os.startfile(target)

    def quit(self, _icon=None, _item=None):
        self.on_quit()
        self.icon.stop()

    def check_updates(self):
        try:
            request = urllib.request.Request(LATEST_API, headers={"User-Agent": "RGBUnitBars"})
            with urllib.request.urlopen(request, timeout=10) as response:
                tag = json.load(response).get("tag_name", "")
            if tag and version_tuple(tag) > version_tuple(__version__):
                self.update_version = tag
                log.info("Update available: %s", tag)
                self.icon.notify(f"Version {tag} is available. Open the tray menu to download it.", "RGB Unit Bars")
                self.refresh()
        except Exception as error:
            log.info("Update check skipped: %s", error)

    def run(self):
        def setup(icon):
            icon.visible = True
            self.refresh()
            threading.Thread(target=self.check_updates, daemon=True).start()

        self.icon.run(setup=setup)
