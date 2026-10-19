import argparse
import json
import sys

from botcan.scraper import Scraper


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="botcan",
        description="Run a YAML browser-automation recipe with Playwright.",
    )
    parser.add_argument("recipe", help="path to the recipe YAML file")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="directory for downloads/screenshots/saves (default: ./output)",
    )
    args = parser.parse_args(argv)

    scraper = Scraper(output_dir=args.output_dir)
    try:
        error = scraper.read_recipe(args.recipe)
    finally:
        scraper.close()
    if error is not None:
        print(f"botcan: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(scraper.extracted_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
