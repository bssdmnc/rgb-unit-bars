import ctypes
import math
from ctypes import wintypes
from dataclasses import dataclass, field

import mss

PIXELS = 24
REFERENCES = (1.0, 0.0, 0.25, 0.5, 0.75)
STEPS = 12
MIN_LEVEL = 12
COLOR_KEYS = ("health_full", "health_low", "mana", "rage", "energy", "combo", "cast")

CAST_OFF = 0
CAST_OWN_ROWS = 1
CAST_INSTEAD_HEALTH = 2
CAST_INSTEAD_POWER = 3
CAST_INSTEAD_BOTH = 4
ORDERS = (
    ("health", "power", "cast"),
    ("power", "health", "cast"),
    ("cast", "health", "power"),
    ("cast", "power", "health"),
    ("health", "cast", "power"),
    ("power", "cast", "health"),
)

POWER_MANA = 0
POWER_RAGE = 1
POWER_FOCUS = 2
POWER_ENERGY = 3
POWER_RUNIC = 6

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except (AttributeError, OSError):
    pass
user32 = ctypes.windll.user32


@dataclass
class UnitState:
    health: float
    power: float
    combo: int
    power_type: int
    cast: float = 0.0
    casting: bool = False


@dataclass
class Settings:
    colors: dict = field(default_factory=lambda: {
        "health_full": (0.0, 1.0, 0.0),
        "health_low": (1.0, 0.0, 0.0),
        "mana": (0.0, 0.4, 1.0),
        "rage": (1.0, 0.0, 0.0),
        "energy": (1.0, 0.85, 0.0),
        "combo": (0.95, 0.0, 1.0),
        "cast": (1.0, 0.61, 0.32),
    })
    combo_rows: int = 0
    health_rows: int = 1
    power_rows: int = 1
    dim: float = 0.10
    low_health: float = 0.25
    pulse: bool = True
    combo_flash: bool = True
    cast_mode: int = CAST_OWN_ROWS
    cast_rows: int = 2
    order: tuple = ORDERS[2]
    cast_invert: bool = False
    cast_mirror: bool = False


def wow_client_rect():
    hwnd = user32.FindWindowW(None, "World of Warcraft")
    if not hwnd or user32.IsIconic(hwnd):
        return None
    point = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    return point.x, point.y, rect.right, rect.bottom


def corner_regions(rect):
    left, top, width, height = rect
    w = min(PIXELS, width)
    right, bottom = left + width - w, top + height - 1
    return [(left, top, w), (right, top, w), (left, bottom, w), (right, bottom, w)]


class WowLink:
    def __init__(self):
        self.sct = mss.MSS()
        self.corner = 0

    def close(self):
        self.sct.close()

    def read(self):
        rect = wow_client_rect()
        if rect is None or rect[2] < PIXELS or rect[3] < 1:
            return None, "no-wow"
        regions = corner_regions(rect)
        for index in [self.corner] + [i for i in range(len(regions)) if i != self.corner]:
            left, top, width = regions[index]
            shot = self.sct.grab({"left": left, "top": top, "width": width, "height": 1})
            state, settings = decode([shot.pixel(x, 0)[:3] for x in range(width)])
            if state:
                self.corner = index
                return (state, settings), "ok"
        return (None, None), "no-addon"


def near(value, target, level):
    return abs(value - target) <= 3 + level * 0.12


def calibration(px):
    magenta, green = px[0], px[1]
    level = (magenta[0] + magenta[2]) / 2
    if level < MIN_LEVEL or not near(magenta[0], magenta[2], level) or not near(magenta[1], 0, level):
        return None
    if not near(green[1], level, level) or not near(green[0], 0, level) or not near(green[2], 0, level):
        return None
    if not all(near(c, level, level) for c in px[2]):
        return None
    points = sorted((fraction, sum(px[2 + i]) / 3) for i, fraction in enumerate(REFERENCES))
    if any(b[1] - a[1] < 1.5 for a, b in zip(points, points[1:])):
        return None
    return points


def decode(px):
    if len(px) < PIXELS:
        return None, None
    points = calibration(px)
    if points is None:
        return None, None

    def fraction(value):
        if value <= points[0][1]:
            return 0.0
        for (f0, v0), (f1, v1) in zip(points, points[1:]):
            if value <= v1:
                return f0 + (f1 - f0) * (value - v0) / (v1 - v0)
        return 1.0

    def gray(pixel):
        return fraction(sum(pixel) / 3)

    def steps(pixel):
        return [round(fraction(c) * STEPS) for c in pixel]

    def clamp(value, low, high):
        return min(max(value, low), high)

    state = UnitState(
        health=gray(px[7]),
        power=gray(px[8]),
        combo=round(gray(px[9]) * 10),
        power_type=round(gray(px[10]) * 10),
        cast=gray(px[11]),
        casting=gray(px[12]) > 0.5,
    )
    colors = {key: tuple(fraction(c) for c in px[13 + i]) for i, key in enumerate(COLOR_KEYS)}
    combo_rows, health_rows, power_rows = steps(px[20])
    dim, low, flags = steps(px[21])
    cast_mode, cast_rows, order = steps(px[22])
    cast_flags = steps(px[23])[0]
    settings = Settings(
        colors=colors,
        combo_rows=clamp(combo_rows, 0, 3),
        health_rows=clamp(health_rows, 1, 5),
        power_rows=clamp(power_rows, 1, 5),
        dim=clamp(dim, 0, 6) * 0.05,
        low_health=clamp(low, 0, 10) * 0.05,
        pulse=bool(flags & 1),
        combo_flash=bool(flags & 2),
        cast_mode=clamp(cast_mode, CAST_OFF, CAST_INSTEAD_BOTH),
        cast_rows=clamp(cast_rows, 1, 5),
        order=ORDERS[clamp(order, 0, len(ORDERS) - 1)],
        cast_invert=bool(cast_flags & 1),
        cast_mirror=bool(cast_flags & 2),
    )
    return state, settings
