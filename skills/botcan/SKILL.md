---
name: botcan
description: Automate a real web browser and scrape websites by writing YAML recipes executed through the botcan MCP tools (play_recipe / play_steps). Use when the user wants to open pages, click, fill forms, extract data, take screenshots, or download files from websites.
---

# Botcan — YAML browser recipes

botcan runs headless Firefox via Playwright against YAML recipes. Each run uses a fresh
disposable browser profile (no cookies/history from the user's real browsing).

## How to execute

Two MCP tools from the `botcan` server, depending on the client's naming:

- `play_recipe` / `botcan_play_recipe` — argument `recipe_path`: run a recipe `.yaml` file on disk. Use when you can write the recipe to a file.
- `play_steps` / `botcan_play_steps` — argument `recipe_yaml`: run recipe text inline (you generate the YAML). Use for quick one-shot jobs.

Optional argument `output_dir` (either tool): directory for downloads/screenshots/JSON saves. Defaults to `./output` relative to the working directory.

Both tools return JSON:

```json
{"extracted_data": {"#product-name": "...", "internal_link": "https://..."}, "error": null}
```

`extracted_data` holds everything collected by `extract` and `copy_link` steps.
`error` is a string on any failure (bad YAML, unknown action, missing selector) and is returned, not raised — surface it to the user.

## Recipe format

Top level: `open` (URL — also starts the browser), `steps` (ordered list), `close` (optional marker).
Each step is a single-key mapping: `{action: {args}}`.

```yaml
open: https://example.com
steps:
  - fill: {selector: "#search", value: "weather"}
  - press: {selector: "#search", key: "Enter"}
  - wait: {selector: "#results", timeout: 5000}
  - extract: {selector: "#results h3", all: true}
  - screenshot: {path: "results.png", full_page: true}
  - save: {path: "results.json", format: json}
close:
```

## Action vocabulary (args required)

| action | args | notes |
| --- | --- | --- |
| click | selector | |
| check / uncheck | selector | checkbox/radio |
| clear | selector | empty a text input |
| fill | selector, value | |
| press | selector, key | e.g. Enter |
| select | selector, value | value = option's `value` attribute |
| hover | selector | |
| scroll | selector | scrolls element into view |
| wait | selector, timeout (optional, ms) | default 30000 |
| copy_link | selector, key | store the `href` under `key` in extracted_data |
| extract | selector, `first: true` or `all: true` | text of first match, or list of all matches; stored under the selector |
| download | selector, path | click triggers download, saved to output_dir/path |
| screenshot | path, full_page (optional) | PNG to output_dir/path |
| save | path, format (json) | dump all collected extracted_data as JSON |

`selector` is any Playwright/CSS selector (`#id`, `.class`, `text=Login`, `:has-text('...')`).

## Rules

- `open` comes first; a step before it errors with "browser is not open".
- Unknown actions or keys are a returned error that lists supported names — fix the recipe on that feedback.
- Prefer `extract` + `save` (or returned JSON) over scrolling screenshots for data the user wants to read.
- Recipes run sequentially; each `open`/`steps` pair is one page visit in the current single-page engine.
