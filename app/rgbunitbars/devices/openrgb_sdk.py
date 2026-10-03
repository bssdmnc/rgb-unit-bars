import socket

from openrgb import OpenRGBClient
from openrgb.utils import DeviceType, ModeColors, RGBColor, ZoneType

from .k3max import DeviceUnavailable

DIRECT_MODE_NAMES = ("direct", "custom", "static")
PROTOCOL_VERSION = 3
CONNECT_TIMEOUT = 5


class OpenRGBKeyboard:
    row_tolerance = 0

    def __init__(self, host="127.0.0.1", port=6742, match=""):
        self.host = host
        self.port = port
        self.match = match.lower()
        self.client = None
        self.device = None
        self.name = "OpenRGB keyboard"
        self.leds = []
        self.led_ids = []
        self.led_total = 0
        self.saved_mode = None
        self.direct = False

    def prepare(self):
        previous_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(CONNECT_TIMEOUT)
        try:
            self.client = OpenRGBClient(self.host, self.port, "RGB Unit Bars", protocol_version=PROTOCOL_VERSION)
        except (OSError, ConnectionError) as error:
            raise DeviceUnavailable(f"OpenRGB SDK server not reachable on {self.host}:{self.port} ({error})")
        finally:
            socket.setdefaulttimeout(previous_timeout)
        keyboards = self.client.get_devices_by_type(DeviceType.KEYBOARD)
        if self.match:
            keyboards = [d for d in keyboards if self.match in d.name.lower()]
        if not keyboards:
            raise DeviceUnavailable("OpenRGB reports no keyboard" + (f" matching '{self.match}'" if self.match else ""))
        keyboards.sort(key=lambda d: not any(z.type == ZoneType.MATRIX and z.matrix_map for z in d.zones))
        self.device = keyboards[0]
        self.name = f"{self.device.name} (OpenRGB)"
        self.saved_mode = self.device.active_mode
        self.leds, self.led_ids = self._layout(self.device)
        self.led_total = len(self.device.leds)

    @staticmethod
    def _layout(device):
        points, ids = [], []
        matrices = [z for z in device.zones if z.type == ZoneType.MATRIX and z.matrix_map]
        if matrices:
            zone = max(matrices, key=lambda z: len(z.leds))
            for row, line in enumerate(zone.matrix_map):
                for col, local in enumerate(line):
                    if local is not None and 0 <= local < len(zone.leds):
                        points.append((col, row))
                        ids.append(zone.leds[local].id)
            return points, ids
        for index, led in enumerate(device.leds):
            points.append((index, 0))
            ids.append(led.id)
        return points, ids

    def _enter_direct(self):
        for index, mode in enumerate(self.device.modes):
            if mode.name.lower() in DIRECT_MODE_NAMES and mode.color_mode == ModeColors.PER_LED:
                self.device.set_mode(index)
                self.direct = True
                return
        raise DeviceUnavailable(f"{self.device.name} has no per-key (Direct) mode in OpenRGB")

    def send(self, colors):
        if self.device is None:
            self.prepare()
        try:
            if not self.direct:
                self._enter_direct()
            frame = [RGBColor(0, 0, 0)] * self.led_total
            for led_id, (r, g, b) in zip(self.led_ids, colors):
                frame[led_id] = RGBColor(r, g, b)
            self.device.set_colors(frame, fast=True)
        except (OSError, ConnectionError, BrokenPipeError) as error:
            self.close()
            raise DeviceUnavailable(f"lost connection to OpenRGB ({error})")

    def idle(self):
        if self.device is not None and self.direct and self.saved_mode is not None:
            try:
                self.device.set_mode(self.saved_mode)
            except (OSError, ConnectionError):
                pass
            self.direct = False

    def close(self):
        self.idle()
        if self.client is not None:
            try:
                self.client.disconnect()
            except (OSError, ConnectionError):
                pass
        self.client = None
        self.device = None
        self.direct = False
