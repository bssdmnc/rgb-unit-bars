import logging
import os
import shutil
import socket
import subprocess
import time

from .paths import DATA_DIR, bundle_dir

log = logging.getLogger("RGBUnitBars")

CREATE_NO_WINDOW = 0x08000000
SERVER_START_TIMEOUT = 15
SERVER_POLL_INTERVAL = 0.25
INSTALL_DIR = os.path.join(DATA_DIR, "openrgb")
CONFIG_DIR = os.path.join(DATA_DIR, "openrgb-config")
SYSTEM_INSTALL = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "OpenRGB", "OpenRGB.exe")


def server_running(host, port, timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def bundled_source():
    path = os.path.join(bundle_dir(), "openrgb")
    return path if os.path.isfile(os.path.join(path, "OpenRGB.exe")) else None


def installed_executable():
    source = bundled_source()
    if source:
        stamp = os.path.join(INSTALL_DIR, ".bundle-size")
        size = str(sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(source) for f in fs))
        current = open(stamp).read() if os.path.isfile(stamp) else ""
        if current != size:
            log.info("Unpacking bundled OpenRGB to %s", INSTALL_DIR)
            shutil.rmtree(INSTALL_DIR, ignore_errors=True)
            shutil.copytree(source, INSTALL_DIR)
            with open(stamp, "w") as f:
                f.write(size)
        return os.path.join(INSTALL_DIR, "OpenRGB.exe")
    if os.path.isfile(SYSTEM_INSTALL):
        return SYSTEM_INSTALL
    return None


class OpenRGBServer:
    def __init__(self, host="127.0.0.1", port=6742):
        self.host = host
        self.port = port
        self.process = None

    def ensure(self):
        if server_running(self.host, self.port):
            return True
        if self.process is not None and self.process.poll() is None:
            return self._wait_until_running()
        if self.host not in ("127.0.0.1", "localhost"):
            return False
        exe = installed_executable()
        if exe is None:
            log.warning("No OpenRGB server on %s:%s and no OpenRGB to start", self.host, self.port)
            return False
        os.makedirs(CONFIG_DIR, exist_ok=True)
        log.info("Starting OpenRGB server: %s", exe)
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        self.process = subprocess.Popen(
            [exe, "--server", "--server-port", str(self.port), "--config", CONFIG_DIR],
            cwd=os.path.dirname(exe),
            creationflags=CREATE_NO_WINDOW,
            startupinfo=startup,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return self._wait_until_running()

    def _wait_until_running(self):
        deadline = time.monotonic() + SERVER_START_TIMEOUT
        while time.monotonic() < deadline:
            if server_running(self.host, self.port):
                return True
            if self.process is not None and self.process.poll() is not None:
                return False
            time.sleep(SERVER_POLL_INTERVAL)
        return False

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            log.info("Stopping OpenRGB server we started")
            self.process.terminate()
            try:
                self.process.wait(5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
