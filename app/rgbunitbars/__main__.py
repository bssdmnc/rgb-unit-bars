import argparse
import time

from .devices import DEVICES, DeviceUnavailable
from .devices.k3max import KEYCHRON_VID
from .devices.via import find_raw_hid
from .render import KeyboardGeometry, render
from .wow_link import WowLink

FPS = 20
KEEPALIVE = 0.5
IDLE_AFTER = 1.5
STATUS_TEXT = {
    "ok": "Reading health/power from WoW.",
    "no-addon": "WoW found, but the addon strip is not visible (loading screen, exclusive fullscreen, UI hidden or addon disabled).",
    "no-wow": "WoW window not found or minimized.",
}


def main():
    parser = argparse.ArgumentParser(prog="rgbunitbars", description="Show WoW health, power and combo points on an RGB keyboard.")
    parser.add_argument("--device", choices=["auto", *sorted(DEVICES)], default="auto", help="keyboard backend (default: auto = K3 Max if connected, else OpenRGB)")
    parser.add_argument("--openrgb-host", default="127.0.0.1")
    parser.add_argument("--openrgb-port", type=int, default=6742)
    parser.add_argument("--keyboard", default="", help="OpenRGB: pick the keyboard whose name contains this text")
    args = parser.parse_args()

    if args.device == "auto":
        args.device = "k3max" if find_raw_hid(KEYCHRON_VID, exclude_product="Link") else "openrgb"
    if args.device == "openrgb":
        device = DEVICES["openrgb"](args.openrgb_host, args.openrgb_port, args.keyboard)
    else:
        device = DEVICES[args.device]()
    waiting = False
    while True:
        try:
            device.prepare()
            break
        except DeviceUnavailable as error:
            if not waiting:
                print(f"Waiting for keyboard: {error}")
                waiting = True
            time.sleep(2)
    geometry = KeyboardGeometry(device.leds, device.row_tolerance)
    link = WowLink()
    print(f"RGB Unit Bars: {device.name}. Ctrl+C to stop.")

    last_colors, last_sent, status, offline = None, 0.0, None, False
    last_state_at, idle = 0.0, True
    try:
        while True:
            started = time.monotonic()
            reading, new_status = link.read()
            state, settings = reading if reading else (None, None)
            if new_status != status:
                status = new_status
                print(STATUS_TEXT[status])
            if state is None and not idle and started - last_state_at > IDLE_AFTER:
                device.idle()
                idle, last_colors = True, None
            if state is not None:
                last_state_at, idle = started, False
                colors = render(state, settings, geometry, started)
                if colors != last_colors or started - last_sent > KEEPALIVE:
                    try:
                        device.send(colors)
                        last_colors, last_sent = colors, started
                        if offline:
                            print("Keyboard connected.")
                            offline = False
                    except DeviceUnavailable as error:
                        if not offline:
                            print(f"Keyboard unavailable: {error}. Retrying...")
                            offline = True
                        time.sleep(1)
            time.sleep(max(0.0, 1 / FPS - (time.monotonic() - started)))
    except KeyboardInterrupt:
        pass
    finally:
        device.close()
        link.close()
    print("Stopped. Keyboard lighting returns to normal in ~1.5 s.")


if __name__ == "__main__":
    main()
