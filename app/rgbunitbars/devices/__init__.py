from .k3max import KeychronK3Max, DeviceUnavailable
from .openrgb_sdk import OpenRGBKeyboard

DEVICES = {
    "k3max": KeychronK3Max,
    "openrgb": OpenRGBKeyboard,
}
