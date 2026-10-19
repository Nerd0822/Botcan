import asyncio
import json
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .scraper import Scraper


mcp = FastMCP(
    "botcan",
    instructions=(
        "Runs YAML browser-automation recipes with headless Playwright (Firefox). "
        "A recipe has top-level keys: open (URL, starts the browser), steps (list), "
        "close (optional). Step actions: click, check, uncheck, clear, press, "
        "copy_link, download, extract, fill, screenshot, save, select, hover, "
        "wait, scroll. play_steps accepts generated recipe text directly."
    ),
)


def _result_payload(extracted_data, error):
    return json.dumps(
        {"extracted_data": extracted_data, "error": error}, ensure_ascii=False
    )


def _run_recipe_file(file_path, output_dir=None):
    scraper = Scraper(output_dir=output_dir, headless=True)
    try:
        error = scraper.read_recipe(file_path)
    finally:
        scraper.close()
    return _result_payload(scraper.extracted_data, error)


@mcp.tool()
async def play_recipe(recipe_path: str, output_dir: str | None = None) -> str:
    """Execute a YAML recipe file: open pages, run browser steps, return extracted data."""
    return await asyncio.to_thread(_run_recipe_file, recipe_path, output_dir)


def _run_inline_recipe(recipe_yaml, output_dir=None):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as recipe_file:
            recipe_file.write(recipe_yaml)
            temp_path = recipe_file.name
        return _run_recipe_file(temp_path, output_dir)
    except Exception as recipe_error:
        return _result_payload({}, f"{type(recipe_error).__name__}: {recipe_error}")
    finally:
        if temp_path is not None:
            Path(temp_path).unlink(missing_ok=True)


@mcp.tool()
async def play_steps(recipe_yaml: str, output_dir: str | None = None) -> str:
    """Execute an inline YAML recipe string (agent-generated). Args mirror recipe file format."""
    return await asyncio.to_thread(_run_inline_recipe, recipe_yaml, output_dir)


def main():
    mcp.run()
