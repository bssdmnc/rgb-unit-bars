from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SIZE = 1024
SS = 4

BG = (17, 19, 25)
BODY = (30, 33, 42)
BODY_EDGE = (48, 52, 64)
KEY_OFF = (44, 48, 60)

ROWS = [
    {"keys": 5, "lit": 3.0, "color": (214, 70, 255)},
    {"keys": 8, "lit": 5.6, "color": (40, 235, 110)},
    {"keys": 8, "lit": 3.4, "color": (40, 120, 255)},
]


def scaled(value):
    return int(value * SS)


def mix(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def key_rects():
    left, right = 130, 894
    top, row_h, gap = 312, 112, 24
    rects = []
    for r, row in enumerate(ROWS):
        y0 = top + r * (row_h + gap)
        count = row["keys"]
        width = (right - left - gap * (count - 1)) / count
        for k in range(count):
            x0 = left + k * (width + gap)
            level = min(max(row["lit"] - k, 0.0), 1.0)
            rects.append(((x0, y0, x0 + width, y0 + row_h), row["color"], level))
    return rects


def draw_logo():
    canvas = SIZE * SS
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, canvas - 1, canvas - 1), radius=scaled(200), fill=BG)

    body = (84, 266, 940, 758)
    draw.rounded_rectangle(tuple(scaled(v) for v in body), radius=scaled(56), fill=BODY, outline=BODY_EDGE, width=scaled(6))

    glow = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for rect, color, level in key_rects():
        if level > 0:
            pad = 8
            box = (rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad)
            glow_draw.rounded_rectangle(tuple(scaled(v) for v in box), radius=scaled(30), fill=color + (int(150 * level),))
    glow = glow.filter(ImageFilter.GaussianBlur(scaled(22)))
    image = Image.alpha_composite(image, glow)
    draw = ImageDraw.Draw(image)

    for rect, color, level in key_rects():
        face = mix(KEY_OFF, color, level * 0.92 + (0.08 if level == 0 else 0))
        top_face = mix(face, (255, 255, 255), 0.18 * level + 0.04)
        draw.rounded_rectangle(tuple(scaled(v) for v in rect), radius=scaled(20), fill=face)
        inner = (rect[0] + 10, rect[1] + 8, rect[2] - 10, rect[3] - 22)
        draw.rounded_rectangle(tuple(scaled(v) for v in inner), radius=scaled(14), fill=top_face)

    mask = Image.new("L", (canvas, canvas), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, canvas - 1, canvas - 1), radius=scaled(200), fill=255)
    image.putalpha(Image.composite(image.getchannel("A"), mask, mask))
    return image.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    logo = draw_logo()
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    logo.save(assets / "logo.png")
    logo.resize((400, 400), Image.LANCZOS).save(assets / "logo_400.png")
    logo.resize((64, 64), Image.LANCZOS).save(ROOT / "addon" / "RGBUnitBars" / "icon.tga")
    print("written", assets / "logo.png")


if __name__ == "__main__":
    main()
