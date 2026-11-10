# botcan

YAML-driven browser automation and scraping. Write a recipe, run it, get extracted data
plus downloaded files. Runs Firefox through Playwright; every run uses a fresh disposable
browser profile.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uvx playwright install firefox     # one-time per machine
```

## Run a recipe

```sh
uv run python main.py                       # demo recipe, visible browser
uv run python main.py my_recipe.yaml        # any recipe
uv run python main.py my_recipe.yaml ./out  # custom output dir (default: ./output)
```

Extracted data is printed as JSON. `download`, `screenshot`, and `save` steps write into
the output dir. On failure the CLI prints `botcan: StepError: ...` and exits 1.

The demo recipe points at `http://127.0.0.1:5500/Projects_/Botcan/demo/demo.html`; serve
the repo's parent directory on port 5500 (VS Code Live Server does this by default) or
adjust the `open:` URL to wherever `demo/demo.html` is served.

## Recipe format

Top level: `open` (URL — starts the browser when hit), `steps` (list), `close` (optional marker).
Each step is a single-key mapping.

```yaml
open: https://example.com
steps:
  - fill: {selector: "#search", value: "weather"}
  - press: {selector: "#search", key: "Enter"}
  - wait: {selector: "#results", timeout: 5000}
  - extract: {selector: "#results h3", all: true}
  - copy_link: {selector: "a.permalink", key: "permalink"}
  - screenshot: {path: "results.png", full_page: true}
  - save: {path: "results.json", format: json}
close:
```

Actions and required args: `click(selector)`, `check(selector)`, `uncheck(selector)`,
`clear(selector)`, `fill(selector, value)`, `press(selector, key)`, `select(selector, value)`,
`hover(selector)`, `scroll(selector)`, `wait(selector, timeout?)`, `copy_link(selector, key)`,
`extract(selector, first?|all?)`, `download(selector, path)`, `screenshot(path, full_page?)`,
`save(path, format)`.

`extract` and `copy_link` fill `extracted_data`: the former under the selector, the latter
under `key`. A step before `open` fails with "browser is not open".

## Run as an MCP server

```sh
uv run python server.py
```

Two tools: `play_recipe` (path to a recipe file) and `play_steps` (inline YAML). Both return:

```json
{"extracted_data": {"#product-name": "...", "internal_link": "https://..."}, "error": null}
```

Bad YAML, unknown actions, and failed steps return a string in `error` (not an exception),
and `extracted_data` keeps everything collected before the failure.

Register with your AI app, pointing `--directory` at this checkout:

```sh
# OpenCode (global for every project)
opencode mcp add botcan --global -- uv --directory <path-to-botcan> run python server.py
```

```jsonc
// OpenCode — ~/.config/opencode/opencode.jsonc
"mcp": {
  "servers": {
    "botcan": {
      "type": "local",
      "command": ["uv", "--directory", "<path-to-botcan>", "run", "python", "server.py"]
    }
  }
}
```

```jsonc
// Claude Desktop — claude_desktop_config.json
{ "mcpServers": { "botcan": { "command": "uv", "args": ["--directory", "<path-to-botcan>", "run", "python", "server.py"] } } }
```

```sh
# Claude Code
claude mcp add botcan -- uv --directory <path-to-botcan> run python server.py
```

```toml
# Codex — ~/.codex/config.toml
[mcp_servers.botcan]
command = "uv"
args = ["--directory", "<path-to-botcan>", "run", "python", "server.py"]
```

## Skill (teaches models the recipe language)

`skills/botcan/SKILL.md` — copy (or symlink) that directory into `~/.claude/skills/botcan/`.
Claude Code reads it natively; OpenCode discovers it through its `~/.claude/skills`
compatibility scan. For claude.ai, upload it as a ZIP in Settings → Skills:

```sh
zip -r botcan-skill.zip skills/botcan
```

## Layout

```
main.py      CLI runner
scraper.py   recipe engine: actions, extraction, errors
server.py    MCP server: play_recipe / play_steps
demo/        demo page + recipe
skills/      model-facing skill for the recipe language
```
