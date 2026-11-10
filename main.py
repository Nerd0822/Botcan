import sys
from pathlib import Path

import orjson
from scraper import RecipeError, Scraper

recipe_path = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path(__file__).parent / "demo/demo.yaml"
)
output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

bot: Scraper = Scraper(HEADLESS=False, output_dir=output_dir)

try:
    extracted_data = bot.execute_recipe(recipe_path)
except RecipeError as recipe_error:
    print(f"botcan: {recipe_error}", file=sys.stderr)
    raise SystemExit(1)

print(orjson.dumps(extracted_data, option=orjson.OPT_INDENT_2).decode())
