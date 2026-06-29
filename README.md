# styledex-mcp

Thin MCP server for managing the StyleDex design library at `~/.styledex/designs`.

The server owns aliases, curated Playwright capture, metadata, artifact writes, validation summaries, rename, list, and delete. It does not expose generic browser controls; it only captures the StyleDex evidence types agents need.

## Install

Install the MCP server:

```bash
uv tool install styledex-mcp
```

Install the Playwright browser used for captures:

```bash
uvx --from styledex-mcp playwright install chromium
```

If `styledex-mcp` is not found after installation, add uv's tool directory to your shell path:

```bash
uv tool update-shell
```

Restart your shell after updating the path.

Upgrade later with:

```bash
uv tool upgrade styledex-mcp
```

Uninstall with:

```bash
uv tool uninstall styledex-mcp
```

## MCP Config

Use the installed `styledex-mcp` executable in your MCP client config.

```json
{
  "mcpServers": {
    "styledex": {
      "command": "styledex-mcp"
    }
  }
}
```

For opencode:

```json
{
  "mcp": {
    "styledex": {
      "type": "local",
      "command": ["styledex-mcp"],
      "enabled": true
    }
  }
}
```

Restart your MCP client after changing MCP config.

`styledex-mcp` uses stdio transport. Running it directly in a terminal is only useful for smoke testing; it waits for an MCP client on stdin.

## Environment

- `STYLEDEX_ROOT`: optional override for the design library root. Defaults to `~/.styledex/designs`.
- Legacy fallback: when `STYLEDEX_ROOT` is unset, `~/.styledex/designs` does not exist, and the old Style Mirror root exists, StyleDex reads `STYLE_MIRROR_ROOT` or `~/.style-mirror/designs` so existing captures remain available after the rename.

## Tools

- `styledex_list`
- `styledex_get`
- `styledex_create`
- `styledex_capture_screenshot`
- `styledex_capture_snapshot`
- `styledex_capture_extract`
- `styledex_save`
- `styledex_rename`
- `styledex_delete`

`styledex_create` supports `mode="overwrite"`.

`styledex_delete` permanently removes an alias directory.

## Capture Contract

```text
styledex_create
styledex_capture_screenshot
styledex_capture_snapshot
styledex_capture_extract
styledex_save
```

`styledex_get` and `styledex_save` include a validation summary, so there is no separate public validation tool.

`styledex_capture_extract` supports `links`, `cssVariables`, and `computedStyles`.

`styledex_save` accepts profile artifacts plus explicit metadata fields: `status`, `confidence`, `caveats`, and `observedNoise`. The MCP updates protected metadata fields such as `alias`, `createdAt`, `lastUpdated`, and `files` itself.

## Artifact Layout

Each saved site is isolated by alias under `~/.styledex/designs/<alias>/`. Screenshots for one alias are never shared with another alias.

Use artifact-type directories inside each alias:

- Screenshots: `screenshots/`
- Structured evidence: `evidence/`

Seed screenshots use the paths returned by `styledex_create` in `suggestedScreenshotPaths`, such as `screenshots/desktop-fold.png`.

Supporting page screenshots should also stay under the same alias-level `screenshots/` directory. Use the returned `suggestedPageScreenshotPaths` patterns, for example:

- `screenshots/pricing-desktop-full.png`
- `screenshots/pricing-mobile-full.png`

Do not put screenshots under `evidence/`. Page-specific JSON evidence can use paths such as `evidence/pages/pricing/computed-styles.json`.

## Development Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m playwright install chromium
```

Run validation:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m mypy
```

Verify the package installs as a persistent tool:

```bash
uv tool install .
uv tool list
```
