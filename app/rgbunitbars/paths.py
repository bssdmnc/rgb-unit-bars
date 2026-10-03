import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

APP_NAME = "RGBUnitBars"
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), APP_NAME)
LOG_FILE = os.path.join(DATA_DIR, "log.txt")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def frozen():
    return getattr(sys, "frozen", False)


def bundle_dir():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def setup_logging(console):
    os.makedirs(DATA_DIR, exist_ok=True)
    handlers = [RotatingFileHandler(LOG_FILE, maxBytes=512 * 1024, backupCount=1, encoding="utf-8")]
    if console:
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers, force=True)
    return logging.getLogger(APP_NAME)


def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(config):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
