import sys

from botcan.config import src_dir
from botcan.scraper import Scraper


def main():
    scraper = Scraper()
    try:
        error = scraper.read_recipe(src_dir / "demo/demo.yaml")
    finally:
        scraper.close()
    if error is not None:
        print(f"botcan: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
