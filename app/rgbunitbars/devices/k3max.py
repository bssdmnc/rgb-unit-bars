from .via import ViaDevice, ViaError, find_raw_hid, ID_CUSTOM_SET_VALUE

KEYCHRON_VID = 0x3434
CHANNEL_CUSTOM = 0x00
VALUE_BARS = 0x01
VALUE_LEDS = 0x02
LEDS_PER_PACKET = 9

LED_POINTS = [
    (0, 0), (14, 0), (29, 0), (44, 0), (59, 0), (74, 0), (89, 0), (104, 0), (119, 0), (134, 0), (149, 0), (164, 0), (179, 0), (194, 0), (209, 0), (223, 0),
    (0, 12), (14, 12), (29, 12), (44, 12), (59, 12), (74, 12), (89, 12), (104, 12), (119, 12), (134, 12), (149, 12), (164, 12), (179, 12), (201, 12), (223, 12),
    (3, 25), (22, 25), (37, 25), (52, 25), (67, 25), (82, 25), (97, 25), (112, 25), (126, 25), (141, 25), (156, 25), (171, 25), (186, 25), (205, 25), (223, 25),
    (5, 38), (26, 38), (41, 38), (55, 38), (70, 38), (85, 38), (100, 38), (115, 38), (130, 38), (145, 38), (160, 38), (175, 38), (199, 38), (223, 38),
    (9, 51), (33, 51), (48, 51), (63, 51), (78, 51), (93, 51), (108, 51), (123, 51), (138, 51), (153, 51), (168, 51), (188, 51), (209, 51), (223, 51),
    (1, 64), (20, 64), (39, 64), (95, 64), (149, 64), (164, 64), (179, 64), (194, 64), (209, 64), (223, 64),
]


class DeviceUnavailable(Exception):
    pass


class KeychronK3Max:
    name = "Keychron K3 Max (RGB Unit Bars firmware)"
    leds = LED_POINTS
    row_tolerance = 4

    def __init__(self):
        self.via = None

    def prepare(self):
        pass

    def idle(self):
        pass

    def connect(self):
        info = find_raw_hid(KEYCHRON_VID, exclude_product="Link")
        if info is None:
            raise DeviceUnavailable("Keychron K3 Max not found on USB (wired mode required)")
        self.via = ViaDevice(info)

    def send(self, colors):
        if self.via is None:
            self.connect()
        try:
            for start in range(0, len(colors), LEDS_PER_PACKET):
                chunk = colors[start:start + LEDS_PER_PACKET]
                payload = [c for rgb in chunk for c in rgb]
                self.via.command([ID_CUSTOM_SET_VALUE, CHANNEL_CUSTOM, VALUE_LEDS, start, len(chunk), *payload])
        except (OSError, ValueError, ViaError):
            self.close()
            raise DeviceUnavailable("lost connection to keyboard")

    def send_bars(self, hue_bottom, hue_step, levels):
        if self.via is None:
            self.connect()
        try:
            self.via.command([ID_CUSTOM_SET_VALUE, CHANNEL_CUSTOM, VALUE_BARS, hue_bottom & 0xFF, hue_step & 0xFF, *levels])
        except (OSError, ValueError, ViaError):
            self.close()
            raise DeviceUnavailable("lost connection to keyboard")

    def close(self):
        if self.via is not None:
            try:
                self.via.close()
            except OSError:
                pass
        self.via = None
