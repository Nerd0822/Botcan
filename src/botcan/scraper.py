from playwright.sync_api import sync_playwright

from .config import ACTIONS, HEADLESS, OUTPUT_DIR

from pathlib import Path
import json
import yaml


class Scraper:
    """Executes YAML recipes with Playwright.

    Error contract: every method returns errors instead of raising.
    load_recipe returns (recipe, error); read_recipe returns an error
    string, or None on success.
    """

    def __init__(self, output_dir=None, headless=None):
        self.pw = None
        self.browser = None
        self.page = None
        self.extracted_data = {}
        self.output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
        self.headless = HEADLESS if headless is None else bool(headless)

    def start(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.firefox.launch(headless=self.headless)
        self.page = self.browser.new_page()

    def close(self):
        if self.pw is not None:
            if self.browser is not None:
                self.browser.close()
                self.pw.stop()
            self.pw = None

    def load_recipe(self, file_path):
        try:
            with open(file_path, "r") as recipe_file:
                return yaml.safe_load(recipe_file), None
        except FileNotFoundError:
            return None, f"recipe file not found: {file_path}"
        except yaml.YAMLError as yaml_error:
            return None, f"invalid YAML in {file_path}: {yaml_error}"

    def read_recipe(self, file_path):
        recipe, error = self.load_recipe(file_path)
        if recipe is None:
            return error or f"recipe is empty: {file_path}"

        self.extracted_data = {}
        try:
            for recipe_key, recipe_value in recipe.items():
                match recipe_key:
                    case "open":
                        self.start()
                        self.page.goto(recipe_value)
                    case "steps":
                        self.run_steps(recipe_value)
                    case "close":
                        self.close()
                    case _:
                        raise ValueError(
                            f"unsupported recipe key: {recipe_key!r}, supported: open, steps, close"
                        )
        except Exception as recipe_error:
            return f"{type(recipe_error).__name__}: {recipe_error}"
        return None

    def run_steps(self, steps):
        for step in steps:
            if not isinstance(step, dict) or len(step) != 1:
                raise ValueError(f"each step must have exactly one action, got: {step!r}")
            (action_name, action_args), = step.items()
            self.run_action(action_name, action_args)

    def run_action(self, action_name, action_args):
        if self.page is None:
            raise RuntimeError("browser is not open: add an 'open' step before other actions")

        match action_name:
            case "click":
                self.page.locator(action_args["selector"]).click()
            case "check":
                self.page.locator(action_args["selector"]).check()
            case "uncheck":
                self.page.locator(action_args["selector"]).uncheck()
            case "clear":
                self.page.locator(action_args["selector"]).clear()
            case "fill":
                self.page.locator(action_args["selector"]).fill(action_args["value"])
            case "press":
                self.page.locator(action_args["selector"]).press(action_args["key"])
            case "select":
                self.page.locator(action_args["selector"]).select_option(action_args["value"])
            case "hover":
                self.page.locator(action_args["selector"]).hover()
            case "copy_link":
                link_url = self.page.locator(action_args["selector"]).get_attribute("href")
                self.extracted_data[action_args["key"]] = link_url
            case "wait":
                self.page.wait_for_selector(
                    action_args["selector"],
                    timeout=int(action_args.get("timeout", 30000)),
                )
            case "scroll":
                self.page.locator(action_args["selector"]).scroll_into_view_if_needed()
            case "extract":
                locator = self.page.locator(action_args["selector"])
                if action_args.get("all"):
                    extracted_value = locator.all_text_contents()
                else:
                    extracted_value = locator.first.text_content()
                self.extracted_data[action_args["selector"]] = extracted_value
            case "download":
                with self.page.expect_download() as download_info:
                    self.page.locator(action_args["selector"]).click()
                download_info.value.save_as(self._output_path(action_args["path"]))
            case "screenshot":
                self.page.screenshot(
                    path=str(self._output_path(action_args["path"])),
                    full_page=bool(action_args.get("full_page", False)),
                )
            case "save":
                output_format = action_args.get("format", "json")
                if output_format != "json":
                    raise ValueError(f"unsupported save format: {output_format}")
                self._output_path(action_args["path"]).write_text(
                    json.dumps(self.extracted_data, indent=2)
                )
            case _:
                raise ValueError(
                    f"unsupported action: {action_name!r}, supported: {list(ACTIONS)}"
                )

    def _output_path(self, file_name):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / file_name
