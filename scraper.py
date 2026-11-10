from pathlib import Path

import orjson
import yaml
from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    sync_playwright,
)
from playwright.sync_api import (
    Error as PlaywrightError,
)

ACTIONS = (
    "click",
    "check",
    "uncheck",
    "clear",
    "fill",
    "press",
    "select",
    "hover",
    "copy_link",
    "wait",
    "scroll",
    "extract",
    "download",
    "screenshot",
    "save",
)


class RecipeError(Exception):
    """Base error for anything the recipe author can fix."""


class RecipeLoadError(RecipeError):
    """Missing file, invalid YAML, or a malformed recipe document."""


class StepError(RecipeError):
    """A step failed or is malformed."""


class Scraper:
    def __init__(self, HEADLESS: bool, output_dir: str | Path = "output"):
        self.pw: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.HEADLESS = HEADLESS
        self.extracted_data: dict = {}
        self.output_dir = Path(output_dir)

    def __start(self) -> Page:
        if self.page is not None:
            return self.page
        try:
            self.pw = sync_playwright().start()
            self.browser = self.pw.firefox.launch(headless=self.HEADLESS)
            self.page = self.browser.new_page()
        except PlaywrightError as browser_error:
            self.__close()
            raise RecipeError(
                f"failed to start browser: {browser_error}"
            ) from browser_error
        return self.page

    def __close(self) -> None:
        try:
            if self.browser is not None:
                self.browser.close()
            if self.pw is not None:
                self.pw.stop()
        except PlaywrightError:
            pass
        finally:
            self.browser = None
            self.pw = None
            self.page = None

    @staticmethod
    def __load_recipe(file_path: str | Path) -> dict:
        try:
            with open(file_path, "r") as recipe_file:
                recipe = yaml.safe_load(recipe_file)
        except FileNotFoundError:
            raise RecipeLoadError(f"recipe file not found: {file_path}") from None
        except yaml.YAMLError as yaml_error:
            raise RecipeLoadError(
                f"invalid YAML in {file_path}: {yaml_error}"
            ) from yaml_error
        if not isinstance(recipe, dict) or not recipe:
            raise RecipeLoadError(f"recipe must be a non-empty mapping: {file_path}")
        return recipe

    def execute_recipe(self, file_path: str | Path) -> dict:
        recipe = self.__load_recipe(file_path)
        self.extracted_data = {}
        try:
            for key, value in recipe.items():
                match key:
                    case "open":
                        if not isinstance(value, str):
                            raise RecipeError(
                                f"'open' must be a URL string, got {value!r}"
                            )
                        try:
                            self.__start().goto(value)
                        except PlaywrightError as browser_error:
                            raise RecipeError(
                                f"failed to open {value}: {browser_error}"
                            ) from browser_error
                    case "steps":
                        self.__run_steps(value)
                    case "close":
                        self.__close()
                    case _:
                        raise RecipeError(f"unsupported recipe key: {key!r}")
        finally:
            self.__close()
        return self.extracted_data

    def __run_steps(self, steps) -> None:
        if not isinstance(steps, list):
            raise StepError(f"'steps' must be a list, got {type(steps).__name__}")
        for index, step in enumerate(steps):
            if not isinstance(step, dict) or len(step) != 1:
                raise StepError(f"step {index}: expected a single action, got {step!r}")
            ((action, args),) = step.items()
            if not isinstance(args, dict):
                raise StepError(f"step {index} ({action}): arguments must be a mapping")
            try:
                self.__run_action(action, args)
            except RecipeError:
                raise
            except KeyError as missing:
                raise StepError(
                    f"step {index} ({action}): missing required field {missing}"
                ) from missing
            except (PlaywrightError, ValueError) as step_error:
                raise StepError(
                    f"step {index} ({action}): {step_error}"
                ) from step_error

    def __run_action(self, action: str, args: dict) -> None:
        if self.page is None:
            raise StepError(
                "browser is not open: add an 'open' step before other actions"
            )
        page = self.page

        match action:
            case "click":
                page.locator(args["selector"]).click()
            case "check":
                page.locator(args["selector"]).check()
            case "uncheck":
                page.locator(args["selector"]).uncheck()
            case "clear":
                page.locator(args["selector"]).clear()
            case "fill":
                page.locator(args["selector"]).fill(args["value"])
            case "press":
                page.locator(args["selector"]).press(args["key"])
            case "select":
                page.locator(args["selector"]).select_option(args["value"])
            case "hover":
                page.locator(args["selector"]).hover()
            case "copy_link":
                link_url = page.locator(args["selector"]).get_attribute("href")
                self.extracted_data[args["key"]] = link_url
            case "wait":
                page.wait_for_selector(
                    args["selector"],
                    timeout=int(args.get("timeout", 30000)),
                )
            case "scroll":
                page.locator(args["selector"]).scroll_into_view_if_needed()
            case "extract":
                locator = page.locator(args["selector"])
                if args.get("all"):
                    extracted_value = locator.all_text_contents()
                else:
                    extracted_value = locator.first.text_content()
                self.extracted_data[args["selector"]] = extracted_value
            case "download":
                with page.expect_download() as download_info:
                    page.locator(args["selector"]).click()
                download_info.value.save_as(self.__output_path(args["path"]))
            case "screenshot":
                page.screenshot(
                    path=str(self.__output_path(args["path"])),
                    full_page=bool(args.get("full_page", False)),
                )
            case "save":
                output_format = args.get("format", "json")
                if output_format != "json":
                    raise RecipeError(f"unsupported save format: {output_format}")
                self.__output_path(args["path"]).write_bytes(
                    orjson.dumps(self.extracted_data, option=orjson.OPT_INDENT_2)
                )
            case _:
                raise StepError(
                    f"unsupported action: {action!r}, supported: {list(ACTIONS)}"
                )

    def __output_path(self, file_name: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / file_name
