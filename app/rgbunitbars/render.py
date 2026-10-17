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
LEVEL_UP_EFFECT_SECONDS = 2.4
LEVEL_UP_COLOR = (1.0, 0.28, 0.0)


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


def level_up_colors(geometry, progress, now):
    last_row = max(geometry.row_count - 1, 1)
    colors = []
    if progress <= 0.5:
        outward = progress * 2
        fade = 1 - outward * 0.08
        for nx, row in geometry.keys:
            x = (nx - 0.5) * 2
            y = (row / last_row - 0.5) * 2
            radius = math.hypot(x, y) / math.sqrt(2)
            distance = radius - outward
            inside = radius <= outward
            shimmer = 0.5 + 0.5 * math.sin(math.atan2(y, x) * 5 + radius * 14 - now * 5)
            fill = (0.38 + 0.08 * shimmer) * fade if inside else 0
            front = math.exp(-((distance / 0.11) ** 2)) * 0.62 * fade
            outer_glow = math.exp(-((distance / 0.25) ** 2)) * 0.16 * fade if not inside else 0
            colors.append(scale(LEVEL_UP_COLOR, min(fill + front + outer_glow, 1)))
        return colors

    returning = (progress - 0.5) * 2
    width = 0.30 * (1 - returning) + 0.035
    fade = (1 - returning) ** 1.2
    spark_x = 0.48 * (1 - returning) + 0.09
    spark_y = 0.28 + 0.12 * math.sin(returning * math.pi)
    for nx, row in geometry.keys:
        x = (nx - 0.5) * 2
        y = (row / last_row - 0.5) * 2
        stripe = math.exp(-((x / width) ** 2))
        upper_spark = math.exp(-(((x - spark_x) / 0.10) ** 2 + ((y - spark_y) / 0.13) ** 2))
        lower_spark = math.exp(-(((x + spark_x) / 0.10) ** 2 + ((y + spark_y) / 0.13) ** 2))
        intensity = min((stripe * 0.8 + upper_spark + lower_spark) * fade, 1)
        colors.append(scale(LEVEL_UP_COLOR, intensity))
    return colors


def render(state, settings, geometry, now):
    if state.dead:
        return [(0, 0, 0) for _ in geometry.keys]
    if state.ghost:
        gray = (0.82, 0.84, 0.86)
        white = (0.96, 0.97, 0.98)
        colors = []
        for nx, row in geometry.keys:
            mix = (math.sin((nx * 4 + row * 0.45 - now * 2) * math.tau) + 1) / 2
            colors.append(tuple(int((gray[i] + (white[i] - gray[i]) * mix) * 255) for i in range(3)))
        return colors
    if state.level_up:
        elapsed = (1 - state.level_up) * LEVEL_UP_EFFECT_SECONDS
        progress = min(max(elapsed / LEVEL_UP_EFFECT_SECONDS, 0), 1)
        return level_up_colors(geometry, progress, now)

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
