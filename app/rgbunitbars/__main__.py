import argparse
import ctypes
import sys
import time

from . import __version__, autostart
from .devices import DEVICES
from .engine import Engine
from .paths import frozen, load_config, save_config, setup_logging

MUTEX_NAME = "Local\\RGBUnitBarsSingleInstance"
ERROR_ALREADY_EXISTS = 183


def single_instance():
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        return None
    return handle


def first_run_setup(log):
    config = load_config()
    if frozen() and not config.get("autostart_initialized"):
        try:
            autostart.set_enabled(True)
            log.info("Enabled start with Windows")
        except OSError:
            log.exception("Could not enable start with Windows")
        config["autostart_initialized"] = True
        save_config(config)


def main():
    parser = argparse.ArgumentParser(prog="rgbunitbars", description="Show WoW health, power and combo points on an RGB keyboard.")
    parser.add_argument("--device", choices=["auto", *sorted(DEVICES)], default="auto", help="keyboard backend (default: auto = K3 Max if connected, else OpenRGB)")
    parser.add_argument("--openrgb-host", default="127.0.0.1")
    parser.add_argument("--openrgb-port", type=int, default=6742)
    parser.add_argument("--keyboard", default="", help="OpenRGB: pick the keyboard whose name contains this text")
    parser.add_argument("--console", action="store_true", help="run without the tray icon, log to the console")
    parser.add_argument("--minimized", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    console = args.console or not frozen()
    log = setup_logging(console=console)
    mutex = single_instance()
    if mutex is None:
        log.info("Another RGB Unit Bars is already running; exiting")
        return
    log.info("RGB Unit Bars %s starting (%s)", __version__, "packaged" if frozen() else "source")
    first_run_setup(log)

    engine = Engine(args.device, args.openrgb_host, args.openrgb_port, args.keyboard)
    engine.start()

    if args.console:
        try:
            while engine.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        engine.stop()
        engine.join(5)
        log.info("Stopped. Keyboard lighting returns to normal in ~1.5 s.")
        return

    from .tray import Tray

    def shutdown():
        engine.stop()
        engine.join(5)
        log.info("Stopped from tray")

    Tray(engine, shutdown).run()


if __name__ == "__main__":
    sys.exit(main())
