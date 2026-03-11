from pathlib import Path

ROOT = Path(__file__).parent

class Configuration:
    VIDEO_PATH    = Path("videos")
    DATABASE_PATH = Path("snorlax.db")
    STATIC_PATH   = ROOT / "static"
    TEMPLATE_PATH = ROOT / "templates"

config = Configuration
