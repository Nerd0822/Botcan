from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent  # the botcan/ folder
src_dir = PACKAGE_DIR.parent
RECIPES_DIR = PACKAGE_DIR / "recipes"
OUTPUT_DIR = Path.cwd() / "output"

HEADLESS = False

ACTIONS = (
    "click",
    "check",
    "uncheck",
    "clear",
    "press",
    "copy_link",
    "download",
    "extract",
    "fill",
    "screenshot",
    "save",
    "select",
    "hover",
    "wait",
    "scroll",
)
