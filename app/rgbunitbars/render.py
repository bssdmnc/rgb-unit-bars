import colorsys
import math

from .wow_link import (
    CAST_INSTEAD_BOTH,
    CAST_INSTEAD_HEALTH,
    CAST_INSTEAD_POWER,
    CAST_OWN_ROWS,
    POWER_ENERGY,
    POWER_FOCUS,
    POWER_MANA,
    POWER_RAGE,
    POWER_RUNIC,
)

MAX_COMBO = 5
FIXED_POWER_COLORS = {
    POWER_FOCUS: (1.0, 0.5, 0.25),
    POWER_RUNIC: (0.0, 0.82, 1.0),
}


class KeyboardGeometry:
    def __init__(self, points, row_tolerance=4):
        ys = sorted({y for _, y in points})
        rows = []
        for y in ys:
            if rows and y - rows[-1][-1] <= row_tolerance:
                rows[-1].append(y)
            else:
                rows.append([y])
        self.row_count = len(rows)
        self.row_of = {}
        for index, group in enumerate(rows):
            for y in group:
                self.row_of[y] = index
        xs = [x for x, _ in points]
        x_min, x_max = min(xs), max(xs)
        span = max(x_max - x_min, 1)
        self.keys = [((x - x_min) / span, self.row_of[y]) for x, y in points]
        gaps = []
        for row in range(self.row_count):
            row_xs = sorted(nx for nx, r in self.keys if r == row)
            gaps += [b - a for a, b in zip(row_xs, row_xs[1:]) if b > a]
        gaps.sort()
        self.key_width = gaps[len(gaps) // 2] if gaps else 1 / 16

    def row_groups(self, layout):
        layout = [(name, weight) for name, weight in layout if weight > 0]
        total = sum(weight for _, weight in layout)
        groups, start, acc = {}, 0, 0
        for name, weight in layout:
            acc += weight
            end = round(acc / total * self.row_count)
            for row in range(start, end):
                groups[row] = name
            start = end
        return groups


def bar_level(nx, pct, key_width):
    return min(max((pct * (1 + key_width) - nx) / key_width, 0.0), 1.0)


def scale(rgb, value):
    value = max(0.0, min(value, 1.0))
    return tuple(int(c * value * 255) for c in rgb)


def blend_hsv(low, high, t):
    h1, s1, v1 = colorsys.rgb_to_hsv(*low)
    h2, s2, v2 = colorsys.rgb_to_hsv(*high)
    return colorsys.hsv_to_rgb(h1 + (h2 - h1) * t, s1 + (s2 - s1) * t, v1 + (v2 - v1) * t)


CAST_REPLACES = {
    CAST_INSTEAD_HEALTH: {"health"},
    CAST_INSTEAD_POWER: {"power"},
    CAST_INSTEAD_BOTH: {"health", "power"},
}


def layout_for(state, settings):
    combo = state.power_type == POWER_ENERGY
    weights = {
        "health": settings.health_rows + (0 if combo else settings.combo_rows),
        "power": settings.power_rows,
        "cast": settings.cast_rows if settings.cast_mode == CAST_OWN_ROWS else 0,
    }
    layout = [(name, weights[name]) for name in settings.order]
    return [("combo", settings.combo_rows)] + layout if combo else layout


def cast_level(nx, state, settings, key_width):
    if not state.casting:
        return 0.0
    progress = 1 - state.cast if settings.cast_invert else state.cast
    return bar_level(1 - nx if settings.cast_mirror else nx, progress, key_width)


def power_color(state, settings):
    named = {POWER_MANA: "mana", POWER_RAGE: "rage", POWER_ENERGY: "energy"}
    if state.power_type in named:
        return settings.colors[named[state.power_type]]
    return FIXED_POWER_COLORS.get(state.power_type, settings.colors["mana"])


def render(state, settings, geometry, now):
    groups = geometry.row_groups(layout_for(state, settings))
    t = min(max((state.health - 0.2) / 0.6, 0.0), 1.0)
    health_rgb = blend_hsv(settings.colors["health_low"], settings.colors["health_full"], t)
    health_pulse = 0.55 + 0.45 * math.sin(now * 10) if settings.pulse and state.health < settings.low_health else 1.0
    combo_pulse = 0.6 + 0.4 * math.sin(now * 14) if settings.combo_flash and state.combo >= MAX_COMBO else 1.0
    power_rgb = power_color(state, settings)
    replaced = CAST_REPLACES.get(settings.cast_mode, set()) if state.casting else set()
    dim = settings.dim
    colors = []
    for nx, row in geometry.keys:
        group = groups.get(row, "power")
        if group in replaced:
            group = "cast"
        if group == "cast":
            lit = cast_level(nx, state, settings, geometry.key_width)
            colors.append(scale(settings.colors["cast"], dim + (1 - dim) * lit))
        elif group == "combo":
            segment = min(int(nx * MAX_COMBO), MAX_COMBO - 1)
            lit = 1.0 if state.combo > segment else 0.0
            colors.append(scale(settings.colors["combo"], (dim + (1 - dim) * lit) * combo_pulse))
        elif group == "health":
            lit = bar_level(nx, state.health, geometry.key_width)
            colors.append(scale(health_rgb, (dim + (1 - dim) * lit) * health_pulse))
        else:
            lit = bar_level(nx, state.power, geometry.key_width)
            colors.append(scale(power_rgb, dim + (1 - dim) * lit))
    return colors
