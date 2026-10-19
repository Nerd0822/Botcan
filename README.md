# botcan

YAML-driven browser automation and scraping. Write a recipe, run it, get extracted data
plus downloaded files. Runs headless Firefox through Playwright; every run uses a fresh
disposable browser profile.

## Quick start (dev)

```sh
uv run python run.py src/demo/demo.yaml    # demo recipe (local demo page on :5500)
```

Output files land in `./output` relative to where you run it.

## Install on other machines

From this GitHub repo directly — no registry needed:

```sh
uv tool install git+https://github.com/Nerd0822/Botcan.git     # botcan CLI + botcan-mcp on PATH
uv add "botcan @ git+https://github.com/Nerd0822/Botcan.git"    # as a dependency in a project
```

Pin a released tag if you want immutable installs (`@v0.1.0` instead of latest commit).
Then one-time per machine, fetch the browser:

```sh
uvx playwright install firefox
```

Use it:

```sh
botcan my_recipe.yaml my_output_dir     # prints extracted_data JSON; downloads/screenshots land in the output dir
botcan-mcp                              # the MCP server (register it in your AI app, see below)
```

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
`save(path, format)`. Unknown actions return a listed error instead of crashing.

`headless` lives in `src/botcan/config.py` (`HEADLESS = False` is handy while developing:
you can watch the browser; the MCP server always runs headless regardless).

## Run as an MCP server

```sh
uv run botcan-mcp                          # stdio MCP server: play_recipe + play_steps
```

Register with your AI app (point `--directory` at your checkout):

```sh
# OpenCode (global for every project)
opencode mcp add botcan --global -- uv --directory <path-to-botcan> run botcan-mcp
```

```jsonc
// Claude Desktop — claude_desktop_config.json
{ "mcpServers": { "botcan": { "command": "uv", "args": ["--directory", "<path-to-botcan>", "run", "botcan-mcp"] } } }
```

```sh
# Claude Code
claude mcp add botcan -- uv --directory <path-to-botcan> run botcan-mcp
```

```toml
# Codex — ~/.codex/config.toml
[mcp_servers.botcan]
command = "uv"
args = ["--directory", "<path-to-botcan>", "run", "botcan-mcp"]
```

## Skill (teaches models the recipe language)

`~/.claude/skills/botcan/SKILL.md` — read natively by Claude Code, auto-discovered by
OpenCode through its `~/.claude/skills` compatibility scan. One file, both apps.

This repo ships the same file at `skills/botcan/SKILL.md` — install it by copying
(or symlinking) that directory into `~/.claude/skills/botcan/`.

For claude.ai: skills are uploaded as a ZIP in Settings → Skills. Build it with:

```sh
zip -r botcan-skill.zip skills/botcan
```

The skill only *writes* recipes there — running them needs the MCP server locally
(see the setup steps above), since a cloud sandbox can't drive your browser.
